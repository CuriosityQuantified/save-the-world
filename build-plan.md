## Phased Build Plan: Interactive Simulation

This plan outlines the development stages, starting with an MVP to validate the core simulation loop and progressively adding features like agentic workflows, critique loops, robust state management, and a polished UI.

**Core Technologies:**

* **LLMs:** For scenario generation, selection, video prompt writing, narration script writing.
* **Video Generation:** RunwayML API.
* **Audio Generation:** ElevenLabs API.
* **State Management:** In-memory (MVP) -> Redis (Later Phases).
* **Orchestration:** Basic script (MVP) -> Google Agent Development Kit (Later Phases).
* **Storage:** Local/Temporary (MVP) -> Cloudflare R2 (Later Phases).
* **UI:** CLI/Simple HTML (MVP) -> Vercel Web App (Later Phases).

## Progress Update (Current Status)

**Completed Items:**
* ✅ Project setup with virtual environment
* ✅ LLM Service implementation with Groq API integration
* ✅ Enhanced scenario generation with optimized prompts
  - Created comprehensive prompt templates for absurd crisis scenarios
  - Implemented JSON response parsing for structured scenario data
  - Added support for initial scenarios and follow-up generation
  - Enhanced with diverse example scenarios (humans, animals, abstract concepts)
  - Optimized temperature settings for more creative outputs
* ✅ Basic testing framework
  - Created test script to verify scenario generation flow
  - Implemented simulation of the 5-turn interactive loop
  - Successfully tested with Llama 4 model
* ✅ Full end-to-end simulation flow
  - Implemented scenario selection (critique_idea)
  - Added scenario generation, selection, and user response handling
  - Created specialized conclusion scenarios for the final turn
* ✅ REST API development with FastAPI
  - Created API endpoints for simulation creation and interaction
  - Implemented WebSocket support for real-time updates
  - Fixed JSON serialization for datetime objects
* ✅ State management
  - Implemented in-memory state service for tracking simulation progress
  - Added proper state transition between turns

**In Progress:**
* 🔄 Integration with RunwayML and ElevenLabs APIs
* 🔄 Simple web UI for user interaction

**Next Steps:**
* ⏩ Complete media generation integration
* ⏩ Implement frontend interface
* ⏩ Add error handling and robustness
* ⏩ Deploy to production environment

### Phase 1: MVP - Core Simulation Loop & API Integration

**Goal:** Create a functional end-to-end simulation loop for a single user, proving the core logic and integration with external media generation APIs.

**Steps:**

1.  **Setup Basic Project:**
    * Create a project directory.
    * Set up a virtual environment and install necessary libraries (e.g., `requests`, `python-dotenv`, LLM client library, basic web server like Flask/FastAPI if needed for simple UI).
    * Configure environment variables for LLM, Runway, and ElevenLabs API keys.
2.  **Implement Simplified Scenario Generation (LLM 1):**
    * Write a Python function `generate_scenario(context: str) -> str`.
    * This function takes the previous turn's context (or an initial prompt) and calls the LLM to generate *one* new situation description.
    * For the first turn, use a predefined starting prompt. For subsequent turns, include the previous situation and the user's response in the context.
3.  **Implement Content Prompt Generation (LLMs 3 & 4):**
    * Write `generate_video_prompt(situation: str) -> str` (using LLM 3).
    * Write `generate_narration_script(situation: str) -> str` (using LLM 4).
    * These functions take the generated situation and create the respective prompts/scripts. Aim for ~10 seconds of content.
4.  **Integrate RunwayML API:**
    * Write a function `submit_runway_job(prompt: str) -> str` that sends the prompt to the Runway API and initiates video generation. It should return a job ID.
    * Write a function `get_runway_result(job_id: str) -> str | None` that polls the Runway API using the job ID and returns the video URL once completed (or `None` if still processing). Handle basic API errors.
5.  **Integrate ElevenLabs API:**
    * Write a function `submit_elevenlabs_job(script: str) -> str` that sends the script to the ElevenLabs API. This might return audio data directly or a job ID depending on the chosen endpoint/workflow.
    * If asynchronous, write a corresponding `get_elevenlabs_result` function similar to Runway's. Ensure the output is a usable audio URL or file path.
6.  **Basic State Management:**
    * Use simple Python variables or a dictionary in the main script to hold the current `situation`, `user_response`, `video_url`, `audio_url`, and `turn_number`. This state will be lost when the script ends.
7.  **Create Simple User Interface (CLI or Basic HTML):**
    * **Option A (CLI):**
        * Print the current `situation` text.
        * Print the `video_url` and `audio_url` (user manually opens them).
        * Use `input()` to get the user's response.
    * **Option B (Basic HTML/Web Server):**
        * Use Flask/FastAPI to serve a single HTML page.
        * Display the `situation` text.
        * Embed HTML5 `<video>` and `<audio>` tags using the retrieved URLs. *Challenge: Ensure media is ready before displaying/enabling play.*
        * Use an HTML `<form>` to submit the user's text response back to the server.
