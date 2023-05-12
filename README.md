# Home Assistant Notify for NextCloud Talk

Send and receive notification to/from a NextCloud Talk Room.

Original code copied from Home Assistent component Notify and modified for nextcloud Talk.

nextcloudtalkclient based on ha-matrix-client

notify based on noxiii/HANotifyNextCloudTalk

Tested with Home Assistant 2023.5.2, NextCloud 25.0.5 and Talk 15.0.5

### Installing

Clone the Repository into ./custom_components/ in the HomeAssistent config directory beside the configuration.yaml
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
      pool_interval: 30                 #listen for command optional, disabled if miss or =0
      rooms:                            #listen for command optional
        - "room1"
        - "user1"
```        
### Automation usage:

#### Sending message
```
service: notify.nextcloudtalk
data:
  target: user1
  message: temp is {{ states.sensor.atc_temperature_2bab3b.state }}°C
```  

```
service: notify.nextcloudtalk
data:
  target: #required
    - user1
    - user2
    - room2
  message: temp is {{ states.sensor.atc_temperature_2bab3b.state }}°C
  data:
    snapshot22_{{ context.id }}.jpg: /config/www/tmp/snapshot22.jpg
```  
```  

alias: snapshot23
description: ''
trigger:
  - platform: time
    at: '14:00'
condition: []
action:
  - service: camera.snapshot
    target:
        device_id: d7e7044b9e489260fd4e613b0ca3b693
    data:
        filename: /config/www/tmp/snapshot23.jpg
  - service: notify.nextcloudtalk
      data:
        message: snapshot23
          target: user1
        data:
            snapshot23_{{ context.id }}.jpg: /config/www/tmp/snapshot23.jpg
mode: single
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
        do {{ trigger.event.data.message }} for {{ trigger.event.data.sender }} aka  {{ trigger.event.data.sender_name }}
      target: '{{trigger.event.data.room}}'
  - service: switch.toggle
    target:
      entity_id: switch.living_room_dehumidifier_2
mode: single

```

```
alias: snapshot23
description: ''
trigger:
  - platform: event
    event_type: nctalk_command
condition:
  - condition: template
    value_template: >-
      {{ (trigger.event.data.sender=='user1') and 
      (trigger.event.data.message.upper() == 'TAKE23')}}
action:
  - service: camera.snapshot
    target:
      device_id: d7e7044b9e489260fd4e613b0ca3b693
    data:
      filename: /config/www/tmp/snapshot23.jpg
  - service: camera.snapshot
    target:
      device_id: c7e7044b9e489260fd4e613b0ca3b694
    data:
      filename: /config/www/tmp/snapshot24.jpg
  - service: notify.nextcloudtalk
    data:
      message: snapshot23
      target: user1
      data:
        snapshot23_{{ context.id }}.jpg: /config/www/tmp/snapshot23.jpg
        snapshot24_{{ context.id }}.jpg: /config/www/tmp/snapshot24.jpg
mode: single
```

