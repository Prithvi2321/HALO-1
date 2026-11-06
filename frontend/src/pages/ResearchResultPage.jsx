/**
 * src/pages/ResearchResultPage.jsx
 * ──────────────────────────────────
 * Evidence-first AI answer view for a single research result.
 * Reads :queryId from the URL param, fetches via getResearchResult(),
 * renders claims with verification badges, sources panel, confidence
 * metrics, warnings, and conflict banner.
 *
 * API swap: replace getResearchResult() body in researchApi.js only.
 * Never edit this file to change data source.
 */

import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { getResearchResult } from "../api/researchApi";
import AppShell from "../components/AppShell";
import PageHeader from "../components/PageHeader";
import StatusBadge from "../components/StatusBadge";
import "./ResearchResultPage.css";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function confidenceColor(score) {
  if (score >= 0.8) return "bar-green";
  if (score >= 0.55) return "bar-amber";
  return "bar-red";
}

function confidenceLabel(score) {
  if (score >= 0.8) return "High";
  if (score >= 0.55) return "Medium";
  return "Low";
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────

function Skeleton() {
  return (
    <AppShell user={null}>
      <div className="rrp-page">
        <div className="rrp-topbar">
          <div className="sk-line sk-back"   aria-hidden="true" />
          <div className="sk-line sk-query"  aria-hidden="true" />
          <div className="sk-line sk-verify" aria-hidden="true" />
        </div>
        <div className="rrp-body">
          <div className="rrp-left">
            <div className="sk-line sk-heading" aria-hidden="true" />
            <div className="sk-line sk-para" aria-hidden="true" />
            <div className="sk-line sk-para sk-para-short" aria-hidden="true" />
            <div className="sk-line sk-para" aria-hidden="true" />
            <div className="sk-claim-block" aria-hidden="true">
              <div className="sk-line sk-para" />
              <div className="sk-line sk-badge" />
            </div>
            <div className="sk-claim-block" aria-hidden="true">
              <div className="sk-line sk-para" />
              <div className="sk-line sk-badge" />
            </div>
          </div>
          <div className="rrp-right">
            <div className="sk-line sk-heading" aria-hidden="true" />
            {[1, 2, 3].map((i) => (
              <div key={i} className="sk-source-card" aria-hidden="true">
                <div className="sk-line sk-para" />
                <div className="sk-line sk-meta" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}

// ─── Error state ──────────────────────────────────────────────────────────────

function ErrorState({ queryId }) {
  return (
    <AppShell user={null}>
      <div className="rrp-page">
        <div className="rrp-error-box">
          <div className="rrp-error-icon">⚠</div>
          <h2>Result not found</h2>
          <p>
            No research result exists for query ID <code>{queryId}</code>.
            It may have expired or been entered incorrectly.
          </p>
          <Link to="/research" className="btn rrp-back-btn">
            ← Back to Research
          </Link>
        </div>
      </div>
    </AppShell>
  );
}

// ─── Metric bar ───────────────────────────────────────────────────────────────

function MetricBar({ label, score }) {
  const pct = Math.round(score * 100);
  const colorCls = confidenceColor(score);
  const levelLabel = confidenceLabel(score);

  return (
    <div className="metric-bar-row">
      <div className="metric-bar-header">
        <span className="metric-bar-label">{label}</span>
        <span className={`metric-bar-value ${colorCls}`}>
          {pct}% — {levelLabel}
        </span>
      </div>
      <div className="metric-bar-track">
        <div
          className={`metric-bar-fill ${colorCls}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ─── Claim block ──────────────────────────────────────────────────────────────

function ClaimBlock({ claim, queryId }) {
  const navigate = useNavigate();
  const { claim_text, verification_status, citation, claim_id } = claim;

  return (
    <div
      className={`claim-block claim-block--${verification_status}`}
      style={{ cursor: "pointer" }}
      onClick={() => navigate(`/research/${queryId}/evidence?claimId=${claim_id}`)}
      title="Click to inspect authoritative evidence and exact passage anchor"
    >
      <div className="claim-block-header">
        <StatusBadge status={verification_status} />
        {citation && (
          <span className="claim-citation-pill">
            {citation.case_name} · {citation.citation_no}
          </span>
        )}
        <span className="claim-inspect-hint">
          Inspect Passage &rarr;
        </span>
      </div>
      <p className="claim-text">{claim_text}</p>
      {citation?.paragraph && (
        <span className="claim-para-ref">{citation.paragraph}</span>
      )}
    </div>
  );
}

// ─── Source card ──────────────────────────────────────────────────────────────

function SourceCard({ source, index, queryId }) {
  const navigate = useNavigate();
  const relevancePct = Math.round((source.relevance ?? 0) * 100);
  const colorCls = confidenceColor(source.relevance ?? 0);

  return (
    <div className="source-card">
      <div className="source-card-top">
        <span className="source-index">{index + 1}</span>
        <div className="source-info">
          <p className="source-title">{source.title}</p>
          <p className="source-meta">
            {source.court} · {source.year}
          </p>
        </div>
      </div>
      <div className="source-card-footer">
        <div className="source-relevance-mini">
          <div className="source-relevance-track">
            <div
              className={`source-relevance-fill ${colorCls}`}
              style={{ width: `${relevancePct}%` }}
            />
          </div>
          <span className={`source-relevance-label ${colorCls}`}>
            {relevancePct}%
          </span>
        </div>
        <button
          className="btn btn-outline source-view-btn"
          id={`view-source-${source.id}`}
          onClick={() => navigate(`/research/${queryId}/evidence`)}
          title="Inspect authoritative legal source passage"
        >
          View Source
        </button>
      </div>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function ResearchResultPage() {
  const { queryId } = useParams();
  const navigate    = useNavigate();

  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);
    setResult(null);

    getResearchResult(queryId)
      .then((data) => { if (!cancelled) setResult(data); })
      .catch(()    => { if (!cancelled) setError(true);  })
      .finally(()  => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [queryId]);

  if (loading) return <Skeleton />;
  if (error || !result) return <ErrorState queryId={queryId} />;

  const {
    answer_text,
    claims,
    sources,
    confidence_score,
    evidence_coverage,
    warnings,
    conflicts_detected,
    temporal_context,
    corpus_version,
    model_version,
    verification_timestamp,
  } = result;

  // Derive a "query text" label from the mock history if available;
  // fall back to a styled query ID display
  const queryLabel = `Query: ${queryId}`;

  // Deduplicate sources by id
  const uniqueSources = sources.reduce((acc, s) => {
    if (!acc.find((x) => x.id === s.id)) acc.push(s);
    return acc;
  }, []);

  // Split answer_text into paragraphs
  const paragraphs = answer_text.split(/\n\n+/).filter(Boolean);

  const overallStatus = conflicts_detected
    ? "conflict"
    : confidence_score >= 0.8
    ? "clean"
    : confidence_score >= 0.55
    ? "mixed"
    : "weak";

  return (
    <AppShell user={null}>
      <div className="rrp-page">

        {/* ── Page Header ── */}
        <PageHeader title="Research Result" />

        {/* ── Top bar ──────────────────────────────────────────────────── */}
        <div className="rrp-topbar">
          <button
            className="btn btn-ghost rrp-back-btn"
            onClick={() => navigate("/research")}
            id="back-to-results-btn"
          >
            ← Back to Results
          </button>

          <div className="rrp-topbar-center">
            <span className="rrp-query-label">{queryLabel}</span>
            <StatusBadge
              status={overallStatus}
              label={
                conflicts_detected
                  ? "Conflicts Detected"
                  : `${confidenceLabel(confidence_score)} Confidence`
              }
            />
          </div>

          <div className="rrp-topbar-actions">
            <Link
              to={`/research/${queryId}/evidence`}
              className="btn btn-secondary"
              id="view-evidence-btn"
            >
              Inspect Evidence &rarr;
            </Link>
            {conflicts_detected && (
              <Link
                to={`/research/${queryId}/conflict`}
                className="btn btn-outline"
                id="inspect-conflict-btn"
              >
                ⚡ Conflict View
              </Link>
            )}
            <Link
              to={`/research/${queryId}/verify`}
              className="btn btn-primary"
              id="verify-all-claims-btn"
            >
              Verify All Claims &rarr;
            </Link>
          </div>
        </div>

        {/* ── Conflict banner ───────────────────────────────────────────── */}
        {conflicts_detected && (
          <div className="conflict-banner" role="alert" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
              <span className="conflict-banner-icon">⚠</span>
              <div>
                <strong>Conflicting authorities detected</strong>
                <p>
                  This result contains claims from sources that contradict each
                  other. Review each claim carefully before relying on this
                  analysis.
                </p>
              </div>
            </div>
            <Link
              to={`/research/${queryId}/conflict`}
              className="btn btn-outline"
              style={{ whiteSpace: "nowrap", marginLeft: "1rem" }}
            >
              Inspect Conflict View &rarr;
            </Link>
          </div>
        )}

        {/* ── Low-confidence banner ─────────────────────────────────────── */}
        {!conflicts_detected && confidence_score < 0.55 && (
          <div className="low-conf-banner" role="alert">
            <span>⚠</span>
            <div>
              <strong>Low confidence result</strong>
              <p>
                The AI's confidence in this answer is{" "}
                {Math.round(confidence_score * 100)}%. Several claims could not
                be fully verified. Treat with caution.
              </p>
            </div>
          </div>
        )}

        {/* ── Main two-column body ──────────────────────────────────────── */}
        <div className="rrp-body">

          {/* LEFT — Answer + Claims */}
          <div className="rrp-left">
            <h2 className="rrp-section-heading">AI-Generated Answer</h2>

            <div className="rrp-answer-prose markdown-prose">
              <ReactMarkdown>
                {answer_text}
              </ReactMarkdown>
            </div>

            {claims.length > 0 && (
              <>
                <h3 className="rrp-claims-heading">
                  Verified Claims ({claims.length})
                </h3>
                <div className="rrp-claims-list">
                  {claims.map((claim) => (
                    <ClaimBlock key={claim.claim_id} claim={claim} queryId={queryId} />
                  ))}
                </div>
              </>
            )}
          </div>

          {/* RIGHT — Sources & Evidence */}
          <aside className="rrp-right">
            <div className="rrp-sources-panel">
              <h2 className="rrp-section-heading">
                Sources &amp; Evidence
                <span className="sources-count-chip">{uniqueSources.length}</span>
              </h2>

              <div className="rrp-sources-list">
                {uniqueSources.map((src, i) => (
                  <SourceCard key={src.id} source={src} index={i} queryId={queryId} />
                ))}
              </div>
            </div>

            {/* ── Confidence metrics ───────────────────────────────────── */}
            <div className="rrp-metrics-panel">
              <h2 className="rrp-section-heading">Confidence Metrics</h2>
              <MetricBar label="Confidence Score"   score={confidence_score}   />
              <MetricBar label="Evidence Coverage"  score={evidence_coverage}  />
            </div>

            {/* ── Warnings ─────────────────────────────────────────────── */}
            {warnings.length > 0 && (
              <div className="rrp-warnings-panel">
                <h3 className="rrp-warnings-heading">⚠ Warnings</h3>
                <ul className="rrp-warnings-list">
                  {warnings.map((w, i) => (
                    <li key={i} className="rrp-warning-item">{w}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* ── Temporal context ─────────────────────────────────────── */}
            {temporal_context && (
              <div className="rrp-temporal-panel">
                <span className="rrp-temporal-icon">🕐</span>
                <p className="rrp-temporal-text">{temporal_context}</p>
              </div>
            )}

            {/* ── Corpus metadata ──────────────────────────────────────── */}
            <div className="rrp-meta-panel">
              <dl className="rrp-meta-dl">
                {corpus_version && (
                  <>
                    <dt>Corpus</dt>
                    <dd>{corpus_version}</dd>
                  </>
                )}
                {model_version && (
                  <>
                    <dt>Model</dt>
                    <dd>{model_version}</dd>
                  </>
                )}
                {verification_timestamp && (
                  <>
                    <dt>Verified</dt>
                    <dd>
                      {new Date(verification_timestamp).toLocaleString("en-IN", {
                        dateStyle: "medium",
                        timeStyle: "short",
                      })}
                    </dd>
                  </>
                )}
              </dl>
            </div>
          </aside>

        </div>
      </div>
    </AppShell>
  );
}
