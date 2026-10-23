# Open Source Navigator 🧭

<img width="1920" height="836" alt="image" src="https://github.com/user-attachments/assets/b23cb8ea-d0ea-4d40-b43d-f25ff2a4ae74" />
<img width="1920" height="836" alt="image" src="https://github.com/user-attachments/assets/db40c06a-fc3a-4d01-8c4f-e626d273a1e1" />
<img width="1920" height="836" alt="image" src="https://github.com/user-attachments/assets/8f7f7848-9cd5-42c9-acd1-d7a9b65ec21f" />
<img width="1920" height="836" alt="image" src="https://github.com/user-attachments/assets/928c3770-a7bc-4234-9ddc-ea334b80c5f2" />
<img width="1920" height="836" alt="image" src="https://github.com/user-attachments/assets/b39b182b-dbbf-4d22-b4ee-38e41d8d4eb8" />

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent, full-stack open-source discovery platform designed to guide developers—especially beginners and junior engineers—to repositories where they can make meaningful contributions.

---

## 🌟 Key Features

- **Personalized Recommendations**: Automatically matches GitHub repositories to developer skills and interests with infinite scrolling.
- **Repository Scoring Engine**:
  - **Complexity Score (1–99)**: Logarithmic metric evaluating repository scope across stars, forks, and issue volume.
  - **Health Score (20–99)**: Community vitality metric factoring fork-to-star ratio and open issue backlog.
- **AI-Powered Insights & Roadmaps**: Integrates Google Gemini (`gemini-3.8-flash`) to generate concise 2-sentence repository summaries and actionable 3-step beginner contribution roadmaps.
- **Bookmarks & Profile Management**: Save prospective repositories for later and update skill tags dynamically.
- **Secure Authentication**: Salted bcrypt password hashing with signed JSON Web Tokens (JWT).

---

## 🏗️ Architecture

```
                                      +-------------------------+
                                      |   GitHub REST API v3    |
                                      +-------------------------+
                                                   ^
                                                   | (Search / Rate-limited)
+-----------------------+              +-------------------------+
|   React 19 Frontend   |              |     FastAPI Backend     |
| (Vite + Tailwind CSS) | <----------> | (Python 3.12 / ASGI)    |
+-----------------------+  HTTP / JWT  +-------------------------+
                                            |               |
                                            v               v
                           +--------------------+   +---------------------+
                           | PostgreSQL/SQLite  |   |   Google Gemini AI  |
                           | (SQLAlchemy ORM)   |   |   (GenAI SDK)       |
                           +--------------------+   +---------------------+
```

---

## 🚀 Quick Start with Docker (Recommended for Production)

The fastest way to spin up the entire production stack (Frontend, Backend, and PostgreSQL database) is with Docker Compose.

### 1. Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/) installed.

### 2. Configure Environment
Create a `.env` file in the root directory (or export environment variables):
```bash
POSTGRES_USER=navigator
POSTGRES_PASSWORD=your_secure_db_password
POSTGRES_DB=navigator_db
SECRET_KEY=generate_a_random_32_byte_hex_secret
ALLOWED_ORIGINS=http://localhost,http://localhost:80,http://localhost:5173
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_TOKEN=your_optional_github_personal_access_token
```

### 3. Launch Services
```bash
docker compose up -d --build
```

- **Frontend Application**: [http://localhost:80](http://localhost:80)
- **Backend API & Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Endpoint**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 💻 Local Development Setup

If you wish to develop without Docker:

### 1. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY and optionally GITHUB_TOKEN

# Run database migrations / start server
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Frontend Setup
```bash
cd frontend

# Install npm dependencies
npm install

# Configure environment
cp .env.example .env.local

# Start Vite dev server
npm run dev
```

The frontend will run on [http://localhost:5173](http://localhost:5173) and proxy API requests to [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## ⚙️ Environment Variables Reference

### Backend (`backend/.env`)

| Variable | Description | Default |
|---|---|---|
| `ENVIRONMENT` | Runtime environment (`development` or `production`) | `development` |
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./sql_app.db` |
| `SECRET_KEY` | Secret key for signing JWT tokens | Insecure default in dev; **mandatory** in prod |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token lifetime in minutes | `10080` (7 days) |
| `ALLOWED_ORIGINS` | Comma-delimited list of CORS permitted origins | `http://localhost:5173,http://127.0.0.1:5173` |
| `GEMINI_API_KEY` | Google AI Studio API key | *(Optional, provides fallback if unset)* |
| `GEMINI_MODEL` | Gemini model variant | `gemini-3.8-flash` |
| `GITHUB_TOKEN` | GitHub Personal Access Token (boosts rate limit to 5,000 req/hr) | *(Optional)* |

### Frontend (`frontend/.env`)

| Variable | Description | Default |
|---|---|---|
| `VITE_API_URL` | URL of the running backend API | `http://127.0.0.1:8000` |

---

## 🧪 Testing

### Backend Unit & Integration Tests
```bash
cd backend
pytest -v
```

### Frontend Build & Lint Verification
```bash
cd frontend
npm run build
npm run lint
```

---

## 🛡️ Production Deployment Checklist

- [x] Set `ENVIRONMENT=production` in the backend environment.
- [x] Configure a persistent PostgreSQL database instance via `DATABASE_URL`.
- [x] Set a cryptographically secure `SECRET_KEY` (e.g. `openssl rand -hex 32`).
- [x] Set `ALLOWED_ORIGINS` to your production frontend domain (e.g., `https://navigator.yourdomain.com`).
- [x] Provide a `GITHUB_TOKEN` to prevent search API rate limiting (403 errors).
- [x] Provide a valid `GEMINI_API_KEY` for AI roadmap generation.
- [x] Ensure `VITE_API_URL` in the frontend build points to your production backend URL.

---

## 📄 License

Distributed under the [MIT License](LICENSE).
