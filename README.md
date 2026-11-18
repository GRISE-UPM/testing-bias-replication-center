# Replication Center

Web portal for the UPM–ESPE project on replicating software engineering experiments. Architecture decisions, concepts and requirements are in [`docs/`](docs/).

## Structure
- `backend/`: Python API (FastAPI, SQLAlchemy; SQLite while developing, PostgreSQL later through `DATABASE_URL`).
- `frontend/`: Angular application.

## Run locally
Backend (http://localhost:8000):
```
cd backend
pip install -r requirements.txt
python -m app.seed        # loads SAMPLE data, not real project data
python -m uvicorn app.main:app --port 8000
python -m pytest          # tests
```
Frontend (http://localhost:4200, proxies `/api` to the backend):
```
cd frontend
npm install
npm start
npm test
```

## Implemented stories
- [#3](https://github.com/GRISE-UPM/testing-bias-replication-center/issues/3) Simplified dashboard on the landing page (`GET /api/stats`, no authentication).
