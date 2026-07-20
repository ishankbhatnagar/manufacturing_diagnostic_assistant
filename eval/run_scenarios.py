"""Full end-to-end diagnostic-accuracy eval: sends every scenario in
data/eval-scenarios/scenarios.json to the live, published Manufacturing
Diagnostic Assistant over Dify's Chat API and scores whether it answered vs. escalated as
expected.

Requires the full local stack running (Docker Dify + all four MCP servers)
-- see STATUS.md "Steps to resume after a reboot". Not run in CI (see
eval/README.md for why); run this manually against your local instance.

Usage:
    cd eval
    .venv\\Scripts\\python.exe run_scenarios.py
"""

import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

REPO_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_PATH = REPO_ROOT / "data" / "eval-scenarios" / "scenarios.json"
CAPTURED_DIR = REPO_ROOT / "knowledge-base" / "captured-expert-answers"
RESULTS_DIR = Path(__file__).parent / "results"

API_BASE = os.environ.get("DIFY_API_BASE", "http://localhost/v1")
API_KEY = os.environ.get("DIFY_API_KEY")

ESCALATE_PREFIX = "This has been escalated to a human expert to review."
FAULT_MODE_ID_PATTERN = re.compile(r"\b[A-Z]{2,5}-\d{2}\b")

RETRIES = 5
RETRY_BACKOFF_SECONDS = 8


def _captured_fault_mode_ids() -> set[str]:
    """Fault mode ids that already have a captured expert answer in the KB --
    scenarios for these may now legitimately answer instead of escalate.
    """
    ids = set()
    if CAPTURED_DIR.exists():
        for path in CAPTURED_DIR.glob("*.md"):
            match = FAULT_MODE_ID_PATTERN.search(path.read_text(encoding="utf-8"))
            if match:
                ids.add(match.group(0))
    return ids


def _ask(symptom_report: str) -> str:
    last_error = None
    for attempt in range(1, RETRIES + 1):
        try:
            resp = requests.post(
                f"{API_BASE}/chat-messages",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={
                    "inputs": {},
                    "query": symptom_report,
                    "response_mode": "blocking",
                    "user": "eval-harness",
                },
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()["answer"]
        except requests.HTTPError as e:
            last_error = f"{e} -- body: {e.response.text[:500]}"
            if attempt < RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS)
        except (requests.RequestException, KeyError) as e:
            last_error = e
            if attempt < RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS)
    raise RuntimeError(f"Chat request failed after {RETRIES} attempts: {last_error}")


def _classify(answer: str) -> str:
    return "escalate" if answer.startswith(ESCALATE_PREFIX) else "answer"


def run() -> dict:
    if not API_KEY or API_KEY == "app-your-key-here":
        print("Set DIFY_API_KEY in eval/.env (see .env.example) -- get it from the app's "
              "API Access page in Dify Studio.", file=sys.stderr)
        sys.exit(1)

    scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    if len(sys.argv) > 1:
        wanted = set(sys.argv[1:])
        scenarios = [s for s in scenarios if s["scenario_id"] in wanted]
    captured_ids = _captured_fault_mode_ids()

    results = []
    for i, s in enumerate(scenarios, 1):
        print(f"[{i}/{len(scenarios)}] {s['scenario_id']}...", end=" ", flush=True)
        try:
            answer = _ask(s["symptom_report"])
        except RuntimeError as e:
            print(f"ERROR: {e}")
            results.append({**s, "actual_outcome": "error", "answer": str(e), "pass": False})
            continue

        actual = _classify(answer)
        expected = s["expected_outcome"]
        grown = (
            expected == "escalate"
            and actual == "answer"
            and s["fault_mode_id"] in captured_ids
        )
        passed = actual == expected or grown

        cites_fault_mode = actual == "answer" and s["fault_mode_id"] in answer

        status = "PASS" if passed else "FAIL"
        if grown:
            status = "PASS (grown)"
        print(f"{status} (expected={expected}, actual={actual})")

        results.append(
            {
                **s,
                "actual_outcome": actual,
                "pass": passed,
                "grown_from_capture": grown,
                "cites_fault_mode_id": cites_fault_mode,
                "answer": answer,
            }
        )

    return {"results": results, "captured_fault_mode_ids": sorted(captured_ids)}


def summarize(report: dict) -> None:
    results = report["results"]
    total = len(results)
    passed = sum(1 for r in results if r["pass"])
    grown = sum(1 for r in results if r.get("grown_from_capture"))
    documented = [r for r in results if r["documented"]]
    undocumented = [r for r in results if not r["documented"]]

    print("\n" + "=" * 60)
    print(f"Overall: {passed}/{total} passed ({passed / total:.0%})")
    if grown:
        print(f"  of which {grown} passed via captured knowledge growth (Phase 07 SECI loop)")
    print(
        f"Documented faults (expect answer): "
        f"{sum(1 for r in documented if r['pass'])}/{len(documented)}"
    )
    print(
        f"Undocumented faults (expect escalate): "
        f"{sum(1 for r in undocumented if r['pass'])}/{len(undocumented)}"
    )
    answer_scenarios = [r for r in results if r["actual_outcome"] == "answer"]
    if answer_scenarios:
        cited = sum(1 for r in answer_scenarios if r["cites_fault_mode_id"])
        print(f"Of {len(answer_scenarios)} answers, {cited} explicitly cited the fault mode id")

    failures = [r for r in results if not r["pass"]]
    if failures:
        print("\nFailures:")
        for r in failures:
            print(
                f"  {r['scenario_id']}: expected {r['expected_outcome']}, "
                f"got {r['actual_outcome']}"
            )
    print("=" * 60)


if __name__ == "__main__":
    report = run()
    summarize(report)

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"run_{int(time.time())}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nFull results written to {out_path}")
