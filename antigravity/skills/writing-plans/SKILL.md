---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** If working in an isolated worktree, it should have been created via the `superpowers:using-git-worktrees` skill at execution time.

**Save plans to:** `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`
- (User preferences for plan location override this default)

## Scope Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

## Core Authoring Rules

### 1. No Full-File Inlining ("Coding in Markdown" Ban)
Never write complete function bodies, full file replacements, or raw HTML/CSS files (>40 lines per block) inside implementation plans. Total code blocks across the plan must remain under 40% of total lines.
Instead of full implementations, every task must specify:
- **Exact Signatures & Types:** Function/class definitions, argument types, return types, and dataclass/Pydantic schemas.
- **Grounded External Calls (Anti-Hallucination):** Every call to an existing repository function, method, or class MUST cite its exact definition path and line number verified on disk (e.g., `source.scan_usage(brain_root, extractor_path)` — ref `agy_dash/source.py:75`). Never guess or invent helper names.
- **Core Algorithmic/Tricky Snippets Only:** Only inline implementation code when demonstrating non-obvious math, tricky library wiring (e.g., complex ECharts series stacking), or exact regex/SQL queries (<30 lines).
- **Template & UI Contracts:** For HTML/Jinja2/CSS tasks, specify the file path, parent template/block hierarchy, required context variables (with exact dict keys/types), HTMX target IDs/endpoints, and key DOM selectors—leave the markup authoring to `implementer`.

### 2. Mandatory Wave Execution Matrix
Every plan MUST include an `## Execution Waves` section immediately before `## Tasks` containing a Markdown table grouping all tasks into sequential waves (`Wave 1`, `Wave 2`, etc.):
- **Rule 1 (Disjoint Files):** Tasks in the same wave MUST have 100% disjoint file touch-sets (both created and modified).
- **Rule 2 (Dependency Order):** Foundational schemas/state go in Wave 1; domain/view builders and templates that consume them go in Wave 2; FastAPI routes/wiring in Wave 3; entrypoint launchers (`run.ps1`) and E2E verification in the final wave.
- **Rule 3 (Explicit Headers):** Every task header MUST include:
  - `**Wave:** N`
  - `**Depends on:** [Task IDs or None]`
  - `**Files Touched:** [exact paths]`
- **Rule 4 (No Git Hygiene Tasks & Repository Scaffolding):** Never create tasks for git branch creation or working-tree cleanup (`git restore`, `git reset`, `git checkout`); workspace state is managed by the orchestrator. When scaffolding a new repository in Task 1, ensure `.gitignore` includes `.code-review-graph/` and `.agy/` alongside build artifacts and dependencies, and ensure the `code-review-graph` post-commit hook is wired for automated background graph updates.

### 3. Strict 4-Step TDD Sequence (With Static Asset Exception)
- **For Python / Logic / Route / View Tasks:** Every task MUST explicitly order these 4 steps:
  1. **Write Failing Test:** Specify the concrete test cases and assertions to add to `tests/test_<module>.py`.
  2. **Verify Red:** Run `pytest tests/test_<module>.py -v` and confirm it fails for the expected reason (missing symbol / assertion failure) BEFORE writing implementation code.
  3. **Implement:** Write the minimal production code satisfying the contract.
  4. **Verify Green:** Run `pytest tests/test_<module>.py -v` and confirm all tests pass.
- **For Static Assets / Config / Scripts (`*.css`, `*.js`, `*.ps1`, `requirements.txt`, pure templates without backend routes yet):** Where unit tests do not apply, specify a concrete single-line **Verification Command** (e.g., syntax validation, file existence/import check, or FastAPI `TestClient` render check once wired).

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---

## Execution Waves

| Wave | Tasks | Description | Files Touched (Disjoint) |
|---|---|---|---|
| Wave 1 | Task 1, Task 2 | Schemas, models, foundation state | `path/to/schema.py`, `path/to/state.py` |
| Wave 2 | Task 3 | Domain logic, view builders, templates | `path/to/views.py`, `path/to/template.html` |
| Wave 3 | Task 4 | Routes, entrypoints, launchers, E2E | `path/to/app.py`, `run.ps1` |

---
```

## Task Structure

````markdown
### Task N: [Component Name]

**Wave:** 1
**Depends on:** [None or Task X, Task Y]
**Files Touched:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails (Red)**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation (Green)**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes (Green)**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## No Placeholders

Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code — the engineer may be reading tasks out of order)
- Steps that describe what to do without showing how (code blocks required for code steps)
- References to types, functions, or methods not defined in any task

## Remember
- Exact file paths always
- Interface contracts and tricky algorithms only — no full-file code dumps (code blocks < 40% of plan)
- Grounded external calls with verified `file:line` citations
- Exact commands with expected output
- DRY, YAGNI, TDD (Red before Green), frequent commits

## Self-Review

After writing the complete plan, look at the spec with fresh eyes and check the plan against it. This is a checklist you run yourself — not a subagent dispatch.

**1. Spec coverage:** Skim each section/requirement in the spec. Can you point to a task that implements it? List any gaps.

**2. Placeholder scan:** Search your plan for red flags — any of the patterns from the "No Placeholders" section above. Fix them.

**3. Type consistency:** Do the types, method signatures, and property names you used in later tasks match what you defined in earlier tasks? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.

If you find issues, fix them inline. No need to re-review — just fix and move on. If you find a spec requirement with no task, add the task.

## Execution Handoff

After saving the plan, offer execution choice:

**"Plan complete and saved to `docs/superpowers/plans/<filename>.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?"**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use superpowers:subagent-driven-development
- Fresh subagent per task + two-stage review

**If Inline Execution chosen:**
- **REQUIRED SUB-SKILL:** Use superpowers:executing-plans
- Batch execution with checkpoints for review
