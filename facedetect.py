# from https://machinelearningmastery.com/how-to-perform-face-detection-with-classical-and-deep-learning-methods-in-python-with-keras/
# https://www.geeksforgeeks.org/python-opencv-cv2-imwrite-method/
# https://stackoverflow.com/questions/15589517/how-to-crop-an-image-in-opencv-using-python
# https://docs.opencv.org/3.1.0/d7/d8b/tutorial_py_face_detection.html#gsc.tab=0

import cv2
from typing import List, Tuple, Callable
from tqdm import tqdm
import os.path
import argparse

verbose = False

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
    ap.add_argument('-v', '--verbose', action='store_true', help='Produce incremental output for monitoring')
    ap.add_argument('-q', '--quiet', action='store_true', help='Produce no ouptut unless there is an exception')
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
    directory, filename = path_to_components(path)
    name, ext = get_name_and_extension(filename)
    if write:
        vsay(f'[-] Ensuring the existance of {os.path.join(directory, "cropped")} or createing it.')
        ensure_dir(os.path.join(directory, 'cropped'))
    _on_each_box(directory, name, ext, boxes, os.path.join(directory, 'cropped'), lambda img, x1, y1, x2, y2: img[y1:y2, x1:x2], show, write)

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
    vsay(f"[-] Found {len(boxes)} faces in file {path}.")
    if len(boxes) > limit:
        print("[*] Warning: file {} -> limit was {} but found {} faces. Taking first {}".format(filename, limit, len(boxes), limit), file=sys.stderr)
        boxes = boxes[:limit]
    if drawOnly:
        vsay(f'[-] Drawing bounding boxes for {path}...')
        results = draw_bounding_box(path, boxes, show, write)
    else:
        vsay(f'[-] Cropping to bounding boxes for {path}...')
        results = crop_to_boxes(path, boxes, show, write)
    return results

def vsay(msg, end="\n"):
    if verbose:
        print(msg, end=end)

def main():
    global verbose
    options = parse_args()
    verbose = options.verbose
    limit = options.max
    if options.directory:
        os.chdir(options.directory)
        vsay(f'[-] Reading files in {options.directory}...')
        if options.verbose or options.quiet:
            iterator = os.listdir('.')
        else:
            print(f'Reading files in "{options.directory}"...')
            iterator = tqdm(os.listdir('.'))
        for filename in iterator:
            vsay(f'[-] Reading file {filename}')
            if not os.path.isdir(filename):
                main_for_file(filename, options.box, options.show or options.nowrite, options.max, not options.nowrite)
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
