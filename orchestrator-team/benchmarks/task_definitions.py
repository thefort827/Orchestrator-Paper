"""
Benchmark Task Definitions for Orchestrator Paper Experiments.

Three task categories of increasing complexity:
  1. Blog System (Simple): 8 files, 2 domains
  2. E-commerce Store (Medium): 14 files, 4 domains
  3. Real-time Chat App (Complex): 18 files, 5 domains
"""
from dataclasses import dataclass, field


@dataclass
class BenchmarkTask:
    task_id: str
    name: str
    description: str
    required_files: list[str]
    expected_endpoints: list[str]
    complexity_score: int  # 1-10
    domains: list[str]
    acceptance_criteria: list[str]


# ── Task 1: Blog System (Simple) ──────────────────────────────────────────────

BLOG_SYSTEM = BenchmarkTask(
    task_id="blog_system",
    name="Personal Blog System",
    description=(
        "Build a personal blog with user authentication, "
        "CRUD posts, comment system, and tag filtering. "
        "Frontend: responsive HTML/CSS/JS. "
        "Backend: Flask REST API with SQLite."
    ),
    required_files=[
        "index.html",
        "style.css",
        "app.js",
        "server.py",
        "models.py",
        "requirements.txt",
        "Dockerfile",
        "README.md",
    ],
    expected_endpoints=[
        "POST /api/auth/register",
        "POST /api/auth/login",
        "GET  /api/posts",
        "POST /api/posts",
        "GET  /api/posts/<id>",
        "PUT  /api/posts/<id>",
        "DELETE /api/posts/<id>",
        "POST /api/posts/<id>/comments",
        "GET  /api/posts/<id>/comments",
        "GET  /api/tags/<tag>",
    ],
    complexity_score=3,
    domains=["frontend", "backend", "database", "devops"],
    acceptance_criteria=[
        "All 8 files present and non-empty",
        "server.py contains Flask app with required endpoints",
        "index.html references style.css and app.js",
        "Dockerfile is valid",
        "requirements.txt lists flask and sqlite dependencies",
    ],
)


# ── Task 2: E-commerce Store (Medium) ────────────────────────────────────────

ECOMMERCE_STORE = BenchmarkTask(
    task_id="ecommerce_store",
    name="E-commerce Store",
    description=(
        "Build a mini e-commerce platform with product catalog, "
        "shopping cart, checkout flow, admin dashboard, and order management. "
        "Frontend: React-like SPA with product grid, cart sidebar, and admin panel. "
        "Backend: FastAPI with PostgreSQL, product/cart/order models, "
        "payment mock, and JWT authentication."
    ),
    required_files=[
        "index.html",
        "style.css",
        "app.js",
        "cart.js",
        "admin.js",
        "server.py",
        "models.py",
        "auth.py",
        "routes_products.py",
        "routes_cart.py",
        "routes_orders.py",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "README.md",
    ],
    expected_endpoints=[
        "POST /api/auth/register",
        "POST /api/auth/login",
        "GET  /api/products",
        "POST /api/products",
        "GET  /api/products/<id>",
        "PUT  /api/products/<id>",
        "DELETE /api/products/<id>",
        "GET  /api/cart",
        "POST /api/cart/items",
        "PUT  /api/cart/items/<id>",
        "DELETE /api/cart/items/<id>",
        "POST /api/checkout",
        "GET  /api/orders",
        "GET  /api/orders/<id>",
        "PUT  /api/admin/orders/<id>/status",
    ],
    complexity_score=6,
    domains=["frontend", "backend", "database", "auth", "devops"],
    acceptance_criteria=[
        "All 15 files present and non-empty",
        "server.py wires all route modules",
        "models.py defines Product, CartItem, Order, User models",
        "auth.py implements JWT token generation and verification",
        "Frontend files (index.html, cart.js, admin.js) are coherent",
        "docker-compose.yml defines postgres + app services",
    ],
)


# ── Task 3: Real-time Chat App (Complex) ─────────────────────────────────────

CHAT_APP = BenchmarkTask(
    task_id="chat_app",
    name="Real-time Chat Application",
    description=(
        "Build a real-time chat application with WebSocket messaging, "
        "group chats, file sharing, message search, user presence, "
        "and an admin moderation dashboard. "
        "Frontend: HTML5 with WebSocket client, chat UI, file upload, "
        "and admin panel. "
        "Backend: FastAPI + WebSocket, SQLAlchemy with PostgreSQL, "
        "Redis for presence/cache, and JWT auth."
    ),
    required_files=[
        "index.html",
        "style.css",
        "app.js",
        "chat.js",
        "admin.js",
        "websocket_client.js",
        "server.py",
        "models.py",
        "auth.py",
        "ws_handler.py",
        "routes_messages.py",
        "routes_groups.py",
        "routes_files.py",
        "presence.py",
        "search.py",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "README.md",
    ],
    expected_endpoints=[
        "POST /api/auth/register",
        "POST /api/auth/login",
        "GET  /api/users/me",
        "GET  /api/groups",
        "POST /api/groups",
        "POST /api/groups/<id>/members",
        "GET  /api/messages/<group_id>",
        "POST /api/messages/<group_id>",
        "POST /api/files/upload",
        "GET  /api/files/<id>",
        "GET  /api/search?q=",
        "GET  /api/admin/users",
        "PUT  /api/admin/users/<id>/ban",
        "GET  /ws",
    ],
    complexity_score=9,
    domains=["frontend", "backend", "database", "websocket", "auth", "devops", "realtime"],
    acceptance_criteria=[
        "All 19 files present and non-empty",
        "ws_handler.py implements WebSocket connection manager",
        "presence.py tracks online/offline status",
        "search.py provides full-text message search",
        "docker-compose.yml includes redis + postgres + app",
        "Frontend has separate chat.js and websocket_client.js",
        "admin.js provides moderation UI",
    ],
)


# ── Registry ──────────────────────────────────────────────────────────────────

ALL_TASKS: dict[str, BenchmarkTask] = {
    t.task_id: t for t in [BLOG_SYSTEM, ECOMMERCE_STORE, CHAT_APP]
}


def get_task(task_id: str) -> BenchmarkTask:
    if task_id not in ALL_TASKS:
        raise ValueError(f"Unknown task: {task_id}. Available: {list(ALL_TASKS.keys())}")
    return ALL_TASKS[task_id]
