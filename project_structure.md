# Interactive Simulation System - Project Structure

This document provides an overview of the project's structure, key components, and where to find important files.

## Core Components

### Prompt Templates

| Component | File Location | Description |
|-----------|---------------|-------------|
| Scenario Generation Prompt | `prompts/scenario_generation_prompt.py` | Contains templates for generating absurd crisis scenarios including `CREATE_IDEA_PROMPT_TEMPLATE`, `INITIAL_CRISIS_EXAMPLES_JSON`, and `FOLLOW_UP_CRISIS_EXAMPLE_JSON` |
| Scenario Selection Prompt | Inside `services/llm_service.py` | Part of the `critique_idea` method, selects the best scenario from multiple options |
| Video Generation Prompt | Inside `services/llm_service.py` | Part of the `create_video_prompt` method, converts scenario descriptions to video generation prompts |
| Narration Script Prompt | Inside `services/llm_service.py` | Part of the `create_narration_script` method, generates narration scripts from scenarios |

### Services

| Service | Status | Description |
|---------|--------|-------------|
| LLM Service | Implemented | Manages LLM API calls using Groq or Google Gemini |
| Media Services | Implemented | Handles HuggingFace API integrations for video and audio |
| State Service | Implemented | Manages state across simulation turns |
| Simulation Service | Implemented | Orchestrates the simulation flow |

### Testing

| Component | File Location | Description |
|-----------|---------------|-------------|
| Scenario Generation Test | `tests/test_scenario_generation.py` | Tests the scenario generation workflow through multiple turns |

### Documentation

| Document | File Location | Description |
|----------|---------------|-------------|
| Build Plan | `build-plan.md` | Detailed phased development approach with progress tracking |
| Flow Description | `flow.md` | Documentation of the core simulation flow |
| Project Structure | `project_structure.md` | This file - overview of key components and locations |

## Implementation Progress

The project is following a phased implementation approach as outlined in `build-plan.md`. Current progress:

- Completed core LLM service for scenario generation
- Implemented and tested scenario generation flow
- Structured prompt templates for generating high-quality absurd scenarios
- Created testing framework for validating the simulation loop

## To Be Implemented

- Scenario selection (critique) implementation
- Video and audio generation services 
- REST API and webhooks
- Frontend UI
- State management
- Media storage integration

## Directory Structure

```
sim-local/
│
├── agents/                     # GADK integration
│   ├── creative_director_agent.py   # Scenario generation/selection agent
│   ├── video_agent.py          # Video generation agent
│   └── narration_agent.py      # Audio generation agent
│
├── api/                        # FastAPI implementation
│   ├── app.py                  # Main FastAPI application
│   ├── router.py               # API routes and handlers
│   └── config.py               # API configuration
│
├── services/                   # Core services
│   ├── llm_service.py          # LLM API client
│   ├── media_service.py         # Media generation (HuggingFace video/audio)
│   ├── huggingface_service.py  # HuggingFace video generation
│   ├── huggingface_tts_service.py # HuggingFace TTS audio generation
│   ├── state_service.py        # State management
│   ├── simulation_service.py   # Simulation orchestration
│   └── cloudflare_r2_service.py # Media storage
│
├── models/                     # Data models
│   ├── scenario.py             # Scenario model
│   ├── user_input.py           # User input model
│   └── simulation_state.py     # Simulation state model
│
├── prompts/                    # LLM prompt templates
│   ├── scenario_generation.py  # Templates for scenario generation
│   ├── scenario_selection.py   # Templates for selecting best scenario
│   ├── video_prompt.py         # Templates for video prompts
│   └── narration_script.py     # Templates for narration scripts
│
├── schemas/                    # API schemas
│   ├── scenario.py             # API scenario schema
│   ├── user_input.py           # API user input schema
│   └── simulation.py           # API simulation schema
│
├── utils/                      # Utility functions
│   ├── media.py                # Media file helpers
│   ├── logging.py              # Logging configuration
│   └── json.py                 # JSON helpers
│
├── scripts/                    # Utility scripts
│   ├── test_llm.py             # Test LLM API integration
│   └── prd.txt                 # Product Requirements Document
│
├── tests/                      # Tests
│   ├── unit/                   # Unit tests
│   │   ├── test_llm_service.py # Test LLM service
│   │   └── test_state_service.py # Test state service
│   ├── integration/            # Integration tests
│   │   ├── test_simulation.py  # Test end-to-end simulation
│   │   └── test_media_service.py # Test media generation
│   └── conftest.py             # Test configuration
│
├── ui/                         # Web UI
│   ├── index.html              # Main HTML page
│   ├── styles.css              # CSS styles
│   └── script.js               # Frontend JavaScript
│
├── media/                      # Media storage
│   ├── videos/                 # Generated videos
│   └── audio/                  # Generated audio files
│
├── .env                        # Environment variables
├── .env.example                # Example environment variables
├── README.md                   # Project documentation
└── requirements.txt            # Python dependencies
```

## Data Flow

1. User initiates simulation request
2. `SimulationService` orchestrates 5-turn flow
3. At each turn:
   - `LLMService` generates scenario options
   - `LLMService` selects best scenario
   - `MediaService` generates video via HuggingFace
   - `MediaService` generates audio via HuggingFace
   - Results presented to user
   - User response captured and added to context
4. Process repeats for 5 turns

## Key Components

### LLM Service
- Handles interactions with Groq and Google Gemini
- Manages prompt templates and context building
- Provides methods for different LLM tasks

### Media Service
- Coordinates video generation using HuggingFace fal-ai
- Coordinates audio generation using HuggingFace Dia-TTS
- Handles media storage and retrieval

### Simulation Service
- Manages overall simulation logic
- Coordinates between LLM and Media services
- Builds and maintains simulation state
- Enforces 5-turn structure

### State Service
- Manages simulation state persistence
- Handles session management
- Provides retrieval methods for active simulations

## Future Structure (Planned)

As we progress, the following structure will evolve:

```
sim-local/
├── api/                         # API server implementation
│   ├── routes/                  # API endpoints
│   └── models/                  # Data models
├── services/                    # Service layer
│   ├── llm_service.py           # LLM service
│   ├── media_service.py         # Media generation (HuggingFace video/audio)
│   └── state_service.py         # State management
├── frontend/                    # Web UI components
├── prompts/                     # All prompt templates
├── tests/                       # Test suite
└── docs/                        # Documentation
``` 