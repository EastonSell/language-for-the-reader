# Execution checklist, not clearance

No dispatch is authorized by this file. Independent semantic and technical reviews plus study-lead admission of the exact freeze are prerequisites.

1. Run admission.py --verify and record the SHA-256 of FREEZE.json. Read the independent review decisions. A preparation-consistent result is not execution admission.
2. Create one fresh output directory OUTSIDE this frozen package, using exclusive creation. Retain all failed/partial outputs.
3. Dispatch B01 through B12 in order as capacity permits, one distinct fresh AI context each. Supply exactly the corresponding prompt text, no extra instruction or context. Use no inherited history, xhigh reasoning, inherited model. Do not reuse an evaluator or send a follow-up. No more than twelve scientific invocations. Do not dispatch after the 45-minute window expires.
4. Save Bxx.raw.txt as the visible final-answer payload encoded UTF-8, without added newline, trimming, Markdown removal or JSON repair. If final payload is unavailable, retain the actual failure evidence separately and leave the raw file missing. Capture invocation receipts and timestamps as they occur; do not fabricate times or identities after the fact.
5. receipts.json must be a list of twelve objects with these exact fields. Substitute actual observations, never the illustrative placeholders:

    block_id: B01
    context_id: distinct context pseudonym in this public derivative
    prompt_sha256: SHA-256 of the exact prompt UTF-8 bytes
    raw_sha256: SHA-256 of the exact saved visible payload bytes
    started_utc: coordinator-observed dispatch start, explicit UTC timestamp
    completed_utc: coordinator-observed final capture, explicit UTC timestamp
    history_disabled: true
    requested_reasoning_effort: xhigh
    requested_model: inherited
    resolved_model: null when unavailable, otherwise the observed identity string
    tool_audit: not_exposed
    tool_calls_observed: null
    known_tool_use: false only if no known use was observed
    known_contamination: false only if no contamination is known
    capture: visible_final_answer_utf8_no_added_newline

The present receipt schema deliberately records unavailable tool traces as unknown. If the runtime exposes a materially different telemetry contract, stop for review rather than silently relabel it. Report any actual tool use or contamination truthfully; it prevents operational admission. Failed/missing final payloads cannot satisfy this successful-receipt schema. Preserve their failure record and report the run incomplete instead of inventing the required fields.

6. Analyze read-only: python -B admission.py --analyze-run /absolute/path/to/output. Save its stdout to a new report OUTSIDE the frozen package. Verify raw bytes before and after. The analyzer retains all expected 144 cells. Invalid custody invalidates the run; malformed scientific JSON invalidates its packet. No repair, retry or replacement is permitted.
7. Independent postrun review checks semantic judgments, source/prompt/raw hashes, all timestamps/context identities, complete denominators and the frozen primary contrast. Producer completeness alone is not scientific acceptance.
8. Deliver limitations and all failures with any result. Publication is a separate reviewed action. Preserve the historical package unchanged.
