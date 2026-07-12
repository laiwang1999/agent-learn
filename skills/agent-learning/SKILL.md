---
name: agent-learning
description: Build and extend the chapter-based Agent learning project with runnable Python examples, focused Chinese Markdown study notes, tests, and framework-aware architecture. Use when adding or revising LangChain, LangGraph, DeepAgents, agent-tooling, memory, workflow, or observability learning chapters in this repository.
---

# Agent Learning

## Overview

Create one verifiable learning slice per source chapter. Keep tutorials executable, keep deterministic logic testable without a model key, and preserve the project boundaries as more frameworks are added.

## Project Architecture

Use this layout:

```text
docs/chapters/<framework>/       # Chapter notes and learning exercises
src/agent_learn/shared/          # Framework-neutral domain code and contracts
src/agent_learn/frameworks/
  langchain/chapter_<nn>/         # Agent, tools, middleware examples
  langgraph/chapter_<nn>/         # Graph, state, persistence examples
  deepagents/chapter_<nn>/        # Planning, sandbox, subagent examples
tests/                            # Deterministic tests without model/network access
skills/agent-learning/           # This project-local workflow
```

Do not import one framework directory from another. Put framework-neutral logic in `shared`; use a framework directory only as an adapter for its APIs. Read [references/project-architecture.md](references/project-architecture.md) before moving code or introducing a new framework.

## Add Or Revise A Chapter

1. Read the source chapter, then inspect `docs/architecture.md` and the nearest existing chapter implementation.
2. Classify the chapter: LangChain for configurable Agent harnesses and tools; LangGraph for explicit stateful control flow; DeepAgents for planning, filesystem work, and subagents. Do not choose a higher-level framework unless its specific capability is exercised.
3. Add `docs/chapters/<framework>/<nn>-<slug>.md`. Include source links, goals, essential concepts, runnable commands, failure modes, and exercises. Use [references/chapter-template.md](references/chapter-template.md).
4. Add a minimal runnable example and an expanded example under the matching `chapter_<nn>` directory. Read secrets from environment variables; do not write a real key or irreversible side effect.
5. Move parsing, calculation, validation, and domain entities to `shared` when they can be used without the framework. Write tests for those deterministic components.
6. Add a dependency only when exercised. Keep model-provider integrations, framework-specific packages, and production-only packages in named optional extras.
7. Run the relevant tests, formatter/linter if available, and a syntax/import check. State clearly if a live model run was skipped because credentials are absent.

## Implementation Rules

- Give tools precise names, typed parameters, and docstrings that describe when to call them.
- Let deterministic code perform exact counts, searches, parsing, and validation. In prompts, require the model to use the corresponding tool rather than guess.
- Treat `thread_id`, checkpoint scope, permissions, URL fetching, and persistent storage as explicit boundaries, not incidental implementation details.
- Keep `InMemorySaver` and in-memory stores limited to local learning examples. Document the production replacement and isolation requirement.
- Keep documentation in Chinese while preserving API names and framework terms in English.

## Validate

Run `pytest` for deterministic behavior. Run `ruff check .` when the development extra is installed. Validate this Skill with the Skill Creator validator after changing its frontmatter or structure.
