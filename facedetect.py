# from https://machinelearningmastery.com/how-to-perform-face-detection-with-classical-and-deep-learning-methods-in-python-with-keras/
# https://www.geeksforgeeks.org/python-opencv-cv2-imwrite-method/
# https://stackoverflow.com/questions/15589517/how-to-crop-an-image-in-opencv-using-python
# https://docs.opencv.org/3.1.0/d7/d8b/tutorial_py_face_detection.html#gsc.tab=0

import numpy as np
import cv2
from typing import List, Tuple, Callable
from tqdm import tqdm
import os.path
import math
import sys
# import argparse
# import pprint

verbose = False

# load the pre-trained model
classifier = cv2.CascadeClassifier('model/haarcascade_frontalface_default.xml')


# def parse_args():
#     ap = argparse.ArgumentParser()
#     gp = ap.add_mutually_exclusive_group(required=True)
#     gp.add_argument('-d', '--directory', help='Detect faces and crop all photos in the given directory')
#     gp.add_argument('-f', '--file', help='Detect faces and crop the given photo')
#     ap.add_argument('-m', '--max', type=int, default=5, help='The maximum number of faces to extract. Defaults to 5. Use 0 for no limit')
#     ap.add_argument('-b', '--box', action='store_true', help='Do not crop, but draw the bounding box to the photo and write that out')
#     ap.add_argument('-s', '--show', action='store_true', help='Show each image as it is being output')
#     ap.add_argument('-n', '--nowrite', action='store_true', help='Perform transformations but do not write files. Implies -s.')
#     ap.add_argument('-v', '--verbose', action='store_true', help='Produce incremental output for monitoring')
#     ap.add_argument('-q', '--quiet', action='store_true', help='Produce no ouptut unless there is an exception')
#     ap.add_argument('-z', '--squeeze', action='store_true', help='Fit the output boxes to the ASPECT ratio for Rediker by growing boxes until they are the approximate aspect ratio of 190x237 but not NOT actually change the size')
#     gp = ap.add_mutually_exclusive_group()
#     gp.add_argument('-p', '--pad', action='store_true', help='Fit the output boxes to the 190x237 shape for Rediker by adding white padding and shrinking. implies -r')
#     gp.add_argument('-r', '--resize', action='store_true', help='Resize the image to be 190x237 plainly as it is. Can be combined with -z to prevent excess distortion when resizing')
#     return ap.parse_args()


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

    return tuple(int(i) for i in (x1, y1, x2, y2))


class NotAnImageError(OSError):
    pass


