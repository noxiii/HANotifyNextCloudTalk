"""NextCloud Talk notification service."""
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.notify import (PLATFORM_SCHEMA,
                                             BaseNotificationService)
from homeassistant.const import (CONF_PASSWORD, CONF_ROOM, CONF_URL,
                                 CONF_USERNAME)

from .nextcloudclient import NextcloudClient


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

    except:
        _LOGGER.warning(
            f"Nextcloud authentication failed for user {username}")

    return None


class NextCloudTalkNotificationService(BaseNotificationService):
    """Implement the notification service for NextCloud Talk."""

    def __init__(self, url, username, password, room):
        """Initialize the service."""
        self.client = NextcloudClient(url, username, password)
        self.room = room

    def send_message(self, message="", **kwargs):
        """Send a message to NextCloud Talk."""
        targets = kwargs.get("target")
        self.client.get_rooms()
        if not targets and not (self.room is None):
            targets = {self.room}
        if not targets:
            _LOGGER.error("NextCloud Talk message no targets")
        else:
            uploaded = {}
            data = kwargs.get("data")
            if data:
                for attach in data:
                    file = open(data[attach], 'rb')
                    self.client.upload_file(attach, file, data)
                    ok = self.client.upload_file(
                                                                attach,
                                                                file,
                                                                data
                                                               )
                    if not ok:
                        uploaded[attach] = data
            for target in targets:
                """ Get Token/ID for target room """
                if self.client.exist_room(target):

                    self.client.send_message(target, message)

                    if len(uploaded) > 0:
                        self.client.send_file(target, target, uploaded)

                else:
                    _LOGGER.error(
                        "Unable to post NextCloud Talk message: no token for: %s", target)
