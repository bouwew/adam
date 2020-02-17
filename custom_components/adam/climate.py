"""Plugwise Adam Climate component for HomeAssistant."""

import logging

import voluptuous as vol
import haanna

import homeassistant.helpers.config_validation as cv
from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateDevice
from homeassistant.components.climate.const import (
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_IDLE,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_AUTO,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    TEMP_CELSIUS,
)
from . import DATA
#from homeassistant.exceptions import PlatformNotReady

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE

_LOGGER = logging.getLogger(__name__)

# Configuration directives
CONF_MIN_TEMP = "min_temp"
CONF_MAX_TEMP = "max_temp"

# Default directives
#DEFAULT_NAME = "Plugwise Adam Development Controller"
DEFAULT_TIMEOUT = 10
THERMOSTAT_ICON = "mdi:thermometer"
DEFAULT_MIN_TEMP = 4
DEFAULT_MAX_TEMP = 30

# HVAC modes
HVAC_MODES_1 = [HVAC_MODE_HEAT, HVAC_MODE_AUTO]
HVAC_MODES_2 = [HVAC_MODE_HEAT_COOL, HVAC_MODE_AUTO]

# Read platform configuration
#PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
#    {
#        vol.Optional(CONF_MIN_TEMP, default=DEFAULT_MIN_TEMP): cv.positive_int,
#        vol.Optional(CONF_MAX_TEMP, default=DEFAULT_MAX_TEMP): cv.positive_int,
#    }
#)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Add the Plugwise ClimateDevice."""
    adam = hass.data[DATA]

    try:
        devices = adam.getDevices()
    except RuntimeError:
        _LOGGER.error("Unable to get location info from the API")
        return


    climate_devices = []
    global controlled_device_id
    ctrl_id = None
    for dev in devices:
        if dev['name'] == 'Controlled Device':
            ctrl_id = dev['id']
        else:
            device = create_climate_device(adam, hass, dev['name'], dev['id'], ctrl_id )
            if not device:
                continue
            climate_devices.append(device)

    if climate_devices:
        add_entities(climate_devices, True)

def create_climate_device(adam, hass, name, dev_id, ctlr_id):
    """Create a Adam climate device."""
    device = PwThermostat(adam, name, dev_id, ctlr_id, DEFAULT_MIN_TEMP, DEFAULT_MAX_TEMP)

    adam.add_device(dev_id, {"ctrl_id": ctlr_id, "name": name, "data": device})

    return device

class PwThermostat(ClimateDevice):
    """Representation of an Plugwise thermostat."""

    def __init__(self, api, name, dev_id, ctlr_id, min_temp, max_temp):
        """Set up the Plugwise API."""
        self._api = api
        self._dev_id = dev_id
        self._ctrl_id = ctlr_id

        self._min_temp = min_temp
        self._max_temp = max_temp
        self._name = name
        self._outdoor_temp = None
        self._dev_type = None
        self._selected_schema = None
        self._preset_mode = None
        self._presets = None
        self._presets_list = None
        self._heating_status = None
        self._cooling_status = None
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
        if self._outdoor_temp:
            attributes["outdoor_temperature"] = self._outdoor_temp
        if self._schema_names:
            attributes["available_schemas"] = self._schema_names
        if self._selected_schema:
            attributes["selected_schema"] = self._selected_schema
        if self._boiler_temp:
            attributes["boiler_temperature"] = self._boiler_temp
        if self._water_pressure:
            attributes["water_pressure"] = self._water_pressure
        return attributes

    @property
    def preset_modes(self):
        """Return the available preset modes list and make the presets with their
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
        """Return the active selected schedule-name, or the (temporary) active preset
        or Temporary in case of a manual change in the set-temperature.
        """
        if self._presets:
            presets = self._presets
            preset_temp = presets.get(self._preset_mode, "none")
            if self.hvac_mode == HVAC_MODE_AUTO:
                if self._thermostat_temp == self._schedule_temp:
                    return "{}".format(self._selected_schema)
                if self._thermostat_temp == preset_temp:
                    return self._preset_mode
                return "Temporary"
            if self._thermostat_temp != preset_temp:
                return "Manual"
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

    def update(self):
        """Update the state of this climate device."""
        self._api.update()

        data = self._api.get_data(self._dev_id)

        if data is None:
            _LOGGER.debug("Received no data for device %s", self._name)
            return

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
            if self._selected_schema != "None":
                self._schema_status = True
                self._schedule_temp = self._thermostat_temp
            else:
                self._schema_status = False
        if 'last_used' in data:
            self._last_active_schema = data['last_used']
        if 'presets' in data:
            self._presets = data['presets']
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


