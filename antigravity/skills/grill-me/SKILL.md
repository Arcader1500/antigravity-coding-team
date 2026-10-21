---
name: grill-me
description: Interview the user about every aspect of their task until reaching a shared understanding. Resolves decisions one by one using the native ask_question interactive prompt with multiple-choice options.
---

Interview the user about every aspect of their task until you reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one by one.

## Core Rules

1. **Ask One Question at a Time**:
   Walk down the design tree sequentially. Do not overwhelm the user with multiple simultaneous questions or monolithic text blocks.

2. **Always Use the Native `ask_question` Tool**:
   **NEVER** print questions as raw markdown text (such as `❓ Q1: ...`) into the chat stream.
   You **MUST** invoke the native `ask_question` tool. In the Antigravity CLI and IDE, calling `ask_question` renders an interactive terminal prompt where the user selects from options with arrow keys or enters custom text.

3. **Format Options for Direct Selection**:
   - Provide 2 to 4 structured, direct-response choices in the `options` array.
   - Always put the recommended option first and prefix it with `(Recommended)`.
   - Format options from the user's perspective (e.g., `"(Recommended) Pure TypeScript / Node.js stack..."`).
   - Set `is_multi_select: false` unless the question genuinely allows multiple simultaneous choices.

4. **Explore First, Never Grill on Facts**:
   Finding facts is your job, never the user's.
   If a question can be answered by exploring the codebase or running tools, do that first (e.g., dispatch `researcher` or inspect files with `view_file`). Never ask the user for information you can discover yourself.

5. **Mandatory Confirmation vs. Autonomous Defaults**:
   Separate decisions into two strict buckets:
   - **Autonomous Engineering Defaults (Do not ask user; document briefly in Spec):**
     Internal helper structure, standard memory/resize cleanup, empty-state guards, error boundaries, and local vendor pinning.
   - **Mandatory User Confirmation (MUST ask via `ask_question` before drafting Spec):**
     - Network ports, CLI flags, entrypoint/launcher commands.
     - Information architecture changes (e.g., adding/removing views, demoting pages to drawers/modals).
     - Localization, currency defaults, exchange rates, and pricing rules.
     - User-visible editorial copy, disclaimers, or warning banners not requested by the user.

6. **Hard Gate: Checkpoint 1 Before Planning**:
   The grilling session is complete when every branch of the design tree is resolved and nothing is left silently assumed.
   Write the Design Spec to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`.
   Present the spec path and defaults summary to the user, and **STOP AND END TURN** for user approval before invoking `writing-plans` or `plan-critic`.
