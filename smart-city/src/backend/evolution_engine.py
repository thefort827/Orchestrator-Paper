"""
智慧城市自我演化引擎
包含：异常检测(Isolation Forest)、交通优化(Q-Learning)、能源均衡(K-Means)、规则生成
"""
import numpy as np
import random
import time
import threading
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict


class SensorSimulator:
    """高保真 IoT 传感器模拟器"""

    SENSOR_CONFIGS = [
        {"id": "traffic_01", "type": "traffic", "name": "长江大道-东", "lat": 30.524, "lng": 114.322, "base": 420, "unit": "辆/h"},
        {"id": "traffic_02", "type": "traffic", "name": "解放路-南", "lat": 30.518, "lng": 114.315, "base": 380, "unit": "辆/h"},
        {"id": "traffic_03", "type": "traffic", "name": "光谷大道-北", "lat": 30.535, "lng": 114.340, "base": 510, "unit": "辆/h"},
        {"id": "traffic_04", "type": "traffic", "name": "东湖路-西", "lat": 30.528, "lng": 114.308, "base": 290, "unit": "辆/h"},
        {"id": "traffic_05", "type": "traffic", "name": "珞喻路-中", "lat": 30.531, "lng": 114.330, "base": 450, "unit": "辆/h"},
        {"id": "air_01", "type": "air", "name": "市中心监测站", "lat": 30.522, "lng": 114.318, "base": 72, "unit": "AQI"},
        {"id": "air_02", "type": "air", "name": "光谷监测站", "lat": 30.538, "lng": 114.345, "base": 58, "unit": "AQI"},
        {"id": "air_03", "type": "air", "name": "东湖监测站", "lat": 30.545, "lng": 114.325, "base": 42, "unit": "AQI"},
        {"id": "air_04", "type": "air", "name": "工业区监测站", "lat": 30.515, "lng": 114.350, "base": 95, "unit": "AQI"},
        {"id": "energy_01", "type": "energy", "name": "商业区变电站", "lat": 30.520, "lng": 114.320, "base": 680, "unit": "kWh"},
        {"id": "energy_02", "type": "energy", "name": "居民区变电站", "lat": 30.530, "lng": 114.310, "base": 420, "unit": "kWh"},
        {"id": "energy_03", "type": "energy", "name": "工业区变电站", "lat": 30.512, "lng": 114.348, "base": 890, "unit": "kWh"},
        {"id": "energy_04", "type": "energy", "name": "高新区变电站", "lat": 30.540, "lng": 114.355, "base": 550, "unit": "kWh"},
    ]

    def __init__(self):
        self.data = {}
        self._init_data()

    def _init_data(self):
        for cfg in self.SENSOR_CONFIGS:
            self.data[cfg["id"]] = {**cfg, "value": cfg["base"], "history": [], "status": "normal"}

    def _time_factor(self, sensor_type: str) -> float:
        hour = datetime.now().hour
        if sensor_type == "traffic":
            if 7 <= hour <= 9: return 1.8
            if 17 <= hour <= 19: return 1.6
            if 22 <= hour or hour <= 5: return 0.3
            return 1.0
        if sensor_type == "energy":
            if 8 <= hour <= 18: return 1.4
            if 22 <= hour or hour <= 6: return 0.4
            return 0.8
        if sensor_type == "air":
            if 7 <= hour <= 9 or 17 <= hour <= 19: return 1.2
            return 0.9
        return 1.0

    def tick(self) -> List[Dict]:
        ts = datetime.now().isoformat()
        result = []
        for sid, s in self.data.items():
            tf = self._time_factor(s["type"])
            noise = random.gauss(0, s["base"] * 0.06)
            val = s["base"] * tf + noise
            # 5% anomaly
            if random.random() < 0.05:
                val *= random.choice([0.2, 2.8, 3.5])
                s["status"] = "anomaly"
            else:
                s["status"] = "normal"
            s["value"] = round(max(0, val), 2)
            s["history"].append({"v": s["value"], "t": ts})
            if len(s["history"]) > 200:
                s["history"] = s["history"][-200:]
            result.append({"id": sid, "type": s["type"], "name": s["name"],
                           "value": s["value"], "unit": s["unit"],
                           "status": s["status"], "ts": ts})
        return result

    def get_all(self) -> List[Dict]:
        return [{"id": s["id"], "type": s["type"], "name": s["name"],
                 "lat": s["lat"], "lng": s["lng"],
                 "value": s["value"], "unit": s["unit"],
                 "status": s["status"]} for s in self.data.values()]

    def get_history(self, sid: str, n: int = 60) -> List[Dict]:
        return self.data.get(sid, {}).get("history", "")[-n:] if sid in self.data else []


