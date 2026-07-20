import { useEffect, useState } from "react";
import { getOpenTickets, resolveTicket, type Ticket } from "../api";

function TicketCard({ ticket, onResolved }: { ticket: Ticket; onResolved: (id: string) => void }) {
  const [expanded, setExpanded] = useState(false);
  const [expertAnswer, setExpertAnswer] = useState("");
  const [faultModeId, setFaultModeId] = useState("");
  const [expertName, setExpertName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleResolve(e: React.FormEvent) {
    e.preventDefault();
    if (!expertAnswer.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await resolveTicket(ticket.ticket_id, {
        expert_answer: expertAnswer,
        fault_mode_id: faultModeId,
        expert_name: expertName,
      });
      onResolved(ticket.ticket_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="ticket-card">
      <div className="ticket-header" onClick={() => setExpanded((v) => !v)}>
        <span className="ticket-id">{ticket.ticket_id}</span>
        <span className="ticket-date">{new Date(ticket.created_at).toLocaleString()}</span>
      </div>
      <p className="ticket-symptom">{ticket.symptom_report}</p>
      {ticket.related_fault_mode_ids.length > 0 && (
        <p className="ticket-related">
          Related fault modes: {ticket.related_fault_mode_ids.join(", ")}
        </p>
      )}

      {expanded && (
        <>
          {ticket.ai_notes && (
            <div className="ticket-detail">
              <strong>AI notes:</strong> {ticket.ai_notes}
            </div>
          )}
          <form onSubmit={handleResolve} className="form">
            <label>Expert answer</label>
            <textarea
              value={expertAnswer}
              onChange={(e) => setExpertAnswer(e.target.value)}
              rows={3}
              placeholder="Diagnosis and fix, in your own words"
              disabled={submitting}
            />
            <div className="form-row">
              <div>
                <label>Fault mode ID (optional)</label>
                <input
                  value={faultModeId}
                  onChange={(e) => setFaultModeId(e.target.value)}
                  placeholder="e.g. GBX-01"
                  disabled={submitting}
                />
              </div>
              <div>
                <label>Your name (optional)</label>
                <input
                  value={expertName}
                  onChange={(e) => setExpertName(e.target.value)}
                  disabled={submitting}
                />
              </div>
            </div>
            <button type="submit" disabled={submitting || !expertAnswer.trim()}>
              {submitting ? "Submitting..." : "Resolve & capture to knowledge base"}
            </button>
          </form>
          {error && <div className="error">{error}</div>}
        </>
      )}
    </div>
  );
}

export default function ExpertView() {
  const [tickets, setTickets] = useState<Ticket[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [justResolved, setJustResolved] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      setTickets(await getOpenTickets());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    load();
  }, []);

  function handleResolved(ticketId: string) {
    setTickets((prev) => prev?.filter((t) => t.ticket_id !== ticketId) ?? null);
    setJustResolved(ticketId);
  }

  return (
    <div className="view">
      <h2>Open escalations</h2>
      <button type="button" className="refresh" onClick={load}>
        Refresh
      </button>

      {error && <div className="error">{error}</div>}
      {justResolved && (
        <div className="success">
          Resolved {justResolved} and captured to the knowledge base -- future matching symptoms
          will now be answered directly instead of escalating.
        </div>
      )}

      {tickets === null && <p>Loading...</p>}
      {tickets?.length === 0 && <p>No open tickets.</p>}
      {tickets?.map((t) => (
        <TicketCard key={t.ticket_id} ticket={t} onResolved={handleResolved} />
      ))}
    </div>
  );
}
