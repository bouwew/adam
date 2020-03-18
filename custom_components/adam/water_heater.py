"""Plugwise Water Heater component for HomeAssistant."""

import logging

import voluptuous as vol
import plugwise

import homeassistant.helpers.config_validation as cv

from . import (
    DOMAIN,
    PwWaterHeater,
)

from homeassistant.helpers.entity import Entity
from homeassistant.const import (
    ATTR_BATTERY_LEVEL,
    ATTR_TEMPERATURE,
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    TEMP_CELSIUS,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_BATTERY,
)
from homeassistant.exceptions import PlatformNotReady

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Add the Plugwise Water Heater."""

    if discovery_info is None:
        return

    devices = []
    ctrl_id = None
    for device,thermostat in hass.data[DOMAIN].items():
        _LOGGER.info('Device %s', device)
        _LOGGER.info('Thermostat %s', thermostat)
        api = thermostat['api']
        try:
            devs = api.get_devices()
        except RuntimeError:
            _LOGGER.error("Unable to get location info from the API")
            return

        appliances = api.get_appliances()
        domain_obj = api.get_domain_objects()
        _LOGGER.info('Dev %s', devs)
        for dev in devs:
            data = None
            _LOGGER.info('Dev %s', dev)
            if dev['name'] == 'Controlled Device':
                ctrl_id = dev['id']
                dev_id = None
                name = 'adam'
                _LOGGER.info('Name %s', name)
                data = api.get_device_data(appliances, domain_obj, dev_id, ctrl_id, None)

                if data is None:
                    _LOGGER.debug("Received no data for device %s.", name)
                    return

                device = PwWaterHeater(api, name, dev_id, ctrl_id)
                _LOGGER.info('Adding water_heater.%s', name)
                if not device:
                    continue
                devices.append(device)
    add_entities(devices, True)
