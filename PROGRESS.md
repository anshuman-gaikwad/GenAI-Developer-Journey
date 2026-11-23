# GrahakNyay — Final Project Progress

## Day 14: Interview Preparation and Final Release

**Branch:** `feat/day14-final-release`

**Goal:** Prepare interview documentation, verify legal-rule versioning, close remaining project tasks, rehearse the application twice, and create a final release tag.

## Completed Milestones

- [x] Day 12 — Deploy FastAPI backend on Render.
- [x] Day 12 — Deploy Streamlit frontend.
- [x] Day 12 — Configure GitHub Actions CI.
- [x] Day 13 S1 — Add API and LLM latency logging.
- [x] Day 13 S1 — Add token usage logging and response caching.
- [x] Day 13 S1 — Add input validation and prompt-injection precautions.
- [x] Day 13 S1 — Verify 37 automated tests.
- [x] Day 13 S2 — Add portfolio README and architecture diagram.
- [x] Day 13 S2 — Create `docs/resume.md`.
- [x] Day 13 S2 — Merge changes into `main`.
- [x] Day 14 — Add jurisdiction boundary tests.
- [x] Day 14 — Verify 41 automated tests.

## Day 14 Checklist

- [x] Review the implementation of Consumer Commission jurisdiction and filing-fee rules.
- [x] Verify the calculator's jurisdiction, filing-fee, and limitation references against official government publications.
- [x] Verify the 2022 and 2023 filing-fee amendments and retain the later 2023 citation.
- [x] Create `docs/interview.md` with a 60-second pitch.
- [x] Write answers to 10 likely interview questions.
- [x] Document the hardest technical problem: versioned legal rules.
- [x] Add automated jurisdiction boundary tests.
- [x] Run Ruff and the complete pytest suite (41 tests passed).
- [x] Rehearse the GrahakNyay demo — first run.
- [x] Rehearse the GrahakNyay demo — second run.
- [x] Commit Day 14 changes and merge the pull request.
- [x] Create and push the final Git release tag.

## Future Enhancement

Record and upload an optional demonstration video when available.

This is a future portfolio enhancement, not a blocker for the Day 14 release.

## Release Notes

**Release status:** Released — v1.0.0 (GitHub Release published).

**Important:** GrahakNyay provides general consumer-rights information and is not professional legal advice. Legal thresholds and filing fees must be checked against applicable official rules and amendments.

**Current test status:** 41 tests passed. Ruff checks passed.

**Known limitation:** Legal rules are coded into the calculator and are not updated automatically when new notifications are issued.

**Live demo finding:** The frontend correctly cites G.S.R. 606(E), 2023. The backend and interview documentation have been aligned with that notification.

## Legal Reference Verification — 24 November 2026

The calculator's three main legal references were reviewed against official Government of India publications.

1. **Jurisdiction:** G.S.R. 912(E), dated 30 December 2021. District Commission up to ₹50 lakh; State Commission above ₹50 lakh and up to ₹2 crore; National Commission above ₹2 crore.

   Official source: https://egazette.gov.in/WriteReadData/2021/232278.pdf

2. **Filing fees:** G.S.R. 606(E), dated 17 August 2023, substituting the table in Rule 7(2). The eleven fee brackets in `app/tools.py` match the published schedule.

   Official source: https://egazette.gov.in/WriteReadData/2023/248158.pdf

3. **Limitation:** Section 69 of the Consumer Protection Act, 2019. The general filing period is two years from the cause of action, with provision for condonation of delay for sufficient cause. The calculator provides an indicative date, not a definitive legal assessment.

   Official source: https://www.indiacode.nic.in/bitstream/123456789/15256/5/A2019-35.pdf

**Scope:** This review covers the calculator's cited rules and the referenced published provisions. It is not a comprehensive audit of all consumer-law amendments or individual-case exceptions. Future notifications must be checked before relying on these calculations for real legal matters.
