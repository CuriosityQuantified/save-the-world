# Interactive Simulation System

A system that generates personalized scenario-based simulations using AI, featuring:
- Scenario generation using LLMs
- Video generation via RunwayML
- Audio narration through ElevenLabs
- Interactive 5-turn simulation flow

## Features

- **FastAPI Backend**: RESTful API with WebSocket support for real-time updates
- **Interactive Web UI**: Simple frontend for interacting with simulations
- **5-Turn Simulation**: Complete simulation flow with state management
- **Media Generation**: Integration with RunwayML and ElevenLabs APIs
- **Diverse Scenarios**: Absurd world-threatening crises including humans, animals, and abstract concepts
- **Conclusive Endings**: Special scenario generation for satisfying final turns

## Project Structure

```
sim-local/
├── api/                          # API implementation
│   ├── app.py                    # FastAPI application
│   └── routes.py                 # API endpoints
├── models/                       # Data models
│   └── simulation.py             # Simulation state models
├── services/                     # Service layer
│   ├── llm_service.py            # LLM interactions
│   ├── media_service.py          # Media generation
│   ├── simulation_service.py     # Simulation orchestration
│   └── state_service.py          # State management
├── prompts/                      # Prompt templates
│   └── scenario_generation_prompt.py  # Scenario generation prompts
├── ui/                           # Frontend
│   └── public/                   # Static files
│       └── index.html            # Main UI
├── tests/                        # Tests
├── .env.example                  # Environment variables template
├── main.py                       # Application entry point
├── requirements.txt              # Dependencies
└── README.md                     # This file
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/CuriosityQuantified/sim-local.git
   cd sim-local
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file from the template:
   ```bash
   cp .env.example .env
   ```

5. Update the `.env` file with your API keys:
   - `GROQ_API_KEY`: Your Groq API key for LLM access
   - `RUNWAY_API_KEY`: Your RunwayML API key for video generation
   - `ELEVENLABS_API_KEY`: Your ElevenLabs API key for audio generation

## Running the Application

Start the application with:

```bash
python main.py
```

The server will start at http://localhost:8000, and you can access the web UI by opening that URL in your browser.

## API Endpoints

- `POST /api/simulations`: Create a new simulation
- `GET /api/simulations/{simulation_id}`: Get a simulation by ID
- `POST /api/simulations/{simulation_id}/respond`: Submit a user response
- `GET /api/simulations`: List all simulations
- `DELETE /api/simulations/{simulation_id}`: Delete a simulation
- `WebSocket /api/ws/simulations/{simulation_id}`: Real-time updates for a simulation

## Development

For development mode with auto-reload:

```bash
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

## Testing

Run tests with:

```bash
pytest
```

## Future Enhancements

- Developer mode to display LLM inputs/outputs
- Persistent storage with Redis
- Production deployment to Vercel
- Media storage with Cloudflare R2
- Enhanced critique capabilities for scenario selection
- User authentication and saved simulations 