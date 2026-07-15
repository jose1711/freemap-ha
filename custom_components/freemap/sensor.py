from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    UnitOfLength,
    UnitOfSpeed,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import FreemapCoordinator


@dataclass(frozen=True)
class FreemapSensorDescription(SensorEntityDescription):
    data_key: str = ""


SENSOR_TYPES: tuple[FreemapSensorDescription, ...] = (
    FreemapSensorDescription(
        key="speed",
        data_key="speed",
        name="Rýchlosť",
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
    ),
    FreemapSensorDescription(
        key="altitude",
        data_key="altitude",
        name="Nadmorská výška",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:elevation-rise",
    ),
    FreemapSensorDescription(
        key="battery",
        data_key="battery",
        name="Batéria",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    FreemapSensorDescription(
        key="bearing",
        data_key="bearing",
        name="Smer",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:compass",
    ),
    FreemapSensorDescription(
        key="accuracy",
        data_key="accuracy",
        name="Presnosť GPS",
        native_unit_of_measurement=UnitOfLength.METERS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:map-marker-radius",
    ),
    FreemapSensorDescription(
        key="gsm_signal",
        data_key="gsmSignal",
        name="GSM signál",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:signal",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FreemapCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        FreemapSensor(coordinator, key, description)
        for key in coordinator.tracked_keys()
        for description in SENSOR_TYPES
    )


class FreemapSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: FreemapCoordinator,
        key: Any,
        description: FreemapSensorDescription,
    ) -> None:
        self._coordinator = coordinator
        self._key = key
        self.entity_description = description
        slug = str(key).lower().replace("-", "_")
        self._attr_unique_id = f"{DOMAIN}_{slug}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(key))},
        )

    @property
    def native_value(self) -> Any:
        data = self._coordinator.latest_data.get(self._key, {})
        return data.get(self.entity_description.data_key)

    async def async_added_to_hass(self) -> None:
        self._coordinator.register_callback(self._key, self._on_update)

    async def async_will_remove_from_hass(self) -> None:
        self._coordinator.unregister_callback(self._key, self._on_update)

    @callback
    def _on_update(self) -> None:
        self.async_write_ha_state()
