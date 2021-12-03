"""NextCloud Talk notification service."""
import logging
import voluptuous as vol
import requests
import json

from homeassistant.const import (
    CONF_PASSWORD, CONF_ROOM, CONF_URL, CONF_USERNAME, CONF_API_VERSION)
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
    vol.Required(CONF_ROOM): cv.string,
    vol.Required(CONF_API_VERSION): cv.string,
})


def get_service(hass, config, discovery_info=None):
    """Return the notify service."""
    # from nextcloudtalk_API.APIExceptions.NextcloudExceptions import (
    #    NextcloudConnectionException, NextcloudAuthenticationException)

    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    url = config.get(CONF_URL)
    room = config.get(CONF_ROOM)
    version = int(config.get(CONF_API_VERSION))

    try:
        return NextCloudTalkNotificationService(url, username, password, room, version)
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

    def __init__(self, url, username, password, room, version):
        """Initialize the service."""
        self.url = url
        self.room = room
        self.version = version
        self._session = requests.Session()
        self._session.auth = (username, password)
        self._session.headers.update({'OCS-APIRequest': 'true'})
        self._session.headers.update({'Accept': 'application/json'})

        """ Get Token/ID for Room """
        prefix = "/ocs/v2.php/apps/spreed/api/v1"
        if self.version >= 12:
          prefix = "/ocs/v2.php/apps/spreed/api/v4"
        request_rooms = self._session.get(self.url+prefix+"/room")
        room_json = request_rooms.json()
        rooms = room_json["ocs"]["data"]
        for roomInfo in rooms:
            if roomInfo["name"] == self.room:
                self.roomtoken = roomInfo["token"]

    def send_message(self, message="", **kwargs):
        """Send a message to NextCloud Talk."""
        data = {"token": self.roomtoken, "message": message, "actorType": "",
                "actorId": "", "actorDisplayName": "", "timestamp": 0, "messageParameters": []}
        prefix = "/ocs/v2.php/apps/spreed/api/v1"
        resp = self._session.post(
            self.url + prefix + "/chat/" + self.roomtoken, data=data)
        print(resp.text)
        if resp.status_code == 201:
            success = resp.json()["ocs"]["meta"]["status"]
            if not success:
                _LOGGER.error("Unable to post NextCloud Talk message")
        else:
            _LOGGER.error("Incorrect status code when posting message: %d",
                          resp.status_code)
