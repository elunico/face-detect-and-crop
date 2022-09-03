# from https://machinelearningmastery.com/how-to-perform-face-detection-with-classical-and-deep-learning-methods-in-python-with-keras/
# https://www.geeksforgeeks.org/python-opencv-cv2-imwrite-method/
# https://stackoverflow.com/questions/15589517/how-to-crop-an-image-in-opencv-using-python
# https://docs.opencv.org/3.1.0/d7/d8b/tutorial_py_face_detection.html#gsc.tab=0
import argparse
import math
import os.path
import sys
import threading
from tkinter import *
from tkinter import filedialog, StringVar
from tkinter import messagebox
from typing import List, Tuple, Callable, Optional
from guitils import GUIProgress

import cv2

verbose = False

# load the pre-trained model
classifier = cv2.CascadeClassifier(os.path.join(sys._MEIPASS, 'haarcascade_frontalface_default.xml'))


class GetParameters:

    def spawn_window(self):
        window = Tk()
        self.windows.append(window)
        return window

    def __init__(self):
        self.windows = []
        self.namespace = argparse.Namespace(**{
            'file': None,
            'directory': None,
            'max': None,
            'box': None,
            'show': None,
            'resize': None,
            'plain': None,
            'pad': None,
        })
        t = self.spawn_window()
        t.title('Face Extractor Program')
        intro = Label(t,
                      text="Welcome to the face extractor program\nThis program will allow you to extract faces from images.\nSelect below to start")
        db = Button(t, text="Run on a whole directory", command=self.run_directory)
        fb = Button(t, text="Run on a single file", command=self.run_file)
        intro.pack()
        fb.pack()
        db.pack()
        t.mainloop()

    def choose_dir(self, root, container: StringVar) -> Optional[StringVar]:
        dir = filedialog.askdirectory(initialdir=os.path.realpath('.'), title="Choose images directory")
        if dir == '':
            return
        container.set(dir)
        self.namespace.directory = dir
        container.was_set = True
        root.update()
        return container

    def get_resize_strategy(self):
        def help():
            helpwin = self.spawn_window()
            helpwin.title('Help for Operation Parameters')
            label = Label(helpwin, text='''
            pad 
                This option takes the image and fits a plain white border around it. 
                It will pad the left and right or top and bottom with white pixels until the aspect ratio of 190/x237 is reached. 
                The image will then be shrunk to 190x237 so that no stretching or squashing will occur
            
            plain
                This option does not alter the cropped image and simply resizes it to 190x237 
                allowing it to be squashed or stretched as needed to fit those dimensions
            ''')
            label.pack()
            helpwin.mainloop()

        window = self.spawn_window()
        window.title("Choose resize strategy")

        label = Label(window, text='Choose the resize strategy')

        choices = ['pad', 'plain']
        variable = StringVar(window)
        variable.set('pad')

        w = OptionMenu(window, variable, *choices)
        help = Button(window, text="Show Help", command=help)
        go = Button(window, text="Go", command=lambda: self.finalize(variable))
        label.pack()
        w.pack()
        go.pack()
        help.pack()
        window.mainloop()

    def run_dir_action(self, actionvar, facevar):
        try:
            facevar.get()
        except Exception:
            return
        setattr(self.namespace, 'max', facevar.get())
        setattr(self.namespace, actionvar.get(), True)
        if actionvar.get() == 'resize':
            self.get_resize_strategy()
        else:
            self.finalize(None)

    def select_parameters(self, container):
        def help():
            helpwin = self.spawn_window()
            helpwin.title('Help for Operation Parameters')
            label = Label(helpwin, text='''
    box
       This option will find faces in the image and write out one image per face. 
       In each of the images it writes, a red box will be drawn around the area it detected as a face. 
       No other alterations to the image will take place
    
    crop 
       This option will find faces in the image and write out one new image per face, 
       where the image is cropped to the bounding box of the detected face. 
       No other alterations to the image take place
    
    resize
       This option is the same as "crop" but it will also take the image that results from the "crop" option and 
       resize to tbe 190x237 pixles, the exact size of a photo that Rediker uses
    ''')
            label.pack()
            helpwin.mainloop()

        if not container.was_set:
            messagebox.showerror('No Selection', 'You must select a file/directory before continuing')
            return

        window = self.spawn_window()
        window.title('Select Operation Parameters')

        label = Label(window, text='Choose the operation to perform on each image')

        choices = ['box', 'crop', 'resize']
        actionvar = StringVar(window)
        actionvar.set('resize')

        w = OptionMenu(window, actionvar, *choices)

        label2 = Label(window, text="Specify the max number of faces the \nprogram should look for per image")
        facevar = IntVar(window)
        facevar.set(5)
        faceentry = Entry(window, textvariable=facevar)

        help = Button(window, text="Show Help", command=help)
        go = Button(window, text="Go", command=lambda: self.run_dir_action(actionvar, facevar))
        label.pack()
        w.pack()
        label2.pack()
        faceentry.pack()
        go.pack()
        help.pack()
        window.mainloop()

    def run_directory(self):
        root = self.spawn_window()
        root.title('Choose directory for source images')

        l = Label(root, text="Select the directory containing the images to process")
        container = StringVar(root)
        container.was_set = False
        dlabel = Label(root, textvariable=container)
        select = Button(root, text="Select Dir", command=lambda: self.choose_dir(root, container))
        button = Button(root, text='Next', command=lambda: self.select_parameters(container))
        l.pack()
        dlabel.pack()
        select.pack()
        button.pack()
        root.mainloop()

    def choose_file(self, parent, container):
        file = filedialog.askopenfilename(initialdir=os.path.realpath('.'), title="Choose images directory")
        if file == '':
            return
        container.set(file)
        self.namespace.file = file
        container.was_set = True
        parent.update()
        return container

    def run_file(self):
        root = self.spawn_window()
        root.title('Choose file for processing')

        l = Label(root, text="Select the file that you want to process")
        container = StringVar(root)
        container.was_set = False
        dlabel = Label(root, textvariable=container)
        select = Button(root, text="Select File", command=lambda: self.choose_file(root, container))
        button = Button(root, text='Next', command=lambda: self.select_parameters(container))
        l.pack()
        dlabel.pack()
        select.pack()
        button.pack()
        root.mainloop()

    def finalize(self, resize_strategy):
        if resize_strategy is not None:
            setattr(self.namespace, resize_strategy.get(), True)

        for window in self.windows:
            print(window)
            try:
                window.destroy()
            except Exception:
                pass