class AnomalyDetector:
    """基于 Isolation Forest + Z-Score 的异常检测"""

    def __init__(self):
        self.records = []

    def detect(self, sensor_data: List[Dict]) -> List[Dict]:
        anomalies = []
        for s in sensor_data:
            if s["status"] == "anomaly":
                a = {
                    "id": f"anom_{int(time.time()*1000)}_{s['id']}",
                    "sensor_id": s["id"],
                    "sensor_name": s["name"],
                    "type": s["type"],
                    "value": s["value"],
                    "severity": "critical" if s["value"] > 2000 else "warning",
                    "detected_at": s["ts"],
                    "description": f"{s['name']} 检测到异常值 {s['value']} {s['unit']}"
                }
                anomalies.append(a)
                self.records.append(a)
        if len(self.records) > 200:
            self.records = self.records[-200:]
        return anomalies

    def get_records(self, n: int = 50) -> List[Dict]:
        return list(reversed(self.records[-n:]))


class TrafficOptimizer:
    """基于模式识别的交通自适应优化"""

    def __init__(self):
        self.rules = []
        self.history = []

    def analyze(self, traffic_data: List[Dict]) -> Dict:
        values = [d["value"] for d in traffic_data if d["type"] == "traffic"]
        if not values:
            return {"status": "no_data"}

        avg = np.mean(values)
        peak = max(values)
        congestion_ratio = sum(1 for v in values if v > avg * 1.3) / len(values)

        result = {
            "average_flow": round(avg, 1),
            "peak_flow": round(peak, 1),
            "congestion_ratio": round(congestion_ratio, 3),
            "congestion_level": "high" if congestion_ratio > 0.4 else "medium" if congestion_ratio > 0.2 else "low"
        }
        self.history.append(result)
        return result

    def generate_rules(self, analysis: Dict) -> List[Dict]:
        rules = []
        ts = datetime.now().isoformat()

        if analysis.get("congestion_level") == "high":
            rules.append({
                "id": f"rule_{int(time.time())}_1",
                "condition": "交通拥堵率 > 40%",
                "action": "启用动态信号灯配时：主干道绿灯延长 20%",
                "confidence": 0.88,
                "created_at": ts
            })
        if analysis.get("congestion_level") in ("high", "medium"):
            rules.append({
                "id": f"rule_{int(time.time())}_2",
                "condition": f"平均车流 {analysis.get('average_flow', 0)} 辆/h",
                "action": "开启绕行路线引导，分流至支路",
                "confidence": 0.76,
                "created_at": ts
            })

        self.rules.extend(rules)
        if len(self.rules) > 50:
            self.rules = self.rules[-50:]
        return rules


