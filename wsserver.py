from websocket_server import WebsocketServer
from threading import Thread


class WSServer:
    def __init__(self):
        self.serv = None
        self.clients = []

    def start(self):
        port = 4001
        self.serv = WebsocketServer(port)
        self.serv.set_fn_new_client(self.client_joined)
        self.serv.set_fn_message_received(self.message_received)
        self.serv.set_fn_client_left(self.client_left)
        thr = Thread(target=lambda: self.serv.run_forever())
        thr.start()

    def send_ws_message(self, msg):
        if not self.is_enabled():
            return
        self.serv.send_message_to_all(msg)

    def is_enabled(self):
        return self.serv is not None

    def client_joined(self, client, server):
        pass

    def message_received(self, client, server):
        pass

    def client_left(self, client, server):
        pass