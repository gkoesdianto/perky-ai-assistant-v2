# Docker Development Environment Setup

## Prerequisites

- Docker Desktop installed and running
- Docker Compose (included with Docker Desktop)

## Quick Start

1. **Start Docker Desktop**
   - On macOS: Open Docker Desktop from Applications
   - Ensure Docker daemon is running (Docker icon in menu bar)

2. **Build and start services**
   ```bash
   docker-compose up --build
   ```

3. **Access services**
   - FastAPI app: <http://localhost:8000>
   - API Documentation: <http://localhost:8000/docs>
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379
   - pgAdmin: <http://localhost:5050> (<admin@perky.com> / admin)

## Common Commands

### Start services

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Rebuild and start
docker-compose up --build
```

### Stop services

```bash
# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove with volumes (clean slate)
docker-compose down -v
```

### View logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f postgres
```

### Access containers

```bash
# Execute commands in running container
docker-compose exec app bash
docker-compose exec postgres psql -U perky_user -d perky_db
docker-compose exec redis redis-cli
```

### Database operations

```bash
# Run migrations
docker-compose exec app alembic upgrade head

# Create new migration
docker-compose exec app alembic revision --autogenerate -m "Description"

# Check migration history
docker-compose exec app alembic history
```

## Development Workflow

1. Code changes in `src/` are automatically reloaded (hot reload enabled)
2. Database data persists in Docker volumes
3. Use pgAdmin at <http://localhost:5050> for database management

## Troubleshooting

### Docker daemon not running

- Start Docker Desktop application
- Wait for Docker icon to indicate it's running
- Verify with: `docker info`

### Port conflicts

- Check if ports are already in use: `lsof -i :8000`
- Stop conflicting services or change ports in docker-compose.yml

### Permission issues

- Ensure current user has Docker permissions
- On Linux: Add user to docker group: `sudo usermod -aG docker $USER`

### Clean restart

```bash
# Remove all containers and volumes
docker-compose down -v

# Rebuild from scratch
docker-compose build --no-cache

# Start fresh
docker-compose up
```

## Environment Variables

- Development settings are in `.env` file
- Copy `.env.example` to `.env` and adjust as needed
- Docker Compose automatically loads `.env` file
