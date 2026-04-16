# LLM Chat Application
## Architecture
This project uses a React SPA frontend with a FastAPI backend following MCS (Models, Controllers, Services). Controllers are thin API routers, business logic is implemented in services, and models are SQLAlchemy ORM entities.
## JWT + Redis Auth Flow
- Access token: JWT, 15 minutes, kept in client memory.
- Refresh token: random token, 30 days, stored in Redis as `refresh:{token}` with value `user_id`.
- On access expiry, client calls `POST /auth/refresh` to receive a new access token.
- Logout calls `POST /auth/logout`, deleting the refresh token key in Redis.
## Setup
1. `cp .env.example .env` and fill values.
2. `docker compose up -d`
3. `pip install -r requirements.txt`
4. `alembic upgrade head`
5. `Q4_K_M.gguf` as `model.gguf` chosen. Dwnload it here: https://hf.tst.eu/model#Gemma-4-Queen-31B-it-i1-GGUF
6. `uvicorn app.main:app --reload`
7. `cd frontend && npm install && npm run dev`
## GitHub OAuth App Settings
Authorization callback URL: `http://localhost:8000/auth/github/callback`
## API Routes
| Method | Route | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | No | Register local user and return token pair |
| POST | `/auth/login` | No | Login local user and return token pair |
| POST | `/auth/refresh` | No | Issue a new access token from refresh token |
| POST | `/auth/logout` | Yes | Revoke refresh token |
| GET | `/auth/github` | No | Redirect to GitHub OAuth authorize URL |
| GET | `/auth/github/callback` | No | Exchange code, link/create user, return token pair |
| POST | `/chats` | Yes | Create chat |
| GET | `/chats` | Yes | List current user chats |
| GET | `/chats/{chat_id}` | Yes | Get chat with messages |
| DELETE | `/chats/{chat_id}` | Yes | Delete chat and its messages |
| GET | `/chats/{chat_id}/messages` | Yes | List messages for chat |
| POST | `/chats/{chat_id}/messages/ask` | Yes | Ask LLM (streaming or non-streaming) |
| GET | `/health` | No | Health check for API, DB, Redis |
