"""
Tests for WebSocket functionality.
"""

import pytest
from fastapi.testclient import TestClient

from smallworld.api.app import app, manager


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestWebSocket:
    """Tests for WebSocket endpoint."""

    def test_websocket_connect(self, client):
        """Test WebSocket connection."""
        with client.websocket_connect("/ws") as websocket:
            # Connection should be established
            assert websocket is not None

    def test_websocket_echo(self, client):
        """Test WebSocket message echo."""
        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("hello")
            data = websocket.receive_json()
            assert data["type"] == "ack"
            assert data["data"] == "hello"

    def test_websocket_multiple_messages(self, client):
        """Test multiple WebSocket messages."""
        with client.websocket_connect("/ws") as websocket:
            messages = ["msg1", "msg2", "msg3"]
            for msg in messages:
                websocket.send_text(msg)
                data = websocket.receive_json()
                assert data["type"] == "ack"
                assert data["data"] == msg


class TestConnectionManager:
    """Tests for ConnectionManager."""

    def test_manager_exists(self):
        """Test manager is initialized."""
        assert manager is not None
        assert hasattr(manager, "active_connections")
        assert hasattr(manager, "connect")
        assert hasattr(manager, "disconnect")
        assert hasattr(manager, "broadcast")

    @pytest.mark.asyncio
    async def test_broadcast_empty(self):
        """Test broadcast with no connections."""
        # Should not raise
        await manager.broadcast({"type": "test"})
