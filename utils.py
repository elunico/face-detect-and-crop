from os import get_terminal_size
import dialog

d = dialog.Dialog()

term_size = get_terminal_size()

if term_size.columns < 60 or term_size.lines < 20:
    raise OSError("Your terminal must be at least 40x20")

box_width = max(term_size.columns - 6, 50)
box_height = max(term_size.lines - 6, 16)


def show_dialog(method, width=None, height=None, help_text='', **kwargs):
    global d
    if method == d.dselect or method == d.fselect:
        height = box_height - 9
    else:
        height = box_height

    if width is None:
        width = box_width

    sentinel = object()

    def do_action():
        result = method(**kwargs, width=width, height=height, help_button=not not help_text)
        if result is None:
            return
        if result[0] == 'cancel':
            raise SystemExit("User cancelled in dialog")
        elif result[0] == 'help':
            d.msgbox(text=help_text, width=box_width, height=box_height)
            return sentinel
        else:
            return result[1]

    result = do_action()
    while result == sentinel:
        result = do_action()

    return result


def dialog_get_int(message, default=None):
    val = None

    while True:
        try:

            v = int(val)
        except (ValueError, TypeError):
            val = d.inputbox(message, width=box_width, height=box_height)
            if not val[1] and default is not None:
                return default
            if val[0] == 'cancel':
                raise SystemExit('User cancelled')
            val = val[1]
        else:
            break
    return v
