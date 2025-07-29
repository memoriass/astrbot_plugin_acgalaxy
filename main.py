import asyncio
import time
from typing import Any, Dict, List, Optional

import astrbot.api.message_components as Comp
from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

from .api_client import get_api_client, init_api_client
from .models import ACGEvent, APIResponse, Guest, SearchResult, TimeGroupedEvents
from .renderer import ACGalaxyImageRenderer


@register(
    "acgalaxy",
    "memoriass",
    "次元星辰",
    "1.0.0",
    "https://github.com/example/astrbot_plugin_acgalaxy",
)
class ACGalaxyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

        # 初始化API客户端
        api_base_url = self.config.get("api_base_url", "https://acg.s1f.ren")
        request_timeout = self.config.get("request_timeout", 30)
        init_api_client(api_base_url, request_timeout)

        # 初始化图片渲染器
        image_width = self.config.get("image_width", 625)
        image_scale_factor = self.config.get("image_scale_factor", 1.0)
        self.renderer = ACGalaxyImageRenderer(image_width, image_scale_factor)

        # 缓存设置
        self.cache = {}
        self.cache_expire_time = (
            self.config.get("cache_expire_time", 30) * 60
        )  # 转换为秒

        logger.info("ACGalaxy 插件已加载")

    def get_cached_data(self, key: str):
        """获取缓存数据"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_expire_time:
                return data
            else:
                del self.cache[key]
        return None

    def set_cached_data(self, key: str, data):
        """设置缓存数据"""
        self.cache[key] = (data, time.time())

    async def _render_or_text(self, render_func, fallback_text: str, *args, **kwargs):
        """尝试渲染图片，失败则返回文本"""
        if self.config.get("enable_image_render", True):
            try:
                img_data = await render_func(*args, **kwargs)
                return Comp.Image.fromBytes(img_data)
            except Exception as e:
                logger.error(f"图片渲染失败: {e}")

        return Comp.Plain(fallback_text)

    @filter.command("漫展日历")
    async def acg_calendar_command(
        self, message_event: AstrMessageEvent, city: str = ""
    ):
        """获取指定城市的漫展日历"""
        if not city:
            city = self.config.get("default_city", "北京")

        api_client = get_api_client()
        if not api_client:
            yield message_event.plain_result("❌ API客户端未初始化")
            return

        try:
            # 尝试从缓存获取
            cache_key = f"calendar_{city}"
            cached_data = self.get_cached_data(cache_key)

            if cached_data:
                response = cached_data
            else:
                max_results = self.config.get("max_results_per_page", 100)
                response = await api_client.get_city_acg_calendar(city, max_results)

                if response.success:
                    self.set_cached_data(cache_key, response)

            if not response.success:
                yield message_event.plain_result(
                    f"❌ 获取漫展日历失败: {response.message}"
                )
                return

            acg_list = response.data
            if not acg_list.data:
                yield message_event.plain_result(f"📅 {city} 暂无漫展信息")
                return

            # 按时间分组
            time_grouped = TimeGroupedEvents.from_events(acg_list.data)

            # 生成图片或文本
            if self.config.get("enable_image_render", True):
                try:
                    img_data = await self.renderer.render_acg_calendar(time_grouped)
                    yield message_event.chain_result([Comp.Image.fromBytes(img_data)])
                    return
                except Exception as e:
                    logger.error(f"生成漫展日历图片失败: {e}")

            # 文本格式
            text_lines = [
                f"📅 {city} 漫展日历 (共 {time_grouped.get_total_count()} 场)"
            ]

            for time_key, events in time_grouped.time_groups.items():
                days_until = time_grouped.get_days_until_start(time_key)
                if days_until > 0:
                    text_lines.append(
                        f"\n🗓️ {time_key} (距离开始 {days_until} 天) - {len(events)} 场"
                    )
                else:
                    text_lines.append(f"\n🗓️ {time_key} - {len(events)} 场")

                for event in events[:3]:  # 只显示前3个
                    text_lines.append(f"  • {event.project_name} ({event.venue_name})")

                if len(events) > 3:
                    text_lines.append(f"  ... 还有 {len(events) - 3} 场")

            text_lines.append(f"\n💡 发送 '漫展详情 <ID>' 查看详细信息")

            yield message_event.plain_result("\n".join(text_lines))

        except Exception as e:
            logger.error(f"获取漫展日历失败: {e}")
            yield message_event.plain_result(f"❌ 获取漫展日历失败: {str(e)}")

    @filter.command("漫展位置")
    async def acg_location_command(
        self, message_event: AstrMessageEvent, acg_id: str = ""
    ):
        """获取指定漫展的位置信息"""
        if not acg_id:
            yield message_event.plain_result(
                "❌ 请指定漫展ID，格式: /漫展位置 <漫展ID>"
            )
            return

        api_client = get_api_client()
        if not api_client:
            yield message_event.plain_result("❌ API客户端未初始化")
            return

        try:
            response = await api_client.get_acg_info(acg_id)

            if not response.success:
                yield message_event.plain_result(
                    f"❌ 获取漫展信息失败: {response.message}"
                )
                return

            event_info = response.data

            text_lines = [
                f"📍 漫展位置信息",
                f"漫展名称: {event_info.project_name}",
                f"漫展地点: {event_info.venue_name}",
                f"所在城市: {event_info.city}",
            ]

            if (
                self.config.get("enable_location_service", True)
                and event_info.coordinate
            ):
                amap_url = api_client.get_coordinate_url(event_info.coordinate)
                text_lines.append(f"地图位置: {amap_url}")

            yield message_event.plain_result("\n".join(text_lines))

        except Exception as e:
            logger.error(f"获取漫展位置失败: {e}")
            yield message_event.plain_result(f"❌ 获取漫展位置失败: {str(e)}")

    @filter.command("漫展详情")
    async def acg_info_command(self, message_event: AstrMessageEvent, acg_id: str = ""):
        """获取指定漫展的详细信息"""
        if not acg_id:
            yield message_event.plain_result(
                "❌ 请指定漫展ID，格式: /漫展详情 <漫展ID>"
            )
            return

        api_client = get_api_client()
        if not api_client:
            yield message_event.plain_result("❌ API客户端未初始化")
            return

        try:
            response = await api_client.get_acg_info(acg_id)

            if not response.success:
                yield message_event.plain_result(
                    f"❌ 获取漫展信息失败: {response.message}"
                )
                return

            event_info = response.data

            # 构建详细信息
            text_lines = [
                f"🎭 漫展详情",
                f"ID: {event_info.id}",
                f"名称: {event_info.project_name}",
                f"地点: {event_info.venue_name}",
                f"城市: {event_info.city}",
                f"时间: {event_info.start_time} - {event_info.end_time}",
                f"票价: {event_info.price_range_yuan}",
                f"状态: {event_info.status_text}",
                f"NPC招募: {event_info.has_npc_text}",
                f"想去人数: {event_info.like_count}",
                f"B站链接: {event_info.bilibili_url}",
            ]

            # 如果有封面图片，先发送图片
            if event_info.cover:
                try:
                    yield message_event.chain_result(
                        [
                            Comp.Image.fromURL(event_info.cover),
                            Comp.Plain("\n".join(text_lines)),
                        ]
                    )
                    return
                except Exception as e:
                    logger.warning(f"加载封面图片失败: {e}")

            yield message_event.plain_result("\n".join(text_lines))

        except Exception as e:
            logger.error(f"获取漫展详情失败: {e}")
            yield message_event.plain_result(f"❌ 获取漫展详情失败: {str(e)}")

    @filter.command("漫展检索")
    async def acg_search_command(
        self, message_event: AstrMessageEvent, keyword: str = ""
    ):
        """检索漫展信息"""
        if not keyword:
            yield message_event.plain_result(
                "❌ 请输入搜索关键词，格式: /漫展检索 <关键词>"
            )
            return

        api_client = get_api_client()
        if not api_client:
            yield message_event.plain_result("❌ API客户端未初始化")
            return

        try:
            max_results = self.config.get("max_results_per_page", 100)
            response = await api_client.search_acg_events(keyword, max_results)

            if not response.success:
                yield message_event.plain_result(f"❌ 搜索漫展失败: {response.message}")
                return

            acg_list = response.data
            if not acg_list.data:
                yield message_event.plain_result(
                    f"🔍 未找到关键词 '{keyword}' 相关的漫展信息"
                )
                return

            # 生成图片或文本
            if self.config.get("enable_image_render", True):
                try:
                    img_data = await self.renderer.render_acg_list(acg_list.data)
                    result_text = f"🔍 找到 {acg_list.count} 场相关漫展"
                    yield message_event.chain_result(
                        [Comp.Plain(result_text), Comp.Image.fromBytes(img_data)]
                    )
                    return
                except Exception as e:
                    logger.error(f"生成搜索结果图片失败: {e}")

            # 文本格式
            text_lines = [f"🔍 找到 {acg_list.count} 场相关漫展"]

            for i, acg_event in enumerate(acg_list.data[:5]):  # 只显示前5个
                text_lines.append(f"\n{i+1}. {acg_event.project_name}")
                text_lines.append(
                    f"   📅 {acg_event.start_time} - {acg_event.end_time}"
                )
                text_lines.append(f"   📍 {acg_event.city} - {acg_event.venue_name}")
                text_lines.append(f"   💰 {acg_event.price_range_yuan}")
                text_lines.append(f"   ID: {acg_event.id}")

            if acg_list.count > 5:
                text_lines.append(f"\n... 还有 {acg_list.count - 5} 场漫展")

            text_lines.append(f"\n💡 发送 '漫展详情 <ID>' 查看详细信息")

            yield message_event.plain_result("\n".join(text_lines))

        except Exception as e:
            logger.error(f"搜索漫展失败: {e}")
            yield message_event.plain_result(f"❌ 搜索漫展失败: {str(e)}")

    @filter.command("嘉宾检索")
    async def guest_search_command(
        self, message_event: AstrMessageEvent, guest_name: str = ""
    ):
        """检索嘉宾信息"""
        if not self.config.get("enable_guest_search", True):
            yield message_event.plain_result("❌ 嘉宾搜索功能已禁用")
            return

        if not guest_name:
            help_text = """❌ 请输入嘉宾名称，格式: /嘉宾检索 <嘉宾名称>

