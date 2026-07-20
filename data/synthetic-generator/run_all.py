"""Runs all Phase 01 generators in order."""

import generate_manuals
import generate_incident_logs
import generate_eval_scenarios

if __name__ == "__main__":
    print("=== Manuals ===")
    generate_manuals.main()
    print("\n=== Incident logs ===")
    generate_incident_logs.main()
    print("\n=== Eval scenarios ===")
    generate_eval_scenarios.main()
