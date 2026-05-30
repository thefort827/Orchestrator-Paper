/* ===== 智慧城市数字孪生 — app.js ===== */
const API = 'http://localhost:8000';
let buildings = [], sensors = [], roads = [];
let scene, camera, renderer, controls;
let sensorMeshes = {}, buildingMeshes = {};
let chartTraffic, chartEnergy;
const trafficHistory = { labels: [], datasets: [{ data: [], borderColor: '#00d4ff', borderWidth: 2, fill: false, tension: 0.4, pointRadius: 0 }] };
const energyHistory = { labels: [], datasets: [{ data: [], backgroundColor: 'rgba(0,212,255,0.6)', borderColor: '#00d4ff', borderWidth: 1 }] };

// ===== Three.js 初始化 =====
function initThree() {
    const container = document.getElementById('three-container');
    const w = container.clientWidth, h = container.clientHeight;

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0e1a);
    scene.fog = new THREE.FogExp2(0x0a0e1a, 0.003);

    camera = new THREE.PerspectiveCamera(50, w / h, 1, 2000);
    camera.position.set(200, 180, 200);

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2.2;
    controls.minDistance = 50;
    controls.maxDistance = 500;

    // 灯光
    const ambient = new THREE.AmbientLight(0x334466, 0.6);
    scene.add(ambient);

    const dirLight = new THREE.DirectionalLight(0xffeedd, 1.0);
    dirLight.position.set(100, 200, 100);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 2048;
    dirLight.shadow.mapSize.height = 2048;
    dirLight.shadow.camera.near = 10;
    dirLight.shadow.camera.far = 500;
    dirLight.shadow.camera.left = -200;
    dirLight.shadow.camera.right = 200;
    dirLight.shadow.camera.top = 200;
    dirLight.shadow.camera.bottom = -200;
    scene.add(dirLight);

    const hemi = new THREE.HemisphereLight(0x0044ff, 0x002233, 0.4);
    scene.add(hemi);

    // 地面
    const groundGeo = new THREE.PlaneGeometry(600, 600);
    const groundMat = new THREE.MeshStandardMaterial({ color: 0x0a1520, roughness: 0.9 });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    scene.add(ground);

    // 网格线
    const gridHelper = new THREE.GridHelper(600, 30, 0x112233, 0x0a1520);
    scene.add(gridHelper);

    window.addEventListener('resize', onResize);
    animate();
}

function onResize() {
    const c = document.getElementById('three-container');
    camera.aspect = c.clientWidth / c.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(c.clientWidth, c.clientHeight);
}

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    // 传感器脉冲动画
    const t = Date.now() * 0.003;
    Object.values(sensorMeshes).forEach((mesh, i) => {
        mesh.scale.setScalar(1 + 0.15 * Math.sin(t + i));
        mesh.material.emissiveIntensity = 0.5 + 0.3 * Math.sin(t + i);
    });
    renderer.render(scene, camera);
}

// ===== 构建城市 =====
function buildCity(bldgData, roadData) {
    const colorMap = {
        government: 0x4a90d9, commercial: 0xe74c3c, tech: 0x2ecc71,
        residential: 0x9b59b6, hospital: 0x1abc9c, school: 0xf39c12,
        stadium: 0xe91e63, factory: 0x795548, power: 0x607d8b,
        mall: 0xff5722, office: 0x3f51b5, park: 0x4caf50,
        datacenter: 0x263238
    };

    bldgData.forEach(b => {
        const h = b.h;
        const geo = new THREE.BoxGeometry(b.type === 'park' ? 30 : 12, h, b.type === 'park' ? 30 : 12);
        const color = colorMap[b.type] || 0x666666;
        const mat = new THREE.MeshStandardMaterial({
            color: color,
            metalness: 0.3,
            roughness: 0.4,
            emissive: color,
            emissiveIntensity: 0.15
        });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(b.x, h / 2, b.z);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.userData = { type: 'building', data: b };
        scene.add(mesh);
        buildingMeshes[b.id] = mesh;

        // 窗户灯光效果
        if (h > 10) {
            const winGeo = new THREE.BoxGeometry(10, h * 0.7, 10);
            const winMat = new THREE.MeshBasicMaterial({ color: 0x001122, transparent: true, opacity: 0.3 });
            const winMesh = new THREE.Mesh(winGeo, winMat);
            winMesh.position.set(b.x, h / 2, b.z);
            scene.add(winMesh);
        }
    });

    roadData.forEach(r => {
        const dx = r.ex - r.sx, dz = r.ez - r.sz;
        const len = Math.sqrt(dx * dx + dz * dz);
        const angle = Math.atan2(dz, dx);
        const geo = new THREE.PlaneGeometry(len, r.w || 6);
        const mat = new THREE.MeshStandardMaterial({ color: 0x1a2a3a, roughness: 0.8 });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.rotation.x = -Math.PI / 2;
        mesh.rotation.z = -angle;
        mesh.position.set((r.sx + r.ex) / 2, 0.1, (r.sz + r.ez) / 2);
        mesh.receiveShadow = true;
        scene.add(mesh);
    });
}

