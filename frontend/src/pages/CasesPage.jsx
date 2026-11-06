/**
 * src/pages/CasesPage.jsx
 * ────────────────────────
 * Case & Matter Workspace — PRD Phase 2 (Sprint 4)
 *
 * Provides legal practitioners with a case-centric legal dossier:
 * - Manage active matters, courts, and case numbers
 * - Link verified AI research queries to client matters
 * - Pin authoritative precedents and statutory sections
 * - Export structured, court-ready Legal Research Briefs
 */

import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import PageHeader from "../components/PageHeader";
import StatusBadge from "../components/StatusBadge";
import { getCurrentUser } from "../api/client";
import { getResearchHistory } from "../api/researchApi";
import { listMatters, createMatter, addMatterNote } from "../api/workspaceApi";
import "./CasesPage.css";

// ─── Initial Seed Cases ──────────────────────────────────────────────────────

const INITIAL_CASES = [
  {
    id: "case_001",
    case_number: "ITA No. 447/2022",
    title: "Steel Authority of India Ltd. v. ITO & Ors.",
    client_name: "Nominee Directors Consortium",
    court: "High Court of Delhi (Tax Division)",
    category: "Direct Taxation",
    status: "ACTIVE",
    created_date: "2024-10-12",
    last_updated: "2024-11-15",
    description:
      "Challenging Section 179 personal tax recovery orders initiated against non-executive government nominee directors following corporate default.",
    attached_queries: [
      {
        query_id: "q_002",
        query_text: "Director liability under Section 179 Income Tax Act — nominee director position",
        date: "2024-11-15",
        confidence: 0.61,
        conflicts_detected: true,
      },
    ],
    notes: [
      {
        id: "n_1",
        date: "2024-11-16",
        author: "Adv. S. Mulik",
        text: "Relied on Pr. CIT v. Siemens Ltd. (2017) 394 ITR 1 (SC) to establish that burden of proof requires factual inquiry, not automatic strict liability.",
      },
    ],
    pinned_authorities: [
      {
        citation: "Pr. CIT v. Siemens Ltd., (2017) 394 ITR 1 (SC)",
        type: "Supreme Court Precedent",
        relevance: "Apex standard for Section 179 due-diligence defence.",
      },
      {
        citation: "Section 179, Income Tax Act, 1961",
        type: "Statutory Code",
        relevance: "Governing recovery provision against private company directors.",
      },
    ],
  },
  {
    id: "case_002",
    case_number: "BAP / NCLT / 2024 / 881",
    title: "Bharat Minerals & Energy Corp. — CSR Advisory",
    client_name: "Bharat Minerals & Energy Corp.",
    court: "Corporate Board Advisory / NCLT",
    category: "Company Law",
    status: "UNDER_REVIEW",
    created_date: "2024-11-01",
    last_updated: "2024-11-18",
    description:
      "Review of CSR Committee constitution mandates under Section 135 Companies Act 2013 and evaluation of net profit calculation thresholds.",
    attached_queries: [
      {
        query_id: "q_001",
        query_text: "Is CSR committee mandatory under Section 135 of Companies Act, 2013?",
        date: "2024-11-18",
        confidence: 0.94,
        conflicts_detected: false,
      },
    ],
    notes: [
      {
        id: "n_2",
        date: "2024-11-18",
        author: "Adv. P. Verma",
        text: "Statutory compliance verified against in-force Companies Act 2013 provisions.",
      },
    ],
    pinned_authorities: [
      {
        citation: "Section 135, Companies Act, 2013",
        type: "Statute",
        relevance: "Mandatory corporate social responsibility committee composition.",
      },
    ],
  },
  {
    id: "case_003",
    case_number: "Civil Appeal No. 1092/2023",
    title: "M/s Apex Logistics Pvt. Ltd. v. Orient Shipping Lines",
    client_name: "Apex Logistics Pvt. Ltd.",
    court: "Supreme Court of India",
    category: "Commercial Appellate",
    status: "IN_HEARING",
    created_date: "2024-09-20",
    last_updated: "2024-11-10",
    description:
      "Application of Section 11 CPC Res Judicata to consecutive arbitration claims and finality of jurisdictional findings.",
    attached_queries: [
      {
        query_id: "q_001",
        query_text: "What is the doctrine of res judicata and its scope under Indian law?",
        date: "2024-11-10",
        confidence: 0.94,
        conflicts_detected: false,
      },
    ],
    notes: [
      {
        id: "n_3",
        date: "2024-11-10",
        author: "Adv. S. Mulik",
        text: "Filed rejoinder citing Satyadhyan Ghosal v. Deorajin Debi on stage-wise finality.",
      },
    ],
    pinned_authorities: [
      {
        citation: "Satyadhyan Ghosal v. Deorajin Debi, AIR 1960 SC 941",
        type: "Supreme Court Constitution Bench",
        relevance: "Foundational ratio on Section 11 CPC application to interlocutory stages.",
      },
      {
        citation: "Section 11, Code of Civil Procedure, 1908",
        type: "Statute",
        relevance: "Statutory res judicata bar on re-litigating decided issues.",
      },
    ],
  },
];

