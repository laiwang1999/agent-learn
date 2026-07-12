# Agent Learning Architecture Reference

Use the project as a collection of vertical learning slices, not as a single application.

| Location | Owns | May depend on |
| --- | --- | --- |
| `docs/chapters/` | source-backed learning notes and exercises | source links and local code paths |
| `src/agent_learn/shared/` | pure domain logic, schemas, fixtures | standard library and explicit domain libraries |
| `frameworks/langchain/` | agent harnesses, tools, middleware | `shared`, LangChain, LangGraph runtime APIs |
| `frameworks/langgraph/` | graphs, state, persistence, interrupts | `shared`, LangGraph |
| `frameworks/deepagents/` | planning, subagents, sandbox adapters | `shared`, DeepAgents and its declared runtime APIs |
| `tests/` | deterministic behavior | `shared` and isolated framework code |

Rules:

- Keep each code chapter in `<two-digit-number>-<topic-slug>` so code order matches its study note and its folder names the learning topic; for example, `03-quickstart` or `08-persistence`.
- Use the same topic slug in `docs/chapters/<framework>/<two-digit-number>-<topic-slug>.md`. Do not create an implementation folder for a Markdown-only chapter.
- Use `src/agent_learn/shared/` for components with a cross-chapter contract. Check it before adding a helper to a chapter; do not duplicate shared configuration, domain models, deterministic utilities, test fixtures, or provider-neutral interfaces.
- Keep `shared/` framework-neutral and one-way: chapter code may import it, but it must never import `frameworks/` or create Agent objects.
- Do not make `langchain`, `langgraph`, or `deepagents` import one another. Extract common behavior first.
- Put external providers, credentials, model names, timeouts, and feature flags in configuration read from environment variables.
- Keep real network, persistent storage, and side effects behind tools or adapters; test their pure collaborators without invoking them.
- Add shared abstractions only after at least two chapters have a concrete need. Early abstraction obscures the lesson.
