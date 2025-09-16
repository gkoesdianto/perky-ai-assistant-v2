# Phase 2: Single Agent Implementation Tasks (Day 1-2)

## Overview

Phase 2 focuses on implementing a single PydanticAI agent with tool calling for the MVP chat system.

## Task List with Dependencies

### 1. Query Analyzer Foundation (Priority: Critical)

**Dependencies**: None - Must be completed first
**Location**: `src/application/ports/` and `src/application/services/`

#### 1.1 Create Query Analyzer Port interface (QueryAnalyzerPort)

- [ ] Define protocol in `src/application/ports/query_analyzer_port.py`
- [ ] Include analyze method signature
- [ ] Define return type as QueryIntent

#### 1.2 Implement Query Analyzer Service

- [ ] Create `src/application/services/query_analyzer.py`
- [ ] Implement delegation to infrastructure port
- [ ] Add conversation context handling

### 2. Start Chat Session Use Case (Priority: High)

**Dependencies**: Query Analyzer Foundation
**Location**: `src/application/use_cases/start_chat_session.py`

#### 2.1 Implement StartChatSessionUseCaseImpl class

- [ ] Create class structure inheriting from interface
- [ ] Initialize with session_repository and redis_client
- [ ] Implement execute method

#### 2.2 Add Session Management Logic

- [ ] Check for existing sessions
- [ ] Create new Session entity
- [ ] Store in Redis with TTL
- [ ] Return SessionDTO

### 3. Process User Message Use Case (Priority: High)

**Dependencies**: Query Analyzer, Start Chat Session
**Location**: `src/application/use_cases/process_message.py`

#### 3.1 Create ProcessUserMessageUseCaseImpl class

- [ ] Initialize with chat_agent, product_service, conversation_repository
- [ ] Implement execute method signature

#### 3.2 Implement Conversation Management

- [ ] Get or create conversation
- [ ] Prepare conversation context
- [ ] Maintain message history (last 4 messages)

#### 3.3 Integrate Single PydanticAI Agent

- [ ] Create user message entity
- [ ] Call agent.run() with context
- [ ] Generate AI response message
- [ ] Save conversation state

### 4. Get Conversation Use Case (Priority: Medium)

**Dependencies**: Process User Message
**Location**: `src/application/use_cases/get_conversation.py`

#### 4.1 Implement GetConversationUseCaseImpl

- [ ] Create class with conversation_repository
- [ ] Implement execute method
- [ ] Handle missing conversations

#### 4.2 Add DTO Conversion

- [ ] Convert Message entities to MessageDTO
- [ ] Create ConversationDTO with messages
- [ ] Include metadata and timestamps

### 5. Chat Orchestrator Service (Priority: High)

**Dependencies**: All Use Cases
**Location**: `src/application/services/chat_orchestrator.py`

#### 5.1 Create ChatOrchestrator class

- [ ] Initialize with all three use cases
- [ ] Add logging configuration

#### 5.2 Implement Connection Handling

- [ ] handle_new_connection method
- [ ] Session initialization with metadata
- [ ] Error handling and logging

#### 5.3 Implement Message Processing

- [ ] handle_user_message method
- [ ] Process and return MessageDTO
- [ ] Indonesian error messages

#### 5.4 Add Conversation History Retrieval

- [ ] get_conversation_history method
- [ ] Handle missing conversations gracefully

### 6. Testing and Validation (Priority: High)

**Dependencies**: All implementations
**Location**: `tests/unit/application/`

#### 6.1 Unit Tests for Use Cases

- [ ] Test StartChatSessionUseCaseImpl
- [ ] Test ProcessUserMessageUseCaseImpl
- [ ] Test GetConversationUseCaseImpl

#### 6.2 Integration Testing

- [ ] Test ChatOrchestrator coordination
- [ ] Verify message flow
- [ ] Test error scenarios

## Implementation Order

```text
graph TD
    A[1. Query Analyzer Port & Service] --> B[2. Start Chat Session Use Case]
    B --> C[3. Process User Message Use Case]
    C --> D[4. Get Conversation Use Case]
    B --> E[5. Chat Orchestrator Service]
    C --> E
    D --> E
    E --> F[6. Testing & Validation]
```

## Time Estimates

| Task Group | Estimated Time | Priority |
|------------|---------------|----------|
| Query Analyzer Foundation | 1-2 hours | Critical |
| Start Chat Session Use Case | 2-3 hours | High |
| Process User Message Use Case | 3-4 hours | High |
| Get Conversation Use Case | 1-2 hours | Medium |
| Chat Orchestrator Service | 2-3 hours | High |
| Testing & Validation | 3-4 hours | High |
| **Total** | **12-18 hours** | - |

## Success Criteria

✅ All use cases implemented with proper interfaces
✅ Chat orchestrator coordinates all operations
✅ Error handling returns Indonesian messages
✅ Conversation context maintained properly
✅ Unit tests pass with >80% coverage
✅ Integration tests verify complete flow

## Notes

- Single agent architecture simplifies implementation
- Mock implementations can be used initially for dependencies
- Focus on core chat flow first, optimize later
- Indonesian language support is required for user-facing messages
