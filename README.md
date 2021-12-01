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

Create a separate user for the notify. Add this user and your own to a room. Be sure that the name the room is uniq.

Add to the configuration.yaml following lines.


```
notify:
    - platform: nextcloudtalk
      name: nextcloudtalk
      url: https://nextcloud.domain.tld
      #url: https://domain.tld/nextcloud
      username: smarthome 
      password: Password
      pool_interval: 5                  #listen for command optional, disabled if miss or =0
      rooms:                            #listen for command optional
        - "room1"
        - "user1"
```        
### Automation usage:

#### Sending message
```
service: notify.nextcloudtalk
data:
  target: #required
    - user1
    - user2
    - room2
  message: temp is {{ states.sensor.atc_temperature_2bab3b.state }}°C
```  
#### Receiving messages  
```
alias: New automation
description: ''
trigger:
  - platform: event
    event_type: nctalk_command
    event_data: {}
condition:
  - condition: template
    value_template: '{{ trigger.event.data.message.upper() == "DOIT"}}'
action:
  - service: notify.nextcloudtalk
    data:
      message: >-
        do {{ trigger.event.data.message }} for {{
        trigger.event.data.sender }}
      target: '{{trigger.event.data.room}}'
  - service: switch.toggle
    target:
      entity_id: switch.living_room_dehumidifier_2
mode: single

```
