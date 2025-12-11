"""Additional transport tests for coverage."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from code_forge.mcp.transport.http import HTTPTransport
from code_forge.mcp.transport.stdio import StdioTransport


class TestHTTPTransportCoverage:
    """Coverage tests for HTTPTransport."""

    @pytest.mark.asyncio
    async def test_send_with_mocked_aiohttp(self) -> None:
        """Test send with mocked aiohttp."""
        transport = HTTPTransport(url="http://localhost:8080")

        # Mock aiohttp module
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value={"result": "ok"})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.close = AsyncMock()

        transport._session = mock_session
        transport._connected = True

        await transport.send({"method": "test"})

        # Verify the message was queued
        assert not transport._message_queue.empty()
        result = await transport._message_queue.get()
        assert result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_send_with_client_error(self) -> None:
        """Test send when client error occurs."""
        transport = HTTPTransport(url="http://localhost:8080")

        # Import aiohttp to create proper error
        import aiohttp

        mock_response = MagicMock()
        mock_response.__aenter__ = AsyncMock(
            side_effect=aiohttp.ClientError("Connection failed")
        )
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.close = AsyncMock()

        transport._session = mock_session
        transport._connected = True

        with pytest.raises(ConnectionError, match="HTTP request failed"):
            await transport.send({"method": "test"})

    @pytest.mark.asyncio
    async def test_send_with_generic_error(self) -> None:
        """Test send when generic error occurs."""
        transport = HTTPTransport(url="http://localhost:8080")

        mock_response = MagicMock()
        mock_response.__aenter__ = AsyncMock(side_effect=Exception("Unknown error"))
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.close = AsyncMock()

        transport._session = mock_session
        transport._connected = True

        with pytest.raises(ConnectionError, match="Send failed"):
            await transport.send({"method": "test"})

    @pytest.mark.asyncio
    async def test_receive_with_message(self) -> None:
        """Test receive with queued message."""
        transport = HTTPTransport(url="http://localhost:8080")
        transport._connected = True

        # Put a message in the queue
        await transport._message_queue.put({"result": "test"})

        result = await transport.receive()
        assert result == {"result": "test"}

    @pytest.mark.asyncio
    async def test_connect_health_check_fails(self) -> None:
        """Test connect when health check fails (should still work)."""
        transport = HTTPTransport(url="http://localhost:8080")

        import aiohttp

        mock_response = MagicMock()
        mock_response.__aenter__ = AsyncMock(
            side_effect=aiohttp.ClientError("Health check failed")
        )
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.close = AsyncMock()

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with patch("aiohttp.ClientTimeout"):
                # Health check failure should not prevent connection
                await transport.connect()
                assert transport._connected is True

                await transport.disconnect()

    @pytest.mark.asyncio
    async def test_connect_exception_cleanup(self) -> None:
        """Test connect cleans up on exception."""
        transport = HTTPTransport(url="http://localhost:8080")

        import aiohttp

        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=Exception("Connection failed"))
        mock_session.close = AsyncMock()

        with patch("aiohttp.ClientTimeout"):
            with patch("aiohttp.ClientSession", return_value=mock_session):
                with pytest.raises(ConnectionError, match="Failed to connect"):
                    await transport.connect()

                # Session should be cleaned up
                mock_session.close.assert_called()

    @pytest.mark.asyncio
    async def test_listen_sse_no_session(self) -> None:
        """Test SSE listener returns early if no session."""
        transport = HTTPTransport(url="http://localhost:8080")
        transport._session = None

        # Should return immediately without error
        await transport._listen_sse()

    @pytest.mark.asyncio
    async def test_listen_sse_closing_flag(self) -> None:
        """Test SSE listener respects closing flag."""
        transport = HTTPTransport(url="http://localhost:8080")
        transport._closing = True

        # Create mock that returns one line then stops
        class MockContent:
            def __init__(self) -> None:
                self.called = False

            def __aiter__(self) -> "MockContent":
                return self

            async def __anext__(self) -> bytes:
                if self.called:
                    raise StopAsyncIteration
                self.called = True
                return b"data: test\n"

        mock_response = MagicMock()
        mock_response.content = MockContent()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        transport._session = mock_session

        # Should return quickly due to _closing flag
        await transport._listen_sse()


class TestStdioTransportCoverage:
    """Coverage tests for StdioTransport."""

    @pytest.mark.asyncio
    async def test_connect_permission_error(self) -> None:
        """Test connect with permission error."""
        transport = StdioTransport(command="/sbin/nologin")

        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=PermissionError("Permission denied"),
        ):
            with pytest.raises(ConnectionError, match="Permission denied"):
                await transport.connect()

    @pytest.mark.asyncio
    async def test_connect_generic_error(self) -> None:
        """Test connect with generic error."""
        transport = StdioTransport(command="test-cmd")

        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=Exception("Unknown error"),
        ):
            with pytest.raises(ConnectionError, match="Failed to start"):
                await transport.connect()

    @pytest.mark.asyncio
    async def test_connect_process_exits_immediately(self) -> None:
        """Test connect when process exits immediately."""
        transport = StdioTransport(command="test-cmd")

        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = MagicMock()
        mock_process.stderr.read = AsyncMock(return_value=b"Error message")

        with patch(
            "asyncio.create_subprocess_exec",
            return_value=mock_process,
        ):
            with pytest.raises(ConnectionError, match="exited immediately"):
                await transport.connect()

    @pytest.mark.asyncio
    async def test_disconnect_process_lookup_error(self) -> None:
        """Test disconnect when process already exited."""
        transport = StdioTransport(command="test-cmd")

        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.terminate = MagicMock(side_effect=ProcessLookupError())

        transport._process = mock_process

        # Should handle gracefully
        await transport.disconnect()
        assert transport._process is None

    @pytest.mark.asyncio
    async def test_disconnect_generic_error(self) -> None:
        """Test disconnect with generic error."""
        transport = StdioTransport(command="test-cmd")

        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.terminate = MagicMock(side_effect=Exception("Unknown error"))

        transport._process = mock_process

        # Should handle gracefully
        await transport.disconnect()
        assert transport._process is None

    @pytest.mark.asyncio
    async def test_receive_process_exited(self) -> None:
        """Test receive when process has exited."""
        transport = StdioTransport(command="test-cmd")

        mock_stdout = MagicMock()
        mock_stdout.readline = AsyncMock(return_value=b"")

        mock_process = MagicMock()
        mock_process.stdout = mock_stdout
        mock_process.returncode = 1

        transport._process = mock_process

        with pytest.raises(ConnectionError, match="Process exited"):
            await transport.receive()

    @pytest.mark.asyncio
    async def test_receive_broken_pipe(self) -> None:
        """Test receive with broken pipe."""
        transport = StdioTransport(command="test-cmd")

        mock_stdout = MagicMock()
        mock_stdout.readline = AsyncMock(side_effect=BrokenPipeError("Broken pipe"))

        mock_process = MagicMock()
        mock_process.stdout = mock_stdout
        mock_process.returncode = None

        transport._process = mock_process

        with pytest.raises(ConnectionError, match="Read failed"):
            await transport.receive()

    @pytest.mark.asyncio
    async def test_receive_server_closed(self) -> None:
        """Test receive when server closes connection."""
        transport = StdioTransport(command="test-cmd")

        mock_stdout = MagicMock()
        mock_stdout.readline = AsyncMock(return_value=b"")

        mock_process = MagicMock()
        mock_process.stdout = mock_stdout
        mock_process.returncode = None  # Process still running but stdout closed

        transport._process = mock_process

        with pytest.raises(ConnectionError, match="Server closed connection"):
            await transport.receive()

    @pytest.mark.asyncio
    async def test_send_broken_pipe(self) -> None:
        """Test send with broken pipe."""
        transport = StdioTransport(command="test-cmd")

        mock_stdin = MagicMock()
        mock_stdin.write = MagicMock(side_effect=BrokenPipeError("Broken pipe"))

        mock_process = MagicMock()
        mock_process.stdin = mock_stdin
        mock_process.returncode = None

        transport._process = mock_process

        with pytest.raises(ConnectionError, match="Write failed"):
            await transport.send({"method": "test"})


class TestClientCoverage:
    """Coverage tests for MCPClient."""

    @pytest.mark.asyncio
    async def test_connect_init_failure_not_mcp_error(self) -> None:
        """Test connect when init fails with non-MCPError."""
        from code_forge.mcp.client import MCPClient, MCPClientError
        from code_forge.mcp.transport.base import MCPTransport

        mock_transport = MagicMock(spec=MCPTransport)
        mock_transport.connect = AsyncMock()
        mock_transport.disconnect = AsyncMock()
        mock_transport.send = AsyncMock()
        mock_transport.is_connected = True

        client = MCPClient(mock_transport, request_timeout=0.5)

        # Make _request raise a generic exception
        async def mock_request(*args: Any, **kwargs: Any) -> None:
            raise Exception("Generic error")

        client._request = mock_request  # type: ignore

        with pytest.raises(MCPClientError, match="Initialization failed"):
            await client.connect()

    @pytest.mark.asyncio
    async def test_connect_init_failure_mcp_error(self) -> None:
        """Test connect when init fails with MCPClientError."""
        from code_forge.mcp.client import MCPClient, MCPClientError
        from code_forge.mcp.transport.base import MCPTransport

        mock_transport = MagicMock(spec=MCPTransport)
        mock_transport.connect = AsyncMock()
        mock_transport.disconnect = AsyncMock()
        mock_transport.send = AsyncMock()
        mock_transport.is_connected = True

        client = MCPClient(mock_transport, request_timeout=0.5)

        async def mock_request(*args: Any, **kwargs: Any) -> None:
            raise MCPClientError("Server error")

        client._request = mock_request  # type: ignore

        with pytest.raises(MCPClientError, match="Server error"):
            await client.connect()

    @pytest.mark.asyncio
    async def test_disconnect_transport_error(self) -> None:
        """Test disconnect when transport raises error."""
        from code_forge.mcp.client import MCPClient
        from code_forge.mcp.transport.base import MCPTransport

        mock_transport = MagicMock(spec=MCPTransport)
        mock_transport.disconnect = AsyncMock(side_effect=Exception("Disconnect error"))
        mock_transport.is_connected = False

        client = MCPClient(mock_transport)

        # Should handle error gracefully
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_request_connection_error(self) -> None:
        """Test _request with connection error."""
        from code_forge.mcp.client import MCPClient, MCPClientError
        from code_forge.mcp.transport.base import MCPTransport

        mock_transport = MagicMock(spec=MCPTransport)
        mock_transport.send = AsyncMock(side_effect=ConnectionError("Connection lost"))
        mock_transport.is_connected = True

        client = MCPClient(mock_transport)

        with pytest.raises(MCPClientError, match="Connection error"):
            await client._request("test", {})

    @pytest.mark.asyncio
    async def test_notify_connection_error(self) -> None:
        """Test _notify with connection error."""
        from code_forge.mcp.client import MCPClient, MCPClientError
        from code_forge.mcp.transport.base import MCPTransport

        mock_transport = MagicMock(spec=MCPTransport)
        mock_transport.send = AsyncMock(side_effect=ConnectionError("Connection lost"))
        mock_transport.is_connected = True

        client = MCPClient(mock_transport)

        with pytest.raises(MCPClientError, match="Notification failed"):
            await client._notify("test", {})

    @pytest.mark.asyncio
    async def test_handle_message_server_request(self) -> None:
        """Test _handle_message with server request."""
        from code_forge.mcp.client import MCPClient
        from code_forge.mcp.transport.base import MCPTransport

        mock_transport = MagicMock(spec=MCPTransport)
        mock_transport.is_connected = True

        client = MCPClient(mock_transport)

        # Handle a server request
        await client._handle_message(
            {"jsonrpc": "2.0", "method": "server/request", "id": 1, "params": {}}
        )
        # Should log and not raise
