import argparse
import os.path
from tkinter import *
from tkinter import StringVar, filedialog, messagebox
from tkinter.ttk import Separator
from typing import Optional


TK_OLD_LABEL = Label


class Label(TK_OLD_LABEL):
    def __init__(self, *args, text='', **kwargs):
        text = text.replace('\n', '')
        super().__init__(*args, text=text, wraplength=325, **kwargs)


class HelpLabel(TK_OLD_LABEL):
    pass


TK_OLD_BUTTON = Button


class Button(TK_OLD_BUTTON):
    def __init__(self, *args, **kwargs):
        super(Button, self).__init__(*args, width=35, **kwargs)


class GetParameters:

    def spawn_window(self, size=None):
        window = Tk()
        if size is not None:
            window.geometry(size)
        self.windows.append(window)
        return window

    def __init__(self):
        self.windows = []
        self.namespace = argparse.Namespace(**{
            'file': None,
            'directory': None,
            'max': None,
            'box': None,
            'show': None,
            'resize': None,
            'plain': None,
            'pad': None,
            'multiplier': None,
            'user_cancelled': True,
            'min_box_width': 0,
            'min_box_height': 0,
            'nowrite': False

        })
        self.choose_parameters()

    def choose_target_directory(self, root, container: StringVar) -> Optional[StringVar]:
        dir = filedialog.askdirectory(initialdir=os.path.realpath('.'), title="Choose images directory")
        if dir == '':
            return
        container.set(dir)
        self.namespace.directory = dir
        container.was_set = True
        root.update()
        return container

    def set_parameters(self, actionvar, facevar, multvar, locationvar, minsizevar):
        minsize = minsizevar.get()
        try:
            minwidth, minheight = minsize.split('x')
            minwidth = int(minwidth)
            minheight = int(minheight)
        except Exception as e:
            messagebox.showerror('Invalid Min Box Size',
                                 "{} is not a valid min size. Click the help button for more\n{}".format(minsize,
                                                                                                         str(e)))
            return

        setattr(self.namespace, 'min_box_width', minwidth)
        setattr(self.namespace, 'min_box_height', minheight)

        if not locationvar.was_set:
            messagebox.showerror('No Selection', 'You must select a file/directory before continuing')
            return
        try:
            facevar.get()
        except Exception:
            return
        setattr(self.namespace, 'max', facevar.get())
        action, *resize = actionvar.get().split(' ')
        if resize:
            setattr(self.namespace, 'resize', True)
            setattr(self.namespace, action, True)
        else:
            setattr(self.namespace, action, True)

        setattr(self.namespace, 'multiplier', int(multvar.get()[0]))

        self.finalize()

    def choose_parameters(self):
        def help():
            helpwin = self.spawn_window()
            helpwin.title('Help for Operation Parameters')
            label = HelpLabel(helpwin, justify=LEFT, anchor='nw', text='''
    Select File Or Directory
       The first thing you must do is select the image(s) that you want to work with. These are the images from which
       the faces will be extracted. You may choose to select a single image file to process, or an entire folder
       containing image files

    Max number of faces
       Sometimes the program will detect parts of an image as a face that are not really faces. This can result in the
       'wrong' part of an image being extracting. Setting the number of faces greater than 1 means if the program
       detects many faces in 1 image it can output 1 file for each face. However, the more output, the more files, and
       the longer the program takes. If the program detects less than max faces it will simply output 1 file for each
       detected face

    Minimum Box Size
       The minimum box size parameter is a string in the format INTEGERxINTEGER such as 200x300 or 400x100. This
       parameter specifies the minimum size a bounding box of a face must be for the program to extract it.
       This helps cut down on false positives by ensuring small anomolies do not get detected by the program.
       You can use '0x0' to ensure all possible faces are extracted

    Program Actions
        box
           This option will find faces in the image and write out one image per face.
           In each of the images it writes, a red box will be drawn around the area it detected as a face.
           No other alterations to the image will take place

        crop
           This option will find faces in the image and write out one new image per face,
           where the image is cropped to the bounding box of the detected face.
           No other alterations to the image take place

        plain resize
           This option is the same as "crop" but it will also take the image that results from the "crop" option and
           resize to tbe 190x237 pixles, the exact size of a photo that Rediker uses. Because this option blindly sizes the
           image to 190x237, this can cause distortions and stretching or squishing of the image.

        pad resize
           This option is the same as "crop" but it will also take the image that results from the "crop" option and perform
           two more tasks. First, it takes the image and adds white borders around the outside as needed until its aspect
           ratio is proportional to 190x237. It then shrinks the resulting image to 190x237 exactly. This prevents the
           squishing and stretching in the plain-resize option but does waste some space with the borders

    Size Multiplier
       If using the one of the "resize" option, this option determines what multiple of the Rediker resolution (190x237) is used
       This can be helpful for lower qualilty or very disproportionate images.
    ''')
            Label(helpwin, text='Face Detector Program Explanations', font=("Arial", 15)).pack(padx=5, pady=5)
            label.pack(padx=2, pady=2, anchor=NW)
            helpwin.mainloop()

        self.actionvar = None
        self.m = None
        t = self.spawn_window('350x575')
        t.title('Face Extractor Program')
        intro = Label(t,
                      text="This program will allow you to take an image"
                           "or folder of images and extract just the faces in the image"
                           "as well as resize the image to proper Rediker size.")
        location_label = Label(t, text='Select an image file or folder of image files to extract faces from')
        locationvar = StringVar(t, '<nothing selected>')
        locationvar.was_set = False
        location = Label(t, textvariable=locationvar)
        db = Button(t, text="I have a folder full of images to process",
                    command=lambda: self.choose_target_directory(t, locationvar))
        fb = Button(t, text="I have 1 image to process", command=lambda: self.choose_target_file(t, locationvar))

        label = Label(t, text='Choose the operation to perform on each image')

        choices = ['box', 'crop', 'plain resize', 'pad resize']
        self.actionvar = StringVar(t)
        self.actionvar.set('pad resize')
        self.actionvar.trace('w', lambda *args: self.update_disabled())

        w = OptionMenu(t, self.actionvar, *choices)

        label2 = Label(t, text="Specify the max number of faces the \nprogram should look for per image")
        facevar = IntVar(t)
        facevar.set(5)
        faceentry = Entry(t, textvariable=facevar)

        label4 = Label(t,
                       text="Specify the minimum WIDTHxHEIGHT measurements in pixels of boxes to extract from images")
        minsizevar = StringVar(t)
        minsizevar.set('200x400')
        minsizeentry = Entry(t, textvariable=minsizevar)

        choices2 = ['1x', '2x', '3x', '4x']
        multvar = StringVar(t)
        multvar.set('1x')
        label3 = Label(t, text="Specify Rediker size multiplier")

        self.m = OptionMenu(t, multvar, *choices2)

        help = Button(t, text="Show Help", command=help)
        go = Button(t, text="Go",
                    command=lambda: self.set_parameters(self.actionvar, facevar, multvar, locationvar, minsizevar))

        intro.pack(padx=2, pady=2)
        Separator(t, orient='horizontal').pack(fill='x', padx=2, pady=2)

        location_label.pack(padx=2, pady=2)
        location.pack(padx=2, pady=2)
        fb.pack(padx=2, pady=2)
        db.pack(padx=2, pady=2)
        Separator(t, orient='horizontal').pack(fill='x', padx=2, pady=2)

        label2.pack(padx=2, pady=2)
        faceentry.pack(padx=2, pady=2)

        label4.pack(padx=2, pady=2)
        minsizeentry.pack(padx=2, pady=2)
        Separator(t, orient='horizontal').pack(fill='x', padx=2, pady=2)

        label.pack(padx=2, pady=2)
        w.pack(padx=2, pady=2)
        Separator(t, orient='horizontal').pack(fill='x', padx=2, pady=2)

        label3.pack(padx=2, pady=2)
        self.m.pack(padx=2, pady=2)
        Separator(t, orient='horizontal').pack(fill='x', padx=2, pady=2)

        go.pack(padx=2, pady=2)
        help.pack(padx=2, pady=2)
        t.mainloop()

    def update_disabled(self):
        if self.actionvar is not None and 'resize' in self.actionvar.get():
            self.m.config(state='normal')
            # self.m.pack()
        elif self.actionvar is not None:
            # self.m.pack_forget()
            self.m.config(state='disabled')

    def choose_target_file(self, parent, container):
        file = filedialog.askopenfilename(initialdir=os.path.realpath('.'), title="Choose image file")
        if file == '':
            return
        container.set(file)
        self.namespace.file = file
        container.was_set = True
        parent.update()
        return container

    def finalize(self):
        self.namespace.user_cancelled = False
        for window in self.windows:
            try:
                window.destroy()
            except Exception:
                pass
