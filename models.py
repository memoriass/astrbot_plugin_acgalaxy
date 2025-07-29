"""
ACGalaxy 数据模型定义
"""
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class ACGEvent:
    """漫展活动信息"""
    id: str
    project_name: str
    start_time: str
    end_time: str
    start_unix: int
    end_unix: int
    city: str
    venue_name: str
    min_price: int  # 价格单位：分
    max_price: int  # 价格单位：分
    like_count: int
    has_npc: int  # 0: 无NPC招募, 1: 有NPC招募
    cover: Optional[str] = None
    coordinate: Optional[str] = None
    description: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ACGEvent':
        """从字典创建漫展活动信息"""
        return cls(
            id=str(data.get("id", "")),
            project_name=data.get("project_name", ""),
            start_time=data.get("start_time", ""),
            end_time=data.get("end_time", ""),
            start_unix=data.get("start_unix", 0),
            end_unix=data.get("end_unix", 0),
            city=data.get("city", ""),
            venue_name=data.get("venue_name", ""),
            min_price=data.get("min_price", 0),
            max_price=data.get("max_price", 0),
            like_count=data.get("like_count", 0),
            has_npc=data.get("has_npc", 0),
            cover=data.get("cover"),
            coordinate=data.get("coordinate"),
            description=data.get("description")
        )
    
    @property
    def price_range_yuan(self) -> str:
        """获取价格范围（元）"""
        min_yuan = self.min_price / 100
        max_yuan = self.max_price / 100
        if min_yuan == max_yuan:
            return f"￥{min_yuan:.0f}"
        return f"￥{min_yuan:.0f} - {max_yuan:.0f}"
    
    @property
    def has_npc_text(self) -> str:
        """获取NPC招募状态文本"""
        return "有NPC招募信息" if self.has_npc == 1 else "无NPC招募信息"
    
    @property
    def status_text(self) -> str:
        """获取活动状态文本"""
        current_time = time.time()
        if current_time < self.start_unix:
            days_until = (self.start_unix - current_time) / 86400
            return f"距离开始还有 {days_until:.0f} 天"
        elif current_time <= self.end_unix:
            return "进行中"
        else:
            return "已结束"
    
    @property
    def is_ongoing(self) -> bool:
        """是否正在进行中"""
        current_time = time.time()
        return self.start_unix <= current_time <= self.end_unix
    
    @property
    def is_upcoming(self) -> bool:
        """是否即将开始"""
        current_time = time.time()
        return current_time < self.start_unix
    
    @property
    def is_finished(self) -> bool:
        """是否已结束"""
        current_time = time.time()
        return current_time > self.end_unix
    
    @property
    def bilibili_url(self) -> str:
        """获取B站展会链接"""
        return f"https://show.bilibili.com/platform/detail.html?id={self.id}"
    
    @property
    def amap_url(self) -> str:
        """获取高德地图链接"""
        if self.coordinate:
            return f"https://uri.amap.com/marker?position={self.coordinate}"
        return ""


@dataclass
class Guest:
    """嘉宾信息"""
    id: str
    name: str
    description: str
    avatar: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Guest':
        """从字典创建嘉宾信息"""
        return cls(
            id=str(data.get("id", "")),
            name=data.get("name", ""),
            description=data.get("description", ""),
            avatar=data.get("avatar")
        )


@dataclass
class GuestACGEvent(ACGEvent):
    """带嘉宾信息的漫展活动"""
    guest: Optional[Guest] = None
    
    @classmethod
    def from_dict_with_guest(cls, data: Dict[str, Any]) -> 'GuestACGEvent':
        """从字典创建带嘉宾信息的漫展活动"""
        event = cls(
            id=str(data.get("id", "")),
            project_name=data.get("project_name", ""),
            start_time=data.get("start_time", ""),
            end_time=data.get("end_time", ""),
            start_unix=data.get("start_unix", 0),
            end_unix=data.get("end_unix", 0),
            city=data.get("city", ""),
            venue_name=data.get("venue_name", ""),
            min_price=data.get("min_price", 0),
            max_price=data.get("max_price", 0),
            like_count=data.get("like_count", 0),
            has_npc=data.get("has_npc", 0),
            cover=data.get("cover"),
            coordinate=data.get("coordinate"),
            description=data.get("description")
        )
        
        # 添加嘉宾信息
        guest_data = data.get("guest")
        if guest_data:
            event.guest = Guest.from_dict(guest_data)
        
        return event


@dataclass
class ACGListResponse:
    """漫展列表响应"""
    count: int
    data: List[ACGEvent]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ACGListResponse':
        """从字典创建漫展列表响应"""
        events = []
        for item in data.get("data", []):
            events.append(ACGEvent.from_dict(item))
        
        return cls(
            count=data.get("count", 0),
            data=events
        )


@dataclass
class GuestListResponse:
    """嘉宾列表响应"""
    data: List[Guest]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GuestListResponse':
        """从字典创建嘉宾列表响应"""
        guests = []
        for item in data.get("data", []):
            guests.append(Guest.from_dict(item))
        
        return cls(data=guests)


