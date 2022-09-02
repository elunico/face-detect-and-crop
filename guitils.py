from tkinter import *
class GUIProgress:
    def __init__(self, text, total, title, main_label):
        self.window = Tk()
        self.window.protocol("WM_DELETE_WINDOW", lambda: ...)
        # self.window.overrideredirect(True)
        self.window.title(title)
        self.window.eval('tk::PlaceWindow . center')

        self.current = 0
        self.total = total
        self._done = False

        self.text = StringVar(self.window)
        self.text.set(text)

        self.top_label = Label(self.window, text=main_label)
        self.status_label = Label(self.window, text='Processing {} of {}'.format(self.current, self.total),
                                  font=("Arial", 24))
        self.label = Label(self.window, textvariable=self.text, font=('Arial', 24))

        self.top_label.pack(padx=10, pady=10)
        self.status_label.pack(padx=10, pady=10)
        self.label.pack(padx=10, pady=10)
        self.job = self.window.after((1000 // 20), self.check_update)

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

