#!/usr/bin/env python3
"""Prepare and mechanically score a frozen exploratory AI evaluation audit. No model calls."""
import argparse
import collections
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VARIANTS = ("literal", "paraphrase", "corrupted", "no_passage")
PROTOCOLS = ("legacy", "entailment")
SEED = "reader-certification-v1-2026-10-25"
SOURCE_NAMES = {
    "source-aware-packet.json": "studies/reader-capacity-gate/evaluation/source-aware-packet.json",
    "historical-rubric.md": "studies/reader-capacity-gate/evaluation/rubric.md",
    "selection-controls-README.md": "studies/reader-selection-controls/README.md",
    "selection-controls-REVIEW.md": "studies/reader-selection-controls/REVIEW.md",
}
PROMPT = """Evaluate the 12 independent passage tasks below. Use only each task's passage.
Do not use tools, browse, read files, consult other agents, or use outside facts.
Do not assume that a question or claim supplies facts missing from its passage.
For question tasks, answer the query from the passage and decide:
answerable = the passage supports a definite answer to the question;
unanswerable = the passage does not supply enough information for a definite answer;
uncertain = you cannot resolve its answerability.
For claim tasks, decide:
supported = the passage entails the ENTIRE claim, including each participant, restriction,
quantity, location, condition, time and negation;
not_supported = any part of the claim is absent, contradicted or otherwise not established;
uncertain = you cannot resolve its entailment.
An empty passage supplies no facts. Evaluate each task independently.
Return ONLY one JSON array with exactly one object per case, using exactly these fields:
case_id: copy the ID;
decision: one of the three labels for that task;
answer: a concise answer or explanation, at most 80 whitespace-separated words;
evidence: a list of exact, contiguous, nonempty quotes from THIS passage, or [] if none;
rationale: at most 60 whitespace-separated words explaining the decision.
Do not quote the query as passage evidence. Do not add fields, Markdown or commentary.

TASKS:
"""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dump(value):
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON object key")
            result[key] = value
        return result
    def constant(value):
        raise ValueError("Nonfinite JSON constant: " + value)
    return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)


def read_json(path):
    return strict_json(Path(path).read_text(encoding="utf-8"))


def verify_sources(root=ROOT):
    identity = read_json(root / "source/GIT_IDENTITY.json")
    if identity["commit"] != "fb85a2ef6ea8d11bd0e5f6a82a15b78d8caeda21":
        raise ValueError("Unexpected source commit")
    expected = {r["path"]: r for r in identity["files"]}
    result = []
    for local, remote in SOURCE_NAMES.items():
        data = (root / "source" / local).read_bytes()
        blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        if blob != expected[remote]["sha"] or len(data) != expected[remote]["size"]:
            raise ValueError(f"Source Git identity mismatch: {local}")
        result.append({"local": "source/" + local, "remote": remote,
                       "git_blob_sha1": blob, "sha256": digest(data), "bytes": len(data)})
    return result


