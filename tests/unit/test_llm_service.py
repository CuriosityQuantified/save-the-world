import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json
import os

# Ensure imports for LLMService and related classes are correct
# This might require adjusting the Python path or using relative imports if run as part of a package
# For now, assuming direct import path works or PYTHONPATH is set up
from services.llm_service import LLMService
from models.simulation import LLMLog
from prompts.scenario_generation_prompt import FINAL_CONCLUSION_EXAMPLE_JSON # For structure reference

# Mock HuggingFaceService if it's a required dependency for LLMService instantiation
class MockHuggingFaceService:
    def __init__(self, api_key, r2_service=None):
        pass

    async def generate_video(self, prompt, turn=1):
        return f"https://example.com/video_for_turn_{turn}.mp4"

@pytest.fixture
def llm_service():
    # Instantiate LLMService with mock dependencies if necessary
    # If HuggingFaceService is required for __init__, pass a mock
    # For this test, we are focusing on create_idea, so HF might not be critical beyond instantiation
    return LLMService(api_key="fake_groq_api_key", huggingface_service=MockHuggingFaceService(api_key="fake_hf_key"))

@pytest.mark.asyncio
async def test_create_idea_final_turn_conclusion_parsing():
    """
    Tests that create_idea correctly parses a slightly messy JSON output 
    for the final turn conclusion, using the specified 'qwen-qwq-32b' model.
    """
    service = LLMService(api_key="test_api_key", huggingface_service=MockHuggingFaceService(api_key="fake_hf_key"))
    service.log_callback = AsyncMock() # Mock the log_callback

    # Simulate context for the final turn (e.g., turn 6 of 6)
    final_turn_context = {
        "simulation_history": "Turn 1: ... User Response: ...\nTurn 5: ... User Response: Final plan!",
        "current_turn_number": 6,
        "previous_turn_number": 5,
        "user_prompt_for_this_turn": "This is my final response for turn 5.",
        "max_turns": 6
    }

    # Expected output structure for a final conclusion
    # Based on FINAL_TURN_TEMPLATE, it should be a single object, not a list in the example
    # The _parse_json_scenarios now wraps single dicts in a list.
    mock_llm_output_json = {
        "situation_description": "The world is saved, with a lingering scent of existential absurdity!",
        "rationale": "User displayed excellent problem-solving skills under bizarre pressure.",
        "grade": 92,
        "grade_explanation": "Consistently high-quality responses, creative and effective."
    }

    # Simulate a slightly messy LLM response string
    # Leading/trailing newlines and wrapped in backticks
    messy_llm_response_str = f"""
```json
{json.dumps(mock_llm_output_json)}
```
    """

    # Mock the Groq client's chat.completions.create method
    # This is the primary method used for 'qwen-qwq-32b' as per current llm_service logic for final turn
    mock_groq_completion = MagicMock()
    mock_groq_completion.choices = [MagicMock()]
    mock_groq_completion.choices[0].message.content = messy_llm_response_str
    
    # The Groq client itself
    mock_groq_client = MagicMock()
    mock_groq_client.chat.completions.create = AsyncMock(return_value=mock_groq_completion) # Use AsyncMock for async context

    # Patch the Groq client instance within the service or where it's instantiated.
    # Assuming self.groq_client is used:
    with patch.object(service, 'groq_client', mock_groq_client):
        generated_scenario_list = await service.create_idea(final_turn_context)

    # Assertions
    assert generated_scenario_list is not None, "create_idea should return a list of scenarios"
    assert len(generated_scenario_list) == 1, "Expected one scenario for the conclusion"
    
    generated_scenario = generated_scenario_list[0]

    # Check that the correct model was intended to be used (qwen-qwq-32b for final turn)
    # The actual call is mocked, but we check if the logic path for qwen-qwq-32b would be taken.
    # We can infer this if groq_client.chat.completions.create was called.
    service.groq_client.chat.completions.create.assert_called_once()
    call_args = service.groq_client.chat.completions.create.call_args
    assert call_args is not None, "Groq client was not called as expected"
    assert call_args.kwargs.get('model') == "qwen-qwq-32b", "Incorrect model specified for final turn"


    # Check that the parsed scenario contains the expected fields and values
    assert generated_scenario['situation_description'] == mock_llm_output_json['situation_description']
    assert generated_scenario['rationale'] == mock_llm_output_json['rationale']
    assert generated_scenario['grade'] == mock_llm_output_json['grade']
    assert generated_scenario['grade_explanation'] == mock_llm_output_json['grade_explanation']

    # Ensure no extra fields like user_role or user_prompt are present for conclusion
    assert 'user_role' not in generated_scenario
    assert 'user_prompt' not in generated_scenario
    
    # Check that an ID was added during validation (even if not in LLM output)
    assert 'id' in generated_scenario
    assert generated_scenario['id'] == f"scenario_{final_turn_context['current_turn_number']}_1"

    # Verify logging (optional, but good practice)
    service.log_callback.assert_called_once()
    log_args = service.log_callback.call_args[0] # Get positional arguments of the call
    assert log_args[1].operation_name == "create_idea"
    assert log_args[1].model_name == "qwen-qwq-32b"
    # Further checks on log_args[1].prompt and log_args[1].completion can be added


