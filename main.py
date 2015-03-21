from editfetcher import EditFetcher
from ChatExchange.chatexchange.client import Client
from ChatExchange.chatexchange.events import MessagePosted
import getpass
import os
import pickle
import Queue

room_number = int(raw_input("Room number: "))
email = raw_input("Email: ")
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
    if event.message.content_source.startswith(prefix + "apiquota"):
        event.message.reply(str(fetcher.api_quota))
    elif event.message.content_source.startswith(prefix + "stop")\
            and event.user.id in owners[host]:
        room.leave()
        c.logout()
        print("Exiting...")
        action_queue.put_nowait(SystemExit)

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
running = True
while running:
    success, latest_edits = fetcher.api_request()
    if success:
        fetcher.process_items(latest_edits)
        print("Queue length: %s" % (len(fetcher.queue),))
        fetcher.empty_queue()
        fetcher.filter_saved_list()
        print("API quota: " + str(fetcher.api_quota))
    try:
        action = action_queue.get(True, 150)
        if action == SystemExit:
            running = False
    except Queue.Empty:
        pass