def build(root=ROOT):
    verify_sources(root)
    original = read_json(root / "source/source-aware-packet.json")
    sources = {}
    for row in original:
        sid = row["source_id"]
        if sid in sources and (sources[sid]["source"] != row["source"] or
                               sources[sid]["propositions"] != row["propositions"]):
            raise ValueError("Inconsistent duplicated source profiles")
        sources[sid] = row
    fixtures = read_json(root / "study/fixtures.json")
    if len(fixtures) != 12 or {f["source_id"] for f in fixtures} != set(sources):
        raise ValueError("Expected one fixture for each of 12 source scenarios")
    combos = [(v, p) for v in VARIANTS for p in PROTOCOLS]
    packets = [{"block_id": f"B{b+1:02}", "cases": []} for b in range(8)]
    key = []
    for index, fixture in enumerate(fixtures):
        source = sources[fixture["source_id"]]
        matches = [p for p in source["propositions"] if p["proposition_id"] == fixture["proposition_id"]]
        if len(matches) != 1:
            raise ValueError("Invalid proposition mapping")
        prop = matches[0]
        claim, text = prop["statement"], source["source"]
        if text.casefold().count(claim.casefold()) != 1:
            raise ValueError("Target fragment must occur exactly once under casefold")
        start = text.casefold().index(claim.casefold())
        end = start + len(claim)
        # All current stimuli are ASCII, so casefold does not change character offsets.
        if not text.isascii() or not claim.isascii():
            raise ValueError("Offset rule currently requires ASCII source and claim")
        for b, packet in enumerate(packets):
            variant, protocol = combos[(b + index) % 8]
            replacement = None
            if variant == "literal":
                passage = text
            elif variant == "no_passage":
                passage = ""
            else:
                replacement = fixture["paraphrase" if variant == "paraphrase" else "corruption"]
                if text[start].islower():
                    replacement = replacement[0].lower() + replacement[1:]
                passage = text[:start] + replacement + text[end:]
                if claim.casefold() in passage.casefold():
                    raise ValueError("Changed treatment must not retain full literal claim")
            cid = "C" + digest(f"{SEED}|{source['source_id']}|{variant}|{protocol}".encode())[:14]
            cell = {"case_id": cid, "passage": passage,
                    "task": "question" if protocol == "legacy" else "claim",
                    "query": prop["question"] if protocol == "legacy" else claim}
            packet["cases"].append(cell)
            key.append({"case_id": cid, "block_id": packet["block_id"],
                        "source_id": source["source_id"], "proposition_id": prop["proposition_id"],
                        "protocol": protocol, "variant": variant, "claim": claim,
                        "source_truth": variant in ("literal", "paraphrase"),
                        "passage": passage, "passage_sha256": digest(passage.encode()),
                        "original_source": text, "replacement_span": [start, end],
                        "replacement": replacement})
    for packet in packets:
        packet["cases"].sort(key=lambda c: digest(f"{SEED}|{packet['block_id']}|{c['case_id']}".encode()))
    if len({r["case_id"] for r in key}) != 96:
        raise ValueError("Case ID collision")
    return packets, sorted(key, key=lambda r: r["case_id"])


def prompt_for(packet):
    return PROMPT + dump(packet["cases"])


def positive(row, response):
    return response["decision"] == ("answerable" if row["protocol"] == "legacy" else "supported")


def validate_response(response, row):
    errors = []
    fields = {"case_id", "decision", "answer", "evidence", "rationale"}
    if not isinstance(response, dict):
        return ["response_not_object"]
    if set(response) != fields:
        errors.append("incorrect_fields")
    if response.get("case_id") != row["case_id"]:
        errors.append("incorrect_case_id")
    decisions = ({"answerable", "unanswerable", "uncertain"} if row["protocol"] == "legacy"
                 else {"supported", "not_supported", "uncertain"})
    if not isinstance(response.get("decision"), str) or response.get("decision") not in decisions:
        errors.append("invalid_decision")
    for name, cap in [("answer", 80), ("rationale", 60)]:
        value = response.get(name)
        if not isinstance(value, str) or not value.strip() or len(value.split()) > cap:
            errors.append("invalid_" + name)
    evidence = response.get("evidence")
    if not isinstance(evidence, list) or any(not isinstance(s, str) or not s for s in evidence):
        errors.append("invalid_evidence")
    elif any(s not in row["passage"] for s in evidence):
        errors.append("quote_not_in_passage")
    return errors


def baseline_predictions(key, name):
    if name == "always_positive":
        return {r["case_id"]: True for r in key}
    if name == "always_negative":
        return {r["case_id"]: False for r in key}
    if name == "claim_substring":
        return {r["case_id"]: r["claim"].casefold() in r["passage"].casefold()
                for r in key if r["protocol"] == "entailment"}
    raise ValueError("Unknown baseline")


def synthetic_responses(key, name):
    # Synthetic oracle is only a scorer fixture, never an observed answerer.
    predictions = ({r["case_id"]: r["source_truth"] for r in key} if name == "oracle"
                   else baseline_predictions(key, name))
    result = []
    for row in key:
        if row["case_id"] not in predictions:
            continue
        yes = predictions[row["case_id"]]
        decision = (("answerable" if yes else "unanswerable") if row["protocol"] == "legacy"
                    else ("supported" if yes else "not_supported"))
        result.append({"case_id": row["case_id"], "decision": decision,
                       "answer": "Synthetic harness fixture, not an AI answer.",
                       "evidence": [row["passage"]] if row["passage"] and yes else [],
                       "rationale": "Synthetic scoring check only."})
    return result


