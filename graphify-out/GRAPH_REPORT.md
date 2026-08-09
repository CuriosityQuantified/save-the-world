# Graph Report - .  (2026-08-08)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1014 nodes · 1743 edges · 78 communities (69 shown, 9 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 131 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `459f24cb`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 44
- Community 45
- Community 46
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 57

## God Nodes (most connected - your core abstractions)
1. `SimulationState` - 67 edges
2. `LLMService` - 46 edges
3. `SimulationService` - 40 edges
4. `StateService` - 31 edges
5. `CloudflareR2Service` - 29 edges
6. `LeaderboardService` - 29 edges
7. `_make_client()` - 28 edges
8. `_mock_sim_service()` - 27 edges
9. `_lb_service()` - 27 edges
10. `SimulationRequest` - 24 edges

## Surprising Connections (you probably didn't know these)
- `CreativeDirectorAgent` --uses--> `LLMService`  [INFERRED]
  agents/creative_director.py → services/llm_service.py
- `VideoAgent` --uses--> `HuggingFaceService`  [INFERRED]
  agents/video_agent.py → services/huggingface_service.py
- `VideoAgent` --uses--> `LLMService`  [INFERRED]
  agents/video_agent.py → services/llm_service.py
- `TestVideoGeneration` --uses--> `VideoAgent`  [INFERRED]
  tests/integration/test_video_generation.py → agents/video_agent.py
- `TestGetLeaderboard` --uses--> `TimePeriod`  [INFERRED]
  tests/unit/test_leaderboard_routes.py → models/leaderboard.py

## Import Cycles
- None detected.

## Communities (78 total, 9 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (34): ABC, BaseAgent, Any, Base Agent Module This module defines the BaseAgent class that all specific…, Abstract base class for all agents in the simulation system., Initialize the base agent. Args: config: Optional configuration dictionary for…, Execute the agent's primary function. Args: context: The context dictionary…, String representation of the agent. (+26 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (21): get_simulation_service(), Dependency to get the simulation service. In a real application, this would be…, field_validator, Remove disallowed ASCII control characters, passing non-strings through…, Model for requesting a new simulation., Model for submitting a user response., SimulationRequest, _strip_control_chars() (+13 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (30): NarrationAgent, Any, Narration Agent Module This module implements the NarrationAgent which is…, Agent responsible for generating audio narration for scenarios. Handles the…, Initialize the Narration Agent. Args: huggingface_tts_service: The HuggingFace…, Execute the Narration Agent workflow: 1. Prepare narration text from scenario…, Exception, requires_api_key (+22 more)

