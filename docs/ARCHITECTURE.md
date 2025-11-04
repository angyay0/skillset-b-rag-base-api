# Architecture Documentation

## Clean Architecture Overview

This project follows **Clean Architecture** principles with clear separation of concerns across multiple layers.

## Project Structure

```
blinky-base-api/
├── src/
│   ├── domain/              # Business logic and entities
│   │   ├── entities/        # Domain entities (User, Conversation, Message)
│   │   └── repositories/    # Repository interfaces
│   ├── application/         # Application services
│   │   └── services/        # Business logic services
│   ├── infrastructure/      # External dependencies
│   │   ├── database/        # Database models and connection
│   │   ├── repositories/    # Repository implementations
│   │   └── ai/             # AI service integration
│   ├── presentation/        # API layer
│   │   ├── controllers/     # Request handlers
│   │   └── routes.py        # Route definitions
│   └── config/             # Configuration and DI
├── alembic/                # Database migrations
├── app_new.py              # Application entry point
├── app.py                  # Legacy monolithic app (deprecated)
└── requirements.txt        # Dependencies
```

## Layers

### 1. Domain Layer (`src/domain/`)
- **Entities**: Core business objects (User, Conversation, Message)
- **Repository Interfaces**: Abstract definitions for data access
- **No dependencies** on other layers
- Pure business logic

### 2. Application Layer (`src/application/`)
- **Services**: Orchestrate business logic
- **Use Cases**: Implement application-specific operations
- Depends only on domain layer
- Example: `ChatService` handles message processing

### 3. Infrastructure Layer (`src/infrastructure/`)
- **Database**: SQLAlchemy models and connection management
- **Repositories**: Concrete implementations of repository interfaces
- **External Services**: Vertex AI, WhatsApp API, Twilio
- Implements interfaces defined in domain layer

### 4. Presentation Layer (`src/presentation/`)
- **Controllers**: Handle HTTP requests/responses
- **Routes**: Define API endpoints
- Thin layer that delegates to application services
- Framework-specific code (Flask)

## Key Design Patterns

### Dependency Injection
- Dependencies are injected through constructors
- `src/config/dependencies.py` manages object creation
- Enables easy testing and swapping implementations

### Repository Pattern
- Abstract data access behind interfaces
- Easy to switch between different storage backends
- Testable with mock repositories

### Service Layer
- Business logic separated from controllers
- Reusable across different interfaces (REST, GraphQL, CLI)
- Single responsibility principle

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100),
    language VARCHAR(10) DEFAULT 'es',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Conversations Table
```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Messages Table
```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    language VARCHAR(10) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Data Flow

1. **Request arrives** at controller (presentation layer)
2. **Controller** extracts data and calls service (application layer)
3. **Service** uses repositories to fetch/store data (infrastructure layer)
4. **Service** calls AI service for response generation
5. **Service** returns result to controller
6. **Controller** formats and returns HTTP response

## Benefits of This Architecture

### Testability
- Each layer can be tested independently
- Mock implementations for testing
- No framework coupling in business logic

### Maintainability
- Clear separation of concerns
- Easy to locate and modify code
- Changes in one layer don't affect others

### Scalability
- Easy to add new features
- Can swap implementations (e.g., different databases)
- Multiple interfaces can use same business logic

### Flexibility
- Database-agnostic domain layer
- Framework-agnostic business logic
- Easy to migrate to different technologies

## Migration from Monolithic App

The original `app.py` has been refactored into:
- **Domain entities**: User, Conversation, Message
- **Repositories**: PostgresUserRepository, PostgresConversationRepository
- **Services**: ChatService
- **Controllers**: WhatsAppController, VoiceController
- **Routes**: Centralized in `routes.py`

## Running Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Adding New Features

1. **Add entity** in `src/domain/entities/` if needed
2. **Define repository interface** in `src/domain/repositories/`
3. **Implement repository** in `src/infrastructure/repositories/`
4. **Create service** in `src/application/services/`
5. **Add controller** in `src/presentation/controllers/`
6. **Register routes** in `src/presentation/routes.py`

## Testing Strategy

- **Unit tests**: Test services with mock repositories
- **Integration tests**: Test repositories with test database
- **E2E tests**: Test controllers with real dependencies
- **Fixtures**: Use dependency injection for test doubles
