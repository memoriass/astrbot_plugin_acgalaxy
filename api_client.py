"""
ACGalaxy API 客户端
"""

from typing import Any, Dict, List, Optional

import httpx
from astrbot.api import logger

from .models import (
    ACGEvent,
    ACGListResponse,
    APIResponse,
    Guest,
    GuestACGListResponse,
    GuestListResponse,
)


class ACGalaxyAPIClient:
    """ACGalaxy API 客户端"""

    def __init__(self, base_url: str = "https://acg.s1f.ren", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def _make_request(
        self, method: str, endpoint: str, params: Dict[str, Any] = None
    ) -> APIResponse:
        """发起HTTP请求"""
        url = f"{self.base_url}{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, json=params)
                else:
                    return APIResponse.error_response(f"不支持的HTTP方法: {method}")

                try:
                    response_data = response.json()
                except:
                    response_data = {"error": response.text}

                return APIResponse.from_http_response(
                    response.status_code, response_data
                )

        except httpx.TimeoutException:
            logger.error(f"ACGalaxy API 请求超时: {url}")
            return APIResponse.error_response("请求超时", 408)
        except httpx.ConnectError:
            logger.error(f"ACGalaxy API 连接失败: {url}")
            return APIResponse.error_response("连接失败", 503)
        except Exception as e:
            logger.error(f"ACGalaxy API 请求异常: {e}")
            return APIResponse.error_response(str(e), 500)

    async def get_acg_info(self, acg_id: str) -> APIResponse:
        """获取漫展详细信息"""
        try:
            response = await self._make_request("GET", f"/detail/{acg_id}")

            if response.success and response.data:
                event_data = response.data.get("data")
                if event_data:
                    event = ACGEvent.from_dict(event_data)
                    return APIResponse.success_response(event, "获取漫展信息成功")
                else:
                    return APIResponse.error_response("漫展信息不存在", 404)

            return response

        except Exception as e:
            logger.error(f"获取漫展信息失败: {e}")
            return APIResponse.error_response(f"获取漫展信息失败: {e}")

    async def get_acg_list(
        self,
        city_id: int = 0,
        city_name: Optional[str] = None,
        key: Optional[str] = None,
        order: Optional[str] = None,
        page: Optional[int] = None,
        count: Optional[int] = None,
    ) -> APIResponse:
        """获取漫展列表"""
        try:
            params = {"city_id": city_id}

            if city_name:
                params["city_name"] = city_name
            if key:
                params["key"] = key
            if order:
                params["order"] = order
            if page:
                params["page"] = page
            if count:
                params["count"] = count

            response = await self._make_request("GET", "/list", params)

            if response.success and response.data:
                acg_list = ACGListResponse.from_dict(response.data)
                return APIResponse.success_response(acg_list, "获取漫展列表成功")

            return response

        except Exception as e:
            logger.error(f"获取漫展列表失败: {e}")
            return APIResponse.error_response(f"获取漫展列表失败: {e}")

    async def get_guest_list(self, guest_name: str) -> APIResponse:
        """获取嘉宾列表"""
        try:
            params = {"guest_name": guest_name}
            response = await self._make_request("GET", "/guests", params)

            if response.success and response.data:
                guest_list = GuestListResponse.from_dict(response.data)
                return APIResponse.success_response(guest_list, "获取嘉宾列表成功")

            return response

        except Exception as e:
            logger.error(f"获取嘉宾列表失败: {e}")
            return APIResponse.error_response(f"获取嘉宾列表失败: {e}")

    async def get_guest_acg_list(self, guest_id: str) -> APIResponse:
        """获取嘉宾相关漫展列表"""
        try:
            response = await self._make_request("GET", f"/guest/{guest_id}")

            if response.success and response.data:
                guest_acg_list = GuestACGListResponse.from_dict(response.data)
                return APIResponse.success_response(
                    guest_acg_list, "获取嘉宾相关漫展成功"
                )

            return response

        except Exception as e:
            logger.error(f"获取嘉宾相关漫展失败: {e}")
            return APIResponse.error_response(f"获取嘉宾相关漫展失败: {e}")

    async def search_acg_events(self, keyword: str, count: int = 100) -> APIResponse:
        """搜索漫展活动"""
        return await self.get_acg_list(key=keyword, count=count)

    async def get_city_acg_calendar(
        self, city_name: str, count: int = 100
    ) -> APIResponse:
        """获取城市漫展日历（按时间排序）"""
        return await self.get_acg_list(city_name=city_name, count=count, order="time")

    async def search_guest_events(self, guest_name: str) -> APIResponse:
        """搜索嘉宾相关漫展"""
        try:
            # 首先获取嘉宾列表
            guest_response = await self.get_guest_list(guest_name)
            if not guest_response.success:
                return guest_response

            guest_list = guest_response.data
            if not guest_list.data:
                return APIResponse.error_response("未找到相关嘉宾信息", 404)

            # 获取所有嘉宾的相关漫展
            all_events = []
            for guest in guest_list.data:
                acg_response = await self.get_guest_acg_list(guest.id)
                if acg_response.success:
                    guest_acg_data = acg_response.data
                    # 为每个活动添加嘉宾信息
                    for event in guest_acg_data.projects:
                        event_dict = event.__dict__.copy()
                        event_dict["guest"] = guest
                        all_events.append(event_dict)

            result_data = {
                "guests": guest_list.data,
                "events": all_events,
                "total_count": len(all_events),
            }

            return APIResponse.success_response(result_data, "搜索嘉宾相关漫展成功")

        except Exception as e:
            logger.error(f"搜索嘉宾相关漫展失败: {e}")
            return APIResponse.error_response(f"搜索嘉宾相关漫展失败: {e}")

    def get_coordinate_url(self, coordinate: str) -> str:
        """获取坐标对应的高德地图URL"""
        if not coordinate:
            return ""
        return f"https://uri.amap.com/marker?position={coordinate}"

    async def test_connection(self) -> APIResponse:
        """测试API连接"""
        try:
            response = await self._make_request("GET", "/list", {"count": 1})
            if response.success:
                return APIResponse.success_response(None, "API连接正常")
            else:
                return APIResponse.error_response(f"API连接失败: {response.message}")
        except Exception as e:
            logger.error(f"测试API连接失败: {e}")
            return APIResponse.error_response(f"测试API连接失败: {e}")


# 全局API客户端实例
_api_client: Optional[ACGalaxyAPIClient] = None


def init_api_client(base_url: str = "https://acg.s1f.ren", timeout: int = 30):
    """初始化API客户端"""
    global _api_client
    _api_client = ACGalaxyAPIClient(base_url, timeout)


def get_api_client() -> Optional[ACGalaxyAPIClient]:
    """获取API客户端实例"""
    return _api_client


# 便捷函数
async def get_acg_info(acg_id: str) -> APIResponse:
    """获取漫展详细信息"""
    client = get_api_client()
    if not client:
        return APIResponse.error_response("API客户端未初始化")
    return await client.get_acg_info(acg_id)


async def get_acg_list(
    city_name: Optional[str] = None,
    key: Optional[str] = None,
    order: Optional[str] = None,
    count: int = 100,
) -> APIResponse:
    """获取漫展列表"""
    client = get_api_client()
    if not client:
        return APIResponse.error_response("API客户端未初始化")
    return await client.get_acg_list(
        city_name=city_name, key=key, order=order, count=count
    )


async def get_guest_list(guest_name: str) -> APIResponse:
    """获取嘉宾列表"""
    client = get_api_client()
    if not client:
        return APIResponse.error_response("API客户端未初始化")
    return await client.get_guest_list(guest_name)


async def get_guest_acg_list(guest_id: str) -> APIResponse:
    """获取嘉宾相关漫展列表"""
    client = get_api_client()
    if not client:
        return APIResponse.error_response("API客户端未初始化")
    return await client.get_guest_acg_list(guest_id)


async def search_acg_events(keyword: str, count: int = 100) -> APIResponse:
    """搜索漫展活动"""
    client = get_api_client()
    if not client:
        return APIResponse.error_response("API客户端未初始化")
    return await client.search_acg_events(keyword, count)


async def get_city_acg_calendar(city_name: str, count: int = 100) -> APIResponse:
    """获取城市漫展日历"""
    client = get_api_client()
    if not client:
        return APIResponse.error_response("API客户端未初始化")
    return await client.get_city_acg_calendar(city_name, count)


async def search_guest_events(guest_name: str) -> APIResponse:
    """搜索嘉宾相关漫展"""
    client = get_api_client()
    if not client:
        return APIResponse.error_response("API客户端未初始化")
    return await client.search_guest_events(guest_name)
