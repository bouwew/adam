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
    DATA_ADAM,
    PwEntity,
)

_LOGGER = logging.getLogger(__name__)

# Configuration directives
CONF_MIN_TEMP = "min_temp"
CONF_MAX_TEMP = "max_temp"
DEFAULT_MIN_TEMP = 4
DEFAULT_MAX_TEMP = 30

# HVAC modes
HVAC_MODES_1 = [HVAC_MODE_HEAT, HVAC_MODE_AUTO]
HVAC_MODES_2 = [HVAC_MODE_HEAT_COOL, HVAC_MODE_AUTO]

SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE)

THERMOSTAT_ICON = "mdi:thermometer"

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

    api = hass.data[DATA_ADAM].data

    devices = []
    ctrl_id = None
    try:
        devs = api.get_devices()
    except RuntimeError:
        _LOGGER.error("Unable to get location info from the API")
        return
    
    for dev in devs:
        if dev['name'] == 'Controlled Device':
            ctrl_id = dev['id']
        if dev['type'] == "thermostat":
            device = PwThermostat(api, dev['name'], dev['id'], ctrl_id, DEFAULT_MIN_TEMP, DEFAULT_MAX_TEMP)
            if not device:
                continue
            devices.append(device)
            _LOGGER.info('Adding climate.%s', dev['name'])
    add_entities(devices, True)

#    hass.helpers.discovery.load_platform('climate', DOMAIN, {}, config)


class PwThermostat(PwEntity, ClimateDevice):
    """Representation of an Plugwise thermostat."""

    def __init__(self, api, name, dev_id, ctlr_id, min_temp, max_temp):
        """Set up the Plugwise API."""
        self._api = api
        self._name = name
        self._dev_id = dev_id
        self._ctrl_id = ctlr_id
        self._min_temp = min_temp
        self._max_temp = max_temp

        self._dev_type = None
        self._selected_schema = None
        self._last_active_schema = None
        self._preset_mode = None
        self._presets = None
        self._presets_list = None
        self._boiler_status = None
        self._cooling_status = None
        self._dhw_status = None
        self._heating_status = None
        self._schema_names = None
        self._schema_status = None
        self._current_temp = None
        self._thermostat_temp = None
        self._boiler_temp = None
        self._water_pressure = None
        self._schedule_temp = None
        self._hvac_mode = None

    @property
    def hvac_action(self):
        """Return the current action."""
        if self._heating_status or self._boiler_status or self._dhw_status:
            return CURRENT_HVAC_HEAT
        if self._cooling_status:
            return CURRENT_HVAC_COOL
        return CURRENT_HVAC_IDLE

    @property
    def name(self):
        """Return the name of the thermostat, if any."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return THERMOSTAT_ICON

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
        attributes = {}
        if self._schema_names:
            attributes["available_schemas"] = self._schema_names
        if self._selected_schema:
            attributes["selected_schema"] = self._selected_schema
        return attributes

    @property
    def preset_modes(self):
        """
        Return the available preset modes list and make the presets with their
        temperatures available.
        """
        return self._presets_list

    @property
    def hvac_modes(self):
        """Return the available hvac modes list."""
        if self._heating_status is not None or self._boiler_status is not None:
            if self._cooling_status is not None:
                return HVAC_MODES_2
            return HVAC_MODES_1

    @property
    def hvac_mode(self):
        """Return current active hvac state."""
        if self._schema_status:
            return HVAC_MODE_AUTO
        if self._heating_status or self._boiler_status or self._dhw_status:
            if self._cooling_status:
                return HVAC_MODE_HEAT_COOL
            return HVAC_MODE_HEAT
        return HVAC_MODE_OFF

    @property
    def target_temperature(self):
        """Return the target_temperature.

        From the XML the thermostat-value is used because it updates 'immediately'
        compared to the target_temperature-value. This way the information on the card
        is "immediately" updated after changing the preset, temperature, etc.
        """
        return self._thermostat_temp

    @property
    def preset_mode(self):
        """Return the active preset."""
        if self._presets:
            return self._preset_mode
        return None

    @property
    def current_temperature(self):
        """Return the current room temperature."""
        return self._current_temp

    @property
    def min_temp(self):
        """Return the minimal temperature possible to set."""
        return self._min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature possible to set."""
        return self._max_temp

    @property
    def temperature_unit(self):
        """Return the unit of measured temperature."""
        return TEMP_CELSIUS
        
    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if (temperature is not None) and (self._min_temp < temperature < self._max_temp):
            _LOGGER.debug("Adjusting temperature to %s degrees C.", temperature)
            self._api.set_temperature(self._dev_id, self._dev_type, temperature)
            self._api.get_appliances()
        else:
            _LOGGER.error("Invalid temperature requested")

    def set_hvac_mode(self, hvac_mode):
        """Set the hvac mode."""
        _LOGGER.debug("Adjusting hvac_mode to %s", hvac_mode)
        state = "false"
        if hvac_mode == HVAC_MODE_AUTO:
            state = "true"
        self._api.set_schedule_state(self._dev_id, self._last_active_schema, state)
        self._api.get_domain_objects()
        self._api.get_appliances()

    def set_preset_mode(self, preset_mode):
        _LOGGER.debug("Adjusting preset to %s", preset_mode)
        """Set the preset mode."""
        self._api.set_preset(self._dev_id, self._dev_type, preset_mode)
        self._api.get_domain_objects()
        self._api.get_appliances()

    def update(self):
        """Update the data for this climate device."""
        _LOGGER.debug("Update climate called")
        data = self._api.get_device_data(self._dev_id, self._ctrl_id, None)

        if data is None:
            _LOGGER.debug("Received no data for device %s.", self._name)
        else:            
            if 'type' in data:
                self._dev_type = data['type']
            if 'setpoint_temp' in data:
                self._thermostat_temp = data['setpoint_temp']
            if 'current_temp' in data:
                self._current_temp = data['current_temp']
            if 'boiler_temp' in data:
                self._boiler_temp = data['boiler_temp']
            if 'available_schedules' in data:
                self._schema_names = data['available_schedules']
            if 'selected_schedule' in data:
                self._selected_schema = data['selected_schedule']
                if self._selected_schema != None:
                    self._schema_status = True
                    self._schedule_temp = self._thermostat_temp
                else:
                    self._schema_status = False
            if 'last_used' in data:
                self._last_active_schema = data['last_used']
            if 'presets' in data:
                self._presets = data['presets']
                if self._presets:
                    self._presets_list = list(self._presets)
            if 'active_preset' in data:
                self._preset_mode = data['active_preset']
            if 'boiler_state' in data:
                self._boiler_status = data['boiler_state']
            if 'central_heating_state' in data:
                self._heating_status = data['central_heating_state']
            if 'cooling_state' in data:
                self._cooling_status = data['cooling_state']
            if 'dhw_state' in data:
                self._dhw_status = data['dhw_state']
