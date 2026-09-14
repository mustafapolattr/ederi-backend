# Ederi
## AI Personal Finance Assistant

**Document Version:** 1.0
**Product Status:** MVP Planning
**Target Platform:** Android
**Backend:** Django + Django REST Framework
**Database:** PostgreSQL
**AI:** LLM-based financial assistant
**Architecture:** Android Client + REST API + Modular Monolith Backend

---

# 1. PRODUCT OVERVIEW

## 1.1 Product Name
**Ederi**
Temporary product name. The name may be changed before public release.

## 1.2 Product Type
Ederi is an Android-first AI-powered personal finance assistant.

It helps users:
- understand where their money goes
- track income and expenses
- manage budgets
- track financial goals
- understand spending patterns
- forecast their future balance
- determine how much money they can safely spend
- interact with their financial data using natural language
- make better day-to-day financial decisions

Ederi is NOT simply an expense tracker.

The core product concept is:
> **Understand your money. Make better decisions. Reach your goals.**

---

# 2. PRODUCT VISION

Ederi should become a personal financial assistant that understands a user's financial situation and turns raw financial data into understandable, actionable information.

Traditional finance applications primarily answer:
> "Where did my money go?"

Ederi should also answer:
> "What can I afford?"
> "Why am I spending more?"
> "How much will I have at the end of the month?"
> "Can I reach my savings goal?"
> "What happens if I spend $500 on this?"
> "What should I change to save more?"

The product should prioritize actionable insights over complicated financial charts.

---

# 3. TARGET MARKET

Ederi is designed as a global product.
The initial product language should be: **English**
The architecture must support internationalization from the beginning.
The application must not be designed specifically around Turkey.
However, the architecture must allow country-specific functionality later.

Examples: TRY, USD, EUR, GBP, other currencies, credit card installments, regional date formats, regional number formats, country-specific financial integrations, Open Banking integrations.

---

# 4. TARGET USERS

Primary users:
- young professionals
- people who want to control their spending
- people trying to save money
- people with multiple accounts/cards
- users who dislike complicated financial applications
- users who want AI-assisted financial insights

The product should initially focus on individual users.
Do NOT implement family/shared accounts in MVP.

---

# 5. CORE USER PROBLEM

Users often have financial data but lack financial clarity. They may know monthly income, account balances, expenses, subscriptions — but still cannot easily answer: How much can I spend? Am I overspending? Will I have enough money at the end of the month? Why did my expenses increase? How much can I save? When can I reach my goal? Can I afford a specific purchase?

Ederi should transform financial data into answers.

---

# 6. PRODUCT PRINCIPLES

**6.1 Simplicity** — Easy to understand. Do not overwhelm users with financial terminology.

**6.2 Actionable Information** — Prefer "You spent 24% more on dining this month." over "Dining: $342.43"

**6.3 Trust** — Financial calculations must be deterministic. The LLM must never be the source of truth for financial numbers.

**6.4 Privacy** — Financial data is highly sensitive. Only the minimum necessary information should be sent to external AI services.

**6.5 Progressive Complexity** — MVP should remain simple. Advanced functionality can be introduced later.

---

# 7. MVP SCOPE

## Included in MVP

**Authentication:** Register, Login, Logout, Password reset, Email verification, User profile

**Financial Accounts:** Cash, Bank account, Credit card, Savings account, Investment account, Other

**Transactions:** Income, Expense, Transfer, Refund, Adjustment

**Categories:** Default categories, Custom categories, Category icons, Category editing

**Budgets:** Monthly budgets, Category budgets, Budget progress, Budget warnings

**Goals:** Savings goals, Target amount, Current amount, Target date, Required monthly contribution, Goal progress

**Recurring Payments:** Subscription tracking, Recurring bills, Recurring income, Expected payment date

**Dashboard:** Net worth, Total balance, Available to spend, Monthly income, Monthly expenses, Savings, Budget status, Goal progress, AI insights

**Forecast:** Expected month-end balance, Expected income, Expected recurring expenses, Expected variable spending

**AI:** Natural language transaction creation, Transaction categorization, Spending analysis, Financial insights, Financial data chat, Basic what-if scenarios

**Import:** CSV transaction import

**Android:** Native Android application, Offline-friendly local state, API synchronization, Push notifications

---

# 8. FEATURES EXPLICITLY OUTSIDE MVP