def score(packets, key, responses, admitted_blocks, execution_errors=()):
    expected = {r["case_id"]: r for r in key}
    global_errors = list(execution_errors)
    admitted = set(admitted_blocks)
    by_id = {}
    duplicates = set()
    if not isinstance(responses, list):
        responses = []
        global_errors.append("responses_not_list")
    for response in responses:
        cid = response.get("case_id") if isinstance(response, dict) else None
        if not isinstance(cid, str) or cid not in expected:
            global_errors.append("unexpected_or_malformed_case")
            continue
        if cid in by_id:
            duplicates.add(cid)
        else:
            by_id[cid] = response
    rows = []
    for cid, row in expected.items():
        response = by_id.get(cid)
        errors = (["missing"] if response is None else validate_response(response, row))
        if cid in duplicates:
            errors = errors + ["duplicate_case"]
        if row["block_id"] not in admitted:
            errors = errors + ["context_not_admitted"]
        valid = not errors
        rows.append({**{k: row[k] for k in ("case_id", "block_id", "source_id", "variant", "protocol")},
                     "valid": valid, "errors": errors,
                     "positive_certificate": positive(row, response) if valid else None,
                     "uncertain": response["decision"] == "uncertain" if valid else None,
                     "ungrounded_positive": positive(row,response) and not response["evidence"] if valid else None})
    expected_blocks = {p["block_id"] for p in packets}
    if admitted != expected_blocks:
        global_errors.append("context_admission_incomplete_or_unexpected")
    complete = all(r["valid"] for r in rows) and not global_errors
    cells = []
    for protocol in PROTOCOLS:
        for variant in VARIANTS:
            group = [r for r in rows if r["protocol"] == protocol and r["variant"] == variant]
            yes = sum(r["positive_certificate"] is True for r in group)
            missing = sum(not r["valid"] for r in group)
            cells.append({"protocol": protocol, "variant": variant, "denominator": 12,
                          "positive": yes, "valid": 12 - missing, "invalid_or_missing": missing,
                          "uncertain": sum(r["uncertain"] is True for r in group),
                          "ungrounded_positive": sum(r["ungrounded_positive"] is True for r in group),
                          "positive_rate_bounds": [yes/12, (yes+missing)/12]})
    pairs = []
    for sid in sorted({r["source_id"] for r in key}):
        group = {r["protocol"]: r for r in rows if r["source_id"] == sid and r["variant"] == "corrupted"}
        l, e = group["legacy"]["positive_certificate"], group["entailment"]["positive_certificate"]
        pairs.append({"source_id": sid, "legacy_positive": l, "entailment_positive": e,
                      "difference": int(l)-int(e) if l is not None and e is not None else None})
    difference = sum(p["difference"] for p in pairs)/12 if complete else None
    def count(protocol, variant):
        return next(c["positive"] for c in cells if c["protocol"] == protocol and c["variant"] == variant)
    supported = (difference >= .25 and count("entailment", "literal") >= 11 and
                 count("entailment", "paraphrase") >= 11 and count("entailment", "no_passage") <= 1) if complete else None
    return {"kind": "mechanical_certification_score_not_human_comprehension",
            "complete_valid_admitted": complete, "expected_count": 96,
            "valid_count": sum(r["valid"] for r in rows),
            "missing_count": sum("missing" in r["errors"] for r in rows),
            "invalid_count": sum(not r["valid"] and "missing" not in r["errors"] for r in rows),
            "global_errors": global_errors, "primary_difference": difference,
            "operational_hypothesis_supported": supported, "cells": cells,
            "source_pairs": pairs, "records": rows}


def freeze_paths(root, paths):
    return {"schema": "reader-audit-freeze-v1",
            "files": [{"path": p, "sha256": digest((root/p).read_bytes()), "bytes": (root/p).stat().st_size}
                      for p in sorted(paths)]}


def verify_freeze(root, frozen):
    errors = []
    if frozen.get("schema") != "reader-audit-freeze-v1":
        return ["invalid_freeze_schema"]
    paths = [r.get("path") for r in frozen.get("files", [])]
    if not paths or len(set(paths)) != len(paths):
        return ["empty_or_duplicate_freeze_paths"]
    for row in frozen["files"]:
        path = root / row["path"]
        if not path.is_file():
            errors.append("missing:" + row["path"])
        else:
            data = path.read_bytes()
            if digest(data) != row["sha256"] or len(data) != row["bytes"]:
                errors.append("changed:" + row["path"])
    return errors