@dataclass
class GuestACGListResponse:
    """嘉宾相关漫展列表响应"""
    guest: Guest
    projects: List[ACGEvent]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GuestACGListResponse':
        """从字典创建嘉宾相关漫展列表响应"""
        guest_data = data.get("data", {}).get("guest", {})
        guest = Guest.from_dict(guest_data)
        
        projects = []
        for item in data.get("data", {}).get("projects", []):
            projects.append(ACGEvent.from_dict(item))
        
        return cls(
            guest=guest,
            projects=projects
        )


@dataclass
class TimeGroupedEvents:
    """按时间分组的漫展活动"""
    time_groups: Dict[str, List[ACGEvent]]
    
    @classmethod
    def from_events(cls, events: List[ACGEvent]) -> 'TimeGroupedEvents':
        """从漫展活动列表创建时间分组"""
        time_groups = {}
        
        for event in events:
            # 判断活动状态
            if event.is_ongoing:
                time_key = "进行中"
            else:
                time_key = event.start_time
            
            if time_key not in time_groups:
                time_groups[time_key] = []
            time_groups[time_key].append(event)
        
        return cls(time_groups=time_groups)
    
    def get_total_count(self) -> int:
        """获取总活动数量"""
        return sum(len(events) for events in self.time_groups.values())
    
    def get_days_until_start(self, time_key: str) -> int:
        """获取距离开始的天数"""
        if time_key == "进行中":
            return 0
        
        # 尝试解析时间
        try:
            # 假设时间格式为 "YYYY-MM-DD" 或 "YYYY-MM-DD HH:MM:SS"
            if " " in time_key:
                date_part = time_key.split(" ")[0]
            else:
                date_part = time_key
            
            target_date = datetime.strptime(date_part, "%Y-%m-%d")
            current_date = datetime.now()
            delta = target_date - current_date
            return max(0, delta.days)
        except:
            return 0


@dataclass
class SearchResult:
    """搜索结果"""
    query: str
    total_count: int
    events: List[ACGEvent]
    guests: Optional[List[Guest]] = None
    guest_events: Optional[List[GuestACGEvent]] = None
    
    @property
    def has_results(self) -> bool:
        """是否有搜索结果"""
        return self.total_count > 0
    
    @property
    def result_summary(self) -> str:
        """获取结果摘要"""
        if not self.has_results:
            return f"未找到关键词 '{self.query}' 相关的漫展信息"
        
        if self.guests:
            guest_count = len(self.guests)
            event_count = len(self.guest_events) if self.guest_events else 0
            return f"找到相关嘉宾 {guest_count} 位，相关漫展 {event_count} 场"
        else:
            return f"找到相关漫展 {self.total_count} 场"


@dataclass
class APIResponse:
    """API响应基类"""
    success: bool
    message: str
    data: Any = None
    status_code: int = 200
    
    @classmethod
    def success_response(cls, data: Any, message: str = "请求成功") -> 'APIResponse':
        """创建成功响应"""
        return cls(success=True, message=message, data=data, status_code=200)
    
    @classmethod
    def error_response(cls, message: str, status_code: int = 500) -> 'APIResponse':
        """创建错误响应"""
        return cls(success=False, message=message, status_code=status_code)
    
    @classmethod
    def from_http_response(cls, status_code: int, response_data: Dict[str, Any]) -> 'APIResponse':
        """从HTTP响应创建API响应"""
        if status_code == 200:
            return cls.success_response(response_data)
        else:
            error_msg = cls._get_error_message(status_code)
            return cls.error_response(f"{error_msg}: {response_data}", status_code)
    
    @staticmethod
    def _get_error_message(status_code: int) -> str:
        """获取错误信息"""
        error_map = {
            400: "请求参数错误",
            404: "资源不存在",
            500: "服务器内部错误",
            502: "网关错误",
            503: "服务不可用",
            504: "网关超时"
        }
        return error_map.get(status_code, f"HTTP错误 {status_code}")


# 工具函数
def calculate_days_until(date_str: str) -> int:
    """计算距离指定日期的天数"""
    try:
        if " " in date_str:
            date_part = date_str.split(" ")[0]
        else:
            date_part = date_str
        
        target_date = datetime.strptime(date_part, "%Y-%m-%d")
        current_date = datetime.now()
        delta = target_date - current_date
        return max(0, delta.days)
    except:
        return 0


def format_coordinate_url(coordinate: str) -> str:
    """格式化坐标为高德地图URL"""
    if not coordinate:
        return ""
    return f"https://uri.amap.com/marker?position={coordinate}"


def group_events_by_time(events: List[ACGEvent]) -> Dict[str, List[ACGEvent]]:
    """按时间分组漫展活动"""
    groups = {}
    
    for event in events:
        if event.is_ongoing:
            time_key = "进行中"
        else:
            time_key = event.start_time
        
        if time_key not in groups:
            groups[time_key] = []
        groups[time_key].append(event)
    
    return groups
