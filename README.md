# Sistema de Gestión de Socios

Sistema integral para gestión de socios.

## 🚀 Tecnologías

### Backend
- Python 3.11+
- FastAPI
- PostgreSQL 15
- Redis 7
- SQLAlchemy + Alembic

### Frontend Desktop
- Python 3.11+
- Flet (Flutter-based)

### App Móvil
- React Native
- Expo

## 📦 Instalación

### 1. Clonar repositorio
```bash
git clone <repo-url>
cd sistema-gestion-socios
```

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
# Editar .env con tus configuraciones
```

### 3. Base de datos (Docker)
```bash
docker-compose up -d postgres redis
```

### 4. Migraciones
```bash
cd backend
alembic upgrade head
```

### 5. Iniciar backend
```bash
cd backend
uvicorn app.main:app --reload
```

### 6. Frontend Desktop
```bash
cd frontend-desktop
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
# Windows Git Bash
PYTHONPATH=. python src/main.py
# O en Windows CMD/PowerShell
set PYTHONPATH=.
python```

### 7. App Móvil
```bash
cd mobile-app
npm install
npx expo start
```

## 📚 Documentación

Ver carpeta `docs/` para más detalles.

## 🔧 Desarrollo

- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## 📝 Licencia

MIT License
