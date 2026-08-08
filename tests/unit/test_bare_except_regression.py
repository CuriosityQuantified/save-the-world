"""
Regression tests for issue #17: bare except swallows BaseException.

The old recovery block in process_user_response used a bare `except: pass`
which silently ate KeyboardInterrupt, SystemExit, and GeneratorExit. It also
used `return simulation` inside the recovery try, meaning the outer `raise`
could never execute -- the original exception was swallowed.

The fix:
  1. Change `except:` to `except Exception:` so BaseException subclasses propagate.
  2. Remove `return simulation` from the recovery block so `raise` always executes.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from models.simulation import SimulationState
from services.simulation_service import SimulationService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service(state_service):
    """Build a SimulationService with the given state_service and mocked LLM/media."""
    llm_service = MagicMock()
    llm_service.set_log_callback = MagicMock()
    # Suppress the Langfuse branch so it doesn't interfere
    del llm_service.current_session_id
    media_service = MagicMock()
    return SimulationService(
        llm_service=llm_service,
        state_service=state_service,
        media_service=media_service,
    )


def _make_state_service(sim, update_side_effect):
    """Wire up a state_service mock that returns `sim` and applies the side effect."""
    state_service = MagicMock()
    state_service.get_simulation.return_value = sim
    state_service.update_simulation.side_effect = update_side_effect
    return state_service


def _stub_create_idea(svc):
    """Stub the async create_idea call so no real LLM request is made."""
    svc.llm_service.create_idea = AsyncMock(return_value={
        "id": "s1",
        "situation_description": "desc",
        "rationale": "r",
        "user_role": "Director",
        "user_prompt": "Act",
    })


# ---------------------------------------------------------------------------
# Test 1: recovery-path saves before re-raise
#
# Strategy: make state_service.update_simulation raise a plain RuntimeError
# on its FIRST call (line ~311, the one BEFORE the inner try block). This
# ensures the outer `except Exception as e:` fires, which triggers the
# recovery path that calls update_simulation a second time (inside the inner
# try of the recovery block). We verify that second call happens and that
# the original exception is re-raised.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_recovery_path_saves_before_reraise():
    """
    When process_user_response raises an unexpected Exception (outside the
    inner scenario-generation try), the recovery path must call
    update_simulation before re-raising. The original exception must be
    re-raised (not swallowed by a return).
    """
    sim = SimulationState()

    boom = RuntimeError("unexpected outer failure")
    recovery_calls = []

    call_count = [0]

    def update_side_effect(s):
        call_count[0] += 1
        if call_count[0] == 1:
            # First call (outer try body, before inner try) — raise to trigger
            # the outer except block
            raise boom
        # Second call (the recovery path inside outer except) — record it
        recovery_calls.append(s)

    svc = _make_service(_make_state_service(sim, update_side_effect))

    # Prevent async LLM calls from running (they come after the first
    # update_simulation in the outer try, so they won't be reached, but
    # mock them defensively)
    _stub_create_idea(svc)

    with pytest.raises(RuntimeError, match="unexpected outer failure"):
        await svc.process_user_response(sim.simulation_id, "some response")

    # The recovery block must have attempted to save the simulation state
    assert len(recovery_calls) >= 1, (
        "update_simulation was NOT called during recovery — "
        "the simulation state was not saved before re-raise"
    )
    assert recovery_calls[0] is sim, (
        "update_simulation in recovery was called with the wrong object"
    )


# ---------------------------------------------------------------------------
# Test 2: KeyboardInterrupt is NOT swallowed by the recovery block
#
# Strategy: same as above, but now the RECOVERY call to update_simulation
# (second call) raises KeyboardInterrupt. With `except Exception:` this
# propagates; with the old `except:` it would be silently swallowed and
# the outer `raise` would then re-raise the original RuntimeError, but the
# KeyboardInterrupt itself would be lost. We verify KeyboardInterrupt escapes.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_keyboard_interrupt_not_swallowed():
    """
    A KeyboardInterrupt raised inside the recovery block must NOT be caught
    by `except Exception:` -- it must propagate out.
    """
    sim = SimulationState()

    call_count = [0]

    def update_side_effect(s):
        call_count[0] += 1
        if call_count[0] == 1:
            # Trigger the outer except block
            raise RuntimeError("trigger outer except")
        # In the recovery block: raise KeyboardInterrupt
        raise KeyboardInterrupt("SIGINT during recovery save")

    svc = _make_service(_make_state_service(sim, update_side_effect))
    _stub_create_idea(svc)

    # With the fix: `except Exception:` does NOT catch KeyboardInterrupt, so
    # the recovery signal itself must escape rather than being replaced by the
    # original RuntimeError.
    with pytest.raises(KeyboardInterrupt, match="SIGINT during recovery save"):
        await svc.process_user_response(sim.simulation_id, "some response")


# ---------------------------------------------------------------------------
# Test 3: SystemExit is NOT swallowed by the recovery block
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_system_exit_not_swallowed():
    """
    A SystemExit raised inside the recovery block must NOT be caught
    by `except Exception:` -- it must propagate out.
    """
    sim = SimulationState()

    call_count = [0]

    def update_side_effect(s):
        call_count[0] += 1
        if call_count[0] == 1:
            raise RuntimeError("trigger outer except")
        raise SystemExit(1)

    svc = _make_service(_make_state_service(sim, update_side_effect))
    _stub_create_idea(svc)

    with pytest.raises(SystemExit) as exc_info:
        await svc.process_user_response(sim.simulation_id, "some response")

    assert exc_info.value.code == 1
