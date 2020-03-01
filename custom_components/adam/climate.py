"""Plugwise Adam Climate component for Home Assistant Core."""

import logging

import voluptuous as vol
import plugwise

import homeassistant.helpers.config_validation as cv
from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateDevice
from homeassistant.components.climate.const import (
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    TEMP_CELSIUS,
)
from . import (
    DOMAIN,
    CONF_MIN_TEMP,
    CONF_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    PwThermostat,
)

from homeassistant.exceptions import PlatformNotReady

_LOGGER = logging.getLogger(__name__)

# Read platform configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_MIN_TEMP, default=DEFAULT_MIN_TEMP): cv.positive_int,
        vol.Optional(CONF_MAX_TEMP, default=DEFAULT_MAX_TEMP): cv.positive_int,
    }
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Add the Plugwise ClimateDevice."""
    
    if discovery_info is None:
        return

    devices = []
    ctrl_id = None
    for device,thermostat in hass.data[DOMAIN].items():
        _LOGGER.info('Device %s',device)
        _LOGGER.info('Thermostat %s',thermostat)
        try:
            devs = thermostat['api'].get_devices()
        except RuntimeError:
            _LOGGER.error("Unable to get location info from the API")
            return
        
        for dev in devs:
            if dev['name'] == 'Controlled Device':
                ctrl_id = dev['id']
            else:
                device = PwThermostat(thermostat['api'], dev['name'], dev['id'], ctrl_id, DEFAULT_MIN_TEMP, DEFAULT_MAX_TEMP)
                if not device:
                    continue
                devices.append(device)
    add_entities(devices, True)
