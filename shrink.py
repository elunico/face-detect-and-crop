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
        directory = do_dialog(d.dselect, filepath=os.getcwd(),
                              title='Choose the folder containing the images to process')
        setattr(options, 'directory', directory)
    else:
        file = do_dialog(d.fselect, filepath=os.getcwd(), title="Choose the image file to process")
        setattr(options, 'file', file)

    width = dialog_int('Enter the desired width of the new images')

    setattr(options, 'width', str(width))

    if choice == 'dir':
        directory = do_dialog(d.dselect, filepath=os.getcwd(), title="Choose the folder to place the processed image")
        setattr(options, 'output', directory)

    print(options)

    return options


def rename_shrunk(input, width):
    new_name = input.split('.')
    new_name[0] = new_name[0] + '_shrunk_' + width
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
    args = get_interactive_args()

    if args.file:
        answer = d.yesno('Warning! Do you want to overwrite the original file?')
        if answer != d.OK:
            directory, cfile = os.path.split(os.path.realpath(args.file))
            output = do_dialog(d.dselect, title="Choose the new output directory for the resulting image. You can specify a different name next",
                               filepath=directory, help_text='If you do not want the "shrink.py" program to overwrite the existing image file, then you can specify a new path to store the image at. First you should choose the directory to save in on this screen. By default it will put you in the directory where the image is found. Once you select the destination directory, you can then specify a new filename.')
            dest_name = do_dialog(d.inputbox, text="Enter new name (old name: {})".format(cfile))
            destination = os.path.join(output, dest_name)
        else:
            dest_name = os.path.split(args.file)[1]
            destination = args.file
        d.gauge_start(text='Processing {}'.format(args.file))
        resize_image(args.file, args.width, destination)
        d.gauge_update(100, 'Done with {}!'.format(dest_name), update_text=True)
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
            new_name = rename_shrunk(path, args.width)
            new_file = os.path.join(outdir, new_name)
            result = resize_image(filename, args.width, new_file)
            if not result:
                d.gauge_update(percentOf(i, total), text='Error: Could not read image named: {}'.format(filename),
                               update_text=True)
        d.gauge_update(100, text="Done", update_text=True)
        d.gauge_stop()
    else:
        raise ValueError("Specify dir or file")


if __name__ == '__main__':
    main()
