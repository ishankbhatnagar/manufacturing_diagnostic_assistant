const API_BASE = import.meta.env.VITE_API_BASE as string;

export interface Ticket {
  ticket_id: string;
  status: string;
  created_at: string;
  symptom_report: string;
  ai_notes: string;
  retrieved_context: string;
  related_fault_mode_ids: string[];
}

export async function askTechnician(
  query: string,
  file: File | null,
): Promise<{ answer: string; conversation_id: string }> {
  const form = new FormData();
  form.set("query", query);
  if (file) form.set("file", file);

  const res = await fetch(`${API_BASE}/api/chat`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getOpenTickets(): Promise<Ticket[]> {
  const res = await fetch(`${API_BASE}/api/tickets`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function resolveTicket(
  ticketId: string,
  payload: { expert_answer: string; fault_mode_id: string; expert_name: string },
): Promise<{ fault_mode_id: string | null; reindexed: boolean }> {
  const res = await fetch(`${API_BASE}/api/tickets/${ticketId}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
