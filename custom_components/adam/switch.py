"""Plugwise Water Heater component for HomeAssistant."""

import logging
import plugwise

from . import (
    DOMAIN,
    DATA_ADAM,
)

from homeassistant.components.switch import SwitchDevice

_LOGGER = logging.getLogger(__name__)

SWITCH_ICON = "mdi:electric-switch"

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Add the Plugwise Plug."""

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
        if dev['type'] == 'plug':
            plug_id = dev['id']
            plug_type = dev['type']
            name = dev['name']
            _LOGGER.info('Name %s', name)
            data = data = api.get_device_data(None, None, plug_id)

            if data is None:
                _LOGGER.debug("Received no data for device %s.", name)
            else:
                device = PwSwitch(api, name, plug_type, plug_id)
                _LOGGER.info('Adding switch.%s', name)
                if not device:
                    continue
                devices.append(device)
    add_entities(devices, True)


class PwSwitch(SwitchDevice):
    """Representation of a Plugwise plug."""

    def __init__(self, api, name, plug_type, plug_id):
        """Set up the Plugwise API."""
        self._api = api
        self._name = name
        self._plug_id = plug_id
        self._plug_type = None
        self._device_is_on = False

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._device_is_on

    def turn_on(self, **kwargs):
        """Turn the device on."""
        _LOGGER.debug("Turn switch.%s on.", self._name)
        self._api.set_relay_state(self._plug_id, self._plug_type, 'on')
        self._api.full_update_device()
        self.update()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        _LOGGER.debug("Turn switch.%s off.", self._name)
        self._api.set_relay_state(self._plug_id, self._plug_type, 'off')
        self._api.full_update_device()
        self.update()

    @property
    def name(self):
        """Return the name of the thermostat, if any."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return SWITCH_ICON

    def update(self):
        """Update the data from the Plugs."""
        _LOGGER.debug("Update switch called")

        data = self._api.get_device_data(None, None, self._plug_id)

        if data is None:
            _LOGGER.debug("Received no data for device %s.", self._name)
        else:
            if 'relay' in data:
                self._plug_type = data['type']
                self._device_is_on = (data['relay'] == 'on')
                _LOGGER.debug("Switch is ON is %s.", self._device_is_on)

