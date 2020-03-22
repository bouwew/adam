"""Plugwise Adam component for Home Assistant Core."""

import asyncio
import logging

import voluptuous as vol
import plugwise

from datetime import timedelta
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect, dispatcher_send)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

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
PLATFORMS = ["climate"] #, "sensor", "switch", "water_heater"]


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

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Plugwise platform."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Plugwise Smiles from a config entry."""
    # TODO Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)

    websession = async_get_clientsession(hass, verify_ssl=False)
    api = plugwise.Plugwise(
                           host = conf[CONF_HOST],
                           password = conf[CONF_PASSWORD],
                           websession = websession
                           )

    await api.connect()

    update_interval = conf.get(CONF_SCAN_INTERVAL)

    _LOGGER.debug("Plugwise async update interval %s", scan_interval)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "updater": SmileDataUpdater(
            hass, "device", entry.entry_id, api, "full_update_device", update_interval
        ),
    }

    #_LOGGER.debug("Plugwise async entry hass data %s",hass.data[DOMAIN])
    # hass.data[DOMAIN][entry.entry_id] = api

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    async def async_refresh_all(_):
        """Refresh all Smile data."""
        for info in hass.data[DOMAIN].values():
            await info["updater"].async_refresh_all()

    # Register service
    hass.services.async_register(DOMAIN, "update", async_refresh_all)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class SmileDataUpdater:
    """Data storage for single API endpoint."""

    def __init__(
        self,
        hass: HomeAssistant,
        data_type: str,
        config_entry_id: str,
        api: Smile,
        update_method: str,
        update_interval: timedelta,
    ):
        """Initialize global data updater."""
        self.hass = hass
        self.data_type = data_type
        self.config_entry_id = config_entry_id
        self.api = api
        self.update_method = update_method
        self.update_interval = update_interval
        self.listeners = []
        self._unsub_interval = None

    @callback
    def async_add_listener(self, update_callback):
        """Listen for data updates."""
        # This is the first listener, set up interval.
        if not self.listeners:
            self._unsub_interval = async_track_time_interval(
                self.hass, self.async_refresh_all, self.update_interval
            )

        self.listeners.append(update_callback)

    @callback
    def async_remove_listener(self, update_callback):
        """Remove data update."""
        self.listeners.remove(update_callback)

        if not self.listeners:
            self._unsub_interval()
            self._unsub_interval = None

    async def async_refresh_all(self, _now: Optional[int] = None) -> None:
        """Time to update."""
        _LOGGER.debug("Plugwise Smile updating with interval: %s", self.update_interval)
        if not self.listeners:
            _LOGGER.debug("Plugwise Smile has no listeners, not updating")
            return

        _LOGGER.debug("Plugwise Smile updating data using: %s", self.update_method)
        #await self.hass.async_add_executor_job(
            # getattr(self.api, self.update_method)
        #)
        await self.api.full_update_device()

        for update_callback in self.listeners:
            update_callback()


