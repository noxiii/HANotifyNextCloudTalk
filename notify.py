"""NextCloud Talk notification service."""
import logging
import voluptuous as vol
import requests
import json

from .nextcloudtalkclient import NextCloudTalkClient

CONF_ROOMS = "rooms"
CONF_POOL_INTERVAL = "pool_interval"

# CONF_ROOM,
from homeassistant.const import (
    CONF_PASSWORD, CONF_URL, CONF_USERNAME)
import homeassistant.helpers.config_validation as cv

from homeassistant.components.notify import (ATTR_DATA, PLATFORM_SCHEMA,
                                             BaseNotificationService)

_LOGGER = logging.getLogger(__name__)

# pylint: disable=no-value-for-parameter
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): vol.Url(),
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_ROOMS, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_POOL_INTERVAL, default=0): vol.Range(
        min=0, max=600
    ),
}
)


def get_service(hass, config, discovery_info=None):
    """Return the notify service."""
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    pool_interval = config.get(CONF_POOL_INTERVAL)

    url = config.get(CONF_URL)
    rooms = config.get(CONF_ROOMS)

    return NextCloudTalkNotificationService(hass, url, username, password, rooms, pool_interval)


class NextCloudTalkNotificationService(BaseNotificationService):
    """Implement the notification service for NextCloud Talk."""
    EVENT_NCTALK_COMMAND = "nctalk_command"
    ncclient = None

    def __init__(self, hass, url, username, password, rooms, pool_interval):
        """Initialize the service."""
        self.hass = hass
        self.url = url
        self.room = room
        self._session = requests.Session()
        self._session.auth = (username, password)
        self._session.headers.update({'OCS-APIRequest': 'true'})
        self._session.headers.update({'Accept': 'application/json'})

    def handler(self, room, sender, sender_name, message):
        ACCEPT = True
        event_data = {
            "message": message,
            "sender": sender,
            "sender_name": sender_name,
            "room": room
        }
        self.hass.bus.fire(self.EVENT_NCTALK_COMMAND, event_data)
        # _LOGGER.warning("nextcloud handler:"+sender+":"+message+":"+room)
        return ACCEPT

    def send_message(self, message="", **kwargs):
        """Send a message to NextCloud Talk."""
        # _LOGGER.error(kwargs)
        targets = kwargs["target"]

        if not targets:
            _LOGGER.error("At least 1 target is required")
            return

        for target in targets:
            """ Get Token/ID for target room """
            if "data" in kwargs and "attachment" in kwargs["data"]:
                if 'attachment_name' in kwargs["data"]:
                    status = self.ncclient.send_file(target,kwargs["data"]["attachment"], attachment_name=kwargs["data"]['attachment_name'])
                else:
                    status = self.ncclient.send_file(target,kwargs["data"]["attachment"])
                if not(status in (200,201,202,204)):
                    _LOGGER.error("send attachment error %s, %s", status, kwargs)
            status = self.ncclient.send_message(target, message)
            if status != 201:
                _LOGGER.error("send message error %s", kwargs)
