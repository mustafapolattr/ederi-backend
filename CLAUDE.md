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

## Current phase
Phase 1 — project foundation only (spec §67). No financial features yet.
Do not start Phase 2 (Accounts/Transactions/Categories) without explicit go-ahead.
