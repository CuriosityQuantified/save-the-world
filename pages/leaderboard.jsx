import React, { useState, useEffect, useCallback } from "react";
import Head from "next/head";

const BACKEND_DEFAULT = "http://localhost:8000";
const LIMITS = [10, 25, 100];
const PERIODS = [
  { value: "all-time", label: "All Time" },
  { value: "weekly", label: "This Week" },
  { value: "daily", label: "Today" },
];

const RANK_COLORS = ["#ffd700", "#c0c0c0", "#cd7f32"];

function RankBadge({ rank }) {
  const color = rank <= 3 ? RANK_COLORS[rank - 1] : "#6b7280";
  return (
    <span
      data-testid={`rank-badge-${rank}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: 32,
        height: 32,
        borderRadius: "50%",
        background: rank <= 3 ? color : "transparent",
        border: rank > 3 ? `1px solid ${color}` : "none",
        color: rank <= 3 ? "#000" : color,
        fontWeight: 700,
        fontSize: 13,
      }}
    >
      {rank}
    </span>
  );
}

function LeaderboardRow({ entry, isHighlighted }) {
  return (
    <tr
      data-testid={`leaderboard-row-${entry.rank}`}
      style={{
        background: isHighlighted ? "rgba(167,139,250,0.15)" : entry.rank % 2 === 0 ? "rgba(255,255,255,0.02)" : "transparent",
        borderLeft: isHighlighted ? "3px solid #a78bfa" : "3px solid transparent",
      }}
    >
      <td style={{ padding: "12px 16px", textAlign: "center", width: 56 }}>
        <RankBadge rank={entry.rank} />
      </td>
      <td style={{ padding: "12px 16px", color: "#e5e7eb", fontWeight: entry.rank <= 3 ? 600 : 400 }}>
        {entry.player_name || <span style={{ color: "#6b7280", fontStyle: "italic" }}>Anonymous</span>}
      </td>
      <td
        data-testid={`score-${entry.rank}`}
        style={{ padding: "12px 16px", textAlign: "right", color: "#a78bfa", fontWeight: 700, fontSize: 18 }}
      >
        {entry.score.toLocaleString()}
      </td>
      <td style={{ padding: "12px 16px", textAlign: "right", color: "#6b7280", fontSize: 12 }}>
        {new Date(entry.created_at).toLocaleDateString()}
      </td>
    </tr>
  );
}

export default function LeaderboardPage() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [period, setPeriod] = useState("all-time");
  const [limit, setLimit] = useState(10);
  const [backendUrl, setBackendUrl] = useState(BACKEND_DEFAULT);
  const [playerRank, setPlayerRank] = useState(null);
  const [simId, setSimId] = useState("");
  const [rankLoading, setRankLoading] = useState(false);

  useEffect(() => {
    async function discoverBackend() {
      try {
        const res = await fetch("/api/backend-port");
        if (res.ok) {
          const { port } = await res.json();
          setBackendUrl(`http://localhost:${port}`);
        }
      } catch (_) {}
    }
    discoverBackend();
  }, []);

  const fetchLeaderboard = useCallback(async () => {
    if (!backendUrl) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${backendUrl}/api/leaderboard?period=${period}&limit=${limit}`);
      if (!res.ok) throw new Error("Failed to load leaderboard");
      setEntries(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [backendUrl, period, limit]);

  useEffect(() => {
    fetchLeaderboard();
  }, [fetchLeaderboard]);

  async function handleLookupRank() {
    if (!simId.trim()) return;
    setRankLoading(true);
    setPlayerRank(null);
    try {
      const res = await fetch(`${backendUrl}/api/leaderboard/rank/${encodeURIComponent(simId)}?period=${period}`);
      if (res.status === 404) {
        setPlayerRank({ notFound: true });
      } else if (!res.ok) {
        throw new Error("Failed to fetch rank");
      } else {
        setPlayerRank(await res.json());
      }
    } catch (e) {
      setPlayerRank({ error: e.message });
    } finally {
      setRankLoading(false);
    }
  }

  const pageStyle = {
    minHeight: "100vh",
    background: "#0f0f1a",
    color: "#e5e7eb",
    fontFamily: "system-ui, -apple-system, sans-serif",
    padding: "40px 32px",
  };

  return (
    <>
      <Head>
        <title>Leaderboard — Save the World</title>
      </Head>
      <div style={pageStyle}>
        <div style={{ maxWidth: 780, margin: "0 auto" }}>

          {/* Header */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 32 }}>
            <div>
              <h1 data-testid="leaderboard-heading" style={{ margin: 0, fontSize: 28, fontWeight: 700 }}>
                Leaderboard
              </h1>
              <p style={{ margin: "6px 0 0", color: "#9ca3af", fontSize: 14 }}>
                Top scores — can you save the world?
              </p>
            </div>
          </div>

          {/* Filters */}
          <div
            data-testid="filter-bar"
            style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 24 }}
          >
            <div>
              <label style={{ fontSize: 12, color: "#9ca3af", display: "block", marginBottom: 4 }}>Period</label>
              <div style={{ display: "flex", gap: 6 }}>
                {PERIODS.map((p) => (
                  <button
                    key={p.value}
                    data-testid={`period-${p.value}`}
                    onClick={() => setPeriod(p.value)}
                    style={{
                      padding: "6px 14px",
                      borderRadius: 6,
                      border: "1px solid",
                      borderColor: period === p.value ? "#6366f1" : "#333",
                      background: period === p.value ? "#6366f1" : "transparent",
                      color: period === p.value ? "#fff" : "#9ca3af",
                      cursor: "pointer",
                      fontSize: 13,
                    }}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label style={{ fontSize: 12, color: "#9ca3af", display: "block", marginBottom: 4 }}>Show</label>
              <div style={{ display: "flex", gap: 6 }}>
                {LIMITS.map((l) => (
                  <button
                    key={l}
                    data-testid={`limit-${l}`}
                    onClick={() => setLimit(l)}
                    style={{
                      padding: "6px 14px",
                      borderRadius: 6,
                      border: "1px solid",
                      borderColor: limit === l ? "#6366f1" : "#333",
                      background: limit === l ? "#6366f1" : "transparent",
                      color: limit === l ? "#fff" : "#9ca3af",
                      cursor: "pointer",
                      fontSize: 13,
                    }}
                  >
                    Top {l}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Leaderboard table */}
          {loading && <p style={{ color: "#9ca3af" }}>Loading leaderboard…</p>}
          {error && <p style={{ color: "#ef4444" }}>Error: {error}</p>}

          {!loading && !error && (
            <div
              data-testid="leaderboard-table-container"
              style={{ background: "#1a1a2e", border: "1px solid #333", borderRadius: 8, overflow: "hidden" }}
            >
              {entries.length === 0 ? (
                <p
                  data-testid="empty-state"
                  style={{ color: "#6b7280", textAlign: "center", padding: "40px 20px" }}
                >
                  No scores yet for this period. Be the first to save the world!
                </p>
              ) : (
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid #333" }}>
                      <th style={{ padding: "10px 16px", color: "#9ca3af", fontSize: 12, textAlign: "center", width: 56 }}>#</th>
                      <th style={{ padding: "10px 16px", color: "#9ca3af", fontSize: 12, textAlign: "left" }}>Player</th>
                      <th style={{ padding: "10px 16px", color: "#9ca3af", fontSize: 12, textAlign: "right" }}>Score</th>
                      <th style={{ padding: "10px 16px", color: "#9ca3af", fontSize: 12, textAlign: "right" }}>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {entries.map((entry) => (
                      <LeaderboardRow
                        key={entry.simulation_id}
                        entry={entry}
                        isHighlighted={entry.simulation_id === simId}
                      />
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* Rank lookup */}
          <div
            data-testid="rank-lookup"
            style={{
              marginTop: 32,
              background: "#1a1a2e",
              border: "1px solid #333",
              borderRadius: 8,
              padding: "20px 24px",
            }}
          >
            <h2 style={{ margin: "0 0 14px", fontSize: 16, fontWeight: 600 }}>Find Your Rank</h2>
            <div style={{ display: "flex", gap: 10 }}>
              <input
                data-testid="sim-id-input"
                type="text"
                value={simId}
                onChange={(e) => setSimId(e.target.value)}
                placeholder="Enter your simulation ID"
                style={{
                  flex: 1,
                  background: "#0f0f1a",
                  border: "1px solid #444",
                  borderRadius: 6,
                  padding: "8px 12px",
                  color: "#e5e7eb",
                  fontSize: 14,
                  outline: "none",
                }}
                onKeyDown={(e) => e.key === "Enter" && handleLookupRank()}
              />
              <button
                data-testid="lookup-rank-btn"
                onClick={handleLookupRank}
                disabled={rankLoading || !simId.trim()}
                style={{
                  background: "#6366f1",
                  color: "#fff",
                  border: "none",
                  borderRadius: 6,
                  padding: "8px 18px",
                  cursor: simId.trim() ? "pointer" : "not-allowed",
                  opacity: simId.trim() ? 1 : 0.5,
                  fontSize: 14,
                  fontWeight: 600,
                }}
              >
                {rankLoading ? "…" : "Look Up"}
              </button>
            </div>

            {playerRank && !playerRank.notFound && !playerRank.error && (
              <div
                data-testid="rank-result"
                style={{ marginTop: 16, padding: "14px", background: "rgba(99,102,241,0.1)", borderRadius: 6 }}
              >
                <span style={{ color: "#a78bfa", fontWeight: 700, fontSize: 18 }}>
                  #{playerRank.rank}
                </span>
                <span style={{ color: "#9ca3af", marginLeft: 10, fontSize: 14 }}>
                  {playerRank.player_name || "Anonymous"} — Score: {playerRank.score} — out of {playerRank.total_entries} entries
                </span>
              </div>
            )}
            {playerRank?.notFound && (
              <p data-testid="rank-not-found" style={{ color: "#6b7280", marginTop: 12, fontSize: 14 }}>
                No leaderboard entry found for that simulation ID.
              </p>
            )}
            {playerRank?.error && (
              <p style={{ color: "#ef4444", marginTop: 12, fontSize: 14 }}>Error: {playerRank.error}</p>
            )}
          </div>

          {/* Nav links */}
          <div style={{ marginTop: 24, display: "flex", gap: 16 }}>
            <a href="/" style={{ color: "#6366f1", fontSize: 13 }}>← Back to Simulation</a>
            <a href="/analytics" style={{ color: "#6366f1", fontSize: 13 }}>Analytics Dashboard</a>
          </div>
        </div>
      </div>
    </>
  );
}
