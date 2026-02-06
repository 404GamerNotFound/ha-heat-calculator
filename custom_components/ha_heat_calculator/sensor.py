"""Sensor platform for HA Heat Calculator."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HeatCalculatorCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up gas allocation sensors from a config entry."""
    coordinator: HeatCalculatorCoordinator = hass.data[DOMAIN][entry.entry_id]
    gas_state = hass.states.get(coordinator.gas_meter_entity_id)
    native_unit = None if gas_state is None else gas_state.attributes.get("unit_of_measurement")

    entities = [
        HeaterGasShareSensor(coordinator, entry, heater_entity_id, native_unit)
        for heater_entity_id in coordinator.heaters
    ]
    async_add_entities(entities)


class HeaterGasShareSensor(CoordinatorEntity[HeatCalculatorCoordinator], SensorEntity):
    """Gas share sensor for one heater entity."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:fire"

    def __init__(
        self,
        coordinator: HeatCalculatorCoordinator,
        entry: ConfigEntry,
        heater_entity_id: str,
        native_unit: str | None,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._heater_entity_id = heater_entity_id
        self._attr_unique_id = f"{entry.entry_id}_{heater_entity_id}_allocated_gas"
        heater_name = heater_entity_id.split(".", maxsplit=1)[-1].replace("_", " ").title()
        self._attr_name = f"{heater_name} Gas Consumption"
        self._attr_native_unit_of_measurement = native_unit

    @property
    def native_value(self) -> float:
        """Return allocated gas consumption."""
        return round(self.coordinator.data[self._heater_entity_id].total_allocated, 3)

    @property
    def extra_state_attributes(self) -> dict[str, str | float | None]:
        """Return additional metadata for transparency."""
        return {
            "heater_entity": self._heater_entity_id,
            "gas_meter_entity": self.coordinator.gas_meter_entity_id,
            "calculation_method": self.coordinator.calculation_method,
            "effort_window": round(self.coordinator.data[self._heater_entity_id].effort_window, 3),
            "last_delta_gas": round(self.coordinator.last_delta_gas, 6),
            "last_distributable_gas": round(self.coordinator.last_distributable_gas, 6),
            "last_warm_water_deducted": round(self.coordinator.last_warm_water_deducted, 6),
            "last_distribution_time": None
            if self.coordinator.last_distribution_time is None
            else self.coordinator.last_distribution_time.isoformat(),
        }