Do NOT implement these unless explicitly requested later: Bank integrations, Open Banking, Automatic bank synchronization, Investment trading, Crypto trading, Tax calculations, Money transfers, Payment processing, Family accounts, Social features, Marketplace, Financial advisor services, Insurance, Loans, Complex autonomous AI agents, Web application, iOS application, Wear OS application.

The architecture should allow these features to be added later.

---

# 9. ANDROID APPLICATION

## 9.1 Technology

Use: Kotlin, Jetpack Compose, Android Jetpack, MVVM or Clean Architecture, Kotlin Coroutines, Kotlin Flow, Retrofit, OkHttp, Kotlin Serialization or Moshi, Room, Hilt, WorkManager, Android Keystore where appropriate.

Use current stable Android development practices. Avoid deprecated Android APIs.

---

# 10. ANDROID ARCHITECTURE

Use a clean, maintainable architecture.

```text
Android App
│
├── Presentation
│   ├── Screens
│   ├── Components
│   ├── ViewModels
│   └── Navigation
│
├── Domain
│   ├── Models
│   ├── UseCases
│   └── Repository Interfaces
│
├── Data
│   ├── Remote
│   ├── Local
│   ├── DTOs
│   ├── Database
│   └── Repository Implementations
│
└── Core
    ├── Network
    ├── Authentication
    ├── Error Handling
    ├── Security
    └── Utilities
```

The application should not put business logic directly into Compose UI.

---

# 11. OFFLINE STRATEGY

Room should be used for local persistence/cache. Users should be able to open previously loaded financial information, create transactions while temporarily offline, edit local data, queue synchronization.

```text
Local Change → Sync Queue → API → Backend Validation → Database → Sync Response → Local Database
```

Conflict resolution must be deterministic.

---

# 12. AUTHENTICATION

Email, Password, Secure token-based authentication.
The Android application must securely store authentication credentials/tokens. Do not store passwords locally. Use Android secure storage mechanisms where appropriate. Authentication state should survive application restarts without exposing credentials.

---

# 13. MAIN NAVIGATION

Recommended bottom navigation: Home, Transactions, Budget, Goals, AI. Profile/settings accessible from the Home screen.

---

# 14. HOME DASHBOARD

The Home screen is the primary screen. Prioritize important information, avoid excessive charts. Shows: Net Worth, Available to Spend, This Month (Income/Expenses/Saved), AI Insight, Budget progress, Goals progress, Upcoming payments.

---

# 15. ACCOUNT MANAGEMENT

Account fields: id, user_id, name, type, currency, initial_balance, current_balance, is_active, created_at, updated_at.
Account types: cash, bank, credit_card, savings, investment, other.
The backend must calculate balances reliably. The client must never be treated as the financial source of truth.

---

# 16. TRANSACTIONS

Transaction types: income, expense, transfer, refund, adjustment.
Transaction fields: id, user_id, account_id, category_id, type, amount, currency, merchant, description, notes, transaction_date, created_at, updated_at.
Optional future fields: tags, location, attachment, recurring_payment_id.

---

# 17. TRANSACTION RULES

- **Expense** decreases account balance.
- **Income** increases account balance.
- **Transfer** moves money between two accounts; must NOT affect net income or expense totals; net worth remains unchanged.
- **Refund** reverses or partially reverses an expense.
- **Adjustment** corrects account balances.

All financial calculations must be tested thoroughly.

---

# 18. CATEGORIES

Default categories: Food, Transport, Housing, Bills, Shopping, Entertainment, Health, Education, Travel, Subscriptions, Personal, Other.
Users can create custom categories.
Category fields: id, user_id, name, icon, color, type, is_default, created_at, updated_at.
Category type: income, expense, both.

---

# 19. TRANSACTION ENTRY

Users add transactions manually (amount, type, category, merchant, account, date, notes). Must be fast — a few seconds.

---

# 20. AI TRANSACTION ENTRY

Users write natural language e.g. "Spent $42.50 at Starbucks yesterday." The AI parses this into structured JSON. AI output must NOT directly modify the database.

Required pipeline:
```text
User Input → LLM → Structured JSON → Schema Validation → Business Validation → User Confirmation if necessary → Database
```

If important information is missing, ask the user (e.g. "Which account did you use?").

---

# 21. AI CATEGORIZATION