// ===== 传感器标记 =====
function addSensorMarkers(sensorData) {
    sensorData.forEach(s => {
        if (sensorMeshes[s.id]) return;
        const geo = new THREE.SphereGeometry(2.5, 16, 16);
        const color = s.type === 'traffic' ? 0x00d4ff : s.type === 'air' ? 0x00e676 : 0xff9100;
        const mat = new THREE.MeshStandardMaterial({
            color: color, emissive: color, emissiveIntensity: 0.6,
            metalness: 0.5, roughness: 0.3
        });
        const mesh = new THREE.Mesh(geo, mat);
        // 传感器位置用经纬度映射到场景坐标
        const x = (s.lng - 114.33) * 2000;
        const z = (s.lat - 30.53) * 2000;
        mesh.position.set(x, 5, z);
        mesh.userData = { type: 'sensor', data: s };
        scene.add(mesh);
        sensorMeshes[s.id] = mesh;
    });
}

// ===== 点击交互 =====
function initClick() {
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    const container = document.getElementById('three-container');

    container.addEventListener('click', (e) => {
        const rect = container.getBoundingClientRect();
        mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(mouse, camera);

        const allMeshes = [...Object.values(buildingMeshes), ...Object.values(sensorMeshes)];
        const hits = raycaster.intersectObjects(allMeshes);
        if (hits.length > 0) {
            const obj = hits[0].object;
            if (obj.userData.type === 'building') {
                showBuildingPopup(obj.userData.data);
            } else if (obj.userData.type === 'sensor') {
                showSensorPopup(obj.userData.data);
            }
        }
    });
}

function showBuildingPopup(b) {
    document.getElementById('popup-name').textContent = b.name;
    document.getElementById('popup-type').textContent = b.type;
    document.getElementById('popup-height').textContent = b.h + 'm';
    document.getElementById('popup-energy').textContent = Math.round(b.h * 15) + ' kWh';
    document.getElementById('building-popup').classList.remove('hidden');
}

function showSensorPopup(s) {
    document.getElementById('popup-name').textContent = s.name;
    document.getElementById('popup-type').textContent = s.type;
    document.getElementById('popup-height').textContent = s.value + ' ' + s.unit;
    document.getElementById('popup-energy').textContent = s.status;
    document.getElementById('building-popup').classList.remove('hidden');
}

function closePopup() {
    document.getElementById('building-popup').classList.add('hidden');
}

// ===== Chart.js =====
function initCharts() {
    const tCtx = document.getElementById('chart-traffic').getContext('2d');
    chartTraffic = new Chart(tCtx, {
        type: 'line',
        data: trafficHistory,
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { display: false },
                y: { display: false, beginAtZero: true }
            },
            animation: { duration: 300 }
        }
    });

    const eCtx = document.getElementById('chart-energy').getContext('2d');
    chartEnergy = new Chart(eCtx, {
        type: 'bar',
        data: energyHistory,
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { display: false },
                y: { display: false, beginAtZero: true }
            },
            animation: { duration: 300 }
        }
    });
}

// ===== AQI 仪表盘 =====
function updateAQI(aqi) {
    const offset = 314 - (Math.min(aqi, 200) / 200) * 314;
    document.getElementById('aqi-arc').setAttribute('stroke-dashoffset', offset);
    document.getElementById('aqi-val').textContent = Math.round(aqi);
    const color = aqi < 50 ? '#00e676' : aqi < 100 ? '#00d4ff' : aqi < 150 ? '#ff9100' : '#ff1744';
    document.getElementById('aqi-arc').setAttribute('stroke', color);
    document.getElementById('aqi-val').style.color = color;
}

