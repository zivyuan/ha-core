"""Constants for the IKL Home integration."""

DOMAIN = "ikl_home"

# API Base URL
API_BASE = "https://gateway.ikingcity.com"

# API Endpoints
API_ENDPOINTS = {
    # 用户相关
    "USER_INFO": "/api/aiot-estate/user/info",
    "USER_PROJECTS": "/api/aiot-estate/user/project/list",
    # 房间相关
    "ROOM_LIST": "/api/aiot-estate/app/struct/checked/list",
    # 设备相关
    "DEVICE_LIST": "/api/aiot-estate/device/list",
    "DEVICE_PROPERTIES": "/api/aiot-estate/device/get/property/info/list",
    "DEVICE_CONTROL": "/api/aiot-estate/proxy/api-standard/device/control/set/property",
}
