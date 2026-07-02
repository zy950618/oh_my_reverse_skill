---
name: karpathy-guidelines
standard_type: auxiliary_policy
description: >-
  Auxiliary foundation guideline for engineering discipline. Use only as a supporting quality checklist when another Skill or coding task is already selected and the work involves implementation, review, refactoring, or verification. It is not a business-task entry point and must not independently handle Web/H5 reverse engineering, CAPTCHA, WAF, model training, API delivery, or site-specific workflows.
license: MIT
platforms: [cross-platform]
category: foundation
---

# Karpathy Guidelines

Behavioral guidelines to reduce common LLM coding mistakes, derived from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876) on LLM coding pitfalls.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## Role

This is a foundation guideline, not a business Skill. It should be loaded by another Skill or by the agent when coding/review/refactor work begins. It does not decide product routing, reverse-engineering scope, CAPTCHA handling, WAF diagnostics, model training, or delivery ownership.

## When To Use

- A selected Skill is about to change files, implement code, review code, or define verification.
- A task needs assumptions, scope, success criteria, and minimal-change discipline.
- A reviewer needs to check whether changes are surgical and test-backed.

## Do NOT Trigger When

- The user asks for Web/H5 reverse engineering, API delivery, CAPTCHA, WAF, fingerprint diagnostics, or Skill scoring as the main task.
- The user asks for a domain workflow that has a dedicated Skill.
- The request is a simple factual answer with no implementation or review work.

## Preconditions

Before applying this guideline, identify the primary task owner Skill or the concrete file/code objective. If no primary task exists, ask for clarification or answer directly without treating this guideline as the entry point.

## How Other Skills Use This

Execution Skills should read this file before implementation and then apply it as a checklist:

- state assumptions and scope;
- keep edits tied to the request;
- choose the smallest correct change;
- define the command or inspection that verifies success;
- report skipped checks honestly.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## Failure Handling

- If scope is unclear, stop before editing and clarify the ambiguity.
- If verification cannot run, report the intended command, why it could not run, and the remaining risk.
- If a change grows beyond the requested scope, split the work or ask before continuing.
- If existing user changes are present, work around them and do not revert them unless explicitly asked.

## Regression Verification

After applying this guideline to a change, verify with the smallest relevant check: unit test, lint/typecheck, targeted script, build, runtime smoke test, or structure-only inspection when execution is not possible. The final report must distinguish verified, skipped, and unverified items.

## Safety Boundary

This guideline does not authorize destructive commands, credential changes, production configuration changes, bypass/evasion work, or irreversible actions. Follow the repository and task-specific safety rules first, then use this document for engineering discipline.
