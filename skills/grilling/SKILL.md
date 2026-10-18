---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

Format a round like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Word each question so "yes" accepts your recommended answer.

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.

## Mandatory Escalation vs. Autonomous Defaults
During grilling and spec authoring, separate assumptions into two strict buckets:
1. **Autonomous Engineering Defaults (Do not ask user, document briefly in Spec):** Internal helper structure, standard memory/resize cleanup, empty-state guards, and local vendor pinning.
2. **Mandatory User Confirmation (Must ask during Grilling or explicitly highlight in Spec before approval):**
   - Network ports, CLI flags, or entrypoint changes (e.g., changing default ports or launcher commands).
   - Information architecture changes (e.g., demoting a top-level page into a drawer/modal, or adding/removing views).
   - Localization, currency defaults, hardcoded exchange rates, or pricing rules.
   - User-visible editorial copy, disclaimers, or warning banners not requested by the user.

**Hard Gate:** Never invoke `writing-plans` or `plan-critic` in the same turn that the Spec is written. Write the Spec file (`docs/superpowers/specs/...`), present a summary of any defaults chosen, and STOP for user approval.

