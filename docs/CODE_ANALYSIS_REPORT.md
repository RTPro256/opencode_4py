# Code Analysis Report

**Generated**: 2026-02-23T19:17:57.954272
**Root**: c:\path\to\opencode_4py

## Large Files (>500 lines or >20K chars)

| File | Lines | Chars | Functions | Classes | Long Functions |
|------|-------|-------|-----------|---------|----------------|
| `src\opencode\src\opencode\cli\commands\rag.py` | 1117 | 41,585 | 18 | 0 | 11 |
| `src\opencode\src\opencode\tests\unit\test_scoring_engine.py` | 1043 | 34,255 | 61 | 13 | 0 |
| `src\opencode\src\opencode\tui\app.py` | 957 | 33,819 | 25 | 6 | 1 |
| `src\opencode\src\opencode\tests\unit\test_ollama_client.py` | 837 | 30,837 | 30 | 13 | 0 |
| `src\opencode\src\opencode\tests\unit\test_workflow_graph.py` | 943 | 30,297 | 47 | 5 | 0 |
| `src\opencode\src\opencode\tests\unit\test_orchestration.py` | 896 | 29,535 | 42 | 8 | 0 |
| `src\opencode\src\opencode\tests\unit\test_rag_safety.py` | 773 | 29,425 | 53 | 11 | 0 |
| `src\opencode\src\opencode\tests\unit\test_validation_pipeline.py` | 753 | 26,576 | 9 | 3 | 0 |
| `src\opencode\src\opencode\tests\unit\test_hardware_backends_cpu.py` | 744 | 26,132 | 56 | 9 | 0 |
| `src\opencode\src\opencode\tests\unit\test_workflow_engine.py` | 737 | 26,104 | 63 | 28 | 0 |
| `src\opencode\src\opencode\tests\unit\test_youtube_channel.py` | 663 | 25,235 | 25 | 4 | 1 |
| `src\opencode\src\opencode\tests\unit\test_lsp_tool.py` | 666 | 25,171 | 55 | 11 | 0 |
| `src\opencode\src\opencode\i18n\manager.py` | 733 | 25,059 | 18 | 2 | 1 |
| `src\opencode\src\opencode\tests\unit\test_session_manager.py` | 782 | 24,967 | 50 | 9 | 0 |
| `src\opencode\src\opencode\tests\unit\test_subagent_manager.py` | 725 | 24,900 | 16 | 9 | 0 |
| `src\opencode\src\opencode\tests\unit\test_router_engine.py` | 764 | 24,734 | 33 | 7 | 0 |
| `src\opencode\src\opencode\tests\unit\test_vram_monitor.py` | 691 | 24,218 | 27 | 4 | 0 |
| `src\opencode\src\opencode\tests\unit\test_skill_manager.py` | 735 | 23,965 | 29 | 6 | 0 |
| `src\opencode\src\opencode\tests\unit\test_subagent_validator.py` | 657 | 23,174 | 81 | 11 | 0 |
| `src\opencode\src\opencode\tests\unit\test_tui_app.py` | 680 | 23,069 | 47 | 9 | 0 |
| `src\opencode\src\opencode\tests\unit\test_anthropic_provider_extended.py` | 568 | 22,942 | 23 | 7 | 0 |
| `src\opencode\src\opencode\tests\unit\test_workflow_engine_extended.py` | 678 | 22,931 | 35 | 17 | 0 |
| `src\opencode\src\opencode\tool\file_tools.py` | 684 | 22,646 | 25 | 5 | 0 |
| `src\opencode\src\opencode\tests\unit\test_openai_provider_extended.py` | 586 | 22,566 | 28 | 8 | 0 |
| `src\opencode\src\opencode\tests\unit\test_rag_pipeline.py` | 653 | 22,425 | 37 | 12 | 0 |
| `src\opencode\src\opencode\tool\lsp.py` | 644 | 22,341 | 15 | 5 | 0 |
| `src\opencode\src\opencode\tests\unit\test_workflow_routes.py` | 593 | 21,876 | 39 | 4 | 0 |
| `src\opencode\src\opencode\tests\unit\test_llmchecker_cli_extended.py` | 596 | 21,587 | 34 | 10 | 0 |
| `src\opencode\src\opencode\server\routes\workflow.py` | 688 | 20,554 | 2 | 10 | 0 |
| `src\opencode\src\opencode\llmchecker\ollama\client.py` | 618 | 20,511 | 7 | 1 | 0 |
| `src\opencode\src\opencode\tests\unit\test_mcp_client_full.py` | 614 | 20,498 | 22 | 6 | 0 |
| `src\opencode\src\opencode\llmchecker\scoring\engine.py` | 623 | 20,146 | 12 | 1 | 2 |
| `src\opencode\src\opencode\tool\apply_patch.py` | 589 | 20,118 | 14 | 6 | 1 |
| `src\opencode\src\opencode\tests\unit\test_util_log.py` | 658 | 19,725 | 57 | 10 | 0 |
| `src\opencode\src\opencode\llmchecker\hardware\detector.py` | 581 | 19,651 | 17 | 1 | 4 |
| `src\opencode\src\opencode\tests\unit\test_skill_discovery.py` | 543 | 19,616 | 39 | 6 | 0 |
| `src\opencode\src\opencode\tests\unit\test_git_tool.py` | 591 | 19,610 | 4 | 2 | 0 |
| `src\opencode\src\opencode\tests\unit\test_citations.py` | 580 | 19,579 | 31 | 4 | 0 |
| `src\opencode\src\opencode\tests\unit\test_apply_patch.py` | 608 | 19,404 | 44 | 13 | 0 |
| `src\opencode\src\opencode\tests\unit\test_hybrid_search.py` | 631 | 19,378 | 32 | 3 | 0 |
| `src\opencode\src\opencode\workflow\engine.py` | 566 | 19,364 | 10 | 4 | 0 |
| `src\opencode\src\opencode\tests\unit\test_modes_base.py` | 545 | 19,299 | 51 | 13 | 0 |
| `src\opencode\src\opencode\util\index_generator.py` | 573 | 18,990 | 17 | 4 | 2 |
| `src\opencode\src\opencode\mcp\oauth.py` | 589 | 18,967 | 12 | 8 | 0 |
| `src\opencode\src\opencode\tests\unit\test_rag_regenerator.py` | 508 | 18,874 | 6 | 2 | 0 |
| `src\opencode\src\opencode\tests\unit\test_tool_base.py` | 584 | 18,625 | 58 | 8 | 0 |
| `src\opencode\src\opencode\tests\unit\test_tools_routes.py` | 506 | 18,352 | 35 | 10 | 0 |
| `src\opencode\src\opencode\tests\unit\test_mcp_types.py` | 590 | 17,939 | 44 | 9 | 0 |
| `src\opencode\src\opencode\tests\unit\test_source_manager.py` | 522 | 17,917 | 32 | 5 | 0 |
| `src\opencode\src\opencode\server\graphql\schema.py` | 582 | 17,639 | 20 | 17 | 0 |
| `src\opencode\src\opencode\tests\unit\test_rag_retriever.py` | 545 | 17,615 | 23 | 4 | 0 |
| `src\opencode\src\opencode\tests\unit\test_explore_tool.py` | 503 | 17,572 | 45 | 3 | 0 |
| `src\opencode\src\opencode\core\session.py` | 537 | 17,329 | 15 | 8 | 0 |
| `src\opencode\src\opencode\core\rag\local_vector_store.py` | 566 | 17,098 | 10 | 6 | 0 |
| `src\opencode\src\opencode\tests\unit\test_router_routes.py` | 516 | 17,009 | 32 | 16 | 0 |
| `src\opencode\src\opencode\tests\unit\test_local_vector_store.py` | 557 | 16,998 | 13 | 5 | 0 |
| `src\opencode\src\opencode\tui\widgets\completion.py` | 526 | 16,339 | 34 | 9 | 1 |
| `src\opencode\src\opencode\skills\manager.py` | 509 | 14,952 | 13 | 1 | 0 |
| `src\opencode\src\opencode\tests\integration\test_mcp_integration.py` | 505 | 14,753 | 31 | 12 | 0 |

