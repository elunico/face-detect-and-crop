# from https://machinelearningmastery.com/how-to-perform-face-detection-with-classical-and-deep-learning-methods-in-python-with-keras/
# https://www.geeksforgeeks.org/python-opencv-cv2-imwrite-method/
# https://stackoverflow.com/questions/15589517/how-to-crop-an-image-in-opencv-using-python
# https://docs.opencv.org/3.1.0/d7/d8b/tutorial_py_face_detection.html#gsc.tab=0
import argparse
import math
import os.path
import sys
import threading
import time
import uuid
from tkinter import *
from tkinter import filedialog, StringVar
from tkinter import messagebox
from typing import List, Tuple, Callable, Optional

import cv2

from guitils import GUIProgress, yesorno, infobox, SimpleContainer

verbose = False

# load the pre-trained model

search_locations = [
    os.path.join(getattr(sys, '_MEIPASS', './'), 'haarcascade_frontalface_default.xml'),
    os.path.join('model', 'haarcascade_frontalface_default.xml'),
    'haarcascade_frontalface_default.xml'
]

location = None
for i in search_locations:
    try:
        with open(i) as f:
            location = i
            break
    except (OSError, AttributeError):
        pass

if location is None:
    messagebox.showerror("Cannot find model file",
                         "The program cannot find the required model file haarcascade_frontalface_default.xml. It cannot function without this file. If you moved the application, be sure to move that file as well")
    raise SystemExit(1)

classifier = cv2.CascadeClassifier(location)


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
        locationvar = StringVar(t, '<nothing selected>')
        locationvar.was_set = False
        location = Label(t, textvariable=locationvar)
        db = Button(t, text="I have a folder full of images to process",
                    command=lambda: self.choose_target_directory(t, locationvar))
        fb = Button(t, text="I have 1 image to process", command=lambda: self.choose_target_file(t, locationvar))
        nb = Button(t, text="Next", command=lambda: self.choose_parameters(locationvar))
        intro.pack(padx=2, pady=2)
        location.pack(padx=2, pady=2)
        fb.pack(padx=2, pady=2)
        db.pack(padx=2, pady=2)
        nb.pack(padx=2, pady=2)
        t.mainloop()

    def choose_target_directory(self, root, container: StringVar) -> Optional[StringVar]:
        dir = filedialog.askdirectory(initialdir=os.path.realpath('.'), title="Choose images directory")
        if dir == '':
            return
        container.set(dir)
        self.namespace.directory = dir
        container.was_set = True
        root.update()
        return container

    def set_parameters(self, actionvar, facevar):
        try:
            facevar.get()
        except Exception:
            return
        setattr(self.namespace, 'max', facevar.get())
        action, *resize = actionvar.get().split(' ')
        if resize:
            setattr(self.namespace, 'resize', True)
            setattr(self.namespace, action, True)
        else:
            setattr(self.namespace, action, True)

        self.finalize()

    def choose_parameters(self, container):
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
    
    plain resize
       This option is the same as "crop" but it will also take the image that results from the "crop" option and 
       resize to tbe 190x237 pixles, the exact size of a photo that Rediker uses. Because this option blindly sizes the
       image to 190x237, this can cause distortions and stretching or squishing of the image. 
       
    pad resize
       This option is the same as "crop" but it will also take the image that results from the "crop" option and perform 
       two more tasks. First, it takes the image and adds white borders around the outside as needed until its aspect
       ratio is proportional to 190x237. It then shrinks the resulting image to 190x237 exactly. This prevents the 
       squishing and stretching in the plain-resize option but does waste some space with the borders
    ''')
            label.pack(padx=2, pady=2)
            helpwin.mainloop()

        if not container.was_set:
            messagebox.showerror('No Selection', 'You must select a file/directory before continuing')
            return

        window = self.spawn_window()
        window.title('Select Operation Parameters')

        label = Label(window, text='Choose the operation to perform on each image')

        choices = ['box', 'crop', 'plain resize', 'padded resize']
        actionvar = StringVar(window)
        actionvar.set('padded resize')

        w = OptionMenu(window, actionvar, *choices)

        label2 = Label(window, text="Specify the max number of faces the \nprogram should look for per image")
        facevar = IntVar(window)
        facevar.set(5)
        faceentry = Entry(window, textvariable=facevar)

        help = Button(window, text="Show Help", command=help)
        go = Button(window, text="Go", command=lambda: self.set_parameters(actionvar, facevar))
        label.pack(padx=2, pady=2)
        w.pack(padx=2, pady=2)
        label2.pack(padx=2, pady=2)
        faceentry.pack(padx=2, pady=2)
        go.pack(padx=2, pady=2)
        help.pack(padx=2, pady=2)
        window.mainloop()

    def choose_target_file(self, parent, container):
        file = filedialog.askopenfilename(initialdir=os.path.realpath('.'), title="Choose image file")
        if file == '':
            return
        container.set(file)
        self.namespace.file = file
        container.was_set = True
        parent.update()
        return container

    def finalize(self):
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


class NotAnImageError(OSError):
    pass


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
    if pixels is None:
        raise NotAnImageError
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
        raise NotAnImageError
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

    msg = None
    if 0 < limit < len(boxes):
        msg = "[*] Warning: file {} -> limit was {} but found {} faces. Taking first {}".format(path, limit, len(boxes),
                                                                                                limit)
        boxes = boxes[:limit]
    if len(boxes) == 0:
        return '[!] Error: No faces found in {}'.format(path)
    if drawOnly:
        draw_bounding_box(path, boxes, show, write)
    else:
        crop_to_boxes(path, boxes, show, write)

    return msg


def vsay(msg, end="\n"):
    if verbose:
        print(msg, end=end)


def main():
    yesorno(title='License Agreement', text='''
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
    WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
    OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
    
    If you accept the terms, you will not be asked again.
    
    Do you accept the terms?
    ''', once_identifier='9e0ecb73-7e83-4c9e-b294-59b7a2b2db5c')
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

        job_gate_variable = SimpleContainer(True)

        def closure():
            for (i, filename) in enumerate(iterator):
                if not job_gate_variable.get():
                    g.update(i, 'Job Cancelled!')
                    print("Cancelled")
                    return
                g.update(i, text='Reading file {}'.format(filename))
                if not os.path.isdir(filename):
                    try:
                        print('Doing {}'.format(filename))
                        msg = main_for_file(filename, drawOnly=options.box, show=options.show,
                                            limit=options.max)

                        if msg is not None:
                            pass
                            g.update(i, msg)
                    except NotAnImageError as e:
                        g.update(i, 'File {} is not an image. Skipping...'.format(filename))
                        time.sleep(0.1)
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
        g = GUIProgress('Working on {}'.format(options.directory), total=total,
                        title="Face Extractor Program Running...",
                        main_label='Running face extractor on {}'.format(options.directory),
                        job_gate_variable=job_gate_variable, thread=thread)
        thread.start()
        g.start()
        if job_gate_variable.get():  # if cancelled don't show the finished message
            infobox(title="Finished!", text="The program has completed processing {}".format(options.directory))
    elif options.file:
        yesorno(title="{} ready".format(options.file),
                text="Program is ready to detect faces in {}. Results will be placed in a sub folder. Any images from a previous run of this program WILL BE OVERWRITTEN\nContinue?".format(
                    options.file))

        label_text = 'Processing file {}'.format(options.file)
        g = GUIProgress(label_text, 1, label_text, label_text, None, None)

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
        messagebox.showerror('An error occurred', 'An error occurred: {}'.format(str(e)))
        print(e)
        # input("There was an error. Press any key to exit")
