#!/usr/bin/env python

from editfetcher import EditFetcher
from ChatExchange.chatexchange.client import Client
from ChatExchange.chatexchange.events import MessagePosted
import getpass
import os
import pickle
import Queue
import excepthook
import sys

sys.excepthook = excepthook.uncaught_exception
excepthook.install_thread_excepthook()

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

fetcher = EditFetcher()

owners = []
if os.path.isfile("owners.txt"):
    with open("owners.txt", "r") as f:
        owners = pickle.load(f)

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
        print("Exiting...")
        sys.stdout.flush()
        fetcher.stop()
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
        with open("owners.txt", "w") as f:
            pickle.dump(owners, f)
        event.message.reply("New owner added")
    elif msg.startswith(prefix + "amiowner"):
        if event.user.id in owners[host]:
            event.message.reply("Yes, you are an owner.")
        else:
            event.message.reply("No, you are not an owner.")

room.watch_socket(on_event)

if os.path.isfile("ApiKey.txt"):
    with open("ApiKey.txt", "r") as f:
        key = f.read().strip()
        fetcher.api_key = key


def send_message_to_room(msg):
    room.send_message(
        "[ [EditMonitor](https://github.com/ProgramFOX/SO-EditMonitor) ] %s"
        % msg
    )

fetcher.chat_send = send_message_to_room
fetcher.ce_client = c
fetcher.get_se_fkey()
fetcher.do_work(150)
