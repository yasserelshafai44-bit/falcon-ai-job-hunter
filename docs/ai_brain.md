# Falcon AI Brain Architecture

## 1. Purpose

Falcon's AI Brain is the intelligence layer that converts candidate information and job information into explainable, auditable career decisions. It must support multiple model providers, preserve truthful candidate data, separate deterministic rules from model-generated content, and require human confirmation for sensitive or uncertain actions.

## 2. Design Principles

- Truth before persuasion: never invent qualifications, employment history, metrics, legal status, or personal details.
- AI-assisted, not AI-uncontrolled: sensitive answers and final submissions require configurable approval.
- Explainability: every match score and recommendation must include its evidence and uncertainty.
- Provider independence: business logic must not depend directly on one LLM vendor.
- Structured outputs: agents return validated Pydantic models rather than free-form text where practical.
- Privacy by default: CVs and candidate data are minimized, access-controlled, and never placed in logs.
- Deterministic foundations: filtering, duplicate detection, permissions, and workflow state use conventional code.
- Testability: prompts, parsers, scoring rules, and provider adapters are independently testable.

## 3. High-Level Architecture

Candidate documents and preferences flow into Candidate Intelligence. Job descriptions flow into Job Intelligence. Both produce normalized structured records and semantic representations. The Matching Engine compares them, creates a score with evidence, and sends shortlisted jobs to application-content agents. A workflow orchestrator manages state, retries, approvals, and audit records.

Main components:

1. Candidate Intelligence
2. Job Intelligence
3. Matching Engine
4. Recruiter Agent
5. CV Agent
6. Cover Letter Agent
7. Screening Answer Agent
8. Interview Agent
9. Career Coach
10. Memory and Retrieval
11. LLM Provider Abstraction
12. Prompt and Evaluation Framework
13. Workflow Orchestration
14. Safety, Privacy, and Audit Layer

## 4. Candidate Intelligence

### Responsibilities

- Parse PDF and DOCX CVs.
- Extract identity, work history, education, certifications, skills, achievements, industries, languages, and location.
- Distinguish direct evidence from inference.
- Normalize job titles, dates, companies, locations, and metrics.
- Build one canonical candidate profile from multiple CV versions.
- Detect conflicts between CV versions and request confirmation instead of guessing.
- Create career-track views such as Multi-Site Operations and Delivery/Marketplace Operations.
- Store source references for every extracted fact.

### Core data structures

- CandidateProfile
- EmploymentRecord
- EducationRecord
- Skill
- Achievement
- LeadershipScope
- CommercialMetric
- CareerPreference
- WorkAuthorization
- CandidateEvidence
- CandidateProfileVersion

### Evidence model

Every important fact should include:

- value
- source document
- page or section
- confidence
- extraction method
- confirmed_by_user
- last_updated

## 5. Job Intelligence

### Responsibilities

- Parse job title, company, location, compensation, working arrangement, duties, requirements, benefits, and application deadline.
- Separate mandatory requirements from preferred requirements.
- Identify seniority, function, industry, team size, operational scope, and commercial ownership.
- Extract ATS keywords without treating keyword frequency as proof of fit.
- Detect ambiguous, discriminatory, or sensitive questions.
- Store the original description and a normalized representation.
- Deduplicate listings across sources.

### Core data structures

- JobListing
- JobRequirement
- JobResponsibility
- CompensationRange
- WorkArrangement
- JobEvidence
- JobIntelligenceProfile

## 6. Matching Engine

The matching engine combines deterministic scoring with optional model-assisted semantic analysis.

### Recommended scoring dimensions

- Relevant experience
- Skills
- Leadership scope
- Industry
- Seniority
- Commercial and P&L responsibility
- Delivery/marketplace experience
- Qualifications
- Location and working arrangement
- Compensation
- Career progression
- Mandatory requirement gaps
- Evidence quality

### Output

- overall_score: 0-100
- recommendation: strong_apply, apply, review, weak_match, reject
- interview_probability_band: low, medium, high
- strengths
- gaps
- mandatory_failures
- evidence
- uncertainty
- recommended_cv_track
- recommended_next_action

The system must never present interview probability as a scientifically precise prediction unless validated against sufficient real outcome data.

## 7. Recruiter Agent

### Responsibilities

- Review shortlisted jobs.
- Rank opportunities by expected value, not application volume.
- Explain why a role is or is not worth pursuing.
- Select the appropriate candidate profile and CV track.
- Identify missing information before application preparation.
- Create a daily review queue.

### Restrictions

- Cannot invent candidate facts.
- Cannot override mandatory requirement failures without explanation.
- Cannot submit an application by itself unless the workflow policy explicitly allows it and no protected or uncertain answer is involved.

## 8. CV Agent

### Responsibilities

- Select the correct master CV.
- Reorder truthful achievements for relevance.
- Adjust the professional summary and skills section.
- Preserve chronology and factual accuracy.
- Generate DOCX and PDF output.
- Record differences from the master CV.
- Run ATS and consistency checks.

### Output

- tailored CV document
- change log
- matched keywords
- excluded content
- factual validation result
- ATS warnings

## 9. Cover Letter Agent

### Responsibilities

- Write concise, employer-specific letters.
- Use verified candidate achievements and job evidence.
- Avoid generic praise and fabricated company claims.
- Adapt tone to the role and employer.
- Produce a rationale and evidence map for internal review.

Company research should be clearly separated from information found in the job listing.

## 10. Screening Answer Agent

Questions are classified into:

- Verified profile facts: may be answered automatically.
- Generated professional responses: may be drafted from evidence.
- Sensitive or legal questions: require user confirmation.
- Unknown questions: must pause the workflow.
- Optional demographic questions: default to no automatic response unless explicitly configured.

