# Graph Report - GraphX  (2026-05-06)

## Corpus Check
- 96 files · ~185,636 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1753 nodes · 3155 edges · 97 communities detected
- Extraction: 76% EXTRACTED · 24% INFERRED · 0% AMBIGUOUS · INFERRED: 772 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 91|Community 91]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 95|Community 95]]
- [[_COMMUNITY_Community 96|Community 96]]
- [[_COMMUNITY_Community 97|Community 97]]

## God Nodes (most connected - your core abstractions)
1. `main()` - 43 edges
2. `_make_id()` - 34 edges
3. `_labels()` - 34 edges
4. `detect()` - 33 edges
5. `Client` - 27 edges
6. `AsyncClient` - 26 edges
7. `Response` - 26 edges
8. `extract_swift()` - 25 edges
9. `extract_python()` - 23 edges
10. `to_wiki()` - 23 edges

## Surprising Connections (you probably didn't know these)
- `test_make_id_strips_dots_and_underscores()` --calls--> `_make_id()`  [INFERRED]
  tests/test_extract.py → graphx/extract.py
- `test_make_id_no_leading_trailing_underscores()` --calls--> `_make_id()`  [INFERRED]
  tests/test_extract.py → graphx/extract.py
- `test_print_benchmark_error_message()` --calls--> `print_benchmark()`  [INFERRED]
  tests/test_benchmark.py → graphx/benchmark.py
- `test_classify_python()` --calls--> `classify_file()`  [INFERRED]
  tests/test_detect.py → graphx/detect.py
- `test_classify_typescript()` --calls--> `classify_file()`  [INFERRED]
  tests/test_detect.py → graphx/detect.py

## Communities (100 total, 12 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (68): _detect_url_type(), _download_binary(), _fetch_arxiv(), _fetch_html(), _fetch_tweet(), _fetch_webpage(), _html_to_markdown(), ingest() (+60 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (53): _body_content(), cache_dir(), cached_files(), check_semantic_cache(), clear_cache(), file_hash(), load_cached(), _normalize_path() (+45 more)

