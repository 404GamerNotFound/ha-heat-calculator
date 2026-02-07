"""Number platform for HA Heat Calculator."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfArea, UnitOfPower, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_GAS_PRICE,
    CONF_HEATER_AREAS,
    CONF_HEATER_OUTPUTS,
    CONF_WARM_WATER_PERCENT,
    DOMAIN,
)
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
    entities = [
        WarmWaterPercentNumber(coordinator, entry),
        GasPriceNumber(coordinator, entry, gas_unit, currency),
    ]
    for heater_entity_id in coordinator.heaters:
        entities.append(HeaterAreaNumber(coordinator, entry, heater_entity_id))
        entities.append(HeaterOutputNumber(coordinator, entry, heater_entity_id))

    async_add_entities(entities)


class WarmWaterPercentNumber(
    CoordinatorEntity[HeatCalculatorCoordinator], NumberEntity, RestoreEntity
):
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
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_warm_water_percent"
        self._attr_device_info = build_device_info(entry)

    async def async_added_to_hass(self) -> None:
        """Restore the last stored value when options are missing."""
        await super().async_added_to_hass()
        if CONF_WARM_WATER_PERCENT in self._entry.options:
            return
        last_state = await self.async_get_last_state()
        if last_state is None:
            return
        try:
            value = float(last_state.state)
        except (TypeError, ValueError):
            return
        await self.coordinator.async_update_options(
            {CONF_WARM_WATER_PERCENT: round(value, 2)}
        )

    @property
    def native_value(self) -> float:
        """Return configured warm water percentage."""
        return self.coordinator.warm_water_percent

    async def async_set_native_value(self, value: float) -> None:
        """Set warm water percentage."""
        await self.coordinator.async_update_options(
            {CONF_WARM_WATER_PERCENT: round(float(value), 2)}
        )


class GasPriceNumber(
    CoordinatorEntity[HeatCalculatorCoordinator], NumberEntity, RestoreEntity
):
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
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_gas_price"
        self._attr_device_info = build_device_info(entry)
        self._attr_native_unit_of_measurement = f"{currency}/{gas_unit}"

    async def async_added_to_hass(self) -> None:
        """Restore the last stored value when options are missing."""
        await super().async_added_to_hass()
        if CONF_GAS_PRICE in self._entry.options:
            return
        last_state = await self.async_get_last_state()
        if last_state is None:
            return
        try:
            value = float(last_state.state)
        except (TypeError, ValueError):
            return
        await self.coordinator.async_update_options({CONF_GAS_PRICE: round(value, 4)})

    @property
    def native_value(self) -> float:
        """Return configured gas price."""
        return round(self.coordinator.gas_price, 4)

    async def async_set_native_value(self, value: float) -> None:
        """Set gas price."""
        await self.coordinator.async_update_options({CONF_GAS_PRICE: round(float(value), 4)})


class HeaterAreaNumber(
    CoordinatorEntity[HeatCalculatorCoordinator], NumberEntity, RestoreEntity
):
    """Number entity to control the heated area per heater."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:ruler-square"
    _attr_native_min_value = 0
    _attr_native_max_value = 1000
    _attr_native_step = 0.1
    _attr_mode = "box"
    _attr_native_unit_of_measurement = UnitOfArea.SQUARE_METERS

    def __init__(
        self,
        coordinator: HeatCalculatorCoordinator,
        entry: ConfigEntry,
        heater_entity_id: str,
    ) -> None:
        """Initialize number."""
        super().__init__(coordinator)
        self._entry = entry
        self._heater_entity_id = heater_entity_id
        self._attr_unique_id = f"{entry.entry_id}_{heater_entity_id}_heated_area"
        heater_name = heater_entity_id.split(".", maxsplit=1)[-1].replace("_", " ").title()
        self._attr_name = f"{heater_name} Heated Area"
        self._attr_device_info = build_device_info(entry)

    async def async_added_to_hass(self) -> None:
        """Restore the last stored value when options are missing."""
        await super().async_added_to_hass()
        if self._heater_entity_id in self.coordinator.heater_areas:
            return
        last_state = await self.async_get_last_state()
        if last_state is None:
            return
        try:
            value = float(last_state.state)
        except (TypeError, ValueError):
            return
        if value <= 0:
            return
        updated = dict(self.coordinator.heater_areas)
        updated[self._heater_entity_id] = round(value, 2)
        await self.coordinator.async_update_options({CONF_HEATER_AREAS: updated})

    @property
    def native_value(self) -> float:
        """Return configured heated area."""
        return round(self.coordinator.heater_areas.get(self._heater_entity_id, 0.0), 2)

    async def async_set_native_value(self, value: float) -> None:
        """Set heated area."""
        area = float(value)
        updated = dict(self.coordinator.heater_areas)
        if area <= 0:
            updated.pop(self._heater_entity_id, None)
        else:
            updated[self._heater_entity_id] = round(area, 2)
        await self.coordinator.async_update_options({CONF_HEATER_AREAS: updated})


class HeaterOutputNumber(
    CoordinatorEntity[HeatCalculatorCoordinator], NumberEntity, RestoreEntity
):
    """Number entity to control heater output in watts."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:flash"
    _attr_native_min_value = 0
    _attr_native_max_value = 100000
    _attr_native_step = 1
    _attr_mode = "box"
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(
        self,
        coordinator: HeatCalculatorCoordinator,
        entry: ConfigEntry,
        heater_entity_id: str,
    ) -> None:
        """Initialize number."""
        super().__init__(coordinator)
        self._entry = entry
        self._heater_entity_id = heater_entity_id
        self._attr_unique_id = f"{entry.entry_id}_{heater_entity_id}_heater_output"
        heater_name = heater_entity_id.split(".", maxsplit=1)[-1].replace("_", " ").title()
        self._attr_name = f"{heater_name} Heater Output"
        self._attr_device_info = build_device_info(entry)

    async def async_added_to_hass(self) -> None:
        """Restore the last stored value when options are missing."""
        await super().async_added_to_hass()
        if self._heater_entity_id in self.coordinator.heater_outputs:
            return
        last_state = await self.async_get_last_state()
        if last_state is None:
            return
        try:
            value = float(last_state.state)
        except (TypeError, ValueError):
            return
        if value <= 0:
            return
        updated = dict(self.coordinator.heater_outputs)
        updated[self._heater_entity_id] = round(value, 1)
        await self.coordinator.async_update_options({CONF_HEATER_OUTPUTS: updated})

    @property
    def native_value(self) -> float:
        """Return configured heater output."""
        return round(self.coordinator.heater_outputs.get(self._heater_entity_id, 0.0), 1)

    async def async_set_native_value(self, value: float) -> None:
        """Set heater output."""
        output = float(value)
        updated = dict(self.coordinator.heater_outputs)
        if output <= 0:
            updated.pop(self._heater_entity_id, None)
        else:
            updated[self._heater_entity_id] = round(output, 1)
        await self.coordinator.async_update_options({CONF_HEATER_OUTPUTS: updated})