AI can suggest transaction categories, but classification is a suggestion only. The backend validates the category. Users must be able to change the category manually.

---

# 22. BUDGETS

Budget fields: id, user_id, category_id, amount, currency, period, start_date, end_date, created_at, updated_at.

```text
budget_remaining = budget_amount - actual_expenses
```

Budget calculations must be backend-driven.

---

# 23. GOALS

Goal fields include target amount, current amount, remaining, target date.

```text
required_monthly_contribution = remaining_amount / remaining_months
```

Goals can include: emergency fund, vacation, car, home, education, custom goal.

---

# 24. RECURRING PAYMENTS

Fields: id, user_id, name, amount, currency, frequency, next_payment_date, category_id, account_id, is_active.
Supported initial frequencies: weekly, monthly, quarterly, yearly.

---

# 25. AVAILABLE TO SPEND

One of the core Ederi metrics — estimates how much the user can safely spend during the remaining period.

```text
available_to_spend =
    current_available_balance
    + expected_income
    - expected_recurring_expenses
    - planned_budget_commitments
    - goal_contributions
```

The exact formula must be documented and implemented deterministically in backend business logic. The AI must never invent this number.

---

# 26. MONTH-END FORECAST

Uses current balance, historical spending, current month spending, expected income, recurring expenses, upcoming payments, active budgets. Forecast methodology should initially remain simple and explainable. Do not build a complex machine-learning forecasting system for MVP.

---

# 27. AI SPENDING ANALYSIS

The AI analyzes aggregated backend data (not raw transactions) and converts it into a human-friendly explanation. The AI must only use facts supplied by the backend.

---

# 28. AI FINANCIAL ASSISTANT

Natural language Q&A screen, e.g. "How much did I spend on food this month?", "Can I afford a $500 phone?", "How long will it take me to reach my vacation goal?" — all answered from actual user data.

---

# 29. AI CHAT ARCHITECTURE

Never send the entire database to the LLM.

```text
User Question → Intent Detection → Backend Data Retrieval → Financial Calculations → Structured Context → LLM → Validated Response → User
```

---

# 30. FINANCIAL SAFETY RULES FOR AI

The AI must never: invent transactions, invent account balances, invent income/expenses, invent calculations, claim access to bank accounts when none exists, execute financial transactions, make investment trading decisions, provide regulated financial advice, manipulate financial records without validation.

The AI may: explain, summarize, categorize, compare, calculate through backend-provided tools, identify patterns, provide general educational suggestions.

---

# 31. WHAT-IF SCENARIOS

Backend performs the calculation (e.g. current balance − hypothetical spend = projected balance); AI explains the result. Do not allow the LLM to perform the underlying financial calculation itself.

---

# 32. NOTIFICATIONS

Budget nearing limit, Budget exceeded, Upcoming recurring payment, Goal progress, Monthly summary, Unusual spending, Forecast warning. Should be useful, not spam.

---

# 33. CSV IMPORT

```text
CSV → File validation → Column detection → Parsing → Validation → Duplicate detection → Preview → User confirmation → Import
```

Never import unvalidated data directly. CSV injection and malicious file content must be considered.

---

# 34. DATABASE

Use PostgreSQL. Initial entities: User, Account, Category, Transaction, Budget, Goal, RecurringPayment, AIConversation, AIMessage, Notification, ImportJob.

Use proper foreign keys and indexes. Use decimal/numeric types for monetary values. NEVER use floating-point numbers as the authoritative storage type for money.

---

# 35. MONEY REPRESENTATION

Backend should use PostgreSQL `NUMERIC` / Django `DecimalField` (e.g. `Decimal("42.50")`). Do NOT use `float`/`double` for authoritative financial calculations. Currency must be explicitly associated with monetary values.

---

# 36. MULTI-CURRENCY

MVP should support multiple currencies at the data-model level (USD, EUR, GBP, TRY, JPY, etc). Each account has a base currency; each transaction has a currency. Currency conversion can initially be limited — do NOT build a complex currency exchange system unless required, but the architecture should allow exchange-rate functionality later.

---

# 37. BACKEND

Use: Python, Django, Django REST Framework, PostgreSQL, Redis, Celery, Docker.

Recommended Django modules: users, accounts, transactions, categories, budgets, goals, recurring_payments, notifications, imports, reports, ai, core.

Do not create microservices for MVP. Use a modular monolith.

---

