from __future__ import annotations

import json


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_ollama_backend_calls_native_chat_api(monkeypatch, tmp_path):
    from graphx.llm import extract_files_direct

    source = tmp_path / "README.md"
    source.write_text("# Project\n\nUses GraphX.", encoding="utf-8")
    seen = {}
    monkeypatch.delenv("OLLAMA_HOST", raising=False)

    def fake_urlopen(req, timeout):
        seen["url"] = req.full_url
        seen["timeout"] = timeout
        seen["payload"] = json.loads(req.data.decode("utf-8"))
        return _FakeResponse(
            {
                "message": {
                    "content": json.dumps(
                        {
                            "nodes": [
                                {
                                    "id": "readme_project",
                                    "label": "Project",
                                    "file_type": "document",
                                    "source_file": "README.md",
                                }
                            ],
                            "edges": [],
                            "hyperedges": [],
                        }
                    )
                },
                "prompt_eval_count": 12,
                "eval_count": 8,
                "done_reason": "stop",
            }
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    result = extract_files_direct([source], backend="ollama", model="llama3.2:3b", root=tmp_path)

    assert seen["url"] == "http://localhost:11434/api/chat"
    assert seen["payload"]["model"] == "llama3.2:3b"
    assert seen["payload"]["stream"] is False
    assert seen["payload"]["format"] == "json"
    assert result["nodes"][0]["id"] == "readme_project"
    assert result["input_tokens"] == 12
    assert result["output_tokens"] == 8
    assert result["finish_reason"] == "stop"


def test_ollama_host_accepts_openai_compat_suffix(monkeypatch, tmp_path):
    from graphx.llm import extract_files_direct

    source = tmp_path / "note.md"
    source.write_text("hello", encoding="utf-8")
    seen = {}

    def fake_urlopen(req, timeout):
        seen["url"] = req.full_url
        return _FakeResponse({"message": {"content": '{"nodes":[],"edges":[],"hyperedges":[]}'}})

    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11434/v1")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    extract_files_direct([source], backend="ollama", model="llama3.2:3b", root=tmp_path)

    assert seen["url"] == "http://127.0.0.1:11434/api/chat"


def test_ollama_host_maps_bind_all_address_to_loopback(monkeypatch, tmp_path):
    from graphx.llm import extract_files_direct

    source = tmp_path / "note.md"
    source.write_text("hello", encoding="utf-8")
    seen = {}

    def fake_urlopen(req, timeout):
        seen["url"] = req.full_url
        return _FakeResponse({"message": {"content": '{"nodes":[],"edges":[],"hyperedges":[]}'}})

    monkeypatch.setenv("OLLAMA_HOST", "0.0.0.0")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    extract_files_direct([source], backend="ollama", model="llama3.2:3b", root=tmp_path)

    assert seen["url"] == "http://127.0.0.1:11434/api/chat"
