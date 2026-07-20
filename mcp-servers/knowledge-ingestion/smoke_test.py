from pathlib import Path

from capture import capture_expert_answer

TEST_TICKET_ID = "TKT-20260718-151407-cab0"  # the escalated "gearbox heat/smell" case

result = capture_expert_answer(
    ticket_id=TEST_TICKET_ID,
    expert_answer=(
        "This is a worn gearbox output-shaft seal. The odd smell is the gear oil starting to "
        "scorch as it seeps past the seal onto the housing, and the heat is from running low "
        "on oil. 1) Check the oil level/color at the sight glass -- if low or dark, that "
        "confirms it. 2) Replace the output-shaft seal at next planned downtime. 3) Top up with "
        "the spec gear oil (see maintenance manual) and monitor for a week. Don't run it dry -- "
        "escalate immediately if the smell gets stronger or oil level keeps dropping."
    ),
    fault_mode_id="GBX-01",
    expert_name="M. Ishikawa",
)
print("File:", result["file"])
print("Fault mode ID:", result["fault_mode_id"])
print("Reindexed:", result["reindexed"])
print("Ticket found:", result["ticket_found"])
if not result["reindexed"]:
    print("Reindex output:", result["reindex_output"])

print("\nCaptured file exists:", Path(result["file"]).exists())
