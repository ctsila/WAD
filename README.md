# WAD-HW1

This repository contains the completed **first homework** for Web Application Development.

## What this homework is about
HW1 is an **LLM Chat Application** with:
- React frontend
- FastAPI backend
- PostgreSQL database
- Redis-based refresh-token authentication
- Chat/message APIs with LLM response support

## How to run the application (from `project` folder)
1. From the repository root, open a terminal and move to the project folder:
   - `cd project`
2. Create environment file:
   - `cp .env.example .env`
3. Start infrastructure services:
   - `docker compose up -d`
4. Install backend dependencies:
   - `pip install -r requirements.txt`
5. Apply database migrations:
   - `alembic upgrade head`
6. Put `model.gguf` into the `project` folder.
7. Start backend server:
   - `uvicorn app.main:app --reload`
8. In another terminal (also from the `project` directory), start frontend:
   - `cd frontend`
   - `npm install`
   - `npm run dev`
