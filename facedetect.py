# from https://machinelearningmastery.com/how-to-perform-face-detection-with-classical-and-deep-learning-methods-in-python-with-keras/
# https://www.geeksforgeeks.org/python-opencv-cv2-imwrite-method/
# https://stackoverflow.com/questions/15589517/how-to-crop-an-image-in-opencv-using-python
# https://docs.opencv.org/3.1.0/d7/d8b/tutorial_py_face_detection.html#gsc.tab=0

import numpy as np
import cv2
from typing import List, Tuple, Callable
from tqdm import tqdm
import os.path
import argparse
import math
import pprint

verbose = False

# load the pre-trained model
classifier = cv2.CascadeClassifier('model/haarcascade_frontalface_default.xml')

global options


def parse_args():
    ap = argparse.ArgumentParser()
    gp = ap.add_mutually_exclusive_group(required=True)
    gp.add_argument('-d', '--directory', help='Detect faces and crop all photos in the given directory')
    gp.add_argument('-f', '--file', help='Detect faces and crop the given photo')
    ap.add_argument('-m', '--max', type=int, default=5, help='The maximum number of faces to extract. Defaults to 5. Use 0 for no limit')
    ap.add_argument('-b', '--box', action='store_true', help='Do not crop, but draw the bounding box to the photo and write that out')
    ap.add_argument('-s', '--show', action='store_true', help='Show each image as it is being output')
    ap.add_argument('-n', '--nowrite', action='store_true', help='Perform transformations but do not write files. Implies -s.')
    ap.add_argument('-v', '--verbose', action='store_true', help='Produce incremental output for monitoring')
    ap.add_argument('-q', '--quiet', action='store_true', help='Produce no ouptut unless there is an exception')
    ap.add_argument('-z', '--squeeze', action='store_true', help='Fit the output boxes to the ASPECT ratio for Rediker by growing boxes until they are the approximate aspect ratio of 190x237 but not NOT actually change the size')
    gp = ap.add_mutually_exclusive_group()
    gp.add_argument('-p', '--pad', action='store_true', help='Fit the output boxes to the 190x237 shape for Rediker by adding white padding and shrinking. implies -r')
    gp.add_argument('-r', '--resize', action='store_true', help='Resize the image to be 190x237 plainly as it is. Can be combined with -z to prevent excess distortion when resizing')
    return ap.parse_args()


def get_name_and_extension(filename):
    if '.' in filename:
        *name, ext = filename.rsplit('.')
        ext = '.' + ext
        name = '.'.join(name)
    else:
        name, ext = filename, ''
    return name, ext


def path_to_components(path):
    parts = os.path.split(path)
    if len(parts) == 1:
        return '', '/' + parts[0] if path.startswith('/') else '', parts[0]
    directory = '/'.join(parts[:-1])
    directory = '/' + directory if path.startswith('/') else directory
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


def flip_flop_maker(flag=True):
    while True:
        yield flag
        flag = not flag


def printing(arg):
    print(arg)
    return arg