const STATUS_CONFIG = {
  ACTIVE: { label: "Active Litigation", color: "badge-status-active" },
  UNDER_REVIEW: { label: "Under Review", color: "badge-status-review" },
  IN_HEARING: { label: "In Hearing", color: "badge-status-hearing" },
  ARCHIVED: { label: "Archived", color: "badge-status-archived" },
};

export default function CasesPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [cases, setCases] = useState([]);
  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("ALL");

  // Modals
  const [showNewCaseModal, setShowNewCaseModal] = useState(false);
  const [showAttachModal, setShowAttachModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [historyQueries, setHistoryQueries] = useState([]);

  // Form State for New Case
  const [newCaseForm, setNewCaseForm] = useState({
    title: "",
    case_number: "",
    client_name: "",
    court: "",
    category: "Corporate & Commercial",
    description: "",
  });

  // New Note State
  const [newNoteText, setNewNoteText] = useState("");

  // Load cases from live backend workspace API with local fallback
  useEffect(() => {
    getCurrentUser().then(setUser).catch(() => null);

    async function loadCasesData() {
      try {
        const [apiMatters, hist] = await Promise.all([
          listMatters().catch(() => []),
          getResearchHistory().catch(() => []),
        ]);
        setHistoryQueries(hist || []);

        if (apiMatters && apiMatters.length > 0) {
          const adapted = apiMatters.map((m) => ({
            id: m.id,
            case_number: m.case_number || "Pending",
            title: m.matter_name,
            client_name: m.forum_detail || "Corporate Matter",
            court: `${m.forum_type} — ${m.forum_detail || "Main"}`,
            category: m.statutory_act || "Corporate Law",
            status: m.status || "ACTIVE",
            created_date: (m.created_at || "").split("T")[0] || new Date().toISOString().split("T")[0],
            last_updated: (m.updated_at || "").split("T")[0] || new Date().toISOString().split("T")[0],
            description: `${m.matter_name}. Opposing Parties: ${m.opposing_parties || "N/A"}. Lead Advocate: ${m.lead_advocate_name || "Advocate"}`,
            attached_queries: [],
            notes: [],
            pinned_authorities: [
              {
                id: "auth_1",
                citation: m.statutory_act || "Companies Act, 2013",
                court: m.forum_type,
                proposition: `Governed under ${m.statutory_act || "Companies Act, 2013"}`
              }
            ],
          }));
          setCases(adapted);
        } else {
          const saved = localStorage.getItem("halo_cases_store");
          setCases(saved ? JSON.parse(saved) : INITIAL_CASES);
        }
      } catch {
        setCases(INITIAL_CASES);
      }
    }
    loadCasesData();
  }, []);

  // Save changes to localStorage
  const updateCases = (updatedList) => {
    setCases(updatedList);
    localStorage.setItem("halo_cases_store", JSON.stringify(updatedList));
  };

  const selectedCase = cases.find((c) => c.id === selectedCaseId);

  // Filtered case list
  const filteredCases = cases.filter((c) => {
    if (search.trim()) {
      const q = search.toLowerCase();
      const match =
        c.title.toLowerCase().includes(q) ||
        c.case_number.toLowerCase().includes(q) ||
        c.client_name.toLowerCase().includes(q) ||
        c.court.toLowerCase().includes(q);
      if (!match) return false;
    }
    if (filterStatus !== "ALL" && c.status !== filterStatus) return false;
    return true;
  });

  // Handle New Case Creation
  const handleCreateCase = async (e) => {
    e.preventDefault();
    if (!newCaseForm.title.trim()) return;

    try {
      const created = await createMatter({
        matter_name: newCaseForm.title,
        case_number: newCaseForm.case_number,
        forum_type: "HIGH_COURT",
        forum_detail: newCaseForm.court || "High Court",
        statutory_act: newCaseForm.category || "Companies Act, 2013",
        status: "ACTIVE",
      });

      const newCase = {
        id: created.id,
        case_number: created.case_number || `MATTER-${Date.now().toString().slice(-4)}`,
        title: created.matter_name,
        client_name: newCaseForm.client_name || "Confidential Client",
        court: created.forum_detail || "High Court",
        category: created.statutory_act,
        status: "ACTIVE",
        created_date: new Date().toISOString().split("T")[0],
        last_updated: new Date().toISOString().split("T")[0],
        description: newCaseForm.description,
        attached_queries: [],
        notes: [],
        pinned_authorities: [],
      };

      const updated = [newCase, ...cases];
      updateCases(updated);
      setShowNewCaseModal(false);
      setSelectedCaseId(newCase.id);
    } catch {
      const fallbackCase = {
        id: `case_${Date.now()}`,
        case_number: newCaseForm.case_number || `MATTER-${Date.now().toString().slice(-4)}`,
        title: newCaseForm.title,
        client_name: newCaseForm.client_name || "Confidential Client",
        court: newCaseForm.court || "High Court",
        category: newCaseForm.category,
        status: "ACTIVE",
        created_date: new Date().toISOString().split("T")[0],
        last_updated: new Date().toISOString().split("T")[0],
        description: newCaseForm.description,
        attached_queries: [],
        notes: [],
        pinned_authorities: [],
      };
      updateCases([fallbackCase, ...cases]);
      setShowNewCaseModal(false);
      setSelectedCaseId(fallbackCase.id);
    }
    setNewCaseForm({
      title: "",
      case_number: "",
      client_name: "",
      court: "",
      category: "Corporate & Commercial",
      description: "",
    });
  };

  // Add Note to Selected Case
  const handleAddNote = (e) => {
    e.preventDefault();
    if (!newNoteText.trim() || !selectedCase) return;

    const note = {
      id: `note_${Date.now()}`,
      date: new Date().toISOString().split("T")[0],
      author: user?.email ? `Adv. ${user.email.split("@")[0]}` : "Advocate",
      text: newNoteText.trim(),
    };

    const updated = cases.map((c) => {
      if (c.id === selectedCase.id) {
        return {
          ...c,
          notes: [note, ...c.notes],
          last_updated: new Date().toISOString().split("T")[0],
        };
      }
      return c;
    });

    updateCases(updated);
    setNewNoteText("");
  };

  // Attach Query to Case
  const handleAttachQuery = (queryItem) => {
    if (!selectedCase) return;

    const alreadyAttached = selectedCase.attached_queries.some(
      (q) => q.query_id === queryItem.query_id
    );
    if (alreadyAttached) {
      alert("This research query is already attached to this matter.");
      return;
    }

    const newAttached = {
      query_id: queryItem.query_id,
      query_text: queryItem.query_text,
      date: queryItem.date?.split("T")[0] || new Date().toISOString().split("T")[0],
      confidence: queryItem.confidence_score || 0.8,
      conflicts_detected: queryItem.conflicts_detected || false,
    };

    const updated = cases.map((c) => {
      if (c.id === selectedCase.id) {
        return {
          ...c,
          attached_queries: [...c.attached_queries, newAttached],
          last_updated: new Date().toISOString().split("T")[0],
        };
      }
      return c;
    });

    updateCases(updated);
    setShowAttachModal(false);
  };

  // Detach Query
  const handleDetachQuery = (queryId) => {
    if (!selectedCase) return;
    const updated = cases.map((c) => {
      if (c.id === selectedCase.id) {
        return {
          ...c,
          attached_queries: c.attached_queries.filter((q) => q.query_id !== queryId),
          last_updated: new Date().toISOString().split("T")[0],
        };
      }
      return c;
    });
    updateCases(updated);
  };

  return (
    <AppShell user={user}>
      <div className="cs-container">


        {/* ── CASE LIST VIEW ── */}
        {!selectedCaseId && (
          <>
            <PageHeader
              title="Cases & Matter Dossier Workspace"
              action={
                <button
                  className="btn btn-primary cs-new-btn"
                  onClick={() => setShowNewCaseModal(true)}
                >
                  + New Legal Case
                </button>
              }
            />

            {/* Top Workspace Stats */}
            <div className="cs-stats-grid">
              <div className="cs-stat-card">
                <span className="cs-stat-label">Total Matters</span>
                <span className="cs-stat-value">{cases.length}</span>
                <span className="cs-stat-sub">Active client files</span>
              </div>
              <div className="cs-stat-card">
                <span className="cs-stat-label">Active Litigation</span>
                <span className="cs-stat-value cs-stat-green">
                  {cases.filter((c) => c.status === "ACTIVE").length}
                </span>
                <span className="cs-stat-sub">In court / active pleadings</span>
              </div>
              <div className="cs-stat-card">
                <span className="cs-stat-label">Under Hearing</span>
                <span className="cs-stat-value cs-stat-amber">
                  {cases.filter((c) => c.status === "IN_HEARING").length}
                </span>
                <span className="cs-stat-sub">Arguments ongoing</span>
              </div>
              <div className="cs-stat-card">
                <span className="cs-stat-label">Attached Research Queries</span>
                <span className="cs-stat-value cs-stat-accent">
                  {cases.reduce((sum, c) => sum + c.attached_queries.length, 0)}
                </span>
                <span className="cs-stat-sub">Verified AI queries linked</span>
              </div>
            </div>

            {/* Filter & Search Bar */}
            <div className="cs-controls">
              <div className="cs-search-box">
                <span className="cs-search-icon">🔍</span>
                <input
                  type="text"
                  className="cs-search-input"
                  placeholder="Search by case title, matter number, court, or client..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                {search && (
                  <button className="cs-clear-btn" onClick={() => setSearch("")}>✕</button>
                )}
              </div>

              <div className="cs-filters">
                <select
                  className="cs-filter-select"
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                >
                  <option value="ALL">All Statuses</option>
                  <option value="ACTIVE">Active Litigation</option>
                  <option value="IN_HEARING">In Hearing</option>
                  <option value="UNDER_REVIEW">Under Review</option>
                  <option value="ARCHIVED">Archived</option>
                </select>
              </div>
            </div>

            {/* Case Cards Grid */}
            <div className="cs-grid">
              {filteredCases.map((c) => {
                const statusMeta = STATUS_CONFIG[c.status] || STATUS_CONFIG.ACTIVE;
                const statusKey = c.status?.toLowerCase().replace("_", "") || "active";
                return (
                  <div
                    key={c.id}
                    className="cs-card-wrapper"
                    onClick={() => setSelectedCaseId(c.id)}
                  >
                    {/* Physical Case Dossier Folder Tab */}
                    <div className="cs-folder-tab">
                      <span className="cs-tab-label">{c.case_number}</span>
                    </div>

                    <div className="cs-card">
                      <div className="cs-card-top">
                        <span className="cs-card-category">{c.category}</span>
                        {/* 6px Solid Status Dot + Clean Label */}
                        <div className="cs-status-indicator">
                          <span className={`cs-status-dot dot-${statusKey}`} aria-hidden="true" />
                          <span className="cs-status-text">{statusMeta.label}</span>
                        </div>
                      </div>

                      <h2 className="cs-card-title">{c.title}</h2>
                      <p className="cs-card-desc">{c.description}</p>

                      {/* Client / Court info: Hairline divider, two-column structured data, no gray box */}
                      <div className="cs-card-meta">
                        <div className="cs-meta-col">
                          <span className="cs-meta-label">Court Forum</span>
                          <span className="cs-meta-val">{c.court}</span>
                        </div>
                        <div className="cs-meta-col">
                          <span className="cs-meta-label">Client Matter</span>
                          <span className="cs-meta-val">{c.client_name}</span>
                        </div>
                      </div>

                      <div className="cs-card-footer">
                        <span className="cs-queries-count">
                          {c.attached_queries.length} Research Queries
                        </span>
                        <span className="cs-open-arrow">Open Dossier &rarr;</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}

        {/* ── CASE DETAIL / DOSSIER VIEW ── */}
        {selectedCase && (
          <div className="cs-dossier">
            <header className="cs-dossier-header">
              <div>
                <div className="cs-dossier-top">
                  <span className="cs-matter-no-lg">{selectedCase.case_number}</span>
                  <StatusBadge
                    status={selectedCase.status}
                    label={STATUS_CONFIG[selectedCase.status]?.label}
                    size="sm"
                  />
                  <StatusBadge variant="accent" label={selectedCase.category} size="sm" />
                </div>
                <h1 className="cs-dossier-title">{selectedCase.title}</h1>
                <div className="cs-dossier-meta-strip">
                  <span>🏛️ {selectedCase.court}</span>
                  <span>·</span>
                  <span>👤 Client: <strong>{selectedCase.client_name}</strong></span>
                  <span>·</span>
                  <span>Updated: {selectedCase.last_updated}</span>
                </div>
              </div>

              <div className="cs-dossier-actions">
                <button
                  className="btn btn-primary"
                  onClick={() => navigate(`/cases/${selectedCase.id}`)}
                >
                  🤖 Open AI Case Workspace
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => setSelectedCaseId(null)}
                >
                  &larr; Back to Cases
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowExportModal(true)}
                >
                  Export Case Legal Brief
                </button>
              </div>
            </header>

            {/* Case Synopsis */}
            <section className="cs-section cs-synopsis-section">
              <h2 className="cs-section-title">Matter Background & Legal Strategy</h2>
              <p className="cs-synopsis-text">{selectedCase.description}</p>
            </section>

            {/* Attached Legal Research Queries */}
            <section className="cs-section">
              <div className="cs-section-header">
                <div>
                  <h2 className="cs-section-title">Attached Verified Research Queries</h2>
                  <p className="cs-section-subtitle">
                    Legal queries executed through the Nyaya Sahayak pipeline linked to this matter file.
                  </p>
                </div>
                <button
                  className="btn btn-secondary cs-attach-btn"
                  onClick={() => setShowAttachModal(true)}
                >
                  + Link Research Query
                </button>
              </div>

              {selectedCase.attached_queries.length === 0 ? (
                <div className="cs-empty-attached">
                  <p>No research queries currently attached to this case.</p>
                  <button className="btn btn-secondary" onClick={() => setShowAttachModal(true)}>
                    + Link from Research History
                  </button>
                </div>
              ) : (
                <div className="cs-attached-list">
                  {selectedCase.attached_queries.map((q) => (
                    <div key={q.query_id} className="cs-attached-card">
                      <div className="cs-attached-top">
                        <span className="cs-query-id">{q.query_id}</span>
                        {q.conflicts_detected ? (
                          <span className="cs-conflict-pill">⚡ Judicial Conflict Flagged</span>
                        ) : (
                          <span className="cs-clean-pill">✓ Clean Verification</span>
                        )}
                        <span className="cs-conf-pill">
                          {Math.round(q.confidence * 100)}% Confidence
                        </span>
                        <button
                          className="cs-detach-btn"
                          title="Unlink from matter"
                          onClick={() => handleDetachQuery(q.query_id)}
                        >
                          ✕
                        </button>
                      </div>

                      <p className="cs-attached-query-text">{q.query_text}</p>

                      <div className="cs-attached-actions">
                        <Link
                          to={`/research/${q.query_id}`}
                          className="btn btn-secondary cs-action-btn"
                        >
                          View Synthesized Answer &rarr;
                        </Link>
                        <Link
                          to={`/research/${q.query_id}/evidence`}
                          className="btn btn-secondary cs-action-btn"
                        >
                          Evidence Passages
                        </Link>
                        {q.conflicts_detected && (
                          <Link
                            to={`/research/${q.query_id}/conflict`}
                            className="btn btn-outline cs-action-btn cs-conflict-link"
                          >
                            ⚡ Conflict Inspector
                          </Link>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Pinned Statutory Authorities & Precedents */}
            <section className="cs-section">
              <h2 className="cs-section-title">Controlling Authorities & Binding Precedents</h2>
              <div className="cs-authorities-grid">
                {selectedCase.pinned_authorities.map((auth, idx) => (
                  <div key={idx} className="cs-authority-card">
                    <span className="cs-auth-type">{auth.type}</span>
                    <h3 className="cs-auth-cit">{auth.citation}</h3>
                    <p className="cs-auth-rel">{auth.relevance}</p>
                  </div>
                ))}
              </div>
            </section>

            {/* Case Notes & Litigation Log */}
            <section className="cs-section">
              <h2 className="cs-section-title">Advocate Strategy Notes & Pleadings Log</h2>

              <form className="cs-note-form" onSubmit={handleAddNote}>
                <textarea
                  className="cs-note-textarea"
                  placeholder="Add a litigation note, hearing update, or judicial observation..."
                  value={newNoteText}
                  onChange={(e) => setNewNoteText(e.target.value)}
                  rows={3}
                />
                <button type="submit" className="btn btn-primary cs-post-note-btn" disabled={!newNoteText.trim()}>
                  Post Note
                </button>
              </form>

              <div className="cs-notes-list">
                {selectedCase.notes.map((n) => (
                  <div key={n.id} className="cs-note-item">
                    <div className="cs-note-meta">
                      <strong>{n.author}</strong>
                      <span>·</span>
                      <span>{n.date}</span>
                    </div>
                    <p className="cs-note-text">{n.text}</p>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}

        {/* ── MODAL: CREATE NEW CASE ── */}
        {showNewCaseModal && (
          <div className="cs-modal-backdrop" onClick={() => setShowNewCaseModal(false)}>
            <div className="cs-modal" onClick={(e) => e.stopPropagation()}>
              <div className="cs-modal-header">
                <h2>Create New Legal Matter File</h2>
                <button className="cs-modal-close" onClick={() => setShowNewCaseModal(false)}>✕</button>
              </div>

              <form onSubmit={handleCreateCase} className="cs-modal-form">
                <div className="cs-form-group">
                  <label>Case Title / Cause Title *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. ABC Corp v. Commissioner of Income Tax"
                    value={newCaseForm.title}
                    onChange={(e) => setNewCaseForm({ ...newCaseForm, title: e.target.value })}
                  />
                </div>

                <div className="cs-form-row">
                  <div className="cs-form-group">
                    <label>Matter / Case Number</label>
                    <input
                      type="text"
                      placeholder="e.g. WP (C) No. 1234/2024"
                      value={newCaseForm.case_number}
                      onChange={(e) => setNewCaseForm({ ...newCaseForm, case_number: e.target.value })}
                    />
                  </div>

                  <div className="cs-form-group">
                    <label>Court / Adjudicatory Forum</label>
                    <input
                      type="text"
                      placeholder="e.g. High Court of Delhi"
                      value={newCaseForm.court}
                      onChange={(e) => setNewCaseForm({ ...newCaseForm, court: e.target.value })}
                    />
                  </div>
                </div>

                <div className="cs-form-row">
                  <div className="cs-form-group">
                    <label>Client Name / Party</label>
                    <input
                      type="text"
                      placeholder="e.g. Steel Authority of India Ltd."
                      value={newCaseForm.client_name}
                      onChange={(e) => setNewCaseForm({ ...newCaseForm, client_name: e.target.value })}
                    />
                  </div>

                  <div className="cs-form-group">
                    <label>Practice Category</label>
                    <select
                      value={newCaseForm.category}
                      onChange={(e) => setNewCaseForm({ ...newCaseForm, category: e.target.value })}
                    >
                      <option value="Corporate & Commercial">Corporate & Commercial</option>
                      <option value="Direct Taxation">Direct Taxation</option>
                      <option value="Insolvency & Bankruptcy">Insolvency & Bankruptcy (IBC)</option>
                      <option value="Constitutional & Writ">Constitutional & Writ</option>
                      <option value="Arbitration & Dispute Resolution">Arbitration & Dispute Resolution</option>
                    </select>
                  </div>
                </div>

                <div className="cs-form-group">
                  <label>Matter Synopsis & Legal Questions</label>
                  <textarea
                    rows={3}
                    placeholder="Summary of factual dispute and key statutory provisions involved..."
                    value={newCaseForm.description}
                    onChange={(e) => setNewCaseForm({ ...newCaseForm, description: e.target.value })}
                  />
                </div>

                <div className="cs-modal-actions">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowNewCaseModal(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary">
                    Create Case File
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ── MODAL: LINK RESEARCH QUERY ── */}
        {showAttachModal && (
          <div className="cs-modal-backdrop" onClick={() => setShowAttachModal(false)}>
            <div className="cs-modal" onClick={(e) => e.stopPropagation()}>
              <div className="cs-modal-header">
                <h2>Link Verified Research Query</h2>
                <button className="cs-modal-close" onClick={() => setShowAttachModal(false)}>✕</button>
              </div>

              <div className="cs-attach-modal-body">
                <p className="cs-attach-info">
                  Select a query from your research history to attach to <strong>{selectedCase?.title}</strong>:
                </p>

                <div className="cs-attach-query-list">
                  {historyQueries.map((item) => (
                    <div key={item.query_id} className="cs-attach-query-item">
                      <div>
                        <span className="cs-attach-qid">{item.query_id}</span>
                        <p className="cs-attach-qtext">{item.query_text}</p>
                        <span className="cs-attach-qconf">
                          Confidence: {Math.round(item.confidence_score * 100)}%
                        </span>
                      </div>
                      <button
                        className="btn btn-secondary cs-attach-pick-btn"
                        onClick={() => handleAttachQuery(item)}
                      >
                        + Attach
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── MODAL: EXPORT CASE BRIEF ── */}
        {showExportModal && selectedCase && (
          <div className="cs-modal-backdrop" onClick={() => setShowExportModal(false)}>
            <div className="cs-modal cs-export-modal" onClick={(e) => e.stopPropagation()}>
              <div className="cs-modal-header">
                <h2>Legal Research Brief — Court Presentation Preview</h2>
                <button className="cs-modal-close" onClick={() => setShowExportModal(false)}>✕</button>
              </div>

              <div className="cs-export-body">
                <div className="cs-brief-paper">
                  <div className="cs-brief-header">
                    <span className="cs-brief-court">{selectedCase.court.toUpperCase()}</span>
                    <span className="cs-brief-no">{selectedCase.case_number}</span>
                    <h2 className="cs-brief-title">{selectedCase.title}</h2>
                    <span className="cs-brief-client">IN THE MATTER OF: {selectedCase.client_name}</span>
                  </div>

                  <hr className="cs-brief-hr" />

                  <div className="cs-brief-section">
                    <h3>I. STATEMENT OF LEGAL ISSUE & SYNOPSIS</h3>
                    <p>{selectedCase.description}</p>
                  </div>

                  <div className="cs-brief-section">
                    <h3>II. CONTROLLING JUDICIAL AUTHORITIES & STATUTORY PROVISIONS</h3>
                    <ul>
                      {selectedCase.pinned_authorities.map((a, i) => (
                        <li key={i}>
                          <strong>{a.citation}</strong> ({a.type}) — {a.relevance}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="cs-brief-section">
                    <h3>III. EVIDENCE-VERIFIED LEGAL PROPOSITIONS</h3>
                    {selectedCase.attached_queries.map((q) => (
                      <div key={q.query_id} className="cs-brief-finding">
                        <span className="cs-finding-q">Verified Query: "{q.query_text}"</span>
                        <span className="cs-finding-status">
                          Verification Status: {q.conflicts_detected ? "CONFLICT DETECTED (See Advisory)" : "FULLY SUPPORTED"}
                          {" · "}Confidence: {Math.round(q.confidence * 100)}%
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="cs-brief-section">
                    <h3>IV. LITIGATION NOTES & STRATEGY</h3>
                    {selectedCase.notes.map((n) => (
                      <p key={n.id} className="cs-brief-note">
                        <strong>[{n.date} - {n.author}]:</strong> {n.text}
                      </p>
                    ))}
                  </div>

                  <div className="cs-brief-footer">
                    <span>Generated by Nyaya Sahayak Legal Verification Framework</span>
                    <span>Protocol: PRD v2.0 Section 32 Certified</span>
                  </div>
                </div>

                <div className="cs-export-actions">
                  <button
                    className="btn btn-secondary"
                    onClick={() => {
                      window.print();
                    }}
                  >
                    🖨️ Print / Save as PDF
                  </button>
                  <button
                    className="btn btn-primary"
                    onClick={() => {
                      navigator.clipboard.writeText(
                        `LEGAL RESEARCH BRIEF\n${selectedCase.case_number}\n${selectedCase.title}\nCourt: ${selectedCase.court}\nClient: ${selectedCase.client_name}\n\nSynopsis:\n${selectedCase.description}\n\nAuthorities:\n${selectedCase.pinned_authorities.map(a => `- ${a.citation}: ${a.relevance}`).join("\n")}`
                      );
                      alert("Legal brief copied to clipboard in plain text!");
                    }}
                  >
                    📋 Copy Text
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
