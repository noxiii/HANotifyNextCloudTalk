"""NextCloud Talk notification service."""
import logging
import voluptuous as vol
import requests
import json
from threading import Thread
import sys
import time
from .nextcloudtalkclient import NextCloudTalkClient

CONF_ROOMS = "rooms"
CONF_POOL_INTERVAL = "pool_interval"


from homeassistant.const import (
    CONF_PASSWORD, CONF_ROOM, CONF_URL, CONF_USERNAME)
import homeassistant.helpers.config_validation as cv

from homeassistant.components.notify import (ATTR_DATA, PLATFORM_SCHEMA,
                                             BaseNotificationService)

_LOGGER = logging.getLogger(__name__)

# pylint: disable=no-value-for-parameter
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): vol.Url(),
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_ROOM): cv.string,
    vol.Optional(CONF_ROOMS, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_POOL_INTERVAL, default=5): vol.Range(
        min=1, max=600
    ),
}
)

#url="https://cloud.my.domain/ocs/v2.php/apps/spreed/api/v3"
#room="smarthome"

def get_service(hass, config, discovery_info=None):
    """Return the notify service."""
    from rocketchat_API.APIExceptions.RocketExceptions import (
        RocketConnectionException, RocketAuthenticationException)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    pool_interval = config.get(CONF_POOL_INTERVAL)

    url = config.get(CONF_URL)
    room = config.get(CONF_ROOM)
    rooms = config.get(CONF_ROOMS)

    try:
        return NextCloudTalkNotificationService(hass, url, username, password, rooms, pool_interval)
    except RocketConnectionException:
        _LOGGER.warning(
            "Unable to connect to NextCloud Talk server at %s", url)

    except RocketAuthenticationException:
        _LOGGER.warning(
            "NextCloud Talk authentication failed for user %s", username)
        _LOGGER.info("Please check your username/password")

    return None


class NextCloudTalkNotificationService(BaseNotificationService):
    """Implement the notification service for NextCloud Talk."""
    EVENT_NCTALK_COMMAND = "nctalk_command"
    ncclient = None

    def __init__(self, hass, url, username, password, rooms, pool_interval):
        """Initialize the service."""
        self.hass = hass
        self.url = url
        self.rooms = rooms
        self.pool_interval = pool_interval
        self.ncclient = NextCloudTalkClient(base_url=url,
                                            username=username, password=password)
        self.ncclient.handler = self.handler
        self.ncclient.should_listen = True
        self.ncclient.start_listener_thread()
        #_LOGGER.warning("nextcloud joining...")
        for room in rooms:
            #_LOGGER.warning("nextcloud join:"+room)
            self.ncclient.joinRoom(room)



    def handler(self, room, sender, message):
        ACCEPT = True
        event_data = {
            "message": message,
            "sender": sender,
            "room": room
        }
        self.hass.bus.fire(self.EVENT_NCTALK_COMMAND, event_data)
        #_LOGGER.warning("nextcloud handler:"+sender+":"+message+":"+room)
        return ACCEPT

    def send_message(self, message="", **kwargs):
        """Send a message to NextCloud Talk."""
        #_LOGGER.error(kwargs)
        targets = kwargs["target"]

        if not targets:
            _LOGGER.error("At least 1 target is required")
            return

        for target in targets:
            """ Get Token/ID for target room """
            self.ncclient.send_message(target, message)


                          