# 38. BACKEND ARCHITECTURE

```text
Android → REST API → Django (Authentication, Accounts, Transactions, Budgets, Goals, Reports, AI → LLM API) → PostgreSQL
```

Redis/Celery for asynchronous work (monthly reports, notifications, heavy CSV processing, AI background processing if necessary).

---

# 39. API VERSIONING

Use `/api/v1/`. All APIs should be versioned.

---

# 40. INITIAL API

**Authentication:** POST /api/v1/auth/register, /login, /logout, /password-reset

**Accounts:** GET/POST /api/v1/accounts, GET/PATCH/DELETE /api/v1/accounts/{id}

**Transactions:** GET/POST /api/v1/transactions, GET/PATCH/DELETE /api/v1/transactions/{id}

**Categories:** GET/POST /api/v1/categories, PATCH/DELETE /api/v1/categories/{id}

**Dashboard:** GET /api/v1/dashboard

**Budgets:** GET/POST /api/v1/budgets, PATCH/DELETE /api/v1/budgets/{id}

**Goals:** GET/POST /api/v1/goals, PATCH/DELETE /api/v1/goals/{id}

**AI:** POST /api/v1/ai/parse-transaction, /analyze, /chat, /scenario

**Import:** POST /api/v1/imports/csv, GET /api/v1/imports/{id}

---

# 41. API DESIGN RULES

