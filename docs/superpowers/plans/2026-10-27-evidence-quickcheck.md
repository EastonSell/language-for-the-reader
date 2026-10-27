# Saved-evidence quickcheck Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** One reliable offline command for the retained reader evidence.
**Architecture:** A new stdlib runner calls unchanged verifiers and tests in subprocesses, parses structured verdicts, and aggregates all failures.
**Tech Stack:** Python 3.10+ standard library.
**Spec:** ../specs/2026-10-27-evidence-quickcheck-design.md

## Global Constraints
No installations, models, evaluator calls, external publication, historical changes or gate reopening.

## Review Focus
- Incomplete cue JSON despite exit zero must fail.
- Missing stage must not suppress other diagnostics.
- Timeout must fail without losing earlier results.
- Invocation outside root and Python environment contamination.
- Byte-for-byte preservation of retained study files.

## Task 1: Runner and documentation
Files: create tooling/check_saved_evidence.py, tooling/tests/test_saved_evidence.py, tooling/SAVED_EVIDENCE.md; modify README.md only to link the command and finite-profile result.
Interface: main(argv=None) -> exit code; run_checks(root, timeout) -> JSON-serializable report.
- [ ] Write failing CLI/unit tests for all statuses, JSON, finite timeout, cwd, environment, structured predicates.
- [ ] Run tests RED (runner absent).
- [ ] Implement minimal fixed-stage subprocess runner and documentation.
- [ ] Run tests GREEN and full default aggregate, and real quickcheck with site packages disabled; compare before/after evidence hashes.
- [ ] Independent review, address important findings via RED/GREEN, hand off unpublished patch.
