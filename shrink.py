import argparse
import os
import os.path
import threading
from tkinter import *
from tkinter import filedialog, ttk, messagebox

import cv2

from guitils import yesorno, GUIProgress, SimpleContainer


def percentOf(value, total):
    return int((value / total) * 100)


def ptail(path):
    return os.path.split(path)[-1]

def phead(path):
    return os.path.split(path)[0]

def get_interactive_args():
    options = argparse.Namespace(**{'file': None, 'directory': None, 'output': None, 'width': None})

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


def resize_image(filename, argwidth, destination):
    img = cv2.imread(filename)
    if img is None:
        return False
    height, width, _ = img.shape
    new_height = int(argwidth)
    new_width = int(width * new_height / height)
    resized_img = cv2.resize(img, (new_width, new_height))
    cv2.imwrite(destination, resized_img)
    return True


def main():
    yesorno(title="Welcome to shrink", text='''
        This program will help you shrink an image file to the correct size for Rediker's photo system. It is worth 
        noting that the facedetect program can do this automatically when detecting faces, however, you can also do it 
        manually here

        You will be guided through the process in a series of steps using interactive dialogs 

        ** INSTRUCTIONS FOR USE**
        1) You may type to enter text in any text box. 
        2) Use the tab key to change between buttons on the bottom
        3) When selecting a file or a folder, a selection screen will appear. You can use tab to move to each pane and 
        \t- You should use the spacebar to select files/folders. 
        \tIt is important that you DO NOT HIT OK until you have used the space bar to select the desired file or folder and see its name in the box 
        4) A help button will appear when help is available. Use tab to select and enter to press it 
        5) Pressing cancel at any time will terminate the program completely and you will have to start over. 

        Would you like to continue using this program?
        ''')
    args = get_interactive_args()

    if args.file:
        destination = args.output
        resize_image(args.file, args.width, destination)
        messagebox.showinfo("Done", "Finished shrinking \n{}\ninto\n{}".format(args.file, args.output))
    elif args.directory:
        outdir = args.output
        yesorno(title="Ready to begin shrinking",
                text="""
                Shrinking files in {}
                Shrunken image files will have their original name + '_shrunk_{}' at the end
                Shrunked images will be written in {}
                
                If files matching this pattern exist, they WILL BE OVERWRITTEN
                
                Continue?""".format(
                    args.directory, args.width, outdir))
        filenames = os.listdir(args.directory)
        total = len(filenames)
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
                g.update(i, 'Shrinking {}'.format(path))
                new_name = rename_shrunk(path, args.width)
                new_file = os.path.join(outdir, new_name)
                result = resize_image(filename, args.width, new_file)
                if not result:
                    g.update(i, text='Error: Could not read image named: {}'.format(filename))
            g.update(total, text="Done")
            g.done()
        thread = threading.Thread(daemon=True, target=target)
        thread.start()
        g.start()

    else:
        messagebox.showerror("No Selection", "No File or Folder was selected")


if __name__ == '__main__':
    main()
