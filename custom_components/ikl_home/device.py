"""IKL Home device base."""

from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .auth import AuthError, IKLAuthClient
from .const import API_BASE

_LOGGER = logging.getLogger(__name__)


class IKLDevice:
    """IKL设备基础类."""

    def __init__(
        self,
        hass: HomeAssistant,
        auth_client: IKLAuthClient,
        device_id: str,
        device_third_id: str,
    ) -> None:
        """初始化设备."""
        self.hass = hass
        self._auth_client = auth_client
        self._device_id = device_id
        self._device_third_id = device_third_id
        self._session = async_get_clientsession(hass)
        self._available = True

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
                "aiot_token": f"{access_token}",
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
                self._available = True
                # 先获取响应文本
                text = await response.text()
                if not text:  # 如果响应为空
                    return {}
                try:
                    return json.loads(text)  # 尝试解析JSON
                except json.JSONDecodeError:
                    _LOGGER.warning(
                        "Response is not JSON format. Response text: %s",
                        text[:200],  # 只记录前200个字符以避免日志过长
                    )
                    return {"raw_response": text}

        except AuthError as err:
            self._available = False
            raise DeviceError("Authentication failed") from err
        except aiohttp.ClientError as err:
            self._available = False
            raise DeviceError(f"Request failed: {err}") from err

    async def async_update(self) -> None:
        """更新设备状态."""
        try:
            response = await self._api_request(
                "GET",
                f"/api/aiot-estate/device/get/property/info/list?deviceId={self.device_id}",
            )
            await self._handle_state_update(response)
        except DeviceError as err:
            _LOGGER.error("Failed to update device %s: %s", self._device_id, err)
            self._available = False

    async def _handle_state_update(self, state_data: dict[str, Any]) -> None:
        """处理状态更新数据.

        子类需要实现此方法来处理具体的状态数据.
        """
        _LOGGER.info(state_data)
        raise NotImplementedError

    async def async_set_property(self, props: dict[str, any]) -> None:
        """设置设备属性."""
        try:
            jsonObj = {"deviceId": self._device_third_id, "property": props}
            await self._api_request(
                method="POST",
                endpoint="/api/aiot-estate/proxy/api-standard/device/control/set/property",
                json=jsonObj,
            )

        except DeviceError as err:
            _LOGGER.error(
                "Failed to set device property %s: %s", self._device_third_id, err
            )
            self._available = False

    @property
    def available(self) -> bool:
        """设备是否可用."""
        return self._available

    @property
    def device_id(self) -> str:
        """获取设备ID."""
        return self._device_id


class DeviceError(Exception):
    """DeviceError."""
