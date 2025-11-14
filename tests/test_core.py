from unimessaging import send_message
import pytest


def test_send_message_basic():
    res = send_message("hello", "alice")
    assert res["status"] == "sent"
    assert res["payload"]["message"] == "hello"
    assert res["payload"]["to"] == "alice"


def test_send_message_empty_raises():
    with pytest.raises(ValueError):
        send_message("")
