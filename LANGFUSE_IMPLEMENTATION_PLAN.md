# Langfuse Integration Implementation Plan (Phases 1-3)

## Overview
We'll implement Langfuse monitoring for the Save The World simulation system with maximum visibility for LLM inputs/outputs. Langfuse will run on **localhost:3005** and all observability components will be organized under an `observability` folder.

## 📋 Implementation Status

### Phase 1: Core LLM Observability ✅ COMPLETE
- [x] Step 1.1: Deploy Langfuse Locally (Port 3005) ✅
- [x] Step 1.2: Install Dependencies ✅
- [x] Step 1.3: Create Langfuse Helper Module ✅
- [x] Step 1.4: Integrate with LLMService ✅
- [x] Step 1.5: Add Environment Configuration ✅
- [x] Step 1.6: Add tracing to create_idea and create_video_prompt methods ✅
- [x] Step 1.7: Fix session initialization in SimulationService ✅
- [x] Step 1.8: Add session persistence and flush on completion ✅

### Phase 2: Media Service Tracking
- [ ] Step 2.1: Instrument Video Generation
- [ ] Step 2.2: Instrument Audio Generation
- [ ] Step 2.3: Add Cost Tracking
- [ ] Step 2.4: Monitor Media Success Rates

### Phase 3: Full Simulation Flow
- [ ] Step 3.1: Session-Based Tracing
- [ ] Step 3.2: Link Multi-Turn Conversations
- [ ] Step 3.3: User Identification & Grading
- [ ] Step 3.4: FastAPI Integration

---

## 🚀 Phase 1: Core LLM Observability (Days 1-2)

### Step 1.1: Deploy Langfuse v3 Locally (Port 3005)
**Status**: 🚧 In Progress

- **Create** `observability/langfuse/docker-compose.yml` with: ✅
  - Langfuse Web UI on port **3005**
  - Langfuse Worker for background processing
  - PostgreSQL on port 5433 (metadata storage)
  - ClickHouse on ports 8123/9000 (analytics data)
  - Redis on port 6379 (queue and cache)
  - MinIO on ports 9002/9001 (S3-compatible object storage)
- **Launch** Langfuse v3 stack via Docker Compose
- **Configure** initial project "save-the-world" and generate API keys

**Architecture Note**: Langfuse v3 uses a distributed architecture with ClickHouse for handling billions of events efficiently, Redis for asynchronous processing, and MinIO for object storage.

### Step 1.2: Install Dependencies
**Status**: ⏳ Not Started

- **Add to** `requirements.txt`:
  - `langfuse==2.59.1`
- **Install** via: `source venv/bin/activate && pip install langfuse`

### Step 1.3: Create Langfuse Helper Module
**Status**: ⏳ Not Started

- **Create** `observability/langfuse/langfuse_service.py` with:
  - VisibilityOptimizedLangfuse class
  - Session management
  - Flat Generation-based tracing (not nested spans)
  - Helper methods for quality scoring

### Step 1.4: Integrate with LLMService
**Status**: ⏳ Not Started

- **Update** `services/llm_service.py`:
  - Import from `observability.langfuse.langfuse_service`
  - Add Langfuse client initialization
  - Wrap `create_idea()` with Generation traces:
    - Name: "Turn X: Idea Generation - [Scenario Title]"
    - Input/output in ChatML format for beautiful rendering
    - Metadata with turn_number, business_context
    - Quality scoring visible immediately
  - Wrap `create_scenario()` with Generation traces:
    - Name: "Turn X: Scenario Design - [Situation Summary]"
    - Full prompt/response visibility
    - Complexity scoring

### Step 1.5: Add Environment Configuration
**Status**: ⏳ Not Started

- **Update** `.env` file with:
  ```
  LANGFUSE_PUBLIC_KEY=your_public_key
  LANGFUSE_SECRET_KEY=your_secret_key
  LANGFUSE_HOST=http://localhost:3005
  ```

---

## 🎬 Phase 2: Media Service Tracking (Days 3-4)

### Step 2.1: Instrument Video Generation
**Status**: ⏳ Not Started

- **Update** `services/media_service.py`:
  - Import from `observability.langfuse.langfuse_service`
  - Add `generate_video()` tracing:
    - Name: "Turn X: Video Generation - [Content Description]"
    - Track HuggingFace API calls
    - Include generation time, resolution, format
    - Speed scoring (Excellent < 20s, Good < 40s, etc.)
  - Handle both success and error cases with descriptive traces

### Step 2.2: Instrument Audio Generation
**Status**: ⏳ Not Started

