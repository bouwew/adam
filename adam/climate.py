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
DEVICE_ICON = "mdi:power"
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
    for dev in devices:
        if dev['name'] != 'Controlled Device':
            device = create_climate_device(adam, hass, dev["name"], dev["id"])
            if not device:
                continue
            climate_devices.append(device)

    if climate_devices:
        add_entities(climate_devices, True)

def create_climate_device(adam, hass, name, dev_id):
    """Create a Adam climate device."""
    device = PwThermostat(adam, name, dev_id, DEFAULT_MIN_TEMP, DEFAULT_MAX_TEMP)

    adam.add_device(dev_id, {"name": name, "data": device})

    return device

class PwThermostat(ClimateDevice):
    """Representation of an Plugwise thermostat."""

    def __init__(self, api, name, data_id, min_temp, max_temp):
        """Set up the Plugwise API."""
        self._api = api
        self._data_id = data_id

        self._min_temp = min_temp
        self._max_temp = max_temp
        self._name = name
        self._outdoor_temperature = None
        self._selected_schema = None
        self._preset_mode = None
        self._presets = None
        self._presets_list = None
        self._heating_status = None
        self._cooling_status = None
        self._schema_names = None
        self._schema_status = None
        self._current_temperature = None
        self._thermostat_temperature = None
        self._boiler_temperature = None
        self._water_pressure = None
        self._schedule_temperature = None
        self._hvac_mode = None

    @property
    def hvac_action(self):
        """Return the current action."""
        if self._heating_status:
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
        if self._name == "Controlled Device":
            return DEVICE_ICON
        return THERMOSTAT_ICON

    @property
    def supported_features(self):
        """Return the list of supported features."""
        if self._name != "Controlled Device":
            return SUPPORT_FLAGS

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
        attributes = {}
        if self._outdoor_temperature:
            attributes["outdoor_temperature"] = self._outdoor_temperature
        if self._schema_names:
            attributes["available_schemas"] = self._schema_names
        if self._selected_schema:
            attributes["selected_schema"] = self._selected_schema
        if self._boiler_temperature:
            attributes["boiler_temperature"] = self._boiler_temperature
        if self._water_pressure:
            attributes["water_pressure"] = self._water_pressure
        return attributes

    @property
    def preset_modes(self):
        """Return the available preset modes list and make the presets with their
        temperatures available.
        """
        if self._name != "Controlled Device":
            return self._presets_list

    @property
    def hvac_modes(self):
        """Return the available hvac modes list."""
        #if self._name == "Controlled Device":
        if self._heating_status is not None:
            if self._cooling_status is not None:
                return HVAC_MODES_2
            return HVAC_MODES_1

    @property
    def hvac_mode(self):
        """Return current active hvac state."""
        if self._name != "Controlled Device":
            if self._schema_status:
                return HVAC_MODE_AUTO
        else:
            if self._heating_status:
                if self._cooling_status:
                    return HVAC_MODE_HEAT_COOL
                return HVAC_MODE_HEAT

    @property
    def target_temperature(self):
        """Return the target_temperature.

        From the XML the thermostat-value is used because it updates 'immediately'
        compared to the target_temperature-value. This way the information on the card
        is "immediately" updated after changing the preset, temperature, etc.
        """
        return self._thermostat_temperature

    @property
    def preset_mode(self):
        """Return the active selected schedule-name, or the (temporary) active preset
        or Temporary in case of a manual change in the set-temperature.
        """
        if self._presets:
            presets = self._presets
            preset_temperature = presets.get(self._preset_mode, "none")
            if self.hvac_mode == HVAC_MODE_AUTO:
                if self._thermostat_temperature == self._schedule_temperature:
                    return "{}".format(self._selected_schema)
                if self._thermostat_temperature == preset_temperature:
                    return self._preset_mode
                return "Temporary"
            if self._thermostat_temperature != preset_temperature:
                return "Manual"
            return self._preset_mode
        return None

    @property
    def current_temperature(self):
        """Return the current room temperature."""
        return self._current_temperature

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

        data = self._api.get_data(self._data_id)

        if data is None:
            _LOGGER.debug("Received no data for device %s", self._name)
            return

        if 'setpoint temp' in data:
            self._thermostat_temperature = data['setpoint temp']
        if 'current temp' in data:
            self._current_temperature = data['current temp']
        if 'available schedules' in data:
            self._schema_names = data['available schedules']
        if 'selected schedule' in data:
            self._selected_schema = data['selected schedule']
            if self._selected_schema != "None":
                self._schema_status = True
                self._schedule_temperature = self._thermostat_temperature
            else:
                self._schema_status = False
        if 'last used' in data:
            self._last_active_schema = data['last used']
        if 'presets' in data:
            self._presets = data['presets']
            self._presets_list = list(self._presets)
        if 'active preset' in data:
            self._preset_mode = data['active preset']
        if 'boiler state' in data:
            self._boiler_status = data['boiler state']
        if 'central heating state' in data:
            self._heating_status = data['central heating state']
        if 'cooling state' in data:
            self._cooling_status = data['cooling state']
        if 'domestic hot water state' in data:
            self._dhw_status = data['domestic hot water state']
        if 'water temp' in data:
            self._boiler_temperature = data['water temp']
        if 'boiler pressure' in data:
            self._water_pressure = data['boiler pressure']
        if 'outdoor temp' in data:
            self._outdoor_temperature = data['outdoor temp']

