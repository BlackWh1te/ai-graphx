# write graph to HTML, JSON, SVG, GraphML, Obsidian vault, and Neo4j Cypher
from __future__ import annotations
import html as _html
import json
import math
import re
from collections import Counter
from pathlib import Path
import networkx as nx
from networkx.readwrite import json_graph
from graphx.security import sanitize_label
from graphx.analyze import _node_community_map

def _strip_diacritics(text: str) -> str:
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


COMMUNITY_COLORS = [
    "#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
    "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC",
]

MAX_NODES_FOR_VIZ = 5_000


def _viz_node_limit() -> int:
    """Return the effective viz node limit, honoring GRAPHX_VIZ_NODE_LIMIT env var.

    Falls back to MAX_NODES_FOR_VIZ when the env var is unset, empty, or non-integer.
    Set to 0 to disable HTML viz unconditionally (useful for CI runners).
    """
    import os
    raw = os.environ.get("GRAPHX_VIZ_NODE_LIMIT")
    if raw is None or not raw.strip():
        return MAX_NODES_FOR_VIZ
    try:
        return int(raw)
    except ValueError:
        return MAX_NODES_FOR_VIZ


def _html_styles() -> str:
    return """<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0f0f1a; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; display: flex; height: 100vh; overflow: hidden; }
  #graph { flex: 1; }
  #sidebar { width: 280px; background: #1a1a2e; border-left: 1px solid #2a2a4e; display: flex; flex-direction: column; overflow: hidden; }
  #search-wrap { padding: 12px; border-bottom: 1px solid #2a2a4e; }
  #search { width: 100%; background: #0f0f1a; border: 1px solid #3a3a5e; color: #e0e0e0; padding: 7px 10px; border-radius: 6px; font-size: 13px; outline: none; }
  #search:focus { border-color: #4E79A7; }
  #search-results { max-height: 140px; overflow-y: auto; padding: 4px 12px; border-bottom: 1px solid #2a2a4e; display: none; }
  .search-item { padding: 4px 6px; cursor: pointer; border-radius: 4px; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .search-item:hover { background: #2a2a4e; }
  #info-panel { padding: 14px; border-bottom: 1px solid #2a2a4e; min-height: 140px; }
  #info-panel h3 { font-size: 13px; color: #aaa; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em; }
  #info-content { font-size: 13px; color: #ccc; line-height: 1.6; }
  #info-content .field { margin-bottom: 5px; }
  #info-content .field b { color: #e0e0e0; }
  #info-content .empty { color: #555; font-style: italic; }
  .neighbor-link { display: block; padding: 2px 6px; margin: 2px 0; border-radius: 3px; cursor: pointer; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border-left: 3px solid #333; }
  .neighbor-link:hover { background: #2a2a4e; }
  #neighbors-list { max-height: 160px; overflow-y: auto; margin-top: 4px; }
  #legend-wrap { flex: 1; overflow-y: auto; padding: 12px; }
  #legend-wrap h3 { font-size: 13px; color: #aaa; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.05em; }
  .legend-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; cursor: pointer; border-radius: 4px; font-size: 12px; }
  .legend-item:hover { background: #2a2a4e; padding-left: 4px; }
  .legend-item.dimmed { opacity: 0.35; }
  .legend-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
  .legend-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .legend-count { color: #666; font-size: 11px; }
  #stats { padding: 10px 14px; border-top: 1px solid #2a2a4e; font-size: 11px; color: #555; }
  #legend-controls { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding: 4px 0; }
  #legend-controls label { display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 12px; color: #aaa; user-select: none; }
  #legend-controls label:hover { color: #e0e0e0; }
  .legend-cb, #select-all-cb { appearance: none; -webkit-appearance: none; width: 14px; height: 14px; border: 1.5px solid #3a3a5e; border-radius: 3px; background: #0f0f1a; cursor: pointer; position: relative; flex-shrink: 0; }
  .legend-cb:checked, #select-all-cb:checked { background: #4E79A7; border-color: #4E79A7; }
  .legend-cb:checked::after, #select-all-cb:checked::after { content: ''; position: absolute; left: 3.5px; top: 1px; width: 4px; height: 7px; border: solid #fff; border-width: 0 2px 2px 0; transform: rotate(45deg); }
  #select-all-cb:indeterminate { background: #4E79A7; border-color: #4E79A7; }
  #select-all-cb:indeterminate::after { content: ''; position: absolute; left: 2px; top: 5px; width: 8px; height: 2px; background: #fff; border: none; transform: none; }
</style>"""


def _hyperedge_script(hyperedges_json: str) -> str:
    return f"""<script>
// Render hyperedges as shaded regions
const hyperedges = {hyperedges_json};
// afterDrawing passes ctx already transformed to network coordinate space.
// Draw node positions raw — no manual pan/zoom/DPR math needed.
network.on('afterDrawing', function(ctx) {{
    hyperedges.forEach(h => {{
        const positions = h.nodes
            .map(nid => network.getPositions([nid])[nid])
            .filter(p => p !== undefined);
        if (positions.length < 2) return;
        ctx.save();
        ctx.globalAlpha = 0.12;
        ctx.fillStyle = '#6366f1';
        ctx.strokeStyle = '#6366f1';
        ctx.lineWidth = 2;
        ctx.beginPath();
        // Centroid and expanded hull in network coordinates
        const cx = positions.reduce((s, p) => s + p.x, 0) / positions.length;
        const cy = positions.reduce((s, p) => s + p.y, 0) / positions.length;
        const expanded = positions.map(p => ({{
            x: cx + (p.x - cx) * 1.15,
            y: cy + (p.y - cy) * 1.15
        }}));
        ctx.moveTo(expanded[0].x, expanded[0].y);
        expanded.slice(1).forEach(p => ctx.lineTo(p.x, p.y));
        ctx.closePath();
        ctx.fill();
        ctx.globalAlpha = 0.4;
        ctx.stroke();
        // Label
        ctx.globalAlpha = 0.8;
        ctx.fillStyle = '#4f46e5';
        ctx.font = 'bold 11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(h.label, cx, cy - 5);
        ctx.restore();
    }});
}});
</script>"""


def _html_script(nodes_json: str, edges_json: str, legend_json: str) -> str:
    return f"""<script>
const RAW_NODES = {nodes_json};
const RAW_EDGES = {edges_json};
const LEGEND = {legend_json};

// HTML-escape helper — prevents XSS when injecting graph data into innerHTML
function esc(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}}

// Build vis datasets
const nodesDS = new vis.DataSet(RAW_NODES.map(n => ({{
  id: n.id, label: n.label, color: n.color, size: n.size,
  font: n.font, title: n.title,
  _community: n.community, _community_name: n.community_name,
  _source_file: n.source_file, _file_type: n.file_type, _degree: n.degree,
}})));

const edgesDS = new vis.DataSet(RAW_EDGES.map((e, i) => ({{
  id: i, from: e.from, to: e.to,
  label: '',
  title: e.title,
  dashes: e.dashes,
  width: e.width,
  color: e.color,
  arrows: {{ to: {{ enabled: true, scaleFactor: 0.5 }} }},
}})));

const container = document.getElementById('graph');
const network = new vis.Network(container, {{ nodes: nodesDS, edges: edgesDS }}, {{
  physics: {{
    enabled: true,
    solver: 'forceAtlas2Based',
    forceAtlas2Based: {{
      gravitationalConstant: -60,
      centralGravity: 0.005,
      springLength: 120,
      springConstant: 0.08,
      damping: 0.4,
      avoidOverlap: 0.8,
    }},
    stabilization: {{ iterations: 200, fit: true }},
  }},
  interaction: {{
    hover: true,
    tooltipDelay: 100,
    hideEdgesOnDrag: true,
    navigationButtons: false,
    keyboard: false,
  }},
  nodes: {{ shape: 'dot', borderWidth: 1.5 }},
  edges: {{ smooth: {{ type: 'continuous', roundness: 0.2 }}, selectionWidth: 3 }},
}});

network.once('stabilizationIterationsDone', () => {{
  network.setOptions({{ physics: {{ enabled: false }} }});
}});

function showInfo(nodeId) {{
  const n = nodesDS.get(nodeId);
  if (!n) return;
  const neighborIds = network.getConnectedNodes(nodeId);
  const neighborItems = neighborIds.map(nid => {{
    const nb = nodesDS.get(nid);
    const color = nb ? nb.color.background : '#555';
    return `<span class="neighbor-link" style="border-left-color:${{esc(color)}}" onclick="focusNode(${{JSON.stringify(nid)}})">${{esc(nb ? nb.label : nid)}}</span>`;
  }}).join('');
  document.getElementById('info-content').innerHTML = `
    <div class="field"><b>${{esc(n.label)}}</b></div>
    <div class="field">Type: ${{esc(n._file_type || 'unknown')}}</div>
    <div class="field">Community: ${{esc(n._community_name)}}</div>
    <div class="field">Source: ${{esc(n._source_file || '-')}}</div>
    <div class="field">Degree: ${{n._degree}}</div>
    ${{neighborIds.length ? `<div class="field" style="margin-top:8px;color:#aaa;font-size:11px">Neighbors (${{neighborIds.length}})</div><div id="neighbors-list">${{neighborItems}}</div>` : ''}}
  `;
}}

function focusNode(nodeId) {{
  network.focus(nodeId, {{ scale: 1.4, animation: true }});
  network.selectNodes([nodeId]);
  showInfo(nodeId);
}}

// Track hovered node — hover detection is more reliable than click params
let hoveredNodeId = null;
network.on('hoverNode', params => {{
  hoveredNodeId = params.node;
  container.style.cursor = 'pointer';
}});
network.on('blurNode', () => {{
  hoveredNodeId = null;
  container.style.cursor = 'default';
}});
container.addEventListener('click', () => {{
  if (hoveredNodeId !== null) {{
    showInfo(hoveredNodeId);
    network.selectNodes([hoveredNodeId]);
  }}
}});
network.on('click', params => {{
  if (params.nodes.length > 0) {{
    showInfo(params.nodes[0]);
  }} else if (hoveredNodeId === null) {{
    document.getElementById('info-content').innerHTML = '<span class="empty">Click a node to inspect it</span>';
  }}
}});

const searchInput = document.getElementById('search');
const searchResults = document.getElementById('search-results');
searchInput.addEventListener('input', () => {{
  const q = searchInput.value.toLowerCase().trim();
  searchResults.innerHTML = '';
  if (!q) {{ searchResults.style.display = 'none'; return; }}
  const matches = RAW_NODES.filter(n => n.label.toLowerCase().includes(q)).slice(0, 20);
  if (!matches.length) {{ searchResults.style.display = 'none'; return; }}
  searchResults.style.display = 'block';
  matches.forEach(n => {{
    const el = document.createElement('div');
    el.className = 'search-item';
    el.textContent = n.label;
    el.style.borderLeft = `3px solid ${{n.color.background}}`;
    el.style.paddingLeft = '8px';
    el.onclick = () => {{
      network.focus(n.id, {{ scale: 1.5, animation: true }});
      network.selectNodes([n.id]);
      showInfo(n.id);
      searchResults.style.display = 'none';
      searchInput.value = '';
    }};
    searchResults.appendChild(el);
  }});
}});
document.addEventListener('click', e => {{
  if (!searchResults.contains(e.target) && e.target !== searchInput)
    searchResults.style.display = 'none';
}});

const hiddenCommunities = new Set();

const selectAllCb = document.getElementById('select-all-cb');

function updateSelectAllState() {{
  const total = LEGEND.length;
  const hidden = hiddenCommunities.size;
  selectAllCb.checked = hidden === 0;
  selectAllCb.indeterminate = hidden > 0 && hidden < total;
}}

function toggleAllCommunities(hide) {{
  document.querySelectorAll('.legend-item').forEach(item => {{
    hide ? item.classList.add('dimmed') : item.classList.remove('dimmed');
  }});
  document.querySelectorAll('.legend-cb').forEach(cb => {{
    cb.checked = !hide;
  }});
  LEGEND.forEach(c => {{
    if (hide) hiddenCommunities.add(c.cid); else hiddenCommunities.delete(c.cid);
  }});
  const updates = RAW_NODES.map(n => ({{ id: n.id, hidden: hide }}));
  nodesDS.update(updates);
  updateSelectAllState();
}}

const legendEl = document.getElementById('legend');
LEGEND.forEach(c => {{
  const item = document.createElement('div');
  item.className = 'legend-item';
  const cb = document.createElement('input');
  cb.type = 'checkbox';
  cb.className = 'legend-cb';
  cb.checked = true;
  cb.addEventListener('change', (e) => {{
    e.stopPropagation();
    if (cb.checked) {{
      hiddenCommunities.delete(c.cid);
      item.classList.remove('dimmed');
    }} else {{
      hiddenCommunities.add(c.cid);
      item.classList.add('dimmed');
    }}
    const updates = RAW_NODES
      .filter(n => n.community === c.cid)
      .map(n => ({{ id: n.id, hidden: !cb.checked }}));
    nodesDS.update(updates);
    updateSelectAllState();
  }});
  item.innerHTML = `<div class="legend-dot" style="background:${{c.color}}"></div>
    <span class="legend-label">${{c.label}}</span>
    <span class="legend-count">${{c.count}}</span>`;
  item.prepend(cb);
  item.onclick = (e) => {{
    if (e.target === cb) return;
    cb.checked = !cb.checked;
    cb.dispatchEvent(new Event('change'));
  }};
  legendEl.appendChild(item);
}});
</script>"""


