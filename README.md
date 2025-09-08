# Perky AI Assistant V2

A FastAPI-based application built with Domain-Driven Design (DDD) architecture.

## Project Structure

```text
perky-ai-assistant-v2/
├── src/
│   ├── domain/           # Core business logic and entities
│   ├── application/      # Application services and use cases
│   ├── infrastructure/   # External services, database, cache
│   ├── presentation/     # API endpoints and schemas
│   └── core/            # Configuration and shared utilities
├── tests/               # Test files
├── migrations/          # Database migrations
├── requirements/        # Dependency files
└── scripts/            # Utility scripts
```

## Prerequisites

- Python 3.11+
- PostgreSQL (for database)
- Redis (for caching)

## Installation

1. **Activate virtual environment** (if not already active):
   ```bash
   # The virtual environment 'perky-ai-assistant-v2' should already be created
   # If you need to activate it:
   source ~/.virtualenvs/perky-ai-assistant-v2/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements/dev.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Running the Application

**Start the development server**:

```bash
python -m uvicorn src.main:app --reload
```

The API will be available at:

- **API**: <http://localhost:8000>
- **Documentation**: <http://localhost:8000/docs>
- **Health Check**: <http://localhost:8000/health>
- **Ready Check**: <http://localhost:8000/ready>

## Development

### Code Quality Tools

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing

### Running Tests

```bash
pytest
```

### Running Linters

```bash
black src/
isort src/
flake8 src/
mypy src/
```

## API Endpoints

### Health Check

- `GET /health` - Application health status
- `GET /ready` - Application readiness status (includes database and cache checks)

## Next Steps

1. **Docker Setup**: Configure Docker and Docker Compose for containerized development
2. **Database Models**: Create SQLAlchemy models and Alembic migrations
3. **Domain Entities**: Implement core domain entities and value objects
4. **API Endpoints**: Add CRUD endpoints for business entities
5. **Authentication**: Implement JWT-based authentication
6. **Testing**: Add unit and integration tests
7. **CI/CD**: Setup continuous integration and deployment

## License

[License Type]

## Contributing

[Contributing Guidelines]
