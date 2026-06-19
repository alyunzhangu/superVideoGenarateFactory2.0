# Two-Segment Storyboards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate at most two story-driven, continuity-locked storyboard boards for reference videos up to 30 seconds, with an explicit narrative split selected before deterministic duration validation.

**Architecture:** The Skill analyzes the approved script and chooses one named `split_boundary` from a completed action, sentence, story beat, scene transition, or internal action beat. `segment_plan.py` does not make creative choices; it validates the chosen boundary against the 5-15 second per-segment limits, the 17-second threshold, and the 30-second input maximum. Each resulting segment gets its own storyboard and Seedance prompt while sharing one continuity manifest.

**Tech Stack:** Codex Skill Markdown, Python 3 standard library, `unittest`, existing image2 and Seedance tooling.

---

### Task 1: Lock Dynamic Split Behavior With Failing Tests

**Files:**
- Modify: `seedance-storyboard-replication/tests/test_segment_plan.py`
- Modify: `seedance-storyboard-replication/tests/test_skill_contract.py`

- [ ] Add tests proving 25-second and 27-second scripts use the caller-selected narrative boundary rather than an automatically balanced point.
- [ ] Add tests proving more than 17 seconds requires `split_boundary`, more than 30 seconds is rejected, a split not present in approved boundaries is rejected, and every valid plan has at most two segments.
- [ ] Add Skill contract assertions for the upload recommendation, 30-second limit, exactly two storyboards for more than 17 seconds, explicit narrative analysis, continuity manifest, and per-segment storyboard mapping.
- [ ] Run the focused tests and verify they fail because `plan_segments` has no `split_boundary` contract and the Skill still describes one whole-video board.

### Task 2: Make the Planner Validate Rather Than Invent the Split

**Files:**
- Modify: `seedance-storyboard-replication/scripts/segment_plan.py`
- Modify: `seedance-storyboard-replication/tests/test_segment_plan.py`

- [ ] Change the API to `plan_segments(boundaries, split_boundary=None)`.
- [ ] Preserve one segment for `<=15s` and one retimed 15-second segment for `>15s` through `17s`.
- [ ] Reject totals above 30 seconds. For `>17s` through `30s`, require one selected boundary, verify it is an approved boundary, and verify both resulting durations are 5-15 seconds.
- [ ] Add CLI flag `--split-boundary FLOAT` and serialize the selected split for traceability.
- [ ] Run the focused planner suite and verify every valid plan contains one or two segments only.

### Task 3: Generate One Continuity-Locked Board Per Segment

**Files:**
- Modify: `seedance-storyboard-replication/SKILL.md`
- Modify: `seedance-storyboard-replication/references/daohuo_storyboard_prompt.md`
- Modify: `seedance-storyboard-replication/references/seedance-prompt.md`
- Modify: `seedance-storyboard-replication/tests/test_skill_contract.py`

- [ ] Add the early user notice: `<=15s` is most stable; `18-30s` needs two generated clips and a natural handoff; a 30-second source must hand off at 15 seconds.
- [ ] Move duration planning before image2 in both routes. Generate one board for one segment or exactly two boards for two segments, never one whole-video board reused by both tasks.
- [ ] Add storyboard dynamic fields for segment index, global Cut range, local duration, incoming state, outgoing state, adjacent-board role, and the shared continuity manifest.
- [ ] Require the user to approve both boards and the boundary continuity. A revision at the boundary invalidates both adjacent storyboard approvals and both affected Seedance prompt digests.
- [ ] Map each Seedance request's `@图片1` to its own segment board and include the same identity/product/environment locks plus explicit incoming/outgoing handoff text.
- [ ] Run the focused contract tests and verify they pass.

### Task 4: Verify, Install, Commit, and Push

**Files:**
- Update installed copy: `/Users/jiangyongjian/.codex/skills/seedance-storyboard-replication/*`

- [ ] Run the full repository test suite, Python compilation, Skill validator, and `git diff --check`.
- [ ] Run planner CLI smoke checks for selected 25-second, 27-second, and 30-second splits and inspect that no plan contains more than two segments.
- [ ] Install the Skill, run installation checks, and rerun the installed test suite and validator.
- [ ] Commit the verified implementation and push `feature/seedance-storyboard-replication` to the existing draft PR.