def bounding_boxes_for_id(
        pixels: 'cv2.image',
        classifier: 'cv2.CascadeClassifier',
        min_box_width: int = 0,
        min_box_height: int = 0
) -> List[Tuple[int, int, int, int]]:
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
    if pixels is None:
        raise NotAnImageError
    # perform face detection
    bboxes = classifier.detectMultiScale(pixels)
    # print bounding box for each detected face
    faces = []
    for i in range(len(bboxes)):
        box = bboxes[i]
        x, y, width, height = box
        if width < min_box_width or height < min_box_height:
            continue
        x1, y1, x2, y2 = x, y, x + width, y + height
        x1, y1, x2, y2 = x1 - (width // 3), y1 - (height // 2), x2 + (width // 3), y2 + (height // 2)
        x1 = lowest(x1, 0)
        y1 = lowest(y1, 0)
        x2 = highest(x2, pixels.shape[1] - 1)
        y2 = highest(y2, pixels.shape[0] - 1)
        faces.append((x1, y1, x2, y2))
    return faces


def on_each_box2(pixels: 'cv2.image', boxes: List[Tuple[int, int, int, int]], transform: Callable[['cv2.image', int, int, int, int], 'cv2.image']) -> List['cv2.image']:
    image = pixels
    results = []
    for i in range(len(boxes)):
        (x1, y1, x2, y2) = boxes[i]
        result = transform(image, x1, y1, x2, y2)
        results.append(result)
    return results


class FDOptions:
    def __init__(self, pad=True, resize=True, multiplier=1) -> None:
        self.pad = pad
        self.resize = resize
        self.multiplier = multiplier


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


def transpose(pair):
    return pair[1], pair[0]


def crop_to_boxes2(image: 'cv2.image', boxes: List[Tuple[int, int, int, int]], options: FDOptions = FDOptions()) -> List['cv2.image']:
    dest_size = (190 * options.multiplier, 237 * options. multiplier)

    def cropnshrink(img, x1, y1, x2, y2):
        i = img[y1:y2, x1:x2]
        if options.pad:
            i = pad_image(i, transpose(dest_size))
            i = cv2.resize(i, dest_size)
        elif options.resize:
            i = cv2.resize(i, dest_size)
        return i

    return on_each_box2(image, boxes, cropnshrink)


def draw_bounding_box2(image: 'cv2.image',  boxes: List[Tuple[int, int, int, int]]) -> 'List[cv2.image]':
    def draw_rect(img, x1, y1, x2, y2, color=(0, 0, 255)):
        image = img.copy()
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        awidth = math.dist((x1, y1), (x2, y1))
        aheight = math.dist((x1, y1), (x1, y2))
        aratio = awidth / aheight
        t = ((x1, y1), (x2, y2), (aratio))
        cv2.putText(image, f'{t!r}', (x1, y1 + 10), cv2.FONT_HERSHEY_PLAIN, 4, color)
        return image

    return on_each_box2(image, boxes, draw_rect)


def main_for_file(pixels, drawOnly: bool = False, limit: int = 5, squeeze: bool = True, pad: bool = True, resize: bool = True, multiplier: int = 1, min_box_width: int = 0, min_box_height: int = 0):
    # load the photograph
    boxes = bounding_boxes_for_id(pixels, classifier, min_box_width, min_box_height)
    for i in range(len(boxes)):
        # fit the boxes to an aspect ratio without loosing information (expand boxes)
        if squeeze:
            boxes[i] = smoosh_box(boxes[i])

    if len(boxes) > limit:
        print("[*] Warning: limit was {} but found {} faces. Taking first {}".format(limit, len(boxes), limit), file=sys.stderr)
        boxes = boxes[:limit]
    if len(boxes) == 0:
        print('[!] Error: No faces found')
        return []
    if drawOnly:
        return draw_bounding_box2(pixels, boxes)
    else:
        return crop_to_boxes2(pixels, boxes, FDOptions(pad=pad, resize=resize, multiplier=multiplier))


def vsay(msg, end="\n"):
    if verbose:
        print(msg, end=end)


# def main():
#     global verbose
#     options = parse_args()
#     verbose = options.verbose
#     subdir = 'marked' if options.box else 'cropped'
#     if options.directory:
#         os.chdir(options.directory)
#         ensure_dir(os.path.join(options.directory, subdir))
#         vsay(f'[-] Reading files in {options.directory}...')
#         if options.verbose or options.quiet:
#             iterator = os.listdir('.')
#         else:
#             print(f'Working on files in: "{options.directory}"...')
#             iterator = tqdm(os.listdir('.'))
#         for filename in iterator:
#             vsay(f'[-] Reading file {filename}')
#             name, ext = get_name_and_extension(filename)
#             if not os.path.isdir(filename):
#                 try:
#                     pixels = cv2.imread(filename)
#                     pixels = main_for_file(pixels, drawOnly=options.box, limit=options.max, squeeze=options.squeeze)
#                     if not options.nowrite:
#                         for idx, box in enumerate(pixels):
#                             if idx >= options.max:
#                                 print("Too many boxes. Stopping")
#                                 break
#                             cv2.imwrite(os.path.join(options.directory, subdir, '{}-box{}.{}'.format(name, idx + 1, ext)), box)
#                 except Exception:
#                     print("Failed to operate on file '{}'. \nSettings: {}\n\n".format(filename, options))
#                     raise
#             else:
#                 vsay(f"[*] Skipping {filename}: is directory.")
#             vsay('*=' * 2 + f'Done with "{filename}"' + '*=' * 2)
#         vsay('=*' * 40)
#         vsay(f'Done with directory "{options.directory}"'.center(80))
#         vsay('=*' * 40)
#     elif options.file:
#         path, filename = path_to_components(options.file)
#         name, ext = get_name_and_extension(filename)
#         ensure_dir(os.path.join(path, subdir))
#         vsay(f"[-] Processing file: {options.file}...")
#         try:
#             pixels = cv2.imread(options.file)
#             pixels = main_for_file(pixels, drawOnly=options.box, limit=options.max, squeeze=options.squeeze)
#             if not options.nowrite:
#                 for idx, box in enumerate(pixels):
#                     if idx >= options.max:
#                         print("Too many boxes. Stopping")
#                         break
#                     cv2.imwrite(os.path.join(path, subdir, '{}-box{}.{}'.format(name, idx + 1, ext)), box)
#         except Exception:
#             print("Failed to operate on file '{}'. \nSettings: {}\n\n".format(options.file, options))
#             raise
#         vsay('*=' * 2 + f'Done with "{options.file}"' + '*=' * 2)


# if __name__ == '__main__':
#     exit(main())
