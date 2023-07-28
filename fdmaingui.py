import os
import threading
import time

import cv2

from facedetect import NotAnImageError, ensure_dir, get_name_and_extension, main_for_file
from fdparametergui import GetParameters
from guitils import (GUIProgress, SimpleContainer, infobox,
                     yesorno)


def fdgui():
    # license_agreement('9e0ecb73-7e83-4c9e-b294-59b7a2b2db5c')
    global verbose, options
    options = GetParameters().namespace
    subdir = 'marked' if options.box else 'cropped'
    if options.user_cancelled:
        return
    if options.directory:
        # os.chdir(options.directory)
        ensure_dir(os.path.join(options.directory, subdir))
        yesorno(title="{} ready".format(options.directory),
                text="Program is ready to detect faces in {}\nResults will be placed in a sub folder. Any images from a previous run of this program WILL BE OVERWRITTEN\nContinue?".format(
                    options.directory))

        iterator = (os.listdir(options.directory))
        total = len(iterator)

        job_gate_variable = SimpleContainer(True)

        def closure():
            for (i, filename) in enumerate(iterator):
                path = os.path.join(options.directory, filename)
                if not job_gate_variable.get():
                    g.update(i, 'Job Cancelled!')
                    print("Cancelled")
                    return
                g.update(i, text='Reading file {}'.format(path))
                if not os.path.isdir(path):
                    try:
                        print('Doing {}'.format(path))
                        name, ext = get_name_and_extension(filename)
                        pixels = cv2.imread(path)
                        pixels = main_for_file(pixels, drawOnly=options.box,
                                               limit=options.max, multiplier=options.multiplier, min_box_height=options.min_box_height, min_box_width=options.min_box_height)

                        if not options.nowrite:
                            for idx, box in enumerate(pixels):
                                if idx >= options.max:
                                    print("Too many boxes. Stopping")
                                    break
                                new_path = os.path.join(options.directory, subdir, '{}-box{}.{}'.format(name, idx + 1, ext))
                                print('writing to new_path {}'.format(new_path))
                                cv2.imwrite(new_path, box)
                        g.update(i, 'Completed {}'.format(path))
                    except NotAnImageError as e:
                        g.update(i, 'File {} is not an image. Skipping...'.format(path))
                        time.sleep(0.1)
                    except Exception as e:
                        g.update(0, 'A critical error has occurred on file {}'.format(path))
                        g.done()
                        infobox(title="ERROR", text="An error has occurred processing {}:\n{}".format(path, str(e)))
                        raise
                else:
                    pass

            print("Done")
            g.done()

        thread = threading.Thread(daemon=True, target=closure)
        g = GUIProgress('Working on {}'.format(options.directory), total=total,
                        title="Face Extractor Program Running...",
                        main_label='Running face extractor on {}'.format(options.directory),
                        job_gate_variable=job_gate_variable)
        thread.start()
        g.start()
        if job_gate_variable.get():  # if cancelled don't show the finished message
            infobox(title="Finished!", text="The program has completed processing {}".format(options.directory))
    elif options.file:
        yesorno(title="{} ready".format(options.file),
                text="Program is ready to detect faces in {}. Results will be placed in a sub folder. Any images from a previous run of this program WILL BE OVERWRITTEN\nContinue?".format(
                    options.file))

        label_text = 'Processing file {}'.format(options.file)
        g = GUIProgress(label_text, 1, label_text, label_text, None)

        def closure():
            name, ext = get_name_and_extension(options.file)
            pixels = cv2.imread(options.file)
            pixels = main_for_file(pixels, drawOnly=options.box,
                                   limit=options.max, multiplier=options.multiplier)
            if not options.nowrite:
                for idx, box in enumerate(pixels):
                    if idx >= options.max:
                        print("Too many boxes. Stopping")
                        break
                    path = '{}-face{}{}'.format(name, idx + 1, ext)
                    cv2.imwrite(path, box)
            g.done()

        thread = threading.Thread(daemon=True, target=closure)
        thread.start()
        g.start()
        infobox(text=f'Done with "{options.file}"')
    # input("The program has completed. Press any key to close")