### Community 2 - "Community 2"
Cohesion: 0.1
Nodes (45): _bfs(), _communities_from_graph(), _dfs(), _filter_blank_stdin(), _filter_graph_by_context(), _find_node(), _infer_context_filters(), _load_graph() (+37 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (43): generate(), Mirrors export.safe_name so community hub filenames and report wikilinks always, _safe_community_name(), _make_extraction(), Tests for confidence_score on edges., Report summary line should include avg confidence for INFERRED edges., Surprising connections section shows confidence score next to INFERRED edges., Return a minimal extraction dict with one edge of each confidence type. (+35 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (45): collect_files(), extract_python(), Extract classes, functions, and imports from a .py file via tree-sitter AST., After merging multiple files, no internal edges should be dangling., Call-graph pass must produce INFERRED calls edges., AST-resolved call edges are deterministic and should be EXTRACTED/1.0., Same input always produces same output., run_analysis() calls compute_score() - must appear as a calls edge. (+37 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (43): _agents_install(), _agents_uninstall(), _install(), Tests for graphx install --platform routing., Claude platform install writes CLAUDE.md; others do not., Installing twice does not duplicate the section., Installs into an existing AGENTS.md without overwriting other content., Uninstall keeps pre-existing content. (+35 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (42): generate_ci_report(), Compare two graphs and return a Markdown report for PR comments., Generate a dynamic SPA dashboard HTML that renders from embedded data     and p, to_index_html(), _agents_uninstall(), _antigravity_install(), _antigravity_uninstall(), _arg_value() (+34 more)

### Community 7 - "Community 7"
Cohesion: 0.1
Nodes (39): extract_go(), extract_rust(), extract_sql(), Extract tables, views, functions, and relationships from .sql files via tree-sit, Extract functions, methods, type declarations, and imports from a .go file., Extract functions, structs, enums, traits, impl methods, and use declarations fr, _call_pairs(), _confidences() (+31 more)

### Community 8 - "Community 8"
Cohesion: 0.1
Nodes (38): _csharp_extra_walk(), _dynamic_import_js(), extract_blade(), _find_body(), _get_c_func_name(), _get_cpp_func_name(), _import_c(), _import_csharp() (+30 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (34): build_whisper_prompt(), download_audio(), _get_whisper(), _get_yt_dlp(), is_url(), _model_name(), Transcribe a video/audio file or URL to a .txt transcript.      If video_path, Transcribe a list of video/audio files or URLs, return paths to transcript .txt (+26 more)

### Community 10 - "Community 10"
Cohesion: 0.08
Nodes (30): get_recent_activity(), _get_staged_changes(), _is_ai_commit(), Get files that are staged but not committed., Detect if a commit was authored by an AI coding assistant., Generate activity.json and write it to the graphx output directory.      Retur, Extract recent git commits with file-change detail for the activity timeline., save_activity() (+22 more)

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (32): build(), build_from_json(), build_merge(), deduplicate_by_label(), _norm_label(), _norm_source_file(), _normalize_id(), Merge multiple extraction results into one graph.      directed=True produces (+24 more)

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (33): claude_install(), claude_uninstall(), _install_claude_hook(), Write the graphx section to the local CLAUDE.md., Add graphx PreToolUse hook to .claude/settings.json., Remove graphx PreToolUse hook from .claude/settings.json., Remove the graphx section from the local CLAUDE.md., _uninstall_claude_hook() (+25 more)

### Community 13 - "Community 13"
Cohesion: 0.1
Nodes (17): ConnectError, ProtocolError, An error occurred at the transport layer., Failed to establish a connection., A protocol was violated., TransportError, BaseTransport, ConnectionPool (+9 more)

### Community 14 - "Community 14"
Cohesion: 0.14
Nodes (28): _community_article(), _cross_community_links(), _god_node_article(), _index_md(), Make a label safe for use as a filename across platforms.      Substitutes cha, Generate a Wikipedia-style wiki from the graph.      Writes:       - index.md, Return (community_label, edge_count) pairs for cross-community connections, sort, _safe_filename() (+20 more)

### Community 15 - "Community 15"
Cohesion: 0.1
Nodes (28): calculate_change_velocity(), detect_external_files(), detect_large_files(), generate_status_report(), get_branch_status(), get_graph_status(), get_hot_files(), get_merge_commits() (+20 more)

### Community 16 - "Community 16"
Cohesion: 0.11
Nodes (4): AsyncClient, Client, Asynchronous HTTP client., Synchronous HTTP client.

### Community 17 - "Community 17"
Cohesion: 0.1
Nodes (6): BaseClient, Shared implementation for Client and AsyncClient.     Handles auth, redirects, c, Cookies, Headers, Core data models: URL, Headers, Cookies, Request, Response. These are the centra, URL

### Community 18 - "Community 18"
Cohesion: 0.12
Nodes (26): _cross_community_surprises(), _cross_file_surprises(), _cross_language(), _file_category(), god_nodes(), graph_diff(), _is_concept_node(), _is_file_node() (+18 more)

### Community 19 - "Community 19"
Cohesion: 0.09
Nodes (26): Enum, _could_contain_included_path(), detect_incremental(), FileType, _is_ignored(), _is_included(), _is_noise_dir(), _is_sensitive() (+18 more)

### Community 20 - "Community 20"
Cohesion: 0.11
Nodes (23): make_graph(), _make_simple_graph(), Tests for analyze.py., Code↔paper edge should score higher than code↔code edge., Helper: build a small nx.Graph from node/edge specs., Multi-file graph: should find cross-file edges between real entities., Concept nodes (empty source_file) must not appear in surprises., Single-file graph: should return cross-community edges, not empty list. (+15 more)

### Community 21 - "Community 21"
Cohesion: 0.11
Nodes (15): Auth, BasicAuth, BearerAuth, DigestAuth, NetRCAuth, Authentication handlers. Auth objects are callables that modify a request before, Load credentials from ~/.netrc based on the request host., Base class for all authentication handlers. (+7 more)

### Community 22 - "Community 22"
Cohesion: 0.13
Nodes (24): _cross_community_surprises(), _cross_file_surprises(), _file_category(), god_nodes(), graph_diff(), _is_concept_node(), _is_file_node(), _node_community_map() (+16 more)

### Community 23 - "Community 23"
Cohesion: 0.14
Nodes (23): extract_julia(), extract_objc(), Extract modules, structs, functions, imports, and calls from a .jl file., Extract interfaces, implementations, protocols, methods, and imports from .m/.mm, Tests for language extractors: Java, C, C++, Ruby, C#, Kotlin, Scala, PHP, Swift, test_julia_call_edges_have_call_context(), test_julia_finds_abstract_type(), test_julia_finds_calls() (+15 more)

### Community 24 - "Community 24"
Cohesion: 0.1
Nodes (23): _pack_chunks_by_tokens(), Greedily pack files into chunks that fit a token budget.      Files are first, Greedily pack files into chunks that fit a token budget.      Files are first, no_tokenizer(), Tests for token-aware chunking and parallel chunk execution in graphx.llm., Force the chars/4 fallback so packing math is deterministic regardless     of w, When tiktoken is installed, the estimator should call into it for     accurate, Without tiktoken installed, the estimator falls back to chars/4. (+15 more)

### Community 25 - "Community 25"
Cohesion: 0.19
Nodes (22): _estimate_tokens(), print_benchmark(), _query_subgraph_tokens(), Token-reduction benchmark - measures how much context graphx saves vs naive full, Print a human-readable benchmark report., Run BFS from best-matching nodes and return estimated tokens in the subgraph con, Measure token reduction: corpus tokens vs graphx query tokens.      Args:, run_benchmark() (+14 more)

### Community 26 - "Community 26"
Cohesion: 0.09
Nodes (23): detect(), Comment lines in .graphxignore are not treated as patterns., Without a VCS root, parent .graphxignore does NOT apply (hermetic)., Upward search stops at the git repo root (.git directory)., A .graphxignore at the git repo root is included when scanning a subdir., detect() result always includes a 'video' key even with no video files., detect() correctly counts video files and does not add them to word count., Video files do not contribute to total_words. (+15 more)

### Community 27 - "Community 27"
Cohesion: 0.23
Nodes (21): Export graph as GraphML - opens in Gephi, yEd, and any GraphML-compatible tool., to_graphml(), str, make_graph(), to_html accepts member_counts without raising., Node file paths in canvas must be vault-root-relative (just fname.md), not hardc, test_to_canvas_file_paths_relative_to_vault(), test_to_cypher_contains_merge_statements() (+13 more)

### Community 28 - "Community 28"
Cohesion: 0.14
Nodes (21): extract_swift(), Extract classes, structs, protocols, functions, imports, and calls from a .swift, _labels(), test_swift_conformance_edge(), test_swift_enum_cases_have_case_of_edge(), test_swift_extension_conformance_edge(), test_swift_extension_does_not_duplicate_type_node(), test_swift_extension_methods_attach_to_type() (+13 more)

### Community 29 - "Community 29"
Cohesion: 0.13
Nodes (20): CloseError, ConnectTimeout, NetworkError, PoolTimeout, ProxyError, httpx-like exception hierarchy. All exceptions inherit from HTTPError at the top, Timed out while connecting to the host., Timed out while receiving data from the host. (+12 more)

### Community 30 - "Community 30"
Cohesion: 0.12
Nodes (19): _call_claude(), _call_ollama(), _call_openai_compat(), detect_backend(), estimate_cost(), _get_tokenizer(), _ollama_host(), _parse_llm_json() (+11 more)

### Community 31 - "Community 31"
Cohesion: 0.13
Nodes (10): Changelog, Get summary statistics for all sessions.                  Args:             d, Initialize changelog with output directory., Delete a session by ID.                  Args:             session_id: Sessio, Clear all sessions (use with caution)., Load changelog from file, or create empty structure., Save changelog to file., Add a new work session to the changelog.                  Args:             t (+2 more)

### Community 32 - "Community 32"
Cohesion: 0.13
Nodes (18): _cypher_escape(), _html_script(), _html_styles(), _hyperedge_script(), prune_dangling_edges(), push_to_neo4j(), Export graph as an Obsidian Canvas file - communities as groups, nodes as cards., Push graph directly to a running Neo4j instance via the Python driver.      Re (+10 more)

### Community 33 - "Community 33"
Cohesion: 0.18
Nodes (17): classify_file(), Video and audio file extensions should classify as VIDEO., A .md file with enough paper signals should classify as PAPER., A plain .md file without paper signals should stay DOCUMENT., The real attention paper file should be classified as PAPER., test_classify_attention_paper(), test_classify_image(), test_classify_markdown() (+9 more)

### Community 34 - "Community 34"
Cohesion: 0.14
Nodes (18): extract_php(), Extract classes, functions, methods, namespace uses, and calls from a .php file., _relations(), test_csharp_finds_usings(), test_php_config_helper_target_matches_first_segment(), test_php_container_bind_links_contract_to_implementation(), test_php_event_listener_links_event_to_listener(), test_php_finds_class() (+10 more)

### Community 35 - "Community 35"
Cohesion: 0.11
Nodes (18): extract_corpus_parallel(), _merge_into(), Extract a corpus in chunks, merging results.      Chunking strategy:, Extract a corpus in chunks, merging results.      Chunking strategy:, Append a chunk result into the running merged accumulator., Append a chunk result into the running merged accumulator., With max_concurrency > 1, total wall time should be ~max(chunk times),     not, max_concurrency=1 should run sequentially (no thread pool). (+10 more)

### Community 36 - "Community 36"
Cohesion: 0.11
Nodes (18): _agents_install(), _check_any_skills_installed(), _devin_install(), _devin_skill_dst(), _devin_uninstall(), _install_codex_hook(), _install_opencode_plugin(), _install_single() (+10 more)

### Community 37 - "Community 37"
Cohesion: 0.15
Nodes (16): extract_dart(), _extract_generic(), extract_lua(), extract_powershell(), _extract_python_rationale(), extract_verilog(), extract_zig(), _file_stem() (+8 more)

### Community 38 - "Community 38"
Cohesion: 0.12
Nodes (18): _check_tree_sitter_version(), extract(), _extract_parallel(), _extract_sequential(), _get_extractor(), Two-pass import resolution: turn file-level imports into class-level edges., Two-pass Java import resolution.      Pass 1: build a global index {ClassName:, Raise a clear error if tree-sitter is too old for the new Language API. (+10 more)

### Community 39 - "Community 39"
Cohesion: 0.14
Nodes (6): CacheManager, createProcessor(), DataProcessor, Loggable, Processor, HttpClient

### Community 40 - "Community 40"
Cohesion: 0.12
Nodes (17): build_url_with_params(), flatten_queryparams(), is_known_encoding(), normalize_header_key(), obfuscate_sensitive_headers(), parse_content_type(), primitive_value_to_str(), Utility functions shared across the library. Small helpers that don't belong in (+9 more)

### Community 41 - "Community 41"
Cohesion: 0.12
Nodes (17): extract_js(), Extract classes, functions, arrow functions, and imports from a .js/.ts/.tsx fil, Dynamic import() calls inside functions should produce imports_from edges., Dynamic imports should have EXTRACTED confidence (they are deterministic string, Dynamic import edge source should be the enclosing function, not the file., Functions without dynamic imports should not get spurious imports_from edges., Dynamic template literals (with ${}) must not produce an imports_from edge., Static template literals (no ${}) should resolve the same as a plain string. (+9 more)

### Community 42 - "Community 42"
Cohesion: 0.17
Nodes (4): Config, createClient(), HttpClient, HttpClientFactory

### Community 43 - "Community 43"
Cohesion: 0.18
Nodes (12): attach_hyperedges(), Store hyperedges in the graph's metadata dict., _make_report(), Tests for hyperedge support in graphx., test_attach_hyperedges_adds_new(), test_attach_hyperedges_deduplicates(), test_attach_hyperedges_multiple_different_ids(), test_attach_hyperedges_skips_entry_without_id() (+4 more)

### Community 44 - "Community 44"
Cohesion: 0.17
Nodes (15): handle_enrich(), Re-enrich a document to pick up new cross-references., enrich_document(), extract_keywords(), find_cross_references(), normalize_text(), process_and_save(), Processor module - transforms validated documents into enriched records ready fo (+7 more)

### Community 45 - "Community 45"
Cohesion: 0.21
Nodes (14): Export graph as an Obsidian vault - one .md file per node with [[wikilinks]],, to_obsidian(), End-to-end pipeline test: detect → extract → build → cluster → analyze → report, Second run on unchanged corpus should produce identical node/edge counts., Run the full pipeline on the fixtures directory. Returns a dict of outputs., run_pipeline(), test_pipeline_all_nodes_have_community(), test_pipeline_detection_finds_code_and_docs() (+6 more)

### Community 46 - "Community 46"
Cohesion: 0.25
Nodes (14): delete_record(), _ensure_storage(), load_index(), load_record(), Storage module - persists documents to disk and maintains the search index. All, Load the full document index from disk., Persist the index to disk., Write a parsed document to storage. Returns the assigned record ID. (+6 more)

### Community 47 - "Community 47"
Cohesion: 0.15
Nodes (14): extract_elixir(), Extract modules, functions, imports, and calls from a .ex/.exs file., _edges_with_relation(), test_elixir_call_edges_have_call_context(), test_elixir_finds_calls(), test_elixir_finds_functions(), test_elixir_finds_imports(), test_elixir_finds_module() (+6 more)

### Community 48 - "Community 48"
Cohesion: 0.2
Nodes (12): load_extraction(), Legacy 'source' key on nodes is renamed to 'source_file' before graph build., Legacy 'from'/'to' keys on edges are accepted alongside 'source'/'target'., Windows backslash paths and POSIX paths for the same file must produce one node., test_ambiguous_edge_preserved(), test_build_from_json_edge_count(), test_build_from_json_node_count(), test_edges_have_confidence() (+4 more)

### Community 49 - "Community 49"
Cohesion: 0.21
Nodes (8): add(), Color, main(), multiply(), NewServer(), process(), validate(), Server

### Community 50 - "Community 50"
Cohesion: 0.2
Nodes (13): batch_parse(), parse_and_save(), parse_file(), parse_json(), parse_markdown(), parse_plaintext(), Parser module - reads raw input documents and converts them into a structured fo, Read a file from disk and return a structured document. (+5 more)

### Community 51 - "Community 51"
Cohesion: 0.14
Nodes (13): handle_delete(), handle_get(), handle_list(), handle_search(), handle_upload(), API module - exposes the document pipeline over HTTP. Thin layer over parser, va, Accept a list of file paths, run the full pipeline on each,     and return a sum, Fetch a document by ID and return it. (+5 more)

### Community 52 - "Community 52"
Cohesion: 0.23
Nodes (12): cluster(), cohesion_score(), _partition(), Community detection on NetworkX graphs. Uses Leiden (graspologic) if available,, Context manager to suppress stdout/stderr during library calls.      graspolog, Run a second Leiden pass on a community subgraph to split it further., Ratio of actual intra-community edges to maximum possible., Run community detection. Returns {node_id: community_id}.      Tries Leiden (g (+4 more)

### Community 53 - "Community 53"
Cohesion: 0.15
Nodes (13): _extract_with_adaptive_retry(), Extract a chunk; if the response is truncated (`finish_reason="length"`),     s, Extract a chunk; if the response is truncated (`finish_reason="length"`),     s, No retry when finish_reason='stop' — single call, result passes through., finish_reason='length' triggers split-in-half. Both halves succeed     on the s, When even the half-chunk truncates, split again. With 8 files and a     truncat, If everything truncates, retries stop at max_depth — partial result     kept wi, A single file that truncates can't be split further — surface a     warning and (+5 more)

### Community 54 - "Community 54"
Cohesion: 0.17
Nodes (13): gemini_install(), gemini_uninstall(), _install_gemini_hook(), Copy skill file to ~/.gemini/skills/graphx/, write GEMINI.md section, and instal, Remove the graphx section from GEMINI.md, uninstall hook, and remove skill file., _uninstall_gemini_hook(), test_gemini_install_idempotent(), test_gemini_install_merges_existing_gemini_md() (+5 more)

### Community 55 - "Community 55"
Cohesion: 0.23
Nodes (10): make_graph(), Clustering should not emit ANSI escape codes or other output.      graspologic, Same as above but for stderr — ANSI codes can go to either stream., test_cluster_covers_all_nodes(), test_cluster_does_not_write_to_stderr(), test_cluster_does_not_write_to_stdout(), test_cluster_returns_dict(), test_cohesion_score_complete_graph() (+2 more)

### Community 56 - "Community 56"
Cohesion: 0.23
Nodes (12): check_format(), check_required_fields(), normalize_fields(), Validator module - checks that parsed documents meet schema requirements before, Run all validation checks on a parsed document. Raises ValidationError on failur, Raise if any required field is missing., Raise if the format is not in the allowed list., Clean up text fields using the processor. (+4 more)

### Community 57 - "Community 57"
Cohesion: 0.18
Nodes (10): Limits, The main Client and AsyncClient classes. BaseClient holds all shared logic. Clie, Timeout, DecodingError, InvalidURL, An error occurred while issuing a request., Decoding of the response failed., URL is improperly formed or cannot be parsed. (+2 more)

### Community 58 - "Community 58"
Cohesion: 0.18
Nodes (5): Response, AsyncBaseTransport, AsyncHTTPTransport, Async transport interface., The async variant of HTTPTransport.

### Community 59 - "Community 59"
Cohesion: 0.17
Nodes (12): extract_csharp(), Extract classes, interfaces, methods, namespaces, and usings from a .cs file., _references(), test_csharp_call_edges_have_call_context(), test_csharp_field_type_references_have_field_context(), test_csharp_finds_class(), test_csharp_finds_interface(), test_csharp_finds_methods() (+4 more)

### Community 60 - "Community 60"
Cohesion: 0.17
Nodes (12): _cursor_install(), _cursor_uninstall(), Write .cursor/rules/graphx.mdc with alwaysApply: true., Remove .cursor/rules/graphx.mdc., cursor install writes .cursor/rules/graphx.mdc., cursor install does not overwrite an existing rule file., cursor uninstall removes the rule file., cursor uninstall does nothing if rule was never written. (+4 more)

### Community 61 - "Community 61"
Cohesion: 0.21
Nodes (8): Base, area(), Circle, describe(), Geometry, Point, Shape, LinearAlgebra

### Community 62 - "Community 62"
Cohesion: 0.18
Nodes (11): extract_kotlin(), Extract classes, objects, functions, and imports from a .kt/.kts file., _calls(), Regression test for the call-walker `simple_identifier` /     `identifier` rena, test_kotlin_emits_in_file_calls(), test_kotlin_finds_class(), test_kotlin_finds_data_class(), test_kotlin_finds_function() (+3 more)

### Community 63 - "Community 63"
Cohesion: 0.2
Nodes (10): capture_commit(), check_hook_status(), detect_commit_source(), install_commit_hook(), Detect if commit was made by AI or user., Install the post-commit hook., Remove the post-commit hook., Check if hook is installed. (+2 more)

### Community 64 - "Community 64"
Cohesion: 0.22
Nodes (10): build_graph(), cluster(), cohesion_score(), Leiden community detection on NetworkX graphs. Splits oversized communities. Ret, Run Leiden community detection. Returns {community_id: [node_ids]}.      Commu, Build a NetworkX graph from graphx node/edge dicts.      Preserves original ed, Run a second Leiden pass on a community subgraph to split it further., Ratio of actual intra-community edges to maximum possible. (+2 more)

### Community 65 - "Community 65"
Cohesion: 0.22
Nodes (10): convert_office_file(), count_words(), docx_to_markdown(), extract_pdf_text(), Extract plain text from a PDF file using pypdf., Convert a .docx file to markdown text using python-docx., Convert an .xlsx file to markdown text using openpyxl., Convert a .docx or .xlsx to a markdown sidecar in out_dir.      Returns the pa (+2 more)

### Community 67 - "Community 67"
Cohesion: 0.22
Nodes (7): Exception, CookieConflict, HTTPError, HTTPStatusError, A 4xx or 5xx response was received., Base class for all httpx exceptions., Attempted to look up a cookie by name but multiple cookies exist.

### Community 68 - "Community 68"
Cohesion: 0.22
Nodes (9): extract_java(), Extract classes, interfaces, methods, constructors, and imports from a .java fil, test_java_finds_class(), test_java_finds_imports(), test_java_finds_interface(), test_java_finds_methods(), test_java_import_edges_have_import_context(), test_java_no_dangling_edges() (+1 more)

### Community 69 - "Community 69"
Cohesion: 0.22
Nodes (9): extract_c(), Extract functions and includes from a .c/.h file., test_c_call_edges_have_call_context(), test_c_calls_are_extracted(), test_c_emits_calls(), test_c_finds_functions(), test_c_finds_includes(), test_c_import_edges_have_import_context() (+1 more)

### Community 70 - "Community 70"
Cohesion: 0.28
Nodes (8): extract_files_direct(), Extract semantic nodes/edges from a list of files using the given backend., Extract semantic nodes/edges from a list of files using the given backend., Return file contents formatted for the extraction prompt., _read_files(), test_ollama_backend_calls_native_chat_api(), test_ollama_host_accepts_openai_compat_suffix(), test_ollama_host_maps_bind_all_address_to_loopback()

### Community 71 - "Community 71"
Cohesion: 0.39
Nodes (5): Analyzer, compute_score(), normalize(), Fixture: functions and methods that call each other - for call-graph extraction, run_analysis()

### Community 72 - "Community 72"
Cohesion: 0.29
Nodes (8): _find_vcs_root(), _load_graphxignore(), _load_graphxinclude(), _parse_gitignore_line(), Parse one raw line from a .graphxignore file per gitignore spec.      - Strip, Walk upward from start; return the first directory containing a VCS marker., Read .graphxignore files and return (anchor_dir, pattern) pairs.      Patterns, Read .graphxinclude allowlist patterns from root and ancestors.      Include p

### Community 73 - "Community 73"
Cohesion: 0.39
Nodes (7): build_tree(), _common_root(), emit_html(), _make_truncation_leaf(), tree_html — emit a D3 v7 collapsible-tree HTML view of a graph.  A self-contai, Build a ``{name, total_count, children}`` hierarchy.      Each leaf is either, write_tree_html()

### Community 74 - "Community 74"
Cohesion: 0.25
Nodes (8): _strip_diacritics(), to_json(), Edges lacking confidence_score get sensible defaults in to_json., test_to_json_defaults_missing_confidence_score(), Write graph.json then reload it - hyperedges must survive., test_hyperedges_roundtrip_via_json_file(), test_to_json_hyperedges_empty_when_none(), test_to_json_includes_hyperedges()

### Community 75 - "Community 75"
Cohesion: 0.25
Nodes (8): extract_scala(), Extract classes, objects, functions, and imports from a .scala file., test_scala_call_edges_have_call_context(), test_scala_finds_class(), test_scala_finds_methods(), test_scala_finds_object(), test_scala_import_edges_have_import_context(), test_scala_no_error()

### Community 76 - "Community 76"
Cohesion: 0.29
Nodes (7): extract_cpp(), Extract functions, classes, and includes from a .cpp/.cc/.cxx/.hpp file., test_cpp_finds_class(), test_cpp_finds_includes(), test_cpp_finds_methods(), test_cpp_import_edges_have_import_context(), test_cpp_no_error()

### Community 77 - "Community 77"
Cohesion: 0.43
Nodes (6): EventServiceProvider, NotifyAdmins, OrderPlaced, SendWelcomeEmail, ShipOrder, UserRegistered

### Community 78 - "Community 78"
Cohesion: 0.33
Nodes (6): extract_ruby(), Extract classes, methods, singleton methods, and calls from a .rb file., test_ruby_finds_class(), test_ruby_finds_function(), test_ruby_finds_methods(), test_ruby_no_error()

### Community 80 - "Community 80"
Cohesion: 0.33
Nodes (5): Animal, -initWithName, -speak, Dog, -fetch

### Community 81 - "Community 81"
Cohesion: 0.67
Nodes (4): AppServiceProvider, CashierGateway, PaymentGateway, StripeGateway

### Community 82 - "Community 82"
Cohesion: 0.6
Nodes (4): Tests for graphx query CLI context filtering., test_query_cli_explicit_context_filter(), test_query_cli_heuristic_context_filter(), _write_graph()

### Community 84 - "Community 84"
Cohesion: 0.4
Nodes (4): NetworkError, connectionFailed, timeout, unauthorized

### Community 85 - "Community 85"
Cohesion: 0.5
Nodes (3): MyApp.Accounts.User, create(), validate()

### Community 89 - "Community 89"
Cohesion: 0.33
Nodes (4): Methods on the same receiver type must share one canonical type node., Type node id should be scoped to directory, not file stem., test_go_receiver_methods_share_type_node(), test_go_receiver_uses_pkg_scope()

### Community 92 - "Community 92"
Cohesion: 0.67
Nodes (3): _estimate_file_tokens(), Estimate the prompt-token cost of a single file under `_read_files` rules., Estimate the prompt-token cost of a single file under `_read_files` rules.

## Knowledge Gaps
- **526 isolated node(s):** `Detect if a commit was authored by an AI coding assistant.`, `Extract recent git commits with file-change detail for the activity timeline.`, `Get files that are staged but not committed.`, `Generate activity.json and write it to the graphx output directory.      Retur`, `Graph analysis: god nodes (most connected), surprising connections (cross-commun` (+521 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphx query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 6` to `Community 32`, `Community 2`, `Community 3`, `Community 36`, `Community 73`, `Community 74`, `Community 10`, `Community 12`, `Community 15`, `Community 54`, `Community 25`, `Community 27`, `Community 60`, `Community 31`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
- **Why does `_run_ollama_build()` connect `Community 6` to `Community 32`, `Community 1`, `Community 35`, `Community 3`, `Community 38`, `Community 74`, `Community 10`, `Community 14`, `Community 15`, `Community 19`, `Community 26`, `Community 27`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Why does `serve()` connect `Community 2` to `Community 49`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Are the 102 inferred relationships involving `str` (e.g. with `get_recent_activity()` and `_normalize_path()`) actually correct?**
  _`str` has 102 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `main()` (e.g. with `_query_graph_text()` and `_score_nodes()`) actually correct?**
  _`main()` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `_make_id()` (e.g. with `test_make_id_strips_dots_and_underscores()` and `test_make_id_consistent()`) actually correct?**
  _`_make_id()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `detect()` (e.g. with `.set()` and `_rebuild_code()`) actually correct?**
  _`detect()` has 20 INFERRED edges - model-reasoned connections that need verification._