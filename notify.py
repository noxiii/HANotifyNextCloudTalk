"""NextCloud Talk notification service."""
import logging
import voluptuous as vol
import requests
import json

from homeassistant.const import (
    CONF_PASSWORD, CONF_ROOM, CONF_URL, CONF_USERNAME)
import homeassistant.helpers.config_validation as cv

from homeassistant.components.notify import (ATTR_DATA, PLATFORM_SCHEMA,
                                             BaseNotificationService)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# pylint: disable=no-value-for-parameter
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): vol.Url(),
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_ROOM): cv.string,
})


def get_service(hass, config, discovery_info=None):
    """Return the notify service."""
    # from nextcloudtalk_API.APIExceptions.NextcloudExceptions import (
    #    NextcloudConnectionException, NextcloudAuthenticationException)

    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    url = config.get(CONF_URL)
    room = config.get(CONF_ROOM)

    try:
        return NextCloudTalkNotificationService(url, username, password, room)
    # except NextcloudConnectionException:
    #    _LOGGER.warning(
    #        "Unable to connect to Nextcloud Talk server at %s", url)

    except NextcloudAuthenticationException:
        _LOGGER.warning(
            "Nextcloud authentication failed for user %s", username)
        _LOGGER.info("Please check your username/password")

    return None


class NextCloudTalkNotificationService(BaseNotificationService):
    """Implement the notification service for NextCloud Talk."""

    def __init__(self, url, username, password, room):
        """Initialize the service."""
        self.url = url
        self.room = room
        self._session = requests.Session()
        self._session.auth = (username, password)
        self._session.headers.update({'OCS-APIRequest': 'true'})
        self._session.headers.update({'Accept': 'application/json'})
        """ Get Token/ID for Room """
        self.caps = self.session.get(url+"/ocs/v1.php/cloud/capabilities").json()
        prefix = "/ocs/v2.php/apps/spreed/api/"
        if 'conversation-v4' in self.caps["ocs"]["data"]["capabilities"]["spreed"]["features"]:
            request_rooms = self._session.get(self.url + prefix + "v4/room")
        else:
            request_rooms = self._session.get(self.url + prefix + "v1/room")
        room_json = request_rooms.json()
        rooms = room_json["ocs"]["data"]
        self.room_tokens = {}
        for roomInfo in rooms:
            self.room_tokens[roomInfo["name"]] = roomInfo["token"]

    def send_message(self, message="", **kwargs):
        """Send a message to NextCloud Talk."""
        targets = kwargs.get["target"]
        if not targets and not (self.room is None):
            targets = {self.room}
        if not targets:
            _LOGGER.error("NextCloud Talk message no targets")
        for target in targets:
            """ Get Token/ID for target room """
            if target in self.room_tokens:
                roomtoken = self.room_tokens[target]
                data = {"token": roomtoken, "message": message, "actorType": "",
                        "actorId": "", "actorDisplayName": "", "timestamp": 0, "messageParameters": []}
                prefix = "/ocs/v2.php/apps/spreed/api/v1"
                resp = self._session.post(
                    self.url + prefix + "/chat/" + roomtoken, data=data)
                if resp.status_code == 201:
                    success = resp.json()["ocs"]["meta"]["status"]
                    if not success:
                        _LOGGER.error("Unable to post NextCloud Talk message")
                else:
                    _LOGGER.error("Incorrect status code when posting message: %d",
                                  resp.status_code)
            else:
                _LOGGER.error("Unable to post NextCloud Talk message: no token for: %s", target)
