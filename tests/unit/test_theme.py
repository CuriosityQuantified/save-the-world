"""Regression tests for issue #7: theme variations.

Theme is an orthogonal scenario-flavor modifier that mirrors the difficulty
feature (#5). Crucially, theme instructions must ONLY change scenario
setting/flavor and visual style — never grading — so difficulty stays balanced
across themes.
"""
import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.simulation import (
    ThemeType,
    SimulationState,
    SimulationRequest,
    ThemeChangeRequest,
)
from prompts.scenario_generation_prompt import (
    get_theme_instructions,
    THEME_INSTRUCTIONS,
)


REAL_THEMES = ("scifi", "historical", "business", "environmental", "political")


class TestThemeModel:
    def test_theme_enum_values(self):
        assert ThemeType.CLASSIC.value == "classic"
        assert ThemeType.SCIFI.value == "scifi"
        assert ThemeType.HISTORICAL.value == "historical"
        assert ThemeType.BUSINESS.value == "business"
        assert ThemeType.ENVIRONMENTAL.value == "environmental"
        assert ThemeType.POLITICAL.value == "political"

    def test_at_least_three_themes_beyond_default(self):
        # Acceptance criterion: at least 3 themes implemented (we have 5 + classic).
        non_classic = [t for t in ThemeType if t != ThemeType.CLASSIC]
        assert len(non_classic) >= 3

    def test_simulation_state_default_theme(self):
        sim = SimulationState()
        assert sim.theme == ThemeType.CLASSIC

    def test_simulation_request_default_theme(self):
        req = SimulationRequest()
        assert req.theme == ThemeType.CLASSIC

    def test_simulation_request_accepts_scifi(self):
        req = SimulationRequest(theme="scifi")
        assert req.theme == ThemeType.SCIFI

    def test_simulation_request_accepts_historical(self):
        req = SimulationRequest(theme="historical")
        assert req.theme == ThemeType.HISTORICAL

    def test_theme_change_request(self):
        req = ThemeChangeRequest(theme="environmental")
        assert req.theme == ThemeType.ENVIRONMENTAL

    def test_theme_and_difficulty_are_independent(self):
        # Theme must be orthogonal to difficulty: setting one doesn't touch the other.
        req = SimulationRequest(theme="business", difficulty="hard")
        assert req.theme == ThemeType.BUSINESS
        assert req.difficulty.value == "hard"


class TestThemeInstructions:
    def test_classic_has_no_override(self):
        instr = get_theme_instructions("classic")
        assert instr["scenario_flavor"] == ""
        assert instr["visual_style"] == ""

    def test_unknown_theme_falls_back_to_classic(self):
        instr = get_theme_instructions("unknown-theme")
        assert instr["scenario_flavor"] == ""
        assert instr["visual_style"] == ""

    @pytest.mark.parametrize("theme", REAL_THEMES)
    def test_real_theme_has_flavor_and_visual_style(self, theme):
        instr = get_theme_instructions(theme)
        assert instr["scenario_flavor"].strip() != ""
        assert instr["visual_style"].strip() != ""

    def test_all_real_themes_present_in_instructions(self):
        for theme in REAL_THEMES:
            assert theme in THEME_INSTRUCTIONS

    def test_balanced_difficulty_invariant_no_grading_language(self):
        """BALANCED DIFFICULTY: no theme instruction may contain grading/scoring
        language. Grading is governed solely by difficulty, so every theme must
        be equally hard/easy — the theme only changes setting and visuals."""
        forbidden = re.compile(
            r"\bscore\b|\bscores\b|\bscoring\b|\bgrade\b|\bgrading\b|\bpoints?\b|"
            r"below\s*50|\d{1,3}\s*[-–]\s*\d{1,3}\b|"
            r"\blenient\b|\bgenerous\b|\bharsh\b|\bstrict\b|\bpenali[sz]e\b",
            re.IGNORECASE,
        )
        for theme, instr in THEME_INSTRUCTIONS.items():
            for key in ("scenario_flavor", "visual_style"):
                text = instr.get(key, "")
                match = forbidden.search(text)
                assert match is None, (
                    f"Theme '{theme}' key '{key}' contains grading language "
                    f"'{match.group(0)}': grading must stay governed by difficulty only."
                )


