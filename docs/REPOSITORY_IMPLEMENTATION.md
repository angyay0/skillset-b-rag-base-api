# Repository Implementation Guide

## Overview

The repository pattern is fully implemented with abstract interfaces in the domain layer and concrete PostgreSQL implementations in the infrastructure layer. All methods are working with actual database data.

## Architecture

```
Domain Layer (Interfaces)
├── UserRepository (abstract)
└── ConversationRepository (abstract)
    └── MessageRepository (abstract)

Infrastructure Layer (Implementations)
├── PostgresUserRepository (concrete)
├── PostgresConversationRepository (concrete)
└── PostgresMessageRepository (concrete)
```

## User Repository

### Interface: `src/domain/repositories/user_repository.py`

Abstract base class defining the contract for user data access.

**Methods:**
- `create(user: User) -> User` - Create a new user
- `get_by_id(user_id: int) -> Optional[User]` - Get user by ID
- `get_by_phone(phone_number: str) -> Optional[User]` - Get user by phone
- `update(user: User) -> User` - Update user
- `delete(user_id: int) -> bool` - Delete user
- `list_all(limit: int, offset: int) -> List[User]` - List all users

### Implementation: `src/infrastructure/repositories/postgres_user_repository.py`

PostgreSQL implementation using SQLAlchemy ORM.

#### Create User

```python
def create(self, user: User) -> User:
    """Create a new user"""
    db_user = UserModel(
        phone_number=user.phone_number,
        name=user.name,
        language=user.language,
        validity_days=user.validity_days,
        is_active=user.is_active
    )
    self.db.add(db_user)
    self.db.commit()
    self.db.refresh(db_user)
    return self._to_entity(db_user)
```

**What it does:**
1. Creates a SQLAlchemy model instance from the domain entity
2. Adds it to the database session
3. Commits the transaction
4. Refreshes to get auto-generated fields (id, created_at)
5. Converts back to domain entity and returns

#### Get User by Phone

```python
def get_by_phone(self, phone_number: str) -> Optional[User]:
    """Get user by phone number"""
    db_user = self.db.query(UserModel).filter(
        UserModel.phone_number == phone_number
    ).first()
    return self._to_entity(db_user) if db_user else None
```

**What it does:**
1. Queries the database for user with matching phone number
2. Returns first match (phone numbers are unique)
3. Converts to domain entity if found, None otherwise

#### Update User

```python
def update(self, user: User) -> User:
    """Update user"""
    db_user = self.db.query(UserModel).filter(UserModel.id == user.id).first()
    if not db_user:
        raise ValueError(f"User with id {user.id} not found")
    
    db_user.phone_number = user.phone_number
    db_user.name = user.name
    db_user.language = user.language
    db_user.validity_days = user.validity_days
    db_user.is_active = user.is_active
    
    self.db.commit()
    self.db.refresh(db_user)
    return self._to_entity(db_user)
```

**What it does:**
1. Finds existing user by ID
2. Raises error if not found
3. Updates all fields
4. Commits changes
5. Returns updated entity

#### Delete User

```python
def delete(self, user_id: int) -> bool:
    """Delete user"""
    db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        return False
    
    self.db.delete(db_user)
    self.db.commit()
    return True
```

**What it does:**
1. Finds user by ID
2. Returns False if not found
3. Deletes from database
4. Returns True on success

#### List All Users

```python
def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
    """List all users"""
    db_users = self.db.query(UserModel).offset(offset).limit(limit).all()
    return [self._to_entity(db_user) for db_user in db_users]
```

**What it does:**
1. Queries all users with pagination
2. Converts each to domain entity
3. Returns list of entities

## Conversation Repository

### Interface: `src/domain/repositories/conversation_repository.py`

Abstract base class for conversation data access.