### Community 3 - "Community 3"
Cohesion: 0.13
Nodes (17): Adds generated scenarios to the specified turn. Args: turn_number: The turn…, Model representing a single scenario in the simulation., Model representing a single turn in the simulation., Scenario, SimulationTurn, _lb_service(), _make_client(), _make_complete_sim() (+9 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (32): Video Agent Module This module implements the VideoAgent which is responsible…, find_available_port(), Main Application Entry Point This module serves as the entry point for the…, Find an available port to use if the default is occupied., Test HuggingFace Inference API for text-to-video generation., test_huggingface_integration(), HuggingFaceService, HuggingFace Service Module This module provides services for generating videos… (+24 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (39): Create New Files:, 📁 Directory Structure, 🔧 Files to Create/Modify, 📝 Implementation Notes, 📋 Implementation Status, Key Decisions, 📊 Key Implementation Principles, Langfuse Integration Implementation Plan (Phases 1-3) (+31 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (32): CloudflareR2Service, Cloudflare R2 Service Module This module provides services for storing and…, Service for handling interactions with Cloudflare R2 Storage. Provides methods…, Initialize the Cloudflare R2 service. Args: endpoint: The Cloudflare R2…, Ensure that the specified bucket exists, create it if it doesn't. Raises:…, Test Module for CloudflareR2Service This module tests the CloudflareR2Service…, Test uploading a video to R2 with private access., Test uploading an audio file to R2 with public access. (+24 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (15): Adds a user response to the specified turn. Args: turn_number: The turn number…, Model representing a user's response to a scenario., UserResponse, empty_service(), _make_sim(), _make_state_service(), populated_service(), datetime (+7 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (17): Custom JSON serialization that handles datetime objects., Generates a text representation of the simulation history for context. Returns:…, Selects a scenario for the specified turn. Args: turn_number: The turn number…, Adds video and narration prompts to the specified turn. Args: turn_number: The…, Adds media URLs to the specified turn. Args: turn_number: The turn number to…, Adds an LLM interaction log to the specified turn. Args: turn_number: The turn…, Model representing the complete state of a simulation., Custom dict method to ensure datetime fields are properly serialized. (+9 more)

### Community 9 - "Community 9"
Cohesion: 0.13
Nodes (18): LLMLog, Model representing a log of an LLM interaction., Simulation Service Module This module provides the main orchestration service…, Service for orchestrating the simulation flow. Coordinates interactions between…, Store an LLM interaction on its owning simulation. Args: turn_number: The turn…, SimulationService, FakeMediaService, make_log() (+10 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (22): debug_media_check(), delete_simulation(), export_analytics_csv(), get_analytics_summary(), get_analytics_trends(), get_leaderboard(), get_leaderboard_service(), get_player_rank() (+14 more)

### Community 11 - "Community 11"
Cohesion: 0.13
Nodes (6): EXPLAIN QUERY PLAN must show no TEMP B-TREE for all-time ranked query. The…, _submit(), TestLargeDataset, TestPlayerRank, TestScoresSavedAndRanked, TestTieBreaking

### Community 12 - "Community 12"
Cohesion: 0.11
Nodes (17): requires_huggingface_api_key, media_service(), asyncio, fixture, Integration tests for MediaService. These tests verify the MediaService which…, Test the end-to-end workflow with both audio and video generation., Test getting R2 storage status., Ensure media directories exist before tests. (+9 more)

### Community 13 - "Community 13"
Cohesion: 0.11
Nodes (14): MediaService, Any, Generate a video using HuggingFace Inference API. Args: prompt: The video…, Generate audio narration using Groq TTS API directly from scenario fields.…, Service for generating media using external APIs. Provides methods for video…, Generate video(s) and audio in parallel for maximum efficiency. If video_prompt…, Get the current R2 configuration. Returns: Dictionary with R2 configuration, Delete media files from storage. Args: object_keys: Single object key or list… (+6 more)

### Community 14 - "Community 14"
Cohesion: 0.18
Nodes (11): LeaderboardEntry, str, TimePeriod, LeaderboardService, datetime, LeaderboardService — SQLite-backed leaderboard (issue #4). Stores high scores…, fixture, Unit tests for LeaderboardService (issue #4: Leaderboard System). Acceptance… (+3 more)

### Community 15 - "Community 15"
Cohesion: 0.10
Nodes (12): Initialize the simulation service. Args: llm_service: Service for LLM…, State Service Module This module provides services for managing simulation…, Service for managing simulation state. In this MVP version, state is stored in…, Initialize the state service with an empty simulations dictionary., Create a new simulation with initial state. Args: simulation: Optional pre-…, Retrieve a simulation by ID. Args: simulation_id: The ID of the simulation to…, Update a simulation in the store. Args: simulation: The simulation state to…, Delete a simulation by ID. Args: simulation_id: The ID of the simulation to… (+4 more)

### Community 16 - "Community 16"
Cohesion: 0.13
Nodes (14): _cors_middleware_kwargs(), Regression tests for issue #12: CORS wildcard + allow_credentials=True…, Reload api.app under a controlled CORS_ORIGINS environment and return the…, Extract kwargs registered for CORSMiddleware from app.user_middleware. Returns…, When CORS_ORIGINS is unset, origins must default to localhost:3000., The default CORS origin list must NOT be the bare wildcard ['*']., The default CORS origin list must be ['http://localhost:3000']., CORSMiddleware registered on the app must not use the wildcard. (+6 more)

### Community 17 - "Community 17"
Cohesion: 0.10
Nodes (14): _make_connector_captor(), Regression tests for issue #11: SSL certificate verification was…, When VERIFY_SSL is True, the ssl= kwarg passed to TCPConnector must NOT be an…, When VERIFY_SSL is False, the ssl= kwarg must produce a context with…, Return a mock TCPConnector class and a list that captures ssl= kwargs., With VERIFY_SSL unset or 'true', certificate verification must be ON., Import (or reload) media_service with a patched environment and invoke the URL-…, VERIFY_SSL module constant must default to True when env var is absent. (+6 more)

### Community 18 - "Community 18"
Cohesion: 0.15
Nodes (15): LLMService, Set a callback function for logging LLM interactions. The callback receives…, Service for handling interactions with Language Models. Provides methods for…, Parse scenario descriptions from the LLM result. Args: result: The raw LLM…, Retrieve a scenario by its unique ID. Args: scenario_id: The unique ID of the…, llm_service(), MockHuggingFaceService, asyncio (+7 more)

### Community 19 - "Community 19"
Cohesion: 0.14
Nodes (13): init_services(), Request, FastAPI Application Module This module defines the main FastAPI application for…, Initialize services on startup., Initialize services and attach them to the router., startup_event(), timeout_middleware(), get_analytics_service() (+5 more)

### Community 20 - "Community 20"
Cohesion: 0.12
Nodes (15): change_difficulty(), Change the difficulty level for a simulation mid-game. Args: simulation_id: The…, DeveloperModeRequest, DifficultyChangeRequest, DifficultyLevel, BaseModel, Enum, str (+7 more)

### Community 21 - "Community 21"
Cohesion: 0.15
Nodes (12): BinaryIO, CloudflareR2ServiceError, Any, Execute an operation with retry logic. Args: operation_func: The function to…, Upload a video to R2 storage. Args: video_data: The video data as bytes or…, Base exception for Cloudflare R2 service errors., Upload an audio file to R2 storage. Args: audio_data: The audio data as bytes…, Download a file from R2 storage. Args: object_key: The object key (including… (+4 more)

### Community 22 - "Community 22"
Cohesion: 0.15
Nodes (11): TestClient, fixture, Create a TestClient for the FastAPI app., Create test media files for testing static file serving., setup_test_media(), test_client(), _make_client(), Regression tests for issue #13: GET /debug/media-check crashed with NameError… (+3 more)

### Community 23 - "Community 23"
Cohesion: 0.12
Nodes (16): express, http-proxy-middleware, next, dependencies, express, http-proxy-middleware, next, devDependencies (+8 more)

### Community 24 - "Community 24"
Cohesion: 0.12
Nodes (15): API Endpoints, Development, Features, Future Enhancements, Google Agent Development Kit Integration, Google Gemini Models, Groq Models, Installation (+7 more)

### Community 25 - "Community 25"
Cohesion: 0.16
Nodes (10): Unit tests for media utility functions. These tests verify the functions in…, Test cases for media utilities., Test that ensure_media_directories creates the necessary directories., Test basic functionality of generate_media_filename., Test generate_media_filename with simulation ID., Test generate_media_filename with different turn numbers., Test generate_media_filename with different file extensions., TestMediaUtils (+2 more)

### Community 26 - "Community 26"
Cohesion: 0.20
Nodes (12): backendPort, { getBackendPortSync }, nextConfig, { getBackendPort }, handler(), checkPort(), fs, getBackendPort() (+4 more)

### Community 27 - "Community 27"
Cohesion: 0.24
Nodes (14): _make_service(), _make_state_service(), asyncio, Regression tests for issue #17: bare except swallows BaseException. The old…, A KeyboardInterrupt raised inside the recovery block must NOT be caught by…, A SystemExit raised inside the recovery block must NOT be caught by `except…, Build a SimulationService with the given state_service and mocked LLM/media., Wire up a state_service mock that returns `sim` and applies the side effect. (+6 more)

### Community 28 - "Community 28"
Cohesion: 0.16
Nodes (12): Submit a completed simulation's grade to the leaderboard. The score is always…, submit_leaderboard_score(), extract_grade(), LeaderboardSubmitRequest, BaseModel, Enum, field_validator, RankInfo (+4 more)

### Community 29 - "Community 29"
Cohesion: 0.14
Nodes (13): Error: "Models.generate_content() got an unexpected keyword argument 'generation_config'", Fallback Mechanism, Gemini 2.5 Flash Integration Guide, Google Agent Development Kit Integration (Advanced), Key Components, Model Configuration, Model Invocation, No Response or Timeout (+5 more)

### Community 30 - "Community 30"
Cohesion: 0.21
Nodes (7): Prompts Module This module contains all the prompt templates and example JSON…, get_formatted_prompt_template(), Scenario Generation Prompt Module This module contains the prompt templates and…, Returns the appropriate prompt template based on whether this is the final…, # IMPORTANT: We do NOT return FINAL_TURN_TEMPLATE here for turn 3, Module containing the prompt template for video description generation., LLM Service Module This module provides services for interfacing with Language…

### Community 31 - "Community 31"
Cohesion: 0.21
Nodes (8): requires_llm_api_key, requires_video_api_key, asyncio, Test generating a video prompt from a scenario., Test direct video generation with HuggingFaceService., Test the full VideoAgent execution pipeline., Test VideoAgent with fallback when HuggingFace API is unavailable., Test that the HuggingFaceService initializes correctly.

### Community 32 - "Community 32"
Cohesion: 0.22
Nodes (7): Any, Log an LLM interaction if a callback is set. Args: turn_number: The current…, Generate a single scenario idea based on context. Args: context: The current…, Parse JSON-formatted scenarios from the LLM result. Args: result: The raw LLM…, Validate a list of scenarios and ensure they have the required fields. Args:…, Validate a single scenario and ensure it has the required fields. Args:…, Create a default scenario when parsing fails. Args: current_turn_number: The…

### Community 33 - "Community 33"
Cohesion: 0.22
Nodes (11): FakeMediaService, LangfuseLessLLM, llm_service(), asyncio, fixture, Regression tests for issue #10: LLMService is missing start_langfuse_session,…, create_new_simulation must not raise AttributeError on the Langfuse call., process_user_response must not raise AttributeError on Langfuse reinit/flush. (+3 more)

### Community 34 - "Community 34"
Cohesion: 0.17
Nodes (7): GroqTTSService, Groq TTS Service Module This module provides a service for generating audio…, Service for generating audio narration using Groq's TTS API. Requires a Groq…, Initialize the Groq TTS service. Args: groq_api_key: The Groq API key, Synchronous helper function to perform the blocking API call and file I/O., Generate audio from text using Groq TTS API. Runs blocking calls in a separate…, Initialize the media service. Args: huggingface_api_key: The HuggingFace API…

### Community 35 - "Community 35"
Cohesion: 0.17
Nodes (7): Test that media directories are correctly mounted in the app., Test serving video files through the static file handler., Test serving audio files through the static file handler., Test handling of requests for nonexistent files., Test that the static file handler prevents path traversal attacks., Test cases for static file serving., TestStaticFileServing

### Community 36 - "Community 36"
Cohesion: 0.33
Nodes (3): get_difficulty_instructions(), Return difficulty-specific prompt instructions. Args: difficulty: The…, TestDifficultyInstructions

### Community 37 - "Community 37"
Cohesion: 0.20
Nodes (5): Pre-initialize the scenarios dictionary with all possible scenario IDs. Args:…, Get or create an LLM instance for the specified model name. Args: model_name:…, Generate a video generation prompt from the scenario details, parse it, and…, Initialize the LLM service. Args: api_key: The Groq API key default_model_name:…, Generates four video scene descriptions from a scenario, then generates a video…

### Community 39 - "Community 39"
Cohesion: 0.29
Nodes (7): create_simulation(), Toggle developer mode for a simulation. Args: simulation_id: The ID of the…, Create a new simulation. Returns: The newly created SimulationState, Submit a user response to a simulation. Args: simulation_id: The ID of the…, submit_response(), toggle_developer_mode(), post

### Community 40 - "Community 40"
Cohesion: 0.29
Nodes (3): LIMITS, PERIODS, RANK_COLORS

### Community 41 - "Community 41"
Cohesion: 0.29
Nodes (3): MOCK_ENTRIES, MOCK_RANK, MOCK_SUBMIT_RESPONSE

### Community 42 - "Community 42"
Cohesion: 0.33
Nodes (5): app, express, handle, next, path

### Community 44 - "Community 44"
Cohesion: 0.40
Nodes (5): Test script for Gemini 2.5 Flash integration. This script tests the integration…, Test direct interaction with Gemini 2.5 Flash., Test integration with Google Agent Development Kit., test_direct_api(), test_gadk_integration()

### Community 46 - "Community 46"
Cohesion: 0.40
Nodes (5): mock_boto3_client(), fixture, r2_credentials(), Mock Cloudflare R2 credentials for testing., Create a mock boto3 client.

### Community 48 - "Community 48"
Cohesion: 0.50
Nodes (3): Test script for scenario generation using the LLM service. This script tests…, Test the scenario generation flow., test_scenario_generation()

### Community 49 - "Community 49"
Cohesion: 0.50
Nodes (3): builds, routes, version

## Knowledge Gaps
- **88 isolated node(s):** `{ getBackendPortSync }`, `backendPort`, `nextConfig`, `express`, `http-proxy-middleware` (+83 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LLMService` connect `Community 18` to `Community 0`, `Community 32`, `Community 33`, `Community 4`, `Community 37`, `Community 9`, `Community 15`, `Community 48`, `Community 19`, `Community 30`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Why does `MediaService` connect `Community 13` to `Community 34`, `Community 4`, `Community 6`, `Community 9`, `Community 12`, `Community 15`, `Community 19`, `Community 21`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Why does `SimulationState` connect `Community 8` to `Community 1`, `Community 3`, `Community 36`, `Community 7`, `Community 9`, `Community 10`, `Community 15`, `Community 20`, `Community 27`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `SimulationState` (e.g. with `SimulationService` and `StateService`) actually correct?**
  _`SimulationState` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `LLMService` (e.g. with `CreativeDirectorAgent` and `VideoAgent`) actually correct?**
  _`LLMService` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `SimulationService` (e.g. with `DifficultyLevel` and `LLMLog`) actually correct?**
  _`SimulationService` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `StateService` (e.g. with `AnalyticsService` and `SimulationService`) actually correct?**
  _`StateService` has 9 INFERRED edges - model-reasoned connections that need verification._