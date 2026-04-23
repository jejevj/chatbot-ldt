# Chatbot Satu Data Pertahanan - Kementerian Pertahanan RI

Chatbot berbasis RAG (Retrieval-Augmented Generation) untuk mencari dan mengakses data terbuka Kementerian Pertahanan Republik Indonesia.

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd ldt_chatbot

# Setup environment
cp .env.docker .env

# Start all services
docker-compose up -d

# Access application
# Frontend: http://localhost:8766/chatbot/
# API Docs: http://localhost:8765/chatbot-api/docs
```

📖 **Detailed Docker guide**: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)

### Option 2: Manual Setup

#### Backend
```bash
cd api
pip install -r requirements.txt
run.bat
```

API: http://localhost:8080/chatbot-api
Docs: http://localhost:8080/chatbot-api/docs

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:3210/chatbot/

## 📁 Project Structure

### Backend (api/)
```
api/
├── app/
│   ├── api/routes/      # API endpoints (chat, sessions, device, data, health)
│   ├── services/        # Business logic (search, llm, embeddings)
│   ├── config.py        # Configuration & settings
│   ├── database.py      # SQLAlchemy models
│   ├── main.py          # FastAPI application
│   └── schemas.py       # Pydantic validation schemas
├── migrations/          # Database SQL migrations
├── scripts/             # Utility scripts (embeddings, migrations)
├── Dockerfile           # Docker image for API
└── main.py             # Application entry point
```

### Frontend (frontend/)
```
frontend/
├── src/
│   ├── components/      # Vue components (ChatMessage, ChatInput, Sidebar, etc.)
│   ├── composables/     # Composition API logic (useChat, useSessions, useDevice)
│   ├── services/        # API service layer (axios)
│   ├── views/           # Page components (ChatView, ErrorPage)
│   ├── router/          # Vue Router configuration
│   ├── config/          # App configuration
│   └── utils/           # Utility functions
├── Dockerfile           # Docker image for frontend
├── nginx.conf           # Nginx configuration
└── App.vue             # Root component
```

## 🛠️ Tech Stack

**Backend:**
- FastAPI - Modern Python web framework
- PostgreSQL + pgvector - Database with vector search
- Qwen 2.5 7B - Language model for generation
- SQLAlchemy - ORM
- Sentence Transformers - Text embeddings

**Frontend:**
- Vue.js 3 - Progressive framework
- Vue Router - Client-side routing
- Vite - Build tool & dev server
- Tailwind CSS - Utility-first CSS
- VueUse - Composition utilities
- Axios - HTTP client

**Infrastructure:**
- Docker & Docker Compose
- Nginx - Web server & reverse proxy

## ⚙️ Configuration

### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://postgres:qwert12345!@127.0.0.1:5433/satu_data_db

# Qwen LLM
QWEN_API_URL=http://localhost:9002/v1/chat/completions
QWEN_MODEL=Qwen/Qwen2.5-7B-Instruct-AWQ

# Maintenance Mode
MAINTENANCE_MODE=false
MAINTENANCE_MESSAGE=Sistem sedang dalam pemeliharaan
MAINTENANCE_ETA=
```

### Frontend (.env)
```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8080/chatbot-api

# Maintenance Mode
VITE_MAINTENANCE_MODE=false
VITE_MAINTENANCE_MESSAGE=Sistem sedang dalam pemeliharaan
VITE_MAINTENANCE_ETA=

# Error Handling
VITE_SHOW_ERROR_DETAILS=false
```

## ✨ Features

- 🔍 **Smart Search**: Keyword-based + vector similarity search
- 💬 **Context-Aware**: Remembers conversation history (10 messages)
- 📚 **Session Management**: Per-device chat sessions
- 🔐 **Device Authentication**: Fingerprint-based identification
- 🌓 **Dark/Light Mode**: Theme switching
- 📱 **Responsive Design**: Mobile-friendly interface
- ✏️ **Edit Messages**: Edit last user message
- 🗑️ **Delete Sessions**: Single or bulk delete
- 🔧 **Maintenance Mode**: Configurable maintenance page
- ❌ **Error Handling**: Custom error pages (404, 500, maintenance)
- 🎨 **Smooth Animations**: Transitions and loading states

