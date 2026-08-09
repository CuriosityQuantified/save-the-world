"""
Regression tests for issue #19: WebSocket connections leak on abnormal disconnect.

The old websocket_endpoint only cleaned up `active_connections` inside the
`except WebSocketDisconnect:` block. Any other exception (RuntimeError,
ConnectionResetError, etc.) bypassed cleanup, leaving stale WebSocket objects
in the dict and causing unbounded growth.

The fix:
  1. Catch `(WebSocketDisconnect, Exception)` in the except clause (suppresses
     receive-loop errors without re-raising).
  2. Move cleanup into a `finally:` block so it always runs, regardless of
     which exception (if any) exits the receive loop.
  3. Be defensive: only remove if simulation_id is still in active_connections
     AND the websocket is still in the list.
"""

from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import WebSocketDisconnect


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_websocket(receive_side_effect):
    """
    Return a mock WebSocket whose receive_text() raises the given exception
    (or, if it's an async iterable of side effects, cycles through them).
    """
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()
    ws.receive_text = AsyncMock(side_effect=receive_side_effect)
    return ws


def _make_simulation_service(simulation_id="sim-test-1"):
    """Return a SimulationService mock that reports a simulation as existing."""
    sim = MagicMock()
    sim.dict.return_value = {"simulation_id": simulation_id}

    state_service = MagicMock()
    state_service.get_simulation.return_value = sim

    svc = MagicMock()
    svc.state_service = state_service
    return svc


# ---------------------------------------------------------------------------
# Import the handler and the shared dict under test
# ---------------------------------------------------------------------------

# We import `active_connections` and `websocket_endpoint` from api.routes.
# Because `active_connections` is a module-level dict we can inspect directly.

import api.routes as routes_module
from api.routes import websocket_endpoint


# ---------------------------------------------------------------------------
# Test 1: Normal WebSocketDisconnect still cleans up (sanity check)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cleanup_on_normal_websocket_disconnect():
    """Cleanup must run when the receive loop exits via WebSocketDisconnect."""
    sim_id = "sim-disconnect-normal"
    ws = _make_websocket(WebSocketDisconnect(code=1001))
    svc = _make_simulation_service(sim_id)

    # Ensure the dict is clean before the test
    routes_module.active_connections.pop(sim_id, None)

    await websocket_endpoint(websocket=ws, simulation_id=sim_id, simulation_service=svc)

    assert sim_id not in routes_module.active_connections, (
        "active_connections entry must be deleted after a normal WebSocketDisconnect"
    )


# ---------------------------------------------------------------------------
# Test 2: RuntimeError during receive still cleans up (the bug case)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cleanup_on_runtime_error():
    """
    Cleanup must run even when the receive loop exits via RuntimeError
    (not WebSocketDisconnect).  This was the leak path in the original code.
    """
    sim_id = "sim-runtime-error"
    ws = _make_websocket(RuntimeError("network blew up"))
    svc = _make_simulation_service(sim_id)

    routes_module.active_connections.pop(sim_id, None)

    await websocket_endpoint(websocket=ws, simulation_id=sim_id, simulation_service=svc)

    assert sim_id not in routes_module.active_connections, (
        "active_connections entry must be deleted after a RuntimeError in the receive loop"
    )


# ---------------------------------------------------------------------------
# Test 3: ConnectionResetError during receive still cleans up
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cleanup_on_connection_reset_error():
    """
    Cleanup must run when the receive loop exits via ConnectionResetError
    (client crash / network reset).
    """
    sim_id = "sim-connection-reset"
    ws = _make_websocket(ConnectionResetError("connection reset by peer"))
    svc = _make_simulation_service(sim_id)

    routes_module.active_connections.pop(sim_id, None)

    await websocket_endpoint(websocket=ws, simulation_id=sim_id, simulation_service=svc)

    assert sim_id not in routes_module.active_connections, (
        "active_connections entry must be deleted after a ConnectionResetError"
    )


# ---------------------------------------------------------------------------
# Test 4: Dict entry fully deleted when it's the last connection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dict_entry_deleted_when_last_connection():
    """
    When the disconnecting WebSocket was the only connection for a simulation,
    the simulation_id key must be fully removed from active_connections (not
    left pointing at an empty list).
    """
    sim_id = "sim-last-conn"
    ws = _make_websocket(WebSocketDisconnect(code=1000))
    svc = _make_simulation_service(sim_id)

    routes_module.active_connections.pop(sim_id, None)

    await websocket_endpoint(websocket=ws, simulation_id=sim_id, simulation_service=svc)

    assert sim_id not in routes_module.active_connections, (
        "The simulation_id key must be fully removed when no connections remain"
    )


# ---------------------------------------------------------------------------
# Test 5: Only the disconnecting websocket is removed when others remain
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_only_disconnecting_ws_removed_when_others_remain():
    """
    When multiple WebSockets share a simulation, only the one that disconnected
    should be removed; the others must remain.
    """
    sim_id = "sim-multi-conn"
    ws_closing = _make_websocket(WebSocketDisconnect(code=1001))
    ws_other = MagicMock()  # a sibling connection that stays open
    svc = _make_simulation_service(sim_id)

    # Pre-populate with just the other connection.  The handler will append
    # ws_closing itself (lines 381-383 of routes.py), so we must NOT add it
    # here to avoid a double-entry that would confuse list.remove().
    routes_module.active_connections[sim_id] = [ws_other]

    # Run the handler for the closing socket
    await websocket_endpoint(websocket=ws_closing, simulation_id=sim_id, simulation_service=svc)

    # The key must still exist because ws_other is still connected
    assert sim_id in routes_module.active_connections, (
        "simulation_id key was deleted even though another connection is still alive"
    )
    remaining = routes_module.active_connections[sim_id]
    assert ws_closing not in remaining, (
        "The disconnecting websocket must be removed from active_connections"
    )
    assert ws_other in remaining, (
        "The still-active websocket must remain in active_connections"
    )

    # Clean up after ourselves
    routes_module.active_connections.pop(sim_id, None)
