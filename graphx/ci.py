import networkx as nx
from networkx.readwrite import json_graph
import json
from pathlib import Path

def generate_ci_report(G_old: nx.Graph, G_new: nx.Graph) -> str:
    """Compare two graphs and return a Markdown report for PR comments."""
    
    # 1. Basic Stats
    old_n, old_e = G_old.number_of_nodes(), G_old.number_of_edges()
    new_n, new_e = G_new.number_of_nodes(), G_new.number_of_edges()
    
    lines = [
        "# Architectural Health Report",
        "",
        "| Metric | Baseline | Current | Delta |",
        "| :--- | :--- | :--- | :--- |",
        f"| Nodes | {old_n} | {new_n} | {new_n - old_n:+d} |",
        f"| Edges | {old_e} | {new_e} | {new_e - old_e:+d} |",
        "",
        "## Key Changes"
    ]
    
    # 2. Dependency Tracking (detecting new cross-file dependencies)
    old_edges = set((u, v) for u, v, d in G_old.edges(data=True) if d.get('relation') == 'calls')
    new_edges = set((u, v) for u, v, d in G_new.edges(data=True) if d.get('relation') == 'calls')
    
    added_deps = new_edges - old_edges
    if added_deps:
        lines.append("### New Dependencies")
        for u, v in sorted(list(added_deps)[:10]):
            u_label = G_new.nodes[u].get('label', u)
            v_label = G_new.nodes[v].get('label', v)
            lines.append(f"- `{u_label}` → `{v_label}`")
    
    # 3. Structural Integrity (God Node shifts)
    old_degrees = sorted([(d, n) for n, d in G_old.degree()], reverse=True)
    new_degrees = sorted([(d, n) for n, d in G_new.degree()], reverse=True)
    
    top_old = {n: d for d, n in old_degrees[:5]}
    top_new = {n: d for d, n in new_degrees[:5]}
    
    sig_shifts = []
    for n, d in top_new.items():
        if n in top_old and abs(d - top_old[n]) > 5:
            sig_shifts.append(f"- `{G_new.nodes[n].get('label', n)}`: {top_old[n]} → {d}")
            
    if sig_shifts:
        lines.append("")
        lines.append("### Significant Structural Shifts (God Nodes)")
        lines.extend(sig_shifts)
        
    lines.append("")
    lines.append("> 💡 **Run `/graphx query` for deep analysis of these changes.**")
    
    return "\n".join(lines)
