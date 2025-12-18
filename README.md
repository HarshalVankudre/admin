<div align="center">

# 🚀 Ruko Admin Dashboard

<p>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
</p>

<p>
  <strong>A sleek, modern admin dashboard for monitoring and managing your Ruko AI chatbot platform.</strong>
</p>

<p>
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-api-reference">API</a> •
  <a href="#-docker-deployment">Docker</a> •
  <a href="#-configuration">Config</a>
</p>

---

</div>

## ✨ Features

<table>
<tr>
<td width="50%">

### 📊 Real-Time Analytics
- **Live Statistics** — Total users, conversations, and messages
- **24-Hour Metrics** — Messages, errors, and active users today
- **Response Time KPIs** — Average, P50, and P95 latencies (7-day window)

</td>
<td width="50%">

### 📈 Interactive Charts
- **Hourly Volume** — Message activity visualization (last 24h)
- **Daily Trends** — 14-day overview of message patterns
- **Tool Usage** — Top assistant tools ranked by frequency

</td>
</tr>
<tr>
<td width="50%">

### 👥 User Management
- **User Directory** — Searchable list with activity metrics
- **User Profiles** — Detailed view with conversation history
- **Engagement Stats** — Messages, errors, and active status per user

</td>
<td width="50%">

### 💬 Conversation Explorer
- **Full History** — Browse all conversations with filters
- **Message Timeline** — Complete message thread with metadata
- **Error Tracking** — Quickly identify and diagnose issues

</td>
</tr>
</table>

##  Quick Start

### Prerequisites

- **Python 3.11+**
- **PostgreSQL** database with Ruko schema
- (Optional) **Docker** for containerized deployment

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/HarshalVankudre/admin.git
cd admin

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# 5. Initialize database schema (first time only)
python backend/create_db.py

# 6. Run the application
python backend/main.py
```

### 🌐 Access the Dashboard

Open your browser and navigate to:

```
http://localhost:8080/dashboard
```

## 🐳 Docker Deployment

### Build & Run

```bash
# Build the image
docker build -t ruko-admin .

# Run the container
docker run --rm -p 8080:8080 --env-file .env ruko-admin
```

### Docker Compose (Optional)

```yaml
version: '3.8'
services:
  ruko-admin:
    build: .
    ports:
      - "8080:8080"
    env_file:
      - .env
    restart: unless-stopped
```

## 📡 API Reference

All API endpoints are prefixed with `/admin` and return JSON responses.

### Health & Status

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | `GET` | Service health check |
| `/admin/db-health` | `GET` | Database connectivity & latency |

### Analytics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/stats` | `GET` | Dashboard statistics & KPIs |
| `/admin/activity` | `GET` | Time series data (hourly/daily) |
| `/admin/tools` | `GET` | Top tools usage (last 7 days) |

### Data Resources

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/users` | `GET` | List all users (paginated, searchable) |
| `/admin/users/{id}` | `GET` | User detail with conversations |
| `/admin/conversations` | `GET` | List conversations (filtered) |
| `/admin/conversations/{id}` | `GET` | Conversation with all messages |
| `/admin/messages` | `GET` | Search messages (filtered) |
| `/admin/errors` | `GET` | Messages with errors |

### Query Parameters

Most list endpoints support:

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | int | Results per page (default: 50) |
| `offset` | int | Pagination offset (default: 0) |
| `search` | string | Search by name, email, or content |
| `date_from` | date | Filter by start date |
| `date_to` | date | Filter by end date |
| `has_error` | bool | Filter by error presence |

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# PostgreSQL Connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ruko_admin
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Connection Pool (optional)
DB_POOL_MIN=1
DB_POOL_MAX=10

# Application
PORT=8080
POSTGRES_CONNECT_TIMEOUT=5
POSTGRES_APP_NAME=ruko-admin-dashboard

# Auto-initialize DB pool on startup
ADMIN_DB_INIT_ON_STARTUP=0
```

## 🏗️ Project Structure

```
admin/
├── 📁 backend/              # Backend API server
│   ├── 📄 main.py           # FastAPI application entry point
│   ├── 📄 config.py         # Configuration settings
│   ├── 📄 database.py       # Database connection pool & utilities
│   ├── 📁 routes/           # API route handlers
│   │   ├── 📄 __init__.py   # Route aggregation
│   │   ├── 📄 health.py     # Health check endpoints
│   │   ├── 📄 stats.py      # Statistics & activity endpoints
│   │   ├── 📄 users.py      # User management endpoints
│   │   ├── 📄 conversations.py  # Conversation endpoints
│   │   └── 📄 messages.py   # Message endpoints
│   ├── 📄 create_db.py      # Database schema initialization
│   ├── 📄 requirements.txt  # Python dependencies
│   └── 📄 __init__.py       # Package init
├── 📁 frontend/             # Frontend UI
│   └── 📄 dashboard.html    # Single-page admin dashboard
├── 📄 Dockerfile            # Container build instructions
├── 📄 .env.example          # Environment template
├── 📄 .gitignore            # Git ignored files
└── 📄 README.md             # Documentation
```

## 🔒 Security Notes

- **Read-Only APIs** — All `/admin/*` endpoints are read-only
- **CORS Enabled** — Configure allowed origins for production
- **No Authentication** — Add your own auth middleware for production use
- **Connection Pooling** — Uses thread-safe connection pooling

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI (Python 3.11) |
| **Database** | PostgreSQL with psycopg2 |
| **Frontend** | Vanilla HTML/CSS/JS (embedded) |
| **Deployment** | Docker + Uvicorn |

## 📜 License

This project is proprietary software. All rights reserved.

---

<div align="center">

[⬆ Back to Top](#-ruko-admin-dashboard)

</div>
