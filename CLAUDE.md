# Ederi — Project Instructions

This repository follows `SPECIFICATION.md` (project root) as the single
source of truth for product scope and architecture. Read it in full before
planning or implementing anything.

## Non-negotiable rules
- Do not invent, remove, or reduce features from the specification.
- Do not introduce microservices, Kubernetes, or unnecessary infrastructure for the MVP — modular monolith only.
- Do not implement bank integrations in the MVP.
- The LLM is never the source of truth for financial numbers. All money math is deterministic backend logic (spec §25–31).
- Never use floating point for money — Decimal / PostgreSQL NUMERIC only (spec §35).
- AI output never writes directly to the database — always schema + business validation first (spec §20, §30).
- Follow the phased plan in spec §60. Do not build features out of order.
- For every feature: understand → analyze → plan → get my approval → implement → test → report (spec §66).

## Simplicity rule
- Keep everything simple and shallow. Prefer the most direct implementation.
- No extra layers, abstractions, or edge-case handling unless the spec requires it.
- UI: plain forms and lists, minimal screens, no complex state logic.
- When in doubt, choose less code.

## Current phase
Phase 3 — Dashboard, Budgets, Goals (spec §60). Approved to proceed.
No Recurring Payments/Forecast/AI/CSV Import yet.
