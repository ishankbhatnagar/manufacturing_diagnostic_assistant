"""Builds the labeled eval set: technician symptom reports mapped to the
correct fault mode, expected outcome (answer vs escalate), and -- for
undocumented faults -- the expert's ground-truth resolution text, used later
to simulate the escalation dashboard in the eval harness.
"""

import json
from pathlib import Path
from fault_catalog import FAULT_MODES

OUT_PATH = Path(__file__).resolve().parents[1] / "eval-scenarios" / "scenarios.json"


def expected_fix_summary(fault: dict) -> str:
    if fault["documented"]:
        return fault["fix_steps"][0] if fault["fix_steps"] else fault["manual_paragraph"]
    return fault["expert_note"][:160] + "..."


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    scenarios = []

    for fault in FAULT_MODES:
        for i, symptom in enumerate(fault["symptom_phrasings"], 1):
            scenario = {
                "scenario_id": f"{fault['id']}-S{i}",
                "fault_mode_id": fault["id"],
                "subsystem": fault["subsystem"],
                "documented": fault["documented"],
                "symptom_report": symptom,
                "expected_outcome": "answer" if fault["documented"] else "escalate",
                "expected_fix_summary": expected_fix_summary(fault),
            }
            if not fault["documented"]:
                scenario["expert_resolution_text"] = fault["expert_note"]
            scenarios.append(scenario)

    OUT_PATH.write_text(json.dumps(scenarios, indent=2, ensure_ascii=False), encoding="utf-8")

    n_answer = sum(1 for s in scenarios if s["expected_outcome"] == "answer")
    n_escalate = sum(1 for s in scenarios if s["expected_outcome"] == "escalate")
    print(f"Wrote {len(scenarios)} eval scenarios to {OUT_PATH}")
    print(f"  - expected 'answer': {n_answer}")
    print(f"  - expected 'escalate': {n_escalate}")


if __name__ == "__main__":
    main()