_CONFIDENCE_SCORE_DEFAULTS = {"EXTRACTED": 1.0, "INFERRED": 0.5, "AMBIGUOUS": 0.2}


def attach_hyperedges(G: nx.Graph, hyperedges: list) -> None:
    """Store hyperedges in the graph's metadata dict."""
    existing = G.graph.get("hyperedges", [])
    seen_ids = {h["id"] for h in existing}
    for h in hyperedges:
        if h.get("id") and h["id"] not in seen_ids:
            existing.append(h)
            seen_ids.add(h["id"])
    G.graph["hyperedges"] = existing


def to_json(G: nx.Graph, communities: dict[int, list[str]], output_path: str, *, force: bool = False) -> bool:
    # Safety check: refuse to silently shrink an existing graph (#479)
    existing_path = Path(output_path)
    if not force and existing_path.exists():
        try:
            existing_data = json.loads(existing_path.read_text(encoding="utf-8"))
            existing_n = len(existing_data.get("nodes", []))
            new_n = G.number_of_nodes()
            if new_n < existing_n:
                import sys as _sys
                print(
                    f"[graphx] WARNING: new graph has {new_n} nodes but existing "
                    f"graph.json has {existing_n}. Refusing to overwrite — you may be "
                    f"missing chunk files from a previous session. "
                    f"Pass force=True to override.",
                    file=_sys.stderr,
                )
                return False
        except Exception:
            pass  # unreadable existing file — proceed with write

    node_community = _node_community_map(communities)
    try:
        data = json_graph.node_link_data(G, edges="links")
    except TypeError:
        data = json_graph.node_link_data(G)
    for node in data["nodes"]:
        node["community"] = node_community.get(node["id"])
        node["norm_label"] = _strip_diacritics(node.get("label", "")).lower()
    for link in data["links"]:
        if "confidence_score" not in link:
            conf = link.get("confidence", "EXTRACTED")
            link["confidence_score"] = _CONFIDENCE_SCORE_DEFAULTS.get(conf, 1.0)
        # Restore original edge direction. Undirected NetworkX storage may
        # canonicalize endpoint order, flipping `calls` and other directional
        # edges in graph.json. The build path stashes the true endpoints in
        # _src/_tgt for exactly this purpose (#563).
        true_src = link.pop("_src", None)
        true_tgt = link.pop("_tgt", None)
        if true_src is not None and true_tgt is not None:
            link["source"] = true_src
            link["target"] = true_tgt
    data["hyperedges"] = getattr(G, "graph", {}).get("hyperedges", [])
    with open(output_path, "w", encoding="utf-8") as f:  # nosec
        json.dump(data, f, indent=2)
    return True


def prune_dangling_edges(graph_data: dict) -> tuple[dict, int]:
    """Remove edges whose source or target node is not in the node set.

    Returns the cleaned graph_data dict and the number of pruned edges.
    """
    node_ids = {n["id"] for n in graph_data["nodes"]}
    links_key = "links" if "links" in graph_data else "edges"
    before = len(graph_data[links_key])
    graph_data[links_key] = [
        e for e in graph_data[links_key]
        if e["source"] in node_ids and e["target"] in node_ids
    ]
    return graph_data, before - len(graph_data[links_key])


def _cypher_escape(s: str) -> str:
    """Escape a string for safe embedding in a Cypher single-quoted literal."""
    return s.replace("\\", "\\\\").replace("'", "\\'")


def to_cypher(G: nx.Graph, output_path: str) -> None:
    lines = ["// Neo4j Cypher import - generated by /graphx", ""]
    for node_id, data in G.nodes(data=True):
        label = _cypher_escape(data.get("label", node_id))
        node_id_esc = _cypher_escape(node_id)
        _ft = re.sub(r"[^A-Za-z0-9_]", "", data.get("file_type", "unknown").capitalize())
        ftype = (_ft if _ft and _ft[0].isalpha() else "Entity")
        lines.append(f"MERGE (n:{ftype} {{id: '{node_id_esc}', label: '{label}'}});")
    lines.append("")
    for u, v, data in G.edges(data=True):
        rel = re.sub(r"[^A-Za-z0-9_]", "_", data.get("relation", "RELATES_TO").upper())
        conf = _cypher_escape(data.get("confidence", "EXTRACTED"))
        u_esc = _cypher_escape(u)
        v_esc = _cypher_escape(v)
        lines.append(
            f"MATCH (a {{id: '{u_esc}'}}), (b {{id: '{v_esc}'}}) "
            f"MERGE (a)-[:{rel} {{confidence: '{conf}'}}]->(b);"
        )
    with open(output_path, "w", encoding="utf-8") as f:  # nosec
        f.write("\n".join(lines))


