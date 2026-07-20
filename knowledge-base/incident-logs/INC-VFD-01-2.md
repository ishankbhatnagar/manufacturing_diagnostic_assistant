# Incident INC-VFD-01-2

- **Date:** 2025-12-14
- **Shift:** Day shift
- **Reported by:** A. Kobayashi
- **Equipment:** Line 7 — vfd
- **Related fault mode:** VFD-01 (VFD overcurrent fault (E003))
- **Status:** Resolved

## Reported symptom

> Drive faults out with an overcurrent code right at line start-up, every time.

## Root cause

E003 indicates the VFD measured current above its instantaneous trip threshold during acceleration. In most cases on Line 7 this traces back to the acceleration ramp being shortened during a previous changeover and never restored, which spikes starting current beyond the motor's safe curve. Mechanical binding is the second most common cause and should be ruled out first.

## Resolution

1. Clear any mechanical jam on the conveyor bed before re-attempting start
2. If ramp time is below 3 seconds, increase it toward the 4-5 second commissioning default
3. Escalate to mechanical for bearing replacement if shaft play is detected
