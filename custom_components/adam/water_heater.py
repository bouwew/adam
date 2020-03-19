"""Plugwise Water Heater component for HomeAssistant."""

import logging
import plugwise

from homeassistant.helpers.entity import Entity

from . import (
    DOMAIN,
    DATA_ADAM,
)

from homeassistant.components.climate.const import (
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
)

_LOGGER = logging.getLogger(__name__)

CURRENT_HVAC_DHW = "dhw"
WATER_HEATER_ICON = "mdi:thermometer"

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Add the Plugwise Water Heater."""

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
    for dev in devs:
        data = None
        _LOGGER.info('Dev %s', dev)
        if dev['name'] == 'Controlled Device':
            ctrl_id = dev['id']
            dev_id = None
            name = 'adam'
            _LOGGER.info('Name %s', name)
            data = api.get_device_data(dev_id, ctrl_id, None)

            if data is None:
                _LOGGER.debug("Received no data for device %s.", name)
                return

            device = PwWaterHeater(api, name, dev_id, ctrl_id)
            _LOGGER.info('Adding water_heater.%s', name)
            if not device:
                continue
            devices.append(device)
    add_entities(devices, True)


class PwWaterHeater(Entity):
    """Representation of a Plugwise water_heater."""

    def __init__(self, api, name, dev_id, ctlr_id):
        """Set up the Plugwise API."""
        self._api = api
        self._name = name
        self._dev_id = dev_id
        self._ctrl_id = ctlr_id
        self._cooling_status = None
        self._heating_status =  None 
        self._boiler_status = None
        self._dhw_status = None

    @property
    def name(self):
        """Return the name of the thermostat, if any."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._heating_status or self._boiler_status:
            return CURRENT_HVAC_HEAT
        if self._dhw_status:
            return CURRENT_HVAC_DHW
        if self._cooling_status:
            return CURRENT_HVAC_COOL
        return CURRENT_HVAC_IDLE

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return WATER_HEATER_ICON

    def update(self):
        """Update the data from the water_heater."""
        _LOGGER.debug("Update water_heater called")
        data = self._api.get_device_data(self._dev_id, self._ctrl_id, None)

        if data is None:
            _LOGGER.debug("Received no data for device %s.", self._name)
        else:
            if 'central_heating_state' in data:
                self._heating_status =  data['central_heating_state'] 
            if 'boiler_state' in data:
                self._boiler_status = data['boiler_state']
            if 'cooling_state' in data:
                self._cooling_status = data['cooling_state'] 
            if 'dhw_state' in data:
                self._dhw_status = data['dhw_state'] 
