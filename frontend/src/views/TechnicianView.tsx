import { useState } from "react";
import { askTechnician } from "../api";

const ESCALATE_PREFIX = "This has been escalated to a human expert to review.";

export default function TechnicianView() {
  const [query, setQuery] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      const result = await askTechnician(query, file);
      setAnswer(result.answer);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  const escalated = answer?.startsWith(ESCALATE_PREFIX) ?? false;

  return (
    <div className="view">
      <h2>Report a symptom</h2>
      <form onSubmit={handleSubmit} className="form">
        <label htmlFor="symptom">Describe what you're seeing</label>
        <textarea
          id="symptom"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. Getting E003 on the drive at startup"
          rows={4}
          disabled={loading}
        />
        <label htmlFor="photo">Photo of a gauge / display / part (optional)</label>
        <input
          id="photo"
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !query.trim()}>
          {loading ? "Diagnosing..." : "Submit"}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {answer && (
        <div className={escalated ? "answer answer-escalated" : "answer answer-confident"}>
          <div className="answer-label">
            {escalated ? "Escalated to a human expert" : "Diagnosis"}
          </div>
          <p>{answer}</p>
        </div>
      )}
    </div>
  );
}
