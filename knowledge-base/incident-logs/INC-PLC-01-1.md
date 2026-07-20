# Incident INC-PLC-01-1

- **Date:** 2026-04-15
- **Shift:** Night shift
- **Reported by:** R. Sato
- **Equipment:** Line 7 — plc
- **Related fault mode:** PLC-01 (Intermittent PLC communication timeout)
- **Status:** Resolved

## Reported symptom

> HMI keeps showing a comms fault for a second or two, then it clears itself.

## Root cause

Intermittent, self-clearing PLC comms faults are almost always physical-layer issues: a marginal connector or a comms cable running too close to VFD output leads, which are electrically noisy. Rule out cabling before escalating to a controls engineering review.

## Resolution

1. Reseat or replace the connector if pins show wear or corrosion
2. Reroute the comms cable away from power cabling, maintaining at least 30cm separation
3. If scan-overrun is confirmed, contact controls engineering to review I/O scan configuration
