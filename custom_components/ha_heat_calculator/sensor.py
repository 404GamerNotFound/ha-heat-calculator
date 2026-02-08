"""Sensor platform for HA Heat Calculator."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HeatCalculatorCoordinator
from .device import build_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up gas allocation sensors from a config entry."""
    coordinator: HeatCalculatorCoordinator = hass.data[DOMAIN][entry.entry_id]
    gas_state = hass.states.get(coordinator.gas_meter_entity_id)
    native_unit = None if gas_state is None else gas_state.attributes.get("unit_of_measurement")
    if native_unit == "m3":
        native_unit = UnitOfVolume.CUBIC_METERS
    if native_unit is None:
        native_unit = UnitOfVolume.CUBIC_METERS

    currency = hass.config.currency or "EUR"
    entities = []
    for heater_entity_id in coordinator.heaters:
        entities.append(HeaterGasShareSensor(coordinator, entry, heater_entity_id, native_unit))
        entities.append(HeaterGasCostSensor(coordinator, entry, heater_entity_id, currency))
    async_add_entities(entities)


class HeaterGasShareSensor(
    CoordinatorEntity[HeatCalculatorCoordinator], SensorEntity, RestoreEntity
):
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
        self._attr_device_info = build_device_info(entry)

    async def async_added_to_hass(self) -> None:
        """Restore the last stored allocation after restart."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is None:
            return
        try:
            value = float(last_state.state)
        except (TypeError, ValueError):
            return
        heater_stats = self.coordinator.data.get(self._heater_entity_id)
        if heater_stats is None:
            return
        heater_stats.total_allocated = max(0.0, value)

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
            "heater_area": self.coordinator.heater_areas.get(self._heater_entity_id),
            "heater_output_watt": self.coordinator.heater_outputs.get(
                self._heater_entity_id
            ),
            "effort_window": round(self.coordinator.data[self._heater_entity_id].effort_window, 3),
            "last_delta_gas": round(self.coordinator.last_delta_gas, 6),
            "last_distributable_gas": round(self.coordinator.last_distributable_gas, 6),
            "last_warm_water_deducted": round(self.coordinator.last_warm_water_deducted, 6),
            "last_distribution_time": None
            if self.coordinator.last_distribution_time is None
            else self.coordinator.last_distribution_time.isoformat(),
        }


class HeaterGasCostSensor(
    CoordinatorEntity[HeatCalculatorCoordinator], SensorEntity, RestoreEntity
):
    """Cost sensor for one heater entity."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:cash"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: HeatCalculatorCoordinator,
        entry: ConfigEntry,
        heater_entity_id: str,
        currency: str,
    ) -> None:
        """Initialize cost sensor."""
        super().__init__(coordinator)
        self._heater_entity_id = heater_entity_id
        self._attr_unique_id = f"{entry.entry_id}_{heater_entity_id}_allocated_cost"
        heater_name = heater_entity_id.split(".", maxsplit=1)[-1].replace("_", " ").title()
        self._attr_name = f"{heater_name} Gas Cost"
        self._attr_native_unit_of_measurement = currency
        self._attr_device_info = build_device_info(entry)

    async def async_added_to_hass(self) -> None:
        """Restore the last stored cost value after restart."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is None:
            return
        try:
            last_cost = float(last_state.state)
        except (TypeError, ValueError):
            return
        heater_stats = self.coordinator.data.get(self._heater_entity_id)
        if heater_stats is None:
            return
        if heater_stats.total_allocated > 0:
            return
        if self.coordinator.gas_price <= 0:
            return
        heater_stats.total_allocated = max(0.0, last_cost / self.coordinator.gas_price)

    @property
    def native_value(self) -> float:
        """Return the calculated gas cost."""
        allocated = self.coordinator.data[self._heater_entity_id].total_allocated
        return round(allocated * self.coordinator.gas_price, 3)
