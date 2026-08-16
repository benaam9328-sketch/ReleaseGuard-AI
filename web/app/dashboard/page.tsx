"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Assessment = {
  release_id: string;
  risk_score: number;
  risk_level: string;
  recommendation: string;
  enforcement: string;
  signals: { signal: string; weight: number; evidence: string }[];
  evidence_summary: Record<string, string | null>;
  dora_context?: {
    snapshot?: {
      includes_synthetic?: boolean;
      window?: {
        deployment_frequency?: { unavailable: boolean; value: number | null; event_count: number | null };
        lead_time_for_changes?: { unavailable: boolean; value: number | null };
        change_failure_rate?: { unavailable: boolean; value: number | null };
        time_to_restore_service?: { unavailable: boolean; value: number | null };
      };
    };
  };
  ai_explanation?: { status: string; text: string | null };
  approval?: { state: string; decision: string | null };
};

type Evidence = {
  release_id: string;
  history?: { similar_historical_failure?: boolean | null; is_synthetic?: boolean; matched_record_ids?: string[] | null };
  missing_sources?: string[];
};

function formatMetric(metric?: { unavailable: boolean; value: number | null; event_count?: number | null }, unit = "") {
  if (!metric || metric.unavailable || metric.value === null) {
    return "unavailable";
  }
  const count = metric.event_count != null ? ` (${metric.event_count} events)` : "";
  return `${metric.value}${unit}${count}`;
}

export default function DashboardPage() {
  const [releaseId, setReleaseId] = useState("REL-001");
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load(id: string) {
    setError("");
    const scored = await fetch(`${API}/v1/releases/${id}/assessment`);
    if (!scored.ok) {
      setAssessment(null);
      setEvidence(null);
      setError("Release not found. Load a demo release first.");
      return;
    }
    const body = (await scored.json()) as Assessment;
    setAssessment(body);
    const raw = await fetch(`${API}/v1/releases/${id}`);
    if (raw.ok) {
      setEvidence(await raw.json());
    }
  }

  async function loadDemo() {
    setBusy(true);
    setError("");
    try {
      const created = await fetch(`${API}/v1/releases`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          release_id: releaseId || "REL-001",
          repository: "releaseguard-ai",
          commit_sha: "abc123def456",
          ci_status: "success",
          test_status: "success",
          critical_vulnerabilities: 0,
          high_vulnerabilities: 2,
        }),
      });
      if (!created.ok) {
        setError("Could not create demo release. Is the API running on port 8000?");
        return;
      }
      await load(releaseId || "REL-001");
    } finally {
      setBusy(false);
    }
  }

  async function decide(decision: "approve" | "reject") {
    if (!assessment) {
      return;
    }
    setBusy(true);
    try {
      const response = await fetch(`${API}/v1/releases/${assessment.release_id}/approval`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision }),
      });
      if (response.ok) {
        setAssessment(await response.json());
      }
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    fetch(`${API}/v1/releases`)
      .then((response) => (response.ok ? response.json() : []))
      .then((rows: Evidence[]) => {
        if (rows[0]?.release_id) {
          setReleaseId(rows[0].release_id);
          return load(rows[0].release_id);
        }
      })
      .catch(() => setError("API is not reachable at " + API));
  }, []);

  const dora = assessment?.dora_context?.snapshot?.window;

  return (
    <main className="mx-auto max-w-5xl px-6 py-8">
      <h1 className="text-2xl font-semibold">ReleaseGuard dashboard</h1>
      <p className="mt-1 text-sm text-slate-600">
        DORA is delivery performance. It is not the risk score.
      </p>

      <div className="mt-6 flex flex-wrap gap-2">
        <input
          className="rounded border border-slate-300 px-3 py-2"
          value={releaseId}
          onChange={(event) => setReleaseId(event.target.value)}
        />
        <button
          className="rounded bg-slate-900 px-4 py-2 text-white"
          onClick={() => load(releaseId)}
          disabled={busy}
        >
          Load
        </button>
        <button
          className="rounded border border-slate-300 px-4 py-2"
          onClick={loadDemo}
          disabled={busy}
        >
          Create demo release
        </button>
      </div>

      {error ? <p className="mt-4 text-sm text-red-700">{error}</p> : null}

      {assessment ? (
        <div className="mt-8 grid gap-4 md:grid-cols-2">
          <section className="rounded-lg bg-white p-4 shadow-sm">
            <h2 className="font-medium">Current release risk</h2>
            <p className="mt-2 text-3xl font-semibold">{assessment.risk_score}</p>
            <p className="text-sm">
              {assessment.risk_level} · {assessment.recommendation}
            </p>
            <p className="mt-1 text-xs text-slate-500">enforcement: {assessment.enforcement}</p>
          </section>

          <section className="rounded-lg bg-white p-4 shadow-sm">
            <h2 className="font-medium">Approval</h2>
            <p className="mt-2 text-sm">State: {assessment.approval?.state || "pending"}</p>
            <div className="mt-3 flex gap-2">
              <button
                className="rounded bg-emerald-700 px-4 py-2 text-white"
                onClick={() => decide("approve")}
                disabled={busy}
              >
                Approve
              </button>
              <button
                className="rounded bg-red-700 px-4 py-2 text-white"
                onClick={() => decide("reject")}
                disabled={busy}
              >
                Reject
              </button>
            </div>
          </section>

          <section className="rounded-lg bg-white p-4 shadow-sm md:col-span-2">
            <h2 className="font-medium">DORA (30-day window)</h2>
            <ul className="mt-2 grid gap-2 text-sm md:grid-cols-2">
              <li>Deployment frequency: {formatMetric(dora?.deployment_frequency, " / day")}</li>
              <li>Lead time: {formatMetric(dora?.lead_time_for_changes, " hours")}</li>
              <li>Change failure rate: {formatMetric(dora?.change_failure_rate, "%")}</li>
              <li>Time to restore: {formatMetric(dora?.time_to_restore_service, " min")}</li>
            </ul>
            {assessment.dora_context?.snapshot?.includes_synthetic ? (
              <p className="mt-2 text-xs text-amber-700">Includes labeled synthetic events.</p>
            ) : null}
          </section>

          <section className="rounded-lg bg-white p-4 shadow-sm">
            <h2 className="font-medium">Findings</h2>
            <ul className="mt-2 list-disc pl-5 text-sm">
              {assessment.signals.map((item) => (
                <li key={item.signal}>
                  {item.signal} (+{item.weight}): {item.evidence}
                </li>
              ))}
            </ul>
            {evidence?.missing_sources?.length ? (
              <p className="mt-2 text-xs text-slate-500">
                Missing: {evidence.missing_sources.join(", ")}
              </p>
            ) : null}
          </section>

          <section className="rounded-lg bg-white p-4 shadow-sm">
            <h2 className="font-medium">History and AI</h2>
            <p className="mt-2 text-sm">
              Similar failure: {String(evidence?.history?.similar_historical_failure ?? "unknown")}
            </p>
            {evidence?.history?.is_synthetic ? (
              <p className="text-xs text-amber-700">Historical match is labeled synthetic.</p>
            ) : null}
            <p className="mt-3 text-sm whitespace-pre-wrap">
              {assessment.ai_explanation?.text || `AI explanation: ${assessment.ai_explanation?.status || "unknown"}`}
            </p>
          </section>
        </div>
      ) : null}
    </main>
  );
}
