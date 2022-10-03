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

    choice = show_dialog(d.menu, text='Do you want to run the program on all the items of a folder or a single file?',
                         choices=[('dir', 'Entire Folder'), ('file', 'A Single File')])

    if choice == 'dir':
        directory = show_dialog(d.dselect, filepath=os.getcwd(),
                                title='Choose the folder containing the images to process')
        setattr(options, 'directory', directory)
    else:
        file = show_dialog(d.fselect, filepath=os.getcwd(), title="Choose the image file to process")
        setattr(options, 'file', file)

    width = dialog_get_int('Enter the desired width of the new images')

    setattr(options, 'width', str(width))

    height = dialog_get_int('Enter the desired height of the new images or -1 to calculate automatically')

    setattr(options, 'height', str(height))

    if choice == 'dir':
        directory = show_dialog(d.dselect, filepath=directory, title="Choose the folder to place the processed image")
        setattr(options, 'output', directory)

    print(options)

    return options


def rename_shrunk(input, width):
    new_name = input.split('.')
    new_name[0] = new_name[0] + '_shrunk_' + width
    return '.'.join(new_name)


def resize_image(filename, argwidth, argheight, destination):
    img = cv2.imread(filename)
    if img is None:
        return False
    height, width, _ = img.shape
    new_width = int(argwidth)
    if argheight == -1:
        new_height = int(width * new_height / height)
    else:
        new_height = int(argheight)
    resized_img = cv2.resize(img, (new_width, new_height))
    cv2.imwrite(destination, resized_img)
    return True


def main():
    show_dialog(d.yesno, title="Welcome to shrink", text='''
        This program will help you shrink an image file to the correct size for Rediker's photo system. It is worth
        noting that the facedetect program can do this automatically when detecting faces, however, you can also do it
        manually here

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
    args = get_interactive_args()

    if args.file:
        answer = d.yesno('Warning! Do you want to overwrite the original file?')
        if answer != d.OK:
            directory, cfile = os.path.split(os.path.realpath(args.file))
            output = show_dialog(d.dselect,
                                 title="Choose the new output directory for the resulting image. You can specify a different name next",
                                 filepath=directory,
                                 help_text='If you do not want the "shrink.py" program to overwrite the existing image file, then you can specify a new path to store the image at. First you should choose the directory to save in on this screen. By default it will put you in the directory where the image is found. Once you select the destination directory, you can then specify a new filename.')
            dest_name = show_dialog(d.inputbox, text="Enter new name (old name: {})".format(cfile))
            destination = os.path.join(output, dest_name)
        else:
            dest_name = os.path.split(args.file)[1]
            destination = args.file
        show_dialog(d.yesno, title="{} ready to be shrunk".format(args.file), text="Program is ready to shrink {} into {} with width {}.\nContinue?".format(args.file, destination, args.width))
        d.gauge_start(text='Processing {}'.format(args.file))
        resize_image(args.file, args.width, args.height, destination)
        d.gauge_update(100, 'Done with {}!'.format(dest_name), update_text=True)
        d.gauge_stop()
    elif args.directory:
        outdir = os.path.join(os.path.curdir, args.output)
        if not os.path.exists(outdir) and not os.path.isdir(outdir):
            show_dialog(d.msgbox, text='Output directory does not exist, it will be created')
            os.makedirs(outdir)
        elif os.path.exists(outdir) and not os.path.isdir(outdir):
            raise TypeError('Output is not a directory')

        show_dialog(d.yesno, title="Ready to begin shrinking", text="Program will begin shrinking images in directory {}\nShrunken image files will have {} appended to their name and be placed in {}.\nIf files matching this pattern exist, they WILL BE OVERWRITTEN\nContinue?".format(args.directory, args.width,outdir))
        filenames = os.listdir(args.directory)
        total = len(filenames)
        d.gauge_start('Processing {} files'.format(total))
        for (i, path) in enumerate(filenames):
            filename = os.path.join(args.directory, path)
            d.gauge_update(percentOf(i, total), text='Processing: ' + filename, update_text=True)
            new_name = rename_shrunk(path, args.width)
            new_file = os.path.join(outdir, new_name)
            result = resize_image(filename, args.width, args.height, new_file)
            if not result:
                d.gauge_update(percentOf(i, total), text='Error: Could not read image named: {}'.format(filename),
                               update_text=True)
        d.gauge_update(100, text="Done", update_text=True)
        d.gauge_stop()
    else:
        raise ValueError("Specify dir or file")


if __name__ == '__main__':
    main()