// ===== 数据更新 =====
async function updateData() {
    try {
        const [overview, traffic, air, energy, status, rules, anomalies] = await Promise.all([
            fetch(API + '/api/city/overview').then(r => r.json()),
            fetch(API + '/api/analytics/traffic').then(r => r.json()),
            fetch(API + '/api/analytics/air').then(r => r.json()),
            fetch(API + '/api/analytics/energy').then(r => r.json()),
            fetch(API + '/evolution/status').then(r => r.json()),
            fetch(API + '/evolution/rules').then(r => r.json()),
            fetch(API + '/evolution/anomalies').then(r => r.json())
        ]);

        // 状态栏
        document.querySelector('#sensor-count strong').textContent = overview.active_sensors;
        document.querySelector('#anomaly-count strong').textContent = overview.anomalies_count;
        document.getElementById('evolution-phase').textContent = status.phase === 'learning' ? '学习中' : '运行中';

        // 交通
        const tAvg = traffic.average_flow;
        document.getElementById('traffic-avg').textContent = Math.round(tAvg);
        document.getElementById('traffic-max').textContent = Math.round(traffic.max_flow);
        const tLevel = traffic.congestion_level;
        const tBadge = document.getElementById('traffic-level');
        tBadge.textContent = tLevel === 'high' ? '拥堵' : tLevel === 'medium' ? '中等' : '畅通';
        tBadge.className = 'card-badge' + (tLevel === 'high' ? ' orange' : '');

        trafficHistory.labels.push('');
        trafficHistory.datasets[0].data.push(tAvg);
        if (trafficHistory.labels.length > 20) { trafficHistory.labels.shift(); trafficHistory.datasets[0].data.shift(); }
        chartTraffic.update('none');

        // 空气
        updateAQI(air.aqi);
        document.getElementById('air-level').textContent = air.level;
        document.getElementById('pm25-val').textContent = air.pm25;
        document.getElementById('pm10-val').textContent = air.pm10;

        // 能耗
        document.getElementById('energy-total').textContent = Math.round(energy.total_kwh);
        document.getElementById('energy-avg').textContent = Math.round(energy.average_kwh);
        document.getElementById('energy-eff').textContent = Math.round(energy.efficiency * 100) + '%';

        energyHistory.labels.push('');
        energyHistory.datasets[0].data.push(energy.total_kwh);
        if (energyHistory.labels.length > 20) { energyHistory.labels.shift(); energyHistory.datasets[0].data.shift(); }
        chartEnergy.update('none');

        // 演化面板
        document.getElementById('evo-fill').style.width = Math.round(status.learning_progress * 100) + '%';
        document.getElementById('evo-pct').textContent = Math.round(status.learning_progress * 100) + '%';

        // 异常表
        const aTbody = document.querySelector('#anomaly-table tbody');
        aTbody.innerHTML = anomalies.map(a =>
            `<tr><td>${new Date(a.detected_at).toLocaleTimeString()}</td><td>${a.sensor_name || a.sensor_id}</td><td>${a.value}</td><td class="severity-${a.severity}">${a.severity}</td></tr>`
        ).join('');

        // 规则表
        const rTbody = document.querySelector('#rules-table tbody');
        rTbody.innerHTML = rules.map(r =>
            `<tr><td>${r.condition}</td><td>${r.action}</td><td>${Math.round(r.confidence * 100)}%</td></tr>`
        ).join('');

        // 历史表
        const hTbody = document.querySelector('#history-table tbody');
        hTbody.innerHTML = (status.history || []).slice(-10).reverse().map(h =>
            `<tr><td>#${h.iteration}</td><td>${h.new_rules}</td><td>${h.new_anomalies}</td><td>${h.traffic?.congestion_level || '-'}</td></tr>`
        ).join('');

    } catch (e) {
        console.error('Update failed:', e);
    }
}

// ===== WebSocket =====
function initWebSocket() {
    const ws = new WebSocket('ws://localhost:8000/ws/sensors');
    ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.type === 'sensor') {
            const s = msg.data;
            if (sensorMeshes[s.id]) {
                const color = s.status === 'anomaly' ? 0xff1744 :
                    s.type === 'traffic' ? 0x00d4ff : s.type === 'air' ? 0x00e676 : 0xff9100;
                sensorMeshes[s.id].material.color.setHex(color);
                sensorMeshes[s.id].material.emissive.setHex(color);
            }
        }
    };
    ws.onclose = () => setTimeout(initWebSocket, 5000);
}

// ===== 演化面板展开 =====
function toggleEvo() {
    const content = document.getElementById('evo-content');
    const arrow = document.getElementById('evo-arrow');
    content.classList.toggle('hidden');
    arrow.classList.toggle('rotated');
}

// ===== 启动 =====
async function init() {
    initThree();
    initCharts();

    const [bldgData, roadData, sensorData] = await Promise.all([
        fetch(API + '/api/city/buildings').then(r => r.json()),
        fetch(API + '/api/city/roads').then(r => r.json()),
        fetch(API + '/api/city/sensors').then(r => r.json())
    ]);

    buildings = bldgData;
    roads = roadData;
    sensors = sensorData;

    buildCity(bldgData, roadData);
    addSensorMarkers(sensorData);
    initClick();
    initWebSocket();

    updateData();
    setInterval(updateData, 3000);
}

window.addEventListener('load', init);
