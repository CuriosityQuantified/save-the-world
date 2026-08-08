from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
import json
import re
import uuid

# ASCII control chars (< 0x20 except tab/newline/CR) plus Unicode bidi and zero-width chars
# that are commonly used in prompt-injection attacks against LLMs.
_CONTROL_CHARS = re.compile(
    r"[\x00-\x08\x0B\x0C\x0E-\x1F"
    r"​-‏"   # zero-width space/non-joiner/joiner/LRM/RLM
    r"‪-‮"   # bidi embedding/override characters
    r"⁦-⁩"   # bidi isolate characters
    r"  "    # line/paragraph separators
    r"﻿"          # byte-order mark
    r"]"
)


def _strip_control_chars(v):
    """Remove disallowed ASCII control characters, passing non-strings through unchanged."""
    if not isinstance(v, str):
        return v
    return _CONTROL_CHARS.sub("", v)


# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class LLMLog(BaseModel):
    """Model representing a log of an LLM interaction."""
    operation_name: str
    prompt: str
    completion: str
    model_name: str
    parameters: Dict[str, Any] = {}
    response_time_seconds: Optional[float] = None  # Response time in seconds
    timestamp: datetime = Field(default_factory=datetime.now)

class Scenario(BaseModel):
    """Model representing a single scenario in the simulation."""
    id: str
    situation_description: str
    rationale: str
    user_role: Optional[str] = ""
    user_prompt: Optional[str] = ""
    grade: Optional[int] = None
    grade_explanation: Optional[str] = None

class UserResponse(BaseModel):
    """Model representing a user's response to a scenario."""
    turn_number: int
    response_text: str
    timestamp: datetime = Field(default_factory=datetime.now)

class SimulationTurn(BaseModel):
    """Model representing a single turn in the simulation."""
    turn_number: int
    scenarios: List[Scenario] = []
    selected_scenario: Optional[Scenario] = None
    user_response: Optional[UserResponse] = None
    video_prompt: Optional[Union[str, List[str]]] = None
    narration_script: Optional[str] = None
    video_urls: Optional[List[str]] = None
    audio_url: Optional[str] = None
    llm_logs: List[LLMLog] = []  # New field to store LLM logs for this turn
    timestamp: datetime = Field(default_factory=datetime.now)

