import argparse
import os
import os.path
import tempfile
import threading
from tkinter import *
from tkinter import filedialog, ttk, messagebox

import cv2
import tqdm
from facedetect import ensure_dir

from guitils import yesorno, GUIProgress, SimpleContainer


def percentOf(value, total):
    return int((value / total) * 100)


def ptail(path):
    return os.path.split(path)[-1]


def phead(path):
    return os.path.split(path)[0]


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('-f', '--file', help='Shrink a single file')
    ap.add_argument('-d', '--directory', help='Shrink all images in a directory (folder)')
    ap.add_argument('-w', '--width', help='Target width to shrink the image to. if -w 0 and height is given width is calculated automatically based on original image dimensions', type=int, default=0)
    ap.add_argument('-t', '--height', help='Target height to shrink the image to. if -h 0 and width is given height is calculated automatically based on original image dimensions', type=int, default=0)
    ap.add_argument('-o', '--output', help='Location to write new images. Fore -f mode it must be a file path for -d it must be a directory. For -f it can be the same path as the input file, but it cannot be the same as the input folder in -d mode')
    ap.add_argument('-g', '--gui', help='Run with GUI interface instead of command line. All other options are ignored', action='store_true')
    options = ap.parse_args()
    if not options.file and not options.directory:
        options.gui = True
        return options

    if options.width == 0 and options.height == 0:
        ap.error("Must specify either --width, --height or both")

    return options


def get_interactive_args():
    options = argparse.Namespace(**{'file': None, 'directory': None, 'output': None, 'width': None, 'height': 0})

    def choose_location(var, method):
        actions = {'file': filedialog.askopenfilename, 'directory': filedialog.askdirectory}
        choice = actions[method](initialdir=os.getcwd())
        if choice:
            var.was_set = True
            var.method = method
            var.set(choice)
            setattr(options, method, choice)

    def save_file(sourcevar, destinationvar):
        if not hasattr(sourcevar, 'method'):
            messagebox.showerror("No source selected", "Choose a source file or folder first!")
            return
        if sourcevar.method == 'directory':
            choice = filedialog.askdirectory(initialdir=sourcevar.get())
        else:
            choice = filedialog.asksaveasfilename(initialdir=phead(sourcevar.get()), initialfile=ptail(sourcevar.get()))
        if choice:
            destinationvar.was_set = True
            destinationvar.set(choice)
            setattr(options, 'output', choice)

    def go_shrink(loc, out, wv):
        try:
            if wv.get() <= 0:
                raise ValueError("Invalid width")
        except Exception:
            messagebox.showerror('Invalid Width', 'You must enter a valid positive integer for width')

        if not loc.was_set:
            messagebox.showinfo('Choose Source', "You must choose a source file or directory to shrink")
            return

        if not out.was_set:
            messagebox.showinfo('Choose Destination', 'You must choose a save location for the shrunken file')
            return

        setattr(options, 'width', wv.get())
        argwindow.destroy()

    argwindow = Tk()
    linstruction = Label(argwindow, text="Choose a file or folder of images to shrink")
    locationvar = StringVar()
    locationvar.was_set = False

    flabel = Label(argwindow, textvariable=locationvar)

    fchoose = Button(argwindow, text="Choose file", command=lambda: choose_location(locationvar, 'file'))
    dchoose = Button(argwindow, text="Choose folder", command=lambda: choose_location(locationvar, 'directory'))
    linstruction.pack()
    flabel.pack()
    fchoose.pack()
    dchoose.pack()
    ttk.Separator(argwindow, orient='horizontal').pack(fill='x', padx=5, pady=5)
    oinstruction = Label(argwindow, text="Choose a destination file for the shrunken file")
    outvar = StringVar()
    outvar.was_set = False

    olabel = Label(argwindow, textvariable=outvar)
    ochoose = Button(argwindow, text="Choose destination", command=lambda: save_file(locationvar, outvar))
    oinstruction.pack()
    olabel.pack()
    ochoose.pack()

    widthvar = IntVar(argwindow, 197)
    slabel = Label(argwindow, text='Enter the width to resize to\n(Height is calculated automatically)')
    sentry = Entry(textvariable=widthvar)
    sbutton = Button(argwindow, text="Shrink!", command=lambda: go_shrink(locationvar, outvar, widthvar))
    slabel.pack()
    sentry.pack()
    sbutton.pack()
    argwindow.mainloop()

    return options


