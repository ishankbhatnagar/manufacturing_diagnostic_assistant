# Line 7 Drive Motor & VFD — Troubleshooting Manual

Covers the 3-phase induction drive motor and variable-frequency drive (VFD) for the Line 7 door-panel assembly conveyor. Use this manual before opening a maintenance ticket for any motor or drive fault.

## MTR-01 — Motor thermal overload trip

**Severity:** medium

Thermal overload trips on the Line 7 drive motor are most often caused by restricted airflow at the cooling fan shroud, which accumulates fabric lint from the door-panel liner material over time. A secondary cause is belt over-tensioning, which increases motor load beyond its continuous rating. Always check airflow before adjusting VFD current limits.

**Likely causes:**
- Motor cooling fan cover blocked with debris, reducing airflow
- Line running above rated load due to over-tight belt tension
- Ambient temperature in the bay exceeding motor's rated duty cycle

**Diagnostic steps:**
1. Check motor nameplate temperature rating against a handheld IR reading on the housing after trip
2. Inspect the cooling fan shroud for dust or fabric debris
3. Verify belt tension against the spec range (should deflect 10-12mm under 4kg thumb pressure)

**Fix procedure:**
1. Clear the fan shroud and cooling fins
2. Re-tension the belt to spec if over-tight
3. If ambient heat is the cause, schedule the run for cooler shift windows or add bay ventilation

**Reported symptoms typically include:**
- "Conveyor motor keeps tripping on overload after running for about 20 minutes."
- "Line 7 drive motor shuts down on a thermal fault mid-shift, restarts fine once it cools."
- "Getting repeated OL trips on the conveyor motor once the line has been running a while."

## VFD-01 — VFD overcurrent fault (E003)

**Severity:** high

E003 indicates the VFD measured current above its instantaneous trip threshold during acceleration. In most cases on Line 7 this traces back to the acceleration ramp being shortened during a previous changeover and never restored, which spikes starting current beyond the motor's safe curve. Mechanical binding is the second most common cause and should be ruled out first.

**Likely causes:**
- Mechanical jam or excessive static friction at start-up
- Acceleration ramp set too aggressive for the load inertia
- Worn motor bearings increasing starting torque demand

**Diagnostic steps:**
1. Attempt a manual jog at low speed to check for mechanical binding
2. Review the VFD's acceleration ramp parameter (P1.05) against the commissioning spec
3. Check motor bearing play by hand-rocking the shaft with power isolated

**Fix procedure:**
1. Clear any mechanical jam on the conveyor bed before re-attempting start
2. If ramp time is below 3 seconds, increase it toward the 4-5 second commissioning default
3. Escalate to mechanical for bearing replacement if shaft play is detected

**Reported symptoms typically include:**
- "VFD is throwing E003 and won't let the line restart."
- "Drive faults out with an overcurrent code right at line start-up, every time."
- "E003 on the VFD display, conveyor won't move at all this morning."
