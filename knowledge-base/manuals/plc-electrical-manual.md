# Line 7 PLC & Electrical Supply — Troubleshooting Manual

Covers the PLC control rack, HMI communications, and incoming electrical supply for Line 7.

## PLC-01 — Intermittent PLC communication timeout

**Severity:** high

Intermittent, self-clearing PLC comms faults are almost always physical-layer issues: a marginal connector or a comms cable running too close to VFD output leads, which are electrically noisy. Rule out cabling before escalating to a controls engineering review.

**Likely causes:**
- Loose or degraded network cable connector at the PLC rack
- Electrical noise coupling into the comms cable from a nearby high-current run
- Firmware-level buffer overflow under high I/O scan load

**Diagnostic steps:**
1. Inspect and reseat the network cable connectors at the PLC and HMI ends
2. Check cable routing for proximity to motor power cables or VFD output leads
3. Pull the PLC's diagnostic buffer log to check for scan-overrun warnings

**Fix procedure:**
1. Reseat or replace the connector if pins show wear or corrosion
2. Reroute the comms cable away from power cabling, maintaining at least 30cm separation
3. If scan-overrun is confirmed, contact controls engineering to review I/O scan configuration

**Reported symptoms typically include:**
- "HMI keeps showing a comms fault for a second or two, then it clears itself."
- "Line hiccups randomly with a PLC timeout error, no pattern to when it happens."
- "Getting sporadic communication faults on the control panel, maybe a few times a shift."

## ELEC-01 — Voltage sag nuisance trips during shift-change

**Severity:** medium

Faults that cluster tightly around shift-change are a strong signal of plant-wide voltage sag from simultaneous line start-ups rather than a Line 7-specific fault. Confirm with a voltage log before doing any component-level troubleshooting.

**Likely causes:**
- Plant-wide voltage sag from simultaneous motor start-up loads across multiple lines
- VFD undervoltage trip threshold set too conservatively for the plant's supply characteristics

**Diagnostic steps:**
1. Correlate the fault timestamp against the plant's shift-change start sequence log
2. Log incoming supply voltage at the Line 7 panel across a shift-change window

**Fix procedure:**
1. If sag is confirmed and within utility tolerance, stagger Line 7's start-up by 2-3 minutes relative to other lines
2. If sag is severe, escalate to facilities electrical for supply-side investigation

**Reported symptoms typically include:**
- "Line trips out right around shift-change every time, like clockwork."
- "We get a nuisance fault every day around the same time in the morning."
- "Drive faults right when the other lines are all starting up together."