class DifficultyLevel(str, Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"


class SimulationState(BaseModel):
    """Model representing the complete state of a simulation."""
    simulation_id: str = Field(default_factory=lambda: f"sim_{uuid.uuid4().hex[:12]}")
    current_turn_number: int = 1  # Keeping for backward compatibility temporarily
    submission_count: int = 0  # NEW: Counter that increments on each POST request
    max_turns: int = 3  # Configurable max submissions before conclusion
    turns: List[SimulationTurn] = []
    is_complete: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    developer_mode: bool = False  # Flag to enable/disable developer mode
    difficulty: DifficultyLevel = DifficultyLevel.NORMAL  # Difficulty level for this simulation

    def dict(self, *args, **kwargs):
        """
        Custom dict method to ensure datetime fields are properly serialized.
        """
        result = super().dict(*args, **kwargs)
        # Convert datetime objects to ISO format strings
        if 'created_at' in result and isinstance(result['created_at'], datetime):
            result['created_at'] = result['created_at'].isoformat()
        if 'updated_at' in result and isinstance(result['updated_at'], datetime):
            result['updated_at'] = result['updated_at'].isoformat()

        # Process turns
        if 'turns' in result and result['turns']:
            for turn in result['turns']:
                if 'timestamp' in turn and isinstance(turn['timestamp'], datetime):
                    turn['timestamp'] = turn['timestamp'].isoformat()
                # Process user response in turn
                if 'user_response' in turn and turn['user_response']:
                    if 'timestamp' in turn['user_response'] and isinstance(turn['user_response']['timestamp'], datetime):
                        turn['user_response']['timestamp'] = turn['user_response']['timestamp'].isoformat()
                # Process LLM logs in turn
                if 'llm_logs' in turn and turn['llm_logs']:
                    for log in turn['llm_logs']:
                        if 'timestamp' in log and isinstance(log['timestamp'], datetime):
                            log['timestamp'] = log['timestamp'].isoformat()

        return result

    def json(self, *args, **kwargs):
        """
        Custom JSON serialization that handles datetime objects.
        """
        return json.dumps(self.dict(*args, **kwargs), cls=DateTimeEncoder)

    def get_history_text(self) -> str:
        """
        Generates a text representation of the simulation history for context.

        Returns:
            A string containing the formatted simulation history.
        """
        history_text = ""

        for turn in self.turns:
            if turn.selected_scenario:
                history_text += f"TURN {turn.turn_number}:\n"
                history_text += f"SITUATION: {turn.selected_scenario.situation_description}\n"
                if turn.selected_scenario.user_role:
                    history_text += f"USER ROLE: {turn.selected_scenario.user_role}\n"
                if turn.selected_scenario.user_prompt:
                    history_text += f"USER PROMPT: {turn.selected_scenario.user_prompt}\n"

                if turn.user_response:
                    history_text += f"USER RESPONSE: {turn.user_response.response_text}\n\n"

        return history_text

    def add_scenarios(self, turn_number: int, scenarios: List[Scenario]) -> None:
        """
        Adds generated scenarios to the specified turn.

        Args:
            turn_number: The turn number to add scenarios to
            scenarios: List of scenario models to add
        """
        # Find or create the turn
        turn = next((t for t in self.turns if t.turn_number == turn_number), None)
        if not turn:
            turn = SimulationTurn(turn_number=turn_number)
            self.turns.append(turn)

        turn.scenarios = scenarios
        self.updated_at = datetime.now()

    def select_scenario(self, turn_number: int, scenario_id: str) -> None:
        """
        Selects a scenario for the specified turn.

        Args:
            turn_number: The turn number to select a scenario for
            scenario_id: The ID of the scenario to select
        """
        turn = next((t for t in self.turns if t.turn_number == turn_number), None)
        if turn and turn.scenarios:
            selected = next((s for s in turn.scenarios if s.id == scenario_id), None)
            if selected:
                turn.selected_scenario = selected
                self.updated_at = datetime.now()

    def add_user_response(self, turn_number: int, response_text: str) -> None:
        """
        Adds a user response to the specified turn.

        Args:
            turn_number: The turn number to add the response to
            response_text: The text of the user's response
        """
        turn = next((t for t in self.turns if t.turn_number == turn_number), None)
        if turn:
            turn.user_response = UserResponse(
                turn_number=turn_number,
                response_text=response_text
            )

            # If this isn't the last turn, increment the current turn
            if turn_number < self.max_turns:
                self.current_turn_number = turn_number + 1
            # Note: is_complete is set in simulation_service.py when processing final turn

            self.updated_at = datetime.now()

    def add_media_prompts(self, turn_number: int, video_prompt: Union[str, List[str]], narration_script: str) -> None:
        """
        Adds video and narration prompts to the specified turn.

        Args:
            turn_number: The turn number to add prompts to
            video_prompt: The prompt for video generation (can be a single string or list of strings)
            narration_script: The script for narration generation
        """
        turn = next((t for t in self.turns if t.turn_number == turn_number), None)
        if turn:
            turn.video_prompt = video_prompt
            turn.narration_script = narration_script
            self.updated_at = datetime.now()

    def add_media_urls(self, turn_number: int, video_urls: Optional[List[str]] = None, audio_url: Optional[str] = None) -> None:
        """
        Adds media URLs to the specified turn.

        Args:
            turn_number: The turn number to add URLs to
            video_urls: The URLs of the generated videos
            audio_url: The URL of the generated audio
        """
        turn = next((t for t in self.turns if t.turn_number == turn_number), None)
        if turn:
            if video_urls:
                turn.video_urls = video_urls
            if audio_url:
                turn.audio_url = audio_url
            self.updated_at = datetime.now()

    def add_llm_log(self, turn_number: int, llm_log: LLMLog) -> None:
        """
        Adds an LLM interaction log to the specified turn.

        Args:
            turn_number: The turn number to add the log to
            llm_log: The LLM log to add
        """
        turn = next((t for t in self.turns if t.turn_number == turn_number), None)
        if not turn:
            turn = SimulationTurn(turn_number=turn_number)
            self.turns.append(turn)

        turn.llm_logs.append(llm_log)
        self.updated_at = datetime.now()

class SimulationRequest(BaseModel):
    """Model for requesting a new simulation."""
    initial_prompt: Optional[str] = Field(None, max_length=500)
    developer_mode: bool = False  # Flag to enable developer mode
    difficulty: DifficultyLevel = DifficultyLevel.NORMAL  # Difficulty level for this simulation

    @field_validator("initial_prompt", mode="before")
    @classmethod
    def strip_control_chars_initial_prompt(cls, v: Optional[str]) -> Optional[str]:
        return _strip_control_chars(v)

class UserResponseRequest(BaseModel):
    """Model for submitting a user response."""
    response_text: str = Field(..., min_length=1, max_length=2000)

    @field_validator("response_text", mode="before")
    @classmethod
    def strip_control_chars_response_text(cls, v: str) -> str:
        return _strip_control_chars(v)

class DeveloperModeRequest(BaseModel):
    """Model for toggling developer mode."""
    enabled: bool


class DifficultyChangeRequest(BaseModel):
    """Model for changing difficulty level mid-game."""
    difficulty: DifficultyLevel
