---
description: Repository Information Overview
alwaysApply: true
---

# mkit-idv Repository Information

## Summary
This repository contains a FastAPI-based backend service for voucher management, featuring a robust authentication flow with JWT access tokens and opaque refresh tokens. It uses SQLAlchemy 2.0 with Alembic for database migrations and Pydantic V2 for settings and validation.

## Structure
- **[./backend](./backend)**: The main Python application, containing the FastAPI app, database models, migrations, and tests.
- **[./frontend](./frontend)**: Placeholder for the frontend application (currently empty).
- **[./plans](./plans)**: Project documentation and detailed implementation plans (e.g., auth refactoring, JWT implementation).
- **[./application.dbml](./application.dbml)**: Database schema design in DBML format.

## Language & Runtime
**Language**: Python  
**Version**: 3.13+  
**Build System**: `pyproject.toml`  
**Package Manager**: `pip` / `uv`

## Dependencies
**Main Dependencies**:
- `fastapi`: Web framework
- `sqlalchemy`: SQL Toolkit and ORM
- `alembic`: Database migrations
- `pydantic`: Data validation
- `pydantic-settings`: Settings management
- `pyjwt`: JWT token handling
- `pwdlib[argon2]`: Password hashing
- `fastapi-limiter`: Rate limiting

**Development Dependencies**:
- `pytest`: Testing framework
- `pytest-asyncio`: Async support for pytest
- `pytest-cov`: Coverage reporting
- `ruff`: Linting and formatting

## Build & Installation
```bash
# Navigate to backend directory
cd backend

# Install dependencies using pip
pip install .

# Or using uv (recommended if available)
uv sync
```

## Main Files & Resources
- **[./backend/app/main.py](./backend/app/main.py)**: Application entry point.
- **[./backend/app/core/settings.py](./backend/app/core/settings.py)**: Configuration and environment variable management.
- **[./backend/alembic.ini](./backend/alembic.ini)**: Alembic migration configuration.
- **[./backend/app/models/](./backend/app/models/)**: SQLAlchemy database models (Users, Sessions, Orders, etc.).

## Testing

**Framework**: `pytest`
**Test Location**: `backend/tests/`
**Naming Convention**: `test_*.py`
**Configuration**: `backend/pyproject.toml` ([tool.pytest.ini_options])

**Run Command**:
```bash
cd backend
pytest
```
