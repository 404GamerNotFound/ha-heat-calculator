"""Switch platform for HA Heat Calculator."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_INCLUDE_WARM_WATER, DOMAIN
from .coordinator import HeatCalculatorCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities from a config entry."""
    coordinator: HeatCalculatorCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IncludeWarmWaterSwitch(coordinator, entry)])


class IncludeWarmWaterSwitch(CoordinatorEntity[HeatCalculatorCoordinator], SwitchEntity):
    """Switch to include or exclude warm water consumption."""

    _attr_has_entity_name = True
    _attr_name = "Include Warm Water"
    _attr_icon = "mdi:water-boiler"

    def __init__(self, coordinator: HeatCalculatorCoordinator, entry: ConfigEntry) -> None:
        """Initialize switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_include_warm_water"

    @property
    def is_on(self) -> bool:
        """Return whether warm water subtraction is enabled."""
        return self.coordinator.include_warm_water

    async def async_turn_on(self, **kwargs) -> None:
        """Enable warm water subtraction."""
        await self.coordinator.async_update_options({CONF_INCLUDE_WARM_WATER: True})

    async def async_turn_off(self, **kwargs) -> None:
        """Disable warm water subtraction."""
        await self.coordinator.async_update_options({CONF_INCLUDE_WARM_WATER: False})
