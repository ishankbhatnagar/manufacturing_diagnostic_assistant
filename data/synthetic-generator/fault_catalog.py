"""
Ground-truth fault catalog for Line 7 (automotive door-panel assembly conveyor).

Each entry is either `documented` (written up in a manual and/or past incident
logs -- the agent should be able to answer these confidently from RAG) or
undocumented (tacit expert knowledge that exists nowhere in writing -- the
agent should escalate these, and the expert's answer becomes the seed content
for the knowledge-ingestion / SECI capture loop in later phases).
"""

FAULT_MODES = [
    # -------------------- documented (7) --------------------
    {
        "id": "MTR-01",
        "subsystem": "motor_drive",
        "name": "Motor thermal overload trip",
        "documented": True,
        "severity": "medium",
        "symptom_phrasings": [
            "Conveyor motor keeps tripping on overload after running for about 20 minutes.",
            "Line 7 drive motor shuts down on a thermal fault mid-shift, restarts fine once it cools.",
            "Getting repeated OL trips on the conveyor motor once the line has been running a while.",
        ],
        "likely_causes": [
            "Motor cooling fan cover blocked with debris, reducing airflow",
            "Line running above rated load due to over-tight belt tension",
            "Ambient temperature in the bay exceeding motor's rated duty cycle",
        ],
        "diagnostic_steps": [
            "Check motor nameplate temperature rating against a handheld IR reading on the housing after trip",
            "Inspect the cooling fan shroud for dust or fabric debris",
            "Verify belt tension against the spec range (should deflect 10-12mm under 4kg thumb pressure)",
        ],
        "fix_steps": [
            "Clear the fan shroud and cooling fins",
            "Re-tension the belt to spec if over-tight",
            "If ambient heat is the cause, schedule the run for cooler shift windows or add bay ventilation",
        ],
        "manual_paragraph": (
            "Thermal overload trips on the Line 7 drive motor are most often caused by restricted airflow "
            "at the cooling fan shroud, which accumulates fabric lint from the door-panel liner material over "
            "time. A secondary cause is belt over-tensioning, which increases motor load beyond its continuous "
            "rating. Always check airflow before adjusting VFD current limits."
        ),
    },
    {
        "id": "VFD-01",
        "subsystem": "vfd",
        "name": "VFD overcurrent fault (E003)",
        "documented": True,
        "severity": "high",
        "symptom_phrasings": [
            "VFD is throwing E003 and won't let the line restart.",
            "Drive faults out with an overcurrent code right at line start-up, every time.",
            "E003 on the VFD display, conveyor won't move at all this morning.",
        ],
        "likely_causes": [
            "Mechanical jam or excessive static friction at start-up",
            "Acceleration ramp set too aggressive for the load inertia",
            "Worn motor bearings increasing starting torque demand",
        ],
        "diagnostic_steps": [
            "Attempt a manual jog at low speed to check for mechanical binding",
            "Review the VFD's acceleration ramp parameter (P1.05) against the commissioning spec",
            "Check motor bearing play by hand-rocking the shaft with power isolated",
        ],
        "fix_steps": [
            "Clear any mechanical jam on the conveyor bed before re-attempting start",
            "If ramp time is below 3 seconds, increase it toward the 4-5 second commissioning default",
            "Escalate to mechanical for bearing replacement if shaft play is detected",
        ],
        "manual_paragraph": (
            "E003 indicates the VFD measured current above its instantaneous trip threshold during "
            "acceleration. In most cases on Line 7 this traces back to the acceleration ramp being shortened "
            "during a previous changeover and never restored, which spikes starting current beyond the motor's "
            "safe curve. Mechanical binding is the second most common cause and should be ruled out first."
        ),
    },
    {
        "id": "CNV-01",
        "subsystem": "conveyor_mechanical",
        "name": "Belt slippage from worn drive pulley",
        "documented": True,
        "severity": "medium",
        "symptom_phrasings": [
            "Belt seems to be slipping on the drive pulley, panels are arriving late to station 3.",
            "Conveyor speed looks inconsistent even though the VFD readout is steady.",
            "Hearing a rhythmic squeal from the drive end, and the line is running slower than takt.",
        ],
        "likely_causes": [
            "Drive pulley lagging worn smooth from years of use",
            "Belt tension below spec, allowing slip under load",
            "Contamination (oil/grease) on the pulley surface reducing friction",
        ],
        "diagnostic_steps": [
            "Visually inspect the pulley lagging for shine/smoothness compared to a new reference pulley",
            "Measure actual belt speed with a tachometer against the VFD's commanded speed",
            "Check for oil or grease contamination near the drive end",
        ],
        "fix_steps": [
            "Clean the pulley surface with the approved degreaser if contamination is found",
            "Re-tension the belt to spec",
            "If lagging is worn smooth, schedule pulley re-lagging at next planned downtime",
        ],
        "manual_paragraph": (
            "A mismatch between commanded VFD speed and actual measured belt speed, especially accompanied by "
            "a rhythmic squeal, points to drive pulley lagging wear. Re-lagging is a planned-maintenance item; "
            "in the interim, cleaning and re-tensioning can restore acceptable grip for one to two more shifts."
        ),
    },
    {
        "id": "SEN-01",
        "subsystem": "sensors",
        "name": "Photoelectric sensor misalignment",
        "documented": True,
        "severity": "low",
        "symptom_phrasings": [
            "Line keeps false-stopping like it thinks a panel is there when it isn't.",
            "Part-present sensor at station 2 is flaky, sometimes it just doesn't see the panel at all.",
            "Getting random stops with no part jam, sensor light looks like it's flickering.",
        ],
        "likely_causes": [
            "Sensor bracket knocked out of alignment during a manual panel adjustment",
            "Sensor lens fouled with dust or overspray from the adjacent paint touch-up station",
            "Reflective background interference after a nearby fixture was repositioned",
        ],
        "diagnostic_steps": [
            "Check the sensor's alignment indicator LED against the reflector",
            "Wipe the lens and re-test",
            "Confirm nothing reflective was recently placed in the sensor's background field",
        ],
        "fix_steps": [
            "Realign the sensor bracket using the laser alignment jig and re-torque the mounting screw",
            "Clean the lens with an approved lint-free wipe",
            "Relocate any new reflective fixtures out of the sensor's field of view",
        ],
        "manual_paragraph": (
            "Photoelectric part-present sensors on Line 7 are set to a tight alignment tolerance because of "
            "the short detection window at takt speed. Most false-stop complaints trace back to bracket "
            "misalignment after nearby manual adjustments, or lens fouling from the adjacent touch-up booth."
        ),
    },
    {
        "id": "PNU-01",
        "subsystem": "pneumatic",
        "name": "Clamp pressure drop from air leak",
        "documented": True,
        "severity": "medium",
        "symptom_phrasings": [
            "Panel clamp isn't holding tight, panels shift slightly during the press cycle.",
            "Pressure gauge on the clamp unit reads low compared to the shift start checklist value.",
            "Hearing a faint hiss near the clamp cylinder, and clamp force seems weak.",
        ],
        "likely_causes": [
            "Cracked or perished air line near the clamp cylinder",
            "Loose push-to-connect fitting from vibration over time",
            "Worn cylinder seal allowing internal bypass",
        ],
        "diagnostic_steps": [
            "Apply leak-detection solution along the air lines and fittings near the clamp",
            "Check the regulator setting against the 6 bar spec",
            "If no external leak found, check for internal bypass by isolating the cylinder and watching for pressure decay",
        ],
        "fix_steps": [
            "Replace any cracked line or reseat/replace a loose fitting",
            "Reset the regulator to spec if it has drifted",
            "Escalate to mechanical for cylinder seal replacement if internal bypass is confirmed",
        ],
        "manual_paragraph": (
            "Clamp pressure complaints are first a leak-hunting exercise, not a cylinder-replacement one. The "
            "push-to-connect fittings near the clamp are prone to loosening from cyclic vibration and should "
            "be the first check before assuming a seal failure."
        ),
    },
    {
        "id": "PLC-01",
        "subsystem": "plc",
        "name": "Intermittent PLC communication timeout",
        "documented": True,
        "severity": "high",
        "symptom_phrasings": [
            "HMI keeps showing a comms fault for a second or two, then it clears itself.",
            "Line hiccups randomly with a PLC timeout error, no pattern to when it happens.",
            "Getting sporadic communication faults on the control panel, maybe a few times a shift.",
        ],
        "likely_causes": [
            "Loose or degraded network cable connector at the PLC rack",
            "Electrical noise coupling into the comms cable from a nearby high-current run",
            "Firmware-level buffer overflow under high I/O scan load",
        ],
        "diagnostic_steps": [
            "Inspect and reseat the network cable connectors at the PLC and HMI ends",
            "Check cable routing for proximity to motor power cables or VFD output leads",
            "Pull the PLC's diagnostic buffer log to check for scan-overrun warnings",
        ],
        "fix_steps": [
            "Reseat or replace the connector if pins show wear or corrosion",
            "Reroute the comms cable away from power cabling, maintaining at least 30cm separation",
            "If scan-overrun is confirmed, contact controls engineering to review I/O scan configuration",
        ],
        "manual_paragraph": (
            "Intermittent, self-clearing PLC comms faults are almost always physical-layer issues: a marginal "
            "connector or a comms cable running too close to VFD output leads, which are electrically noisy. "
            "Rule out cabling before escalating to a controls engineering review."
        ),
    },
    {
        "id": "ELEC-01",
        "subsystem": "electrical",
        "name": "Voltage sag nuisance trips during shift-change",
        "documented": True,
        "severity": "medium",
        "symptom_phrasings": [
            "Line trips out right around shift-change every time, like clockwork.",
            "We get a nuisance fault every day around the same time in the morning.",
            "Drive faults right when the other lines are all starting up together.",
        ],
        "likely_causes": [
            "Plant-wide voltage sag from simultaneous motor start-up loads across multiple lines",
            "VFD undervoltage trip threshold set too conservatively for the plant's supply characteristics",
        ],
        "diagnostic_steps": [
            "Correlate the fault timestamp against the plant's shift-change start sequence log",
            "Log incoming supply voltage at the Line 7 panel across a shift-change window",
        ],
        "fix_steps": [
            "If sag is confirmed and within utility tolerance, stagger Line 7's start-up by 2-3 minutes relative to other lines",
            "If sag is severe, escalate to facilities electrical for supply-side investigation",
        ],
        "manual_paragraph": (
            "Faults that cluster tightly around shift-change are a strong signal of plant-wide voltage sag "
            "from simultaneous line start-ups rather than a Line 7-specific fault. Confirm with a voltage log "
            "before doing any component-level troubleshooting."
        ),
    },
    # -------------------- undocumented / tacit (5) --------------------
    {
        "id": "BRG-01",
        "subsystem": "conveyor_mechanical",
        "name": "Early-stage bearing wear (audible, pre-failure)",
        "documented": False,
        "severity": "high",
        "symptom_phrasings": [
            "Not really a fault code, but the drive end sounds different lately, kind of a high whine.",
            "Everything's running fine on paper, but there's a new noise from the tail pulley I can't place.",
            "No errors on the HMI, just a faint whine that gets louder toward end of shift.",
        ],
        "likely_causes": [],
        "diagnostic_steps": [],
        "fix_steps": [],
        "manual_paragraph": None,
        "expert_note": (
            "That high, steady whine — not a rattle, not a knock, a whine — is the tell for a bearing starting "
            "to go dry. It won't throw any code because load and current both look normal right up until it "
            "seizes, sometimes with only a day or two of warning. I put two fingers on the bearing housing "
            "(power still on, hand flat, never wrap fingers around anything moving) and if it's noticeably "
            "warmer than the opposite side bearing, that confirms it. Swap it on the next planned stop, don't "
            "wait for a code, because by the time it faults you're looking at an unplanned line-down and "
            "possible shaft damage instead of a 40-minute bearing swap."
        ),
    },
    {
        "id": "ENC-01",
        "subsystem": "motor_drive",
        "name": "Encoder feedback drift causing gradual mis-registration",
        "documented": False,
        "severity": "medium",
        "symptom_phrasings": [
            "Panels have been landing a couple millimeters off at station 4, but it's been gradual, not sudden.",
            "Registration's drifted slightly over the past week or two, nothing threw an alarm though.",
            "Position looks slightly off compared to last month, hard to say exactly when it started.",
        ],
        "likely_causes": [],
        "diagnostic_steps": [],
        "fix_steps": [],
        "manual_paragraph": None,
        "expert_note": (
            "This one's sneaky because it never trips anything — the encoder count itself is fine, it's the "
            "coupling between the encoder shaft and the motor shaft that's slowly slipping a fraction of a "
            "degree at a time from thermal cycling. You won't catch it by looking at the encoder counts in "
            "isolation. What I do is compare today's home-position offset against the value recorded in the "
            "commissioning sheet — if it's drifted more than about 0.5 degrees, the coupling needs to be "
            "re-clamped and the axis re-homed. Left alone it keeps creeping and eventually you get intermittent "
            "part rejects that look like a totally unrelated tooling problem."
        ),
    },
    {
        "id": "VFD-02",
        "subsystem": "vfd",
        "name": "Harmonic interference from adjacent welding robot",
        "documented": False,
        "severity": "medium",
        "symptom_phrasings": [
            "VFD throws a random fault only when the welding cell next door is running its heavy cycle.",
            "Drive faults seem to line up with the robot cell doing its big weld sequence, but I'm not 100% sure.",
            "Sporadic drive fault, and now that I think about it, it's always when the neighboring cell is busy.",
        ],
        "likely_causes": [],
        "diagnostic_steps": [],
        "fix_steps": [],
        "manual_paragraph": None,
        "expert_note": (
            "Nobody believes this the first time, but the welding robot cell next door puts harmonic noise "
            "back onto the shared supply feed during its high-current weld pulses, and our VFD's input filter "
            "was never sized for that. It only shows up when both lines are running heavy at the same time, "
            "which is why it looks random — it's not random, it's correlated with their cycle, just on a "
            "different line so nobody thinks to check it. Fastest confirmation: ask their operator to run one "
            "isolated weld cycle while you watch our VFD's DC bus ripple reading. If it spikes in sync, that's "
            "your answer. Real fix is an input line reactor on our VFD, but until that's installed, avoid "
            "scheduling our high-load changeovers during their heavy weld blocks."
        ),
    },
    {
        "id": "GBX-01",
        "subsystem": "conveyor_mechanical",
        "name": "Gearbox grease contamination from wrong lubricant substitution",
        "documented": False,
        "severity": "high",
        "symptom_phrasings": [
            "Gearbox is running hotter than usual and there's a slightly odd smell near the drive end.",
            "Noticed some foamy-looking residue near the gearbox breather, not sure if that's normal.",
            "Gearbox oil looks a bit milky when I checked the sight glass, temperature's up a few degrees too.",
        ],
        "likely_causes": [],
        "diagnostic_steps": [],
        "fix_steps": [],
        "manual_paragraph": None,
        "expert_note": (
            "Milky or foamy grease at the breather almost always means someone topped up with the wrong "
            "lubricant grade during a changeover — there are two gearboxes on this line that look identical "
            "but spec different synthetic greases, and they don't mix well; the wrong one breaks down and "
            "foams under heat instead of lubricating properly. If you see that residue, don't just top it up "
            "again, that makes it worse. Full drain, flush with the correct grade, and refill to the sight "
            "glass line. I'd also tag the grease gun used for that changeover so whoever did it doesn't repeat "
            "it on the other line."
        ),
    },
    {
        "id": "GND-01",
        "subsystem": "sensors",
        "name": "Static discharge sensor glitches from loose grounding strap",
        "documented": False,
        "severity": "low",
        "symptom_phrasings": [
            "Sensors glitch out only on dry days, seems worse in winter for some reason.",
            "Getting weird one-off sensor faults that clear themselves, mostly when humidity's low.",
            "Random single-cycle sensor fault, no pattern except it seems to happen more when it's dry out.",
        ],
        "likely_causes": [],
        "diagnostic_steps": [],
        "fix_steps": [],
        "manual_paragraph": None,
        "expert_note": (
            "The humidity correlation is the giveaway — that's static, not a sensor defect. The door-panel "
            "liner material builds a static charge as it slides across the conveyor bed, and it should "
            "discharge harmlessly through the frame's grounding strap. One of those straps near station 2 has "
            "been loose for a while, so instead of discharging cleanly it sometimes arcs near the sensor wiring "
            "and causes a brief glitch. Check the grounding strap continuity with a multimeter, not just a "
            "visual check, because it can look connected but have a bad crimp. Re-terminate it and the dry-day "
            "glitches stop."
        ),
    },
]
