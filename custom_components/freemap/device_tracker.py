from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import FreemapCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FreemapCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        FreemapDeviceTracker(coordinator, key)
        for key in coordinator.tracked_keys()
    )


class FreemapDeviceTracker(TrackerEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False
    _attr_source_type = SourceType.GPS

    def __init__(self, coordinator: FreemapCoordinator, key: Any) -> None:
        self._coordinator = coordinator
        self._key = key
        slug = _slug(key)
        self._attr_unique_id = f"{DOMAIN}_{slug}_tracker"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(key))},
            name=coordinator.device_names[key],
            manufacturer="Freemap Slovakia",
            model="GPS Tracker",
            configuration_url="https://www.freemap.sk",
        )

    @property
    def _data(self) -> dict:
        return self._coordinator.latest_data.get(self._key, {})

    @property
    def latitude(self) -> float | None:
        return self._data.get("lat")

    @property
    def longitude(self) -> float | None:
        return self._data.get("lon")

    @property
    def location_accuracy(self) -> int:
        acc = self._data.get("accuracy")
        return int(acc) if acc is not None else 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        d = self._data
        attrs: dict[str, Any] = {}
        for field in ("altitude", "speed", "bearing", "battery", "gsmSignal", "message", "ts"):
            val = d.get(field)
            if val is not None:
                attrs[field] = val
        return attrs

    async def async_added_to_hass(self) -> None:
        self._coordinator.register_callback(self._key, self._on_update)

    async def async_will_remove_from_hass(self) -> None:
        self._coordinator.unregister_callback(self._key, self._on_update)

    @callback
    def _on_update(self) -> None:
        self.async_write_ha_state()


def _slug(key: Any) -> str:
    return str(key).lower().replace("-", "_")
