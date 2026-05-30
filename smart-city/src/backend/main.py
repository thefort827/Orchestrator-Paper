"""智慧城市数字孪生 — FastAPI 后端"""
import asyncio
import json
import os
import time
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from evolution_engine import EvolutionEngine

app = FastAPI(title="Smart City Digital Twin", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

engine = EvolutionEngine()

# ===== 城市数据 =====

BUILDINGS = [
    {"id": "b01", "name": "市政中心", "type": "government", "x": 0, "z": 0, "h": 35, "color": "#4a90d9"},
    {"id": "b02", "name": "商业大厦A", "type": "commercial", "x": 80, "z": -50, "h": 55, "color": "#e74c3c"},
    {"id": "b03", "name": "商业大厦B", "type": "commercial", "x": -60, "z": -30, "h": 48, "color": "#e67e22"},
    {"id": "b04", "name": "科技园区", "type": "tech", "x": 100, "z": 70, "h": 30, "color": "#2ecc71"},
    {"id": "b05", "name": "居民楼群", "type": "residential", "x": -80, "z": 60, "h": 28, "color": "#9b59b6"},
    {"id": "b06", "name": "中心医院", "type": "hospital", "x": 50, "z": 90, "h": 22, "color": "#1abc9c"},
    {"id": "b07", "name": "大学", "type": "school", "x": -100, "z": 10, "h": 18, "color": "#f39c12"},
    {"id": "b08", "name": "体育场", "type": "stadium", "x": 30, "z": -90, "h": 15, "color": "#e91e63"},
    {"id": "b09", "name": "工厂区", "type": "factory", "x": -120, "z": -70, "h": 20, "color": "#795548"},
    {"id": "b10", "name": "发电站", "type": "power", "x": 130, "z": -20, "h": 28, "color": "#607d8b"},
    {"id": "b11", "name": "购物中心", "type": "mall", "x": -40, "z": -80, "h": 25, "color": "#ff5722"},
    {"id": "b12", "name": "写字楼C", "type": "office", "x": 70, "z": 40, "h": 42, "color": "#3f51b5"},
    {"id": "b13", "name": "公园绿地", "type": "park", "x": 0, "z": -60, "h": 2, "color": "#4caf50"},
    {"id": "b14", "name": "湖畔公寓", "type": "residential", "x": -30, "z": 100, "h": 32, "color": "#00bcd4"},
    {"id": "b15", "name": "数据中心", "type": "datacenter", "x": 110, "z": -60, "h": 18, "color": "#263238"},
]

ROADS = [
    {"id": "r01", "name": "长安大道", "sx": -160, "sz": 0, "ex": 160, "ez": 0, "w": 8},
    {"id": "r02", "name": "解放大道", "sx": 0, "sz": -130, "ex": 0, "ez": 130, "w": 8},
    {"id": "r03", "name": "光谷路", "sx": -120, "sz": -60, "ex": 120, "ez": -60, "w": 6},
    {"id": "r04", "name": "珞喻路", "sx": -120, "sz": 60, "ex": 120, "ez": 60, "w": 6},
    {"id": "r05", "name": "东湖路", "sx": 60, "sz": -120, "ex": 60, "ez": 120, "w": 5},
    {"id": "r06", "name": "环湖路", "sx": -80, "sz": 100, "ex": 80, "ez": 100, "w": 4},
]

# ===== REST API =====

@app.get("/api/city/buildings")
async def get_buildings():
    return BUILDINGS

@app.get("/api/city/roads")
async def get_roads():
    return ROADS

@app.get("/api/city/sensors")
async def get_sensors():
    return engine.simulator.get_all()

@app.get("/api/city/overview")
async def get_overview():
    sensors = engine.simulator.get_all()
    active = sum(1 for s in sensors if s["status"] == "normal")
    return {
        "total_buildings": len(BUILDINGS),
        "total_roads": len(ROADS),
        "total_sensors": len(sensors),
        "active_sensors": active,
        "health_score": engine.get_status()["health_score"],
        "anomalies_count": len(engine.anomalies),
        "rules_count": len(engine.rules)
    }

@app.get("/api/analytics/traffic")
async def get_traffic():
    data = engine.simulator.tick()
    traffic = [d for d in data if d["type"] == "traffic"]
    vals = [d["value"] for d in traffic]
    return {
        "sensors": traffic,
        "average_flow": round(sum(vals) / len(vals), 1) if vals else 0,
        "max_flow": round(max(vals), 1) if vals else 0,
        "min_flow": round(min(vals), 1) if vals else 0,
        "congestion_level": engine.traffic_optimizer.history[-1].get("congestion_level", "low") if engine.traffic_optimizer.history else "low"
    }

@app.get("/api/analytics/air")
async def get_air():
    data = engine.simulator.tick()
    air = [d for d in data if d["type"] == "air"]
    vals = [d["value"] for d in air]
    avg = sum(vals) / len(vals) if vals else 0
    return {
        "sensors": air,
        "aqi": round(avg, 1),
        "level": "优" if avg < 50 else "良" if avg < 100 else "轻度污染" if avg < 150 else "中度污染",
        "pm25": round(avg * 0.35, 1),
        "pm10": round(avg * 0.55, 1)
    }

@app.get("/api/analytics/energy")
async def get_energy():
    data = engine.simulator.tick()
    energy = [d for d in data if d["type"] == "energy"]
    vals = [d["value"] for d in energy]
    return {
        "sensors": energy,
        "total_kwh": round(sum(vals), 1),
        "average_kwh": round(sum(vals) / len(vals), 1) if vals else 0,
        "efficiency": round(engine.energy_balancer.analyze(energy).get("balance_score", 0.8), 3)
    }

@app.get("/evolution/status")
async def get_evolution_status():
    return engine.get_status()

@app.get("/evolution/rules")
async def get_evolution_rules():
    return engine.get_rules()

@app.get("/evolution/anomalies")
async def get_evolution_anomalies():
    return engine.get_anomalies()

@app.get("/evolution/history")
async def get_evolution_history():
    return engine.get_history()

# ===== WebSocket =====

ws_clients = set()

@app.websocket("/ws/sensors")
async def ws_sensors(websocket: WebSocket):
    await websocket.accept()
    ws_clients.add(websocket)
    try:
        while True:
            data = engine.simulator.tick()
            for s in data[:6]:
                await websocket.send_json({"type": "sensor", "data": s})
                if s["status"] == "anomaly":
                    await websocket.send_json({"type": "anomaly", "data": {
                        "sensor_id": s["id"], "name": s["name"],
                        "value": s["value"], "severity": "warning"
                    }})
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        ws_clients.discard(websocket)

# ===== 静态文件 =====

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.get("/")
async def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
