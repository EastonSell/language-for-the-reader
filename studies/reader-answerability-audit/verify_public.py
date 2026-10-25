#!/usr/bin/env python3
"""Read-only, standard-library verifier for this sanitized postrun derivative.

No model calls, network requests, regeneration of evidence, or private originals
are needed. A self-contained manifest/seal checks internal integrity, not an
independently authenticated timestamp. Supply a trusted manifest hash separately
when external authentication is required. Context aliases are not runtime IDs.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
import types

ROOT = Path(__file__).resolve().parent
VARIANTS = ("literal", "paraphrase", "corrupted", "no_passage")
PROTOCOLS = ("legacy", "entailment")
BLOCKS = tuple(f"B{i:02}" for i in range(1, 9))
SEED = "reader-certification-v1-2026-10-25"
COMMIT = "fb85a2ef6ea8d11bd0e5f6a82a15b78d8caeda21"
REFERENCE_SHA256 = "c28a52bbad734551ce40e9f853a4d6c63bc142165fb3dc190b76e04d6453d6f8"
FIXTURES_SHA256 = "0554e123a49af9c67dd3d77ba7d17927861d951faef7470d4d42e220c732e2bf"
FREEZE_SHA256 = "af05781b1aa922ea869cd08fd01055a661dce2785acb7f09f0cc7586413ceb33"
RECEIPTS_SOURCE_SHA256 = "321165916466ecd5269cf3bc0c121fc8d91ea712aeab26a2fffd7b5035e12549"
RECEIPTS_PROJECTION_SHA256 = "98c49ffb7426570bdf291640b5452c06e8a0cfbc145af5ca26b78bbcce355184"
ANALYSIS_SOURCE_SHA256 = "9de119bd812df565bbc792dc6ceb42de9e6120a586b95175dd4ca4f2000b78e1"
SELF_FILES = {"PUBLIC_MANIFEST.json", "PUBLIC_SEAL.json"}
SOURCE_FILES = {
    "source-aware-packet.json": ("studies/reader-capacity-gate/evaluation/source-aware-packet.json", "75b8a3b9cfe1094f72c8d6e15e6acd02219d46dc", 84145),
    "historical-rubric.md": ("studies/reader-capacity-gate/evaluation/rubric.md", "274f2762777ff2286442f84609bbaf5f004f31d8", 6944),
    "selection-controls-README.md": ("studies/reader-selection-controls/README.md", "b0e972e19a8d9339a07604beedc316c2583c0c63", 11007),
    "selection-controls-REVIEW.md": ("studies/reader-selection-controls/REVIEW.md", "215f6dd450902fa1ab80ce3ad1f27e8bd04028e0", 4225),
}
PUBLIC_RECEIPT_FIELDS = {"context_alias", "record_kind", "history_disabled", "dispatch_note"}
RETAINED_RECEIPT_FIELDS = {
    "block_id", "started_utc", "dispatch_returned_utc", "fork_turns", "reasoning_effort",
    "model_identity", "prompt_sha256", "completed_utc", "raw_file", "raw_sha256",
    "tool_audit", "tool_calls_observed", "context_contamination_observed", "raw_capture",
}


class VerificationError(ValueError):
    """A public integrity, schema, custody, or reproduction check failed."""


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def same(actual, expected, message):
    # Canonical JSON also distinguishes booleans from integers, unlike Python ==.
    require(canonical(actual) == canonical(expected), message)


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON object key: " + key)
            result[key] = value
        return result

    def invalid_constant(value):
        raise VerificationError("nonfinite JSON constant: " + value)

    def finite_float(value):
        parsed = float(value)
        require(math.isfinite(parsed), "nonfinite JSON number: " + value)
        return parsed

    try:
        return json.loads(data, object_pairs_hook=pairs, parse_constant=invalid_constant, parse_float=finite_float)
    except (ValueError, UnicodeError, TypeError) as error:
        raise VerificationError("invalid strict JSON: " + str(error)) from error


def read_json(path):
    try:
        return strict_json(path.read_bytes())
    except OSError as error:
        raise VerificationError(f"missing or unreadable file: {path.name}") from error


def is_hash(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def safe_path(value):
    require(isinstance(value, str) and value and "\\" not in value and ":" not in value
            and all(ord(character) >= 32 and ord(character) != 127 for character in value),
            "invalid manifest path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and all(p not in ("", ".", "..") for p in value.split("/"))
            and str(path) == value, "unsafe manifest path: " + value)
    require("__pycache__" not in path.parts, "manifest must not list Python cache paths")
    return value


def verify_manifest(root, expected_manifest_sha256=None):
    require(root.is_dir(), "package root is not a directory")
    # Sealed releases admit no symlinks or cache directories. Run tests with -B.
    all_paths = list(root.rglob("*"))
    require(not root.is_symlink() and not any(p.is_symlink() for p in all_paths), "package contains a symlink")
    require(not any("__pycache__" in p.relative_to(root).parts for p in all_paths),
            "sealed package contains a Python cache directory; use python -B")
    require(all(p.is_dir() or p.is_file() for p in all_paths), "package contains a nonregular filesystem entry")
    files = {p.relative_to(root).as_posix() for p in all_paths if p.is_file()}
    require(SELF_FILES <= files, "missing public manifest or seal")
    manifest_path = root / "PUBLIC_MANIFEST.json"
    manifest_hash = digest(manifest_path.read_bytes())
    manifest = read_json(manifest_path)
    require(isinstance(manifest, dict) and set(manifest) == {"kind", "files", "excluded_self_authentication_files"},
            "invalid public manifest schema")
    require(manifest["kind"] == "postrun_public_derivative_file_manifest", "invalid public manifest kind")
    exclusions = manifest["excluded_self_authentication_files"]
    require(isinstance(exclusions, list) and len(exclusions) == 2 and set(exclusions) == SELF_FILES,
            "manifest exclusions must be only the manifest and seal")
    rows = manifest["files"]
    require(isinstance(rows, list) and rows, "empty or malformed manifest files")
    listed = set()
    for row in rows:
        require(isinstance(row, dict) and set(row) == {"path", "bytes", "sha256"}, "invalid manifest file schema")
        name = safe_path(row["path"])
        require(name not in listed and name not in SELF_FILES, "duplicate or self-listed manifest path")
        listed.add(name)
        require(type(row["bytes"]) is int and row["bytes"] >= 0 and is_hash(row["sha256"]), "invalid manifest size or hash")
        require(name in files, "manifest file missing: " + name)
        data = (root / name).read_bytes()
        require(len(data) == row["bytes"] and digest(data) == row["sha256"], "manifest file digest mismatch: " + name)
    require(listed == files - SELF_FILES, "manifest exact file coverage mismatch")
    seal = read_json(root / "PUBLIC_SEAL.json")
    require(isinstance(seal, dict) and seal.get("kind") == "postrun_public_derivative_seal", "invalid public seal")
    require(seal.get("public_manifest_sha256") == manifest_hash, "public seal manifest hash mismatch")
    if expected_manifest_sha256 is not None:
        require(is_hash(expected_manifest_sha256) and expected_manifest_sha256 == manifest_hash,
                "trusted manifest hash does not match")
    inventory = "\n".join(sorted(files)) + "\n"
    require((root / "FILES.txt").read_bytes() == inventory.encode("utf-8"),
            "FILES.txt inventory does not exactly cover the public tree")
    return manifest_hash, len(listed)


def verify_source_custody(root):
    identity = read_json(root / "source/GIT_IDENTITY.json")
    require(isinstance(identity, dict) and identity.get("repository") == "EastonSell/language-for-the-reader"
            and identity.get("commit") == COMMIT, "unexpected source Git identity")
    files = identity.get("files")
    require(isinstance(files, list) and len(files) == 4, "source Git file coverage mismatch")
    require(all(isinstance(row, dict) and isinstance(row.get("path"), str) for row in files), "invalid source Git file schema")
    by_path = {row["path"]: row for row in files}
    require(len(by_path) == 4 and set(by_path) == {v[0] for v in SOURCE_FILES.values()}, "duplicate or unexpected source Git paths")
    verified = []
    for local, (remote, expected_blob, size) in SOURCE_FILES.items():
        row = by_path[remote]
        require(row.get("mode") == "100644" and row.get("type") == "blob" and row.get("sha") == expected_blob
                and type(row.get("size")) is int and row["size"] == size, "source Git metadata mismatch: " + local)
        expected_url = "https://api.github.com/repos/EastonSell/language-for-the-reader/git/blobs/" + expected_blob
        require(row.get("url") == expected_url, "source Git URL mismatch: " + local)
        data = (root / "source" / local).read_bytes()
        blob = hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()
        require(blob == expected_blob and len(data) == size, "source Git blob identity mismatch: " + local)
        verified.append({"local": "source/" + local, "remote": remote, "git_blob_sha1": blob,
                         "sha256": digest(data), "bytes": len(data)})
    same(read_json(root / "prepared/source-verification.json"), verified, "source verification projection mismatch")
    return verified


def load_reference(root):
    path = root / "reference/original_audit.py"
    data = path.read_bytes()
    require(digest(data) == REFERENCE_SHA256, "reference scorer hash mismatch; refusing to execute it")
    module = types.ModuleType("hash_verified_original_audit")
    module.__file__ = str(path)
    # Its main guard is false. Only read-only build/prompt/score functions are called.
    exec(compile(data, str(path), "exec"), module.__dict__)
    return module


def reconstruct_cases(root):
    """Independently rebuild the deterministic factorial from source and fixtures."""
    fixture_path = root / "study/fixtures.json"
    require(digest(fixture_path.read_bytes()) == FIXTURES_SHA256, "fixture freeze hash mismatch")
    originals = read_json(root / "source/source-aware-packet.json")
    require(isinstance(originals, list), "source packet must be an array")
    sources = {}
    for row in originals:
        require(isinstance(row, dict) and isinstance(row.get("source_id"), str), "invalid source profile")
        sid = row["source_id"]
        if sid in sources:
            same([row["source"], row["propositions"]], [sources[sid]["source"], sources[sid]["propositions"]],
                 "inconsistent duplicated source profiles")
        sources[sid] = row
    fixtures = read_json(fixture_path)
    require(isinstance(fixtures, list) and len(fixtures) == 12
            and {f["source_id"] for f in fixtures} == set(sources), "expected 12 distinct source fixtures")
    packets = [{"block_id": bid, "cases": []} for bid in BLOCKS]
    key = []
    combos = [(variant, protocol) for variant in VARIANTS for protocol in PROTOCOLS]
    for index, fixture in enumerate(fixtures):
        source = sources[fixture["source_id"]]
        props = [prop for prop in source["propositions"] if prop["proposition_id"] == fixture["proposition_id"]]
        require(len(props) == 1, "invalid fixture proposition mapping")
        prop = props[0]
        claim, original = prop["statement"], source["source"]
        require(original.isascii() and claim.isascii() and original.casefold().count(claim.casefold()) == 1,
                "invalid claim replacement span")
        start = original.casefold().index(claim.casefold())
        end = start + len(claim)
        for block_index, packet in enumerate(packets):
            variant, protocol = combos[(block_index + index) % 8]
            replacement = None
            if variant == "literal":
                passage = original
            elif variant == "no_passage":
                passage = ""
            else:
                replacement = fixture["paraphrase" if variant == "paraphrase" else "corruption"]
                if original[start].islower():
                    replacement = replacement[0].lower() + replacement[1:]
                passage = original[:start] + replacement + original[end:]
                require(claim.casefold() not in passage.casefold(), "changed treatment retained literal claim")
            cid = "C" + digest(f"{SEED}|{source['source_id']}|{variant}|{protocol}".encode())[:14]
            packet["cases"].append({"case_id": cid, "passage": passage,
                                    "task": "question" if protocol == "legacy" else "claim",
                                    "query": prop["question"] if protocol == "legacy" else claim})
            key.append({"case_id": cid, "block_id": packet["block_id"], "source_id": source["source_id"],
                        "proposition_id": prop["proposition_id"], "protocol": protocol, "variant": variant,
                        "claim": claim, "source_truth": variant in ("literal", "paraphrase"), "passage": passage,
                        "passage_sha256": digest(passage.encode()), "original_source": original,
                        "replacement_span": [start, end], "replacement": replacement})
    for packet in packets:
        packet["cases"].sort(key=lambda c: digest(f"{SEED}|{packet['block_id']}|{c['case_id']}".encode()))
    require(len(key) == 96 and len({r["case_id"] for r in key}) == 96, "expected 96 unique cases")
    require(all(len({r["source_id"] for r in key if r["block_id"] == b}) == 12 for b in BLOCKS), "incomplete block source coverage")
    require(all(len({(r["variant"], r["protocol"]) for r in key if r["source_id"] == s}) == 8 for s in sources),
            "incomplete source factorial coverage")
    return packets, sorted(key, key=lambda row: row["case_id"])


def verify_prepared(root, reference):
    packets, key = reconstruct_cases(root)
    same(read_json(root / "prepared/packets.json"), packets, "prepared packet reconstruction mismatch")
    same(read_json(root / "prepared/gold-key.json"), key, "prepared gold key reconstruction mismatch")
    same(reference.build(root), (packets, key), "independent and original case builders disagree")
    for packet in packets:
        expected = reference.prompt_for(packet).encode("utf-8")
        require((root / "prepared" / (packet["block_id"] + ".prompt.txt")).read_bytes() == expected,
                "frozen prompt reconstruction mismatch: " + packet["block_id"])
    return packets, key


def validate_payload(payload, packet, key):
    expected = {case["case_id"] for case in packet["cases"]}
    require(isinstance(payload, list) and len(payload) == 12, "raw payload must have exactly 12 cases")
    require(all(isinstance(row, dict) and set(row) == {"case_id", "decision", "answer", "evidence", "rationale"}
                for row in payload), "raw response strict schema mismatch")
    ids = [row["case_id"] for row in payload]
    require(all(isinstance(cid, str) for cid in ids) and len(set(ids)) == 12 and set(ids) == expected,
            "raw duplicate, missing, unexpected, or malformed case IDs")
    by_id = {row["case_id"]: row for row in key}
    quote_count = 0
    for response in payload:
        cid = response["case_id"]
        require(cid in by_id, "raw case ID not in key")
        row = by_id[cid]
        labels = {"answerable", "unanswerable", "uncertain"} if row["protocol"] == "legacy" else {"supported", "not_supported", "uncertain"}
        require(isinstance(response["decision"], str) and response["decision"] in labels, "invalid raw decision: " + cid)
        for field, cap in (("answer", 80), ("rationale", 60)):
            value = response[field]
            require(isinstance(value, str) and value.strip() and len(value.split()) <= cap, "invalid raw " + field + ": " + cid)
        evidence = response["evidence"]
        require(isinstance(evidence, list) and all(isinstance(q, str) and q for q in evidence), "invalid raw evidence: " + cid)
        require(all(quote in row["passage"] for quote in evidence), "evidence quote not in this case passage: " + cid)
        quote_count += len(evidence)
    return quote_count


def utc_time(value):
    require(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value), "receipt time must be explicit UTC")
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise VerificationError("invalid receipt time") from error


def verify_receipts(root, packets, key):
    wrapper = read_json(root / "run-001/receipts.public.json")
    require(isinstance(wrapper, dict) and set(wrapper) == {"kind", "source_sha256", "identity_policy", "receipts"}, "invalid public receipts schema")
    require(wrapper["kind"] == "sanitized_derivative_receipts_not_runtime_identities"
            and wrapper["source_sha256"] == RECEIPTS_SOURCE_SHA256, "receipt derivative source identity mismatch")
    require(isinstance(wrapper["identity_policy"], str) and wrapper["identity_policy"].strip(), "missing receipt identity policy")
    receipts = wrapper["receipts"]
    require(isinstance(receipts, list) and len(receipts) == 8, "receipt count mismatch")
    require(all(isinstance(r, dict) and set(r) == RETAINED_RECEIPT_FIELDS | PUBLIC_RECEIPT_FIELDS for r in receipts),
            "receipt strict schema mismatch or private identity field present")
    require([r["block_id"] for r in receipts] == list(BLOCKS), "receipt block coverage or order mismatch")
    require([r["context_alias"] for r in receipts] == [f"C{i:02}" for i in range(1, 9)], "receipt alias uniqueness or mapping mismatch")
    responses, times, quote_count = [], [], 0
    by_block = {p["block_id"]: p for p in packets}
    for receipt in receipts:
        bid = receipt["block_id"]
        require(receipt["record_kind"] == "sanitized_derivative", "receipt is not marked as derivative")
        require(receipt["history_disabled"] is True and receipt["fork_turns"] == "none"
                and receipt["reasoning_effort"] == "xhigh", "receipt history or configuration mismatch")
        require(isinstance(receipt["dispatch_note"], str) and receipt["dispatch_note"].strip(), "missing sanitized dispatch note")
        model = receipt["model_identity"]
        require(isinstance(model, dict) and set(model) == {"requested", "resolved", "source"}
                and model["requested"] == "inherited" and model["resolved"] is None
                and isinstance(model["source"], str) and model["source"].strip(), "receipt model identity mismatch")
        require(receipt["tool_audit"] == "not_exposed" and receipt["tool_calls_observed"] is None,
                "receipt tool trace scope mismatch; no full-trace claim is available")
        require(receipt["context_contamination_observed"] is False, "receipt contamination observation mismatch")
        require(isinstance(receipt["raw_capture"], str) and receipt["raw_capture"].strip(), "missing receipt raw capture limitation")
        start, dispatch, end = (utc_time(receipt[k]) for k in ("started_utc", "dispatch_returned_utc", "completed_utc"))
        require(start <= dispatch <= end, "receipt time ordering mismatch")
        times.append((start, end))
        require(receipt["raw_file"] == bid + ".raw.txt", "receipt raw filename mismatch")
        prompt = (root / "prepared" / (bid + ".prompt.txt")).read_bytes()
        raw = (root / "run-001" / receipt["raw_file"]).read_bytes()
        require(receipt["prompt_sha256"] == digest(prompt), "receipt prompt hash mismatch")
        require(receipt["raw_sha256"] == digest(raw), "receipt raw hash mismatch")
        payload = strict_json(raw)
        quote_count += validate_payload(payload, by_block[bid], key)
        responses.extend(payload)
    require((max(end for _, end in times) - min(start for start, _ in times)).total_seconds() <= 3600,
            "receipt wall-time budget exceeded")
    projection = [{k: v for k, v in r.items() if k in RETAINED_RECEIPT_FIELDS} for r in receipts]
    require(digest(canonical(projection)) == RECEIPTS_PROJECTION_SHA256, "retained receipt metadata differs from original projection")
    require(len(responses) == 96 and len({r["case_id"] for r in responses}) == 96, "raw global case coverage mismatch")
    require(quote_count == 75, "observed evidence quote count mismatch")
    return receipts, responses, quote_count


def score_valid(packets, key, responses):
    """Independent arithmetic for already validated, fully admitted inputs only.

    Invalid/incomplete input is rejected, never silently scored as observed data.
    The original scorer's invalid-input behavior remains in the pinned reference.
    """
    require(len(packets) == 8 and {p["block_id"] for p in packets} == set(BLOCKS), "score block coverage mismatch")
    require(len(key) == 96 and len({r["case_id"] for r in key}) == 96, "score key coverage mismatch")
    require(isinstance(responses, list) and len(responses) == 96, "score response count mismatch")
    for packet in packets:
        ids = {c["case_id"] for c in packet["cases"]}
        group = [r for r in responses if isinstance(r, dict) and r.get("case_id") in ids]
        validate_payload(group, packet, key)
    by_id = {r["case_id"]: r for r in responses}
    rows = []
    for item in key:
        response = by_id[item["case_id"]]
        positive = response["decision"] == ("answerable" if item["protocol"] == "legacy" else "supported")
        rows.append({**{k: item[k] for k in ("case_id", "block_id", "source_id", "variant", "protocol")},
                     "valid": True, "errors": [], "positive_certificate": positive,
                     "uncertain": response["decision"] == "uncertain", "ungrounded_positive": positive and not response["evidence"]})
    cells = []
    for protocol in PROTOCOLS:
        for variant in VARIANTS:
            group = [r for r in rows if r["protocol"] == protocol and r["variant"] == variant]
            require(len(group) == 12, "score cell denominator mismatch")
            positive = sum(r["positive_certificate"] for r in group)
            cells.append({"protocol": protocol, "variant": variant, "denominator": 12,
                          "positive": positive, "valid": 12, "invalid_or_missing": 0,
                          "uncertain": sum(r["uncertain"] for r in group),
                          "ungrounded_positive": sum(r["ungrounded_positive"] for r in group),
                          "positive_rate_bounds": [positive / 12, positive / 12]})
    pairs = []
    for source in sorted({r["source_id"] for r in key}):
        group = {r["protocol"]: r for r in rows if r["source_id"] == source and r["variant"] == "corrupted"}
        legacy = group["legacy"]["positive_certificate"]
        entailment = group["entailment"]["positive_certificate"]
        pairs.append({"source_id": source, "legacy_positive": legacy, "entailment_positive": entailment,
                      "difference": int(legacy) - int(entailment)})
    difference = sum(row["difference"] for row in pairs) / 12
    counts = {(c["protocol"], c["variant"]): c["positive"] for c in cells}
    supported = difference >= 0.25 and counts["entailment", "literal"] >= 11 and counts["entailment", "paraphrase"] >= 11 and counts["entailment", "no_passage"] <= 1
    return {"kind": "mechanical_certification_score_not_human_comprehension", "complete_valid_admitted": True,
            "expected_count": 96, "valid_count": 96, "missing_count": 0, "invalid_count": 0,
            "global_errors": [], "primary_difference": difference, "operational_hypothesis_supported": supported,
            "cells": cells, "source_pairs": pairs, "records": rows}


def verify_analysis(root, packets, key, receipts, responses, reference):
    score = score_valid(packets, key, responses)
    same(score, reference.score(packets, key, responses, list(BLOCKS)), "independent and original score disagree")
    expected = dict(score)
    expected.update(custody=[{"block_id": r["block_id"], "issues": [], "receipt": r} for r in receipts],
                    tool_isolation="procedural_only_shared_tools_and_files_not_security_isolated",
                    tool_trace_limitations=list(BLOCKS), freeze_sha256=FREEZE_SHA256,
                    derivative_kind="sanitized_public_analysis_projection", original_analysis_sha256=ANALYSIS_SOURCE_SHA256)
    same(read_json(root / "run-001/analysis.public.json"), expected, "retained public analysis or custody does not match recomputation")
    # Reproduce the retained synthetic harness file separately from observed data.
    synthetic = {}
    for name in ("oracle", "always_positive", "always_negative"):
        result = score_valid(packets, key, reference.synthetic_responses(key, name))
        same(result, reference.score(packets, key, reference.synthetic_responses(key, name), list(BLOCKS)), "synthetic score cross-check failed")
        synthetic[name] = {k: v for k, v in result.items() if k != "records"}
    lexical = {r["case_id"]: r["claim"].casefold() in r["passage"].casefold() for r in key if r["protocol"] == "entailment"}
    synthetic["claim_substring"] = {"input_scope": "entailment only", "cells": [
        {"variant": variant, "positive": sum(lexical[r["case_id"]] for r in key if r["protocol"] == "entailment" and r["variant"] == variant), "denominator": 12}
        for variant in VARIANTS]}
    same(read_json(root / "prepared/synthetic-checks.json"), {"kind": "synthetic_harness_checks_not_answerer_results", "checks": synthetic}, "retained synthetic harness check mismatch")
    return score



def verify_derivation(root):
    """Check declared transformations, without pretending omitted bytes are public."""
    document = read_json(root / "DERIVATION.json")
    require(isinstance(document, dict) and document.get("kind") == "postrun_public_derivative_provenance",
            "invalid derivation provenance schema")
    require(document.get("assembled_after_run") is True
            and document.get("hidden_instructions_included") is False
            and document.get("original_scientific_payloads_changed") is False,
            "derivation provenance scope mismatch")
    artifacts = document.get("artifacts")
    require(isinstance(artifacts, list) and len(artifacts) == 61, "derivation original artifact coverage mismatch")
    originals = {}
    retained_count = 0
    for row in artifacts:
        require(isinstance(row, dict), "invalid derivation artifact row")
        name = safe_path(row.get("original_path"))
        require(name not in originals, "duplicate derivation original path")
        originals[name] = row
        require(is_hash(row.get("original_sha256")) and type(row.get("original_bytes")) is int
                and row["original_bytes"] >= 0 and isinstance(row.get("transformation"), str)
                and row["transformation"].strip(), "invalid derivation artifact metadata")
        disposition = row.get("disposition")
        require(disposition in ("byte_identical", "transformed", "omitted"), "invalid derivation disposition")
        if disposition == "byte_identical":
            public = safe_path(row.get("public_path"))
            data = (root / public).read_bytes()
            require(row.get("public_sha256") == row["original_sha256"] == digest(data)
                    and row["original_bytes"] == len(data), "derivation byte-identity hash mismatch: " + public)
            retained_count += 1
        elif disposition == "transformed":
            paths = row.get("public_paths")
            require(isinstance(paths, list) and paths and all(isinstance(x, str) for x in paths)
                    and len(set(paths)) == len(paths), "invalid derivation transformed paths")
            for public in paths:
                require((root / safe_path(public)).is_file(), "derivation transformed output missing")
        else:
            require("public_path" not in row and "public_paths" not in row, "omitted derivation artifact has a public path")
    require(retained_count == 29, "derivation byte-identical artifact count mismatch")
    pins = {"FREEZE.json": FREEZE_SHA256, "audit.py": REFERENCE_SHA256,
            "run-001/receipts.json": RECEIPTS_SOURCE_SHA256, "run-001/analysis.json": ANALYSIS_SOURCE_SHA256}
    for name, expected in pins.items():
        require(name in originals and originals[name]["original_sha256"] == expected,
                "derivation pinned original hash mismatch: " + name)
    private = document.get("private_record_hashes")
    require(isinstance(private, dict) and set(private) == {"predata_freeze_sha256", "predata_review_receipt_sha256", "postrun_review_receipt_sha256"}
            and all(is_hash(v) for v in private.values()), "invalid private provenance hash declarations")
    require(private["predata_freeze_sha256"] == FREEZE_SHA256, "derivation omitted freeze hash mismatch")
    require(private["predata_review_receipt_sha256"] == "92ef410f961ecff2a2744edfb128f84367ba6c7b08f28d2c24d3dc7c07a0c98f"
            and private["postrun_review_receipt_sha256"] == "0ee42cfcd6b5c1f70e93871b57a9bf20bc8aceecd5d2754248513de6d16b5d74",
            "derivation private review provenance hash mismatch")
    aliases = document.get("identity_aliases")
    require(isinstance(aliases, list) and len(aliases) == 8
            and all(isinstance(row, dict) for row in aliases), "invalid derivation alias map")
    same([(row.get("block_id"), row.get("public_context_alias")) for row in aliases],
         [(bid, "C" + bid[1:]) for bid in BLOCKS], "derivation alias mapping mismatch")
    for path in document.get("new_public_artifacts", []):
        require((root / safe_path(path)).is_file(), "derivation new public artifact missing")
    return len(artifacts), retained_count


def verify(root=ROOT, expected_manifest_sha256=None):
    root = Path(root)
    try:
        manifest_hash, file_count = verify_manifest(root, expected_manifest_sha256)
        sources = verify_source_custody(root)
        reference = load_reference(root)
        packets, key = verify_prepared(root, reference)
        receipts, responses, quotes = verify_receipts(root, packets, key)
        score = verify_analysis(root, packets, key, receipts, responses, reference)
        original_artifacts, byte_identical_artifacts = verify_derivation(root)
    except VerificationError:
        raise
    except (OSError, KeyError, TypeError, ValueError, AttributeError, IndexError) as error:
        raise VerificationError("malformed or missing public artifact: " + str(error)) from error
    observed_window = int((max(utc_time(r["completed_utc"]) for r in receipts)
                           - min(utc_time(r["started_utc"]) for r in receipts)).total_seconds())
    counts = {(cell["protocol"], cell["variant"]): cell["positive"] for cell in score["cells"]}
    return {"verified": True, "kind": "postrun_public_derivative_verification",
            "manifest_files": file_count, "public_manifest_sha256": manifest_hash,
            "trusted_manifest_pin_checked": expected_manifest_sha256 is not None,
            "source_git_blobs": len(sources), "cases": len(key), "blocks": len(packets),
            "original_artifacts_mapped": original_artifacts, "byte_identical_artifacts": byte_identical_artifacts,
            "exact_evidence_quotes": quotes, "primary_difference": score["primary_difference"],
            "observed_window_seconds": observed_window,
            "primary_counts": {"legacy_corrupted_positive": counts["legacy", "corrupted"],
                               "entailment_corrupted_positive": counts["entailment", "corrupted"], "paired_sources": 12},
            "gate_counts": {"entailment_literal_positive": counts["entailment", "literal"],
                            "entailment_paraphrase_positive": counts["entailment", "paraphrase"],
                            "entailment_no_passage_positive": counts["entailment", "no_passage"]},
            "operational_hypothesis_supported": score["operational_hypothesis_supported"],
            "runtime_identity_verification": "not_possible_from_sanitized_aliases",
            "tool_trace_verification": "not_exposed_procedural_observations_only",
            "authentication_scope": "postrun_internal_integrity_not_independent_timestamp_or_runtime_attestation"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="public study directory")
    parser.add_argument("--expected-manifest-sha256", help="optional independently trusted public manifest SHA-256")
    args = parser.parse_args()
    try:
        result = verify(args.root, args.expected_manifest_sha256)
    except VerificationError as error:
        print(json.dumps({"verified": False, "error": str(error)}, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
