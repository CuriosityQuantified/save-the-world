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

| Service | File Location | Description |
|---------|---------------|-------------|
| LLM Service | `services/llm_service.py` | Central service for all LLM interactions, including scenario generation, selection, video prompts, and narration scripts |
| Media Services | To be implemented | Will handle RunwayML and ElevenLabs API integrations |
| API Service | To be implemented | Will provide REST endpoints for the frontend |

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
├── services/
│   └── llm_service.py           # LLM interaction service
├── tests/
│   └── test_scenario_generation.py  # Test for scenario generation
├── scenario_generation_prompt.py    # Prompt templates for scenario generation
├── build-plan.md                # Phased build plan with progress
├── flow.md                      # Core simulation flow documentation
└── project_structure.md         # This file
```

## Future Structure (Planned)

As we progress, the following structure will evolve:

```
sim-local/
├── api/                         # API server implementation
│   ├── routes/                  # API endpoints
│   └── models/                  # Data models
├── services/                    # Service layer
│   ├── llm_service.py           # LLM service
│   ├── media_service.py         # Media generation (RunwayML/ElevenLabs)
│   └── state_service.py         # State management
├── frontend/                    # Web UI components
├── prompts/                     # All prompt templates
├── tests/                       # Test suite
└── docs/                        # Documentation
``` 