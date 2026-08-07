import React, { useState, useEffect } from "react";
import Head from "next/head";

const BACKEND_DEFAULT = "http://localhost:8000";

function MetricCard({ label, value, testId }) {
  return (
    <div
      data-testid={testId}
      style={{
        background: "#1a1a2e", border: "1px solid #333", borderRadius: 8,
        padding: "20px 24px", minWidth: 160, textAlign: "center",
      }}
    >
      <div data-testid={testId && `${testId}-value`} style={{ fontSize: 28, fontWeight: 700, color: "#a78bfa" }}>{value}</div>
      <div style={{ fontSize: 13, color: "#9ca3af", marginTop: 6 }}>{label}</div>
    </div>
  );
}

function TrendChart({ trends }) {
  if (!trends || trends.length === 0) {
    return <p style={{ color: "#6b7280" }}>No trend data yet.</p>;
  }

  const maxStarted = Math.max(...trends.map(t => t.simulations_started), 1);
  const barWidth = Math.min(60, Math.floor(560 / trends.length) - 8);
  const chartH = 160;

  return (
    <div style={{ overflowX: "auto" }}>
      <svg
        aria-label="Simulations trend chart"
        width={Math.max(600, trends.length * (barWidth + 8) + 40)}
        height={chartH + 60}
        style={{ display: "block" }}
      >
        {trends.map((t, i) => {
          const startedH = Math.max(4, Math.round((t.simulations_started / maxStarted) * chartH));
          const completedH = Math.max(
            t.simulations_completed > 0 ? 4 : 0,
            Math.round((t.simulations_completed / maxStarted) * chartH),
          );
          const x = 20 + i * (barWidth + 8);
          return (
            <g key={t.date}>
              <rect
                x={x} y={chartH - startedH}
                width={barWidth} height={startedH}
                fill="#6366f1" rx={3}
                aria-label={`${t.date}: ${t.simulations_started} started`}
              />
              <rect
                x={x} y={chartH - completedH}
                width={barWidth} height={completedH}
                fill="#a78bfa" rx={3}
                aria-label={`${t.date}: ${t.simulations_completed} completed`}
              />
              <text
                x={x + barWidth / 2} y={chartH + 16}
                textAnchor="middle" fontSize={10} fill="#9ca3af"
              >
                {t.date.slice(5)}
              </text>
              <text
                x={x + barWidth / 2} y={chartH - startedH - 4}
                textAnchor="middle" fontSize={10} fill="#e5e7eb"
              >
                {t.simulations_started}
              </text>
            </g>
          );
        })}
      </svg>
      <div style={{ display: "flex", gap: 16, marginTop: 8, fontSize: 12, color: "#9ca3af" }}>
        <span><span style={{ background: "#6366f1", display: "inline-block", width: 12, height: 12, borderRadius: 2, marginRight: 4 }} />Started</span>
        <span><span style={{ background: "#a78bfa", display: "inline-block", width: 12, height: 12, borderRadius: 2, marginRight: 4 }} />Completed</span>
      </div>
    </div>
  );
}

export default function AnalyticsDashboard() {
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [backendUrl, setBackendUrl] = useState(BACKEND_DEFAULT);

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

  useEffect(() => {
    if (!backendUrl) return;
    async function fetchAnalytics() {
      setLoading(true);
      setError(null);
      try {
        const [sumRes, trendRes] = await Promise.all([
          fetch(`${backendUrl}/api/analytics/summary`),
          fetch(`${backendUrl}/api/analytics/trends`),
        ]);
        if (!sumRes.ok || !trendRes.ok) throw new Error("Failed to load analytics");
        const [sumData, trendData] = await Promise.all([sumRes.json(), trendRes.json()]);
        setSummary(sumData);
        setTrends(trendData);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }
    fetchAnalytics();
  }, [backendUrl]);

  function handleExport() {
    window.location.href = `${backendUrl}/api/analytics/export`;
  }

  const pageStyle = {
    minHeight: "100vh", background: "#0f0f1a", color: "#e5e7eb",
    fontFamily: "system-ui, -apple-system, sans-serif", padding: "40px 32px",
  };

  return (
    <>
      <Head>
        <title>Analytics — Save the World</title>
      </Head>
      <div style={pageStyle}>
        <div style={{ maxWidth: 860, margin: "0 auto" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
            <div>
              <h1 style={{ margin: 0, fontSize: 28, fontWeight: 700 }}>Analytics Dashboard</h1>
              <p style={{ margin: "6px 0 0", color: "#9ca3af", fontSize: 14 }}>
                Simulation engagement metrics
              </p>
            </div>
            <button
              onClick={handleExport}
              data-testid="export-csv-btn"
              style={{
                background: "#6366f1", color: "#fff", border: "none",
                borderRadius: 6, padding: "10px 20px", cursor: "pointer",
                fontSize: 14, fontWeight: 600,
              }}
            >
              Export CSV
            </button>
          </div>

          {loading && <p style={{ color: "#9ca3af" }}>Loading analytics…</p>}
          {error && <p style={{ color: "#ef4444" }}>Error: {error}</p>}

          {summary && (
            <>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 16, marginBottom: 40 }}>
                <MetricCard label="Total Simulations" value={summary.total_simulations} testId="metric-total" />
                <MetricCard label="Completed" value={summary.completed_simulations} testId="metric-completed" />
                <MetricCard label="Completion Rate" value={`${summary.completion_rate}%`} testId="metric-completion-rate" />
                <MetricCard label="Avg Turns" value={summary.avg_turns_per_simulation} testId="metric-avg-turns" />
                <MetricCard label="Total Responses" value={summary.total_user_responses} testId="metric-total-responses" />
                <MetricCard label="Avg Response Length" value={`${summary.avg_response_length} chars`} testId="metric-avg-length" />
              </div>

              <div style={{
                background: "#1a1a2e", border: "1px solid #333", borderRadius: 8, padding: "24px",
              }}>
                <h2 style={{ margin: "0 0 20px", fontSize: 18, fontWeight: 600 }}>Trends Over Time</h2>
                <TrendChart trends={trends} />
              </div>
            </>
          )}

          <div style={{ marginTop: 24 }}>
            <a href="/" style={{ color: "#6366f1", fontSize: 13 }}>← Back to Simulation</a>
          </div>
        </div>
      </div>
    </>
  );
}
