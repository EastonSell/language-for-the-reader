"""Verifier tests. Every altered input is a temporary synthetic test mutation, not data."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
try:
    spec = importlib.util.spec_from_file_location("public_verifier", ROOT / "verify_public.py")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
except FileNotFoundError:
    verifier = None


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.write_bytes(encoded(value))


def reseal(root):
    """Only synthetic temporary copies are resealed; no evidence is repaired."""
    manifest = read(root / "PUBLIC_MANIFEST.json")
    manifest["files"] = [
        {"path": str(path.relative_to(root)), "bytes": len(path.read_bytes()),
         "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
        and path.name not in ("PUBLIC_MANIFEST.json", "PUBLIC_SEAL.json")
    ]
    write(root / "PUBLIC_MANIFEST.json", manifest)
    seal = read(root / "PUBLIC_SEAL.json")
    seal["public_manifest_sha256"] = hashlib.sha256((root / "PUBLIC_MANIFEST.json").read_bytes()).hexdigest()
    write(root / "PUBLIC_SEAL.json", seal)


class PublicVerifierTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(verifier, "public verifier implementation is missing")
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic-verifier-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "package"
        shutil.copytree(ROOT, self.root)

    def reject(self, pattern):
        with self.assertRaisesRegex(verifier.VerificationError, pattern):
            verifier.verify(self.root)

    def change_json(self, name, change, seal=True):
        path = self.root / name
        value = read(path)
        change(value)
        write(path, value)
        if seal:
            reseal(self.root)

    def test_reproduces_all_observed_counts_and_arithmetic(self):
        result = verifier.verify(self.root)
        self.assertTrue(result["verified"])
        self.assertEqual(result["cases"], 96)
        self.assertEqual(result["blocks"], 8)
        self.assertEqual(result["exact_evidence_quotes"], 75)
        self.assertEqual(result["primary_difference"], 11 / 12)
        self.assertEqual(result["observed_window_seconds"], 297)
        self.assertEqual(result["primary_counts"], {"legacy_corrupted_positive": 11, "entailment_corrupted_positive": 0, "paired_sources": 12})
        self.assertEqual(result["gate_counts"], {"entailment_literal_positive": 12, "entailment_paraphrase_positive": 12, "entailment_no_passage_positive": 0})
        self.assertIs(result["operational_hypothesis_supported"], True)
        self.assertEqual(result["runtime_identity_verification"], "not_possible_from_sanitized_aliases")

    def test_cli_succeeds_without_private_files(self):
        run = subprocess.run([sys.executable, "-B", str(self.root / "verify_public.py")],
                             capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(json.loads(run.stdout)["verified"])

    def test_manifest_rejects_changed_unlisted_and_missing_files(self):
        for action in ("changed", "unlisted", "missing"):
            with self.subTest(action=action):
                target = self.root / "prepared/B01.prompt.txt"
                before = target.read_bytes()
                if action == "changed":
                    target.write_bytes(before + b"synthetic mutation")
                elif action == "unlisted":
                    (self.root / "synthetic-extra.txt").write_text("synthetic test input")
                else:
                    target.unlink()
                self.reject("manifest")
                target.write_bytes(before)
                (self.root / "synthetic-extra.txt").unlink(missing_ok=True)

    def test_manifest_rejects_duplicate_entries_and_unsafe_paths(self):
        original = read(self.root / "PUBLIC_MANIFEST.json")
        for bad in ("duplicate", "../escape", "/absolute", "a/../b", "a\\b"):
            with self.subTest(path=bad):
                altered = copy.deepcopy(original)
                if bad == "duplicate":
                    altered["files"].append(altered["files"][0])
                else:
                    altered["files"][0]["path"] = bad
                write(self.root / "PUBLIC_MANIFEST.json", altered)
                seal = read(self.root / "PUBLIC_SEAL.json")
                seal["public_manifest_sha256"] = hashlib.sha256((self.root / "PUBLIC_MANIFEST.json").read_bytes()).hexdigest()
                write(self.root / "PUBLIC_SEAL.json", seal)
                self.reject("manifest|path")

    def test_portable_paths_reject_drive_prefixes_and_control_characters(self):
        for path in ("C:/synthetic-file", "synthetic\nfile", "synthetic\tfile"):
            with self.subTest(path=path), self.assertRaisesRegex(verifier.VerificationError, "path"):
                verifier.safe_path(path)

    def test_seal_and_external_manifest_pin(self):
        digest = hashlib.sha256((self.root / "PUBLIC_MANIFEST.json").read_bytes()).hexdigest()
        self.assertTrue(verifier.verify(self.root, expected_manifest_sha256=digest)["verified"])
        with self.assertRaisesRegex(verifier.VerificationError, "trusted manifest"):
            verifier.verify(self.root, expected_manifest_sha256="0" * 64)
        self.change_json("PUBLIC_SEAL.json", lambda value: value.update(public_manifest_sha256="0" * 64), seal=False)
        self.reject("seal")

    def test_files_inventory_exactly_covers_public_tree(self):
        inventory = self.root / "FILES.txt"
        inventory.write_text(inventory.read_text() + "synthetic-not-present.txt\n")
        reseal(self.root)
        with self.assertRaisesRegex(verifier.VerificationError, "inventory|FILES"):
            verifier.verify_manifest(self.root)

    def test_cache_directory_cannot_hide_extra_files(self):
        cache = self.root / "__pycache__"
        cache.mkdir(exist_ok=True)
        (cache / "synthetic-extra.txt").write_text("Synthetic test content, not evidence")
        reseal(self.root)
        with self.assertRaisesRegex(verifier.VerificationError, "cache"):
            verifier.verify_manifest(self.root)

    def test_symlinks_rejected_even_inside_cache(self):
        cache = self.root / "__pycache__"
        cache.mkdir(exist_ok=True)
        (cache / "synthetic-link").symlink_to(self.root / "prepared/packets.json")
        self.reject("symlink")

    def test_source_bytes_and_git_blob_identity_checked_after_reseal(self):
        target = self.root / "source/source-aware-packet.json"
        target.write_bytes(target.read_bytes() + b"\n")
        reseal(self.root)
        self.reject("source|Git|freeze")

    def test_duplicate_or_missing_packet_ids_rejected_after_reseal(self):
        original = read(self.root / "prepared/packets.json")
        for mode in ("duplicate", "missing"):
            altered = copy.deepcopy(original)
            if mode == "duplicate":
                altered[0]["cases"][1] = altered[0]["cases"][0]
            else:
                altered[0]["cases"].pop()
            write(self.root / "prepared/packets.json", altered)
            reseal(self.root)
            self.reject("packet|freeze")

    def test_prompt_key_and_fixture_consistency_rejected_after_reseal(self):
        target = self.root / "prepared/B01.prompt.txt"
        target.write_bytes(target.read_bytes().replace(b"Use only", b"Use also", 1))
        reseal(self.root)
        self.reject("prompt|freeze")

    def test_gold_key_mutation_rejected(self):
        self.change_json("prepared/gold-key.json", lambda value: value[0].update(source_truth=not value[0]["source_truth"]))
        self.reject("key|freeze")

    def test_raw_schema_duplicate_and_missing_cases_rejected(self):
        packet = read(self.root / "prepared/packets.json")[0]
        key = read(self.root / "prepared/gold-key.json")
        raw = read(self.root / "run-001/B01.raw.txt")
        for mode in ("duplicate", "missing", "extra_field", "wrong_label", "wrong_type"):
            altered = copy.deepcopy(raw)
            if mode == "duplicate":
                altered[1] = altered[0]
            elif mode == "missing":
                altered.pop()
            elif mode == "extra_field":
                altered[0]["synthetic_extra"] = True
            elif mode == "wrong_label":
                altered[0]["decision"] = "yes"
            else:
                altered[0]["answer"] = 12
            with self.subTest(mode=mode), self.assertRaises(verifier.VerificationError):
                verifier.validate_payload(altered, packet, key)

    def test_exact_quotes_not_query_or_other_passage(self):
        packet = read(self.root / "prepared/packets.json")[0]
        key = read(self.root / "prepared/gold-key.json")
        raw = read(self.root / "run-001/B01.raw.txt")
        for quote in ("SYNTHETIC QUOTE NOT IN ANY PASSAGE", "", 9):
            altered = copy.deepcopy(raw)
            altered[0]["evidence"] = [quote]
            with self.subTest(quote=quote), self.assertRaisesRegex(verifier.VerificationError, "evidence|quote"):
                verifier.validate_payload(altered, packet, key)

    def test_word_limits_and_empty_text_enforced(self):
        packet = read(self.root / "prepared/packets.json")[0]
        key = read(self.root / "prepared/gold-key.json")
        raw = read(self.root / "run-001/B01.raw.txt")
        for field, value in (("answer", "word " * 81), ("rationale", "word " * 61), ("answer", " ")):
            altered = copy.deepcopy(raw)
            altered[0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(verifier.VerificationError, field):
                verifier.validate_payload(altered, packet, key)

    def test_strict_json_rejects_duplicates_nonfinite_and_trailing_text(self):
        for raw in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', '{"a":1e999}', '[] trailing'):
            with self.subTest(raw=raw), self.assertRaises(verifier.VerificationError):
                verifier.strict_json(raw)

    def test_receipts_reject_private_or_duplicate_context_identity(self):
        original = read(self.root / "run-001/receipts.public.json")
        for mode in ("private", "duplicate", "missing", "wrong_alias"):
            altered = copy.deepcopy(original)
            if mode == "private":
                altered["receipts"][0]["agent_id"] = "synthetic-private-identity"
            elif mode == "duplicate":
                altered["receipts"][1]["context_alias"] = altered["receipts"][0]["context_alias"]
            elif mode == "missing":
                altered["receipts"].pop()
            else:
                altered["receipts"][0]["context_alias"] = "context-with-runtime-name"
            write(self.root / "run-001/receipts.public.json", altered)
            reseal(self.root)
            with self.subTest(mode=mode):
                self.reject("receipt|alias|identity")

    def test_receipts_reject_wrong_hash_history_or_tool_scope(self):
        original = read(self.root / "run-001/receipts.public.json")
        for field, value in (("raw_sha256", "0" * 64), ("prompt_sha256", "0" * 64),
                             ("history_disabled", False), ("fork_turns", "all"),
                             ("tool_calls_observed", 0), ("context_contamination_observed", True)):
            altered = copy.deepcopy(original)
            altered["receipts"][0][field] = value
            write(self.root / "run-001/receipts.public.json", altered)
            reseal(self.root)
            with self.subTest(field=field):
                self.reject("receipt|hash|history|configuration|tool|contamination")

    def test_receipt_times_require_utc_order_budget_and_unchanged_metadata(self):
        original = read(self.root / "run-001/receipts.public.json")
        cases = (("started_utc", "2026-10-25T05:23:14"),
                 ("completed_utc", "2026-10-25T05:20:00Z"),
                 ("dispatch_returned_utc", "2026-10-25T06:24:00Z"),
                 ("completed_utc", "2026-10-25T07:24:00Z"),
                 ("started_utc", "2026-10-25T05:23:15Z"))
        for field, value in cases:
            altered = copy.deepcopy(original)
            altered["receipts"][0][field] = value
            write(self.root / "run-001/receipts.public.json", altered)
            reseal(self.root)
            with self.subTest(field=field, value=value):
                self.reject("time|budget|metadata|UTC")

    def test_analysis_arithmetic_and_custody_tampering_rejected(self):
        original = read(self.root / "run-001/analysis.public.json")
        for mode in ("difference", "cell", "custody", "gate"):
            altered = copy.deepcopy(original)
            if mode == "difference":
                altered["primary_difference"] = 1.0
            elif mode == "cell":
                altered["cells"][0]["positive"] = 11
            elif mode == "custody":
                altered["custody"][0]["issues"] = ["synthetic"]
            else:
                altered["operational_hypothesis_supported"] = False
            write(self.root / "run-001/analysis.public.json", altered)
            reseal(self.root)
            with self.subTest(mode=mode):
                self.reject("analysis|custody|score")

    def test_provenance_byte_identity_and_omitted_freeze_hash_checked(self):
        original = read(self.root / "DERIVATION.json")
        for mode in ("retained_hash", "freeze_hash", "duplicate_original"):
            altered = copy.deepcopy(original)
            if mode == "retained_hash":
                row = next(r for r in altered["artifacts"] if r["disposition"] == "byte_identical")
                row["original_sha256"] = "0" * 64
            elif mode == "freeze_hash":
                altered["private_record_hashes"]["predata_freeze_sha256"] = "0" * 64
            else:
                altered["artifacts"].append(copy.deepcopy(altered["artifacts"][0]))
            write(self.root / "DERIVATION.json", altered)
            reseal(self.root)
            with self.subTest(mode=mode):
                self.reject("provenance|derivation|freeze")

    def test_reference_code_is_hash_pinned_before_import(self):
        target = self.root / "reference/original_audit.py"
        target.write_bytes(target.read_bytes() + b"\nraise RuntimeError('synthetic mutation')\n")
        reseal(self.root)
        self.reject("reference|freeze")

    def test_synthetic_score_gates_and_reference_agree(self):
        reference = verifier.load_reference(self.root)
        packets, key = reference.build(self.root)
        blocks = [packet["block_id"] for packet in packets]
        for mode in ("oracle", "always_positive", "always_negative", "passing", "boundary_passing", "literal_gate", "paraphrase_gate", "empty_gate", "difference_gate"):
            responses = reference.synthetic_responses(key, mode if mode in ("oracle", "always_positive", "always_negative") else "oracle")
            by_id = {response["case_id"]: response for response in responses}
            if mode not in ("oracle", "always_positive", "always_negative"):
                for row in key:
                    if row["protocol"] == "legacy" and row["variant"] == "corrupted":
                        by_id[row["case_id"]]["decision"] = "answerable"
                if mode in ("literal_gate", "paraphrase_gate", "empty_gate", "difference_gate"):
                    variant = {"literal_gate": "literal", "paraphrase_gate": "paraphrase", "empty_gate": "no_passage", "difference_gate": "corrupted"}[mode]
                    group = [row for row in key if row["protocol"] == "entailment" and row["variant"] == variant]
                    for row in group[:(10 if mode == "difference_gate" else 2)]:
                        by_id[row["case_id"]]["decision"] = "supported" if mode in ("empty_gate", "difference_gate") else "not_supported"
                if mode == "boundary_passing":
                    for variant, positive_count in (("corrupted", 9), ("literal", 11), ("paraphrase", 11), ("no_passage", 1)):
                        group = [row for row in key if row["protocol"] == "entailment" and row["variant"] == variant]
                        for i, row in enumerate(group):
                            by_id[row["case_id"]]["decision"] = "supported" if i < positive_count else "not_supported"
            actual = verifier.score_valid(packets, key, responses)
            self.assertEqual(actual, reference.score(packets, key, responses, blocks))
            self.assertIs(actual["operational_hypothesis_supported"], mode in ("passing", "boundary_passing"), mode)


if __name__ == "__main__":
    unittest.main()