def to_html(
    G: nx.Graph,
    communities: dict[int, list[str]],
    output_path: str,
    community_labels: dict[int, str] | None = None,
    member_counts: dict[int, int] | None = None,
) -> None:
    """Generate an interactive vis.js HTML visualization of the graph.

    Features: node size by degree, click-to-inspect panel, search box,
    community filter, physics clustering by community, confidence-styled edges.
    Raises ValueError if graph exceeds MAX_NODES_FOR_VIZ.

    If member_counts is provided (aggregated community view), node sizes are
    based on community member counts rather than graph degree.
    """
    limit = _viz_node_limit()
    if G.number_of_nodes() > limit:
        raise ValueError(
            f"Graph has {G.number_of_nodes()} nodes - too large for HTML viz "
            f"(limit: {limit}). Use --no-viz, raise GRAPHX_VIZ_NODE_LIMIT, "
            f"or reduce input size."
        )

    node_community = _node_community_map(communities)
    degree = dict(G.degree())
    max_deg = max(degree.values(), default=1) or 1
    max_mc = (max(member_counts.values(), default=1) or 1) if member_counts else 1

    # Build nodes list for vis.js
    vis_nodes = []
    for node_id, data in G.nodes(data=True):
        cid = node_community.get(node_id, 0)
        color = COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)]
        label = sanitize_label(data.get("label", node_id))
        deg = degree.get(node_id, 1)
        if member_counts:
            mc = member_counts.get(cid, 1)
            size = 10 + 30 * (mc / max_mc)
            font_size = 12
        else:
            size = 10 + 30 * (deg / max_deg)
            # Only show label for high-degree nodes by default; others show on hover
            font_size = 12 if deg >= max_deg * 0.15 else 0
        vis_nodes.append({
            "id": node_id,
            "label": label,
            "color": {"background": color, "border": color, "highlight": {"background": "#ffffff", "border": color}},
            "size": round(size, 1),
            "font": {"size": font_size, "color": "#ffffff"},
            "title": _html.escape(label),
            "community": cid,
            "community_name": sanitize_label((community_labels or {}).get(cid, f"Community {cid}")),
            "source_file": sanitize_label(str(data.get("source_file") or "")),
            "file_type": data.get("file_type", ""),
            "degree": deg,
        })

    # Build edges list. Restore original edge direction from _src/_tgt
    # (stashed by build.py for exactly this reason): undirected NetworkX
    # canonicalizes endpoint order, which would otherwise flip the arrow
    # for `calls` and `rationale_for` in the rendered graph (#563).
    vis_edges = []
    for u, v, data in G.edges(data=True):
        confidence = data.get("confidence", "EXTRACTED")
        relation = data.get("relation", "")
        true_src = data.get("_src", u)
        true_tgt = data.get("_tgt", v)
        vis_edges.append({
            "from": true_src,
            "to": true_tgt,
            "label": relation,
            "title": _html.escape(f"{relation} [{confidence}]"),
            "dashes": confidence != "EXTRACTED",
            "width": 2 if confidence == "EXTRACTED" else 1,
            "color": {"opacity": 0.7 if confidence == "EXTRACTED" else 0.35},
            "confidence": confidence,
        })

    # Build community legend data
    legend_data = []
    for cid in sorted((community_labels or {}).keys()):
        color = COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)]
        lbl = _html.escape(sanitize_label((community_labels or {}).get(cid, f"Community {cid}")))
        n = member_counts.get(cid, len(communities.get(cid, []))) if member_counts else len(communities.get(cid, []))
        legend_data.append({"cid": cid, "color": color, "label": lbl, "count": n})

    # Escape </script> sequences so embedded JSON cannot break out of the script tag
    def _js_safe(obj) -> str:
        return json.dumps(obj).replace("</", "<\\/")

    nodes_json = _js_safe(vis_nodes)
    edges_json = _js_safe(vis_edges)
    legend_json = _js_safe(legend_data)
    hyperedges_json = _js_safe(getattr(G, "graph", {}).get("hyperedges", []))
    title = _html.escape(sanitize_label(str(output_path)))
    stats = f"{G.number_of_nodes()} nodes &middot; {G.number_of_edges()} edges &middot; {len(communities)} communities"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>graphx - {title}</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
{_html_styles()}
</head>
<body>
<div id="graph"></div>
<div id="sidebar">
  <div id="search-wrap">
    <input id="search" type="text" placeholder="Search nodes..." autocomplete="off">
    <div id="search-results"></div>
  </div>
  <div id="info-panel">
    <h3>Node Info</h3>
    <div id="info-content"><span class="empty">Click a node to inspect it</span></div>
  </div>
  <div id="legend-wrap">
    <h3>Communities</h3>
    <div id="legend-controls">
      <label><input type="checkbox" id="select-all-cb" checked onchange="toggleAllCommunities(!this.checked)">Select All</label>
    </div>
    <div id="legend"></div>
  </div>
  <div id="stats">{stats}</div>
</div>
{_html_script(nodes_json, edges_json, legend_json)}
{_hyperedge_script(hyperedges_json)}
</body>
</html>"""

    Path(output_path).write_text(html, encoding="utf-8")  # nosec


# Keep backward-compatible alias - skill.md calls generate_html
generate_html = to_html


def to_obsidian(
    G: nx.Graph,
    communities: dict[int, list[str]],
    output_dir: str,
    community_labels: dict[int, str] | None = None,
    cohesion: dict[int, float] | None = None,
) -> int:
    """Export graph as an Obsidian vault - one .md file per node with [[wikilinks]],
    plus one _COMMUNITY_name.md overview note per community (sorted to top by underscore prefix).

    Open the output directory as a vault in Obsidian to get an interactive
    graph view with community colors and full-text search over node metadata.

    Returns the number of node notes + community notes written.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    node_community = _node_community_map(communities)

    # Map node_id → safe filename so wikilinks stay consistent.
    # Deduplicate: if two nodes produce the same filename, append a numeric suffix.
    def safe_name(label: str) -> str:
        cleaned = re.sub(r'[\\/*?:"<>|#^[\]]', "", label.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")).strip()
        # Strip trailing .md/.mdx/.markdown so "CLAUDE.md" doesn't become "CLAUDE.md.md"
        cleaned = re.sub(r"\.(md|mdx|markdown)$", "", cleaned, flags=re.IGNORECASE)
        return cleaned or "unnamed"

    node_filename: dict[str, str] = {}
    seen_names: dict[str, int] = {}
    for node_id, data in G.nodes(data=True):
        base = safe_name(data.get("label", node_id))
        if base in seen_names:
            seen_names[base] += 1
            node_filename[node_id] = f"{base}_{seen_names[base]}"
        else:
            seen_names[base] = 0
            node_filename[node_id] = base

    # Helper: compute dominant confidence for a node across all its edges
    def _dominant_confidence(node_id: str) -> str:
        confs = []
        for u, v, edata in G.edges(node_id, data=True):
            confs.append(edata.get("confidence", "EXTRACTED"))
        if not confs:
            return "EXTRACTED"
        return Counter(confs).most_common(1)[0][0]

    # Map file_type → graphx tag
    _FTYPE_TAG = {
        "code": "graphx/code",
        "document": "graphx/document",
        "paper": "graphx/paper",
        "image": "graphx/image",
    }

    # Write one .md file per node
    for node_id, data in G.nodes(data=True):
        label = data.get("label", node_id)
        cid = node_community.get(node_id)
        community_name = (
            community_labels.get(cid, f"Community {cid}")
            if community_labels and cid is not None
            else f"Community {cid}"
        )

        # Build tags for this node
        ftype = data.get("file_type", "")
        ftype_tag = _FTYPE_TAG.get(ftype, f"graphx/{ftype}" if ftype else "graphx/document")
        dom_conf = _dominant_confidence(node_id)
        conf_tag = f"graphx/{dom_conf}"
        comm_tag = f"community/{community_name.replace(' ', '_')}"
        node_tags = [ftype_tag, conf_tag, comm_tag]

        lines: list[str] = []

        # YAML frontmatter - readable in Obsidian's properties panel
        lines += [
            "---",
            f'source_file: "{data.get("source_file", "")}"',
            f'type: "{ftype}"',
            f'community: "{community_name}"',
        ]
        if data.get("source_location"):
            lines.append(f'location: "{data["source_location"]}"')
        # Add tags list to frontmatter
        lines.append("tags:")
        for tag in node_tags:
            lines.append(f"  - {tag}")
        lines += ["---", "", f"# {label}", ""]

        # Outgoing edges as wikilinks
        neighbors = list(G.neighbors(node_id))
        if neighbors:
            lines.append("## Connections")
            for neighbor in sorted(neighbors, key=lambda n: G.nodes[n].get("label", n)):
                edge_data = G.edges[node_id, neighbor]
                neighbor_label = node_filename[neighbor]
                relation = edge_data.get("relation", "")
                confidence = edge_data.get("confidence", "EXTRACTED")
                lines.append(f"- [[{neighbor_label}]] - `{relation}` [{confidence}]")
            lines.append("")

        # Inline tags at bottom of note body (for Obsidian tag panel)
        inline_tags = " ".join(f"#{t}" for t in node_tags)
        lines.append(inline_tags)

        fname = node_filename[node_id] + ".md"
        (out / fname).write_text("\n".join(lines), encoding="utf-8")  # nosec

    # Write one _COMMUNITY_name.md overview note per community
    # Build inter-community edge counts for "Connections to other communities"
    inter_community_edges: dict[int, dict[int, int]] = {}
    for cid in communities:
        inter_community_edges[cid] = {}
    for u, v in G.edges():
        cu = node_community.get(u)
        cv = node_community.get(v)
        if cu is not None and cv is not None and cu != cv:
            inter_community_edges.setdefault(cu, {})
            inter_community_edges.setdefault(cv, {})
            inter_community_edges[cu][cv] = inter_community_edges[cu].get(cv, 0) + 1
            inter_community_edges[cv][cu] = inter_community_edges[cv].get(cu, 0) + 1

    # Precompute per-node community reach (number of distinct communities a node connects to)
    def _community_reach(node_id: str) -> int:
        neighbor_cids = {
            node_community[nb]
            for nb in G.neighbors(node_id)
            if nb in node_community and node_community[nb] != node_community.get(node_id)
        }
        return len(neighbor_cids)

    community_notes_written = 0
    for cid, members in communities.items():
        community_name = (
            community_labels.get(cid, f"Community {cid}")
            if community_labels and cid is not None
            else f"Community {cid}"
        )
        n_members = len(members)
        coh_value = cohesion.get(cid) if cohesion else None

        lines: list[str] = []

        # YAML frontmatter
        lines.append("---")
        lines.append("type: community")
        if coh_value is not None:
            lines.append(f"cohesion: {coh_value:.2f}")
        lines.append(f"members: {n_members}")
        lines.append("---")
        lines.append("")
        lines.append(f"# {community_name}")
        lines.append("")

        # Cohesion + member count summary
        if coh_value is not None:
            cohesion_desc = (
                "tightly connected" if coh_value >= 0.7
                else "moderately connected" if coh_value >= 0.4
                else "loosely connected"
            )
            lines.append(f"**Cohesion:** {coh_value:.2f} - {cohesion_desc}")
        lines.append(f"**Members:** {n_members} nodes")
        lines.append("")

        # Members section
        lines.append("## Members")
        for node_id in sorted(members, key=lambda n: G.nodes[n].get("label", n)):
            data = G.nodes[node_id]
            node_label = node_filename[node_id]
            ftype = data.get("file_type", "")
            source = data.get("source_file", "")
            entry = f"- [[{node_label}]]"
            if ftype:
                entry += f" - {ftype}"
            if source:
                entry += f" - {source}"
            lines.append(entry)
        lines.append("")

        # Dataview live query (improvement 2)
        comm_tag_name = community_name.replace(" ", "_")
        lines.append("## Live Query (requires Dataview plugin)")
        lines.append("")
        lines.append("```dataview")
        lines.append(f"TABLE source_file, type FROM #community/{comm_tag_name}")
        lines.append("SORT file.name ASC")
        lines.append("```")
        lines.append("")

        # Connections to other communities
        cross = inter_community_edges.get(cid, {})
        if cross:
            lines.append("## Connections to other communities")
            for other_cid, edge_count in sorted(cross.items(), key=lambda x: -x[1]):
                other_name = (
                    community_labels.get(other_cid, f"Community {other_cid}")
                    if community_labels and other_cid is not None
                    else f"Community {other_cid}"
                )
                other_safe = safe_name(other_name)
                lines.append(f"- {edge_count} edge{'s' if edge_count != 1 else ''} to [[_COMMUNITY_{other_safe}]]")
            lines.append("")

        # Top bridge nodes - highest degree nodes that connect to other communities
        bridge_nodes = [
            (node_id, G.degree(node_id), _community_reach(node_id))
            for node_id in members
            if _community_reach(node_id) > 0
        ]
        bridge_nodes.sort(key=lambda x: (-x[2], -x[1]))
        top_bridges = bridge_nodes[:5]
        if top_bridges:
            lines.append("## Top bridge nodes")
            for node_id, degree, reach in top_bridges:
                node_label = node_filename[node_id]
                lines.append(
                    f"- [[{node_label}]] - degree {degree}, connects to {reach} "
                    f"{'community' if reach == 1 else 'communities'}"
                )

        community_safe = safe_name(community_name)
        fname = f"_COMMUNITY_{community_safe}.md"
        (out / fname).write_text("\n".join(lines), encoding="utf-8")  # nosec
        community_notes_written += 1

    # Improvement 4: write .obsidian/graph.json to color nodes by community in graph view
    obsidian_dir = out / ".obsidian"
    obsidian_dir.mkdir(exist_ok=True)
    graph_config = {
        "colorGroups": [
            {
                "query": f"tag:#community/{label.replace(' ', '_')}",
                "color": {"a": 1, "rgb": int(COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)].lstrip('#'), 16)}
            }
            for cid, label in sorted((community_labels or {}).items())
        ]
    }
    (obsidian_dir / "graph.json").write_text(json.dumps(graph_config, indent=2), encoding="utf-8")  # nosec

    return G.number_of_nodes() + community_notes_written


