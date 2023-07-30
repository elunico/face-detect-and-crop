# from https://machinelearningmastery.com/how-to-perform-face-detection-with-classical-and-deep-learning-methods-in-python-with-keras/
# https://www.geeksforgeeks.org/python-opencv-cv2-imwrite-method/
# https://stackoverflow.com/questions/15589517/how-to-crop-an-image-in-opencv-using-python
# https://docs.opencv.org/3.1.0/d7/d8b/tutorial_py_face_detection.html#gsc.tab=0

import argparse
import math
import os.path
import sys
from multiprocessing import Pool
from typing import Callable, List, Tuple, Union

import cv2
from tqdm import tqdm

Box = Tuple[int, int, int, int]

verbose = False


def parse_args():
    ap = argparse.ArgumentParser()
    gp = ap.add_mutually_exclusive_group()
    gp.add_argument('-g', '--gui', help='Open a gui version of the program. Ignores all other options', action='store_true')
    gp.add_argument('-d', '--directory', help='Detect faces and crop all photos in the given directory')
    gp.add_argument('-f', '--file', help='Detect faces and crop the given photo')
    ap.add_argument('-m', '--max', type=int, default=5, help='The maximum number of faces to extract. Defaults to 5. Use 0 for no limit')
    ap.add_argument('-b', '--box', action='store_true', help='Do not crop, but draw the bounding box to the photo and write that out')
    ap.add_argument('-s', '--show', action='store_true', help='Show each image as it is being output')
    ap.add_argument('-n', '--nowrite', action='store_true', help='Perform transformations but do not write files. Implies -s.')
    ap.add_argument('-v', '--verbose', action='store_true', help='Produce incremental output for monitoring')
    ap.add_argument('-q', '--quiet', action='store_true', help='Produce no ouptut unless there is an exception')
    ap.add_argument('-z', '--squeeze', action='store_true', help='Fit the output boxes to the ASPECT ratio for Rediker by growing boxes until they are the approximate aspect ratio of 190x237 but not NOT actually change the size')
    ap.add_argument('--multiplier', type=int, default=1, help='If resize is specified, resize to the given multiplier of Rediker size')
    ap.add_argument('--minheight', type=int, default=0, help='Discard any faces detected whose bounding box has a height smaller than that specified here')
    ap.add_argument('--minwidth', type=int, default=0, help='Discard any faces detected whose bounding box has a width smaller than that specified here')
    gp = ap.add_mutually_exclusive_group()
    gp.add_argument('-p', '--pad', action='store_true', help='Fit the output boxes to the 190x237 shape for Rediker by adding white padding and shrinking. implies -r')
    gp.add_argument('-r', '--resize', action='store_true', help='Resize the image to be 190x237 plainly as it is. Can be combined with -z to prevent excess distortion when resizing')
    options = ap.parse_args()
    if not options.gui and not options.file and not options.directory:
        options.gui = True
    return options


def get_name_and_extension(filename: str) -> Tuple[str, str]:
    if '.' not in filename:
        return filename, ''

    name, dot, ext = filename.rpartition('.')
    return name, dot + ext


def path_to_components(path: str) -> Tuple[str, str]:
    return os.path.split(path)


def ensure_dir(dirpath):
    if not os.path.isdir(dirpath) and not os.path.exists(dirpath):
        os.mkdir(dirpath)
    elif not os.path.isdir(dirpath) and os.path.exists(dirpath):
        raise OSError('Program requires {} to be a directory but it is not'.format(dirpath))


def constrain(value: Union[int, float], *, minimum: Union[int, float] = None, maximum: Union[int, float] = None) -> Union[int, float]:
    if minimum is not None and value < minimum:
        return minimum
    if maximum is not None and value > maximum:
        return maximum
    return value


def flip_flop_maker(flag=True):
    while True:
        yield flag
        flag = not flag