def rename_shrunk(input, width):
    new_name = input.split('.')
    new_name[0] = new_name[0] + '_shrunk_' + str(width)
    return '.'.join(new_name)


def resize_image_data(img: 'cv2.image', argwidth: int, argheight: int):
    if img is None:
        return None
    if argwidth == 0 and argheight == 0:
        raise ValueError("Cannot resize an image to 0x0")

    height, width, _ = img.shape
    if argwidth == 0:
        argwidth = int(width * (argheight / height))
    if argheight == 0:
        argheight = int(height * (argwidth / width))

    resized_img = cv2.resize(img, (argwidth, argheight))
    return resized_img


def resize_image_bytes(img: bytes, argwidth: int, argheight: int):
    with tempfile.NamedTemporaryFile('wb') as f:
        f.write(img)

        data = cv2.imread(f.name)
        return resize_image_data(data, argwidth, argheight)


def resize_image(filename, argwidth, argheight, destination):
    img = cv2.imread(filename)
    new_img = resize_image_data(img, argwidth, argheight)
    # img = cv2.imread(filename)
    # if img is None:
    #     return False
    # height, width, _ = img.shape
    # new_height = int(argwidth)
    # new_width = int(width * new_height / height)
    # resized_img = cv2.resize(img, (new_width, new_height))
    cv2.imwrite(destination, new_img)
    return True


def main():
    options = parse_args()
    if options.gui:
        args = get_interactive_args()
    else:
        args = options

    if args.file:
        destination = args.output
        _, file = os.path.split(destination)
        if not file:
            raise ValueError("output for file mode must be full path to output filename not directory")
        resize_image(args.file, args.width, args.height, destination)
        messagebox.showinfo("Done", "Finished shrinking \n{}\ninto\n{}".format(args.file, args.output))
    elif args.directory:
        outdir = os.path.join(args.output, 'shrunk')
        if not os.path.exists(outdir):
            ensure_dir(outdir)
        elif os.path.exists(outdir) and not os.path.isdir(outdir):
            raise ValueError("Output for directory mode must be folder not filename")
        if options.gui:
            yesorno(title="Ready to begin shrinking",
                    text="""
                Shrinking files in {}
                Shrunken image files will have their original name + '_shrunk_{}' at the end
                Shrunked images will be written in {}

                If files matching this pattern exist, they WILL BE OVERWRITTEN

                Continue?""".format(
                        args.directory, args.width, outdir))
        else:
            r = input('Ready to begin shrinking from {}. \nShrunken images will be written to {}? y/(n) '.format(args.directory, args.output))
            if not r.lower().startswith('y'):
                print("Cancelled")
                return
        filenames = os.listdir(args.directory)
        total = len(filenames)
        if options.gui:
            shrinkgate = SimpleContainer(True)
            g = GUIProgress('Shrinking files...',
                            total,
                            title='Shrinking files in {}'.format(args.directory),
                            main_label='Shrinking files in {}'.format(args.directory),
                            job_gate_variable=shrinkgate)

            def target():
                for (i, path) in enumerate(filenames):
                    if not shrinkgate.get():
                        g.update(0, 'User cancelled')
                        g.done()
                        break
                    filename = os.path.join(args.directory, path)
                    if not os.path.isdir(filename):
                        g.update(i, 'Shrinking {}'.format(path))
                        new_name = rename_shrunk(path, args.width)
                        new_file = os.path.join(outdir, new_name)
                        try:
                            result = resize_image(filename, args.width, args.height, new_file)
                        except cv2.error:
                            print("Cannot process {}".format(path))
                        else:
                            if not result:
                                g.update(i, text='Error: Could not read image named: {}'.format(filename))
                g.update(total, text="Done")
                g.done()
            thread = threading.Thread(daemon=True, target=target)
            thread.start()
            g.start()
        else:
            for file in tqdm.tqdm(filenames):
                path = os.path.join(args.directory, file)
                if not os.path.isdir(path):
                    # print("Working on {}".format(path))
                    new_file = rename_shrunk(path, args.width)
                    try:
                        result = resize_image(path, args.width, args.height, new_file)
                    except cv2.error:
                        print("Cannot process {}".format(path))
                    else:
                        if not result:
                            print("Error: {}".format(result))

    else:
        # messagebox.showerror("No Selection", "No File or Folder was selected")
        pass


if __name__ == '__main__':
    main()
