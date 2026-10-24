# BRIEFING — 2026-10-24T03:27:30Z

## Mission
Orchestrate HexMedia Studio multi-user auth, conversation memory, LangGraph persistence, studio UI & media manager.

## 🔒 My Identity
- Archetype: teamwork_preview_orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: /root/hexmedia/.agents/teamwork/teamwork_preview_orchestrator_1
- Original parent: ace1a314-3ae0-44fc-a595-c083f7f64dc9
- Original parent conversation ID: ace1a314-3ae0-44fc-a595-c083f7f64dc9

## 🔒 My Workflow
- **Pattern**: Project Pattern
- **Scope document**: /root/hexmedia/PROJECT.md
1. **Decompose**: Surveyed codebase with 3 Explorers. Synthesized architecture and Feature Inventory into PROJECT.md with 4 milestones (M1-M4) + E2E Testing Track.
2. **Dispatch & Execute**:
   - **Direct (iteration loop)**: Top-level orchestrator runs parallel E2E Test Track (via teamwork_preview_test_writer) and Milestone execution loops (teamwork_preview_worker -> 2 teamwork_preview_reviewer -> 2 teamwork_preview_challenger -> teamwork_preview_auditor -> Gate).
3. **On failure** (in this order):
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
4. **Succession**: At 16 spawns, write handoff.md, cancel crons, spawn successor
- **Work items**:
  1. Survey & Architecture Mapping [in-progress]
  2. Decomposition & PROJECT.md [pending]
  3. E2E Testing Track [pending]
  4. Implementation Milestones Execution [pending]
  5. Final Acceptance & Verification [pending]
- **Current phase**: 1
- **Current focus**: Survey & Architecture Mapping via 3 Explorers

## 🔒 Key Constraints
- Never write, modify, or create source code files directly.
- Never run build/test commands yourself — require workers to do so.
- Never investigate or explore the problem at the code level — dispatch Explorers for technical investigation.
- File edits restricted to .agents/teamwork metadata/state files (.md) and PROJECT.md.
- Never reuse a subagent after it has delivered its handoff — always spawn fresh.
- Forensic Auditor has hard binary veto.
- Follow AGENTS.md verification gates and definition of done.

## Current Parent
- Conversation ID: ace1a314-3ae0-44fc-a595-c083f7f64dc9
- Updated: 2026-10-24T03:27:04Z

## Key Decisions Made
- Selected Project Pattern with dual track (Implementation + E2E Testing).
- Survey phase initiated with 3 parallel explorers to inspect codebase, current models, LangGraph setup, Django Ninja API, UI, and test harness.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| Survey Explorer 1 | teamwork_preview_explorer | Survey Auth & Isolation | completed | 273ce8af-e0a9-4d86-9845-17be67a593b8 |
| Survey Explorer 2 | teamwork_preview_explorer | Survey LangGraph & Memory | completed | f4c5fde8-14dc-4c17-88d2-a05d0109b9bb |
| Survey Explorer 3 | teamwork_preview_explorer | Survey UI & Test Harness | completed | 31c5dac2-2cbd-45ab-bd45-2502596e024a |
| E2E Test Writer | teamwork_preview_test_writer | Opaque-box E2E Test Suite | completed | bd4d0695-9c2e-4bbc-a7cc-83e7e4f75379 |
| Worker M1 | teamwork_preview_worker | Milestone 1 Implementation | completed | 2ead3fed-131e-4df0-be6f-abb20e6df2b1 |
| Reviewer 1 | teamwork_preview_reviewer | M1 Code Review | in-progress | 23d10aaa-e430-4301-a725-064fa34eaa2a |
| Reviewer 2 | teamwork_preview_reviewer | M1 Security Review | in-progress | 53660d99-0bd2-4a29-b12d-d7e419cad7e3 |
| Challenger 1 | teamwork_preview_challenger | M1 Adversarial Verification | in-progress | 3281cce9-7621-4e15-ac56-72cdcb6e9c20 |
| Challenger 2 | teamwork_preview_challenger | M1 Stress Verification | in-progress | c9f26261-7075-42ab-8cd0-6e096c7d9415 |
| Auditor 1 | teamwork_preview_auditor | M1 Forensic Audit | in-progress | 0e1d7478-e87b-4dbb-96a8-0940b34bee5d |

## Succession Status
- Succession required: no
- Spawn count: 10 / 16
- Pending subagents: 23d10aaa-e430-4301-a725-064fa34eaa2a, 53660d99-0bd2-4a29-b12d-d7e419cad7e3, 3281cce9-7621-4e15-ac56-72cdcb6e9c20, c9f26261-7075-42ab-8cd0-6e096c7d9415, 0e1d7478-e87b-4dbb-96a8-0940b34bee5d
- Predecessor: none
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: f6e60383-d401-479c-9123-ee0a9cb852cc/task-10
- Safety timer: f6e60383-d401-479c-9123-ee0a9cb852cc/task-167
- On succession: kill all timers before spawning successor
- On context truncation: run `manage_task(Action="list")` — re-create if missing

## Artifact Index
- /root/hexmedia/.agents/teamwork/ORIGINAL_REQUEST.md — Original requirements
- /root/hexmedia/.agents/teamwork/teamwork_preview_orchestrator_1/DISPATCH.md — Incoming dispatches
- /root/hexmedia/.agents/teamwork/teamwork_preview_orchestrator_1/BRIEFING.md — Persistent context & state
- /root/hexmedia/.agents/teamwork/teamwork_preview_orchestrator_1/progress.md — Execution tracking & heartbeat
- /root/hexmedia/PROJECT.md — Global architecture, milestones, interface contracts
