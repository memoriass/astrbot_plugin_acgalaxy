# 次元星辰 - AstrBot 插件

基于 NoneBot 插件 `nonebot-plugin-ACGalaxy` 移植的 AstrBot 版本，简单高效的漫展信息展示插件，收集展示漫展信息，支持检索、排序、获取定位信息。


**基础配置：**
- `api_base_url`: 漫展信息API地址（默认: https://acg.s1f.ren）
- `enable_image_render`: 启用图片渲染（默认: true）
- `request_timeout`: 请求超时时间（默认: 30秒）

**功能配置：**
- `enable_location_service`: 启用位置服务（默认: true）
- `enable_guest_search`: 启用嘉宾搜索（默认: true）
- `default_city`: 默认城市（默认: 北京）

**性能配置：**
- `max_results_per_page`: 每页最大结果数（默认: 100）
- `cache_expire_time`: 缓存过期时间（默认: 30分钟）
- `image_width`: 生成图片宽度（默认: 625像素）
- `image_scale_factor`: 图片缩放因子（默认: 1.0）

### 4. 配置示例

```json
{
  "api_base_url": "https://acg.s1f.ren",
  "enable_image_render": true,
  "request_timeout": 30,
  "max_results_per_page": 100,
  "image_width": 625,
  "image_scale_factor": 1.0,
  "cache_expire_time": 30,
  "enable_location_service": true,
  "default_city": "北京",
  "enable_guest_search": true
}
```

## 使用方法

### 基础命令

- `/漫展日历 [城市]` - 查看指定城市的漫展日历
- `/漫展位置 <漫展ID>` - 获取指定漫展的位置信息
- `/漫展详情 <漫展ID>` - 查看漫展详细信息
- `/漫展检索 <关键词>` - 搜索漫展信息
- `/嘉宾检索 <嘉宾名称>` - 搜索嘉宾相关漫展
- `/acg_status` - 查看插件状态

### 使用示例

```bash
# 查看北京的漫展日历
/漫展日历 北京

# 查看上海的漫展日历
/漫展日历 上海

# 查看漫展详情
/漫展详情 87584

# 查看漫展位置
/漫展位置 87584

# 搜索动漫相关漫展
/漫展检索 动漫节

# 搜索声优相关漫展
/嘉宾检索 花泽香菜

# 查看插件状态
/acg_status
```
## 故障排除

### 常见问题

1. **API连接失败**
   ```
   错误：连接失败
   解决：检查网络连接和API地址配置
   ```

2. **图片生成失败**
   ```
   错误：图片渲染失败
   解决：检查playwright是否正确安装，或禁用图片渲染
   ```

3. **搜索无结果**
   ```
   错误：未找到相关信息
   解决：尝试使用不同的关键词或检查API服务状态
   ```

4. **缓存问题**
   ```
   错误：数据不是最新的
   解决：等待缓存过期或重启插件
   ```

### 调试方法

1. 使用 `/acg_status` 检查插件状态
2. 查看 AstrBot 日志中的错误信息
3. 运行测试脚本验证功能
4. 检查网络连接和API服务状态

## 开发说明

### 插件架构

```
astrbot_plugin_acgalaxy/
├── main.py          # 主插件类和命令处理
├── models.py        # 数据模型定义
├── api_client.py    # API客户端封装
├── renderer.py      # 图片渲染器
├── templates/       # HTML模板文件
├── __init__.py      # 包初始化
└── test_plugin.py   # 测试脚本
```

### 核心组件

1. **ACGalaxyAPIClient** - API调用封装
2. **数据模型** - ACGEvent、Guest、SearchResult 等
3. **ACGalaxyImageRenderer** - 图片渲染器
4. **缓存系统** - 提高响应速度
5. **模板系统** - HTML模板管理

### API 对应关系

| 功能 | API 端点 | 插件方法 |
|------|----------|----------|
| 漫展列表 | `/list` | `get_acg_list` |
| 漫展详情 | `/detail/{id}` | `get_acg_info` |
| 嘉宾列表 | `/guests` | `get_guest_list` |
| 嘉宾漫展 | `/guest/{id}` | `get_guest_acg_list` |


## 许可证

本插件遵循 Apache-2.0 许可证。

## 致谢

- 参考了 [nonebot-plugin-kawaii-status](https://github.com/KomoriDev/nonebot-plugin-kawaii-status) 的设计思路
- 感谢 AstrBot 项目提供的优秀框架

