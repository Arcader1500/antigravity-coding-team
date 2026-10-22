# Code Quality Reviewer Prompt Template

Use this template when dispatching a code quality reviewer subagent.

**Purpose:** Verify implementation is well-built (clean, tested, maintainable)

**Only dispatch after spec compliance review passes.**

```
Task tool (general-purpose):
  Use the code-review skill.
  Start with the code-review-graph MCP — the review scope is not enumerated, so the graph is how you find what the change affects: `detect_changes_tool` for changed files, `get_review_context_tool` for risk-scored snippets, `get_impact_radius_tool` for blast radius, `get_affected_flows_tool` for impacted flows, `query_graph_tool` (`tests_for`) for caller/test coverage. Name the graph tools you called in your report.

  DESCRIPTION: [task summary, from implementer's report]
  PLAN_OR_REQUIREMENTS: Task N from [plan-file]
  BASE_SHA: [commit before task]
  HEAD_SHA: [current commit]
```

**In addition to standard code quality concerns, the reviewer should check:**
- Does each file have one clear responsibility with a well-defined interface?
- Are units decomposed so they can be understood and tested independently?
- Is the implementation following the file structure from the plan?
- Did this implementation create new files that are already large, or significantly grow existing files? (Don't flag pre-existing file sizes — focus on what this change contributed.)

**Code reviewer returns:** Strengths, Issues (Critical/Important/Minor), Assessment
