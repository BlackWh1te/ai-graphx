from __future__ import annotations

import json

import graphx.__main__ as mainmod


def test_ollama_path_first_build_writes_graphx_out(monkeypatch, tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text("def main():\n    return 1\n", encoding="utf-8")
    (project / "README.md").write_text("# Local Project\n", encoding="utf-8")

    def fake_semantic(files, **kwargs):
        assert kwargs["backend"] == "ollama"
        assert kwargs["model"] == "llama3.2:3b"
        return {
            "nodes": [
                {
                    "id": "readme_local_project",
                    "label": "Local Project",
                    "file_type": "document",
                    "source_file": "README.md",
                }
            ],
            "edges": [],
            "hyperedges": [],
            "input_tokens": 10,
            "output_tokens": 5,
        }

    monkeypatch.setattr("graphx.llm.extract_corpus_parallel", fake_semantic)

    code = mainmod._run_ollama_build([str(project), "--ollama", "--model", "llama3.2:3b", "--no-viz"])

    assert code == 0
    out = project / "graphx-out"
    assert (out / "graph.json").exists()
    assert (out / "GRAPH_REPORT.md").exists()
    data = json.loads((out / "graph.json").read_text(encoding="utf-8"))
    labels = {node.get("label") for node in data["nodes"]}
    assert "Local Project" in labels