## Long Functions (>50 lines)

| File | Function | Lines |
|------|----------|-------|
| `src\opencode\src\opencode\i18n\manager.py` | `_get_embedded_translations()` | 371 |
| `src\opencode\src\opencode\core\subagents\builtin.py` | `_register_builtin_agents()` | 199 |
| `src\opencode\src\opencode\web\app.py` | `create_app()` | 133 |
| `src\opencode\src\opencode\cli\commands\rag.py` | `merge_rags()` | 124 |
| `src\opencode\src\opencode\workflow\templates\ensemble.py` | `build()` | 117 |
| `src\opencode\src\opencode\cli\commands\rag.py` | `get_community_rag()` | 109 |
| `src\opencode\src\opencode\workflow\nodes\chart.py` | `_build_chart_config()` | 106 |
| `src\opencode\src\opencode\tests\utils\test_data.py` | `_initialize_default_data()` | 102 |
| `src\opencode\src\opencode\workflow\templates\voting.py` | `build()` | 99 |
| `src\opencode\src\opencode\cli\commands\llmchecker.py` | `recommend_models()` | 93 |
| `scripts\analyze_code.py` | `generate_report()` | 86 |
| `src\opencode\src\opencode\cli\commands\rag.py` | `list_remote_rags()` | 86 |
| `src\opencode\src\opencode\cli\commands\llmchecker.py` | `calibrate()` | 85 |
| `src\opencode\src\opencode\workflow\templates\sequential.py` | `build()` | 83 |
| `src\opencode\src\opencode\cli\commands\index.py` | `generate_index()` | 82 |
| `src\opencode\src\opencode\util\index_generator.py` | `format_index()` | 82 |
| `src\opencode\src\opencode\provider\vercel.py` | `models()` | 79 |
| `src\opencode\src\opencode\cli\commands\debug_cmd.py` | `query_troubleshooting_rag()` | 76 |
| `src\opencode\src\opencode\cli\commands\rag.py` | `create_rag()` | 75 |
| `src\opencode\src\opencode\cli\commands\rag.py` | `query_rag()` | 74 |
| ... | ... | (55 more) |

## Circular Dependencies

No circular dependencies detected.

## Summary

- **Total files**: 389
- **Total lines**: 121,436
- **Total characters**: 4,031,758
- **Total functions**: 5181
- **Total classes**: 1508
- **Large files**: 59
- **Long functions**: 75
- **Circular dependencies**: 0