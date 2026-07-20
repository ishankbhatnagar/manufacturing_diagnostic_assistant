from ticketing import list_open_tickets, open_ticket

ticket = open_ticket(
    symptom_report="Gearbox is running hotter than usual and there's a slightly odd smell near the drive end.",
    ai_notes="Found references to motor thermal overload (MTR-01) and belt tension issues, "
    "but they don't directly explain a gearbox running hot with an odd smell.",
    retrieved_context="[incident-log] INC-MTR-01-1.md (fault mode: MTR-01) -- relevance 0.42\n"
    "Motor tripped on thermal overload after prolonged high-load run...",
)
print("Created:", ticket["ticket_id"])
print("Related fault mode IDs:", ticket["related_fault_mode_ids"])

print("\nOpen tickets:")
for t in list_open_tickets():
    print(" ", t["ticket_id"], "-", t["symptom_report"][:60])
