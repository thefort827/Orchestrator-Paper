# 智慧城市数字孪生系统 — API 契约

## 系统概述

基于 Three.js + FastAPI 的智慧城市数字孪生平台，具备自我演化能力。

## 技术栈

- **前端**: HTML5 + Three.js (3D) + Chart.js (图表) + WebSocket
- **后端**: Python FastAPI + SQLite + WebSocket
- **AI引擎**: scikit-learn + numpy (异常检测/聚类/优化)

## API 端点

### 1. 城市基础数据

```
GET  /api/city/buildings          → [{id, name, type, position, height, energy_usage}]
GET  /api/city/roads              → [{id, name, coordinates, traffic_level}]
GET  /api/city/sensors            → [{id, name, type, position, status}]
GET  /api/city/overview           → {total_buildings, total_sensors, alerts_count, health_score}
```

### 2. 实时传感器数据

```
GET  /api/sensors/{id}/readings   → [{timestamp, value, unit}]
GET  /api/sensors/realtime        → {sensor_id, value, timestamp, anomaly_score}
WS   /ws/sensors                  → 实时传感器数据流 (JSON)
```

### 3. 分析与洞察

```
GET  /api/analytics/traffic       → {hourly: [...], congestion_zones: [...]}
GET  /api/analytics/air_quality   → {aqi, pm25, pm10, co, no2, dominant_pollutant}
GET  /api/analytics/energy        → {total_kwh, by_building: [...], efficiency_score}
GET  /api/analytics/alerts        → [{id, type, severity, message, timestamp, resolved}]
```

### 4. 自我演化引擎

```
GET  /evolution/status            → {phase, metrics, learning_rate, iterations}
GET  /evolution/rules             → [{id, condition, action, confidence, created_at}]
POST /evolution/optimize          → {target: "traffic"|"energy"|"air", parameters: {...}}
GET  /evolution/history           → [{timestamp, metric, old_value, new_value, improvement}]
GET  /evolution/anomalies         → [{sensor_id, type, severity, detected_at, description}]
```

### 5. 系统管理

```
GET  /api/system/health           → {status, uptime, components: {...}}
POST /api/system/simulate         → {scenario: "rush_hour"|"pollution_event"|"power_outage"}
```

## 数据模型

### Building
```json
{
  "id": "b001",
  "name": "市政中心",
  "type": "government",
  "position": {"x": 100, "y": 0, "z": 50},
  "height": 30,
  "energy_usage": 450.5,
  "floor_count": 8
}
```

### Sensor
```json
{
  "id": "s001",
  "name": "交通流量传感器-A区",
  "type": "traffic",
  "position": {"x": 120, "y": 2, "z": 80},
  "status": "active",
  "reading": {"value": 245, "unit": "vehicles/hour", "timestamp": "2026-05-30T10:00:00Z"}
}
```

### EvolutionRule
```json
{
  "id": "r001",
  "condition": "traffic_congestion > 0.8 AND time == 'rush_hour'",
  "action": "extend_green_phase(target_intersection, +15s)",
  "confidence": 0.92,
  "improvement_pct": 12.5,
  "created_at": "2026-05-30T10:00:00Z"
}
```

### Anomaly
```json
{
  "id": "a001",
  "sensor_id": "s005",
  "type": "spike",
  "severity": "high",
  "detected_at": "2026-05-30T10:05:00Z",
  "description": "PM2.5 浓度突增 300%，可能由附近工地引起",
  "auto_response": "已通知环保部门，标记周边区域为监控重点"
}
```

## WebSocket 消息格式

```json
// 传感器数据流
{"type": "sensor_update", "data": {"sensor_id": "s001", "value": 245, "timestamp": "..."}}

// 异常告警
{"type": "anomaly_detected", "data": {"sensor_id": "s005", "severity": "high", "description": "..."}}

// 演化更新
{"type": "evolution_update", "data": {"metric": "traffic_efficiency", "old": 0.72, "new": 0.84, "improvement": "16.7%"}}
```

## 自我演化机制

### 1. 异常检测 (Isolation Forest)
- 实时监控所有传感器数据
- 检测异常值并分类（spike/drop/drift/pattern_change）
- 自动触发响应规则

### 2. 交通自适应优化 (Q-Learning)
- 根据实时车流量调整信号灯时长
- 学习历史模式，预测高峰期
- 目标：最小化平均等待时间

### 3. 能源负载均衡 (聚类分析)
- K-Means 聚类分析建筑用电模式
- 识别高能耗建筑并推荐优化方案
- 动态分配电力资源

### 4. 规则自动生成 (频繁模式挖掘)
- 从历史数据中挖掘频繁模式
- 自动生成 if-then 规则
- 规则经置信度评估后部署

### 5. 仪表盘自适应 (用户行为学习)
- 追踪用户查看频率
- 自动调整仪表盘布局
- 高频查看的组件置于显眼位置