## 📚 API Documentation

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8765/chatbot-api/docs
- **ReDoc**: http://localhost:8765/chatbot-api/redoc

### Main Endpoints

- `POST /chatbot-api/chat/history` - Send message with history
- `GET /chatbot-api/chat/sessions` - List all sessions
- `GET /chatbot-api/chat/sessions/{id}` - Get session messages
- `DELETE /chatbot-api/chat/sessions/{id}` - Delete session
- `POST /chatbot-api/device/register` - Register device
- `GET /chatbot-api/health` - Health check

## 🐳 Docker Deployment

### Ports

- **Frontend**: 8766
- **Backend API**: 8765
- **PostgreSQL**: 5433 (jika menggunakan Docker PostgreSQL)

### Option 1: Dengan PostgreSQL di Docker (Default)

```bash
# Start semua services termasuk PostgreSQL
docker-compose up -d
```

### Option 2: Dengan PostgreSQL Eksternal (Sudah Ada)

Jika Anda sudah punya PostgreSQL yang berjalan:

```bash
# Setup environment
cp .env.external-db .env
# Edit .env dan sesuaikan DATABASE_URL

# Start tanpa PostgreSQL
docker-compose -f docker-compose.external-db.yml up -d
```

📖 **Panduan lengkap**: [EXTERNAL_DATABASE.md](EXTERNAL_DATABASE.md)

### Services

1. **postgres** - PostgreSQL with pgvector (opsional, jika tidak pakai eksternal)
2. **api** - FastAPI backend
3. **frontend** - Vue.js + Nginx

### Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild
docker-compose up -d --build

# Check status
docker-compose ps
```

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for complete guide.

## 🔧 Maintenance Mode

### Enable Maintenance

**Backend** (api/.env):
```env
MAINTENANCE_MODE=true
MAINTENANCE_MESSAGE=Sistem sedang dalam pemeliharaan
MAINTENANCE_ETA=2 jam
```

**Frontend** (frontend/.env):
```env
VITE_MAINTENANCE_MODE=true
VITE_MAINTENANCE_MESSAGE=Sistem sedang dalam pemeliharaan
VITE_MAINTENANCE_ETA=23:00 WIB
```

Restart services after changing configuration.

## 🗄️ Database

### Schema

- `t_devices` - Device registrations
- `t_chat_sessions` - Chat sessions
- `t_chat_messages` - Chat messages
- `v_detail_data_terbuka` - Data view (read-only)

### Migrations

```bash
# Run migrations
cd api/scripts
python run_migration.py

# Generate embeddings
python generate_embeddings.py
```

## 🚦 Error Handling

Application includes comprehensive error handling:

- **404 Page** - Page not found
- **500 Page** - Server error
- **Maintenance Page** - System maintenance
- **Network Error** - Connection issues

See [ERROR_HANDLING.md](ERROR_HANDLING.md) for details.

## 🔒 Security

- Device fingerprint authentication
- CORS configuration
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection (Vue.js escaping)
- Security headers (Nginx)
- Environment variable secrets

## 📊 Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8765/chatbot-api/health

# Frontend health
curl http://localhost:8766/chatbot/

# Database health
docker exec chatbot-postgres pg_isready -U postgres
```

### Logs

```bash
# Docker logs
docker-compose logs -f api
docker-compose logs -f frontend

# API logs (manual setup)
tail -f api/logs/api.log
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License.

## 📧 Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: See markdown files in repository

## 🙏 Acknowledgments

- Kementerian Pertahanan Republik Indonesia
- Qwen Team for the LLM model
- Vue.js & FastAPI communities
