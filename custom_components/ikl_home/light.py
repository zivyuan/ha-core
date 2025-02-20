"""Platform for light integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import ColorMode, LightEntity, LightEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the IKL Light platform."""
    # 这里应该从您的第三方平台API获取灯具列表
    # 示例: lights = await get_lights_from_api(config_entry.data["token"])

    lights = []  # 临时示例
    async_add_entities(IKLLight(light) for light in lights)


class IKLLight(LightEntity):
    """Representation of an IKL Light."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_supported_features = LightEntityFeature.TRANSITION

    def __init__(self, light_data: dict) -> None:
        """Initialize an IKL Light."""
        self._light_data = light_data
        self._attr_unique_id = f"ikl_light_{light_data.get('id')}"
        self._attr_name = light_data.get("name", "IKL Light")
        self._attr_is_on = False
        self._attr_brightness = 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        # 实现开灯逻辑
        # await api.turn_on(self._light_data["id"])
        self._attr_is_on = True

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        # 实现关灯逻辑
        # await api.turn_off(self._light_data["id"])
        self._attr_is_on = False

    async def async_update(self) -> None:
        """Fetch new state data for this light."""
        # 实现状态更新逻辑
        # data = await api.get_light_state(self._light_data["id"])
        # self._attr_is_on = data["state"]
        # self._attr_brightness = data["brightness"]
