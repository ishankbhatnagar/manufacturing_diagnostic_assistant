"""Renders the documented fault modes into per-subsystem manual markdown files."""

from pathlib import Path
from fault_catalog import FAULT_MODES

OUT_DIR = Path(__file__).resolve().parents[2] / "knowledge-base" / "manuals"

MANUAL_GROUPS = [
    {
        "filename": "motor-and-vfd-manual.md",
        "title": "Line 7 Drive Motor & VFD — Troubleshooting Manual",
        "intro": (
            "Covers the 3-phase induction drive motor and variable-frequency drive (VFD) for the "
            "Line 7 door-panel assembly conveyor. Use this manual before opening a maintenance ticket "
            "for any motor or drive fault."
        ),
        "fault_ids": ["MTR-01", "VFD-01"],
    },
    {
        "filename": "conveyor-mechanical-manual.md",
        "title": "Line 7 Conveyor Mechanical — Troubleshooting Manual",
        "intro": "Covers the belt, drive pulley, and mechanical drivetrain of the Line 7 conveyor.",
        "fault_ids": ["CNV-01"],
    },
    {
        "filename": "sensor-system-manual.md",
        "title": "Line 7 Part-Sensing System — Troubleshooting Manual",
        "intro": "Covers the photoelectric part-present sensors used along the Line 7 conveyor.",
        "fault_ids": ["SEN-01"],
    },
    {
        "filename": "pneumatic-system-manual.md",
        "title": "Line 7 Pneumatic Clamp Press — Troubleshooting Manual",
        "intro": "Covers the pneumatic clamp cylinder and air supply for the Line 7 panel press station.",
        "fault_ids": ["PNU-01"],
    },
    {
        "filename": "plc-electrical-manual.md",
        "title": "Line 7 PLC & Electrical Supply — Troubleshooting Manual",
        "intro": "Covers the PLC control rack, HMI communications, and incoming electrical supply for Line 7.",
        "fault_ids": ["PLC-01", "ELEC-01"],
    },
]


def render_fault_section(fault: dict) -> str:
    lines = [f"## {fault['id']} — {fault['name']}", ""]
    lines.append(f"**Severity:** {fault['severity']}")
    lines.append("")
    lines.append(fault["manual_paragraph"])
    lines.append("")
    lines.append("**Likely causes:**")
    for c in fault["likely_causes"]:
        lines.append(f"- {c}")
    lines.append("")
    lines.append("**Diagnostic steps:**")
    for i, s in enumerate(fault["diagnostic_steps"], 1):
        lines.append(f"{i}. {s}")
    lines.append("")
    lines.append("**Fix procedure:**")
    for i, s in enumerate(fault["fix_steps"], 1):
        lines.append(f"{i}. {s}")
    lines.append("")
    lines.append("**Reported symptoms typically include:**")
    for p in fault["symptom_phrasings"]:
        lines.append(f"- \"{p}\"")
    lines.append("")
    return "\n".join(lines)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    by_id = {f["id"]: f for f in FAULT_MODES}
    written = []

    for group in MANUAL_GROUPS:
        parts = [f"# {group['title']}", "", group["intro"], ""]
        for fid in group["fault_ids"]:
            parts.append(render_fault_section(by_id[fid]))
        content = "\n".join(parts)
        path = OUT_DIR / group["filename"]
        path.write_text(content, encoding="utf-8")
        written.append(path)

    print(f"Wrote {len(written)} manual files to {OUT_DIR}")
    for p in written:
        print(f"  - {p.name}")


if __name__ == "__main__":
    main()