- **Update** `services/media_service.py`:
  - Add `generate_audio()` tracing:
    - Name: "Turn X: Audio Generation - [Content Description]"
    - Track Groq TTS API calls
    - Include duration, voice model, quality settings
    - Speed and quality scoring

### Step 2.3: Add Cost Tracking
**Status**: ⏳ Not Started

- **Enhance** media traces with:
  - API cost calculations for HuggingFace
  - Token usage for Groq TTS
  - Cumulative cost tracking per session
  - Resource usage metadata

### Step 2.4: Monitor Media Success Rates
**Status**: ⏳ Not Started

- **Implement** scoring system:
  - Track generation success/failure rates
  - Monitor retry attempts
  - Log fallback strategies (mocked responses)
  - Quality assessment scores

---

## 🔄 Phase 3: Full Simulation Flow (Days 5-7)

### Step 3.1: Session-Based Tracing
**Status**: ⏳ Not Started

- **Update** `services/simulation_service.py`:
  - Import from `observability.langfuse.langfuse_service`
  - Create session on `create_new_simulation()`:
    - Session ID: `simulation_{timestamp}`
    - Session name includes user objective
  - Pass session_id through all service calls
  - Maintain session context across all 3 turns

### Step 3.2: Link Multi-Turn Conversations
**Status**: ⏳ Not Started

- **Implement** turn linking:
  - Each turn's traces share the same session_id
  - Descriptive naming: "Turn 1/2/3" prefix
  - Include previous turn context in metadata
  - Track conversation flow and decision progression

### Step 3.3: User Identification & Grading
**Status**: ⏳ Not Started

- **Add** user tracking:
  - Include user_id in session metadata (if available)
  - Track user response times
  - Monitor interaction patterns
- **Implement** conclusion tracing:
  - Name: "Final Grading - [Grade Score]"
  - Include grading criteria and rationale
  - Track overall simulation performance
  - Quality metrics summary

### Step 3.4: FastAPI Integration
**Status**: ⏳ Not Started

- **Update** `api/app.py`:
  - Import from `observability.langfuse.langfuse_service`
  - Add Langfuse middleware for request tracking
  - Create trace context for each API endpoint
  - Link WebSocket events to sessions
  - Handle graceful shutdown with trace flushing

---

## 📁 Directory Structure

```
save-the-world/
├── observability/                    # All observability tools
│   ├── __init__.py
│   └── langfuse/                    # Langfuse-specific files
│       ├── __init__.py
│       ├── docker-compose.yml       # Langfuse deployment config
│       └── langfuse_service.py      # Langfuse helper module
├── services/
│   ├── llm_service.py               # Update with tracing
│   ├── media_service.py             # Update with tracing
│   └── simulation_service.py        # Update with session management
├── api/
│   └── app.py                       # Update with middleware
├── requirements.txt                  # Add langfuse dependency
└── .env                             # Add Langfuse credentials
```

---

## 📊 Key Implementation Principles

### Visibility-First Design
- **Flat structure**: All LLM/media calls as top-level Generations
- **Descriptive names**: Include content in trace names
- **One-click access**: Inputs/outputs visible immediately
- **No nested spans**: Avoid deep hierarchies

### Trace Naming Convention
```
"Turn {number}: {Operation} - {Content Description}"
Examples:
- "Turn 1: Idea Generation - Crisis Management Scenario"
- "Turn 2: Video Generation - Supply Chain Recovery"
- "Turn 3: Audio Generation - Success Celebration"
- "Final Grading - Business Impact Score: 85/100"
```

### Metadata Structure
```python
{
    "turn_number": 1-3,
    "operation_type": "idea_generation|scenario_design|video_generation|audio_generation",
    "scenario_description": "Brief content summary",
    "business_context": "User's business context",
    "quality_score": 0.0-1.0,
    "generation_time_seconds": float,
    "timestamp": ISO-8601
}
```

---

## 🧪 Testing Strategy

1. **Unit Tests**: Test Langfuse integration in isolation
2. **Integration Tests**: Verify end-to-end trace flow
3. **Manual Verification**: Check Langfuse UI at localhost:3005
4. **Performance Tests**: Ensure minimal overhead (<100ms)

---

## 📈 Success Metrics

- [ ] All LLM calls visible with one click in Langfuse UI
- [ ] Complete 3-turn simulation traceable in single session
- [ ] Media generation performance clearly tracked
- [ ] Error cases properly logged with context
- [ ] Quality scores visible at trace level
- [ ] No performance degradation (< 5% overhead)

---

## 🔧 Files to Create/Modify

### Create New Files:
1. [ ] `observability/__init__.py` (empty init file)
2. [ ] `observability/langfuse/__init__.py` (empty init file)
3. [ ] `observability/langfuse/docker-compose.yml` (Langfuse deployment)
4. [ ] `observability/langfuse/langfuse_service.py` (helper module)

