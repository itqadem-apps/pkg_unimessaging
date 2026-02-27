# Testing

## Running the Test Suite

```bash
pytest tests/ -v
```

Or with shorter output:

```bash
pytest -q
```

## Existing Tests

The package includes basic tests in `tests/test_core.py`:

### `test_send_message_basic`

Verifies the happy path -- sending a message returns the correct status and payload.

```python
def test_send_message_basic():
    res = send_message("hello", "alice")
    assert res["status"] == "sent"
    assert res["payload"]["message"] == "hello"
    assert res["payload"]["to"] == "alice"
```

### `test_send_message_empty_raises`

Verifies that empty messages raise a `ValueError`.

```python
def test_send_message_empty_raises():
    with pytest.raises(ValueError):
        send_message("")
```

## Writing Tests for Custom Adapters

### Unit Testing a Gateway

```python
import pytest
from unimessaging.domain.entities import Message


class TestMyGateway:
    def test_deliver_returns_dict(self):
        gateway = MyGateway()
        msg = Message("hello", "alice")
        result = gateway.deliver(msg)
        assert isinstance(result, dict)

    def test_deliver_contains_message_fields(self):
        gateway = MyGateway()
        msg = Message("test", "bob")
        result = gateway.deliver(msg)
        assert result["message"] == "test"
        assert result["to"] == "bob"
```

### Integration Testing with the Facade

```python
from unimessaging import send_message


def test_send_message_with_custom_gateway():
    gateway = MyGateway()
    result = send_message("hello", "alice", gateway=gateway)
    assert result["status"] == "sent"
```

### Testing with a Mock Gateway

```python
from unittest.mock import MagicMock
from unimessaging import SendMessageUseCase, SendMessageRequest


def test_use_case_calls_gateway():
    mock_gateway = MagicMock()
    mock_gateway.deliver.return_value = {"message": "hi", "to": "bob"}

    use_case = SendMessageUseCase(mock_gateway)
    response = use_case.execute(SendMessageRequest("hi", "bob"))

    mock_gateway.deliver.assert_called_once()
    assert response.status == "sent"
```

### Testing Domain Validation

```python
import pytest
from unimessaging.domain.entities import Message
from unimessaging.domain.exceptions import InvalidMessageError


def test_empty_content_raises():
    with pytest.raises(InvalidMessageError, match="message content cannot be empty"):
        Message("", "alice")


def test_empty_recipient_raises():
    with pytest.raises(InvalidMessageError, match="recipient cannot be empty"):
        Message("hello", "")


def test_whitespace_is_stripped():
    msg = Message("  hello  ", "  alice  ")
    assert msg.content == "hello"
    assert msg.recipient == "alice"


def test_message_is_immutable():
    msg = Message("hello", "alice")
    with pytest.raises(AttributeError):
        msg.content = "bye"
```

## Test Configuration

The `pyproject.toml` includes development dependencies:

```toml
[project.optional-dependencies]
dev = ["pytest", "mypy"]
```

Install them with:

```bash
pip install -e ".[dev]"
```