**Methods:**
- `create(conversation: Conversation) -> Conversation`
- `get_by_id(conversation_id: int) -> Optional[Conversation]`
- `get_by_user_and_channel(user_id: int, channel: str) -> Optional[Conversation]`
- `list_by_user(user_id: int, limit: int) -> List[Conversation]`
- `update(conversation: Conversation) -> Conversation`

### Implementation: `src/infrastructure/repositories/postgres_conversation_repository.py`

#### Get by User and Channel

```python
def get_by_user_and_channel(self, user_id: int, channel: str) -> Optional[Conversation]:
    """Get active conversation by user and channel"""
    db_conversation = self.db.query(ConversationModel).filter(
        ConversationModel.user_id == user_id,
        ConversationModel.channel == channel,
        ConversationModel.is_active == True
    ).first()
    return self._to_entity(db_conversation) if db_conversation else None
```

**What it does:**
1. Queries for active conversation matching user and channel
2. Ensures conversation is active
3. Returns first match or None

**Use case:** Find existing conversation when user sends a message

#### List by User

```python
def list_by_user(self, user_id: int, limit: int = 100) -> List[Conversation]:
    """List conversations by user"""
    db_conversations = self.db.query(ConversationModel).filter(
        ConversationModel.user_id == user_id
    ).order_by(ConversationModel.created_at.desc()).limit(limit).all()
    return [self._to_entity(conv) for conv in db_conversations]
```

**What it does:**
1. Queries all conversations for a user
2. Orders by creation date (newest first)
3. Limits results
4. Returns list of entities

## Message Repository

### Interface: `src/domain/repositories/conversation_repository.py`

Abstract base class for message data access.

**Methods:**
- `create(message: Message) -> Message`
- `get_by_id(message_id: int) -> Optional[Message]`
- `list_by_conversation(conversation_id: int, limit: int) -> List[Message]`
- `get_conversation_history(conversation_id: int, limit: int) -> List[Message]`

### Implementation: `src/infrastructure/repositories/postgres_conversation_repository.py`

#### Create Message

```python
def create(self, message: Message) -> Message:
    """Create a new message"""
    db_message = MessageModel(
        conversation_id=message.conversation_id,
        user_message=message.user_message,
        assistant_response=message.assistant_response,
        language=message.language,
        metadata=message.metadata
    )
    self.db.add(db_message)
    self.db.commit()
    self.db.refresh(db_message)
    return self._to_entity(db_message)
```

**What it does:**
1. Creates message record with all fields
2. Stores metadata as JSON
3. Saves to database
4. Returns created entity

#### Get Conversation History

```python
def get_conversation_history(self, conversation_id: int, limit: int = 10) -> List[Message]:
    """Get recent conversation history"""
    return self.list_by_conversation(conversation_id, limit)
```

**What it does:**
1. Retrieves recent messages for a conversation
2. Orders by creation date (newest first)
3. Limits to specified number
4. Used for providing context to AI

## Entity Conversion

All repositories use a `_to_entity()` method to convert database models to domain entities.

### Example: User Conversion

```python
@staticmethod
def _to_entity(db_user: UserModel) -> User:
    """Convert database model to entity"""
    return User(
        id=db_user.id,
        phone_number=db_user.phone_number,
        name=db_user.name,
        language=db_user.language,
        validity_days=db_user.validity_days,
        is_active=db_user.is_active,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )
```

**Why separate entities from models?**
- **Domain entities** are pure business objects with no database dependencies
- **Database models** are SQLAlchemy-specific with ORM features
- Conversion keeps domain layer independent of infrastructure

## Usage Examples

### Creating a User

```python
from src.infrastructure.database.connection import get_db
from src.infrastructure.repositories.postgres_user_repository import PostgresUserRepository
from src.domain.entities.user import User
from datetime import datetime

# Get database session
db = get_db()

# Create repository
user_repo = PostgresUserRepository(db)

# Create user entity
user = User(
    id=None,
    phone_number="+1234567890",
    name="John Doe",
    language="es",
    validity_days=30,
    is_active=True,
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)

# Save to database
created_user = user_repo.create(user)
print(f"Created user with ID: {created_user.id}")
```

