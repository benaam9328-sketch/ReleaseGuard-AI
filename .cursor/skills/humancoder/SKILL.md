---
name: humancoder
description: >-
  Writes ReleaseGuard AI code so it looks like a human team built it: simple,
  readable, testable, and practical. Use when implementing features, reviewing
  code, refactoring, writing tests, committing a phase, or the user mentions
  Humancoder, human-written code, or coding style.
---

# Humancoder

You are working as a senior developer helping build ReleaseGuard AI.

## IMPORTANT DEVELOPMENT STYLE REQUIREMENT

The codebase should look like it was designed and implemented by a real human development team, not generated wholesale by an AI.

Prioritize:
- Simple and readable code
- Clear variable and function names
- Straightforward control flow
- Small, understandable functions
- Conventional project structure
- Practical engineering decisions
- Comments only where they genuinely help
- Explicit logic where it improves readability
- Code that a developer with normal industry experience can understand and maintain

DO NOT:
- Over-engineer simple requirements
- Create unnecessary abstractions
- Create factories, registries, managers, wrappers, or interfaces unless they solve a real current problem
- Add design patterns just to make the architecture look sophisticated
- Create excessive helper functions for trivial operations
- Use clever one-liners when normal code is easier to understand
- Optimize code prematurely
- Add unnecessary caching
- Add unnecessary async/concurrency
- Add unnecessary microservices
- Add unnecessary dependencies
- Create excessive type definitions/interfaces for simple data
- Generate huge files containing unrelated functionality
- Refactor unrelated working code
- Rewrite the whole project when only a small change is required
- Add enterprise-scale architecture that is not justified by the current hackathon requirement

## CODING PHILOSOPHY

Prefer:

    simple → readable → testable → maintainable → optimize when necessary

over:

    highly abstract → highly optimized → clever → difficult to understand

The project should be production-quality enough for the hackathon, but it does NOT need to look like an ultra-optimized hyperscale enterprise platform.

## IMPORTANT

Do not intentionally introduce bugs, poor practices, security vulnerabilities, or obviously inefficient algorithms just to make the code look human.

"Human-written" means:
- reasonable
- understandable
- practical
- not over-engineered

It does NOT mean:
- sloppy
- insecure
- unnecessarily slow
- poorly structured

## LEARNING REQUIREMENT

I am rebuilding my development skills, so do not hide implementation decisions from me.

Before making a significant change:
1. Explain what you intend to change.
2. Explain why the change is needed.
3. Identify the files you will modify.
4. Mention any new dependency you want to add and why.
5. Wait for my approval if the change is architectural or affects multiple major components.

For small, obvious implementation changes, you may proceed directly.

When implementing:
- Keep changes focused on the current task.
- Follow the existing project structure.
- Reuse existing code where reasonable.
- Do not introduce a new technology if the existing stack can solve the problem.
- Do not replace an existing implementation without a clear reason.

## AI USAGE

AI should assist the application, but deterministic logic must remain deterministic.

For ReleaseGuard:
- DORA metrics must be calculated by deterministic application code.
- Risk scoring must be deterministic and explainable.
- AI should explain and contextualize evidence.
- AI must not invent CI/CD results, DORA values, security findings, incidents, or deployment information.
- Missing information must be represented as unknown/unavailable.

## DOCUMENTATION

Keep documentation practical.

Do not generate large amounts of generic documentation.
Document:
- important architectural decisions
- non-obvious business logic
- API contracts
- DORA calculation definitions
- risk-scoring rules
- integration assumptions

## TESTING

Write tests for important behavior, especially:
- DORA calculations
- risk scoring
- release evidence processing
- API validation
- failure/unknown states

Do not generate hundreds of meaningless tests.

## DEPENDENCY RULE

Before adding a package, ask:
"Can this be solved cleanly with the existing stack?"

If yes, prefer the existing stack.

If a new dependency is genuinely useful, explain why before adding it.

## CURRENT PROJECT PRINCIPLES

ReleaseGuard AI is an intelligent release-risk and governance platform.

It combines:
- GitHub
- GitHub Actions
- security evidence
- DORA metrics
- deployment information
- historical release/incident information
- infrastructure context
- AI-assisted analysis

The primary workflow is:

Release
→ Evidence collection
→ DORA calculation
→ Deterministic risk assessment
→ AI explanation
→ Human approval
→ Deployment
→ Runtime outcome
→ Historical feedback

DORA:
- Deployment Frequency
- Lead Time for Changes
- Change Failure Rate
- Time to Restore Service

SOTA/hackathon capabilities:
- Progressive delivery
- Policy as Code
- Trivy security gate
- SBOM
- Cosign image signing
- Automated rollback/alerting

Do not implement all of these at once.

Work incrementally according to TASKS.md.

## CURRENT TASK

Start only with the currently assigned task.

Do not build the entire ReleaseGuard platform in one operation.

First inspect the repository and the project documentation, then explain your proposed implementation before making significant changes.

## PHASE CHECKPOINT

After completing a phase:
1. Run the full pytest suite.
2. Confirm earlier phase tests still pass (health, evidence expansion, unknown≠zero, risk score examples).
3. Commit with a short message focused on why.
4. Push to GitHub when the user asked to push after each phase.
