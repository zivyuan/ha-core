"""IKL Home authentication."""

from __future__ import annotations

import logging

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_BASE

_LOGGER = logging.getLogger(__name__)


class IKLAuthClient:
    """IKL认证客户端."""

    def __init__(
        self,
        hass: HomeAssistant,
        app_key: str,
        app_secret: str,
    ) -> None:
        """初始化认证客户端."""
        self.hass = hass
        self.app_key = app_key
        self.app_secret = app_secret
        self.session = async_get_clientsession(hass)
        self._access_token: str | None = None

    async def async_get_access_token(self) -> str:
        """获取访问令牌."""
        if not self._access_token:
            await self.async_authenticate()
        return self._access_token

    async def async_authenticate(self) -> None:
        """进行认证."""
        # TODO: 完成认证逻辑
        try:
            async with self.session.post(
                f"{API_BASE}/auth/token",
                json={
                    "app_key": self.app_key,
                    "app_secret": self.app_secret,
                },
            ) as response:
                response.raise_for_status()
                result = await response.json()
                self._access_token = result["access_token"]
        except aiohttp.ClientError as err:
            _LOGGER.error("Authentication failed: %s", err)
            raise AuthError("Failed to authenticate") from err

    async def async_validate_auth(self) -> bool:
        """验证认证信息是否有效."""
        try:
            await self.async_authenticate()
            return True
        except AuthError:
            return False


class AuthError(Exception):
    """认证错误."""
