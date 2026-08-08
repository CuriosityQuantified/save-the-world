"""Regression tests for issue #5: difficulty levels."""
import pytest
from models.simulation import DifficultyLevel, SimulationState, SimulationRequest, DifficultyChangeRequest
from prompts.scenario_generation_prompt import get_difficulty_instructions


class TestDifficultyModel:
    def test_difficulty_enum_values(self):
        assert DifficultyLevel.EASY.value == "easy"
        assert DifficultyLevel.NORMAL.value == "normal"
        assert DifficultyLevel.HARD.value == "hard"

    def test_simulation_state_default_difficulty(self):
        sim = SimulationState()
        assert sim.difficulty == DifficultyLevel.NORMAL

    def test_simulation_request_default_difficulty(self):
        req = SimulationRequest()
        assert req.difficulty == DifficultyLevel.NORMAL

    def test_simulation_request_accepts_easy(self):
        req = SimulationRequest(difficulty="easy")
        assert req.difficulty == DifficultyLevel.EASY

    def test_simulation_request_accepts_hard(self):
        req = SimulationRequest(difficulty="hard")
        assert req.difficulty == DifficultyLevel.HARD

    def test_difficulty_change_request(self):
        req = DifficultyChangeRequest(difficulty="hard")
        assert req.difficulty == DifficultyLevel.HARD


class TestDifficultyInstructions:
    def test_easy_grading_is_lenient(self):
        instr = get_difficulty_instructions("easy")
        assert "generous" in instr["grading_instructions"].lower() or "encouraging" in instr["grading_instructions"].lower()

    def test_hard_grading_is_strict(self):
        instr = get_difficulty_instructions("hard")
        assert "below 50" in instr["grading_instructions"] or "strict" in instr["grading_instructions"].lower() or "harsh" in instr["grading_instructions"].lower()

    def test_normal_has_no_override(self):
        instr = get_difficulty_instructions("normal")
        assert instr["grading_instructions"] == ""

    def test_unknown_difficulty_falls_back_to_normal(self):
        instr = get_difficulty_instructions("unknown")
        assert instr["grading_instructions"] == ""

    def test_easy_has_scenario_complexity(self):
        instr = get_difficulty_instructions("easy")
        assert instr["scenario_complexity"] != ""

    def test_hard_has_scenario_complexity(self):
        instr = get_difficulty_instructions("hard")
        assert instr["scenario_complexity"] != ""

    def test_normal_has_no_scenario_complexity(self):
        instr = get_difficulty_instructions("normal")
        assert instr["scenario_complexity"] == ""


class TestDifficultyOnSimulationState:
    def test_can_set_easy_difficulty(self):
        sim = SimulationState()
        sim.difficulty = DifficultyLevel.EASY
        assert sim.difficulty == DifficultyLevel.EASY

    def test_difficulty_serializes_as_string(self):
        sim = SimulationState()
        sim.difficulty = DifficultyLevel.HARD
        data = sim.dict()
        assert data["difficulty"] == "hard"

    def test_difficulty_round_trips_via_value(self):
        """DifficultyLevel(value) must reconstruct the enum correctly."""
        for level in ("easy", "normal", "hard"):
            assert DifficultyLevel(level).value == level
