import sys
from datetime import datetime

wsserv = None
verbose_output = False


def send_to_console_and_ws(msg, verbose=False):
    msg = "[" + datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") + "] " + msg
    if verbose_output is True or \
            (verbose_output is False and verbose is False):
        print(msg)
        sys.stdout.flush()
    if wsserv is not None:
        if verbose:
            msg = "-" + msg
        else:
            msg = "+" + msg
        wsserv.send_ws_message(msg)
