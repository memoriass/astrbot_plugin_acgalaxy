"""
ACGalaxy 图片渲染器
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright
from astrbot.api import logger

from .models import ACGEvent, Guest, TimeGroupedEvents, SearchResult


class ACGalaxyImageRenderer:
    """ACGalaxy 图片渲染器"""
    
    def __init__(self, width: int = 625, device_scale_factor: float = 1.0):
        self.width = width
        self.device_scale_factor = device_scale_factor
        self.templates_dir = Path(__file__).parent / "templates"
        
        # 确保模板目录存在
        self.templates_dir.mkdir(exist_ok=True)
    
    async def _capture_element_screenshot(
        self, 
        html_content: str, 
        element_selector: str = "#app"
    ) -> bytes:
        """截取HTML元素的屏幕截图"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(args=["--no-sandbox"])
                page = await browser.new_page(device_scale_factor=self.device_scale_factor)
                await page.set_viewport_size({"width": self.width, "height": 1200})
                
                # 设置页面内容
                await page.set_content(html_content)
                
                # 等待页面渲染完成
                await page.wait_for_timeout(1000)
                
                # 截取指定元素的截图
                element = page.locator(element_selector)
                screenshot = await element.screenshot()
                
                await browser.close()
                return screenshot
                
        except Exception as e:
            logger.error(f"截取屏幕截图失败: {e}")
            raise
    
    def _load_template(self, template_name: str) -> str:
        """加载HTML模板"""
        template_path = self.templates_dir / template_name
        if not template_path.exists():
            # 如果模板不存在，创建默认模板
            self._create_default_templates()
        
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"加载模板失败: {e}")
            return self._get_fallback_template()
    
    def _get_fallback_template(self) -> str:
        """获取备用模板"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>ACGalaxy</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .event { border: 1px solid #ccc; margin: 10px 0; padding: 10px; }
                .event-title { font-weight: bold; font-size: 16px; }
                .event-info { color: #666; margin: 5px 0; }
            </style>
        </head>
        <body>
            <div id="app">
                <h2>漫展信息</h2>
                <div class="event">
                    <div class="event-title">模板加载失败</div>
                    <div class="event-info">请检查模板文件</div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_default_templates(self):
        """创建默认模板文件"""
        # 创建漫展列表模板
        acg_list_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>漫展列表</title>
            <style>
                body { font-family: "Microsoft YaHei", Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                #app { max-width: 600px; margin: 0 auto; }
                .header { text-align: center; margin-bottom: 20px; color: #333; }
                .tip { text-align: center; color: #666; font-size: 12px; margin-bottom: 20px; }
                .event-card { background: white; border-radius: 8px; margin: 10px 0; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .event-title { font-weight: bold; font-size: 16px; color: #333; margin-bottom: 8px; }
                .event-time { color: #e74c3c; font-size: 14px; margin-bottom: 5px; }
                .event-location { color: #666; font-size: 14px; margin-bottom: 5px; }
                .event-price { color: #27ae60; font-weight: bold; margin-bottom: 5px; }
                .event-meta { font-size: 12px; color: #999; }
                .npc-badge { background: #3498db; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; }
                .no-npc-badge { background: #95a5a6; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; }
            </style>
        </head>
        <body>
            <div id="app">
                <div class="header">
                    <h2>漫展列表</h2>
                </div>
                <div class="tip">
                    发送 "漫展详情 展会id" 查看详细信息<br>
                    发送 "漫展位置 展会id" 查看位置信息
                </div>
                <div id="events">
                    <!-- 漫展列表将在这里渲染 -->
                </div>
            </div>
            <script>
                const events = @@acg_list@@;
                const container = document.getElementById('events');
                
                events.forEach(event => {
                    const card = document.createElement('div');
                    card.className = 'event-card';
                    
                    const npcBadge = event.has_npc === 1 
                        ? '<span class="npc-badge">有NPC招募</span>'
                        : '<span class="no-npc-badge">无NPC招募</span>';
                    
                    card.innerHTML = `
                        <div class="event-title">${event.project_name}</div>
                        <div class="event-time">📅 ${event.start_time} - ${event.end_time}</div>
                        <div class="event-location">📍 ${event.city} - ${event.venue_name}</div>
                        <div class="event-price">💰 ￥${event.min_price/100} - ${event.max_price/100}</div>
                        <div class="event-meta">
                            ${npcBadge}
                            <span style="margin-left: 10px;">❤️ ${event.like_count}</span>
                            <span style="margin-left: 10px;">ID: ${event.id}</span>
                        </div>
                    `;
                    
                    container.appendChild(card);
                });
            </script>
        </body>
        </html>
        """
        
        # 创建时间分组模板
        acg_list_times_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>漫展日历</title>
            <style>
                body { font-family: "Microsoft YaHei", Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                #app { max-width: 600px; margin: 0 auto; }
                .header { text-align: center; margin-bottom: 20px; color: #333; }
                .tip { text-align: center; color: #666; font-size: 12px; margin-bottom: 20px; }
                .time-group { margin-bottom: 30px; }
                .time-header { background: #3498db; color: white; padding: 10px; border-radius: 5px; font-weight: bold; margin-bottom: 10px; }
                .event-card { background: white; border-radius: 8px; margin: 10px 0; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .event-title { font-weight: bold; font-size: 16px; color: #333; margin-bottom: 8px; }
                .event-time { color: #e74c3c; font-size: 14px; margin-bottom: 5px; }
                .event-location { color: #666; font-size: 14px; margin-bottom: 5px; }
                .event-price { color: #27ae60; font-weight: bold; margin-bottom: 5px; }
                .event-meta { font-size: 12px; color: #999; }
                .npc-badge { background: #3498db; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; }
                .no-npc-badge { background: #95a5a6; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; }
            </style>
        </head>
        <body>
            <div id="app">
                <div class="header">
                    <h2>漫展日历</h2>
                </div>
                <div class="tip">
                    发送 "漫展详情 展会id" 查看详细信息<br>
                    发送 "漫展位置 展会id" 查看位置信息
                </div>
                <div id="time-groups">
                    <!-- 时间分组将在这里渲染 -->
                </div>
            </div>
            <script>
                const timeGroups = @@acg_list@@;
                const container = document.getElementById('time-groups');
                
                function calculateDaysUntil(dateStr) {
                    if (dateStr === '进行中') return 0;
                    try {
                        const targetDate = new Date(dateStr.split(' ')[0]);
                        const currentDate = new Date();
                        const diffTime = targetDate - currentDate;
                        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                        return Math.max(0, diffDays);
                    } catch {
                        return 0;
                    }
                }
                
                Object.keys(timeGroups).forEach(timeKey => {
                    const events = timeGroups[timeKey];
                    const daysUntil = calculateDaysUntil(timeKey);
                    
                    const groupDiv = document.createElement('div');
                    groupDiv.className = 'time-group';
                    
                    const headerDiv = document.createElement('div');
                    headerDiv.className = 'time-header';
                    headerDiv.textContent = `${timeKey} 共 ${events.length} 场`;
                    if (daysUntil > 0) {
                        headerDiv.textContent += ` (距离开始还有 ${daysUntil} 天)`;
                    }
                    
                    groupDiv.appendChild(headerDiv);
                    
                    events.forEach(event => {
                        const card = document.createElement('div');
                        card.className = 'event-card';
                        
                        const npcBadge = event.has_npc === 1 
                            ? '<span class="npc-badge">有NPC招募</span>'
                            : '<span class="no-npc-badge">无NPC招募</span>';
                        
                        card.innerHTML = `
                            <div class="event-title">${event.project_name}</div>
                            <div class="event-time">📅 ${event.start_time} - ${event.end_time}</div>
                            <div class="event-location">📍 ${event.city} - ${event.venue_name}</div>
                            <div class="event-price">💰 ￥${event.min_price/100} - ${event.max_price/100}</div>
                            <div class="event-meta">
                                ${npcBadge}
                                <span style="margin-left: 10px;">❤️ ${event.like_count}</span>
                                <span style="margin-left: 10px;">ID: ${event.id}</span>
                            </div>
                        `;
                        
                        groupDiv.appendChild(card);
                    });
                    
                    container.appendChild(groupDiv);
                });
            </script>
        </body>
        </html>
        """
        
        # 创建嘉宾搜索模板
        acg_list_guest_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>嘉宾相关漫展</title>
            <style>
                body { font-family: "Microsoft YaHei", Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                #app { max-width: 600px; margin: 0 auto; }
                .header { text-align: center; margin-bottom: 20px; color: #333; }
                .tip { text-align: center; color: #666; font-size: 12px; margin-bottom: 20px; }
                .guest-section { margin-bottom: 30px; }
                .guest-header { background: #9b59b6; color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
                .guest-name { font-size: 18px; font-weight: bold; margin-bottom: 5px; }
                .guest-desc { font-size: 14px; opacity: 0.9; }
                .event-card { background: white; border-radius: 8px; margin: 10px 0; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .event-title { font-weight: bold; font-size: 16px; color: #333; margin-bottom: 8px; }
                .event-time { color: #e74c3c; font-size: 14px; margin-bottom: 5px; }
                .event-location { color: #666; font-size: 14px; margin-bottom: 5px; }
                .event-price { color: #27ae60; font-weight: bold; margin-bottom: 5px; }
                .event-meta { font-size: 12px; color: #999; }
                .npc-badge { background: #3498db; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; }
                .no-npc-badge { background: #95a5a6; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; }
            </style>
        </head>
        <body>
            <div id="app">
                <div class="header">
                    <h2>嘉宾相关漫展</h2>
                </div>
                <div class="tip">
                    发送 "漫展详情 展会id" 查看详细信息<br>
                    发送 "漫展位置 展会id" 查看位置信息
                </div>
                <div id="content">
                    <!-- 内容将在这里渲染 -->
                </div>
            </div>
            <script>
                const events = @@acg_list@@;
                const guests = @@guest_list@@;
                const container = document.getElementById('content');
                
                // 按嘉宾分组事件
                const eventsByGuest = {};
                events.forEach(event => {
                    const guestId = event.guest ? event.guest.id : 'unknown';
                    if (!eventsByGuest[guestId]) {
                        eventsByGuest[guestId] = [];
                    }
                    eventsByGuest[guestId].push(event);
                });
                
                // 渲染每个嘉宾的相关漫展
                guests.forEach(guest => {
                    const guestEvents = eventsByGuest[guest.id] || [];
                    
                    const sectionDiv = document.createElement('div');
                    sectionDiv.className = 'guest-section';
                    
                    const headerDiv = document.createElement('div');
                    headerDiv.className = 'guest-header';
                    headerDiv.innerHTML = `
                        <div class="guest-name">${guest.name}</div>
                        <div class="guest-desc">${guest.description || '暂无描述'}</div>
                    `;
                    
                    sectionDiv.appendChild(headerDiv);
                    
                    guestEvents.forEach(event => {
                        const card = document.createElement('div');
                        card.className = 'event-card';
                        
                        const npcBadge = event.has_npc === 1 
                            ? '<span class="npc-badge">有NPC招募</span>'
                            : '<span class="no-npc-badge">无NPC招募</span>';
                        
                        card.innerHTML = `
                            <div class="event-title">${event.project_name}</div>
                            <div class="event-time">📅 ${event.start_time} - ${event.end_time}</div>
                            <div class="event-location">📍 ${event.city} - ${event.venue_name}</div>
                            <div class="event-price">💰 ￥${event.min_price/100} - ${event.max_price/100}</div>
                            <div class="event-meta">
                                ${npcBadge}
                                <span style="margin-left: 10px;">❤️ ${event.like_count}</span>
                                <span style="margin-left: 10px;">ID: ${event.id}</span>
                            </div>
                        `;
                        
                        sectionDiv.appendChild(card);
                    });
                    
                    container.appendChild(sectionDiv);
                });
            </script>
        </body>
        </html>
        """
        
        # 写入模板文件
        templates = {
            "acg_list.html": acg_list_template,
            "acg_list_times.html": acg_list_times_template,
            "acg_list_guest.html": acg_list_guest_template
        }
        
        for filename, content in templates.items():
            template_path = self.templates_dir / filename
            try:
                with open(template_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"创建模板文件: {filename}")
            except Exception as e:
                logger.error(f"创建模板文件失败 {filename}: {e}")
    
    async def render_acg_list(self, events: List[ACGEvent]) -> bytes:
        """渲染漫展列表"""
        try:
            template = self._load_template("acg_list.html")
            
            # 将事件列表转换为字典列表
            events_data = [event.__dict__ for event in events]
            
            # 替换模板中的数据
            html_content = template.replace("@@acg_list@@", json.dumps(events_data, ensure_ascii=False))
            
            return await self._capture_element_screenshot(html_content)
            
        except Exception as e:
            logger.error(f"渲染漫展列表失败: {e}")
            raise
    
    async def render_acg_calendar(self, time_grouped_events: TimeGroupedEvents) -> bytes:
        """渲染漫展日历（按时间分组）"""
        try:
            template = self._load_template("acg_list_times.html")
            
            # 将时间分组转换为字典
            time_groups_data = {}
            for time_key, events in time_grouped_events.time_groups.items():
                time_groups_data[time_key] = [event.__dict__ for event in events]
            
            # 替换模板中的数据
            html_content = template.replace("@@acg_list@@", json.dumps(time_groups_data, ensure_ascii=False))
            
            return await self._capture_element_screenshot(html_content)
            
        except Exception as e:
            logger.error(f"渲染漫展日历失败: {e}")
            raise
    
    async def render_guest_events(self, guests: List[Guest], events: List[Dict[str, Any]]) -> bytes:
        """渲染嘉宾相关漫展"""
        try:
            template = self._load_template("acg_list_guest.html")
            
            # 转换数据
            guests_data = [guest.__dict__ for guest in guests]
            
            # 替换模板中的数据
            html_content = template.replace("@@guest_list@@", json.dumps(guests_data, ensure_ascii=False))
            html_content = html_content.replace("@@acg_list@@", json.dumps(events, ensure_ascii=False))
            
            return await self._capture_element_screenshot(html_content)
            
        except Exception as e:
            logger.error(f"渲染嘉宾相关漫展失败: {e}")
            raise
