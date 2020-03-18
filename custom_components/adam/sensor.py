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
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_PRESSURE,
    PRESSURE_MBAR
)
from homeassistant.exceptions import PlatformNotReady

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    ATTR_TEMPERATURE : [TEMP_CELSIUS, None, DEVICE_CLASS_TEMPERATURE],
    ATTR_BATTERY_LEVEL : ["%" , None, DEVICE_CLASS_BATTERY],
    "illuminance" : ["lm" , None, DEVICE_CLASS_ILLUMINANCE],
    "pressure" : [PRESSURE_MBAR , None, DEVICE_CLASS_PRESSURE],
}

SENSOR_AVAILABLE = {
    "boiler_temperature": ATTR_TEMPERATURE,
    "water_pressure": "pressure",
    "battery_charge": ATTR_BATTERY_LEVEL,
    "outdoor_temperature": ATTR_TEMPERATURE,
    "illuminance": "illuminance",
}

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Add the Plugwise Thermostat Sensor."""

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

        _LOGGER.info('Dev %s', devs)
        for dev in devs:
            data = None
            _LOGGER.info('Dev %s', dev)
            if dev['name'] == 'Controlled Device':
                ctrl_id = dev['id']
                dev_id = None
                name = 'adam'
                _LOGGER.info('Name %s', name)
                data = api.get_device_data(dev_id, ctrl_id, None)
            if dev['type'] == 'thermostat':
                name = dev['name']
                dev_id = dev['id']
                _LOGGER.info('Name %s', name)
                data = api.get_device_data(dev_id, ctrl_id, None)

            if data is None:
                _LOGGER.debug("Received no data for device %s.", name)
                #return
            else:
                _LOGGER.debug("Device data %s.", data)
                for sensor,sensor_type in SENSOR_AVAILABLE.items():
                    addSensor=False
                    if sensor == 'boiler_temperature':
                        if 'boiler_temp' in data:
                            if data['boiler_temp']:
                                addSensor=True
                    if sensor == 'water_pressure':
                        if 'water_pressure' in data:
                            if data['water_pressure']:
                                addSensor=True
                    if sensor == 'battery_charge':
                        if 'battery' in data:
                            if data['battery']:
                                addSensor=True
                    if sensor == 'outdoor_temperature':
                        if 'outdoor_temp' in data:
                            if data['outdoor_temp']:
                                addSensor=True
                    if sensor == 'illuminance':
                        if 'illuminance' in data:
                            if data['illuminance']:
                                addSensor=True
                    if addSensor:
                        _LOGGER.info('Adding sensor.%s', '{}_{}'.format(name, sensor))
                        devices.append(PwThermostatSensor(api,'{}_{}'.format(name, sensor), dev_id, ctrl_id, sensor, sensor_type))
                    
    _LOGGER.info('Adding entities:', devices)
    add_entities(devices, True)

