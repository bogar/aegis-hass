"""Tests for HtsClient."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ajax_cobranded.api.hts.client import (
    HTS_HOST,
    HTS_PORT,
    HtsClient,
)
from custom_components.ajax_cobranded.api.hts.protocol import ETX, STX

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client(**kwargs: object) -> HtsClient:
    defaults = {
        "login_token": b"\xde\xad\xbe\xef",
        "user_hex_id": "C9D0E1F2",
        "device_id": "device123",
        "app_label": "com.test.app",
    }
    defaults.update(kwargs)
    return HtsClient(**defaults)


# ---------------------------------------------------------------------------
# __init__ state
# ---------------------------------------------------------------------------


class TestInit:
    def test_default_host_and_port(self) -> None:
        client = _make_client()
        assert client._host == HTS_HOST
        assert client._port == HTS_PORT

    def test_custom_host_and_port(self) -> None:
        client = _make_client(host="localhost", port=9999)
        assert client._host == "localhost"
        assert client._port == 9999

    def test_reader_writer_none(self) -> None:
        client = _make_client()
        assert client._reader is None
        assert client._writer is None

    def test_not_connected(self) -> None:
        client = _make_client()
        assert client._connected is False
        assert client.is_connected is False

    def test_seq_num_zero(self) -> None:
        client = _make_client()
        assert client._seq_num == 1

    def test_sender_id_from_user_hex_id(self) -> None:
        client = _make_client(user_hex_id="C9D0E1F2")
        assert client._sender_id == 0xC9D0E1F2
        assert client._receiver_id == 0

    def test_connection_token_empty(self) -> None:
        client = _make_client()
        assert client._connection_token == b""

    def test_hubs_empty(self) -> None:
        client = _make_client()
        assert client._hubs == []

    def test_ping_task_none(self) -> None:
        client = _make_client()
        assert client._ping_task is None

    def test_hub_states_empty(self) -> None:
        client = _make_client()
        assert client._hub_states == {}
        assert client.hub_states == {}

    def test_on_state_update_none(self) -> None:
        client = _make_client()
        assert client._on_state_update is None

    def test_login_token_stored(self) -> None:
        client = _make_client(login_token=b"\x01\x02\x03")
        assert client._login_token == b"\x01\x02\x03"

    def test_device_id_stored(self) -> None:
        client = _make_client(device_id="mydevice")
        assert client._device_id == "mydevice"

    def test_app_label_stored(self) -> None:
        client = _make_client(app_label="com.my.app")
        assert client._app_label == "com.my.app"


# ---------------------------------------------------------------------------
# _next_seq
# ---------------------------------------------------------------------------


class TestNextSeq:
    def test_starts_at_zero(self) -> None:
        client = _make_client()
        assert client._next_seq() == 1

    def test_increments(self) -> None:
        client = _make_client()
        client._next_seq()  # 1
        assert client._next_seq() == 2

    def test_sequential_calls(self) -> None:
        client = _make_client()
        results = [client._next_seq() for _ in range(5)]
        assert results == [1, 2, 3, 4, 5]

    def test_wraps_at_0xffffff(self) -> None:
        client = _make_client()
        client._seq_num = 0xFFFFFF
        assert client._next_seq() == 0xFFFFFF
        assert client._seq_num == 0  # wrapped

    def test_wrap_next_is_zero(self) -> None:
        client = _make_client()
        client._seq_num = 0xFFFFFF
        client._next_seq()  # consumes 0xFFFFFF
        assert client._next_seq() == 0  # next is 0

    def test_no_value_exceeds_max(self) -> None:
        client = _make_client()
        client._seq_num = 0xFFFFFE
        for _ in range(4):
            seq = client._next_seq()
            assert 0 <= seq <= 0xFFFFFF


# ---------------------------------------------------------------------------
# _send_message
# ---------------------------------------------------------------------------


class TestSendMessage:
    """_send_message should produce a valid STX...ETX frame on the wire."""

    @pytest.mark.asyncio
    async def test_frame_starts_with_stx_ends_with_etx(self) -> None:
        client = _make_client()

        written_data = bytearray()

        mock_writer = MagicMock()
        mock_writer.write = lambda data: written_data.extend(data)
        mock_writer.drain = AsyncMock()
        client._writer = mock_writer

        from custom_components.ajax_cobranded.api.hts.messages import MsgType

        await client._send_message(MsgType.PING, b"")

        assert len(written_data) > 0
        assert written_data[0] == STX
        assert written_data[-1] == ETX

    @pytest.mark.asyncio
    async def test_drain_called(self) -> None:
        client = _make_client()

        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        client._writer = mock_writer

        from custom_components.ajax_cobranded.api.hts.messages import MsgType

        await client._send_message(MsgType.PING, b"")

        mock_writer.drain.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_seq_increments_on_send(self) -> None:
        client = _make_client()

        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        client._writer = mock_writer

        from custom_components.ajax_cobranded.api.hts.messages import MsgType

        assert client._seq_num == 1
        await client._send_message(MsgType.PING, b"")
        assert client._seq_num == 2

    @pytest.mark.asyncio
    async def test_frame_is_bytes(self) -> None:
        client = _make_client()

        captured = []
        mock_writer = MagicMock()
        mock_writer.write = lambda data: captured.append(bytes(data))
        mock_writer.drain = AsyncMock()
        client._writer = mock_writer

        from custom_components.ajax_cobranded.api.hts.messages import MsgType

        await client._send_message(MsgType.PING, b"")

        assert len(captured) == 1
        assert isinstance(captured[0], bytes)