def prepare(root):
    packets, key = build(root)
    out = root/"prepared"
    out.mkdir(exist_ok=True)
    for packet in packets:
        (out/(packet["block_id"]+".prompt.txt")).write_text(prompt_for(packet), encoding="utf-8")
    (out/"packets.json").write_text(dump(packets), encoding="utf-8")
    (out/"gold-key.json").write_text(dump(key), encoding="utf-8")
    (out/"source-verification.json").write_text(dump(verify_sources(root)))
    synthetic = {}
    admitted = [p["block_id"] for p in packets]
    for name in ("oracle", "always_positive", "always_negative"):
        result = score(packets,key,synthetic_responses(key,name),admitted)
        synthetic[name] = {k:v for k,v in result.items() if k != "records"}
    lexical = baseline_predictions(key,"claim_substring")
    synthetic["claim_substring"] = {"input_scope": "entailment only", "cells":
        [{"variant":v, "positive":sum(lexical[r["case_id"]] for r in key if r["protocol"]=="entailment" and r["variant"]==v), "denominator":12}
         for v in VARIANTS]}
    (out/"synthetic-checks.json").write_text(dump({"kind":"synthetic_harness_checks_not_answerer_results", "checks":synthetic}))
    paths = ["audit.py","PROTOCOL.md","PLAN.md","EXECUTE.md","study/fixtures.json","tests/test_audit.py"]
    paths += ["source/GIT_IDENTITY.json"]+["source/"+n for n in SOURCE_NAMES]
    paths += [str(p.relative_to(root)) for p in sorted(out.iterdir()) if p.is_file()]
    freeze = freeze_paths(root,paths)
    (root/"FREEZE.json").write_text(dump(freeze))
    return {"cases":len(key),"blocks":len(packets),"freeze_sha256":digest((root/"FREEZE.json").read_bytes()),
            "source_checks":len(verify_sources(root)),"data_executed":False}


def invocation_times(receipt):
    start = datetime.datetime.fromisoformat(receipt["started_utc"].replace("Z", "+00:00"))
    end = datetime.datetime.fromisoformat(receipt["completed_utc"].replace("Z", "+00:00"))
    if start.tzinfo is None or end.tzinfo is None or end < start:
        raise ValueError("Times require timezone and chronological order")
    return start, end


def check_receipt_collection(receipts, packets):
    errors = []
    expected = {p["block_id"] for p in packets}
    ids = []
    agents = []
    starts = []
    ends = []
    for receipt in receipts:
        if not isinstance(receipt, dict) or not isinstance(receipt.get("block_id"), str) or receipt["block_id"] not in expected:
            errors.append("unexpected_receipt")
            continue
        ids.append(receipt["block_id"])
        agent = receipt.get("agent_id")
        if not isinstance(agent, str) or not agent.strip():
            errors.append("missing_agent_identity")
        else:
            agents.append(agent)
        try:
            start, end = invocation_times(receipt)
            starts.append(start); ends.append(end)
        except (KeyError, AttributeError, TypeError, ValueError):
            errors.append("invalid_invocation_times")
    if len(ids) != 8 or set(ids) != expected:
        errors.append("receipt_count_or_coverage_mismatch")
    if len(set(ids)) != len(ids):
        errors.append("duplicate_receipt")
    if len(set(agents)) != len(agents):
        errors.append("reused_agent_context")
    if starts and ends and (max(ends)-min(starts)).total_seconds() > 3600:
        errors.append("wall_time_budget_exceeded")
    return sorted(set(errors))