@pytest.mark.asyncio
async def test_create_idea_final_turn_fallback_parsing():
    """
    Tests that create_idea correctly parses a final turn conclusion 
    when the JSON is not perfectly clean and requires the find '{' '}' fallback.
    """
    service = LLMService(api_key="test_api_key", huggingface_service=MockHuggingFaceService(api_key="fake_hf_key"))
    service.log_callback = AsyncMock()

    final_turn_context = {
        "simulation_history": "History...", "current_turn_number": 6, "max_turns": 6,
        "previous_turn_number": 5, "user_prompt_for_this_turn": "Final response"
    }
    mock_llm_output_json = {
        "situation_description": "Fallback test success.",
        "rationale": "Fallback rationale.",
        "grade": 75,
        "grade_explanation": "Fallback explanation."
    }
    # Simulate LLM response with leading garbage and no markdown, forcing find {' '}'
    messy_llm_response_str = f"Some unexpected text before the JSON... \n {json.dumps(mock_llm_output_json)} \n ...and some after."

    mock_groq_completion = MagicMock()
    mock_groq_completion.choices = [MagicMock()]
    mock_groq_completion.choices[0].message.content = messy_llm_response_str
    
    mock_groq_client = MagicMock()
    mock_groq_client.chat.completions.create = AsyncMock(return_value=mock_groq_completion)

    with patch.object(service, 'groq_client', mock_groq_client):
        generated_scenario_list = await service.create_idea(final_turn_context)

    assert generated_scenario_list is not None
    assert len(generated_scenario_list) == 1
    generated_scenario = generated_scenario_list[0]

    assert generated_scenario['situation_description'] == mock_llm_output_json['situation_description']
    assert generated_scenario['grade'] == mock_llm_output_json['grade']
    assert 'id' in generated_scenario

    service.log_callback.assert_called_once()
    log_args = service.log_callback.call_args[0]
    assert log_args[1].model_name == "qwen-qwq-32b"


