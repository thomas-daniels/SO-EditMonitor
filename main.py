#!/usr/bin/env python

import excepthook
import sys

sys.excepthook = excepthook.uncaught_exception
excepthook.install_thread_excepthook()

from editfetcher import EditFetcher
from ChatExchange.chatexchange.client import Client
from ChatExchange.chatexchange.events import MessagePosted
import getpass
import os
import pickle
import Queue
import sendmsg
import wsserver
from datetime import datetime
from restrictedmode import RestrictedMode

wsserv = wsserver.WSServer()
wsserv_enabled = False
if "--enable-websocket-server" in sys.argv:
    wsserv.start()
    wsserv_enabled = True
    sendmsg.wsserv = wsserv
    sys.argv.remove("--enable-websocket-server")
if "--verbose" in sys.argv:
    sendmsg.verbose_output = True
    sys.argv.remove("--verbose")

if not os.path.isdir("logs"):
    os.mkdir("logs")

sendmsg.logfilename = "logs/log-" + \
                      datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S") + \
                      ".txt"

if len(sys.argv) > 1:
    room_number = int(sys.argv[1])
else:
    room_number = int(raw_input("Room number: "))
if len(sys.argv) > 2:
    email = sys.argv[2]
else:
    email = raw_input("Email: ")
if len(sys.argv) > 3:
    password = sys.argv[3]
else:
    password = getpass.getpass()
if len(sys.argv) > 4:
    secondary_room_number = sys.argv[4]
else:
    secondary_room_number = int(raw_input("Secondary room (0 to disable): "))
host = "stackoverflow.com"
c = Client(host)
c.login(email, password)
del email
del password
room = c.get_room(room_number)
room.join()
room.send_message(
    "[EditMonitor](https://github.com/ProgramFOX/SO-EditMonitor) started."
)

if secondary_room_number != 0:
    secondary_room = c.get_room(secondary_room_number)
    secondary_room.join()
    secondary_room.send_message(
        "[EditMonitor](https://github.com/ProgramFOX/SO-EditMonitor) started. (Note: this is the secondary room so I don't listen for commands here.)"
    )
else:
    secondary_room = None

fetcher = EditFetcher()

owners = []
if os.path.isfile("owners.txt"):
    with open("owners.txt", "r") as f:
        owners = pickle.load(f)
mode = 63
if os.path.isfile("mode.txt"):
    with open("mode.txt", "r") as f:
        mode = int(f.read().strip())

prefix = "!>"
action_queue = Queue.Queue()


def on_event(event, _):
    if not isinstance(event, MessagePosted):
        return
    msg = event.message.content_source
    if msg.startswith(prefix + "apiquota"):
        event.message.reply(str(fetcher.api_quota))
    elif msg.startswith(prefix + "stop")\
            and event.user.id in owners[host]:
        room.leave()
        c.logout()
        sendmsg.send_to_console_and_ws("Exiting...")
        fetcher.stop()
        if wsserv_enabled:
            wsserv.stop()
    elif msg.startswith(prefix + "forcecheck")\
            and event.user.id in owners[host]:
        fetcher.force_check()
    elif msg.startswith(prefix + "addowner")\
            and event.user.id in owners[host]:
        args = msg.split(" ")[1:]
        if len(args) != 2:
            event.message.reply("2 arguments expected. "
                                "Syntax: `!>addowner host id`")
            return
        new_owner_host = args[0]
        new_owner_id_s = args[1]
        if not new_owner_host.endswith(".com"):
            new_owner_host += ".com"
        if new_owner_host not in ["stackexchange.com", "stackoverflow.com",
                                  "meta.stackexchange.com"]:
            event.message.reply("Invalid host for new owner. "
                                "Syntax: `!>addowner host id`")
            return
        try:
            new_owner_id = int(new_owner_id_s)
        except ValueError:
            event.message.reply("Invalid ID for new owner. "
                                "Syntax: `!>addowner host id`")
            return
        if new_owner_host not in owners:
            owners[new_owner_host] = []
        if new_owner_id in owners[new_owner_host]:
            event.message.reply("User is already owner.")
            return
        owners[new_owner_host].append(new_owner_id)
        with open("owners.txt", "w") as fi:
            pickle.dump(owners, fi)
        event.message.reply("New owner added")
    elif msg.startswith(prefix + "amiowner"):
        if event.user.id in owners[host]:
            event.message.reply("Yes, you are an owner.")
        else:
            event.message.reply("No, you are not an owner.")
    elif msg.startswith(prefix + "mode") and event.user.id in owners[host]:
        args = msg.strip().split(" ")[1:]
        if len(args) == 0:
            event.message.reply(
                "Mode for 'Approved with 2 rejection votes': **{}**".format(fetcher.restricted_mode.mode)
            )
        elif len(args) == 1:
            new_mode = args[0]
            if not new_mode.isdigit():
                event.message.reply("Invalid mode.")
                return
            new_mode_int = int(new_mode)
            if new_mode_int > 63:
                event.message.reply("Mode cannot be greater than 63.")
                return
            fetcher.restricted_mode = RestrictedMode(new_mode_int)
            with open("mode.txt", "w+") as mode_file:
                mode_file.write(str(new_mode_int))
            event.message.reply("Mode set to {}. The enabled rejection reasons are: {}."
                                .format(
                                    fetcher.restricted_mode.mode, ", ".join(fetcher.restricted_mode.enabled_reasons)
                                ))

room.watch_socket(on_event)

if os.path.isfile("ApiKey.txt"):
    with open("ApiKey.txt", "r") as f:
        key = f.read().strip()
        fetcher.api_key = key


def send_message_to_room(msg, verbose=False):
    room.send_message(
        "[ [EditMonitor](https://github.com/ProgramFOX/SO-EditMonitor) ] %s"
        % msg
    )
    sendmsg.send_to_console_and_ws(msg, verbose)


def send_message_to_secondary_room(msg, verbose=False):
    secondary_room.send_message(
        "[ [EditMonitor](https://github.com/ProgramFOX/SO-EditMonitor) ] %s"
        % msg
    )
    sendmsg.send_to_console_and_ws(msg, verbose)

fetcher.chat_send = send_message_to_room
fetcher.chat_send_secondary = send_message_to_secondary_room if secondary_room is not None else lambda x: None
fetcher.ce_client = c
fetcher.restricted_mode = RestrictedMode(mode)
fetcher.get_se_fkey()
fetcher.do_work(150)