def analyze_run(root, run_dir):
    errors = verify_freeze(root,read_json(root/"FREEZE.json"))
    if errors:
        raise ValueError("Freeze integrity failed: "+repr(errors))
    packets=read_json(root/"prepared/packets.json")
    key=read_json(root/"prepared/gold-key.json")
    receipts=read_json(run_dir/"receipts.json")
    if not isinstance(receipts,list):
        raise ValueError("Receipts must be an array")
    responses=[];admitted=[];custody=[]
    expected={p["block_id"]:p for p in packets}
    collection_errors = check_receipt_collection(receipts, packets)
    valid_starts = []
    for receipt in receipts:
        try:
            if isinstance(receipt,dict) and receipt.get("block_id") in expected:
                valid_starts.append(invocation_times(receipt)[0])
        except (KeyError, AttributeError, TypeError, ValueError):
            pass
    deadline = min(valid_starts)+datetime.timedelta(seconds=3600) if valid_starts else None
    seen=collections.Counter(r.get("block_id") for r in receipts if isinstance(r,dict) and isinstance(r.get("block_id"),str))
    agents=collections.Counter(r.get("agent_id") for r in receipts if isinstance(r,dict) and isinstance(r.get("agent_id"),str))
    for receipt in receipts:
        issues=[]
        if not isinstance(receipt,dict) or not isinstance(receipt.get("block_id"),str) or receipt.get("block_id") not in expected:
            custody.append({"issues":["unexpected_receipt"]});continue
        bid=receipt["block_id"]
        if seen[bid]!=1:issues.append("duplicate_receipt")
        if isinstance(receipt.get("agent_id"),str) and agents[receipt["agent_id"]]!=1:
            issues.append("reused_agent_context")
        prompt_sha=digest((root/"prepared"/(bid+".prompt.txt")).read_bytes())
        if receipt.get("prompt_sha256")!=prompt_sha:issues.append("prompt_identity_mismatch")
        if receipt.get("fork_turns")!="none" or receipt.get("reasoning_effort")!="xhigh":
            issues.append("configuration_mismatch")
        tool_audit = receipt.get("tool_audit")
        tool_calls = receipt.get("tool_calls_observed")
        if tool_audit not in ("full_trace", "self_report_only", "not_exposed"):
            issues.append("missing_tool_audit_scope")
        if tool_calls is not None and (type(tool_calls) is not int or tool_calls != 0):
            issues.append("tool_use_observed_or_bad_count")
        if tool_audit == "full_trace" and tool_calls is None:
            issues.append("full_trace_requires_observed_count")
        if tool_audit == "not_exposed" and tool_calls is not None:
            issues.append("unexposed_tool_trace_requires_null_count")
        if receipt.get("context_contamination_observed") is not False:
            issues.append("context_contamination_or_unknown")
        if not isinstance(receipt.get("model_identity"),dict) or receipt["model_identity"].get("requested") != "inherited":
            issues.append("missing_or_changed_model_configuration")
        if not isinstance(receipt.get("agent_id"),str) or not receipt["agent_id"].strip() or not receipt.get("started_utc") or not receipt.get("completed_utc"):
            issues.append("missing_invocation_identity_or_times")
        try:
            start, end = invocation_times(receipt)
            if deadline is not None and end > deadline:
                issues.append("context_completed_after_budget")
        except (KeyError, AttributeError, TypeError, ValueError):
            issues.append("invalid_invocation_times")
        raw_file=receipt.get("raw_file")
        if not isinstance(raw_file,str) or Path(raw_file).name!=raw_file:
            custody.append({"block_id":bid,"issues":issues+["invalid_raw_filename"]});continue
        raw_path=run_dir/raw_file
        if not raw_path.is_file():
            custody.append({"block_id":bid,"issues":issues+["missing_raw_response"]});continue
        raw=raw_path.read_bytes()
        if digest(raw)!=receipt.get("raw_sha256"):issues.append("raw_identity_mismatch")
        try:
            result=strict_json(raw)
            if not isinstance(result,list):raise ValueError("not list")
        except (ValueError,UnicodeDecodeError):
            result=[];issues.append("raw_response_not_json_array")
        ids=[r.get("case_id") for r in result if isinstance(r,dict) and isinstance(r.get("case_id"),str)]
        if len(result)!=12 or set(ids)!={c["case_id"] for c in expected[bid]["cases"]} or len(set(ids))!=12:
            issues.append("block_response_identity_mismatch")
        responses.extend(result)
        if not issues:admitted.append(bid)
        custody.append({"block_id":bid,"issues":issues,"receipt":receipt})
    output=score(packets,key,responses,admitted,execution_errors=collection_errors)
    output["custody"]=custody
    output["tool_isolation"] = "procedural_only_shared_tools_and_files_not_security_isolated"
    output["tool_trace_limitations"] = [r.get("block_id") for r in receipts if isinstance(r,dict) and r.get("tool_audit") != "full_trace"]
    output["freeze_sha256"]=digest((root/"FREEZE.json").read_bytes())
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("prepare","verify","analyze-run"))
    parser.add_argument("--run-dir",type=Path)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    if args.command=="prepare":
        result=prepare(ROOT)
    elif args.command=="verify":
        errors=verify_freeze(ROOT,read_json(ROOT/"FREEZE.json"))
        result={"verified":not errors,"errors":errors}
        if errors:raise ValueError(str(errors))
    else:
        if not args.run_dir or not args.output:parser.error("analyze-run requires --run-dir and --output")
        if args.output.exists():parser.error("Use a fresh output path; refusing to replace evidence")
        result=analyze_run(ROOT,args.run_dir)
    if args.output:
        args.output.write_text(dump(result))
    else:
        print(dump(result),end="")


if __name__=="__main__":
    main()