def smoosh_box(box: Box) -> Box:
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
) -> List[Box]:
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
        x1 = constrain(x1, minimum=0)
        y1 = constrain(y1, minimum=0)
        x2 = constrain(x2, maximum=pixels.shape[1] - 1)
        y2 = constrain(y2, maximum=pixels.shape[0] - 1)
        faces.append((x1, y1, x2, y2))
    return faces


def on_each_box2(pixels: 'cv2.image', boxes: List[Box], transform: Callable[['cv2.image', int, int, int, int], 'cv2.image']) -> List['cv2.image']:
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


def crop_to_boxes2(image: 'cv2.image', boxes: List[Box], options: FDOptions = FDOptions()) -> List['cv2.image']:
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


def draw_bounding_box2(image: 'cv2.image',  boxes: List[Box]) -> 'List[cv2.image]':
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
    classifier = cv2.CascadeClassifier(os.path.abspath(os.path.join(os.curdir, 'model', 'haarcascade_frontalface_default.xml')))
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


def do_multiprocess(filename, subdir, name, ext, options):
    try:
        pixels = cv2.imread(filename)
        pixels = main_for_file(pixels, drawOnly=options.box, limit=options.max, squeeze=options.squeeze, pad=options.pad, resize=options.resize, min_box_height=options.minheight, min_box_width=options.minwidth, multiplier=1 if not options.resize and not options.pad else options.multiplier)
        if not options.nowrite:
            for idx, box in enumerate(pixels):
                if idx >= options.max:
                    print("Too many boxes. Stopping")
                    break
                path = os.path.join(options.directory, subdir, '{}-box{}.{}'.format(name, idx + 1, ext))
                cv2.imwrite(path, box)
    except Exception as e:
        print("Failed to operate on file '{}'. \nSettings: {}\nError: {}\n\n".format(filename, options, e))
        # raise


def main():
    global verbose
    options = parse_args()
    verbose = options.verbose
    subdir = 'marked' if options.box else 'cropped'
    if options.gui:
        from fdmaingui import fdgui
        fdgui()
        return
    if options.directory:
        ensure_dir(os.path.join(options.directory, subdir))
        vsay(f'[-] Reading files in {options.directory}...')
        if options.verbose or options.quiet:
            iterator = os.listdir('.')
        else:
            print(f'Working on files in: "{options.directory}"...')
            iterator = tqdm(os.listdir(options.directory))
        contents = []
        for name in iterator:
            filename = os.path.join(options.directory, name)
            vsay(f'[-] Reading file {filename}')
            name, ext = get_name_and_extension(name)
            if not os.path.isdir(filename):
                contents.append((filename, subdir, name, ext, options))
            else:
                vsay(f"[*] Skipping {filename}: is directory.")
        with Pool() as pool:
            for result in pool.starmap(do_multiprocess, contents):
                print('completed {}'.format(result))
        vsay('=*' * 40)
        vsay(f'Done with directory "{options.directory}"'.center(80))
        vsay('=*' * 40)
    elif options.file:
        path, filename = path_to_components(options.file)
        name, ext = get_name_and_extension(filename)
        ensure_dir(os.path.join(path, subdir))
        vsay(f"[-] Processing file: {options.file}...")
        try:
            pixels = cv2.imread(options.file)
            pixels = main_for_file(pixels, drawOnly=options.box, limit=options.max, squeeze=options.squeeze, min_box_height=options.minheight, min_box_width=options.minwidth, pad=options.pad, resize=options.resize, multiplier=1 if not options.resize and not options.pad else options.multiplier)
            if not options.nowrite:
                for idx, box in enumerate(pixels):
                    if idx >= options.max:
                        print("Too many boxes. Stopping")
                        break
                    cv2.imwrite(os.path.join(path, subdir, '{}-box{}.{}'.format(name, idx + 1, ext)), box)
        except Exception:
            print("Failed to operate on file '{}'. \nSettings: {}\n\n".format(options.file, options))
            raise
        vsay('*=' * 2 + f'Done with "{options.file}"' + '*=' * 2)


if __name__ == '__main__':
    exit(main())
