import getedits
from ChatExchange.chatexchange.client import Client
from ChatExchange.chatexchange.events import MessagePosted
import getpass
import time
import os

room_number = int(raw_input("Room number: "))
email = raw_input("Email: ")
password = getpass.getpass()
c = Client("stackoverflow.com")
c.login(email, password)
del email
del password
room = c.get_room(room_number)
room.join()
room.send_message("EditMonitor started.")


def on_event(event, _):
    if not isinstance(event, MessagePosted):
        return
    if event.message.content_source.startswith(">>apiquota"):
        event.message.reply(str(getedits.api_quota))

room.watch_socket(on_event)

if os.path.isfile("ApiKey.txt"):
    with open("ApiKey.txt", "r") as f:
        key = f.read().strip()
        getedits.api_key = key


def send_notification_to_room(msg, s_id):
    room.send_message("[ EditMonitor ] %s: [%s](http://stackoverflow.com/suggested-edits/%s)"
                      % (msg, s_id, s_id))

getedits.action_needed = send_notification_to_room
while True:
    latest_edits = getedits.api_request()
    getedits.process_items(latest_edits)
    print("Queue length: %s" % (len(getedits.queue),))
    getedits.empty_queue()
    getedits.filter_saved_list()
    print("API quota: " + str(getedits.api_quota))
    time.sleep(150)
