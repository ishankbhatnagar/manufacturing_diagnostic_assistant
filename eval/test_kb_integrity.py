"""Data-integrity checks for the eval scenarios, image manifest, and
knowledge base. Pure Python + stdlib -- no Docker/Dify/Groq/torch needed --
so this is what actually runs in CI (see eval/README.md).
"""

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_PATH = REPO_ROOT / "data" / "eval-scenarios" / "scenarios.json"
MANIFEST_PATH = REPO_ROOT / "data" / "eval-scenarios" / "symptom-images" / "manifest.json"
IMAGES_DIR = MANIFEST_PATH.parent
KB_ROOT = REPO_ROOT / "knowledge-base"
TICKETS_DIR = REPO_ROOT / "data" / "tickets"

sys.path.insert(0, str(REPO_ROOT / "data" / "synthetic-generator"))
from fault_catalog import FAULT_MODES  # noqa: E402

FAULT_MODE_ID_PATTERN = re.compile(r"\b[A-Z]{2,5}-\d{2}\b")
CATALOG_IDS = {f["id"] for f in FAULT_MODES}
DOCUMENTED_IDS = {f["id"] for f in FAULT_MODES if f["documented"]}
UNDOCUMENTED_IDS = {f["id"] for f in FAULT_MODES if not f["documented"]}


@pytest.fixture(scope="module")
def scenarios():
    return json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_scenario_ids_unique(scenarios):
    ids = [s["scenario_id"] for s in scenarios]
    assert len(ids) == len(set(ids)), "duplicate scenario_id found"


def test_scenario_required_fields(scenarios):
    required = {
        "scenario_id",
        "fault_mode_id",
        "subsystem",
        "documented",
        "symptom_report",
        "expected_outcome",
        "expected_fix_summary",
    }
    for s in scenarios:
        missing = required - s.keys()
        assert not missing, f"{s.get('scenario_id')} missing fields: {missing}"


def test_scenario_expected_outcome_valid(scenarios):
    for s in scenarios:
        assert s["expected_outcome"] in ("answer", "escalate"), s["scenario_id"]


def test_scenario_documented_matches_expected_outcome(scenarios):
    # Ground-truth authoring invariant: a scenario built from a documented
    # fault mode should originally expect "answer", undocumented "escalate".
    # (Live eval runs may diverge from this *on purpose* once Phase 07
    # captures an expert answer -- that's growth, not a data bug. This test
    # is about the authored scenarios.json file itself staying consistent.)
    for s in scenarios:
        expected = "answer" if s["documented"] else "escalate"
        assert s["expected_outcome"] == expected, (
            f"{s['scenario_id']}: documented={s['documented']} but "
            f"expected_outcome={s['expected_outcome']}"
        )


def test_scenario_fault_mode_ids_exist_in_catalog(scenarios):
    for s in scenarios:
        assert s["fault_mode_id"] in CATALOG_IDS, (
            f"{s['scenario_id']} references unknown fault_mode_id {s['fault_mode_id']}"
        )


def test_every_catalog_fault_mode_has_a_scenario(scenarios):
    covered = {s["fault_mode_id"] for s in scenarios}
    missing = CATALOG_IDS - covered
    assert not missing, f"fault modes with no eval scenario: {missing}"


def test_manifest_entries_valid(manifest):
    required = {"filename", "fault_mode_id", "expected_text_contains"}
    for entry in manifest:
        missing = required - entry.keys()
        assert not missing, f"{entry.get('filename')} missing fields: {missing}"
        assert entry["fault_mode_id"] in CATALOG_IDS
        assert entry["expected_text_contains"], f"{entry['filename']} has no expected text"


def test_manifest_images_exist_on_disk(manifest):
    for entry in manifest:
        image_path = IMAGES_DIR / entry["filename"]
        assert image_path.exists(), f"missing image file: {image_path}"


def test_documented_fault_modes_have_manual_or_incident_coverage():
    manual_text = " ".join(
        p.read_text(encoding="utf-8") for p in (KB_ROOT / "manuals").glob("*.md")
    )
    incident_text = " ".join(
        p.read_text(encoding="utf-8") for p in (KB_ROOT / "incident-logs").glob("*.md")
    )
    combined = manual_text + incident_text
    for fault_id in DOCUMENTED_IDS:
        assert fault_id in combined, (
            f"documented fault mode {fault_id} has no manual/incident-log coverage"
        )


def test_undocumented_fault_modes_have_no_manual_or_incident_coverage():
    # The whole point of the "undocumented" set is that they're NOT written
    # up anywhere -- if one leaks into manuals/incident-logs, the eval's
    # escalate-vs-answer ground truth is no longer valid for it.
    manual_text = " ".join(
        p.read_text(encoding="utf-8") for p in (KB_ROOT / "manuals").glob("*.md")
    )
    incident_text = " ".join(
        p.read_text(encoding="utf-8") for p in (KB_ROOT / "incident-logs").glob("*.md")
    )
    combined = manual_text + incident_text
    for fault_id in UNDOCUMENTED_IDS:
        assert fault_id not in combined, (
            f"undocumented fault mode {fault_id} unexpectedly appears in manuals/incident-logs"
        )


def test_captured_expert_answers_have_a_fault_mode_id():
    captured_dir = KB_ROOT / "captured-expert-answers"
    if not captured_dir.exists():
        return
    for path in captured_dir.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        assert FAULT_MODE_ID_PATTERN.search(text), (
            f"{path.name} has no fault-mode-id-shaped token -- indexer.py won't link it "
            "to a fault mode"
        )


def test_tickets_have_valid_schema():
    if not TICKETS_DIR.exists():
        return
    required = {"ticket_id", "status", "created_at", "symptom_report"}
    for path in TICKETS_DIR.glob("*.json"):
        ticket = json.loads(path.read_text(encoding="utf-8"))
        missing = required - ticket.keys()
        assert not missing, f"{path.name} missing fields: {missing}"
        assert ticket["status"] in ("open", "resolved"), path.name
