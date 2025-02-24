Enocean custom component for Home Assistant with Cover support
========================================

## Installation

Configuration basically is the same as for the original enocean component of HomeAssistant. The cover platform is additonal.
First add the Enenocean with Cover support to home assistant via integrations.

Configuration of the items is not (yet) possible via the UI, thus add the following entries for enocean covers

```yaml
cover:
  - platform: enocean_cs
    id: [0xAA, 0xBB, 0xCC, 0xDD]
    sender_id: [0xFF, 0xEE, 0xEF, 0xAA]
    name: Cover left
    use_vld: True #optionally, when using a D2 profile
```