Examples requiring confirmation include sponsorship, criminal history, disability disclosure, salary declarations, restrictive covenants, and legal attestations.

## 11. Interview Agent

### Responsibilities

- Build job-specific preparation packs.
- Generate likely competency and technical questions.
- Map questions to verified STAR examples.
- Identify weak areas requiring preparation.
- Simulate interviews and provide evidence-based feedback.
- Never claim knowledge of confidential employer interview questions.

## 12. Career Coach

### Responsibilities

- Analyze application outcomes.
- Recommend improvements to search strategy, positioning, and skill development.
- Identify patterns by role, source, CV version, salary, and employer type.
- Avoid drawing strong conclusions from very small samples.
- Distinguish observation, inference, and recommendation.

## 13. Memory Strategy

Use separate memory classes:

### Transactional memory

Stored in PostgreSQL:

- candidate profiles
- job listings
- applications
- approvals
- generated documents
- workflow state
- outcomes
- audit events

### Semantic memory

Stored using pgvector or another replaceable vector store:

- CV evidence chunks
- achievements
- job-description chunks
- company notes
- interview notes
- recruiter interactions

### Session memory

Temporary working context for one workflow execution. It must not become permanent unless explicitly persisted.

### Memory rules

- Data is scoped by user.
- Sensitive values are encrypted where appropriate.
- Deletion propagates to derived embeddings.
- Retrieval results include source IDs.
- Model-generated assumptions are never stored as confirmed facts.

## 14. Embeddings and Vector Search

Create an EmbeddingProvider interface with implementations for supported vendors.

Use embeddings for retrieval and semantic similarity, not as the sole basis for final decisions.

Recommended indexed objects:

- candidate achievements
- employment evidence
- skills
- job requirements
- job responsibilities
- company knowledge
- prior interview examples

Every vector record should store:

- tenant/user ID
- source object ID
- source type
- text hash
- model name
- embedding version
- created_at

Re-embedding must be controlled through explicit version migrations.

## 15. LLM Provider Abstraction

Define a common interface:

- generate_text
- generate_structured
- stream_text
- count_or_estimate_tokens
- health_check

Potential adapters:

- OpenAI
- Anthropic
- Google Gemini
- local or self-hosted models

Provider choice should be configuration-driven and support task-level routing. For example, extraction may use a cheaper model while complex application reasoning uses a stronger model.

The core application must not import vendor SDKs outside provider adapters.

## 16. Prompt Architecture

Prompts should be versioned files, not scattered string literals.

Suggested structure:

```text
backend/app/ai/prompts/
    candidate_extraction/
    job_extraction/
    matching/
    cv_tailoring/
    cover_letters/
    screening_answers/
    interviews/
```

Each prompt definition should include:

- name
- version
- purpose
- system instructions
- input schema
- output schema
- examples
- safety rules
- evaluation cases

Prompt changes should be auditable and tested before production rollout.

## 17. Structured Output and Validation

All high-value AI operations should return validated Pydantic schemas.

On validation failure:

1. Retry once with validation feedback.
2. Use a deterministic fallback when available.
3. Mark the task as requiring review if still invalid.
4. Never silently coerce sensitive or uncertain content.

## 18. Workflow Orchestration

Recommended workflow states:

- discovered
- parsed
- scored
- shortlisted
- materials_preparing
- materials_ready
- awaiting_review
- approved
- applying
- blocked
- submitted
- failed
- withdrawn
- rejected
- interview
- offer

The orchestrator should support:

- idempotency
- retries
- timeouts
- cancellation
- approval gates
- audit logging
- resumable workflows

Start with explicit application services and background jobs. Introduce a multi-agent orchestration framework only when complexity justifies it.

## 19. Safety, Privacy, and Governance

- Never log CV contents, passwords, tokens, or sensitive answers.
- Use secret management rather than committed API keys.
- Encrypt sensitive stored values.
- Apply least-privilege access.
- Maintain immutable audit records for application actions.
- Respect website terms and technical restrictions.
- Do not bypass CAPTCHA or anti-bot protections.
- Require human review for uncertain, legal, or sensitive answers.
- Allow users to inspect, correct, export, and delete their data.

## 20. Observability

Track:

- provider latency and failures
- token and cost usage
- structured-output validation failures
- prompt version
- retrieval sources
- workflow state transitions
- approval and submission events
- matching score distributions
- application outcomes

Metrics must not include raw personal data.

## 21. Evaluation

Create repeatable evaluation datasets for:

- CV extraction accuracy
- job requirement extraction
- match ranking quality
- hallucination rate
- factual consistency
- CV tailoring correctness
- screening-answer safety
- cover-letter relevance

Human review remains the reference standard for early versions.

## 22. Suggested Implementation Order

1. Provider interfaces and configuration
2. Candidate evidence schema
3. Deterministic CV text extraction
4. Structured candidate extraction
5. Job intelligence schema
6. Structured job extraction
7. Deterministic baseline matching
8. Semantic retrieval
9. Explainable hybrid scoring
10. CV and cover-letter agents
11. Approval workflow
12. Outcome analytics and evaluation

## 23. Non-Goals for the Initial AI Sprint

Do not yet implement:

- fully autonomous application submission
- multi-agent swarms
- automatic recruiter messaging
- self-training models
- unverifiable interview-probability percentages
- automated answers to sensitive declarations
- complex vector infrastructure before a validated retrieval need exists

## 24. Definition of Done

The AI architecture is ready for implementation when:

- interfaces and ownership boundaries are clear
- candidate and job evidence models are defined
- provider abstraction is vendor-neutral
- privacy and approval rules are explicit
- matching outputs are explainable
- prompt versioning and evaluation are specified
- the initial implementation sequence is agreed