### Finding and Updating a User

```python
# Find user by phone
user = user_repo.get_by_phone("+1234567890")

if user:
    # Update validity
    user.validity_days = 60
    updated_user = user_repo.update(user)
    print(f"Updated user validity to {updated_user.validity_days} days")
else:
    print("User not found")
```

### Getting Conversation History

```python
from src.infrastructure.repositories.postgres_conversation_repository import (
    PostgresConversationRepository,
    PostgresMessageRepository
)

# Create repositories
conversation_repo = PostgresConversationRepository(db)
message_repo = PostgresMessageRepository(db)

# Get active conversation
conversation = conversation_repo.get_by_user_and_channel(
    user_id=1,
    channel="whatsapp"
)

if conversation:
    # Get last 5 messages
    history = message_repo.get_conversation_history(
        conversation_id=conversation.id,
        limit=5
    )
    
    for msg in history:
        print(f"User: {msg.user_message}")
        print(f"Bot: {msg.assistant_response}")
```

## Database Session Management

### Context Manager (Recommended)

```python
from src.infrastructure.database.connection import get_db_context

with get_db_context() as db:
    user_repo = PostgresUserRepository(db)
    user = user_repo.get_by_phone("+1234567890")
    # Session automatically closed
```

### Manual Management

```python
from src.infrastructure.database.connection import get_db

db = get_db()
try:
    user_repo = PostgresUserRepository(db)
    user = user_repo.get_by_phone("+1234567890")
finally:
    db.close()
```

## Error Handling

### Not Found Errors

```python
try:
    user = user_repo.update(non_existent_user)
except ValueError as e:
    print(f"Error: {e}")  # "User with id X not found"
```

### Database Errors

```python
from sqlalchemy.exc import IntegrityError

try:
    user_repo.create(user_with_duplicate_phone)
except IntegrityError:
    print("Phone number already exists")
```

## Testing Repositories

### Unit Tests with Mocks

```python
from unittest.mock import Mock
from src.domain.repositories.user_repository import UserRepository

def test_chat_service():
    # Mock repository
    mock_repo = Mock(spec=UserRepository)
    mock_repo.get_by_phone.return_value = mock_user
    
    # Test service with mock
    service = ChatService(user_repo=mock_repo, ...)
    result = service.process_message(...)
```

### Integration Tests with Test Database

```python
import pytest
from src.infrastructure.database.connection import Base, engine

@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_user_repository(test_db):
    db = get_db()
    user_repo = PostgresUserRepository(db)
    
    # Test create
    user = user_repo.create(test_user)
    assert user.id is not None
    
    # Test get
    found = user_repo.get_by_id(user.id)
    assert found.phone_number == test_user.phone_number
```

## Performance Considerations

### Indexing

Database models have indexes on:
- `phone_number` (unique index for fast lookups)
- `user_id` (foreign key index)
- `conversation_id` (foreign key index)

### Query Optimization

```python
# Good: Single query with filter
user = user_repo.get_by_phone("+1234567890")

# Bad: Load all then filter in Python
all_users = user_repo.list_all(limit=10000)
user = [u for u in all_users if u.phone_number == "+1234567890"][0]
```

### Pagination

```python
# Get users in batches
page_size = 100
offset = 0

while True:
    users = user_repo.list_all(limit=page_size, offset=offset)
    if not users:
        break
    
    process_users(users)
    offset += page_size
```

## Summary

✅ **All repository methods are fully implemented and working with database data**

- **User Repository**: CRUD operations for users
- **Conversation Repository**: Manage conversations by user and channel
- **Message Repository**: Store and retrieve message history

The repositories provide a clean abstraction over the database, allowing the application layer to work with domain entities without knowing about SQLAlchemy or PostgreSQL specifics.
