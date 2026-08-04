\# Sprint 6 – AI Matching Engine



\## Goal



Build an explainable matching engine that compares candidate intelligence with discovered jobs and produces a reliable recommendation.



\## Core Principles



\- Never invent candidate qualifications.

\- Every score must be explainable.

\- Mandatory job requirements must be treated separately from preferred requirements.

\- Deterministic rules should be used before AI-generated interpretation.

\- Low-confidence matches must be marked for review.

\- The engine must support future LLM and embedding upgrades without depending on one provider.



\## Components



backend/app/models/

&#x20;   job\_match.py



backend/app/schemas/

&#x20;   job\_matching.py



backend/app/services/

&#x20;   matching\_engine.py

&#x20;   match\_scoring.py



backend/app/api/routes/

&#x20;   matches.py



backend/alembic/versions/

&#x20;   sprint6\_job\_matches.py



tests/

&#x20;   test\_match\_scoring.py

&#x20;   test\_matching\_engine.py

&#x20;   test\_match\_routes.py



\## Scoring Dimensions



\- Relevant experience

\- Skills

\- Leadership scope

\- Industry fit