@pytest.mark.asyncio
async def test_create_idea_live_groq_call():
    """
    Tests that create_idea can make a live call to the Groq API
    and parse a valid response. This test requires the GROQ_API_KEY
    environment variable to be set.
    """
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        pytest.skip("GROQ_API_KEY environment variable not set. Skipping live test.")

    # Instantiate LLMService with the live API key
    # Using a mock HuggingFaceService as it's not the focus of this test
    service = LLMService(api_key=groq_api_key, huggingface_service=MockHuggingFaceService(api_key="fake_hf_key"))
    service.log_callback = AsyncMock()  # Mock the log_callback

    # Simulate context for an initial turn
    initial_turn_context = {
        "simulation_history": "",
        "current_turn_number": 1,
        "previous_turn_number": 0,
        "user_prompt_for_this_turn": "Generate a very simple absurd scenario about sentient teacups.",
        "max_turns": 6
    }

    try:
        generated_scenario = await service.create_idea(initial_turn_context)
    except Exception as e:
        pytest.fail(f"Live API call to create_idea failed: {e}")

    # Assertions
    assert generated_scenario is not None, "create_idea should return a scenario object"
    assert isinstance(generated_scenario, dict), "create_idea should return a dictionary"
    
    # Check for essential keys in the generated scenario
    # For initial turn, we expect: id, situation_description, rationale, user_role, user_prompt
    expected_keys = ["id", "situation_description", "rationale", "user_role", "user_prompt"]
    for key in expected_keys:
        assert key in generated_scenario, f"Key '{key}' missing from generated scenario"
        assert generated_scenario[key] is not None, f"Key '{key}' should not be None"
        assert isinstance(generated_scenario[key], str) or (key == "grade" and isinstance(generated_scenario[key], int)), f"Key '{key}' has unexpected type: {type(generated_scenario[key])}"


    # Verify logging (optional, but good practice for live calls too)
    service.log_callback.assert_called_once()
    log_args = service.log_callback.call_args[0]  # Get positional arguments of the call
    assert log_args[1].operation_name == "create_idea"
    # The model used might vary depending on LLMService internal logic for non-final turns,
    # so we might not assert a specific model unless we force one.
    # For now, just check that a model_name is logged.
    assert log_args[1].model_name is not None and len(log_args[1].model_name) > 0, "Model name not logged"
    assert log_args[1].completion is not None # Ensure some completion was logged


    # The following test is for final turn fallback parsing, ensure it's correctly placed
    @pytest.mark.asyncio
    async def test_create_idea_final_turn_fallback_parsing():
        """
        Tests that create_idea correctly parses a final turn conclusion 
        when the JSON is not perfectly clean and requires the find '{' '}' fallback.
        """
        service = LLMService(api_key="test_api_key", huggingface_service=MockHuggingFaceService(api_key="fake_hf_key"))
        service.log_callback = AsyncMock()

        final_turn_context = {
            "simulation_history": "History...", "current_turn_number": 6, "max_turns": 6,
            "previous_turn_number": 5, "user_prompt_for_this_turn": "Final response"
        }
        mock_llm_output_json = {
            "situation_description": "Fallback test success.",
            "rationale": "Fallback rationale.",
            "grade": 75,
            "grade_explanation": "Fallback explanation."
        }
        # Simulate LLM response with leading garbage and no markdown, forcing find {' '}'
        messy_llm_response_str = f"Some unexpected text before the JSON... \n {json.dumps(mock_llm_output_json)} \n ...and some after."

        mock_groq_completion = MagicMock()
        mock_groq_completion.choices = [MagicMock()]
        mock_groq_completion.choices[0].message.content = messy_llm_response_str
        
        mock_groq_client = MagicMock()
        mock_groq_client.chat.completions.create = AsyncMock(return_value=mock_groq_completion)

        with patch.object(service, 'groq_client', mock_groq_client):
            generated_scenario_list = await service.create_idea(final_turn_context)

        assert generated_scenario_list is not None
        assert len(generated_scenario_list) == 1
        generated_scenario = generated_scenario_list[0]

        assert generated_scenario['situation_description'] == mock_llm_output_json['situation_description']
        assert generated_scenario['grade'] == mock_llm_output_json['grade']
        assert 'id' in generated_scenario

        service.log_callback.assert_called_once()
        log_args = service.log_callback.call_args[0]
        assert log_args[1].model_name == "qwen-qwq-32b" 