Predictable, consistent status codes, error format, pagination, validation errors, authentication errors.

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid transaction amount.",
    "field": "amount"
  }
}
```

Do not expose internal stack traces to clients.

---

# 42. SECURITY

Secure authentication, authorization, object-level access control, password hashing, rate limiting, input validation, SQL injection protection, CSRF protection where applicable, secure CORS configuration, secure headers, secrets management, audit logging, secure file upload, API throttling.

Every endpoint must verify that the requested object belongs to the authenticated user or that the user is otherwise authorized. Prevent IDOR vulnerabilities.

---

# 43. AI SECURITY

Consider: prompt injection, malicious transaction descriptions, malicious CSV content, data leakage, excessive data sent to LLM, unauthorized AI actions, hallucinated financial information. User-controlled text must never be treated as trusted instructions. AI outputs must be validated.

---

# 44. PRIVACY

Support: account deletion, data deletion, privacy settings, minimal AI data sharing, audit logs, secure storage, data export. Designed with GDPR and KVKK considerations in mind. Legal compliance must be reviewed before public launch.

---

# 45. AI DATA POLICY

The AI service should receive only the data necessary to answer a question — never the entire user database. Backend calculates relevant statistics; only relevant aggregated information is sent.

---

# 46. ANDROID UI/UX PRINCIPLES

Material Design / Material 3. Clean, modern, minimal, readable, responsive, accessible. Avoid excessive gradients and unnecessary visual complexity. Important numbers should have clear visual hierarchy.

---

# 47. CORE ANDROID SCREENS

Splash, Onboarding, Login, Register, Forgot Password, Home, Accounts, Account Details, Transactions, Transaction Details, Add/Edit Transaction, Budgets, Budget Details, Create Budget, Goals, Goal Details, Create Goal, Recurring Payments, AI Assistant, CSV Import, Notifications, Profile, Settings, Privacy, Security.

---

# 48. ONBOARDING

Target: under 5 minutes.

```text
Welcome → Create Account → Choose Currency → Create First Account → Enter Current Balance → Optional First Transaction → Create Optional Goal → Dashboard
```

Do not force users to configure everything.

---

# 49. FIRST VALUE

The application should aim to show a useful dashboard immediately after initial setup (balance, this month's income/expenses, available to spend, a first AI insight).

---

# 50. TESTING

**Backend tests:** model, service, API, authentication, authorization, financial calculation, transaction, budget, goal, forecast, import, AI validation tests.

**Android tests:** unit, ViewModel, repository, UI, navigation, offline/sync tests.

---

# 51. FINANCIAL TESTING

Test: income, expense, transfer, refund, adjustment, multiple accounts, multiple currencies, budget/goal calculations, recurring payments, forecast, available-to-spend. Example: starting balance $1,000, expense $100 → expected balance $900. Transfer preserves total net worth.

---

# 52. SECURITY TESTING

Test for: IDOR, broken authorization, SQL injection, XSS, CSRF, rate-limit bypass, authentication bypass, JWT/session issues, file upload vulnerabilities, CSV injection, prompt injection, data leakage, sensitive information exposure.

---

# 53. PERFORMANCE

MVP prioritizes correctness and maintainability, but: optimize database queries, add indexes where appropriate, avoid N+1 queries, use pagination, cache appropriate data, avoid unnecessary AI calls, use background tasks for expensive operations.

---

# 54. OBSERVABILITY

Structured logging, error tracking, request tracing where appropriate, performance monitoring, background job monitoring. Never log: passwords, authentication tokens, sensitive financial information unnecessarily, complete AI prompts containing sensitive data unless explicitly required and protected.

---

# 55. MONETIZATION

Freemium model. **Free:** manual transaction tracking, accounts, basic budgets/goals, limited AI. **Premium:** unlimited AI, advanced insights/forecasting/scenarios/reports, additional customization. Do not over-engineer billing in the initial development phase.

---

# 56. FUTURE ROADMAP

**Phase 2:** improved AI insights, advanced forecasting, better recurring-payment detection, advanced reports, premium subscription.
**Phase 3:** bank integrations, Open Banking, automatic transaction sync/categorization/balance updates.
**Phase 4:** investment tracking, advanced financial planning, family accounts, web app, iOS app.

---

# 57. BANK INTEGRATION PRINCIPLE

Bank integration is intentionally NOT part of MVP, but the architecture must allow it to be added later without rewriting the system. The transaction domain must not assume that all transactions originate from manual entry (possible future source: manual, csv, bank, api, import).

---

# 58. PRODUCT DIFFERENTIATION

Ederi should NOT compete purely on "we also have expense tracking." Main differentiation: **financial clarity + AI assistance**, connecting Transactions → Spending Patterns → Budget → Forecast → Goals → AI Insights → Action.

---

# 59. NORTH STAR METRIC

Not downloads/registrations/app opens alone. Meaningful metric: **number of active users who regularly track/review their financial situation and receive value from Ederi.** Supporting metrics: onboarding completion, first transaction, transactions per active user, D7/D30 retention, MAU, AI interactions, budget/goal creation, subscription conversion.

---

# 60. DEVELOPMENT STRATEGY

Development must happen incrementally. Do NOT attempt to generate the entire application in one step.

```text
Phase 1: Project setup, Authentication, Database, Basic Android architecture
Phase 2: Accounts, Transactions, Categories
Phase 3: Dashboard, Budgets, Goals
Phase 4: Recurring payments, Forecast, Available to spend
Phase 5: AI transaction parser, AI insights, AI chat
Phase 6: CSV import, Notifications
Phase 7: Testing, Security, Performance, Release preparation
```

Each phase must produce a working state.

---

# 61. GIT STRATEGY

Branches: main, develop, feature/*, bugfix/*. Commits should be small and meaningful (e.g. `feat: add account management`, `test: add transaction calculation tests`).

---

# 62. ENVIRONMENT CONFIGURATION

Separate development/staging/production. Never commit secrets (DATABASE_URL, SECRET_KEY, JWT_SECRET, REDIS_URL, LLM_API_KEY). Use environment variables or secure secret management.

---

# 63. CODING STANDARDS

**Backend:** PEP 8, type hints where useful, clear service boundaries, serializers for API validation, business logic in services/domain layer, meaningful names, small functions, tests for important behavior.

**Android:** Kotlin idioms, immutable UI state where practical, ViewModel-based state management, coroutines/Flow, dependency injection, reusable Compose components, no business logic inside composables.

---

# 64. IMPORTANT ARCHITECTURAL RULE

Do NOT over-engineer. MVP = Android + Django REST API + PostgreSQL + Redis/Celery where necessary + LLM API. Do NOT introduce Kubernetes, microservices, event-driven distributed architecture, Kafka, complex service mesh, or unnecessary infrastructure unless there is a demonstrated requirement.

---

# 65. AI CODING ASSISTANT INSTRUCTIONS

You are a senior Android and backend software engineer implementing Ederi based strictly on this specification. This document is the source of truth.

## Rules
1. Do not invent features.
2. Do not remove required features.
3. Do not change architecture without explaining why.
4. Do not introduce unnecessary technologies.
5. Do not introduce microservices for MVP.
6. Do not implement bank integrations in MVP.
7. Do not use LLMs as the source of financial truth.
8. Do not use floating point for authoritative monetary calculations.
9. Validate all AI outputs.
10. Never allow an LLM response to directly modify the database.
11. All financial calculations must be deterministic.
12. All important financial logic must have automated tests.
13. Follow secure coding practices.
14. Protect user data.
15. Do not expose sensitive information in logs.
16. Follow Android modern development practices.
17. Follow clean architecture principles.
18. Keep the code maintainable.
19. Avoid premature optimization.
20. Avoid unnecessary abstraction.
21. Do not implement future features unless explicitly requested.

---

# 66. AI IMPLEMENTATION WORKFLOW

For every requested feature:

1. **Understand** — read the relevant requirements.
2. **Analyze** — identify affected modules, database changes, API changes, Android changes, security implications, testing requirements.
3. **Plan** — provide a concise implementation plan before writing code.
4. **Implement** — implement the feature.
5. **Test** — write and run appropriate tests.
6. **Review** — correctness, security, architecture, edge cases, performance, maintainability.
7. **Report** — what was implemented, files changed, tests added/executed, known limitations.

---

# 67. FIRST DEVELOPMENT TASK

Do NOT start by implementing the whole application. First create the project foundation.

**Backend:** Django project, DRF, PostgreSQL configuration, environment configuration, base project structure, authentication foundation, testing configuration, Docker configuration.

**Android:** Kotlin Android project, Jetpack Compose, Material 3, Navigation, Hilt, Retrofit, Room, Coroutines, Flow, basic project architecture, environment configuration, testing foundation.

Do not implement financial features yet. The first milestone is a clean, compilable, testable project foundation.

---

# 68. FIRST OUTPUT REQUIRED FROM CODING AI

Before writing implementation code, provide: (1) proposed repository structure, (2) backend directory structure, (3) Android directory structure, (4) database migration strategy, (5) authentication strategy, (6) API communication strategy, (7) local/offline data strategy, (8) environment configuration strategy, (9) testing strategy, (10) development phases.

Then wait for approval before implementing the first major feature.

---

# 69. DEFINITION OF DONE

A feature is complete when: requirements are implemented, code is clean, security is considered, edge cases are handled, automated tests exist and pass, API behavior is documented where necessary, Android UI handles loading/error/empty states, errors are handled gracefully, no obvious architecture violations exist.

---

# 70. ERROR STATES

Every Android screen that communicates with the backend should consider: Loading, Success, Empty, Error, Offline, Unauthorized. Do not show raw backend errors directly to users — provide human-readable messages.

---

# 71. EMPTY STATES

Examples: "No transactions yet." → "Add your first transaction." "Create a goal and start planning your future." "Set a monthly budget to understand your spending."

---

# 72. ACCESSIBILITY

Readable typography, sufficient contrast, content descriptions, screen reader compatibility, scalable text where possible, touch targets of appropriate size. Do not communicate financial meaning through color alone.

---

# 73. RELEASE STRATEGY

Initial release target: Android, for Google Play distribution. Before production release: privacy policy, terms of service, account deletion, crash reporting, analytics, security review, production environment, database backups, monitoring, Play Store assets, app signing, release configuration. Legal and financial compliance must be reviewed before public launch.

---

# 74. FINAL PRODUCT PRINCIPLE

Ederi should answer three questions: **1. Where is my money going?** (transactions, categories, reports). **2. What can I afford?** (available-to-spend, budgets, forecasts). **3. How can I reach my goals?** (goals, forecasts, scenarios, AI insights).

---

# 75. FINAL INSTRUCTION TO THE CODING AI

Build Ederi as a production-quality Android-first personal finance application.

Use: Android/Kotlin/Jetpack Compose/Clean Architecture/MVVM/Room/Retrofit/Hilt/Coroutines-Flow for the client; Python/Django/DRF/PostgreSQL/Redis/Celery for the backend; LLM API with structured outputs, validated AI processing, and backend-controlled financial calculations for AI.

Start with the foundation. Do not build everything at once. Do not invent functionality. Do not implement bank integrations in MVP. Do not use the LLM as a financial calculation engine. Do not allow AI output to directly modify financial data.

Priorities, in order: 1) Correctness, 2) Security, 3) Privacy, 4) Maintainability, 5) User experience, 6) Testability, 7) Performance.

The final product should feel like a trustworthy personal financial assistant, not merely another expense-tracking application.