def to_index_html(
    G: nx.Graph,
    communities: dict[int, list[str]],
    output_dir: str,
    community_labels: dict[int, str] | None = None,
    cohesion: dict[int, float] | None = None,
    god_nodes_data: list[dict] | None = None,
    project_name: str | None = None,
    status_report: dict | None = None,
) -> None:
    """Generate a dynamic SPA dashboard HTML that renders from embedded data
    and polls activity.json for live updates.

    The page works as a standalone file (file://) with all graph data embedded
    in window.INITIAL_DATA.  The activity timeline section additionally polls
    activity.json every 30 s so users see new commits without regenerating the
    HTML.
    """
    from collections import Counter
    from datetime import datetime
    import json as _json

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    node_community = _node_community_map(communities)
    degree = dict(G.degree())
    max_deg = max(degree.values(), default=1) or 1

    # --- Build community stats ---
    community_stats = []
    for cid in sorted(communities.keys(), key=lambda x: -len(communities[x])):
        label = (community_labels or {}).get(cid, f"Community {cid}")
        coh_val = cohesion.get(cid) if cohesion else None
        color = COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)]
        members = communities[cid]
        top_node = max(members, key=lambda n: degree.get(n, 0)) if members else None
        top_label = G.nodes[top_node].get("label", "") if top_node else ""
        community_stats.append(
            {
                "cid": cid,
                "label": label,
                "count": len(members),
                "color": color,
                "cohesion": coh_val,
                "top_node": top_label,
            }
        )

    # --- God nodes ---
    gods_preview = (god_nodes_data or [])[:10]

    # --- Audit trail ---
    conf_counts = Counter()
    for _, _, data in G.edges(data=True):
        conf_counts[data.get("confidence", "EXTRACTED")] += 1
    total_edges = sum(conf_counts.values()) or 1
    audit_trail = [
        {
            "type": "EXTRACTED",
            "count": conf_counts.get("EXTRACTED", 0),
            "pct": round(conf_counts.get("EXTRACTED", 0) / total_edges * 100),
        },
        {
            "type": "INFERRED",
            "count": conf_counts.get("INFERRED", 0),
            "pct": round(conf_counts.get("INFERRED", 0) / total_edges * 100),
        },
        {
            "type": "AMBIGUOUS",
            "count": conf_counts.get("AMBIGUOUS", 0),
            "pct": round(conf_counts.get("AMBIGUOUS", 0) / total_edges * 100),
        },
    ]

    # --- Output file existence ---
    outputs_exist = {
        "graph.html": (out / "graph.html").exists(),
        "GRAPH_TREE.html": (out / "GRAPH_TREE.html").exists(),
        "wiki": (out / "wiki" / "index.md").exists(),
        "GRAPH_REPORT.md": (out / "GRAPH_REPORT.md").exists(),
        "graph.json": (out / "graph.json").exists(),
        "graph.svg": (out / "graph.svg").exists(),
        "graph.graphml": (out / "graph.graphml").exists(),
    }

    # --- Status report data (for embedded initial render) ---
    sr = status_report or {}
    git_info = sr.get("branch_status", {})
    current_branch = git_info.get("current", "unknown")
    staged = sr.get("staged_changes", [])
    merge_commits = sr.get("merge_commits", [])[:5]
    all_commits = sr.get("commits", [])[:20]
    hot_files = sr.get("hot_files", [])[:10]
    external_files = sr.get("external_files", [])[:10]
    large_files = sr.get("large_files", [])[:5]
    velocity = sr.get("velocity", {})
    daily_counts = velocity.get("daily_counts", {})
    graph_status = sr.get("graph_status", {})
    last_build = graph_status.get("last_build", "")
    total_runs = graph_status.get("total_runs", 0)
    needs_update = graph_status.get("needs_update", False)

    def _fmt_date(iso_str: str) -> str:
        if not iso_str:
            return "N/A"
        try:
            dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return str(iso_str)[:16]

    def _esc(s) -> str:
        return _html.escape(str(s))

    # Prepare initial data JSON for embedding
    initial_data = {
        "project_name": project_name or "Ai-GraphX",
        "graph": {
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(),
            "communities": len(communities),
            "last_build": _fmt_date(last_build),
            "total_runs": total_runs,
            "needs_update": needs_update,
        },
        "branch": current_branch,
        "git": {
            "current_branch": current_branch,
            "total_branches": len(git_info.get("all", [])),
            "untracked_branches": len(git_info.get("untracked", [])),
            "staged_count": len(staged),
            "staged": staged[:10],
            "is_git_repo": bool(sr.get("is_git_repo", False)),
        },
        "activity": {
            "commits": all_commits,
            "merge_commits": merge_commits,
            "hot_files": hot_files,
            "external_files": external_files,
            "large_files": large_files,
            "velocity": {
                "daily_counts": daily_counts,
                "total_commits": velocity.get("total_commits", 0),
                "average_per_day": velocity.get("average_per_day", 0),
            },
        },
        "community_stats": community_stats[:12],
        "total_communities": len(community_stats),
        "god_nodes": gods_preview[:8],
        "audit_trail": audit_trail,
        "outputs_exist": outputs_exist,
    }

    initial_json = _json.dumps(initial_data, default=str)

    title = f"{_esc(project_name or 'Ai-GraphX')} Dashboard"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #0a0a12;
    color: #e0e0e0;
    min-height: 100vh;
    line-height: 1.6;
  }}
  .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}

  /* Header */
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 0;
    border-bottom: 1px solid #1a1a2e;
    margin-bottom: 30px;
    flex-wrap: wrap;
    gap: 10px;
  }}
  .header h1 {{
    font-size: 1.8rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }}
  .header-stats {{ font-size: 0.9rem; color: #888; }}
  .live-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(46,204,113,0.1);
    color: #2ecc71;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
  }}
  .live-dot {{
    width: 8px; height: 8px;
    background: #2ecc71;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }}
  @keyframes pulse {{
    0% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.5; transform: scale(1.2); }}
    100% {{ opacity: 1; transform: scale(1); }}
  }}

  /* Section */
  .section {{ margin-bottom: 40px; }}
  .section h2 {{
    font-size: 1.3rem;
    margin-bottom: 20px;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 10px;
    padding-bottom: 10px;
    border-bottom: 1px solid #1a1a2e;
  }}
  .section h2::before {{
    content: '';
    width: 4px; height: 24px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 2px;
  }}

  /* Build info */
  .info-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
    margin-bottom: 20px;
  }}
  .info-card {{
    background: rgba(255,255,255,0.03);
    border: 1px solid #1a1a2e;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
  }}
  .info-label {{ font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
  .info-value {{ font-size: 1.4rem; font-weight: 700; color: #fff; }}
  .status-ok {{ color: #2ecc71; }}
  .status-warn {{ color: #f39c12; }}

  /* Nav cards */
  .nav-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
    margin-bottom: 20px;
  }}
  .nav-card {{
    background: rgba(255,255,255,0.03);
    border: 1px solid #1a1a2e;
    border-radius: 10px;
    padding: 20px;
    text-decoration: none;
    color: inherit;
    display: block;
    transition: all 0.2s;
  }}
  .nav-card:hover {{ background: rgba(255,255,255,0.06); border-color: #667eea; transform: translateY(-2px); }}
  .nav-card.disabled {{ opacity: 0.4; pointer-events: none; }}
  .nav-card h3 {{ font-size: 1rem; margin-bottom: 6px; color: #fff; }}
  .nav-card p {{ font-size: 0.8rem; color: #888; }}

  /* Activity timeline */
  .timeline {{
    position: relative;
    max-width: 1200px;
    margin: 0 auto;
  }}
  .timeline::after {{
    content: '';
    position: absolute;
    width: 3px;
    background: #1a1a2e;
    top: 0; bottom: 0;
    left: 50%;
    margin-left: -1.5px;
  }}
  .timeline-item {{
    padding: 10px 40px;
    position: relative;
    width: 50%;
  }}
  .timeline-item.left {{ left: 0; }}
  .timeline-item.right {{ left: 50%; }}
  .timeline-item::after {{
    content: '';
    position: absolute;
    width: 16px; height: 16px;
    right: -8px;
    background: #667eea;
    border: 3px solid #0a0a12;
    top: 20px;
    border-radius: 50%;
    z-index: 1;
  }}
  .timeline-item.right::after {{ left: -8px; }}
  .timeline-card {{
    padding: 16px;
    background: rgba(255,255,255,0.03);
    border: 1px solid #1a1a2e;
    border-radius: 10px;
    position: relative;
  }}
  .timeline-card:hover {{ border-color: #667eea; }}
  .tl-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
    flex-wrap: wrap;
  }}
  .tl-hash {{
    font-family: monospace;
    font-size: 0.85rem;
    color: #667eea;
    background: rgba(102,126,234,0.1);
    padding: 2px 8px;
    border-radius: 4px;
  }}
  .tl-source {{
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.65rem;
    text-transform: uppercase;
    font-weight: 700;
  }}
  .ai-badge {{ background: rgba(155,89,182,0.2); color: #9b59b6; }}
  .user-badge {{ background: rgba(46,204,113,0.2); color: #2ecc71; }}
  .tl-date {{ font-size: 0.8rem; color: #888; margin-left: auto; }}
  .tl-author {{ font-size: 0.85rem; color: #aaa; margin-bottom: 6px; }}
  .tl-msg {{ font-size: 0.85rem; color: #ccc; margin-bottom: 10px; word-break: break-word; }}
  .tl-files {{ margin-top: 8px; }}
  .tl-file {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 3px 0;
    font-size: 0.75rem;
    border-bottom: 1px solid rgba(255,255,255,0.03);
  }}
  .tl-file:last-child {{ border-bottom: none; }}
  .tl-action {{
    width: 20px; height: 20px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.6rem;
    font-weight: 700;
    color: #fff;
    flex-shrink: 0;
  }}
  .tl-action.added {{ background: #2ecc71; }}
  .tl-action.modified {{ background: #f39c12; }}
  .tl-action.deleted {{ background: #e74c3c; }}
  .tl-fpath {{ font-family: monospace; color: #bbb; flex: 1; overflow: hidden; text-overflow: ellipsis; }}
  .tl-more {{ color: #888; font-size: 0.75rem; font-style: italic; }}

  /* Hot files */
  .hot-files-list {{ display: flex; flex-direction: column; gap: 8px; }}
  .hot-file-item {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: rgba(255,255,255,0.03);
    border: 1px solid #1a1a2e;
    border-radius: 8px;
    transition: all 0.2s;
  }}
  .hot-file-item:hover {{ border-color: #667eea; }}
  .hot-rank {{
    width: 32px; height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.85rem;
    flex-shrink: 0;
  }}
  .hot-info {{ flex: 1; }}
  .hot-path {{ font-family: monospace; font-size: 0.85rem; color: #ccc; }}
  .hot-meta {{ font-size: 0.75rem; color: #888; margin-top: 2px; }}

  /* File tables */
  .file-table {{ overflow-x: auto; }}
  .file-table table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }}
  .file-table th {{
    text-align: left;
    padding: 10px;
    color: #888;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 1px;
    border-bottom: 1px solid #1a1a2e;
  }}
  .file-table td {{
    padding: 10px;
    border-bottom: 1px solid rgba(255,255,255,0.03);
    color: #ccc;
    font-family: monospace;
    font-size: 0.8rem;
  }}
  .file-table tr:hover td {{ background: rgba(255,255,255,0.02); }}

  /* Velocity */
  .velocity-chart {{ display: flex; flex-direction: column; gap: 8px; }}
  .velocity-row {{
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 0.85rem;
  }}
  .velocity-date {{ width: 100px; color: #888; font-family: monospace; font-size: 0.8rem; flex-shrink: 0; }}
  .velocity-bar-wrap {{
    flex: 1;
    height: 20px;
    background: rgba(255,255,255,0.03);
    border-radius: 4px;
    overflow: hidden;
  }}
  .velocity-bar {{
    height: 100%;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    border-radius: 4px;
    transition: width 0.5s ease;
  }}
  .velocity-count {{ width: 30px; text-align: right; color: #aaa; }}
  .velocity-summary {{
    margin-top: 12px;
    padding: 12px;
    background: rgba(255,255,255,0.03);
    border-radius: 8px;
    font-size: 0.9rem;
    color: #aaa;
    text-align: center;
  }}

  /* Merge commits */
  .merge-list {{ display: flex; flex-direction: column; gap: 8px; }}
  .merge-item {{
    padding: 12px;
    background: rgba(255,255,255,0.03);
    border: 1px solid #1a1a2e;
    border-radius: 8px;
    font-size: 0.85rem;
  }}
  .merge-item:hover {{ border-color: #667eea; }}
  .merge-hash {{
    font-family: monospace;
    color: #667eea;
    background: rgba(102,126,234,0.1);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.8rem;
  }}
  .merge-author {{ color: #aaa; margin-left: 8px; }}
  .merge-date {{ color: #888; margin-left: 8px; font-size: 0.8rem; }}
  .merge-msg {{ color: #ccc; margin-top: 6px; word-break: break-word; }}
  .merge-parents {{ color: #666; font-size: 0.75rem; margin-top: 4px; font-family: monospace; }}

  /* Git status */
  .git-status-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 20px;
  }}
  .git-card {{
    background: rgba(255,255,255,0.03);
    border: 1px solid #1a1a2e;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
  }}
  .git-label {{ font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
  .git-value {{ font-size: 1.3rem; font-weight: 700; color: #fff; }}
  .git-value.branch {{ color: #667eea; }}
  .staged-yes {{ color: #f39c12; }}
  .staged-no {{ color: #2ecc71; }}
  .staged-list {{
    background: rgba(255,255,255,0.02);
    border: 1px solid #1a1a2e;
    border-radius: 10px;
    padding: 16px;
    margin-top: 12px;
  }}
  .staged-list h4 {{ font-size: 0.9rem; color: #aaa; margin-bottom: 12px; }}
  .staged-item {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 6px 0;
    font-size: 0.85rem;
    border-bottom: 1px solid #1a1a2e;
  }}
  .staged-item:last-child {{ border-bottom: none; }}
  .staged-action {{
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.65rem;
    text-transform: uppercase;
    font-weight: 700;
    min-width: 60px;
    text-align: center;
  }}
  .staged-action.added {{ background: #2ecc71; color: #fff; }}
  .staged-action.modified {{ background: #f39c12; color: #fff; }}
  .staged-action.deleted {{ background: #e74c3c; color: #fff; }}
  .staged-path {{ flex: 1; font-family: monospace; font-size: 0.8rem; color: #ccc; }}
  .staged-size {{ color: #666; font-size: 0.75rem; }}

  /* Communities */
  .communities-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 12px;
  }}
  .community-card {{
    background: rgba(255,255,255,0.03);
    border: 1px solid #1a1a2e;
    border-radius: 10px;
    padding: 16px;
    transition: all 0.2s;
  }}
  .community-card:hover {{ background: rgba(255,255,255,0.05); border-color: #667eea; }}
  .community-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
  }}
  .community-dot {{ width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; }}
  .community-name {{ font-weight: 600; color: #fff; font-size: 0.95rem; flex: 1; overflow: hidden; text-overflow: ellipsis; }}
  .community-count {{ font-size: 0.8rem; color: #888; }}
  .community-meta {{ font-size: 0.8rem; color: #aaa; }}
  .cohesion-badge {{
    display: inline-block;
    padding: 3px 8px;
    border-radius: 10px;
    font-size: 0.75rem;
    margin-top: 6px;
  }}
  .cohesion-high {{ background: rgba(46,204,113,0.15); color: #2ecc71; }}
  .cohesion-med {{ background: rgba(241,196,15,0.15); color: #f1c40f; }}
  .cohesion-low {{ background: rgba(231,76,60,0.15); color: #e74c3c; }}

  /* God nodes */
  .god-nodes-list {{ display: flex; flex-direction: column; gap: 8px; }}
  .god-node-item {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: rgba(255,255,255,0.03);
    border: 1px solid #1a1a2e;
    border-radius: 8px;
    transition: all 0.2s;
  }}
  .god-node-item:hover {{ border-color: #667eea; }}
  .god-rank {{
    width: 28px; height: 28px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.8rem;
    flex-shrink: 0;
  }}
  .god-info {{ flex: 1; }}
  .god-name {{ font-weight: 600; color: #fff; font-size: 0.9rem; }}
  .god-degree {{ font-size: 0.8rem; color: #888; }}

  /* Audit trail */
  .audit-trail {{
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }}
  .audit-item {{
    flex: 1;
    min-width: 160px;
    padding: 16px;
    background: rgba(255,255,255,0.03);
    border: 1px solid #1a1a2e;
    border-radius: 10px;
    text-align: center;
  }}
  .audit-value {{ font-size: 1.6rem; font-weight: 700; margin-bottom: 4px; }}
  .audit-value.extracted {{ color: #2ecc71; }}
  .audit-value.inferred {{ color: #f39c12; }}
  .audit-value.ambiguous {{ color: #e74c3c; }}
  .audit-label {{ font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px; }}
  .audit-pct {{ font-size: 0.75rem; color: #666; margin-top: 4px; }}

  /* Empty state */
  .empty-state {{
    color: #666;
    font-style: italic;
    text-align: center;
    padding: 30px;
    font-size: 0.9rem;
  }}

  /* Polling status */
  .poll-status {{
    text-align: center;
    padding: 8px;
    font-size: 0.8rem;
    color: #666;
    margin-top: 10px;
  }}
  .poll-status.updating {{ color: #667eea; }}
  .poll-status.error {{ color: #e74c3c; }}

  /* Footer */
  .footer {{
    text-align: center;
    padding: 30px 20px;
    color: #666;
    font-size: 0.85rem;
    border-top: 1px solid #1a1a2e;
    margin-top: 40px;
  }}
  .footer a {{ color: #667eea; text-decoration: none; }}
  .footer a:hover {{ text-decoration: underline; }}

  @media (max-width: 768px) {{
    .timeline::after {{ left: 20px; }}
    .timeline-item {{ width: 100%; padding-left: 50px; padding-right: 10px; }}
    .timeline-item.right {{ left: 0; }}
    .timeline-item::after {{ left: 12px !important; right: auto !important; }}
    .header {{ flex-direction: column; align-items: flex-start; gap: 10px; }}
    .nav-grid {{ grid-template-columns: 1fr; }}
    .git-status-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .info-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .communities-grid {{ grid-template-columns: 1fr; }}
    .audit-trail {{ flex-direction: column; }}
  }}
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1 id="page-title">{title}</h1>
    <div style="display:flex;align-items:center;gap:12px;">
      <span class="live-badge"><span class="live-dot"></span>Live</span>
      <div class="header-stats" id="header-stats">loading...</div>
    </div>
  </div>

  <div class="section">
    <h2>Graph Status</h2>
    <div class="info-grid" id="graph-status-grid"></div>
    <div class="nav-grid" id="output-nav"></div>
  </div>

  <div class="section">
    <h2>Git Status</h2>
    <div class="git-status-grid" id="git-status-grid"></div>
    <div id="staged-files"></div>
  </div>

  <div class="section">
    <h2>Activity Timeline</h2>
    <div id="activity-timeline"></div>
    <div class="poll-status" id="poll-status">Auto-refreshing every 30s...</div>
  </div>

  <div class="section">
    <h2>Hot Files (Most Changed)</h2>
    <div id="hot-files"></div>
  </div>

  <div class="section">
    <h2>Change Velocity (Last 7 Days)</h2>
    <div id="velocity-chart"></div>
  </div>

  <div class="section">
    <h2>Recent Merge Commits</h2>
    <div id="merge-commits"></div>
  </div>

  <div class="section">
    <h2>External Files (Untracked)</h2>
    <div id="external-files"></div>
  </div>

  <div class="section">
    <h2>Large Files (&gt;10MB)</h2>
    <div id="large-files"></div>
  </div>

  <div class="section">
    <h2 id="communities-title">Communities</h2>
    <div class="communities-grid" id="communities-grid"></div>
  </div>

  <div class="section">
    <h2>God Nodes (Top Connected)</h2>
    <div class="god-nodes-list" id="god-nodes"></div>
  </div>

  <div class="section">
    <h2>Audit Trail</h2>
    <div class="audit-trail" id="audit-trail"></div>
  </div>

  <div class="footer">
    <p>Generated by <a href="https://pypi.org/project/ai-graphx/" target="_blank">Ai-GraphX</a> &middot; <a href="#" onclick="location.reload();return false;">Refresh Dashboard</a></p>
  </div>
</div>

<script>
// Embedded initial data from graph generation
const INITIAL_DATA = {initial_json};

// State for live updates
let currentActivity = null;
let pollTimer = null;

// --- Utility functions ---
function esc(s) {{
  const div = document.createElement('div');
  div.textContent = String(s);
  return div.innerHTML;
}}

function fmtDate(isoStr) {{
  if (!isoStr || isoStr === 'N/A') return 'N/A';
  try {{
    const d = new Date(isoStr);
    if (isNaN(d)) return isoStr.slice(0,16);
    return d.toISOString().slice(0,16).replace('T',' ');
  }} catch(e) {{ return isoStr.slice(0,16); }}
}}

function timeAgo(isoStr) {{
  if (!isoStr) return '';
  try {{
    const d = new Date(isoStr);
    const now = new Date();
    const diff = Math.floor((now - d) / 1000);
    if (diff < 60) return 'just now';
    if (diff < 3600) return Math.floor(diff/60) + 'm ago';
    if (diff < 86400) return Math.floor(diff/3600) + 'h ago';
    return Math.floor(diff/86400) + 'd ago';
  }} catch(e) {{ return ''; }}
}}

// --- Renderers ---
function renderGraphStatus() {{
  const g = INITIAL_DATA.graph;
  const statusClass = g.needs_update ? 'status-warn' : 'status-ok';
  const statusText = g.needs_update ? 'NEEDS UPDATE' : 'OK';
  const html = `
    <div class="info-card"><div class="info-label">Status</div><div class="info-value ${{statusClass}}">${{esc(statusText)}}</div></div>
    <div class="info-card"><div class="info-label">Nodes</div><div class="info-value">${{esc(g.nodes)}}</div></div>
    <div class="info-card"><div class="info-label">Edges</div><div class="info-value">${{esc(g.edges)}}</div></div>
    <div class="info-card"><div class="info-label">Communities</div><div class="info-value">${{esc(g.communities)}}</div></div>
    <div class="info-card"><div class="info-label">Total Runs</div><div class="info-value">${{esc(g.total_runs)}}</div></div>
    <div class="info-card"><div class="info-label">Last Build</div><div class="info-value">${{esc(g.last_build)}}</div></div>
  `;
  document.getElementById('graph-status-grid').innerHTML = html;
  document.getElementById('header-stats').textContent = `${{g.nodes}} nodes \u00b7 ${{g.edges}} edges \u00b7 ${{g.communities}} communities \u00b7 Branch: ${{esc(INITIAL_DATA.branch)}}`;
}}

function renderOutputNav() {{
  const o = INITIAL_DATA.outputs_exist;
  const items = [
    {{key:'graph.html', icon:'🕸', title:'Interactive Graph', desc:'Force-directed visualization'}},
    {{key:'GRAPH_TREE.html', icon:'🌳', title:'Tree View', desc:'Collapsible directory tree'}},
    {{key:'wiki', icon:'📚', title:'Knowledge Wiki', desc:'Wikipedia-style articles'}},
    {{key:'GRAPH_REPORT.md', icon:'📋', title:'Audit Report', desc:'God nodes, connections'}},
    {{key:'graph.json', icon:'📦', title:'Raw Graph JSON', desc:'Download complete data', dl:true}},
    {{key:'graph.svg', icon:'🖼', title:'SVG Export', desc:'Vector graphic', dl:true}},
  ];
  const html = items.map(item => {{
    const disabled = !o[item.key] ? 'disabled' : '';
    const dl = item.dl ? 'download' : '';
    const href = item.key === 'wiki' ? 'wiki/index.md' : item.key;
    return `<a href="${{esc(href)}}" class="nav-card ${{disabled}}" ${{dl}}><h3>${{item.icon}} ${{esc(item.title)}}</h3><p>${{esc(item.desc)}}</p></a>`;
  }}).join('');
  document.getElementById('output-nav').innerHTML = html;
}}

function renderGitStatus() {{
  const g = INITIAL_DATA.git;
  if (!g.is_git_repo) {{
    document.getElementById('git-status-grid').innerHTML = '<p class="empty-state">Not a git repository.</p>';
    document.getElementById('staged-files').innerHTML = '';
    return;
  }}
  const stagedClass = g.staged_count > 0 ? 'staged-yes' : 'staged-no';
  let html = `
    <div class="git-card"><div class="git-label">Current Branch</div><div class="git-value branch">${{esc(g.current_branch)}}</div></div>
    <div class="git-card"><div class="git-label">Total Branches</div><div class="git-value">${{esc(g.total_branches)}}</div></div>
    <div class="git-card"><div class="git-label">Untracked Branches</div><div class="git-value">${{esc(g.untracked_branches)}}</div></div>
    <div class="git-card"><div class="git-label">Staged Changes</div><div class="git-value ${{stagedClass}}">${{esc(g.staged_count)}}</div></div>
  `;
  document.getElementById('git-status-grid').innerHTML = html;

  if (g.staged && g.staged.length > 0) {{
    let stagedHtml = '<div class="staged-list"><h4>Staged Files (Not Committed)</h4>';
    g.staged.forEach(s => {{
      stagedHtml += `<div class="staged-item"><span class="staged-action ${{esc(s.action||'modified')}}">${{esc((s.action||'modified').toUpperCase())}}</span> <span class="staged-path">${{esc(s.file)}}</span> <span class="staged-size">${{Number(s.size||0).toLocaleString()}} bytes</span></div>`;
    }});
    stagedHtml += '</div>';
    document.getElementById('staged-files').innerHTML = stagedHtml;
  }} else {{
    document.getElementById('staged-files').innerHTML = '';
  }}
}}

function renderActivityTimeline(commits) {{
  if (!commits || commits.length === 0) {{
    document.getElementById('activity-timeline').innerHTML = '<p class="empty-state">No commit history found.</p>';
    return;
  }}
  let html = '<div class="timeline">';
  commits.forEach((commit, i) => {{
    const side = i % 2 === 0 ? 'left' : 'right';
    const hash = esc(commit.short_hash || (commit.hash||'').slice(0,7) || '?');
    const author = esc(commit.author || 'Unknown');
    const date = fmtDate(commit.date);
    const msg = esc((commit.message||'').slice(0,80));
    const source = commit.source === 'ai' ? 'ai' : 'user';
    const badgeClass = source === 'ai' ? 'ai-badge' : 'user-badge';
    const badgeLabel = source === 'ai' ? 'AI' : 'USER';
    const files = commit.files_changed || [];
    let filesHtml = '';
    files.slice(0,8).forEach(fc => {{
      const action = fc.action || 'modified';
      filesHtml += `<div class="tl-file"><span class="tl-action ${{esc(action)}}">${{esc(action.charAt(0).toUpperCase())}}</span><span class="tl-fpath">${{esc(fc.file)}}</span></div>`;
    }});
    if (files.length > 8) {{
      filesHtml += `<div class="tl-file"><span class="tl-more">+${{files.length - 8}} more files</span></div>`;
    }}
    html += `
      <div class="timeline-item ${{side}}">
        <div class="timeline-dot"></div>
        <div class="timeline-card">
          <div class="tl-header">
            <span class="tl-hash">${{hash}}</span>
            <span class="tl-source ${{badgeClass}}">${{badgeLabel}}</span>
            <span class="tl-date">${{date}}</span>
          </div>
          <div class="tl-author">${{author}}</div>
          <div class="tl-msg">${{msg}}</div>
          <div class="tl-files">${{filesHtml}}</div>
        </div>
      </div>
    `;
  }});
  html += '</div>';
  document.getElementById('activity-timeline').innerHTML = html;
}}

function renderHotFiles(hotFiles) {{
  if (!hotFiles || hotFiles.length === 0) {{
    document.getElementById('hot-files').innerHTML = '<p class="empty-state">No hot files detected yet.</p>';
    return;
  }}
  let html = '<div class="hot-files-list">';
  hotFiles.forEach(hf => {{
    const fpath = esc(hf.file || '?');
    const count = hf.commit_count || 0;
    const last = hf.last_commit || {{}};
    const lastHash = esc((last.hash||'').slice(0,7) || '?');
    const lastDate = fmtDate(last.date);
    const srcIcon = last.source === 'ai' ? '&#129302;' : '&#128100;';
    html += `
      <div class="hot-file-item">
        <div class="hot-rank">${{esc(count)}}</div>
        <div class="hot-info">
          <div class="hot-path">${{fpath}}</div>
          <div class="hot-meta">Last: ${{lastHash}} &middot; ${{lastDate}} &middot; ${{srcIcon}}</div>
        </div>
      </div>
    `;
  }});
  html += '</div>';
  document.getElementById('hot-files').innerHTML = html;
}}

function renderVelocity(velocity) {{
  const daily = velocity.daily_counts || {{}};
  const entries = Object.entries(daily).sort().reverse().slice(0,14);
  if (entries.length === 0) {{
    document.getElementById('velocity-chart').innerHTML = '<p class="empty-state">No velocity data available.</p>';
    return;
  }}
  const maxCount = Math.max(...entries.map(e => e[1]), 1);
  let html = '<div class="velocity-chart">';
  entries.forEach(([date, count]) => {{
    const pct = (count / maxCount * 100).toFixed(0);
    html += `
      <div class="velocity-row">
        <div class="velocity-date">${{esc(date)}}</div>
        <div class="velocity-bar-wrap"><div class="velocity-bar" style="width:${{pct}}%"></div></div>
        <div class="velocity-count">${{esc(count)}}</div>
      </div>
    `;
  }});
  html += '</div>';
  html += `<div class="velocity-summary">Total: ${{esc(velocity.total_commits||0)}} commits &middot; Avg: ${{Number(velocity.average_per_day||0).toFixed(1)}}/day</div>`;
  document.getElementById('velocity-chart').innerHTML = html;
}}

function renderMergeCommits(merges) {{
  if (!merges || merges.length === 0) {{
    document.getElementById('merge-commits').innerHTML = '<p class="empty-state">No merge commits found.</p>';
    return;
  }}
  let html = '<div class="merge-list">';
  merges.forEach(mc => {{
    const hash = esc(mc.hash || '?');
    const author = esc(mc.author || '?');
    const date = fmtDate(mc.date);
    const msg = esc((mc.message||'').slice(0,60));
    const parents = (mc.parents || []).join(', ');
    html += `
      <div class="merge-item">
        <span class="merge-hash">${{hash}}</span>
        <span class="merge-author">${{author}}</span>
        <span class="merge-date">${{date}}</span>
        <div class="merge-msg">${{msg}}</div>
        <div class="merge-parents">merged: ${{esc(parents)}}</div>
      </div>
    `;
  }});
  html += '</div>';
  document.getElementById('merge-commits').innerHTML = html;
}}

function renderExternalFiles(files) {{
  if (!files || files.length === 0) {{
    document.getElementById('external-files').innerHTML = '<p class="empty-state">No external (untracked) files detected.</p>';
    return;
  }}
  let html = '<div class="file-table"><table><thead><tr><th>File</th><th>Created</th><th>Modified</th><th>Size</th></tr></thead><tbody>';
  files.forEach(ef => {{
    const size = Number(ef.size || 0) / (1024*1024);
    html += `<tr><td>${{esc(ef.file||'')}}</td><td>${{fmtDate(ef.created)}}</td><td>${{fmtDate(ef.modified)}}</td><td>${{size.toFixed(2)}} MB</td></tr>`;
  }});
  html += '</tbody></table></div>';
  document.getElementById('external-files').innerHTML = html;
}}

function renderLargeFiles(files) {{
  if (!files || files.length === 0) {{
    document.getElementById('large-files').innerHTML = '<p class="empty-state">No large files (&gt;10MB) detected.</p>';
    return;
  }}
  let html = '<div class="file-table"><table><thead><tr><th>File</th><th>Size</th></tr></thead><tbody>';
  files.forEach(lf => {{
    html += `<tr><td>${{esc(lf.file||'')}}</td><td>${{Number(lf.size_mb||0).toFixed(2)}} MB</td></tr>`;
  }});
  html += '</tbody></table></div>';
  document.getElementById('large-files').innerHTML = html;
}}

function renderCommunities() {{
  const comms = INITIAL_DATA.community_stats;
  const total = INITIAL_DATA.total_communities;
  document.getElementById('communities-title').textContent = `Communities (${{total}})`;
  let html = '';
  comms.forEach(c => {{
    const cohesionClass = c.cohesion >= 0.7 ? 'cohesion-high' : c.cohesion >= 0.4 ? 'cohesion-med' : 'cohesion-low';
    const cohesionText = c.cohesion ? `Cohesion: ${{c.cohesion.toFixed(2)}}` : 'Cohesion: N/A';
    const topNode = esc((c.top_node||'').slice(0,40));
    const topSuffix = (c.top_node||'').length > 40 ? '...' : '';
    html += `
      <div class="community-card">
        <div class="community-header">
          <div class="community-dot" style="background:${{esc(c.color)}}"></div>
          <div class="community-name">${{esc(c.label)}}</div>
          <div class="community-count">${{esc(c.count)}} nodes</div>
        </div>
        <div class="community-meta">Top: ${{topNode}}${{topSuffix}}</div>
        <span class="cohesion-badge ${{cohesionClass}}">${{esc(cohesionText)}}</span>
      </div>
    `;
  }});
  if (total > comms.length) {{
    html += `<div class="community-card" style="display:flex;align-items:center;justify-content:center;color:#888;"><div>+${{total - comms.length}} more communities</div></div>`;
  }}
  document.getElementById('communities-grid').innerHTML = html;
}}

function renderGodNodes() {{
  const gods = INITIAL_DATA.god_nodes;
  let html = '';
  gods.forEach((god, idx) => {{
    html += `
      <div class="god-node-item">
        <div class="god-rank">${{idx+1}}</div>
        <div class="god-info">
          <div class="god-name">${{esc(god.label || 'Unknown')}}</div>
          <div class="god-degree">${{esc(god.degree || 0)}} connections</div>
        </div>
      </div>
    `;
  }});
  document.getElementById('god-nodes').innerHTML = html;
}}

function renderAuditTrail() {{
  const trail = INITIAL_DATA.audit_trail;
  let html = '';
  trail.forEach(a => {{
    html += `
      <div class="audit-item">
        <div class="audit-value ${{esc(a.type.toLowerCase())}}">${{esc(a.count)}}</div>
        <div class="audit-label">${{esc(a.type)}}</div>
        <div class="audit-pct">${{esc(a.pct)}}%</div>
      </div>
    `;
  }});
  document.getElementById('audit-trail').innerHTML = html;
}}

// --- Live polling for activity.json ---
async function fetchActivity() {{
  try {{
    const resp = await fetch('activity.json', {{ cache: 'no-store' }});
    if (!resp.ok) return null;
    return await resp.json();
  }} catch (e) {{
    return null;
  }}
}}

async function updateActivityFromJson() {{
  const statusEl = document.getElementById('poll-status');
  statusEl.textContent = 'Checking for updates...';
  statusEl.className = 'poll-status updating';

  const data = await fetchActivity();
  if (!data) {{
    statusEl.textContent = 'Live updates paused (refresh page for latest). Run `graphx serve` for live polling.';
    statusEl.className = 'poll-status error';
    return;
  }}

  const commits = data.commits || [];
  // Only update if different from current embedded data
  if (JSON.stringify(commits) !== JSON.stringify(currentActivity)) {{
    currentActivity = commits;
    renderActivityTimeline(commits);
    // Also update related sections if present
    if (data.hot_files) renderHotFiles(data.hot_files);
    statusEl.textContent = `Updated ${{commits.length}} commits from activity.json`;
    statusEl.className = 'poll-status';
  }} else {{
    statusEl.textContent = 'Up to date. Next check in 30s...';
    statusEl.className = 'poll-status';
  }}
}}

// --- Main render ---
function renderAll() {{
  renderGraphStatus();
  renderOutputNav();
  renderGitStatus();

  const act = INITIAL_DATA.activity;
  currentActivity = act.commits;
  renderActivityTimeline(act.commits);
  renderHotFiles(act.hot_files);
  renderVelocity(act.velocity);
  renderMergeCommits(act.merge_commits);
  renderExternalFiles(act.external_files);
  renderLargeFiles(act.large_files);

  renderCommunities();
  renderGodNodes();
  renderAuditTrail();
}}

// Initialize
document.addEventListener('DOMContentLoaded', () => {{
  renderAll();
  // Poll for live activity updates every 30 seconds
  pollTimer = setInterval(updateActivityFromJson, 30000);
  // First check after 2 seconds (give browser time to settle)
  setTimeout(updateActivityFromJson, 2000);
}});
</script>
</body>
</html>
"""
    (out / "index.html").write_text(html, encoding="utf-8")

def to_canvas(
    G: nx.Graph,
    communities: dict[int, list[str]],
    output_path: str,
    community_labels: dict[int, str] | None = None,
    node_filenames: dict[str, str] | None = None,
) -> None:
    """Export graph as an Obsidian Canvas file - communities as groups, nodes as cards.

    Generates a structured layout: communities arranged in a grid, nodes within
    each community arranged in rows. Edges shown between connected nodes.
    Opens in Obsidian as an infinite canvas with community groupings visible.
    """
    # Obsidian canvas color codes (cycle through for communities)
    CANVAS_COLORS = ["1", "2", "3", "4", "5", "6"]  # red, orange, yellow, green, cyan, purple

    def safe_name(label: str) -> str:
        cleaned = re.sub(r'[\\/*?:"<>|#^[\]]', "", label.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")).strip()
        cleaned = re.sub(r"\.(md|mdx|markdown)$", "", cleaned, flags=re.IGNORECASE)
        return cleaned or "unnamed"

    # Build node_filenames if not provided (same dedup logic as to_obsidian)
    if node_filenames is None:
        node_filenames = {}
        seen_names: dict[str, int] = {}
        for node_id, data in G.nodes(data=True):
            base = safe_name(data.get("label", node_id))
            if base in seen_names:
                seen_names[base] += 1
                node_filenames[node_id] = f"{base}_{seen_names[base]}"
            else:
                seen_names[base] = 0
                node_filenames[node_id] = base

    num_communities = len(communities)
    cols = math.ceil(math.sqrt(num_communities)) if num_communities > 0 else 1
    rows = math.ceil(num_communities / cols) if num_communities > 0 else 1

    canvas_nodes: list[dict] = []
    canvas_edges: list[dict] = []

    # Lay out communities in a grid
    gap = 80
    group_x_offsets: list[int] = []
    group_y_offsets: list[int] = []

    # Precompute group sizes so we can calculate offsets
    sorted_cids = sorted(communities.keys())
    group_sizes: dict[int, tuple[int, int]] = {}
    for cid in sorted_cids:
        members = communities[cid]
        n = len(members)
        w = max(600, 220 * math.ceil(math.sqrt(n)) if n > 0 else 600)
        h = max(400, 100 * math.ceil(n / 3) + 120 if n > 0 else 400)
        group_sizes[cid] = (w, h)

    # Compute cumulative row heights and col widths for grid placement
    # Each grid cell uses the max width/height in its col/row
    col_widths: list[int] = []
    row_heights: list[int] = []
    for col_idx in range(cols):
        max_w = 0
        for row_idx in range(rows):
            linear = row_idx * cols + col_idx
            if linear < len(sorted_cids):
                cid = sorted_cids[linear]
                w, _ = group_sizes[cid]
                max_w = max(max_w, w)
        col_widths.append(max_w)

    for row_idx in range(rows):
        max_h = 0
        for col_idx in range(cols):
            linear = row_idx * cols + col_idx
            if linear < len(sorted_cids):
                cid = sorted_cids[linear]
                _, h = group_sizes[cid]
                max_h = max(max_h, h)
        row_heights.append(max_h)

    # Map from cid → (group_x, group_y, group_w, group_h)
    group_layout: dict[int, tuple[int, int, int, int]] = {}
    for idx, cid in enumerate(sorted_cids):
        col_idx = idx % cols
        row_idx = idx // cols
        gx = sum(col_widths[:col_idx]) + col_idx * gap
        gy = sum(row_heights[:row_idx]) + row_idx * gap
        gw, gh = group_sizes[cid]
        group_layout[cid] = (gx, gy, gw, gh)

    # Build set of all node_ids in canvas for edge filtering
    all_canvas_nodes: set[str] = set()
    for members in communities.values():
        all_canvas_nodes.update(members)

    # Generate group and node canvas entries
    for idx, cid in enumerate(sorted_cids):
        members = communities[cid]
        community_name = (
            community_labels.get(cid, f"Community {cid}")
            if community_labels and cid is not None
            else f"Community {cid}"
        )
        gx, gy, gw, gh = group_layout[cid]
        canvas_color = CANVAS_COLORS[idx % len(CANVAS_COLORS)]

        # Group node
        canvas_nodes.append({
            "id": f"g{cid}",
            "type": "group",
            "label": community_name,
            "x": gx,
            "y": gy,
            "width": gw,
            "height": gh,
            "color": canvas_color,
        })

        # Node cards inside the group - rows of 3
        sorted_members = sorted(members, key=lambda n: G.nodes[n].get("label", n))
        for m_idx, node_id in enumerate(sorted_members):
            col = m_idx % 3
            row = m_idx // 3
            nx_x = gx + 20 + col * (180 + 20)
            nx_y = gy + 80 + row * (60 + 20)
            fname = node_filenames.get(node_id, safe_name(G.nodes[node_id].get("label", node_id)))
            canvas_nodes.append({
                "id": f"n_{node_id}",
                "type": "file",
                "file": f"{fname}.md",
                "x": nx_x,
                "y": nx_y,
                "width": 180,
                "height": 60,
            })

    # Generate edges - only between nodes both in canvas, cap at 200 highest-weight
    all_edges_weighted: list[tuple[float, str, str, str]] = []
    for u, v, edata in G.edges(data=True):
        if u in all_canvas_nodes and v in all_canvas_nodes:
            weight = edata.get("weight", 1.0)
            relation = edata.get("relation", "")
            conf = edata.get("confidence", "EXTRACTED")
            label = f"{relation} [{conf}]" if relation else f"[{conf}]"
            all_edges_weighted.append((weight, u, v, label))

    all_edges_weighted.sort(key=lambda x: -x[0])
    for weight, u, v, label in all_edges_weighted[:200]:
        canvas_edges.append({
            "id": f"e_{u}_{v}",
            "fromNode": f"n_{u}",
            "toNode": f"n_{v}",
            "label": label,
        })

    canvas_data = {"nodes": canvas_nodes, "edges": canvas_edges}
    Path(output_path).write_text(json.dumps(canvas_data, indent=2), encoding="utf-8")  # nosec


def push_to_neo4j(
    G: nx.Graph,
    uri: str,
    user: str,
    password: str,
    communities: dict[int, list[str]] | None = None,
) -> dict[str, int]:
    """Push graph directly to a running Neo4j instance via the Python driver.

    Requires: pip install neo4j

    Uses MERGE so re-running is safe - nodes and edges are upserted, not duplicated.
    Returns a dict with counts of nodes and edges pushed.
    """
    try:
        from neo4j import GraphDatabase
    except ImportError as e:
        raise ImportError(
            "neo4j driver not installed. Run: pip install neo4j"
        ) from e

    node_community = _node_community_map(communities) if communities else {}

    def _safe_rel(relation: str) -> str:
        return re.sub(r"[^A-Z0-9_]", "_", relation.upper().replace(" ", "_").replace("-", "_")) or "RELATED_TO"

    def _safe_label(label: str) -> str:
        """Sanitize a Neo4j node label to prevent Cypher injection."""
        sanitized = re.sub(r"[^A-Za-z0-9_]", "", label)
        return sanitized if sanitized else "Entity"

    driver = GraphDatabase.driver(uri, auth=(user, password))
    nodes_pushed = 0
    edges_pushed = 0

    with driver.session() as session:
        for node_id, data in G.nodes(data=True):
            props = {k: v for k, v in data.items() if isinstance(v, (str, int, float, bool))}
            props["id"] = node_id
            cid = node_community.get(node_id)
            if cid is not None:
                props["community"] = cid
            ftype = _safe_label(data.get("file_type", "Entity").capitalize())
            session.run(
                f"MERGE (n:{ftype} {{id: $id}}) SET n += $props",
                id=node_id,
                props=props,
            )
            nodes_pushed += 1

        for u, v, data in G.edges(data=True):
            rel = _safe_rel(data.get("relation", "RELATED_TO"))
            props = {k: v for k, v in data.items() if isinstance(v, (str, int, float, bool))}
            session.run(
                f"MATCH (a {{id: $src}}), (b {{id: $tgt}}) "
                f"MERGE (a)-[r:{rel}]->(b) SET r += $props",
                src=u,
                tgt=v,
                props=props,
            )
            edges_pushed += 1

    driver.close()
    return {"nodes": nodes_pushed, "edges": edges_pushed}


def to_graphml(
    G: nx.Graph,
    communities: dict[int, list[str]],
    output_path: str,
) -> None:
    """Export graph as GraphML - opens in Gephi, yEd, and any GraphML-compatible tool.

    Community IDs are written as a node attribute so Gephi can colour by community.
    Edge confidence (EXTRACTED/INFERRED/AMBIGUOUS) is preserved as an edge attribute.
    """
    H = G.copy()
    node_community = _node_community_map(communities)
    for node_id in H.nodes():
        H.nodes[node_id]["community"] = node_community.get(node_id, -1)
    nx.write_graphml(H, output_path)


def to_svg(
    G: nx.Graph,
    communities: dict[int, list[str]],
    output_path: str,
    community_labels: dict[int, str] | None = None,
    figsize: tuple[int, int] = (20, 14),
) -> None:
    """Export graph as an SVG file using matplotlib + spring layout.

    Lightweight and embeddable - works in Obsidian notes, Notion, GitHub READMEs,
    and any markdown renderer. No JavaScript required.

    Node size scales with degree. Community colors match the HTML output.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError as e:
        raise ImportError("matplotlib not installed. Run: pip install matplotlib") from e

    node_community = _node_community_map(communities)

    fig, ax = plt.subplots(figsize=figsize, facecolor="#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    ax.axis("off")

    pos = nx.spring_layout(G, seed=42, k=2.0 / (G.number_of_nodes() ** 0.5 + 1))

    degree = dict(G.degree())
    max_deg = max(degree.values(), default=1) or 1

    node_colors = [COMMUNITY_COLORS[node_community.get(n, 0) % len(COMMUNITY_COLORS)] for n in G.nodes()]
    node_sizes = [300 + 1200 * (degree.get(n, 1) / max_deg) for n in G.nodes()]

    # Draw edges - dashed for non-EXTRACTED
    for u, v, data in G.edges(data=True):
        conf = data.get("confidence", "EXTRACTED")
        style = "solid" if conf == "EXTRACTED" else "dashed"
        alpha = 0.6 if conf == "EXTRACTED" else 0.3
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        ax.plot([x0, x1], [y0, y1], color="#aaaaaa", linewidth=0.8,
                linestyle=style, alpha=alpha, zorder=1)

    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                           node_size=node_sizes, alpha=0.9)
    nx.draw_networkx_labels(G, pos, ax=ax,
                            labels={n: G.nodes[n].get("label", n) for n in G.nodes()},
                            font_size=7, font_color="white")

    # Legend
    if community_labels:
        patches = [
            mpatches.Patch(
                color=COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)],
                label=f"{label} ({len(communities.get(cid, []))})",
            )
            for cid, label in sorted(community_labels.items())
        ]
        ax.legend(handles=patches, loc="upper left", framealpha=0.7,
                  facecolor="#2a2a4e", labelcolor="white", fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, format="svg", bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