def parse_args():
    global options
    options = GetParameters().namespace
    return options


def get_name_and_extension(filename):
    if '.' in filename:
        *name, ext = filename.rsplit('.')
        ext = '.' + ext
        name = '.'.join(name)
    else:
        name, ext = filename, ''
    return name, ext


def path_to_components(path):
    sep = os.path.sep
    parts = os.path.split(path)
    if len(parts) == 1:
        return '', sep + parts[0] if path.startswith(sep) else '', parts[0]
    directory = sep.join(parts[:-1])
    directory = sep + directory if path.startswith(sep) else directory
    return directory, parts[-1]


def ensure_dir(dirpath):
    if not os.path.isdir(dirpath) and not os.path.exists(dirpath):
        os.mkdir(dirpath)


def highest(value, limit):
    if value > limit:
        value = limit
    return value


def lowest(value, limit):
    if value < limit:
        value = limit
    return value


def printing(arg):
    print(arg)
    return arg


def bounding_boxes_for_id(path: str, classifier: 'cv2.CascadeClassifier') -> List[Tuple[int, int, int, int]]:
    '''
    This function receives a path and a face classifier and returns a list
    of 4-ples that contain bounding boxes around faces suitable for use in
    ID Photos (extra space around the face)

    It returns (x1, y1, x2, y2) of the bounding box for the face which is larger
    than the bounding box returned by the classifier by 67% in the x direction
    and 100% in the y direction than that which is returned by the classifier

    The a List of Tuple is returned because the classifier may detect more than
    1 face in the image

    WARNING: THIS WILL NOT REMOVE bounding boxes less than 10 pixels in EITHER height or width or both
    '''
    # load the photograph
    pixels = cv2.imread(path)
    # perform face detection
    bboxes = classifier.detectMultiScale(pixels)
    # print bounding box for each detected face
    faces = []
    for i in range(len(bboxes)):
        box = bboxes[i]
        x, y, width, height = box
        # if width < 10 or height < 10:
        # continue
        x1, y1, x2, y2 = x, y, x + width, y + height
        x1, y1, x2, y2 = x1 - (width // 3), y1 - (height // 2), x2 + (width // 3), y2 + (height // 2)
        x1 = lowest(x1, 0)
        y1 = lowest(y1, 0)
        x2 = highest(x2, pixels.shape[1] - 1)
        y2 = highest(y2, pixels.shape[0] - 1)
        faces.append((x1, y1, x2, y2))
    return faces


def _on_each_box(
        indir: str,
        name: str,
        ext: str,
        boxes: List[Tuple[int, int, int, int]],
        outdir: str,
        transform: Callable[['cv2.image', int, int, int, int], 'cv2.image'],
        show: bool = False,
        write: bool = True
) -> 'List[cv2.image]':
    vsay(f'[-] Reading image from {os.path.join(indir, name + ext)}...')
    image = cv2.imread(os.path.join(indir, name + ext))
    if image is None:
        vsay(f'[*] Got empty image from path {os.path.join(indir, name + ext)}')
    else:
        vsay(f'[-] Got image with dimensions: {image.shape}...')
    results = []
    for i in range(len(boxes)):
        vsay(f'[-] Processing box {i} of {len(boxes)}...')
        (x1, y1, x2, y2) = boxes[i]
        result = transform(image, x1, y1, x2, y2)
        results.append(result)
        if show:
            cv2.imshow('Result', result)
            cv2.waitKey(0)
        outfile = '{}/{}_face{}{}'.format(outdir, name, i, ext)
        if write:
            try:
                vsay(f'[-] Writing result to {outfile}...')
                cv2.imwrite(outfile, result)
            except cv2.error as e:
                print("[!] Could not write image called {}".format(outfile), file=sys.stderr)
                print(e.msg, file=sys.stderr)
    return results


def calculate_padding(img, ratio_size):
    h, w = img.shape[:2]
    th, tw = ratio_size
    goal_aspect = tw / th
    current_aspect = w / h

    padding_height = 0
    padding_width = 0
    if goal_aspect > current_aspect:
        while goal_aspect > current_aspect:
            padding_width += 1
            current_aspect = (w + padding_width) / (h + padding_height)

    if goal_aspect < current_aspect:
        while goal_aspect < current_aspect:
            padding_height += 1
            current_aspect = (w + padding_width) / (h + padding_height)

    pad_left, pad_right = (padding_width // 2), ((padding_width // 2) + (padding_width % 2))
    pad_top, pad_bottom = (padding_height // 2), ((padding_height // 2) + (padding_height % 2))

    return pad_left, pad_right, pad_top, pad_bottom


def pad_image(img, ratio_size, pad_color=(255, 255, 255)):
    pad_left, pad_right, pad_top, pad_bottom = calculate_padding(img, ratio_size)
    scaled_img = cv2.copyMakeBorder(img, pad_top, pad_bottom, pad_left, pad_right, borderType=cv2.BORDER_CONSTANT,
                                    value=pad_color)
    return scaled_img


def crop_to_boxes(path: str, boxes: List[Tuple[int, int, int, int]], show: bool = False,
                  write: bool = True) -> 'List[cv2.image]':
    '''
    This function takes a filename of an image and a list of bounding boxes
    to crop to. It crops the image called filename to the places specified
    by the bounding box. It writes the output to cropped/%filename_face%d.%s
    creating the directory cropped if necessary. In this face %filename
    is the name of the file WITHOUT the extension %d is the number starting
    at 0 of the bounding box being cropped to and %s is the extension from the
    filename

    Bounding box should be a 4-ple of (x1, y1, x2, y2) and boxes should be a
    list of bounding box
    '''

    def cropnshrink(img, x1, y1, x2, y2):
        i = img[y1:y2, x1:x2]
        if options.pad:
            i = pad_image(i, (237, 190))
            i = cv2.resize(i, (190, 237))
        elif options.resize:
            i = cv2.resize(i, (190, 237))
        return i

    directory, filename = path_to_components(path)
    name, ext = get_name_and_extension(filename)
    if write:
        vsay(f'[-] Ensuring the existance of {os.path.join(directory, "cropped")} or createing it.')
        ensure_dir(os.path.join(directory, 'cropped'))

    _on_each_box(directory, name, ext, boxes, os.path.join(directory, 'cropped'), cropnshrink, show, write)


def draw_bounding_box(path: str, boxes: List[Tuple[int, int, int, int]], show: bool = False,
                      write: bool = True) -> 'List[cv2.image]':
    '''
    This function takes a filename of an image and a list of bounding boxes
    It draws a rectangle around the given bounding box and writes the image out
    to marked/%filename_face%d.%s creating the directory marked if necessary. In this face %filename
    is the name of the file WITHOUT the extension %d is the number starting
    at 0 of the bounding box being cropped to and %s is the extension from the
    filename

    Bounding box should be a 4-ple of (x1, y1, x2, y2) and boxes should be a
    list of bounding box
    '''
    directory, filename = path_to_components(path)
    name, ext = get_name_and_extension(filename)
    if write:
        vsay(f'[-] Ensuring the existance of {os.path.join(directory, "marked")} or createing it.')
        ensure_dir(os.path.join(directory, 'marked'))

    def draw_rect(img, x1, y1, x2, y2, color=(0, 0, 255)):
        image = img.copy()
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        awidth = math.dist((x1, y1), (x2, y1))
        aheight = math.dist((x1, y1), (x1, y2))
        aratio = awidth / aheight
        t = ((x1, y1), (x2, y2), (aratio))
        cv2.putText(image, f'{t!r}', (x1, y1 + 10), cv2.FONT_HERSHEY_PLAIN, 4, color)
        return image

    _on_each_box(directory, name, ext, boxes, os.path.join(directory, 'marked'), draw_rect, show, write)


def test():
    for filename in range(1, 12):
        name = 'test{}.png'.format(filename)
        boxes = bounding_boxes_for_id(name, classifier)
        draw_bounding_box(name, boxes)


def main_for_file(path, drawOnly: bool = False, show: bool = False, limit: int = 5, write: bool = True):
    vsay(f"[-] Computing bounding boxes for {path}...")
    boxes = bounding_boxes_for_id(path, classifier)

    # vsay(f"[-] Found {len(boxes)} faces in file {path}.")
    msg = None
    if 0 < limit < len(boxes):
        msg = "[*] Warning: file {} -> limit was {} but found {} faces. Taking first {}".format(path, limit, len(boxes),
                                                                                                limit)
        boxes = boxes[:limit]
    if len(boxes) == 0:
        return '[!] Error: No faces found in {}'.format(path)
    if drawOnly:
        # vsay(f'[-] Drawing bounding boxes for {path}...')
        draw_bounding_box(path, boxes, show, write)
    else:
        # vsay(f'[-] Cropping to bounding boxes for {path}...')
        crop_to_boxes(path, boxes, show, write)

    return msg


def vsay(msg, end="\n"):
    if verbose:
        print(msg, end=end)


def percentFor(i, total):
    return int((i / total) * 100)


def yesorno(title, text):
    window = Tk()
    window.title(title)
    # window.attributes('-disabled', True)
    label = Label(window, text=text)
    result = {'status': 'cancel'}
    ok = Button(window, text="OK", command=lambda: result.__setitem__('status', 'ok') or window.destroy())
    cancel = Button(window, text="Cancel", command=lambda: result.__setitem__('status', 'cancel') or window.destroy())
    label.pack()
    ok.pack()
    cancel.pack()
    window.mainloop()
    if result['status'] == 'cancel':
        raise SystemExit()


def infobox(title='', text=''):
    messagebox.showinfo(title, text)


def main():
    yesorno(title="Welcome to facedetect", text='''
    This program will help you extract faces from an image or a folder of many images.
    You can have the program draw boxes around faces, show but not write out the final images, crop, and even resize
    the cropped images.

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
    global verbose, options
    options = parse_args()
    if options.directory:
        os.chdir(options.directory)
        yesorno(title="{} ready".format(options.directory),
                text="Program is ready to detect faces in {}\nResults will be placed in a sub folder. Any images from a previous run of this program WILL BE OVERWRITTEN\nContinue?".format(
                    options.directory))

        iterator = (os.listdir('.'))
        total = len(iterator)
        g = GUIProgress('Working on {}'.format(options.directory), total=total,
                        title="Face Extractor Program Running...",
                        main_label='Running face extractor on {}'.format(options.directory))

        def closure():
            for (i, filename) in enumerate(iterator):
                g.update(i, text='Reading file {}'.format(filename))
                if not os.path.isdir(filename):
                    try:
                        print('Doing {}'.format(filename))
                        msg = main_for_file(filename, drawOnly=options.box, show=options.show,
                                            limit=options.max)

                        if msg is not None:
                            pass
                            g.update(i, msg)
                    except Exception as e:
                        g.update(0, 'A critical error has occurred on file {}'.format(filename))
                        g.done()
                        infobox(title="ERROR", text="An error has occurred processing {}:\n{}".format(filename, str(e)))
                        raise
                else:
                    pass

            print("Done")
            g.done()

        thread = threading.Thread(daemon=True, target=closure)
        thread.start()
        g.start()

        infobox(title="Finished!", text="The program has completed processing {}".format(options.directory))
    elif options.file:
        yesorno(title="{} ready".format(options.file),
                text="Program is ready to detect faces in {}. Results will be placed in a sub folder. Any images from a previous run of this program WILL BE OVERWRITTEN\nContinue?".format(
                    options.file))

        label_text = 'Processing file {}'.format(options.file)
        g = GUIProgress(label_text, 1, label_text, label_text)
        def closure():
            main_for_file(options.file, drawOnly=options.box, show=options.show,
                          limit=options.max)
            g.done()

        thread = threading.Thread(daemon=True, target=closure)
        thread.start()
        g.start()
        infobox(text=f'Done with "{options.file}"')
    # input("The program has completed. Press any key to close")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        input("There was an error. Press any key to exit")
