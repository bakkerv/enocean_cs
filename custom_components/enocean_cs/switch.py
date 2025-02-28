"""Support for EnOcean switches."""
from __future__ import annotations

from enocean.utils import combine_hex
import voluptuous as vol
from enocean.protocol.constants import RORG
from enocean.protocol.packet import RadioPacket


from homeassistant.components.switch import (
    PLATFORM_SCHEMA as SWITCH_PLATFORM_SCHEMA,
    SwitchEntity,
)
from homeassistant.const import CONF_ID, CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN, LOGGER, SWITCH_ALL_CHANNELS
from .entity import EnOceanEntity

CONF_CHANNEL = "channel"
CONF_SENDER_ID = "sender_id"
DEFAULT_NAME = "EnOcean Switch"

PLATFORM_SCHEMA = SWITCH_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ID): vol.All(cv.ensure_list, [vol.Coerce(int)]),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_CHANNEL, default=SWITCH_ALL_CHANNELS): vol.All(
            int, vol.Range(min=0, max=31)
        ),  # Default all channels
        vol.Required(CONF_SENDER_ID): vol.All(cv.ensure_list, [vol.Coerce(int)]),
    }
)


def generate_unique_id(dev_id: list[int], channel: int) -> str:
    """Generate a valid unique id."""
    return f"{combine_hex(dev_id)}-{channel}"


def _migrate_to_new_unique_id(hass: HomeAssistant, dev_id, channel) -> None:
    """Migrate old unique ids to new unique ids."""
    old_unique_id = f"{combine_hex(dev_id)}"

    ent_reg = er.async_get(hass)
    entity_id = ent_reg.async_get_entity_id(Platform.SWITCH, DOMAIN, old_unique_id)

    if entity_id is not None:
        new_unique_id = generate_unique_id(dev_id, channel)
        try:
            ent_reg.async_update_entity(entity_id, new_unique_id=new_unique_id)
        except ValueError:
            LOGGER.warning(
                "Skip migration of id [%s] to [%s] because it already exists",
                old_unique_id,
                new_unique_id,
            )
        else:
            LOGGER.debug(
                "Migrating unique_id from [%s] to [%s]",
                old_unique_id,
                new_unique_id,
            )


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the EnOcean switch platform."""
    channel: int = config[CONF_CHANNEL]
    dev_id: list[int] = config[CONF_ID]
    dev_name: str = config[CONF_NAME]
    sender_id = config[CONF_SENDER_ID]

    _migrate_to_new_unique_id(hass, dev_id, channel)
    async_add_entities([EnOceanSwitch(dev_id, dev_name, channel, sender_id)])


class EnOceanSwitch(EnOceanEntity, SwitchEntity):
    """Representation of an EnOcean switch device."""

    _attr_is_on = False
    def __init__(self, dev_id: list[int], dev_name: str, channel: int, sender_id: list[int]):
        """Initialize the EnOcean switch device."""
        super().__init__(dev_id)
        self._light = None
        self.channel = channel
        self.sender_id = sender_id
        self._attr_unique_id = generate_unique_id(dev_id, channel)
        self._attr_name = dev_name

    def turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        packet = RadioPacket.create(
            rorg=RORG.VLD,
            rorg_func=0x01,
            rorg_type=0x01,
            sender=self.sender_id,
            destination=self.dev_id,
            command=1,  # Change actuator
            DV=0,  # Switch to new output value (no dimming value)
            IO=self.channel,  # The configured channel
            OV=0x64,  # ON (or 100%)
        )
        self.send_packet(packet)
        self._attr_is_on = True

    def turn_off(self, **kwargs):
        """Turn off the switch."""
        packet = RadioPacket.create(
            rorg=RORG.VLD,
            rorg_func=0x01,
            rorg_type=0x01,
            sender=self.sender_id,
            destination=self.dev_id,
            command=1,  # Change actuator
            DV=0,  # Switch to new output value (no dimming value)
            IO=self.channel,  # The configured channel
            OV=0x0,  # OF (or 0%)
        )
        self.send_packet(packet)
        self._attr_is_on = False

    def value_changed(self, packet):
        """Update the internal state of the switch."""
        if packet.data[0] == 0xA5:
            # power meter telegram, turn on if > 10 watts
            packet.parse_eep(0x12, 0x01)
            if packet.parsed["DT"]["raw_value"] == 1:
                raw_val = packet.parsed["MR"]["raw_value"]
                divisor = packet.parsed["DIV"]["raw_value"]
                watts = raw_val / (10**divisor)
                if watts > 1:
                    self._attr_is_on = True
                    self.schedule_update_ha_state()
        elif packet.data[0] == 0xD2:
            # actuator status telegram
            packet.parse_eep(0x01, 0x01)
            if packet.parsed["CMD"]["raw_value"] == 4:
                channel = packet.parsed["IO"]["raw_value"]
                output = packet.parsed["OV"]["raw_value"]
                if channel == self.channel or self.channel == SWITCH_ALL_CHANNELS:
                    self._attr_is_on = output > 0
                    self.schedule_update_ha_state()
