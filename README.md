#Home Assistant Notify NextCloud Talk

Send notify to a NextCloud Talk Room.

Original code copied from Home Assistent component Notify and modified for nextcloud Talk.

Tested with HA 0.97

### Installing

Go to HomeAssistent config directory ./custom_components and clone the Git Repo.
Then restart HomeAssistent

### Configuration

Add to configuration.yaml 

```
notify:
    - platform: nextcloudtalk
      name: nextcloudtalk
      url: https://cloud.domain.tdl
      username: hassio 
      password: Password
      room: smarthome


```
