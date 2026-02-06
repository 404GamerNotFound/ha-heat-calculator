"""Select platform for HA Heat Calculator."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CALCULATION_METHODS, CONF_CALCULATION_METHOD, DOMAIN
from .coordinator import HeatCalculatorCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities from a config entry."""
    coordinator: HeatCalculatorCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CalculationMethodSelect(coordinator, entry)])


class CalculationMethodSelect(CoordinatorEntity[HeatCalculatorCoordinator], SelectEntity):
    """Select entity to choose the allocation method."""

    _attr_has_entity_name = True
    _attr_name = "Calculation Method"
    _attr_icon = "mdi:function-variant"
    _attr_options = list(CALCULATION_METHODS)

    def __init__(self, coordinator: HeatCalculatorCoordinator, entry: ConfigEntry) -> None:
        """Initialize select."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_calculation_method"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="HA Heat Calculator",
            model="Heat Allocation",
        )

    @property
    def current_option(self) -> str:
        """Return selected calculation method key."""
        return self.coordinator.calculation_method

    async def async_select_option(self, option: str) -> None:
        """Set calculation method."""
        if option not in CALCULATION_METHODS:
            return
        await self.coordinator.async_update_options({CONF_CALCULATION_METHOD: option})
