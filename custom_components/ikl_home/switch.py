"""Platform for switch integration."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import yaml

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .auth import IKLAuthClient
from .device import DeviceError, IKLDevice

_LOGGER = logging.getLogger(__name__)


# 加载设备配置
def load_device_config() -> dict:
    """加载设备配置."""
    config_path = os.path.join(os.path.dirname(__file__), "device_config.yaml")
    try:
        with open(config_path, encoding="utf-8") as file:
            return yaml.safe_load(file)
    except Exception as err:
        _LOGGER.error("Failed to load device config: %s", err)
        return {}


DEVICE_CONFIG = load_device_config()


keyNames = [
    "power",
    "k0_power",
    "k1_power",
    "k2_power",
    "k3_power",
    "k4_power",
    "k5_power",
    "k6_power",
]


def get_switch_keys(props):
    """获取按键列表."""
    keys = []
    for key in props:
        code = key.get("code")
        if code in keyNames:
            keys.append(key)

    return keys


class IKLSwitchDevice(IKLDevice):
    """IKL开关设备."""

    def __init__(
        self,
        hass: HomeAssistant,
        auth_client: IKLAuthClient,
        device_id: str,
        device_third_id: str,
        code: str = "power",
    ) -> None:
        """初始化设备."""
        super().__init__(hass, auth_client, device_id, device_third_id)
        self._code = code
        self._state = False

    async def _handle_state_update(self, state_data: dict[str, Any]) -> None:
        """处理开关状态更新."""
        if state_data.get("data"):
            for prop in state_data["data"]:
                if prop["code"] == self._code:
                    self._state = prop["value"] == "1"
                    break
        else:
            self._state = False

    async def async_turn_on(self) -> None:
        """打开开关."""
        await self.async_set_property({"power": "1"})
        await asyncio.sleep(0.3)  # 等待设备状态更新
        await self.async_update()  # 从设备获取最新状态

    async def async_turn_off(self) -> None:
        """关闭开关."""
        await self.async_set_property({"power": "0"})
        await asyncio.sleep(0.3)  # 等待设备状态更新
        await self.async_update()  # 从设备获取最新状态

    @property
    def is_on(self) -> bool:
        """返回开关状态."""
        return self._state


class IKLChannelSwitch(SwitchEntity):
    """Representation of a single channel in an IKL Switch Panel."""

    def __init__(
        self,
        hass: HomeAssistant,
        auth_client: IKLAuthClient,
        device: dict,
        key: dict,
    ) -> None:
        """Initialize an IKL Channel Switch."""
        self._device_data = device
        self._key = key

        # 设备ID（面板ID）
        self._device_id = device.get("deviceId", "unknown")
        self._device_third_id = device.get("thirdRealId", "unknown")
        device_name = device.get("name", "未命名开关")
        key_name = key.get("name", "开关")

        # 实体属性设置
        key_code = key.get("code", "power")
        self._attr_unique_id = f"ikl_switch_{self._device_id}_{key_code}"
        self._attr_name = f"{device_name} {key_name}"

        # 初始化设备控制器
        self._device = IKLSwitchDevice(
            hass, auth_client, self._device_id, self._device_third_id
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this switch panel."""
        return DeviceInfo(
            identifiers={("ikl_home", self._device_data.get("deviceId"))},
            name=self._device_data.get("name", "未命名开关"),
            manufacturer="IKL",
            model=self._device_data["model"],
            hw_version=self._device_data.get("currVersion", "Unknown"),
            sw_version=self._device_data.get("firmware_version", "Unknown"),
            suggested_area=self._device_data.get("area", None),
        )

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._device.is_on

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._device.available

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the channel on."""
        try:
            await self._device.async_turn_on()
            self.async_write_ha_state()
        except DeviceError as error:
            _LOGGER.error(
                "Failed to turn on switch %s: %s",
                self._device_id,
                str(error),
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the channel off."""
        try:
            await self._device.async_turn_off()
            self.async_write_ha_state()
        except DeviceError as error:
            _LOGGER.error(
                "Failed to turn off switch %s: %s",
                self._device_id,
                str(error),
            )

    async def async_update(self) -> None:
        """Fetch new state data for this channel."""
        await self._device.async_update()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the IKL Switch platform."""
    auth_client = IKLAuthClient(
        hass,
        config_entry.data["app_key"],
        config_entry.data["app_secret"],
    )

    # 这里应该从您的第三方平台API获取开关面板列表
    panels = [
        {
            "deviceId": "ry.02002.switch.4.6ffab3a4-b8fa-420f-b244-86e62dba25d1",
            "projectId": "1242017326234144770",
            "projectName": None,
            "spaceId": "1845041781018910722",
            "spaceName": None,
            "roomCode": "default",
            "pid": "ry.02002.switch.4",
            "name": "客厅灯",
            "deviceType": None,
            "model": "rexense.laffey.switch1.d8b",
            "thirdRealId": "1859530722278223874",
            "thirdDid": None,
            "sn": None,
            "bind": 1,
            "bindTime": 1739331659000,
            "bindOperator": None,
            "online": 1,
            "switchOn": 0,
            "productName": "智居墙壁开关M1（单键 零火版）",
            "pictureUrl": "[]",
            "productType": "02",
            "productTypeName": "M系列开关",
            "connectType": 20,
            "roomName": "默认",
            "switchFlag": None,
            "addressDetail": None,
            "parentThirdRealId": "1800820678117740546",
            "productGroupDeviceId": None,
            "pictureUrlApp": "http://aihouse-template.ks3-cn-beijing.ksyuncs.com/aiot_opeserve_platform/aiot_opeserve_platform/operation/1ed18d2e-ae22-4c08-b10d-2f945c44f259.png",
            "normallyOpen": None,
            "currVersion": None,
            "lastVersion": "1.0",
            "freezeLock": None,
            # 属性列表
            "properties": [
                {
                    "code": "power",
                    "dataType": "enum",
                    "description": "",
                    "deviceId": "1859530722278223874",
                    "expectValue": None,
                    "id": "1859530722303389697",
                    "imgId": "1501858364470153391",
                    "imgUrl": "http://aihouse-template.ks3-cn-beijing.ksyuncs.com/public/online/product/device/image/switch1_open.png",
                    "name": "按键",
                    "permit": 1,
                    "permitName": None,
                    "scene": "e,a",
                    "thumbnailUrl": "http://aihouse-template.ks3-cn-beijing.ksyuncs.com/public/online/product/device/image/switch1_open.png",
                    "unit": "[-]",
                    "updateTime": "2025-02-20 10:13:04",
                    "value": "0",
                    "valueRange": '[{"description":"关闭","value":"0"},{"description":"开启","value":"1"}]',
                }
            ],
        }
    ]  # 临时示例数据

    entities = []
    for panel in panels:
        keys = get_switch_keys(props=panel.get("properties", []))

        # 为每个通道创建一个开关实体
        for channel in keys:
            entities.append(  # noqa: PERF401
                IKLChannelSwitch(
                    hass,
                    auth_client,
                    panel,
                    channel,
                )
            )

    async_add_entities(entities)