def smoosh_box(box):
    flipflopper = flip_flop_maker()

    dwidth = 190
    dheight = 237
    dratio = dwidth / dheight
    x1, y1, x2, y2 = box

    awidth = math.dist((x1, y1), (x2, y1))
    aheight = math.dist((x1, y1), (x1, y2))
    aratio = awidth / aheight
    if aratio > dratio:
        while aratio > dratio and (y1 - ((aheight * 0.05) + 1)) >= 0 and (y2 + ((aheight * 0.05) + 1)) <= aheight:
            if next(flipflopper):
                y2 += ((aheight * 0.05) + 1)
            else:
                y1 -= ((aheight * 0.05) + 1)
            awidth = math.dist((x1, y1), (x2, y1))
            aheight = math.dist((x1, y1), (x1, y2))
            aratio = awidth / aheight
    if aratio < dratio:
        while aratio < dratio and (x1 - ((awidth * 0.05) + 1)) >= 0 and (x2 + ((awidth * 0.05) + 1)) <= awidth:
            if next(flipflopper):
                x2 += ((awidth * 0.05) + 1)
            else:
                x1 -= ((awidth * 0.05) + 1)
            awidth = math.dist((x1, y1), (x2, y1))
            aheight = math.dist((x1, y1), (x1, y2))
            aratio = awidth / aheight

    return printing(tuple(int(i) for i in (x1, y1, x2, y2)))


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
        x1, y1, x2, y2 = x1 - (width//3), y1 - (height//2), x2 + (width//3), y2 + (height//2)
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


def padded_resize(img, size, padColor=(255, 255, 255)):
    # https://stackoverflow.com/questions/44720580/resize-image-canvas-to-maintain-square-aspect-ratio-in-python-opencv
    h, w = img.shape[:2]
    sh, sw = size

    # interpolation method
    if h > sh or w > sw:  # shrinking image
        interp = cv2.INTER_AREA
    else:  # stretching image
        interp = cv2.INTER_CUBIC

    # aspect ratio of image
    aspect = w/h  # if on Python 2, you might need to cast as a float: float(w)/h

    # compute scaling and pad sizing
    if aspect > 1:  # horizontal image
        new_w = sw
        new_h = np.round(new_w/aspect).astype(int)
        pad_vert = abs((sh-new_h)/2)
        pad_top, pad_bot = np.floor(pad_vert).astype(int), np.ceil(pad_vert).astype(int)
        pad_left, pad_right = 0, 0
    elif aspect < 1:  # vertical image
        new_h = sh
        new_w = np.round(new_h*aspect).astype(int)
        pad_horz = abs((sw-new_w)/2)
        pad_left, pad_right = np.floor(pad_horz).astype(int), np.ceil(pad_horz).astype(int)
        pad_top, pad_bot = 0, 0
    else:  # square image
        new_h, new_w = sh, sw
        pad_left, pad_right, pad_top, pad_bot = 0, 0, 0, 0

    # set pad color
    if len(img.shape) == 3 and not isinstance(padColor, (list, tuple, np.ndarray)):  # color image but only one color provided
        padColor = [padColor]*3

    # scale and pad
    scaled_img = cv2.resize(img, (new_w, new_h), interpolation=interp)
    scaled_img = cv2.copyMakeBorder(scaled_img, pad_top, pad_bot, pad_left, pad_right, borderType=cv2.BORDER_CONSTANT, value=padColor)

    return scaled_img


def crop_to_boxes(path: str, boxes: List[Tuple[int, int, int, int]], show: bool = False, write: bool = True) -> 'List[cv2.image]':
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
            i = padded_resize(i, (237, 190))
        elif options.resize:
            i = cv2.resize(i, (190, 237))
        return i

    directory, filename = path_to_components(path)
    name, ext = get_name_and_extension(filename)
    if write:
        vsay(f'[-] Ensuring the existance of {os.path.join(directory, "cropped")} or createing it.')
        ensure_dir(os.path.join(directory, 'cropped'))

    _on_each_box(directory, name, ext, boxes, os.path.join(directory, 'cropped'), cropnshrink, show, write)


def draw_bounding_box(path: str, boxes: List[Tuple[int, int, int, int]], show: bool = False, write: bool = True) -> 'List[cv2.image]':
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
    for i in range(len(boxes)):
        # fit the boxes to an aspect ratio without loosing information (expand boxes)
        if options.squeeze:
            boxes[i] = smoosh_box(boxes[i])

    vsay(f"[-] Found {len(boxes)} faces in file {path}.")
    if len(boxes) > limit:
        print("[*] Warning: file {} -> limit was {} but found {} faces. Taking first {}".format(path, limit, len(boxes), limit), file=sys.stderr)
        boxes = boxes[:limit]
    if len(boxes) == 0:
        print('[!] Error: No faces found in {}'.format(path))
    if drawOnly:
        vsay(f'[-] Drawing bounding boxes for {path}...')
        draw_bounding_box(path, boxes, show, write)
    else:
        vsay(f'[-] Cropping to bounding boxes for {path}...')
        crop_to_boxes(path, boxes, show, write)


def vsay(msg, end="\n"):
    if verbose:
        print(msg, end=end)


def main():
    global verbose, options
    options = parse_args()
    verbose = options.verbose
    limit = options.max
    if options.directory:
        os.chdir(options.directory)
        vsay(f'[-] Reading files in {options.directory}...')
        if options.verbose or options.quiet:
            iterator = os.listdir('.')
        else:
            print(f'Working on files in: "{options.directory}"...')
            iterator = tqdm(os.listdir('.'))
        for filename in iterator:
            vsay(f'[-] Reading file {filename}')
            if not os.path.isdir(filename):
                try:
                    main_for_file(filename, options.box, options.show or options.nowrite, options.max, not options.nowrite)
                except Exception:
                    print("Failed to operate on file '{}'. \nSettings: {}\n\n".format(filename, options))
                    raise
            else:
                vsay(f"[*] Skipping {filename}: is directory.")
            vsay('*=' * 2 + f'Done with "{filename}"' + '*=' * 2)
        vsay('=*' * 40)
        vsay(f'Done with directory "{options.directory}"'.center(80))
        vsay('=*' * 40)
    elif options.file:
        vsay(f"[-] Processing file: {options.file}...")
        main_for_file(options.file, options.box, options.show or options.nowrite, options.max, not options.nowrite)
        vsay('*=' * 2 + f'Done with "{filename}"' + '*=' * 2)


if __name__ == '__main__':
    exit(main())
