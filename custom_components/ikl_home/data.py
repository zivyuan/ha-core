"""IKL Home data management."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .auth import AuthError, IKLAuthClient
from .const import API_BASE, API_ENDPOINTS

_LOGGER = logging.getLogger(__name__)


class IKLDataManager:
    """IKL数据管理器."""

    def __init__(
        self,
        hass: HomeAssistant,
        auth_client: IKLAuthClient,
    ) -> None:
        """初始化数据管理器."""
        self.hass = hass
        self._auth_client = auth_client
        self._session = async_get_clientsession(hass)
        self._rooms: list[dict[str, Any]] = []
        self._devices: list[dict[str, Any]] = []

    async def _api_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """发送API请求."""
        try:
            access_token = await self._auth_client.async_get_access_token()
            headers = {
                "aiot_token": access_token,
                "Content-Type": "application/json",
            }

            url = f"{API_BASE}{endpoint}"
            async with self._session.request(
                method,
                url,
                headers=headers,
                **kwargs,
            ) as response:
                response.raise_for_status()
                return await response.json()

        except AuthError as err:
            raise DataError("Authentication failed") from err

    async def async_load_rooms(self) -> list[dict[str, Any]]:
        """加载房间列表."""
        try:
            response = await self._api_request(
                "GET",
                API_ENDPOINTS["ROOM_LIST"],
            )
            self._rooms = response.get("data", [])
            return self._rooms
        except Exception as err:
            _LOGGER.error("Failed to load rooms: %s", err)
            raise DataError("Failed to load rooms") from err

    async def async_load_devices(self) -> list[dict[str, Any]]:
        """加载设备列表."""
        try:
            response = await self._api_request(
                "GET",
                API_ENDPOINTS["DEVICE_LIST"],
            )
            self._devices = response.get("data", [])
            return self._devices
        except Exception as err:
            _LOGGER.error("Failed to load devices: %s", err)
            raise DataError("Failed to load devices") from err

    async def async_get_device_properties(self, device_id: str) -> list[dict[str, Any]]:
        """获取设备属性."""
        try:
            response = await self._api_request(
                "GET",
                f"{API_ENDPOINTS['DEVICE_PROPERTIES']}?deviceId={device_id}",
            )
            return response.get("data", [])
        except Exception as err:
            _LOGGER.error("Failed to get device properties: %s", err)
            raise DataError("Failed to get device properties") from err

    def get_room_devices(self, room_id: str) -> list[dict[str, Any]]:
        """获取指定房间的设备列表."""
        return [device for device in self._devices if device.get("roomId") == room_id]

    @property
    def rooms(self) -> list[dict[str, Any]]:
        """获取房间列表."""
        return self._rooms

    @property
    def devices(self) -> list[dict[str, Any]]:
        """获取设备列表."""
        return self._devices


class DataError(Exception):
    """数据操作错误."""
