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
  langchain/<nn>-<topic-slug>/    # Agent, tools, middleware examples
  langgraph/<nn>-<topic-slug>/    # Graph, state, persistence examples
  deepagents/<nn>-<topic-slug>/   # Planning, sandbox, subagent examples
tests/                            # Deterministic tests without model/network access
skills/agent-learning/           # This project-local workflow
```

Do not import one framework directory from another. Put framework-neutral logic in `shared`; use a framework directory only as an adapter for its APIs. Read [references/project-architecture.md](references/project-architecture.md) before moving code or introducing a new framework.

## Add Or Revise A Chapter

1. Read the source chapter, then inspect `docs/architecture.md` and the nearest existing chapter implementation.
2. Classify the chapter: LangChain for configurable Agent harnesses and tools; LangGraph for explicit stateful control flow; DeepAgents for planning, filesystem work, and subagents. Do not choose a higher-level framework unless its specific capability is exercised.
3. Decide whether the chapter needs code before creating implementation files. Use the delivery rules below.
4. Add `docs/chapters/<framework>/<nn>-<slug>.md`. Include source links, goals, essential concepts, runnable commands when code exists, failure modes, and exercises. Use [references/chapter-template.md](references/chapter-template.md).
5. For a code chapter, add a minimal runnable example and an expanded example under the matching `<nn>-<topic-slug>` directory. Read secrets from environment variables; do not write a real key or irreversible side effect.
6. Before adding a helper to a chapter, inspect `src/agent_learn/shared/`. Put a component there when it has a clear cross-chapter contract; keep one-off lesson-specific logic in the chapter. Write tests for shared deterministic components.
7. Add a dependency only when exercised. Keep model-provider integrations, framework-specific packages, and production-only packages in named optional extras.
8. Run the relevant tests, formatter/linter if available, and a syntax/import check. For chapters that require a real-model path, verify the live example imports cleanly and document the run command; state clearly if a live model run was skipped because credentials are absent.

## Choose The Delivery

Deliver Markdown only when the source chapter is conceptual, architectural, comparative, operational, or retrospective; when it has no behavior that a reader can meaningfully run; or when a code example would only repeat an existing chapter without teaching a new boundary. For a Markdown-only chapter, do not create an empty chapter package, placeholder test, dependency, or artificial code sample.

Deliver Markdown and code when the chapter introduces an executable API, tool contract, state transition, workflow, persistence behavior, streaming behavior, integration boundary, or other behavior that is clearer through direct observation. Keep code focused on the new lesson and add tests only for deterministic logic.

Do not use code as a completion requirement. The Markdown note is the required deliverable for every chapter; code is an additional deliverable only when it improves learning.

## Require Real Model Runnable Path

Deterministic offline tests remain required for pure logic, parsing, validation, and contracts that do not need provider behavior. They do not replace a live-model path when the chapter's core lesson depends on model or Agent runtime behavior.

When the source chapter teaches any of the following, deliver at least one runnable example that calls a real model through environment-configured credentials:

- model invocation, provider options, or structured output from an LLM
- Agent loop behavior, including tool selection, multi-turn replies, or `return_direct`
- live streaming, including `stream_events`, token deltas, or streamed tool-call lifecycle
- middleware that only makes sense with a model, such as summarization, dynamic prompt shaping at runtime, or output guardrails observed on wire events
- checkpointer-backed multi-turn memory where the lesson is continuity across invocations, not just local state shape

For those chapters:

1. Reuse the existing model factory and `.env` pattern; read model name, API key, timeout, and provider settings from environment variables. Never commit real keys.
2. Keep deterministic helpers and `pytest` coverage for everything that can be verified without a model or network.
3. In the chapter Markdown, document both paths explicitly: offline deterministic commands and the live-model command block, including required env vars and optional extras such as `openai`.
4. Name the live example clearly in the chapter note and link to its file path.
5. If a live model run cannot be executed in the current environment, state that fact and the missing credential or dependency. Do not fabricate model output, token streams, or usage metadata.

Offline simulation is still appropriate as a supporting example when it teaches projection shapes, schema, or message contracts, but it must not be the only runnable path for a chapter whose main learning goal is observing real model or Agent behavior.

## Name Chapter Directories

For every code chapter, name its implementation directory `<two-digit-number>-<topic-slug>`. Make `topic-slug` a short, lowercase, hyphen-separated English description of the chapter's actual learning topic, and use the same topic slug in the chapter Markdown filename. For example: `langchain/03-quickstart/`, `langgraph/08-persistence/`, and `deepagents/12-subagents/`.

Do not use generic directory names such as `chapter_03`, `example`, `demo`, or `practice`. When a source chapter covers several ideas, name the directory after its primary new capability; place supporting examples inside that directory. Do not create a code directory for a Markdown-only chapter.

## Share Cross-Chapter Components

Use `src/agent_learn/shared/` as the only home for reusable learning components. Before creating or copying a helper in a chapter directory, check whether an equivalent shared component already exists.

Move a component to `shared/` when two or more chapters use it, or when it is intentionally a project-wide contract such as configuration loading, domain data models, deterministic parsing or validation, test fixtures, or provider-neutral interfaces. Give shared modules topic-based names and keep their public behavior small and documented.

Do not put framework-specific Agent construction, LangChain/LangGraph/DeepAgents objects, a chapter's prompt, or a one-off teaching shortcut in `shared/`. `shared/` must not import from `frameworks/`; framework chapters may import from `shared/`. Do not duplicate a shared component back into a chapter.

## Implementation Rules

- Give tools precise names, typed parameters, and docstrings that describe when to call them.
- Let deterministic code perform exact counts, searches, parsing, and validation. In prompts, require the model to use the corresponding tool rather than guess.
- Treat `thread_id`, checkpoint scope, permissions, URL fetching, and persistent storage as explicit boundaries, not incidental implementation details.
- Keep `InMemorySaver` and in-memory stores limited to local learning examples. Document the production replacement and isolation requirement.
- Keep documentation in Chinese while preserving API names and framework terms in English.

## Validate

Run `pytest` for deterministic behavior. Run `ruff check .` when the development extra is installed. Validate this Skill with the Skill Creator validator after changing its frontmatter or structure.
