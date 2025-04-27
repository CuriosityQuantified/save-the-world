# Interactive Simulation System

A system that generates personalized scenario-based simulations using AI, featuring:
- Scenario generation using LLMs (Groq or Google Gemini)
- Video generation via HuggingFace fal-ai provider or RunwayML Gen-4 Turbo
- Audio narration through ElevenLabs
- Interactive 5-turn simulation flow

## Features

- **FastAPI Backend**: RESTful API with WebSocket support for real-time updates
- **Interactive Web UI**: Simple frontend for interacting with simulations
- **5-Turn Simulation**: Complete simulation flow with state management
- **Media Generation**: Integration with HuggingFace fal-ai, RunwayML Gen-4 Turbo and ElevenLabs APIs
- **Multiple LLM Support**: Works with Groq models and Google Gemini 2.5 Flash
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

   For the HuggingFace fal-ai text-to-video integration, make sure you have the latest huggingface_hub with all required dependencies:
   ```bash
   pip install "huggingface_hub[inference,cli]>=0.21.0"
   ```

4. Create a `.env` file from the template:
   ```bash
   cp .env.example .env
   ```

5. Update the `.env` file with your API keys:
   - `GROQ_API_KEY`: Your Groq API key for LLM access
   - `RUNWAY_API_KEY`: Your RunwayML API key for video generation
   - `HUGGINGFACE_API_KEY`: Your HuggingFace API key for video generation and text-to-speech narration
   - `ELEVENLABS_API_KEY`: Your ElevenLabs API key (legacy, optional)
   - `GOOGLE_API_KEY`: Your Google API key for Gemini models (optional)

## Running the Application

Start the application with:

```bash
python main.py
```

The server will start at http://localhost:8000, and you can access the web UI by opening that URL in your browser.

## Testing RunwayML Integration

To test the RunwayML Gen-4 Turbo integration:

1. Ensure your `RUNWAY_API_KEY` is set in your `.env` file
2. Run the test script:
   ```bash
   python scripts/test_runway.py
   ```
3. Or provide a custom prompt:
   ```bash
   python scripts/test_runway.py "Generate a 10-second video of: A serene beach at sunset with waves gently washing ashore."
   ```

The script will generate a 10-second video using RunwayML Gen-4 Turbo and provide a URL to view the result.

## Testing HuggingFace Integration

To test the HuggingFace text-to-video integration:

1. Ensure your `HUGGINGFACE_API_KEY` is set in your `.env` file
2. Run the test script:
   ```bash
   python scripts/test_huggingface.py
   ```
3. Or provide a custom prompt:
   ```bash
   python scripts/test_huggingface.py "Generate a video of: A serene beach at sunset with waves gently washing ashore."
   ```

### Testing HuggingFace fal-ai Text-to-Video

To test the HuggingFace fal-ai text-to-video provider with the Wan2.1-T2V-14B model:

1. Ensure your `HUGGINGFACE_API_KEY` is set in your `.env` file
2. Run the fal-ai test script:
   ```bash
   python scripts/test_huggingface_fal.py
   ```
3. Or provide a custom prompt:
   ```bash
   python scripts/test_huggingface_fal.py "Generate a video of: A serene beach at sunset with waves gently washing ashore."
   ```

This integration uses the Wan-AI/Wan2.1-T2V-14B model through the fal-ai provider.

To test the HuggingFace Dia-TTS text-to-speech integration:

1. Ensure your `HUGGINGFACE_API_KEY` is set in your `.env` file
2. Run the test script:
   ```bash
   python scripts/test_huggingface_tts.py
   ```
3. Or provide a custom prompt:
   ```bash
   python scripts/test_huggingface_tts.py "Welcome to the interactive simulation. Let's explore a fascinating scenario together!"
   ```

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

## LLM Support

The application supports multiple LLM providers:

### Groq Models
By default, the application uses Groq's "qwen-qwq-32b" model. To use Groq:
- Ensure `GROQ_API_KEY` is set in your `.env` file

### Google Gemini Models
The application also supports Google's Gemini 2.5 Flash model. To use Gemini:
- Set `GOOGLE_API_KEY` in your `.env` file
- When the Google API key is provided, Gemini becomes the primary LLM
- If Gemini API calls fail, the application automatically falls back to Groq

### Google Agent Development Kit Integration
For advanced agent capabilities using Google Gemini:
1. Install the Google ADK package:
   ```bash
   pip install google-adk
   ```

2. Run the Gemini test script:
   ```bash
   python tests/test_gemini.py
   ```

3. To test with Agent Development Kit integration:
   ```bash
   python tests/test_gemini.py --gadk
   ``` 