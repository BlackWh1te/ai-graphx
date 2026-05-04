"""graphx - extract · build · cluster · analyze · report."""

__version__ = "0.1.0"


def __getattr__(name):
    # Lazy imports so `graphx install` works before heavy deps are in place.
    _map = {
        "extract": ("graphx.extract", "extract"),
        "collect_files": ("graphx.extract", "collect_files"),
        "build_from_json": ("graphx.build", "build_from_json"),
        "cluster": ("graphx.cluster", "cluster"),
        "score_all": ("graphx.cluster", "score_all"),
        "cohesion_score": ("graphx.cluster", "cohesion_score"),
        "god_nodes": ("graphx.analyze", "god_nodes"),
        "surprising_connections": ("graphx.analyze", "surprising_connections"),
        "suggest_questions": ("graphx.analyze", "suggest_questions"),
        "generate": ("graphx.report", "generate"),
        "to_json": ("graphx.export", "to_json"),
        "to_html": ("graphx.export", "to_html"),
        "to_svg": ("graphx.export", "to_svg"),
        "to_canvas": ("graphx.export", "to_canvas"),
        "to_wiki": ("graphx.wiki", "to_wiki"),
    }
    if name in _map:
        import importlib
        mod_name, attr = _map[name]
        mod = importlib.import_module(mod_name)
        return getattr(mod, attr)
    raise AttributeError(f"module 'graphx' has no attribute {name!r}")
