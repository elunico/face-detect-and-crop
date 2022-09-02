# from https://machinelearningmastery.com/how-to-perform-face-detection-with-classical-and-deep-learning-methods-in-python-with-keras/
# https://www.geeksforgeeks.org/python-opencv-cv2-imwrite-method/
# https://stackoverflow.com/questions/15589517/how-to-crop-an-image-in-opencv-using-python
# https://docs.opencv.org/3.1.0/d7/d8b/tutorial_py_face_detection.html#gsc.tab=0

import argparse
import os.path
import sys
from typing import List, Tuple, Callable

import cv2
import math

from utils import *

verbose = False

# load the pre-trained model
classifier = cv2.CascadeClassifier('model/haarcascade_frontalface_default.xml')

global options


def parse_args():
    global options

    options = argparse.Namespace(**{
        'file': None,
        'directory': None,
        'output': None,
        'width': None,
        'max': None,
        'box': None,
        'show': None,
        'nowrite': None,
        'verbose': None,
        'quiet': None,
        'squeeze': None,
        'pad': None,
        'resize': None,
    })

    choice = show_dialog(d.menu, text='Do you want to run the program on all the items of a folder or a single file?',
                         choices=[('dir', 'Entire Folder'), ('file', 'A Single File')])

    if choice == 'dir':
        directory = show_dialog(d.dselect, filepath=os.getcwd(),
                                title='Choose the folder containing the images to process')
        setattr(options, 'directory', directory)
    else:
        file = show_dialog(d.fselect, filepath=os.getcwd(), title="Choose the image file to process")
        setattr(options, 'file', file)

    max_faces = dialog_get_int('Enter the maximum number of faces to extract or 0 for no limit (Default 5)', default=5)
    setattr(options, 'max', (max_faces))

    action = show_dialog(d.menu, text='Choose options for this program run', width=box_width, height=box_height,
                         choices=[
                           ('box', 'Write out 1 image per face with a box around the face'),
                           ('crop', 'Write out 1 cropped to face image per face detected in the image'),
                           ('resize', 'Take same as \'crop\' but also resize the resulting cropped image to 190x237')
                       ], help_text='''
                       box
                           This option will find faces in the image and write out one image per face. In each of the images it writes, a red box will be drawn around the area it detected as a face. No other alterations to the image will take place
                       
                       crop 
                           This option will find faces in the image and write out one new image per face, where the image is cropped to the bounding box of the detected face. No other alterations to the image take place
                       
                       resize
                           This option is the same as "crop" but it will also take the image that results from the "crop" option and resize to tbe 190x237 pixles, the exact size of a photo that Rediker uses
                       ''')

    setattr(options, action, True)

    if 'resize' in action:
        size_change_option = show_dialog(d.menu, text='Choose a resizing method', choices=[
            ('pad', 'Pad the image to the correct proportions then shrink to 190x237'),
            ('plain', 'Stretch or squash the image to fit it to the 190x237 aspect ratio')
        ], help_text='''
        pad 
            This option takes the image and fits a plain white border around it. It will pad the left and right or top and bottom with white pixels until the aspect ratio of 190/x237 is reached. The image will then be shrunk to 190x237 so that no stretching or squashing will occur
        
        plain
            This option does not alter the cropped image and simply resizes it to 190x237 allowing it to be squashed or stretched as needed to fit those dimensions
        ''')
        setattr(options, size_change_option, True)

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


def main():
    show_dialog(d.yesno, title="Welcome to facedetect", text='''
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
    verbose = options.verbose
    if options.directory:
        os.chdir(options.directory)
        show_dialog(d.yesno, title="{} ready".format(options.directory), text="Program is ready to detect faces in {}\nResults will be placed in a sub folder. Any images from a previous run of this program WILL BE OVERWRITTEN\nContinue?".format(options.directory))

        show_dialog(d.infobox, text=f'Reading files in {options.directory}...')
        if options.verbose or options.quiet:
            iterator = os.listdir('.')
        else:
            # print(f'Working on files in: "{options.directory}"...')
            iterator = (os.listdir('.'))
        total = len(iterator)
        d.gauge_start('Working on files in {}'.format(options.directory))
        for (i, filename) in enumerate(iterator):
            # vsay(f'[-] Reading file {filename}')
            d.gauge_update(percentFor(i, total), text='Reading file {}'.format(filename), update_text=True)
            if not os.path.isdir(filename):
                try:
                    msg = main_for_file(filename, drawOnly=options.box, show=options.show or options.nowrite,
                                        limit=options.max, write=not options.nowrite)
                    if msg is not None:
                        d.gauge_update(percentFor(i + 1, total), msg, update_text=True)
                except Exception:
                    d.gauge_update(percentFor(i + 1, total),
                                   "Failed to operate on file '{}'. \nSettings: {}\n\n".format(filename, options),
                                   update_text=True)
                    raise
            else:
                d.gauge_update(percentFor(i + 1, total), f"Skipping {filename}: is directory.", update_text=True)
            d.gauge_update(percentFor(i + 1, total), f'Done with "{filename}"' + '*=' * 2, update_text=True)
        d.gauge_update(100, f'Done with "{options.directory}"', update_text=True)
        d.gauge_stop()
    elif options.file:
        # vsay(f"[-] Processing file: {options.file}...")
        show_dialog(d.yesno, title="{} ready".format(options.directory), text="Program is ready to detect faces in {}. Results will be placed in a sub folder. Any images from a previous run of this program WILL BE OVERWRITTEN\nContinue?".format(options.file))
        show_dialog(d.infobox, text=f"Processing file: {options.file}...")
        main_for_file(options.file, drawOnly=options.box, show=options.show or options.nowrite,
                      limit=options.max, write=not options.nowrite)
        show_dialog(d.infobox, text=f'Done with "{options.file}"')


if __name__ == '__main__':
    exit(main())
