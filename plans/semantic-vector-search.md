# Plan: Implementing Semantic Vector Search in Ai-GraphX

This plan outlines the integration of vector embeddings for semantic search in Ai-GraphX.

## Objective
Enable semantic similarity search across nodes in the knowledge graph, allowing users to find files and concepts based on meaning rather than exact label matches.

## Phase 1: Embedding Generation
- **Integration**: Add a new module `graphx/vector.py` that utilizes `sentence-transformers` for local embedding generation.
- **Workflow**: Integrate into the build pipeline after `extract` to compute embeddings for all file nodes.
- **Storage**: Append `embedding: [float32]` vector to node metadata in `graph.json`.

## Phase 2: Indexing & Search
- **Indexing**: Implement a basic FAISS indexer (or HNSWlib) in `graphx/vector.py` for efficient vector lookups.
- **Command Integration**:
    - `graphx query --semantic "<query>"`: Enhances current BFS query with semantic similarity as a ranking factor.
    - `graphx explain <node> --similar`: Uses vector search to find conceptually related nodes even if they are not connected in the graph.

## Phase 3: Dashboard Visualization
- **UI**: Add a "Semantic Search" bar to the Explorer tab in `index.html`.
- **Interaction**: Selecting a search result focuses the graph on the most semantically similar node.

## Technical Requirements
- `sentence-transformers`: For local, privacy-preserving embedding generation.
- `faiss-cpu`: For high-performance vector search.
- Storage: Keep indices in `graphx-out/vectors.index` and `graphx-out/nodes.json`.

## Verification Plan
1. **Embedding Check**: Verify that `graph.json` contains the `embedding` key for nodes.
2. **Semantic Query Test**: Run `graphx query --semantic "data processing"` and confirm it identifies related nodes not directly linked.
3. **Dashboard Test**: Ensure the search bar in the unified dashboard accurately highlights similar nodes.
