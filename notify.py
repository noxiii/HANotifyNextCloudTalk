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

    try:
        return NextCloudTalkNotificationService(url, username, password, room)
    except RocketConnectionException:
        _LOGGER.warning(
            "Unable to connect to Rocket.Chat server at %s", url)

    return NextCloudTalkNotificationService(hass, url, username, password, rooms, pool_interval)


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
        # _LOGGER.warning("nextcloud joining...")
        for room in rooms:
            # _LOGGER.warning("nextcloud join:"+room)
            self.ncclient.joinRoom(room)
        if not (pool_interval is None) and not (rooms is None) and (pool_interval > 0) and len(rooms) > 0:
            self.ncclient.should_listen = True
            self.ncclient.start_listener_thread()
            _LOGGER.warning("pooling enabled by config (pool_interval="+str(pool_interval)+" rooms="+str(len(rooms)))
        else:
            _LOGGER.warning("pooling disabled by config (pool_interval=0 or empty rooms)")


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
