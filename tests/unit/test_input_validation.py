"""
Tests for input length validation (issue #15).

Covers:
  - UserResponseRequest: max_length=2000, min_length=1, required field, control char stripping
  - SimulationRequest: max_length=500 on initial_prompt, optional field
  - Control char stripping: ASCII banned range + Unicode bidi/ZWJ chars
  - Strip-before-length-check ordering: control chars stripped before max_length is evaluated
  - API boundary: POST /api/simulations returns 422 when initial_prompt > 500 chars
  - API boundary: POST /api/simulations/{id}/respond returns 422 when response_text > 2000 chars
  - API boundary: POST /api/simulations/{id}/respond with exactly 2000-char response is accepted
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from api.routes import router, get_simulation_service
from models.simulation import (
    SimulationRequest,
    SimulationState,
    UserResponseRequest,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sim(sim_id: str = "sim_abc123") -> SimulationState:
    return SimulationState(simulation_id=sim_id)


def _make_sim_service(sim: SimulationState) -> MagicMock:
    """Return a mock SimulationService suitable for respond-endpoint tests."""
    svc = MagicMock()
    svc.state_service.get_simulation.return_value = sim
    # process_user_response is async
    svc.process_user_response = AsyncMock(return_value=sim)
    # create_new_simulation is async
    svc.create_new_simulation = AsyncMock(return_value=sim)
    return svc


def _make_client(sim_service) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_simulation_service] = lambda: sim_service
    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# Unit tests: UserResponseRequest (Pydantic model)
# ---------------------------------------------------------------------------

class TestUserResponseRequest:
    def test_accepts_exactly_2000_chars(self):
        text = "a" * 2000
        req = UserResponseRequest(response_text=text)
        assert len(req.response_text) == 2000

    def test_rejects_response_text_longer_than_2000(self):
        text = "a" * 2001
        with pytest.raises(ValidationError):
            UserResponseRequest(response_text=text)

    def test_rejects_missing_response_text(self):
        with pytest.raises(ValidationError):
            UserResponseRequest()

    def test_rejects_empty_response_text(self):
        # min_length=1: empty string must be rejected
        with pytest.raises(ValidationError):
            UserResponseRequest(response_text="")

    def test_strips_control_characters_from_response_text(self):
        # ASCII 0x01 (SOH) and 0x0E (SO) should be stripped;
        # tab (0x09), newline (0x0A), CR (0x0D) should survive.
        raw = "hello\x01world\x0E\tthere\nnew\rline"
        req = UserResponseRequest(response_text=raw)
        assert "\x01" not in req.response_text
        assert "\x0E" not in req.response_text
        # Allowed characters preserved
        assert "\t" in req.response_text
        assert "\n" in req.response_text
        assert "\r" in req.response_text

    def test_all_banned_control_chars_stripped(self):
        # Verify the full banned range 0x00-0x08 and 0x0B-0x0C and 0x0E-0x1F
        banned = "".join(chr(i) for i in range(0x00, 0x09))  # 0x00-0x08
        banned += chr(0x0B) + chr(0x0C)
        banned += "".join(chr(i) for i in range(0x0E, 0x20))  # 0x0E-0x1F
        raw = "start" + banned + "end"
        req = UserResponseRequest(response_text=raw)
        assert req.response_text == "startend"

    def test_allowed_control_chars_preserved(self):
        raw = "tab\there\nnewline\rcarriage"
        req = UserResponseRequest(response_text=raw)
        assert req.response_text == raw

    def test_strips_unicode_bidi_override(self):
        # U+202E right-to-left override is a common prompt injection char
        raw = "‮malicious instructions"
        req = UserResponseRequest(response_text=raw)
        assert "‮" not in req.response_text
        assert "malicious instructions" in req.response_text

    def test_strips_zero_width_space(self):
        # U+200B zero-width space — used to split filter-matching strings
        raw = "hel​lo"
        req = UserResponseRequest(response_text=raw)
        assert "​" not in req.response_text
        assert "hello" == req.response_text

    def test_strips_bom(self):
        # U+FEFF byte-order mark
        raw = "﻿hello"
        req = UserResponseRequest(response_text=raw)
        assert "﻿" not in req.response_text
        assert "hello" == req.response_text

    def test_strip_before_length_check_ordering(self):
        # 2001 chars where 1 is a control char → stripped to 2000 → must pass max_length
        # This verifies mode="before" validator runs before the max_length constraint.
        text = "a" * 2000 + "\x01"
        req = UserResponseRequest(response_text=text)
        assert len(req.response_text) == 2000

    def test_all_control_chars_stripped_leaves_empty_string_rejected(self):
        # All-control-char input strips to "" which must be rejected by min_length=1
        all_banned = "\x01\x02\x03"
        with pytest.raises(ValidationError):
            UserResponseRequest(response_text=all_banned)


# ---------------------------------------------------------------------------
# Unit tests: SimulationRequest (Pydantic model)
# ---------------------------------------------------------------------------

class TestSimulationRequest:
    def test_accepts_none_initial_prompt(self):
        req = SimulationRequest(initial_prompt=None)
        assert req.initial_prompt is None

    def test_accepts_exactly_500_char_initial_prompt(self):
        prompt = "b" * 500
        req = SimulationRequest(initial_prompt=prompt)
        assert len(req.initial_prompt) == 500

    def test_rejects_initial_prompt_longer_than_500(self):
        prompt = "b" * 501
        with pytest.raises(ValidationError):
            SimulationRequest(initial_prompt=prompt)

    def test_missing_initial_prompt_defaults_to_none(self):
        # initial_prompt is Optional with default None; omitting it should not raise
        req = SimulationRequest()
        assert req.initial_prompt is None

    def test_strips_control_characters_from_initial_prompt(self):
        raw = "save\x01the\x0Eworld"
        req = SimulationRequest(initial_prompt=raw)
        assert "\x01" not in req.initial_prompt
        assert "\x0E" not in req.initial_prompt
        assert "savetheworld" == req.initial_prompt

    def test_none_initial_prompt_does_not_trigger_validator_error(self):
        # Explicitly passing None must not raise
        req = SimulationRequest(initial_prompt=None, developer_mode=False)
        assert req.initial_prompt is None


# ---------------------------------------------------------------------------
# API boundary tests (FastAPI TestClient)
# ---------------------------------------------------------------------------

class TestCreateSimulationAPI:
    """POST /api/simulations"""

    def test_initial_prompt_over_500_chars_returns_422(self):
        sim = _make_sim()
        client = _make_client(_make_sim_service(sim))
        long_prompt = "x" * 501
        res = client.post("/api/simulations", json={"initial_prompt": long_prompt})
        assert res.status_code == 422

    def test_initial_prompt_exactly_500_chars_accepted(self):
        sim = _make_sim()
        client = _make_client(_make_sim_service(sim))
        prompt = "x" * 500
        res = client.post("/api/simulations", json={"initial_prompt": prompt})
        assert res.status_code == 201

    def test_no_initial_prompt_accepted(self):
        sim = _make_sim()
        client = _make_client(_make_sim_service(sim))
        res = client.post("/api/simulations", json={})
        assert res.status_code == 201


class TestSubmitResponseAPI:
    """POST /api/simulations/{id}/respond"""

    def test_response_text_over_2000_chars_returns_422(self):
        sim = _make_sim("sim_test1")
        client = _make_client(_make_sim_service(sim))
        long_text = "y" * 2001
        res = client.post("/api/simulations/sim_test1/respond", json={"response_text": long_text})
        assert res.status_code == 422

    def test_response_text_exactly_2000_chars_accepted(self):
        sim = _make_sim("sim_test2")
        client = _make_client(_make_sim_service(sim))
        text = "y" * 2000
        res = client.post("/api/simulations/sim_test2/respond", json={"response_text": text})
        assert res.status_code == 200

    def test_missing_response_text_returns_422(self):
        sim = _make_sim("sim_test3")
        client = _make_client(_make_sim_service(sim))
        res = client.post("/api/simulations/sim_test3/respond", json={})
        assert res.status_code == 422
