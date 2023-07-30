from tkinter import *
from tkinter import messagebox, Tk, Label, Button
import os.path


class GUIProgress:
    def __init__(self, text, total, title, main_label, job_gate_variable):
        self.window = Tk()
        self.window.protocol("WM_DELETE_WINDOW", lambda: ...)
        self.window.title(title)
        self.window.eval('tk::PlaceWindow . center')

        self.keepgoing = job_gate_variable
        self.current = 0
        self.total = total
        self._done = False

        self.text = StringVar(self.window)
        self.text.set(text)

        self.top_label = Label(self.window, text=main_label)
        self.status_label = Label(self.window, text='Processing {} of {}'.format(self.current, self.total),
                                  font=("Arial", 24))
        self.label = Label(self.window, textvariable=self.text, font=('Arial', 24))
        self.stop_button = Button(self.window, text='Stop Processing', command=self._cancel_job)

        self.top_label.pack(padx=10, pady=10)
        self.status_label.pack(padx=10, pady=10)
        self.label.pack(padx=10, pady=10)
        self.stop_button.pack()
        self.job = self.window.after((1000 // 20), self.check_update)

    def _cancel_job(self):
        if messagebox.askyesno("Stop Job", "Are you sure you want to stop the current process?"):
            # if the program has completed before the user accepts, do nothing
            if self._done:
                return
            self.window.after_cancel(self.job)
            # if there is a gate stop it
            if self.keepgoing is not None:
                self.keepgoing.set(False)
            self.window.destroy()
            messagebox.showwarning("Cancelled", "The program was cancelled")
            # self.thread.join()

    def check_update(self):
        if self._done:
            self.text.set('Finished')
            self.status_label.config(text='')
            self.window.after_cancel(self.job)
            self.window.destroy()
            return
        self.status_label.config(text='Processing {} of {}'.format(self.current, self.total))
        self.window.update()
        self.job = self.window.after(16, self.check_update)

    def update(self, current, text=None):
        self.current = current
        self.text.set(text)

    def done(self):
        self._done = True

    def start(self):
        self.window.lift()
        self.window.mainloop()


def bind(fn, *args, **kwargs):
    return lambda: fn(*args, **kwargs)


def appsupportdir():
    windows = r'%APPDATA%'
    windows = os.path.expandvars(windows)
    if 'APPDATA' not in windows:
        return windows

    user_directory = os.path.expanduser('~')

    macos = os.path.join(user_directory, 'Library', 'Application Support')
    if os.path.exists(macos):
        return macos

    linux = os.path.join(user_directory, '.local', 'share')
    if os.path.exists(linux):
        return linux

    return user_directory


def pathinappsupportdir(*paths, create=False):
    location = os.path.join(appsupportdir(), *paths)

    if create:
        os.makedirs(location)

    return location


def yesorno(title, text, once_identifier=None, denyButton='Cancel', acceptButton='OK', exitOnNo=True):
    folder = pathinappsupportdir('facedetect', 'yesnosingle')
    if not os.path.isdir(folder):
        try:
            os.makedirs(folder)
        except FileNotFoundError:
            pass
    if once_identifier is not None:
        destination_file = os.path.join(folder, once_identifier)
        if os.path.exists(destination_file):
            return
    window = Tk()
    window.title(title)
    label = Label(window, text=text)
    result = YesNoStatus()
    ok = Button(window, text=acceptButton, command=lambda: result.ok() or window.destroy())
    cancel = Button(window, text=denyButton, command=lambda: result.cancel() or window.destroy())
    label.pack(padx=2, pady=2)
    ok.pack(padx=2, pady=2)
    cancel.pack(padx=2, pady=2)
    window.mainloop()
    if result.is_ok() and once_identifier is not None:
        destination_file = os.path.join(folder, once_identifier)
        with open(destination_file, 'w') as f:
            f.write('sentinel')

    if result.is_cancel() and exitOnNo:
        raise SystemExit()
    elif result.is_cancel() and not exitOnNo:
        return False


def infobox(title='', text=''):
    messagebox.showinfo(title, text)


class YesNoStatus:
    def __init__(self):
        self.status = 'cancel'

    def is_ok(self):
        return self.status == 'ok'

    def ok(self):
        self.status = 'ok'

    def is_cancel(self):
        return self.status != 'ok'

    def cancel(self):
        self.status = 'cancel'


class SimpleContainer:
    def __init__(self, value):
        self.value = value

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


def percentFor(i, total):
    return int((i / total) * 100)


def license_agreement(id):
    yesorno(title='License Agreement', text='''
        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
        WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
        IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
        WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
        OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

        If you accept the terms, you will not be asked again.

        Do you accept the terms?
        ''', once_identifier=id)