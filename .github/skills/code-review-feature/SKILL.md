---
name: code-review-feature
description: Independently review a feature for security risks and code quality issues using two read-only Copilot subagents, then consolidate their findings. Use when reviewing a feature, change, or pull request in Spendly.
argument-hint: "[feature name, file path, or pull request context]"
user-invocable: true


---

# Feature review

Review the feature or change identified by the user's request. Use the user's scope and supplied context; if the target cannot be determined, ask for clarification before reviewing. For a request to review current changes, use read-only inspection (such as the available diff context or `git diff`) to establish the changed files and scope. Keep the review read-only: do not edit files, implement fixes, run tests, or commit changes.

## Delegate both reviews

1. Identify the same feature scope and relevant files for both reviewers. Use the current change context or the user's stated scope; include directly related implementation and tests where relevant.
2. In the same orchestration turn, delegate two independent subagent tasks using the custom agents `security-reviewer` and `code-quality-reviewer`. Give both agents the same feature scope and review context, and ask each to review independently without seeing or relying on the other's findings.
3. Run the tasks in parallel when the available Copilot harness supports it. If parallel execution is unavailable, run them sequentially.
4. Wait for each delegated result before consolidating. Do not substitute a self-review for a reviewer that was not actually run. If delegation, execution, or a usable result is missing, mark that review incomplete and state why.

## Consolidate findings

Include only actionable findings supported by code evidence. Merge duplicate reports of the same underlying issue, retain the highest severity justified by evidence, and identify all reviewers who reported the merged finding. Keep separate findings for distinct issues, even when they are in the same file.

Use this format for every finding:

- **Severity** — Critical, High, Medium, or Low
- **Finding** — concise issue and impact
- **Location** — repository-relative file path and line number or range
- **Evidence** — specific code behavior supporting the finding
- **Recommended fix** — actionable remediation
- **Reported by** — `security-reviewer`, `code-quality-reviewer`, or both

Severity guidance: Critical means a readily exploitable issue with severe impact; High means a serious security or correctness issue; Medium means a meaningful but constrained issue; Low means a minor actionable issue. Do not inflate severity or report speculative concerns as confirmed findings.

## Final report

Return one report with:

1. **Review scope** — feature/change reviewed.
2. **Agent execution** — each agent's status (`completed` or `incomplete`) and evidence that it returned a result. Never claim an agent ran unless its task was actually delegated and completed.
3. **Findings** — the consolidated, deduplicated findings in the format above. If a completed agent found none, say so explicitly.
4. **Incomplete reviews / limits** — name any missing reviewer, unavailable scope, or other limitation; say “None” only when both reviews completed and no material limitation remains.

If both agents completed and found no actionable issues, state that clearly. Do not imply that tests or other checks were run.
