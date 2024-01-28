"""Support for setting qBitTorrent client to Alternative Speed Limits."""
from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import QBittorrentDataCoordinator

_LOGGING = logging.getLogger(__name__)


@dataclass(frozen=True)
class QBittorrentSwitchEntityDescriptionMixin:
    """Mixin for required keys."""

    is_on_func: Callable[[QBittorrentDataCoordinator], bool | None]
    on_func: Callable[[QBittorrentDataCoordinator], None]
    off_func: Callable[[QBittorrentDataCoordinator], None]
    toggle_func: Callable[[QBittorrentDataCoordinator], None]


@dataclass(frozen=True)
class QBittorrentSwitchEntityDescription(
    SwitchEntityDescription, QBittorrentSwitchEntityDescriptionMixin
):
    """Entity description class for qBittorent switches."""


SWITCH_TYPES: tuple[QBittorrentSwitchEntityDescription, ...] = (
    QBittorrentSwitchEntityDescription(
        key="alternative_speed_limits",
        translation_key="alternative_speed_limits",
        is_on_func=lambda coordinator: coordinator.get_alt_speed_enabled(),
        on_func=lambda coordinator: coordinator.set_alt_speed_enabled(True),
        off_func=lambda coordinator: coordinator.set_alt_speed_enabled(False),
        toggle_func=lambda coordinator: coordinator.toggle_alt_speed_enabled(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the qBittorrent switch."""

    coordinator: QBittorrentDataCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        QBittorrentSwitch(coordinator, description) for description in SWITCH_TYPES
    )


class QBittorrentSwitch(CoordinatorEntity[QBittorrentDataCoordinator], SwitchEntity):
    """Representation of a qBittorrent switch."""

    entity_description: QBittorrentSwitchEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: QBittorrentDataCoordinator,
        entity_description: QBittorrentSwitchEntityDescription,
    ) -> None:
        """Initialize the qBittorrent switch."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}-{entity_description.key}"
        )
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            manufacturer="qBittorrent",
        )

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self.entity_description.is_on_func(self.coordinator)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        await self.hass.async_add_executor_job(
            self.entity_description.on_func, self.coordinator
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        await self.hass.async_add_executor_job(
            self.entity_description.off_func, self.coordinator
        )
        await self.coordinator.async_request_refresh()

    async def async_toggle(self, **kwargs: Any) -> None:
        """Toggle the device."""
        await self.hass.async_add_executor_job(
            self.entity_description.toggle_func, self.coordinator
        )
        await self.coordinator.async_request_refresh()
