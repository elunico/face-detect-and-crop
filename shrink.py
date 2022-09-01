import argparse
import cv2
import os.path
import dialog
import os
from utils import *

d = dialog.Dialog()


def percentOf(value, total):
    return int((value / total) * 100)


def get_interactive_args():
    options = argparse.Namespace(**{'file': None, 'directory': None, 'output': None, 'width': None})

    choice = do_dialog(d.menu, text='Do you want to run the program on all the items of a folder or a single file?',
                       choices=[('dir', 'Entire Folder'), ('file', 'A Single File')])

    if choice == 'dir':
        directory = do_dialog(d.dselect, filepath=os.getcwd(), title='Choose the folder containing the images to process')
        setattr(options, 'directory', directory)
    else:
        file = do_dialog(d.fselect, filepath=os.getcwd(), title="Choose the image file to process")
        setattr(options, 'file', [file])

    width = dialog_int('Enter the desired width of the new images')

    setattr(options, 'width', str(width))

    if choice == 'dir':
        directory = do_dialog(d.dselect, filepath=os.getcwd(), title="Choose the folder to place the processed image")
        setattr(options, 'output', directory[1])

    return options


def parse_args():
    # parser = argparse.ArgumentParser(description='Shrink an image')
    # group = parser.add_mutually_exclusive_group(required=True)
    # group.add_argument('-d', '--directory', dest='directory', help='Folder to effect all images of')
    # group.add_argument('-f', '--file', dest='file', nargs='*', help='File(s) to resize')
    # parser.add_argument('-o', '--output', dest='output', help='Output directory to use')
    # parser.add_argument('-w', '--width', dest='width', required=True, help='New width for the image, height calculated automatically')
    # parser.add_argument('-i', '--interactive', action='store_true',help='prompt for answers instead of using the CLI switches')

    # args = parser.parse_args()

    # if args.interactive:
    #     return get_interactive_args()

    # if args.directory and not args.output:
    #     parser.error("Cannot specifiy input directory without specifying output directory")
    # else:
    #     return args
    return get_interactive_args()


def rename_shrunk(input, width):
    new_name = input.split('.')
    new_name[0] = new_name[0] + '_shrunk_' + width
    return '.'.join(new_name)


# def vsay(msg):
#     print('[*] ' + str(msg))


# def verror(msg):
#     print('[!] ' + str(msg))


def main():
    args = parse_args()

    if args.file:
        answer = d.yesno('Warning! Files will be overwritten! Continue processing anyway?')
        if answer != d.OK:
            return
        total = len(args.file)
        d.gauge_start('Processing {} files'.format(total))
        for i, filename in enumerate(args.file):
            d.gauge_update(percentOf(i, total), text='Processing {}'.format(filename), update_text=True)
            img = cv2.imread(filename)
            if img is None:
                d.gauge_update(percentOf(i, total), text='Error: Could not read image named: {}'.format(filename), update_text=True)
                continue
            height, width, _ = img.shape
            new_height = int(args.width)
            new_width = int(width * new_height / height)
            resized_img = cv2.resize(img, (new_width, new_height))
            cv2.imwrite(filename, resized_img)
            d.gauge_update(percentOf(i + 1, total), 'Done! {} remaining'.format(total - i - 1))
        d.gauge_update(100, "All Done!")
        d.gauge_stop()
    elif args.directory:
        outdir = os.path.join(os.path.curdir, args.output)
        if not os.path.exists(outdir) and not os.path.isdir(outdir):
            do_dialog(d.msgbox, text='Output directory does not exist, it will be created')
            os.makedirs(outdir)
        elif os.path.exists(outdir) and not os.path.isdir(outdir):
            raise TypeError('Output is not a directory')

        do_dialog(d.msgbox, text="Program will begin shrink on directory {}".format(args.directory))
        filenames = os.listdir(args.directory)
        total = len(filenames)
        d.gauge_start('Processing {} files'.format(total))
        for (i, path) in enumerate(filenames):
            filename = os.path.join(args.directory, path)
            d.gauge_update(percentOf(i, total), text='Processing: ' + filename, update_text=True)
            img = cv2.imread(filename)
            if img is None:
                d.gauge_update(percentOf(i, total), text='Error: Could not read image named: {}'.format(filename), update_text=True)
                continue
            height, width, _ = img.shape
            new_height = int(args.width)
            new_width = int(width * new_height / height)
            resized_img = cv2.resize(img, (new_width, new_height))
            new_name = rename_shrunk(path, args.width)
            new_file = os.path.join(outdir, new_name)
            cv2.imwrite(new_file, resized_img)
        d.gauge_update(100, text="Done", update_text=True)
        d.gauge_stop()
    else:
        raise ValueError("Specify dir or file")


if __name__ == '__main__':
    main()
