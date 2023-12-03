#!/bin/python
"""NextCloud Client"""
import logging

import requests

_LOGGER = logging.getLogger(__name__)


class NextcloudClient:
    def __init__(self, url, username, password):
        self.url = url
        self._session = requests.Session()
        self._session.auth = (username, password)
        self._session.headers.update({"OCS-APIRequest": "true"})
        self._session.headers.update({"Accept": "application/json"})

        self.caps = self._session.get(
            f"{url}/ocs/v1.php/cloud/capabilities").json()

        self.attachments_folder = self.caps["ocs"]["data"]["capabilities"][
            "spreed"]["config"]["attachments"]["folder"]
        self.attachments_allowed = self.caps["ocs"]["data"]["capabilities"][
            "spreed"]["config"]["attachments"]["allowed"]
        self.webdav_root = self.caps["ocs"]["data"]["capabilities"][
            "core"]["webdav-root"]

        self.prefix = "/ocs/v2.php/apps/spreed/api/"

    def get_rooms(self):
        if "conversation-v4" in self.caps["ocs"]["data"]["capabilities"][
                "spreed"]["features"]:
            request_rooms = self._session.get(
                f"{self.url}{self.prefix}v4/room")
        else:
            request_rooms = self._session.get(
                f"{self.url}{self.prefix}v1/room")

        room_json = request_rooms.json()
        rooms = room_json["ocs"]["data"]
        self.room_tokens = {}
        for roomInfo in rooms:
            self.room_tokens[roomInfo["name"]] = roomInfo["token"]
        return list(self.room_tokens.keys())

    def exist_room(self, room):
        if room in self.room_tokens:
            return True
        return False

    def send_message(self, room, message):
        roomtoken = self.room_tokens[room]
        data = {
            "token": roomtoken,
            "message": message,
            "actorType": "",
            "actorId": "",
            "actorDisplayName": "",
            "timestamp": 0,
            "messageParameters": []
        }
        resp = self._session.post(
            f"{self.url}{self.prefix}/v1/chat/{roomtoken}", data=data)

        # not correct
        if resp.status_code == 201:
            success = resp.json()["ocs"]["meta"]["status"]

            if not success:
                _LOGGER.error(
                    "Unable to post NextCloud Talk message")
            else:
                _LOGGER.error(
                    "Incorrect status code when posting message: "
                    f"{resp.status_code}")

    def send_file(self, room, uploaded):
        roomtoken = self.room_tokens[room]
        for uploaded_file in uploaded:
            data = {"shareType": 10, "shareWith": roomtoken,
                    "path": f"{self.attachments_folder}/{uploaded_file}",
                    "referenceId": "",
                    "talkMetaData": {"messageType": "comment"}}
            share_url = f"{self.url}{self.prefix}/v1/shares"
            resp = self._session.post(share_url, data=data)
            if resp.status_code != 200:
                _LOGGER.error(
                    f"Share file {uploaded_file} error for {room}, "
                    f"{share_url}, {resp}, {data}")

    def upload_file(self, attach, file, data):
        resp = self._session.put(
            f"{self.url}/{self.webdav_root}{self.attachments_folder}/{attach}",
            data=file)
        if resp.status_code in (200, 201, 202, 204):
            return True
        else:
            _LOGGER.error(f"upload attachment error {resp.status_code}, {attach}, {data[attach]}")
        return False
