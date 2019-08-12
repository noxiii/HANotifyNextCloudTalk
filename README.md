# Home Assistant Notify for NextCloud Talk

Send notification to a NextCloud Talk Room.

Original code copied from Home Assistent component Notify and modified for nextcloud Talk.

Tested with Home Assistent 0.97, NextCloud 16.0.3 and Talk 6.0.4

### Installing

Clone the Repository into ./custom_component/ in the HomeAssistent config directory beside the configuration.yaml 
Then restart HomeAssistent to load the custom component.

### Configuration

Create a seperate user for the notify. Add this user and your own to a room. Be sure that the name the room is uniq.

Add to the configuration.yaml following lines. Add for every room a seperate notify.

```
notify:
    - platform: nextcloudtalk
      name: nextcloudtalk
      url: https://nextcloud.domain.tld
      username: smarthome  (If you use the subdir, add the directory: https://domain.tld/nextcloud)
      password: Password
      room: smarthome


```
