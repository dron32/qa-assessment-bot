import json
import types

import pytest

from app.backend.src.llm.client import LlmClient, FAST_PROFILE


class DummyChoice:
    def __init__(self, content: str) -> None:
        self.message = types.SimpleNamespace(content=content)
        self.delta = types.SimpleNamespace(content=content)


class DummyResponse:
    def __init__(self, content: str) -> None:
        self.choices = [DummyChoice(content)]
        self.usage = {"prompt_tokens": 1, "completion_tokens": 10}


class DummyStream:
    def __iter__(self):
        yield DummyResponse("hello ")
        yield DummyResponse("world")


class DummyChat:
    def completions(self):  # type: ignore[override]
        raise NotImplementedError


def monkeypatch_openai(monkeypatch: pytest.MonkeyPatch, payload: str) -> None:
    class DummyClient:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    if kwargs.get("stream"):
                        return DummyStream()
                    return DummyResponse(payload)

    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr("app.backend.src.llm.client.OpenAI", lambda api_key=None: DummyClient())


def test_generate_template_parses_json(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps({"outline": "x", "example": "y", "bullet_points": ["a", "b", "c"]})
    monkeypatch_openai(monkeypatch, payload)
    client = LlmClient()
    out = client.generate_template(competency="comp", context="ctx", trace_id="t1")
    assert out.outline == "x"
    assert len(out.bullet_points) == 3


def test_stream_chat_yields_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps({"outline": "x", "example": "y", "bullet_points": ["a", "b", "c"]})
    monkeypatch_openai(monkeypatch, payload)
    client = LlmClient()
    chunks = list(client.stream_chat(system_prompt="sys", user_text="hi", trace_id="t2", profile=FAST_PROFILE))
    assert "hello" in "".join(chunks)


