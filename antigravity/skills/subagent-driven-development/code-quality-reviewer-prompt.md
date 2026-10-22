# Code Quality Reviewer Prompt Template

Use this template for final independent code-reviewer review or focused re-review.

**Purpose:** Verify spec compliance and code quality against approved requirements.

**Dispatch after all implementation waves and outstanding writers finish.**

```
invoke_subagent with agent: code-reviewer:
  Use the bundled code-review-and-quality skill.
  Start with the code-review-graph MCP — the review scope is not enumerated, so the graph is how you find what the change affects: `detect_changes_tool` for changed files, `get_review_context_tool` for risk-scored snippets, `get_impact_radius_tool` for blast radius, `get_affected_flows_tool` for impacted flows, `query_graph_tool` (`tests_for`) for caller/test coverage. Name the graph tools you called in your report.

  DESCRIPTION: [task summary, from implementer's report]
  PLAN_OR_REQUIREMENTS: [approved spec and full plan; relevant tasks for re-review]
  BASE_SHA: [commit before implementation]
  HEAD_SHA: [current commit]
```

**In addition to standard code quality concerns, the reviewer should check:**
- Does each file have one clear responsibility with a well-defined interface?
- Are units decomposed so they can be understood and tested independently?
- Is the implementation following the file structure from the plan?
- Did this implementation create new files that are already large, or significantly grow existing files? (Don't flag pre-existing file sizes — focus on what this change contributed.)

**Code reviewer returns:** Blocker/Important/Nit findings with file:line and a concrete fix; verdict Approve / Approve with comments / Request changes.