8.  **Implement Core Loop:**
    * Write the main script logic:
        * Initialize turn = 0, context = initial_prompt.
        * **Loop 5 times:**
            * Increment turn number.
            * `situation = generate_scenario(context)`
            * `video_prompt = generate_video_prompt(situation)`
            * `narration_script = generate_narration_script(situation)`
            * `runway_job_id = submit_runway_job(video_prompt)`
            * `elevenlabs_job_id = submit_elevenlabs_job(narration_script)`
            * **Poll** for results (wait until both `video_url` and `audio_url` are available). *This will be blocking.*
            * Display situation, video, audio to the user (via CLI or web UI).
            * Get `user_response`.
            * Update `context` = f"Previous Situation: {situation}\nUser Action: {user_response}"
        * End simulation.

**MVP Outcome:** A runnable script or basic web app demonstrating one complete 5-turn simulation, including calls to external APIs and user interaction, albeit with simplified logic and basic UI/state handling.

### Phase 2: Introduce Agents, Robust State & Async Handling

**Goal:** Refactor the MVP logic into a more structured agent-based system, implement persistent state, and handle asynchronous API calls properly.

**Steps:**

1.  **Bootstrap GADK Project:** Scaffold a GADK project. Define `CreativeDirectorAgent`, `VideoAgent`, `NarrationAgent`.
2.  **Refactor LLM Calls into Tools:** Convert the Python functions from Phase 1 (`generate_scenario`, `generate_video_prompt`, `generate_narration_script`) into GADK Tools within the appropriate agents.
3.  **Implement Full Scenario Generation/Selection:** Implement the `create_idea` (generate 5) and `critique_idea` (select 1) tools within the `CreativeDirectorAgent`.
4.  **Implement Redis State Management:** Define the `ScenarioState` Pydantic model. Implement `load/save_scenario_state` helpers. Update tools to read from and write to Redis instead of using in-memory variables. Store `turn_history`.
5.  **Refactor API Calls:** Move Runway/ElevenLabs submission logic into `submit_video_job` and `submit_tts_job` tools within their respective agents. These tools should update the `ScenarioState` in Redis with job IDs and status.
6.  **Handle Asynchronous Callbacks/Polling:**
    * **Option A (Webhooks):** Configure Runway/ElevenLabs to send completion events to webhook endpoints hosted by your GADK application (e.g., on Vercel). These endpoints trigger functions to update the `ScenarioState` in Redis with the final media URLs.
    * **Option B (Background Polling):** Implement a separate process or scheduled task that periodically checks the status of pending jobs (using job IDs stored in Redis) and updates the `ScenarioState` upon completion.
7.  **Orchestration:** Define the GADK event flow: `CreativeDirectorAgent` finishes -> triggers `VideoAgent` and `NarrationAgent` in parallel -> UI waits for status updates in Redis indicating media readiness.

### Phase 3: Implement Critique Loops & Error Handling

**Goal:** Enhance agents with self-critique capabilities and make the system more resilient.

**Steps:**

1.  **Implement Critique Tools:** Add `critique_video_prompt` and `critique_narration_script` tools. Define prompts/rubrics for critique. Implement the logic within agents to loop between `create_X` and `critique_X` until quality thresholds are met.
2.  **Robust Error Handling:** Add `try/except` blocks around LLM calls, API calls, and Redis interactions. Implement retry logic for transient errors. Handle API rate limits gracefully.
3.  **Configuration Management:** Ensure all API keys, model names, and other settings are configurable via environment variables or a dedicated config file.

### Phase 4: Build Production Front-End & Deployment

**Goal:** Create a polished user interface and deploy the full application.

**Steps:**

1.  **Develop Web UI (Vercel):** Build a React/Vue/HTML+JS front-end. Display scenario context, turn history, embedded media players. Implement a clean input mechanism. Fetch state/URLs from the backend orchestrator/API.
2.  **Cloudflare R2 Integration:** Configure an R2 bucket. Update `VideoAgent` and `NarrationAgent` (or the webhook handlers) to upload completed media files to R2 and store the R2 URL (potentially signed) in the `ScenarioState`. Configure CORS.
3.  **Deploy GADK Orchestrator:** Deploy the GADK application (including webhook endpoints) to Vercel or another suitable hosting provider.
4.  **Connect UI and Backend:** Ensure the front-end communicates correctly with the deployed backend API endpoints to start simulations, fetch status/media URLs, and submit user responses.

### Phase 5: Testing, Iteration & Hardening

**Goal:** Ensure stability, performance, and usability through testing and refinement.

**Steps:**

1.  **End-to-End Testing:** Create test cases covering various scenarios, edge cases, and potential failures.
2.  **Monitoring & Logging:** Integrate logging tools to track agent execution, API calls, errors, and performance. Set up monitoring dashboards.
3.  **Cost Controls:** Implement limits on the number of turns, LLM calls per turn, or total API usage per simulation to prevent runaway costs.
4.  **User Feedback & Prompt Tuning:** Gather feedback from users and refine LLM prompts for scenarios, video generation, and narration to improve quality and coherence. Iterate on the UI/UX based on feedback.
5.  **Security Review:** Ensure API keys are secure, signed URLs have appropriate expiry, and input validation is in place.