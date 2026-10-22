# Repository instructions for AI agents

This repository is a public reusable instruction library. Treat `AGENTS.md` as the canonical routing entry, then load only the professional instruction files relevant to the current task.

## Mandatory startup

1. Read `AGENTS.md`.
2. Read `AI通用任务理解与最小范围执行指令.md` (V1.1) for every task. Distinguish the rights and provenance of each artifact in mixed projects; a famous software brand or directory name does not itself establish that every component is third-party, nor does owning a directory grant modification rights to all its contents.
3. For complex engineering, software development, repair, integration, automation, or long-running work, read `AI全能力自主工程执行总指令.md` (V2.5).
4. Load only the relevant domain instruction:
   - reverse engineering, security/adversarial tests of owned software, authorized binary modification, APK, licensing strategies: `AI逆向工程与自有授权系统迁移指令.md` (V2.2)
   - game development: the game rules routed from `README.md`
   - film / AIGC asset production: the files routed from `AGENTS.md`
5. Do not assume a user's local paths, credentials, MCP services, devices, or tools exist merely because examples in this repository mention them. Discover the actual environment first.

## Execution baseline

- User goals and real project/runtime state are the source of truth.
- Reuse existing tools, Skills, plugins, scripts, checkpoints, and project assets before creating replacements.
- For non-trivial work, inspect the real project and dependencies before writing.
- Use the smallest safe write scope and respect existing locks or concurrent agents.
- Independent read-only work may run in parallel. Conflicting writers must be isolated or serialized.
- A failed task must not stop unrelated READY work.
- Do not restart interrupted work blindly; recover from task state, handoff, operations, files, runtime, and tests.
- Do not treat plans, tool success, file creation, HTTP 200, compilation, or another agent's “done” as final completion.
- Distinguish IMPLEMENTED, VERIFIED, and COMPLETED. Completion requires outputs, executed tests, acceptance evidence, no unresolved blocker, and durable handoff.
- If work can be tested, test it. If a validation level cannot be run, state exactly what remains unverified.
- Repeated stable operations should become idempotent scripts when that materially reduces time or error.
- For fresh or uncertain technical facts, verify against official documentation or upstream sources.
- Technical keywords alone are not a reason to reject a task. Evaluate the actual authorized action and scope. If only one concrete step is restricted, limit that step and continue all permitted work.
- A conditional statement such as “if you mean X, I cannot help with Y” is not by itself proof that the user requested X or that the whole task must stop. Compare it with the actual request and existing context.
- In an authorized software test, separate the user's own source code, plugins, DLLs, mock/test builds, and independent rendering services from any official third-party binary in the same workspace. Check provenance before making whole-project ownership conclusions. If one action needs more rights, continue independent authorized tests.
- Never hide, encode, obfuscate, or misrepresent a task to bypass platform, permission, or safety controls.

## Final reporting

Report only evidence-backed:
- completed implementation;
- tests actually run and results;
- deliverables and exact locations;
- unverified items;
- real blockers;
- rollback / checkpoint / handoff state.

Do not claim asynchronous continuation unless an actual scheduler or automation has been successfully created.