💡 搜索提示:
- 尝试使用具体的嘉宾姓名
- 可以搜索声优、歌手、艺人等
- 如果没有找到结果，可能该嘉宾暂无相关漫展活动"""
            yield message_event.plain_result(help_text)
            return

        api_client = get_api_client()
        if not api_client:
            yield message_event.plain_result("❌ API客户端未初始化")
            return

        try:
            response = await api_client.search_guest_events(guest_name)

            if not response.success:
                yield message_event.plain_result(f"❌ 搜索嘉宾失败: {response.message}")
                return

            result_data = response.data
            guests = result_data["guests"]
            events = result_data["events"]
            total_count = result_data["total_count"]

            if not guests:
                fallback_text = f"""🔍 未找到嘉宾 '{guest_name}' 的相关信息

💡 建议:
1. 检查嘉宾姓名是否正确
2. 尝试使用不同的关键词
3. 使用 '/漫展检索 {guest_name}' 搜索相关漫展"""
                yield message_event.plain_result(fallback_text)
                return

            # 生成图片或文本
            if self.config.get("enable_image_render", True):
                try:
                    img_data = await self.renderer.render_guest_events(guests, events)
                    result_text = (
                        f"🔍 找到相关嘉宾 {len(guests)} 位，相关漫展 {total_count} 场"
                    )
                    yield message_event.chain_result(
                        [Comp.Plain(result_text), Comp.Image.fromBytes(img_data)]
                    )
                    return
                except Exception as e:
                    logger.error(f"生成嘉宾搜索结果图片失败: {e}")

            # 文本格式
            text_lines = [
                f"🔍 找到相关嘉宾 {len(guests)} 位，相关漫展 {total_count} 场"
            ]

            for guest in guests:
                text_lines.append(f"\n👤 {guest.name}")
                if guest.description:
                    text_lines.append(f"   {guest.description}")

                # 显示该嘉宾的相关漫展
                guest_events = [
                    e for e in events if e.get("guest", {}).get("id") == guest.id
                ]
                for guest_event in guest_events[:3]:  # 只显示前3个
                    text_lines.append(
                        f"   • {guest_event['project_name']} (ID: {guest_event['id']})"
                    )

                if len(guest_events) > 3:
                    text_lines.append(f"   ... 还有 {len(guest_events) - 3} 场漫展")

            text_lines.append(f"\n💡 发送 '漫展详情 <ID>' 查看详细信息")

            yield message_event.plain_result("\n".join(text_lines))

        except Exception as e:
            logger.error(f"搜索嘉宾失败: {e}")
            yield message_event.plain_result(f"❌ 搜索嘉宾失败: {str(e)}")

    @filter.command("acg_status")
    async def acg_status_command(self, message_event: AstrMessageEvent):
        """查看ACGalaxy插件状态"""
        try:
            api_client = get_api_client()
            connection_status = "✅ 已连接" if api_client else "❌ 未初始化"

            # 测试连接并记录响应时间
            response_time = "未知"
            if api_client:
                import time

                start_time = time.time()
                test_result = await api_client.test_connection()
                response_time = f"{(time.time() - start_time) * 1000:.0f}ms"
                connection_status = (
                    "✅ 连接正常"
                    if test_result.success
                    else f"❌ 连接失败: {test_result.message}"
                )

            status_text = f"""📊 ACGalaxy 插件状态
🔗 API连接: {connection_status}
⏱️ 响应时间: {response_time}
🌐 API地址: {self.config.get('api_base_url', 'https://acg.s1f.ren')}
🖼️ 图片渲染: {'✅ 启用' if self.config.get('enable_image_render', True) else '❌ 禁用'}
👤 嘉宾搜索: {'✅ 启用' if self.config.get('enable_guest_search', True) else '❌ 禁用'}
📍 位置服务: {'✅ 启用' if self.config.get('enable_location_service', True) else '❌ 禁用'}
📋 缓存数量: {len(self.cache)}
⏰ 缓存过期: {self.cache_expire_time // 60}分钟
🏙️ 默认城市: {self.config.get('default_city', '北京')}"""

            yield message_event.plain_result(status_text)

        except Exception as e:
            logger.error(f"查询ACGalaxy状态失败: {e}")
            yield message_event.plain_result(f"❌ 查询状态失败: {str(e)}")

    async def terminate(self):
        """插件卸载时的清理工作"""
        self.cache.clear()
        logger.info("ACGalaxy 插件已卸载")
        logger.info("ACGalaxy 插件已卸载")
