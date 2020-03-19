"""Plugwise Adam component for Home Assistant Core."""

import logging

import voluptuous as vol
import plugwise

from datetime import timedelta
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import track_time_interval
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect, dispatcher_send)
from homeassistant.helpers import config_validation as cv
from homeassistant.util import Throttle

from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)

from homeassistant.exceptions import PlatformNotReady

_LOGGER = logging.getLogger(__name__)

# Default directives
DEFAULT_NAME = "Adam"
DEFAULT_USERNAME = "smile"
DEFAULT_PORT = 80
DEFAULT_MIN_TEMP = 4
DEFAULT_MAX_TEMP = 30
DOMAIN = 'adam'
DATA_ADAM = "adam_data"
SIGNAL_UPDATE_ADAM = "adam_update"
SCAN_INTERVAL = timedelta(seconds=30)

# Read configuration
#ADAM_CONFIG = vol.Schema(
#        {
#            vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
#            vol.Required(CONF_PASSWORD): cv.string,
#            vol.Required(CONF_HOST): cv.string,
#            vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
#            vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): cv.string,
#        }
#)

# Read platform configuration
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_HOST): cv.string,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): cv.time_period,
#                vol.Optional(CONF_ADAM): vol.All(
#                    cv.ensure_list,
#                    [
#                        vol.All(
#                            cv.ensure_list, [ADAM_CONFIG],
#                        ),
#                    ],
            }
#                )
#            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

def setup(hass, config):
    """Set up the Plugwise (Anna) Thermostat."""
    conf = config.get(DOMAIN)
    scan_interval = conf.get(CONF_SCAN_INTERVAL)

    if conf is None:
        raise PlatformNotReady

    _LOGGER.info('Plugwise %s',conf)
    hass.data[DATA_ADAM] = {}

#    if CONF_ADAM in conf:
#        adams = conf[CONF_ADAM]

#    _LOGGER.info('Adams %s', adams)
#    hass.data[DOMAIN] = {}

#        for adam in adams:
#            _LOGGER.info('Adam %s', adam)
#            adam_config=adam[0]

    adam = plugwise.Plugwise(
            conf[CONF_USERNAME],
            conf[CONF_PASSWORD],
            conf[CONF_HOST],
            conf[CONF_PORT],
    )

    try:
        adam.ping_gateway()
    except OSError:
        _LOGGER.debug("Ping failed, retrying later", exc_info=True)
        raise PlatformNotReady

    hass.data[DATA_ADAM] = PwHub(adam)

    def adam_refresh(event_time):
        """Call Adam to refresh information."""
        _LOGGER.debug("Collecting Adam data")
        hass.data[DATA_ADAM].data.full_update_device()
        dispatcher_send(hass, SIGNAL_UPDATE_ADAM)

    # Call the Plugwise API to refresh updates
    track_time_interval(hass, adam_refresh, scan_interval)

    adam.full_update_device()
    hass.helpers.discovery.load_platform('climate', DOMAIN, {}, config)
    hass.helpers.discovery.load_platform('sensor', DOMAIN, {}, config)
    hass.helpers.discovery.load_platform('switch', DOMAIN, {}, config)
    hass.helpers.discovery.load_platform('water_heater', DOMAIN, {}, config)

    _LOGGER.info('Config %s', hass.data[DATA_ADAM])
    return True


class PwHub:
    """Representation of a base Plugwise device."""

    def __init__(self, data):
        """Initialize the device."""
        self.data = data


class PwEntity(Entity):
    """Entity class for Plugwise devices."""

    def __init__(self, data):
        """Initialize the Hydrawise entity."""
        self.data = data

    async def async_added_to_hass(self):
        """Register callbacks."""
        async_dispatcher_connect(
            self.hass, SIGNAL_UPDATE_ADAM, self._update_callback)

    @callback
    def _update_callback(self):
        """Call update method."""
        self.async_schedule_update_ha_state(True)