### Update Existing Files:
1. [ ] `requirements.txt` (add langfuse==2.59.1)
2. [ ] `.env` (add Langfuse credentials)
3. [ ] `services/llm_service.py` (add tracing)
4. [ ] `services/media_service.py` (add tracing)
5. [ ] `services/simulation_service.py` (session management)
6. [ ] `api/app.py` (middleware & lifecycle)

---

## 🚀 Launch Commands

```bash
# 1. Start Langfuse
cd observability/langfuse
docker-compose up -d

# 2. Install Python dependencies
source venv/bin/activate
pip install -r requirements.txt

# 3. Restart the backend to pick up changes
# (Backend is already running on port 8000)
```

---

## 📝 Implementation Notes

### Progress Log
- **2025-09-07**: Created implementation plan with observability folder structure
- **2025-09-07**: Adjusted Langfuse port from 3001 to 3005
- **2025-09-07**: Phase 1 Implementation Progress:
  - ✅ Created `observability/langfuse/` folder structure with __init__ files
  - ✅ Created Docker Compose configuration for Langfuse on port 3005
  - ✅ Installed langfuse==2.59.1 Python SDK
  - ✅ Created `langfuse_service.py` with VisibilityOptimizedLangfuse class
  - ✅ Added Langfuse environment variables to .env file
  - ✅ Imported Langfuse into LLMService
  - ✅ Added Langfuse initialization and session management methods to LLMService
  - 🚧 Next: Add tracing to create_idea and create_video_prompt methods
- **2025-09-07**: Upgraded to Langfuse v3 Architecture:
  - ✅ Researched Langfuse v3 with ClickHouse requirements
  - ✅ Updated Docker Compose with full v3 stack (ClickHouse, Redis, MinIO)
  - ✅ Configured all 6 services for distributed architecture
  - ✅ Fixed worker startup issues (added LANGFUSE_S3_EVENT_UPLOAD_BUCKET)
  - ✅ Successfully launched complete Langfuse v3 stack on port 3005
  - ✅ All services healthy and running (web, worker, postgres, clickhouse, redis, minio)
- **2025-09-07**: Completed Phase 1 - Core LLM Observability:
  - ✅ User added API keys to .env file
  - ✅ Added start_langfuse_session method to LLMService
  - ✅ Instrumented create_idea method with Langfuse tracing
  - ✅ Instrumented create_video_prompt method with Langfuse tracing
  - ✅ Fixed import errors in langfuse_service.py
  - ✅ Backend running successfully with Langfuse integration on port 8001
- **2025-09-07**: Fixed Phase 1 - Session Initialization Issue:
  - ✅ Identified root cause: LLMService.current_session_id was always None
  - ✅ Added start_langfuse_session() call in SimulationService.create_new_simulation()
  - ✅ Added session persistence check in process_user_response()
  - ✅ Added flush() call on simulation completion for reliable trace delivery
  - ✅ Phase 1 now fully operational with proper session-based tracing

### Key Decisions
1. Using `observability/` folder for better organization and future expansion
2. Langfuse service module placed within langfuse subfolder for clarity
3. Port 3005 chosen to avoid conflicts with other local services
4. Flat Generation structure prioritized for maximum visibility
5. **Langfuse v3 chosen over v2** for scalability and performance:
   - ClickHouse enables handling billions of events efficiently
   - Asynchronous processing via Redis improves reliability
   - MinIO provides scalable object storage for exports
   - Distributed architecture supports production-scale deployments

### Langfuse v3 Service Ports
- **3005**: Langfuse Web UI (main interface)
- **5433**: PostgreSQL (metadata storage)
- **8123**: ClickHouse HTTP interface (analytics queries)
- **9000**: ClickHouse Native protocol (migrations)
- **6379**: Redis (queue and cache)
- **9002**: MinIO API (object storage)
- **9001**: MinIO Console (storage management)

### Risks & Mitigations
- **Risk**: Performance overhead from tracing
  - **Mitigation**: Async tracing, batch flushing, <100ms target
- **Risk**: Large trace volumes overwhelming UI
  - **Mitigation**: Descriptive naming, proper tagging, session grouping
- **Risk**: Sensitive data in traces
  - **Mitigation**: Careful data selection, PII filtering

---

## 🔄 Next Steps

1. Begin Phase 1 implementation
2. Test each component before moving to next phase
3. Update this document with progress and learnings
4. Gather feedback after each phase completion

This plan prioritizes maximum visibility of model inputs/outputs with minimal UI navigation required, using the `observability` folder structure for better organization.