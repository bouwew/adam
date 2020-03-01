"""Plugwise Sensor component for HomeAssistant."""

import logging

import voluptuous as vol
import plugwise

import homeassistant.helpers.config_validation as cv

from . import (
    DOMAIN,
    PwThermostatSensor,
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

SENSOR_TYPES = {
    ATTR_TEMPERATURE : [TEMP_CELSIUS, None, DEVICE_CLASS_TEMPERATURE],
    ATTR_BATTERY_LEVEL : ["%" , None, DEVICE_CLASS_BATTERY],
}

SENSOR_AVAILABLE = {
    "boiler_temperature": ATTR_TEMPERATURE,
    "battery_charge": ATTR_BATTERY_LEVEL,
}

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Add the Plugwise Thermostat Sensor."""

    if discovery_info is None:
        return

    devices = []
    ctrl_id = None
    for device,thermostat in hass.data[DOMAIN].items():
        _LOGGER.info('Device %s',device)
        _LOGGER.info('Thermostat %s',thermostat)
        api = thermostat['api']
        try:
            devs = api.get_devices()
        except RuntimeError:
            _LOGGER.error("Unable to get location info from the API")
            return

        data = None
        appliances = api.get_appliances()
        domain_obj = api.get_domain_objects()
        _LOGGER.info('Dev %s', devs)
        for dev in devs:
            _LOGGER.info('Dev %s', dev)
            if dev['name'] == 'Controlled Device':
                ctrl_id = dev['id']
                dev_id = None
                name = dev['name']
                _LOGGER.info('Name %s', name)
                data = api.get_device_data(appliances, domain_obj, dev_id, ctrl_id)
            else:
                name = dev['name']
                dev_id = dev['id']
                _LOGGER.info('Name %s', name)
                data = api.get_device_data(appliances, domain_obj, dev_id, ctrl_id)

            if data is None:
                _LOGGER.debug("Received no data for device %s.", name)
                return

            for sensor,sensor_type in SENSOR_AVAILABLE.items():
                addSensor=False
                if sensor == 'boiler_temperature':
                    if 'boiler_temp' in data:
                        if data['boiler_temp']:
                            addSensor=True
                            _LOGGER.info('Adding boiler_temp')
                if sensor == 'battery_charge':
                    if 'battery' in data:
                        if data['battery']:
                            addSensor=True
                            _LOGGER.info('Adding battery_charge')
                if addSensor:
                    devices.append(PwThermostatSensor(api,'{}_{}'.format(name, sensor), dev_id, ctrl_id, sensor, sensor_type))
    add_entities(devices, True)

