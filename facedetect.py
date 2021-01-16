# from https://machinelearningmastery.com/how-to-perform-face-detection-with-classical-and-deep-learning-methods-in-python-with-keras/
# https://www.geeksforgeeks.org/python-opencv-cv2-imwrite-method/
# https://stackoverflow.com/questions/15589517/how-to-crop-an-image-in-opencv-using-python
# https://docs.opencv.org/3.1.0/d7/d8b/tutorial_py_face_detection.html#gsc.tab=0

import cv2
from typing import List, Tuple, Callable
import os.path
import argparse

# load the pre-trained model
classifier = cv2.CascadeClassifier('model/haarcascade_frontalface_default.xml')

def parse_args():
    ap = argparse.ArgumentParser()
    gp = ap.add_mutually_exclusive_group(required=True)
    gp.add_argument('-d', '--directory', help='Detect faces and crop all photos in the given directory')
    gp.add_argument('-f', '--file', help='Detect faces and crop the given photo')
    ap.add_argument('-m', '--max', type=int, default=5, help='The maximum number of faces to extract. Defaults to 5. Use 0 for no limit')
    ap.add_argument('-b', '--box', action='store_true', help='Do not crop, but draw the bounding box to the photo and write that out')
    ap.add_argument('-s', '--show', action='store_true', help='Show each image as it is being output')
    ap.add_argument('-n', '--nowrite', action='store_true', help='Perform transformations but do not write files. Implies -s.')
    return ap.parse_args()

def get_name_and_extension(filename):
    if '.' in filename:
        name, ext = filename.rsplit('.')
        ext = '.' + ext
    else:
        name, ext = filename, ''
    return name, ext

def ensure_dir(dirname):
    if not os.path.isdir(dirname) and not os.path.exists(dirname):
        os.mkdir(dirname)

def highest(value, limit):
    if value > limit:
        value = limit
    return value

def lowest(value, limit):
    if value < limit:
        value = limit
    return value

def bounding_boxes_for_id(filename: str, classifier: 'cv2.CascadeClassifier') -> List[Tuple[int, int, int, int]]:
    '''
    This function receives a filename and a face classifier and returns a list
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
    pixels = cv2.imread(filename)
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
            name: str,
            ext: str,
            boxes: List[Tuple[int, int, int, int]],
            outdir: str,
            transform: Callable[['cv2.image', int, int, int, int], 'cv2.image'],
            show: bool = False,
            write: bool = True
        ) -> 'List[cv2.image]':
    image = cv2.imread(name + ext)
    results = []
    for i in range(len(boxes)):
        (x1, y1, x2, y2) = boxes[i]
        result = transform(image, x1, y1, x2, y2)
        results.append(result)
        if show:
            cv2.imshow('Result', result)
            cv2.waitKey(0)
        outfile = '{}/{}_face{}{}'.format(outdir, name, i, ext)
        if write:
            try:
                cv2.imwrite(outfile, result)
            except cv2.error as e:
                print("Could not write image called {}".format(outfile))
                print(e.msg)
    return results

def crop_to_boxes(filename: str, boxes: List[Tuple[int, int, int, int]], show: bool = False, write: bool = True) -> 'List[cv2.image]':
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
    name, ext = get_name_and_extension(filename)
    if write:
        ensure_dir('cropped')

    _on_each_box(name, ext, boxes, 'cropped', lambda img, x1, y1, x2, y2: img[y1:y2, x1:x2], show, write)

def draw_bounding_box(filename: str, boxes: List[Tuple[int, int, int, int]], show: bool = False, write: bool = True) -> 'List[cv2.image]':
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
    name, ext = get_name_and_extension(filename)
    if write:
        ensure_dir('marked')

    def draw_rect(img, x1, y1, x2, y2, color=(0, 0, 255)):
        image = img.copy()
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        return image

    _on_each_box(name, ext, boxes, 'marked', draw_rect, show, write)


def test():
    for filename in range(1, 12):
        name = 'test{}.png'.format(filename)
        boxes = bounding_boxes_for_id(name, classifier)
        draw_bounding_box(name, boxes)

def main_for_file(filename, drawOnly: bool = False, show: bool = False, limit: int = 5, write: bool = True):
    boxes = bounding_boxes_for_id(filename, classifier)
    if len(boxes) > limit:
        print("Warning: file {} -> limit was {} but found {} faces. Taking first {}".format(filename, limit, len(boxes), limit))
        boxes = boxes[:limit]
    if drawOnly:
        results = draw_bounding_box(filename, boxes, show, write)
    else:
        results = crop_to_boxes(filename, boxes, show, write)
    return results

def main():
    options = parse_args()
    limit = options.max
    if options.directory:
        os.chdir(options.directory)
        for filename in os.listdir('.'):
            if not os.path.isdir(filename):
                main_for_file(filename, options.box, options.show or options.nowrite, options.max, not options.nowrite)
    elif options.file:
        main_for_file(options.file, options.box, options.show or options.nowrite, options.max, not options.nowrite)



if __name__ == '__main__':
    exit(main())