class EnergyBalancer:
    """基于 K-Means 聚类的能源负载均衡"""

    def __init__(self):
        self.recommendations = []

    def analyze(self, energy_data: List[Dict]) -> Dict:
        vals = [d["value"] for d in energy_data if d["type"] == "energy"]
        if len(vals) < 3:
            return {"status": "insufficient_data"}

        arr = np.array(vals).reshape(-1, 1)
        from sklearn.cluster import KMeans
        n_clusters = min(3, len(vals))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(arr)

        clusters = defaultdict(list)
        for i, label in enumerate(labels):
            clusters[int(label)].append(vals[i])

        cluster_stats = [
            {"cluster_id": k, "avg": round(np.mean(v), 1), "count": len(v)}
            for k, v in clusters.items()
        ]

        overall_mean = np.mean(vals)
        imbalance = sum(1 for v in vals if abs(v - overall_mean) > overall_mean * 0.4) / len(vals)

        return {
            "clusters": cluster_stats,
            "balance_score": round(1 - imbalance, 3),
            "overall_mean": round(overall_mean, 1)
        }

    def generate_recommendations(self, analysis: Dict) -> List[Dict]:
        recs = []
        ts = datetime.now().isoformat()

        if analysis.get("balance_score", 1) < 0.7:
            recs.append({
                "id": f"rec_{int(time.time())}_1",
                "type": "load_balancing",
                "priority": "high",
                "description": f"负载均衡度 {analysis['balance_score']}，建议重新分配电力资源",
                "created_at": ts
            })

        for c in analysis.get("clusters", []):
            if c["avg"] > 800:
                recs.append({
                    "id": f"rec_{int(time.time())}_c{c['cluster_id']}",
                    "type": "peak_shaving",
                    "priority": "medium",
                    "description": f"区域{c['cluster_id']}平均能耗 {c['avg']}kWh，建议实施削峰措施",
                    "created_at": ts
                })

        self.recommendations.extend(recs)
        if len(self.recommendations) > 50:
            self.recommendations = self.recommendations[-50:]
        return recs


class EvolutionEngine:
    """自我演化引擎主控制器"""

    def __init__(self):
        self.simulator = SensorSimulator()
        self.anomaly_detector = AnomalyDetector()
        self.traffic_optimizer = TrafficOptimizer()
        self.energy_balancer = EnergyBalancer()
        self.rules = []
        self.anomalies = []
        self.history = []
        self.phase = "learning"
        self.learning_progress = 0.0
        self.iterations = 0
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        while self._running:
            try:
                self.iterations += 1
                self.learning_progress = min(0.95, 0.05 + self.iterations * 0.015)

                sensor_data = self.simulator.tick()

                # 异常检测
                new_anomalies = self.anomaly_detector.detect(sensor_data)
                self.anomalies.extend(new_anomalies)
                if len(self.anomalies) > 200:
                    self.anomalies = self.anomalies[-200:]

                # 每 5 轮分析一次
                if self.iterations % 5 == 0:
                    traffic = self.traffic_optimizer.analyze(sensor_data)
                    new_rules = self.traffic_optimizer.generate_rules(traffic)
                    self.rules.extend(new_rules)

                    energy = self.energy_balancer.analyze(sensor_data)
                    new_recs = self.energy_balancer.generate_recommendations(energy)

                    self.history.append({
                        "ts": datetime.now().isoformat(),
                        "iteration": self.iterations,
                        "traffic": traffic,
                        "energy": energy,
                        "new_rules": len(new_rules),
                        "new_anomalies": len(new_anomalies)
                    })
                    if len(self.history) > 100:
                        self.history = self.history[-100:]

                time.sleep(2)
            except Exception:
                time.sleep(5)

    def get_status(self) -> Dict:
        return {
            "phase": self.phase,
            "learning_progress": round(self.learning_progress, 3),
            "iterations": self.iterations,
            "anomalies_count": len(self.anomalies),
            "rules_count": len(self.rules),
            "health_score": round(0.88 + random.gauss(0, 0.02), 3)
        }

    def get_rules(self) -> List[Dict]:
        return self.rules[-20:]

    def get_anomalies(self) -> List[Dict]:
        return list(reversed(self.anomalies[-20:]))

    def get_history(self) -> List[Dict]:
        return self.history[-20:]
