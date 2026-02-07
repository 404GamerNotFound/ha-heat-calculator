"""Number platform for HA Heat Calculator."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_GAS_PRICE, CONF_WARM_WATER_PERCENT, DOMAIN
from .coordinator import HeatCalculatorCoordinator
from .device import build_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities from a config entry."""
    coordinator: HeatCalculatorCoordinator = hass.data[DOMAIN][entry.entry_id]
    gas_state = hass.states.get(coordinator.gas_meter_entity_id)
    gas_unit = None if gas_state is None else gas_state.attributes.get("unit_of_measurement")
    if gas_unit == "m3":
        gas_unit = UnitOfVolume.CUBIC_METERS
    if gas_unit is None:
        gas_unit = UnitOfVolume.CUBIC_METERS

    currency = hass.config.currency or "EUR"
    async_add_entities(
        [
            WarmWaterPercentNumber(coordinator, entry),
            GasPriceNumber(coordinator, entry, gas_unit, currency),
        ]
    )


class WarmWaterPercentNumber(CoordinatorEntity[HeatCalculatorCoordinator], NumberEntity):
    """Number entity to control warm water percentage."""

    _attr_has_entity_name = True
    _attr_name = "Warm Water Percentage"
    _attr_icon = "mdi:percent"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = "slider"

    def __init__(self, coordinator: HeatCalculatorCoordinator, entry: ConfigEntry) -> None:
        """Initialize number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_warm_water_percent"
        self._attr_device_info = build_device_info(entry)

    @property
    def native_value(self) -> float:
        """Return configured warm water percentage."""
        return self.coordinator.warm_water_percent

    async def async_set_native_value(self, value: float) -> None:
        """Set warm water percentage."""
        await self.coordinator.async_update_options(
            {CONF_WARM_WATER_PERCENT: round(float(value), 2)}
        )


class GasPriceNumber(CoordinatorEntity[HeatCalculatorCoordinator], NumberEntity):
    """Number entity to control the gas price per cubic meter."""

    _attr_has_entity_name = True
    _attr_name = "Gas Price"
    _attr_icon = "mdi:currency-eur"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 0.01
    _attr_mode = "box"

    def __init__(
        self,
        coordinator: HeatCalculatorCoordinator,
        entry: ConfigEntry,
        gas_unit: str,
        currency: str,
    ) -> None:
        """Initialize number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_gas_price"
        self._attr_device_info = build_device_info(entry)
        self._attr_native_unit_of_measurement = f"{currency}/{gas_unit}"

    @property
    def native_value(self) -> float:
        """Return configured gas price."""
        return round(self.coordinator.gas_price, 4)

    async def async_set_native_value(self, value: float) -> None:
        """Set gas price."""
        await self.coordinator.async_update_options({CONF_GAS_PRICE: round(float(value), 4)})
