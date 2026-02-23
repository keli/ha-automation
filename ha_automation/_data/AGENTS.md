# AI Assistant Guide for Home Assistant Automation Toolkit

## 关键规则

### 1. 始终通过 toolkit API 操作，不要绕开

```python
from ha_automation import HAClient, DeviceDiscovery, AutomationManager

client = HAClient()       # 自动读取 ~/.config/ha-automation/config
discovery = DeviceDiscovery(client)
manager = AutomationManager(client)
```

- ✅ 用 `HAClient` 查询设备状态、日志等
- ✅ 用 `manager.create_or_update(config)` 创建/更新自动化
- ❌ 不要手写 `requests` / `curl` 直接调 HA REST API
- ❌ 不要生成 YAML 让用户手动粘贴

### 2. 使用固定 ID（不要时间戳）

```python
# ✅ 正确
{"id": "night_hallway_light", ...}
manager.create_or_update(config)   # 幂等，重复运行不会创建重复

# ❌ 错误
{"id": f"automation_{int(time.time())}", ...}  # 每次创建新的
```

### 3. 文件位置

- 个人自动化脚本 → 本项目的 `automations/` 目录（IDE 里直接可见）
- HA 连接配置 → 本项目根目录的 `.ha-config`（含 token，已 gitignore，**不要读取或修改**）

`ha-automation sync` 会自动检测当前目录下的 `automations/` 子目录。

---

## 标准工作流

```python
# 1. 发现设备
devices = discovery.discover_all()
lights = discovery.get_lights()
sensors = discovery.get_motion_sensors()
results = discovery.search("走廊")          # 支持中英文
by_domain = discovery.get_by_domain('switch')
by_area = discovery.get_by_area("Living Room")

# 2. 构建配置（固定 ID）
config = {
    "id": "my_automation",          # 固定 ID
    "alias": "自动化名称",
    "description": "描述",
    "trigger": [...],
    "condition": [...],             # 可选
    "action": [...],
    "mode": "single"                # single / restart / queued / parallel
}

# 3. 创建/更新
automation_id, was_created = manager.create_or_update(config)
print(f"{'创建' if was_created else '更新'}: automation.{automation_id}")
```

---

## HA 配置速查

### Trigger

```python
# 实体状态变化
{"platform": "state", "entity_id": "...", "to": "on", "from": "off", "for": "00:05:00"}

# 定时
{"platform": "time", "at": "22:00:00"}

# 数值阈值
{"platform": "numeric_state", "entity_id": "...", "above": 26, "below": 20}

# 模板
{"platform": "template", "value_template": "{{ states('sensor.temp') | float > 25 }}"}

# 日出日落
{"platform": "sun", "event": "sunset", "offset": "-00:30:00"}

# event 域实体（小米无线开关等）用 state trigger，不要用 event trigger
{"platform": "state", "entity_id": "event.xiaomi_xxx_click"}
```

### Condition

```python
{"condition": "time", "after": "22:00:00", "before": "06:00:00", "weekday": ["mon","tue"]}
{"condition": "state", "entity_id": "...", "state": "off"}
{"condition": "numeric_state", "entity_id": "...", "above": 20, "below": 30}
{"condition": "template", "value_template": "{{ is_state('sun.sun', 'below_horizon') }}"}
{"condition": "sun", "after": "sunset", "after_offset": "-01:00:00"}
```

### Action

```python
# 服务调用
{"service": "light.turn_on", "target": {"entity_id": "light.xxx"}, "data": {"brightness_pct": 80}}
{"service": "switch.turn_off", "target": {"entity_id": ["switch.a", "switch.b"]}}
{"service": "notify.notify", "data": {"message": "消息", "title": "标题"}}
{"service": "climate.set_temperature", "target": {"entity_id": "..."}, "data": {"temperature": 24}}

# 延时
{"delay": "00:05:00"}

# 条件分支
{"choose": [{"conditions": [...], "sequence": [...]}], "default": [...]}
```

---

## CLI 常用命令

```bash
# 本地脚本管理
ha-automation scripts                        # 列出本地脚本及启用状态
ha-automation script-disable <script>        # 禁用脚本（sync 时跳过）
ha-automation script-enable <script>         # 启用脚本
ha-automation run <script>                   # 单独运行一个脚本

# 同步
ha-automation sync                           # 同步所有已启用脚本到 HA
ha-automation sync --dry-run                 # 预览变更

# 设备
ha-automation discover                       # 发现并缓存设备
ha-automation devices "关键词"               # 搜索设备

# HA 自动化管理
ha-automation list                           # 列出所有自动化
ha-automation show automation.xxx            # 查看详情
ha-automation trigger automation.xxx         # 手动触发
ha-automation enable/disable automation.xxx  # 启用/禁用
ha-automation delete <id>                    # 删除
ha-automation reload                         # 重载所有自动化
ha-automation test                           # 测试连接
```

---

## 注意事项

- **小米 event 域实体**（无线开关）：触发器用 `platform: state`，不要用 `platform: event` + `event_type: xiaomi_home_event`
- 查询 HA 状态时用 `client.get_states(entity_id="...")` 而不是 bash + requests
- 设备名有歧义时直接硬编码 entity_id 并注释说明用途
