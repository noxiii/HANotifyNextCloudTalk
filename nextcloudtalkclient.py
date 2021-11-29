import sys
import time
from threading import Thread

import requests

# based on ha-matrix-client
class Room(object):
    token: str = ""
    lastreadmessage: int = 0
    unreadmessages: int = 0
    listen: bool = False


class NextCloudTalkClient(object):
    interval = 5 # pool interval

    def __init__(self, base_url, username, password):
        self.sync_thread = None
        self.should_listen = False
        self.rooms = {}

        self.url = base_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.headers.update({'OCS-APIRequest': 'true'})
        self.session.headers.update({'Accept': 'application/json'})
        self.handler = None

    def joinRoom(self, room):
        if room in self.rooms.keys():
            self.rooms[room].listen = True
        else:
            r = Room()
            r.token = ''
            r.lastreadmessage = 0
            r.unreadmessages = 0
            r.listen = True
            self.rooms[room] = r
            self.getRoomsInfo()

    def getRoomsInfo(self):
        request_rooms = self.session.get(self.url + "/v4/room")
        room_json = request_rooms.json()
        server_rooms = room_json["ocs"]["data"]
        for roomInfo in server_rooms:
            if not (roomInfo["name"] in self.rooms.keys()):
                self.rooms[roomInfo["name"]] = Room()
                self.rooms[roomInfo["name"]].token = roomInfo["token"]
        for client_room_name in self.rooms.keys():
            client_room = self.rooms[client_room_name]
            server_room = None
            for roomInfo in server_rooms:
                if roomInfo["name"] == client_room_name:
                    server_room = roomInfo
            if server_room == None:                # create conversation for user
                data = {"roomType": 1, "invite": client_room_name, "roomName": client_room_name}
                resp = self.session.post(self.url + "/v4/room", data=data)
                resp_json = resp.json()
                created_rooms = resp_json["ocs"]["data"]
                for roomInfo in created_rooms:
                    if roomInfo["name"] == client_room_name:
                        server_room = roomInfo
            if not (server_room == None):
                client_room.token = server_room["token"]
                client_room.lastreadmessage = server_room["lastReadMessage"]
                client_room.unreadmessages = server_room["unreadMessages"]

    def send_message(self, room_name, message="", **kwargs):
        roomtoken = self.rooms[room_name].token
        data = {"token": roomtoken, "message": message, "actorType": "", "actorId": "", "actorDisplayName": "",
                "timestamp": 0, "messageParameters": []}
        resp = self.session.post(self.url + "/v1/chat/" + roomtoken, data=data)
        if resp.status_code == 201:
            success = resp.json()["ocs"]["meta"]["status"]
            if not success:
                print("Unable to post NextCloud Talk message")
        else:
            print("Incorrect status code when posting message: %d", resp.status_code)
        return None

    def mark_read_message(self, room_name, id_message):
        data = {"lastReadMessage": id_message}
        resp = self.session.post(self.url + "/v1/chat/" + self.rooms[room_name].token + "/read", data=data)
        return resp.status_code

    def clear_chat(self, roomtoken):
        resp = self.session.delete(self.url + "/v1/chat/" + roomtoken)
        return resp.status_code

    def receive_message(self, room_name):
        room = self.rooms[room_name]
        self.session.headers.update({"X-Chat-Last-Given": str(room.lastreadmessage)})
        resp = self.session.get(self.url + "/v1/chat/" + room.token + "?lookIntoFuture=1&setReadMarker=0&limit=" + str(
            room.unreadmessages) + "&lastKnownMessageId=" + str(room.lastreadmessage))
        messages = ""
        if resp.status_code == 200:
            messages = resp.json()["ocs"]["data"]
        if resp.status_code == 304:
            print("no new messages")

        return messages

    def _sync(self, timeout_ms=30000):
        self.getRoomsInfo()
        for room_name in self.rooms.keys():
            room = self.rooms[room_name]
            # print(room_name,"token=", room.token, room.listen)
            if room.listen and (not (room.token == "") and room.unreadmessages > 0):
                mmm = self.receive_message(room_name)
                for msg in mmm:
                    if not (self.handler == None):
                        if self.handler(room_name, msg['actorId'], msg["message"]):
                            self.mark_read_message(room_name, msg["id"])

    def listen_forever(self, timeout_ms=30000, exception_handler=None, bad_sync_timeout=5):
        _bad_sync_timeout = bad_sync_timeout
        self.should_listen = True
        while (self.should_listen):
            try:
                self._sync(timeout_ms)
                time.sleep(self.interval)
                _bad_sync_timeout = bad_sync_timeout
            except Exception as e:
                if exception_handler is not None:
                    exception_handler(e)
                else:
                    raise

    def start_listener_thread(self, timeout_ms=30000, exception_handler=None):
        """ Start a listener thread to listen for events in the background.
        Args:
            timeout_ms (int): How long to poll the Home Server for before
               retrying.
            exception_handler (func(exception)): Optional exception handler
               function which can be used to handle exceptions in the caller
               thread.
        """
        try:
            thread = Thread(target=self.listen_forever,
                            args=(timeout_ms, exception_handler))
            thread.daemon = True
            self.sync_thread = thread
            self.should_listen = True
            thread.start()
        except RuntimeError:
            e = sys.exc_info()[0]

    def stop_listener_thread(self):
        """ Stop listener thread running in the background
        """
        if self.sync_thread:
            self.should_listen = False
            self.sync_thread.join()
            self.sync_thread = None