class TestThemeOnSimulationState:
    def test_can_set_scifi_theme(self):
        sim = SimulationState()
        sim.theme = ThemeType.SCIFI
        assert sim.theme == ThemeType.SCIFI

    def test_theme_serializes_as_string(self):
        sim = SimulationState()
        sim.theme = ThemeType.HISTORICAL
        data = sim.dict()
        assert data["theme"] == "historical"

    def test_theme_round_trips_via_value(self):
        for theme in ("classic",) + REAL_THEMES:
            assert ThemeType(theme).value == theme


class TestThemeVideoPrompt:
    """Theme-appropriate media: create_video_prompt must inject the theme's
    visual style into the prompt forwarded to (and logged for) the LLM."""

    def _make_service(self):
        from services.llm_service import LLMService

        class MockHF:
            def __init__(self, *a, **k):
                pass

        return LLMService(api_key="fake", huggingface_service=MockHF())

    @pytest.mark.asyncio
    async def test_video_prompt_includes_theme_visual_style(self):
        service = self._make_service()
        service.log_interaction = AsyncMock()

        # Offline chain: mock the LLM instance and the LLMChain used inside.
        fake_chain = MagicMock()
        fake_chain.arun = AsyncMock(
            return_value='{"scenes": ["a", "b", "c", "d"]}'
        )

        visual_style = get_theme_instructions("scifi")["visual_style"]

        with patch.object(service, "_get_llm_instance", return_value=MagicMock()), \
             patch("services.llm_service.LLMChain", return_value=fake_chain):
            scenes = await service.create_video_prompt(
                {"situation_description": "A crisis unfolds."},
                turn_number=1,
                theme="scifi",
            )

        assert scenes == ["a", "b", "c", "d"]

        # The visual style must reach the LLM chain input.
        chain_kwargs = fake_chain.arun.call_args.kwargs
        forwarded = chain_kwargs.get("scenario", "")
        assert visual_style in forwarded, (
            "Theme visual style must be forwarded to the video-prompt LLM chain."
        )

        # And it must appear in the logged prompt for observability.
        logged_prompt = service.log_interaction.call_args.args[2]
        assert visual_style in logged_prompt

    @pytest.mark.asyncio
    async def test_classic_theme_adds_no_visual_style(self):
        service = self._make_service()
        service.log_interaction = AsyncMock()

        fake_chain = MagicMock()
        fake_chain.arun = AsyncMock(
            return_value='{"scenes": ["a", "b", "c", "d"]}'
        )

        with patch.object(service, "_get_llm_instance", return_value=MagicMock()), \
             patch("services.llm_service.LLMChain", return_value=fake_chain):
            await service.create_video_prompt(
                {"situation_description": "A crisis unfolds."},
                turn_number=1,
                theme="classic",
            )

        forwarded = fake_chain.arun.call_args.kwargs.get("scenario", "")
        assert "THEME VISUAL STYLE" not in forwarded


class TestThemeScenarioFlavor:
    """Consistent narrative within themes: create_idea must inject the theme's
    scenario_flavor into the prompt forwarded to the scenario-generation LLM."""

    def _make_service(self):
        from services.llm_service import LLMService

        class MockHF:
            def __init__(self, *a, **k):
                pass

        return LLMService(api_key="fake", huggingface_service=MockHF())

    @pytest.mark.asyncio
    async def test_scenario_flavor_reaches_llm_input(self):
        service = self._make_service()
        service.log_interaction = AsyncMock()

        fake_chain = MagicMock()
        fake_chain.arun = AsyncMock(return_value="{}")  # parsing result is irrelevant

        flavor = get_theme_instructions("scifi")["scenario_flavor"]

        with patch.object(service, "_get_llm_instance", return_value=MagicMock()), \
             patch("services.llm_service.LLMChain", return_value=fake_chain):
            await service.create_idea({"current_turn_number": 1, "theme": "scifi"})

        forwarded = fake_chain.arun.call_args.kwargs.get("prompt", "")
        assert flavor in forwarded, (
            "Theme scenario flavor must be forwarded to the scenario-generation LLM."
        )

    @pytest.mark.asyncio
    async def test_classic_theme_adds_no_scenario_flavor(self):
        service = self._make_service()
        service.log_interaction = AsyncMock()

        fake_chain = MagicMock()
        fake_chain.arun = AsyncMock(return_value="{}")

        with patch.object(service, "_get_llm_instance", return_value=MagicMock()), \
             patch("services.llm_service.LLMChain", return_value=fake_chain):
            await service.create_idea({"current_turn_number": 1, "theme": "classic"})

        forwarded = fake_chain.arun.call_args.kwargs.get("prompt", "")
        assert "THEME (setting)" not in forwarded
