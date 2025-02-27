"""Config flow for IKL Home integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .auth import AuthError, IKLAuthClient
from .const import API_ENDPOINTS, DOMAIN
from .data import DataError, IKLDataManager

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional("name"): str,
        vol.Required("app_key"): str,
        vol.Required("app_secret"): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for IKL Home."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._auth_client: IKLAuthClient | None = None
        self._data_manager: IKLDataManager | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # 验证认证信息
                self._auth_client = IKLAuthClient(
                    self.hass,
                    user_input["app_key"],
                    user_input["app_secret"],
                )
                if not await self._auth_client.async_validate_auth():
                    errors["base"] = "invalid_auth"
                else:
                    # 检查是否已存在相同的 app_key 配置
                    await self._async_verify_unique_config(user_input["app_key"])
                    self.data = user_input
                    return await self.async_step_rooms()

            except AuthError:
                errors["base"] = "invalid_auth"
            except DuplicateConfigError:
                errors["base"] = "already_configured"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_rooms(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """获取房间列表."""
        if not self._auth_client:
            return self.async_abort(reason="auth_missing")

        if not self._data_manager:
            self._data_manager = IKLDataManager(self.hass, self._auth_client)

        try:
            rooms = await self._data_manager.async_load_rooms()
            self.data["rooms"] = rooms

            # 使用默认标题
            title = self.data.get("name")
            if not title:
                title = f"IKL Home ({self.data['app_key'][:8]}...)"

            return self.async_create_entry(title=title, data=self.data)

        except DataError as err:
            _LOGGER.error("Failed to get room data: %s", err)
            return self.async_abort(reason="room_list_failed")

    async def _async_verify_unique_config(self, app_key: str) -> None:
        """检查是否存在重复配置."""
        current_entries = self._async_current_entries()

        for entry in current_entries:
            if entry.data.get("app_key") == app_key:
                raise DuplicateConfigError


class DuplicateConfigError(HomeAssistantError):
    """当发现重复配置时抛出的错误."""
