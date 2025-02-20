"""Config flow for IKL Home integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .auth import AuthError, IKLAuthClient
from .const import DOMAIN

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

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # 验证认证信息
                auth = IKLAuthClient(
                    self.hass,
                    user_input["app_key"],
                    user_input["app_secret"],
                )
                if not await auth.async_validate_auth():
                    errors["base"] = "invalid_auth"
                else:
                    # 检查是否已存在相同的 app_key 配置
                    await self._async_verify_unique_config(user_input["app_key"])

                    # 使用用户输入的名称或默认名称
                    title = user_input.get("name")
                    if not title:
                        title = f"IKL Home ({user_input['app_key'][:8]}...)"

                    return self.async_create_entry(title=title, data=user_input)
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

    async def _async_verify_unique_config(self, app_key: str) -> None:
        """检查是否存在重复配置."""
        current_entries = self._async_current_entries()

        for entry in current_entries:
            if entry.data.get("app_key") == app_key:
                raise DuplicateConfigError


class DuplicateConfigError(HomeAssistantError):
    """当发现重复配置时抛出的错误."""
