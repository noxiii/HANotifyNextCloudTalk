# Home Assistant Notify for NextCloud Talk

Send and receive notification to/from a NextCloud Talk Room.

Original code copied from Home Assistent component Notify and modified for nextcloud Talk.

nextcloudtalkclient based on ha-matrix-client
notify based on noxiii/HANotifyNextCloudTalk

Tested with Home Assistant 2021.11.5, NextCloud 22.2.3 and Talk 12.1.2

### Installing

Clone the Repository into ./custom_component/ in the HomeAssistent config directory beside the configuration.yaml 
Then restart HomeAssistant to load the custom component.

### Configuration

Create a seperate user for the notify. Add this user and your own to a room. Be sure that the name the room is uniq.

Add to the configuration.yaml following lines. Add for every room a separate notify.

```
notify:
    - platform: nextcloudtalk
      name: nextcloudtalk
      url: https://nextcloud.domain.tld
      username: smarthome  (If you use the subdir, add the directory: https://domain.tld/nextcloud)
      password: Password
      room: smarthome
      rooms: 
        - "room1"
        - "login2"
 

```
