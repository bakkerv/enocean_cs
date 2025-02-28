"""Constants for the EnOcean integration."""

import logging

from homeassistant.const import Platform

DOMAIN = "enocean_cs"
DATA_ENOCEAN = "enocean_cs"
ENOCEAN_DONGLE = "dongle"

ERROR_INVALID_DONGLE_PATH = "invalid_dongle_path"

SIGNAL_RECEIVE_MESSAGE = "enocean.receive_message"
SIGNAL_SEND_MESSAGE = "enocean.send_message"

LOGGER = logging.getLogger(__package__)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.COVER,
]
SWITCH_ALL_CHANNELS = 30
COVER_ALL_CHANNELS = 15
