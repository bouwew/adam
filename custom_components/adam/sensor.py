"""Plugwise Sensor component for HomeAssistant."""

import logging
import plugwise

from . import (
    DOMAIN,
    DATA_ADAM,
    PwEntity,
)

#from homeassistant.helpers.entity import Entity
from homeassistant.const import (
    ATTR_BATTERY_LEVEL,
    ATTR_TEMPERATURE,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_PRESSURE,
    DEVICE_CLASS_TEMPERATURE,
    ENERGY_WATT_HOUR,
    POWER_WATT,
    PRESSURE_MBAR,
    TEMP_CELSIUS,
)

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    ATTR_TEMPERATURE : [TEMP_CELSIUS, None, DEVICE_CLASS_TEMPERATURE],
    ATTR_BATTERY_LEVEL : ["%" , None, DEVICE_CLASS_BATTERY],
    "illuminance" : ["lm" , None, DEVICE_CLASS_ILLUMINANCE],
    "pressure" : [PRESSURE_MBAR , None, DEVICE_CLASS_PRESSURE],
    "energy_flow" : [POWER_WATT , None, DEVICE_CLASS_POWER ],
    "energy_measured" : [ENERGY_WATT_HOUR , None, DEVICE_CLASS_POWER ],
}

SENSOR_AVAILABLE = {
    "boiler_temperature": ATTR_TEMPERATURE,
    "water_pressure": "pressure",
    "battery_charge": ATTR_BATTERY_LEVEL,
    "outdoor_temperature": ATTR_TEMPERATURE,
    "illuminance": "illuminance",
    "electricity_consumed": "energy_flow",
    "electricity_consumed_interval": "energy_measured",
    "electricity_produced": "energy_flow",
    "electricity_produced_interval": "energy_measured",

}

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Add the Plugwise Thermostat Sensor."""

    if discovery_info is None:
        return

    api = hass.data[DATA_ADAM].data

    devices = []
    ctrl_id = None
    try:
        devs = api.get_devices()
    except RuntimeError:
        _LOGGER.error("Unable to get location info from the API")
        return

    _LOGGER.info('Dev %s', devs)
    
    ctrl_temp = None
    for dev in devs:
        data = None
        _LOGGER.info('Dev %s', dev)
        if dev['name'] == 'Controlled Device':
            dev_id =  None
            ctrl_id = dev['id']
            ctrl_temp = ctrl_id
            plug_id = None
            name = 'adam'
            _LOGGER.info('Name %s', name)
            data = api.get_device_data(dev_id, ctrl_id, plug_id)
        if dev['type'] == 'thermostat':
            dev_id = dev['id']
            ctrl_id = ctrl_temp
            plug_id = None
            name = dev['name']
            _LOGGER.info('Name %s', name)
            data = api.get_device_data(dev_id, ctrl_id, plug_id)
        if dev['type'] == 'plug':
            dev_id = None
            ctrl_id = None
            plug_id = dev['id']
            name = dev['name']
            _LOGGER.info('Name %s', name)
            data = api.get_device_data(dev_id, ctrl_id, plug_id)

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
                if sensor == 'electricity_consumed':
                    if 'electricity_consumed' in data:
                        if data['electricity_consumed']:
                            addSensor=True
                if sensor == 'electricity_consumed_interval':
                    if 'electricity_consumed_interval' in data:
                        if data['electricity_consumed_interval']:
                            addSensor=True
                if sensor == 'electricity_produced':
                    if 'electricity_produced' in data:
                        if data['electricity_produced']:
                            addSensor=True
                if sensor == 'electricity_produced_interval':
                    if 'electricity_produced_interval' in data:
                        if data['electricity_produced_interval']:
                            addSensor=True
                if addSensor:
                    _LOGGER.info('Adding sensor.%s', '{}_{}'.format(name, sensor))
                    devices.append(PwThermostatSensor(api,'{}_{}'.format(name, sensor), dev_id, ctrl_id, plug_id, sensor, sensor_type))
                    
    _LOGGER.info('Adding entities:', devices)
    add_entities(devices, True)


class PwThermostatSensor(PwEntity):
    """Representation of a Plugwise thermostat sensor."""

    def __init__(self, api, name, dev_id, ctlr_id, plug_id, sensor, sensor_type):
        """Set up the Plugwise API."""
        self._api = api
        self._name = name
        self._dev_id = dev_id
        self._ctrl_id = ctlr_id
        self._plug_id = plug_id
        self._device = sensor_type[2]
        self._sensor = sensor
        self._sensor_type = sensor_type
        self._state = None

    @property
    def name(self):
        """Return the name of the thermostat, if any."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_class(self):
        """Device class of this entity."""
        if self._sensor_type == "temperature":
            return DEVICE_CLASS_TEMPERATURE
        if self._sensor_type == "battery_level":
            return DEVICE_CLASS_BATTERY
        if self._sensor_type == "illuminance":
            return DEVICE_CLASS_ILLUMINANCE
        if self._sensor_type == "pressure":
            return DEVICE_CLASS_PRESSURE
        if self._sensor_type == "energy_flow" or self._sensor_type == "energy_measured":
            return DEVICE_CLASS_POWER

#    @property
#    def device_state_attributes(self):
#        """Return the state attributes."""
#        return self._state_attributes

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        if self._sensor_type == "temperature":
            return self.hass.config.units.temperature_unit
        if self._sensor_type == "battery_level":
            return "%"
        if self._sensor_type == "illuminance":
            return "lm"
        if self._sensor_type == "pressure":
            return PRESSURE_MBAR
        if self._sensor_type == "energy_flow":
            return POWER_WATT
        if self._sensor_type == "energy_measured":
            return ENERGY_WATT_HOUR


    @property
    def icon(self):
        """Icon for the sensor."""
        if self._sensor_type == "temperature":
            return "mdi:thermometer"
        if self._sensor_type == "battery_level":
            return "mdi:water-battery"
        if self._sensor_type == "illuminance":
            return "mdi:lightbulb-on-outline"
        if self._sensor_type == "pressure":
            return "mdi:water"
        if self._sensor_type == "energy_flow" or self._sensor_type == "energy_measured":
            return "mdi:flash"

    def update(self):
        """Update the data from the thermostat."""
        _LOGGER.debug("Update sensor called")
        data = self._api.get_device_data(self._dev_id, self._ctrl_id, self._plug_id)

        if data is None:
            _LOGGER.debug("Received no data for device %s.", self._name)
        else:
            if self._sensor == 'boiler_temperature':
                if 'boiler_temp' in data:
                    self._state = data['boiler_temp']
            if self._sensor == 'water_pressure':
                if 'water_pressure' in data:
                    self._state = data['water_pressure']
            if self._sensor == 'battery_charge':
                if 'battery' in data:
                    value = float(data['battery'])
                    self._state = int(round(value * 100))
            if self._sensor == 'outdoor_temperature':
                if 'outdoor_temp' in data:
                    self._state = data['outdoor_temp']
            if self._sensor == 'illuminance':
                if 'illuminance' in data:
                    self._state = data['illuminance']
            if self._sensor == 'electricity_consumed':
                if 'electricity_consumed' in data:
                    self._state = data['electricity_consumed']
            if self._sensor == 'electricity_consumed_interval':
                if 'electricity_consumed_interval' in data:
                    self._state = data['electricity_consumed_interval']
            if self._sensor == 'electricity_produced':
                if 'electricity_produced' in data:
                    self._state = data['electricity_produced']
            if self._sensor == 'electricity_produced_interval':
                if 'electricity_produced_interval' in data:
                    self._state = data['electricity_produced_interval']

