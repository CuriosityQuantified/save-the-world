"""Regression tests for issue #24: migrate LLMChain -> LCEL pipe syntax.

`LLMChain` is deprecated in LangChain 0.2.x and removed in 0.3.x. This suite
locks in the acceptance criteria for the migration:

1. Neither `services/llm_service.py` nor `services/simulation_service.py`
   references the deprecated `LLMChain` class or the `.arun(` call form; the
   LCEL `.ainvoke(` form is used instead.
2. `create_idea` drives the LLM through an offline-mocked LCEL chain
   (`prompt | llm | StrOutputParser()`) and still returns a parsed dict.
3. `create_video_prompt` drives the LLM through an offline-mocked LCEL chain
   and still returns its parsed structure.
4. The requirements files no longer pin the pre-0.3 `langchain==0.2` line.

All LLM interaction is mocked offline via `_get_llm_instance`, so no network
call is ever made.
"""

import inspect
import json
import re
from pathlib import Path

import pytest
from unittest.mock import AsyncMock, patch

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

import services.llm_service as llm_service_module
import services.simulation_service as simulation_service_module
from services.llm_service import LLMService


REPO_ROOT = Path(__file__).resolve().parents[2]


class MockHF:
    def __init__(self, *a, **k):
        pass


def _make_service():
    return LLMService(api_key="fake", huggingface_service=MockHF())


def _fake_llm(canned_output):
    """Offline LCEL LLM stand-in: prompt | fake | StrOutputParser() -> canned_output."""
    return RunnableLambda(lambda _prompt_value: AIMessage(content=canned_output))


# --- Criterion 1: no LLMChain / no .arun( in migrated modules -----------------


@pytest.mark.parametrize(
    "module", [llm_service_module, simulation_service_module],
    ids=["llm_service", "simulation_service"],
)
def test_module_source_has_no_llmchain(module):
    source = inspect.getsource(module)
    assert "LLMChain" not in source, (
        f"{module.__name__} still references the deprecated LLMChain"
    )


def test_llm_service_uses_lcel_not_arun():
    source = inspect.getsource(llm_service_module)
    assert ".arun(" not in source, "llm_service still calls the deprecated chain.arun(...)"
    assert ".ainvoke(" in source, "llm_service should drive LCEL chains via .ainvoke(...)"
    assert "StrOutputParser" in source, (
        "llm_service should use StrOutputParser to preserve the string return of LCEL chains"
    )


def test_llm_service_imports_prompttemplate_from_core():
    source = inspect.getsource(llm_service_module)
    assert "from langchain_core.prompts import PromptTemplate" in source
    # The deprecated import path must be gone.
    assert "from langchain.prompts import PromptTemplate" not in source
    assert "from langchain.chains import LLMChain" not in source


# --- Criterion 2: create_idea via offline LCEL mock returns a dict ------------


@pytest.mark.asyncio
async def test_create_idea_lcel_offline_returns_dict():
    service = _make_service()
    service.log_callback = AsyncMock()

    final_turn_context = {
        "simulation_history": "History...",
        "current_turn_number": 6,
        "max_turns": 6,
        "previous_turn_number": 5,
        "user_prompt_for_this_turn": "Final response",
    }
    payload = {
        "situation_description": "LCEL migration works.",
        "rationale": "Because the pipe composes.",
        "grade": 88,
        "grade_explanation": "Solid.",
    }
    messy = f"```json\n{json.dumps(payload)}\n```"

    with patch.object(service, "_get_llm_instance", return_value=_fake_llm(messy)):
        result = await service.create_idea(final_turn_context)

    assert isinstance(result, dict), "create_idea should return a parsed dict"
    assert result["situation_description"] == payload["situation_description"]
    assert result["grade"] == payload["grade"]
    assert "id" in result


# --- Criterion 3: create_video_prompt via offline LCEL mock -------------------


@pytest.mark.asyncio
async def test_create_video_prompt_lcel_offline_returns_scenes():
    service = _make_service()
    service.log_interaction = AsyncMock()

    canned = '{"scenes": ["s1", "s2", "s3", "s4"]}'
    with patch.object(service, "_get_llm_instance", return_value=_fake_llm(canned)):
        scenes = await service.create_video_prompt(
            {"situation_description": "A crisis unfolds."},
            turn_number=1,
            theme="classic",
        )

    assert scenes == ["s1", "s2", "s3", "s4"]


# --- Criterion 4: requirements no longer pin langchain 0.2 --------------------


@pytest.mark.parametrize(
    "req_name", ["requirements.txt", "requirements-prod.txt"],
)
def test_requirements_not_pinned_to_langchain_0_2(req_name):
    text = (REPO_ROOT / req_name).read_text()
    # Find an actual langchain meta-package pin line (not langchain-core etc.,
    # not comments).
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("#") or not line:
            continue
        m = re.match(r"^langchain==([0-9]+\.[0-9]+)", line)
        if m:
            assert m.group(1) != "0.2", (
                f"{req_name} still pins the removed-LLMChain langchain==0.2 line: {line}"
            )
            # Any explicit pin must be >= 0.3.
            major, minor = (int(x) for x in m.group(1).split("."))
            assert (major, minor) >= (0, 3), (
                f"{req_name} pins langchain below 0.3: {line}"
            )
