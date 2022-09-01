from os import get_terminal_size
import dialog

d = dialog.Dialog()

_old_print = print


def print(*args, **kwargs):
    # _old_print(inspect.getouterframes(inspect.currentframe()))
    _old_print(*args, **kwargs)


def do_dialog(method, width=None, height=None, **kwargs):
    global d
    if method == d.dselect or method == d.fselect:
        height = box_height - 9
    else:
        height = box_height

    result = method(**kwargs, width=box_width, height=height)
    if result is None:
        return
    if result[0] == 'cancel':
        raise SystemExit("User cancalled in dialog")
    else:
        return result[1]


term_size = get_terminal_size()

if (term_size.columns < 60 or term_size.lines < 20):
    raise OSError("Your terminal must be at least 40x20")

box_width = max(term_size.columns - 6, 50)
box_height = max(term_size.lines - 6, 16)


def dialog_int(message, default=None):
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
