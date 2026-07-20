"""Renders past resolved incident tickets for documented fault modes only.

Undocumented (tacit) faults intentionally have no incident history -- that's
the entire premise of the project: nobody wrote it down.
"""

from pathlib import Path
from fault_catalog import FAULT_MODES

OUT_DIR = Path(__file__).resolve().parents[2] / "knowledge-base" / "incident-logs"

TECHNICIANS = ["R. Sato", "K. Tanaka", "M. Suzuki", "A. Kobayashi", "T. Yamamoto"]
SHIFTS = ["Day shift", "Night shift", "Swing shift"]

# deterministic pseudo-dates so the dataset is reproducible
DATES = [
    "2025-11-03", "2025-11-18", "2025-12-02", "2025-12-14", "2026-01-06",
    "2026-01-22", "2026-02-09", "2026-02-27", "2026-03-11", "2026-03-30",
    "2026-04-15", "2026-05-02", "2026-05-19", "2026-06-04",
]


def render_incident(fault: dict, symptom: str, date: str, tech: str, shift: str, ticket_no: str) -> str:
    lines = [
        f"# Incident {ticket_no}",
        "",
        f"- **Date:** {date}",
        f"- **Shift:** {shift}",
        f"- **Reported by:** {tech}",
        f"- **Equipment:** Line 7 — {fault['subsystem'].replace('_', ' ')}",
        f"- **Related fault mode:** {fault['id']} ({fault['name']})",
        f"- **Status:** Resolved",
        "",
        "## Reported symptom",
        "",
        f"> {symptom}",
        "",
        "## Root cause",
        "",
        fault["manual_paragraph"] or "",
        "",
        "## Resolution",
        "",
    ]
    for i, s in enumerate(fault["fix_steps"], 1):
        lines.append(f"{i}. {s}")
    lines.append("")
    return "\n".join(lines)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    documented = [f for f in FAULT_MODES if f["documented"]]

    date_i = 0
    written = []
    for fault in documented:
        # two historical incidents per documented fault, using different phrasing variants
        for n in range(2):
            symptom = fault["symptom_phrasings"][n % len(fault["symptom_phrasings"])]
            date = DATES[date_i % len(DATES)]
            tech = TECHNICIANS[date_i % len(TECHNICIANS)]
            shift = SHIFTS[date_i % len(SHIFTS)]
            date_i += 1
            ticket_no = f"INC-{fault['id']}-{n + 1}"
            content = render_incident(fault, symptom, date, tech, shift, ticket_no)
            path = OUT_DIR / f"{ticket_no}.md"
            path.write_text(content, encoding="utf-8")
            written.append(path)

    print(f"Wrote {len(written)} incident log files to {OUT_DIR}")


if __name__ == "__main__":
    main()
