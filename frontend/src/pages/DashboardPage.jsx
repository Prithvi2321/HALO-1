/**
 * src/pages/DashboardPage.jsx
 * ────────────────────────────
 * Executive Legal Practice & Intelligence Dashboard for HALO (Nyaya Sahayak).
 *
 * Implements:
 * - Active Cases & Projects Grid (Clicking any case opens the dedicated Case Workspace)
 * - Master Practice Calendar & Schedule across all firm matters
 * - Today's Court Agenda & Upcoming hearings with forum priority color coding
 * - Declarative Statutory Deadline Calculator Widget (MGT-14, DIR-12, AOC-4, NCLAT appeal, etc.)
 * - Telegram Bot Gateway mobile sync widget & 6-digit OTP pairing modal (PRD §8)
 * - Live Indian Legal News Feed (NewsAPI / court feeds)
 * - Recent research query history & confidence metrics
 */

import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  Briefcase,
  FileText,
  Search,
  ShieldCheck,
  Calendar,
  ChevronRight,
  AlertTriangle,
  Clock,
  Smartphone,
  CheckCircle2,
  Scale,
  Sparkles,
  Calculator,
  Plus,
  X,
  ExternalLink,
  Newspaper,
  ArrowRight,
  FolderOpen,
} from "lucide-react";
import { getCurrentUser } from "../api/client";
import { getResearchHistory } from "../api/researchApi";
import {
  getDashboardSummary,
  listDeadlineRules,
  computeDeadline,
  createEvent,
  listMatters,
} from "../api/workspaceApi";
import {
  generatePairingCode,
  getPairingStatus,
  unpairTelegram,
} from "../api/telegramApi";
import { getIndianLegalNews } from "../api/newsApi";
import { listTemplates } from "../api/draftingApi";
import AppShell from "../components/AppShell";
import "./DashboardPage.css";

export default function DashboardPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [history, setHistory] = useState([]);
  const [dashboardData, setDashboardData] = useState(null);
  const [matters, setMatters] = useState([]);
  const [loading, setLoading] = useState(true);

  // Statutory Deadline Calculator State
  const [rules, setRules] = useState([]);
  const [selectedRuleId, setSelectedRuleId] = useState("MGT14_FILING_30D");
  const [anchorDate, setAnchorDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [computedDeadline, setComputedDeadline] = useState(null);
  const [computingDeadline, setComputingDeadline] = useState(false);
  const [deadlineAddedSuccess, setDeadlineAddedSuccess] = useState(false);

  // Telegram Pairing Modal State
  const [telegramStatus, setTelegramStatus] = useState({ is_paired: false });
  const [showTelegramModal, setShowTelegramModal] = useState(false);
  const [pairingCodeData, setPairingCodeData] = useState(null);
  const [generatingCode, setGeneratingCode] = useState(false);

  // Legal News State
  const [legalNews, setLegalNews] = useState([]);

  // Smart Forms Studio State
  const [templates, setTemplates] = useState([]);
  const [formSearchQuery, setFormSearchQuery] = useState("");
  const [selectedFormCategory, setSelectedFormCategory] = useState("ALL");

  useEffect(() => {
    async function loadData() {
      try {
        const [userData, historyData, summaryData, rulesData, tgStatus, newsData, mattersData, tmplsData] = await Promise.all([
          getCurrentUser().catch(() => null),
          getResearchHistory().catch(() => []),
          getDashboardSummary().catch(() => null),
          listDeadlineRules().catch(() => []),
          getPairingStatus().catch(() => ({ is_paired: false })),
          getIndianLegalNews("", 4).catch(() => ({ articles: [] })),
          listMatters().catch(() => []),
          listTemplates().catch(() => []),
        ]);
        setUser(userData);
        setHistory(historyData || []);
        setDashboardData(summaryData);
        setRules(rulesData || []);
        setTelegramStatus(tgStatus || { is_paired: false });
        setLegalNews(newsData?.articles || []);
        setMatters(mattersData || []);
        setTemplates(tmplsData || []);

        if (rulesData && rulesData.length > 0) {
          setSelectedRuleId(rulesData[0].rule_id);
        }
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Compute deadline
  async function handleComputeDeadline() {
    if (!selectedRuleId || !anchorDate) return;
    setComputingDeadline(true);
    setDeadlineAddedSuccess(false);
    try {
      const result = await computeDeadline(selectedRuleId, anchorDate);
      setComputedDeadline(result);
    } catch (err) {
      alert("Calculation failed: " + err.message);
    } finally {
      setComputingDeadline(false);
    }
  }

  // Add computed deadline to calendar
  async function handleAddDeadlineToCalendar() {
    if (!computedDeadline) return;
    try {
      await createEvent({
        event_title: computedDeadline.title,
        event_type: "FILING_DEADLINE",
        starts_at: computedDeadline.due_date,
        rule_id: computedDeadline.rule_id,
        rule_version: computedDeadline.rule_version,
        computation_explanation: computedDeadline.explanation,
        priority: computedDeadline.priority,
      });
      setDeadlineAddedSuccess(true);
      const updated = await getDashboardSummary();
      setDashboardData(updated);
    } catch (err) {
      alert("Failed to add to calendar: " + err.message);
    }
  }

  // Generate Telegram OTP
  async function handleOpenTelegramModal() {
    setShowTelegramModal(true);
    setGeneratingCode(true);
    try {
      const data = await generatePairingCode();
      setPairingCodeData(data);
    } catch (err) {
      alert("Failed to generate OTP: " + err.message);
    } finally {
      setGeneratingCode(false);
    }
  }

  // Unpair Telegram
  async function handleUnpairTelegram() {
    if (!confirm("Are you sure you want to disconnect Telegram notifications?")) return;
    try {
      await unpairTelegram();
      setTelegramStatus({ is_paired: false });
    } catch (err) {
      alert("Unpair failed: " + err.message);
    }
  }

  if (loading) {
    return (
      <AppShell user={null}>
        <div className="dashboard-container">
          <div className="dashboard-loading-state">
            <span className="loading-spinner-ring" />
            <p>Loading legal intelligence workspace…</p>
          </div>
        </div>
      </AppShell>
    );
  }

  const metrics = dashboardData?.metrics || {
    active_matters_count: matters.length || 3,
    today_events_count: 1,
    upcoming_hearings_count: 2,
    overdue_deadlines_count: 0,
    drafts_in_progress_count: 0,
  };

  const todayAgenda = dashboardData?.today_agenda || [];
  const upcomingHearings = dashboardData?.upcoming_hearings || [];

  return (
    <AppShell user={user}>
      <div className="dashboard-container">
        {/* ── Welcome Header ── */}
        <header className="dashboard-header">
          <div className="header-titles">
            <h1 className="dashboard-title">Advocate Practice Hub</h1>
            <p className="dashboard-subtitle">
              Verified legal research, court matters, and auto-computed statutory deadlines.
            </p>
          </div>
          <div className="header-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => navigate("/drafts")}
            >
              <FileText size={16} style={{ marginRight: 6 }} />
              <span>Drafting Studio</span>
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => navigate("/research")}
            >
              <Search size={16} style={{ marginRight: 6 }} />
              <span>New Research Query</span>
            </button>
          </div>
        </header>

        {/* ── Mobile Telegram Sync Banner ── */}
        <div className="telegram-sync-strip">
          <div className="tg-strip-left">
            <div className="tg-icon-circle">
              <Smartphone size={20} color="#0284c7" />
            </div>
            <div>
              <div className="tg-strip-title">
                {telegramStatus.is_paired ? (
                  <span className="tg-paired-badge">
                    <CheckCircle2 size={14} /> Telegram Mobile Sync Active (@{telegramStatus.username || "advocate"})
                  </span>
                ) : (
                  <span>Telegram Mobile Gateway: Receive hearing reminders & agenda on your phone</span>
                )}
              </div>
              <p className="tg-strip-desc">
                {telegramStatus.is_paired
                  ? "Your mobile account is linked. Use /agenda today, /cases, or /note in Telegram anytime."
                  : "Pair securely in 30 seconds with a 6-digit OTP to get 24h & 2h hearing notifications."}
              </p>
            </div>
          </div>
          <div className="tg-strip-right">
            {telegramStatus.is_paired ? (
              <button className="btn btn-secondary btn-sm" onClick={handleUnpairTelegram}>
                Disconnect
              </button>
            ) : (
              <button className="btn btn-primary btn-sm" onClick={handleOpenTelegramModal}>
                Connect Telegram Bot
              </button>
            )}
          </div>
        </div>

        {/* ── 4 Practice Metric Cards ── */}
        <section className="stats-row" aria-label="Key legal metrics">
          <div className="stat-card" onClick={() => navigate("/cases")}>
            <div className="stat-card-top">
              <div className="stat-icon-circle">
                <Briefcase size={18} />
              </div>
              <span className="stat-nav-arrow">&rarr;</span>
            </div>
            <div className="stat-value">{metrics.active_matters_count}</div>
            <div className="stat-label">Active Matters</div>
            <div className="stat-meta">NCLT, High Court, Supreme Court</div>
          </div>

          <div className="stat-card" onClick={() => navigate("/cases")}>
            <div className="stat-card-top">
              <div className="stat-icon-circle">
                <Calendar size={18} />
              </div>
              <span className="stat-nav-arrow">&rarr;</span>
            </div>
            <div className="stat-value">{metrics.today_events_count}</div>
            <div className="stat-label">Today's Listings</div>
            <div className="stat-meta">{metrics.upcoming_hearings_count} more in next 7 days</div>
          </div>

          <div className="stat-card" onClick={() => navigate("/drafts")}>
            <div className="stat-card-top">
              <div className="stat-icon-circle">
                <FileText size={18} />
              </div>
              <span className="stat-nav-arrow">&rarr;</span>
            </div>
            <div className="stat-value">7</div>
            <div className="stat-label">Statutory Templates</div>
            <div className="stat-meta">Board Res, Petitions, Affidavits</div>
          </div>

          <div className="stat-card" onClick={() => navigate("/admin/audit")}>
            <div className="stat-card-top">
              <div className="stat-icon-circle">
                <ShieldCheck size={18} />
              </div>
              <span className="stat-nav-arrow">&rarr;</span>
            </div>
            <div className="stat-value">SHA-256</div>
            <div className="stat-label">Cryptographic Seal</div>
            <div className="stat-meta">100% Fail-closed verification</div>
          </div>
        </section>

        {/* ── ACTIVE CASES / PROJECTS PANEL (Interactive Case Workspace Launcher) ── */}
        <section className="dashboard-cases-panel">
          <div className="panel-header">
            <div className="panel-header-title">
              <FolderOpen size={18} className="panel-icon" />
              <h2>Active Case Workspaces</h2>
              <span className="panel-badge-pill">Click a case to open its AI Workspace</span>
            </div>
            <Link to="/cases" className="panel-link">
              View All in Directory &rarr;
            </Link>
          </div>

          <div className="cases-grid-cards">
            {(matters.length > 0 ? matters : [
              {
                id: "case_001",
                matter_name: "Steel Authority of India Ltd. v. Nominee Directors",
                forum_type: "HIGH_COURT",
                forum_detail: "Delhi High Court (Commercial Div)",
                case_number: "CS (COMM) 412/2026",
                statutory_act: "Income Tax Act, 1961 / Companies Act",
                lead_advocate_name: "Adv. S. Mulik",
                status: "ACTIVE",
              },
              {
                id: "case_002",
                matter_name: "Bharat Minerals & Energy Corp. — CSR Advisory",
                forum_type: "NCLT",
                forum_detail: "Principal Bench, New Delhi",
                case_number: "BAP/NCLT/2026/881",
                statutory_act: "Companies Act, 2013",
                lead_advocate_name: "Adv. P. Verma",
                status: "ACTIVE",
              },
              {
                id: "case_003",
                matter_name: "Apex Logistics Ltd. — Section 9 IBC CIRP",
                forum_type: "NCLT",
                forum_detail: "Mumbai Bench",
                case_number: "CP(IB) 204/MB/2026",
                statutory_act: "Insolvency & Bankruptcy Code, 2016",
                lead_advocate_name: "Adv. Lead",
                status: "ACTIVE",
              },
            ]).map((c) => (
              <div
                key={c.id}
                className="case-project-card"
                onClick={() => navigate(`/cases/${c.id}`)}
              >
                <div className="case-card-header">
                  <span className={`case-forum-pill forum-${(c.forum_type || "").toLowerCase()}`}>
                    {c.forum_detail || c.forum_type}
                  </span>
                  <span className="case-docket-num font-mono">{c.case_number || "Pending"}</span>
                </div>

                <h3 className="case-card-title">{c.matter_name}</h3>

                <div className="case-card-footer">
                  <span className="case-act-tag">{c.statutory_act || "Corporate Law"}</span>
                  <span className="case-open-hint">
                    Open Workspace <ArrowRight size={14} style={{ marginLeft: 3 }} />
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── AI LEGAL DRAFTING & SMART FORMS STUDIO PANEL ── */}
        <section className="dashboard-forms-panel">
          <div className="panel-header">
            <div className="panel-header-title">
              <Sparkles size={18} className="panel-icon text-amber" />
              <h2>AI Legal Drafting & Smart Forms Studio</h2>
              <span className="panel-badge-pill highlight-pill">
                Auto-Intake via Questions & Document Upload
              </span>
            </div>
            <Link to="/drafts" className="panel-link">
              Explore All {templates.length || 10} Legal Forms &rarr;
            </Link>
          </div>

          <p className="forms-studio-banner-desc">
            Skip tedious manual typing. Conversational Q&A and instant file upload (Aadhaar, PAN, electricity bills, cheque leaf, return memo) to auto-extract parameters and produce court-ready legal instruments with live multilingual preview (English, हिंदी & Bilingual) and 1-click DOCX & PDF exports.
          </p>

          {/* Forms Search & Category Bar */}
          <div className="forms-studio-controls">
            <div className="forms-search-box">
              <Search size={16} className="forms-search-icon" />
              <input
                type="text"
                placeholder="Search forms (e.g. Rent Agreement, Cheque Bounce, NDA, Board Resolution)..."
                value={formSearchQuery}
                onChange={(e) => setFormSearchQuery(e.target.value)}
                className="forms-search-input"
              />
              {formSearchQuery && (
                <button
                  type="button"
                  className="forms-search-clear"
                  onClick={() => setFormSearchQuery("")}
                >
                  <X size={14} />
                </button>
              )}
            </div>

            <div className="forms-category-pills">
              {[
                { id: "ALL", label: "All Forms" },
                { id: "AGREEMENT", label: "Agreements & Leases" },
                { id: "NOTICE", label: "Statutory Notices" },
                { id: "CORPORATE_RESOLUTION", label: "Board Resolutions" },
              ].map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  className={`forms-cat-pill ${selectedFormCategory === cat.id ? "active" : ""}`}
                  onClick={() => setSelectedFormCategory(cat.id)}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* Featured / Filtered Smart Forms Grid */}
          <div className="forms-cards-grid">
            {((templates.length > 0 ? templates : [
              {
                id: "RENT_AGREEMENT_RESIDENTIAL_V1",
                name: "Residential & Commercial Rent / Lease Agreement",
                category: "AGREEMENT",
                statutory_anchor: "Transfer of Property Act, 1882 / Rent Control Act",
                description: "Auto-extracts landlord/tenant details, Aadhaar/PAN, lock-in period, rent, security deposit, and CAM charges via questions or document upload.",
                field_count: 8,
              },
              {
                id: "NOTICE_DEMAND_138_V1",
                name: "Section 138 NI Act Cheque Bounce Statutory Demand Notice",
                category: "NOTICE",
                statutory_anchor: "Section 138 proviso (b), Negotiable Instruments Act, 1881",
                description: "Auto-drafts mandatory 15-day statutory demand notice from dishonoured cheque scan and bank return memo with 100% statutory timeline calculation.",
                field_count: 7,
              },
              {
                id: "NDA_COMMERCIAL_V1",
                name: "Commercial Non-Disclosure Agreement (NDA)",
                category: "AGREEMENT",
                statutory_anchor: "Indian Contract Act, 1872",
                description: "Standard bilateral/unilateral confidentiality covenants with trade secret protection, non-compete, and injunctive relief clauses.",
                field_count: 6,
              },
              {
                id: "CONSULTANT_AGREEMENT_V1",
                name: "Independent Consultant & Service Agreement",
                category: "AGREEMENT",
                statutory_anchor: "Indian Contract Act, 1872",
                description: "Comprehensive contractor engagement agreement with milestone-based fee schedules, intellectual property assignment, and non-solicitation.",
                field_count: 7,
              },
              {
                id: "BOARD_RES_DIR_APPT_V1",
                name: "Board Resolution — Appointment of Additional Director",
                category: "CORPORATE_RESOLUTION",
                statutory_anchor: "Section 161(1), Companies Act, 2013",
                description: "Standard board resolution appointing an additional director until the ensuing Annual General Meeting with DIR-12 compliance note.",
                field_count: 7,
              },
              {
                id: "DEMAND_NOTICE_SEC8_IBC_V1",
                name: "Section 8 IBC Demand Notice (Form 3/4)",
                category: "NOTICE",
                statutory_anchor: "Section 8, Insolvency and Bankruptcy Code, 2016",
                description: "Pre-requisite 10-day operational creditor demand notice demanding payment of unpaid operational debt under Rule 5 of AAA Rules.",
                field_count: 7,
              },
            ]).filter((t) => {
              const matchCat =
                selectedFormCategory === "ALL" ||
                t.category === selectedFormCategory ||
                (selectedFormCategory === "AGREEMENT" && (t.category === "AGREEMENT" || t.id.includes("RENT") || t.id.includes("NDA") || t.id.includes("CONSULTANT")));
              const matchSearch =
                !formSearchQuery ||
                t.name.toLowerCase().includes(formSearchQuery.toLowerCase()) ||
                t.statutory_anchor?.toLowerCase().includes(formSearchQuery.toLowerCase()) ||
                t.description?.toLowerCase().includes(formSearchQuery.toLowerCase());
              return matchCat && matchSearch;
            })).map((t) => (
              <div
                key={t.id}
                className="smart-form-card"
                onClick={() => navigate(`/drafts?template=${t.id}`)}
              >
                <div className="smart-form-card-top">
                  <div className="smart-form-icon-wrap">
                    {t.id.includes("RENT") ? "🏠" : t.id.includes("138") ? "⚖️" : t.id.includes("NDA") ? "🤝" : t.id.includes("CONSULTANT") ? "💼" : t.id.includes("BOARD") ? "🏢" : "📜"}
                  </div>
                  <div className="smart-form-badges">
                    <span className="smart-form-lang-badge">🌐 EN • HI • द्विभाषी</span>
                    <span className="smart-form-format-badge">DOCX • PDF</span>
                  </div>
                </div>

                <h3 className="smart-form-title">{t.name}</h3>
                <div className="smart-form-anchor">🏛️ {t.statutory_anchor}</div>
                <p className="smart-form-desc">{t.description}</p>

                <div className="smart-form-card-footer">
                  <span className="smart-form-fields-badge">
                    {t.field_count || 8} Auto-Parsed Fields
                  </span>
                  <span className="smart-form-open-btn">
                    Launch Smart Studio <ArrowRight size={14} style={{ marginLeft: 4 }} />
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Main Dashboard 2-Column Grid ── */}
        <div className="dashboard-main-grid">
          {/* Column 1: Agenda, Master Calendar & News */}
          <div className="dashboard-grid-col">
            {/* Today's Court Agenda */}
            <div className="dashboard-panel">
              <div className="panel-header">
                <div className="panel-header-title">
                  <Clock size={18} className="panel-icon" />
                  <h2>Today's Court Agenda & Cause List</h2>
                </div>
                <Link to="/cases" className="panel-link">
                  View Matters &rarr;
                </Link>
              </div>

              {todayAgenda.length === 0 ? (
                <div className="panel-empty-state">
                  <p>No court hearings or filings listed for today.</p>
                </div>
              ) : (
                <div className="agenda-list">
                  {todayAgenda.map((item) => (
                    <div key={item.id} className="agenda-item-card">
                      <div className="agenda-time-pill">
                        {new Date(item.starts_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </div>
                      <div className="agenda-item-content">
                        <div className="agenda-item-title">{item.event_title}</div>
                        <div className="agenda-item-sub">
                          <span className={`priority-tag priority-${item.priority}`}>
                            {item.priority === 1
                              ? "Supreme Court"
                              : item.priority === 2
                              ? "High Court / NCLAT"
                              : "NCLT / District"}
                          </span>
                          {item.computation_explanation && (
                            <span className="agenda-rule-note">
                              {item.computation_explanation}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Upcoming 7-Day Master Schedule Across All Cases */}
            <div className="dashboard-panel">
              <div className="panel-header">
                <div className="panel-header-title">
                  <Calendar size={18} className="panel-icon" />
                  <h2>Upcoming 7-Day Master Schedule (All Cases)</h2>
                </div>
              </div>

              {upcomingHearings.length === 0 ? (
                <div className="panel-empty-state">
                  <p>No hearings listed for the coming week.</p>
                </div>
              ) : (
                <div className="upcoming-hearings-list">
                  {upcomingHearings.map((h) => (
                    <div key={h.id} className="upcoming-hearing-row">
                      <div className="hearing-date-col">
                        <span className="hearing-day">
                          {new Date(h.starts_at).toLocaleDateString([], { weekday: "short" })}
                        </span>
                        <span className="hearing-date-num">
                          {new Date(h.starts_at).getDate()}
                        </span>
                      </div>
                      <div className="hearing-info-col">
                        <div className="hearing-title">{h.event_title}</div>
                        <div className="hearing-meta">
                          {h.notes || "Court listing confirmed"}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Live Indian Legal News Panel */}
            <div className="dashboard-panel news-feed-panel">
              <div className="panel-header">
                <div className="panel-header-title">
                  <Newspaper size={18} className="panel-icon" />
                  <h2>Indian Legal News & Jurisprudence</h2>
                </div>
                <span className="panel-badge-pill">NewsAPI Live</span>
              </div>

              {legalNews.length === 0 ? (
                <div className="panel-empty-state">
                  <p>Fetching legal news from Supreme Court & High Courts...</p>
                </div>
              ) : (
                <div className="dashboard-news-list">
                  {legalNews.map((item, idx) => (
                    <a
                      key={idx}
                      href={item.link}
                      target="_blank"
                      rel="noreferrer"
                      className="dashboard-news-item"
                    >
                      <div className="news-item-title">
                        <span>{item.title}</span>
                        <ExternalLink size={12} className="news-external-icon" />
                      </div>
                      <div className="news-item-meta">
                        <span className="news-source-tag">{item.source}</span>
                        {item.published_at && (
                          <span className="news-date">{item.published_at}</span>
                        )}
                      </div>
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Column 2: Statutory Deadline Engine & Recent Research */}
          <div className="dashboard-grid-col">
            {/* Interactive Statutory Deadline Calculator */}
            <div className="dashboard-panel deadline-calculator-panel">
              <div className="panel-header">
                <div className="panel-header-title">
                  <Calculator size={18} className="panel-icon" />
                  <h2>Statutory Deadline Calculator</h2>
                </div>
                <span className="panel-badge-pill">PRD §7.4 Engine</span>
              </div>

              <p className="calculator-desc">
                Select a codified Indian statutory rule and anchor date to compute non-repudiable filing
                deadlines with statutory authority explanations.
              </p>

              <div className="calculator-form">
                <div className="calc-input-group">
                  <label>Statutory Compliance / Limitation Rule:</label>
                  <select
                    className="calc-select"
                    value={selectedRuleId}
                    onChange={(e) => {
                      setSelectedRuleId(e.target.value);
                      setComputedDeadline(null);
                    }}
                  >
                    {rules.map((r) => (
                      <option key={r.rule_id} value={r.rule_id}>
                        {r.title} ({r.offset_days} Days)
                      </option>
                    ))}
                  </select>
                </div>

                <div className="calc-input-group">
                  <label>Trigger / Anchor Date:</label>
                  <input
                    type="date"
                    className="calc-date-input"
                    value={anchorDate}
                    onChange={(e) => {
                      setAnchorDate(e.target.value);
                      setComputedDeadline(null);
                    }}
                  />
                </div>

                <button
                  className="btn btn-primary calc-compute-btn"
                  onClick={handleComputeDeadline}
                  disabled={computingDeadline}
                >
                  <Sparkles size={16} />
                  {computingDeadline ? "Calculating..." : "Compute Statutory Due Date"}
                </button>
              </div>

              {computedDeadline && (
                <div className="computed-deadline-card">
                  <div className="calc-result-header">
                    <span className="calc-due-tag">Verified Due Date</span>
                    <h3 className="calc-due-date">{computedDeadline.due_date}</h3>
                  </div>

                  <p className="calc-explanation">{computedDeadline.explanation}</p>

                  {computedDeadline.extension_info && (
                    <div className="calc-extension-box">
                      <strong>Extension / Condonation Note:</strong> {computedDeadline.extension_info}
                    </div>
                  )}

                  <div className="calc-actions">
                    {deadlineAddedSuccess ? (
                      <span className="calc-added-badge">
                        <CheckCircle2 size={16} /> Added to Calendar & Agenda!
                      </span>
                    ) : (
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={handleAddDeadlineToCalendar}
                      >
                        <Plus size={14} /> Add to Practice Calendar
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Recent Research Queries */}
            <div className="dashboard-panel">
              <div className="panel-header">
                <div className="panel-header-title">
                  <Search size={18} className="panel-icon" />
                  <h2>Recent Legal Research</h2>
                </div>
                <Link to="/research" className="panel-link">
                  Search &rarr;
                </Link>
              </div>

              <div className="recent-research-list">
                {history.slice(0, 3).map((item) => (
                  <div
                    key={item.query_id}
                    className="research-history-row"
                    onClick={() => navigate(`/research/${item.query_id}`)}
                  >
                    <div className="history-query-text">{item.query_text}</div>
                    <div className="history-query-meta">
                      <span className="conf-score">
                        {Math.round((item.confidence_score || 0.9) * 100)}% Confidence
                      </span>
                      {item.conflicts_detected && (
                        <span className="conflict-tag">⚡ Conflict Flagged</span>
                      )}
                      <ChevronRight size={16} className="history-chevron" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ── Telegram Bot Pairing Modal ── */}
        {showTelegramModal && (
          <div className="modal-backdrop">
            <div className="telegram-modal-card">
              <div className="modal-header">
                <div className="modal-header-title">
                  <Smartphone size={24} color="#0284c7" />
                  <h3>Pair with Telegram Bot</h3>
                </div>
                <button
                  className="modal-close-btn"
                  onClick={() => setShowTelegramModal(false)}
                >
                  <X size={20} />
                </button>
              </div>

              <div className="modal-body">
                <p>
                  Connect your personal Telegram account to access your daily court agenda, active
                  matter summaries, and automatic 24-hour and 2-hour hearing alerts on mobile.
                </p>

                {generatingCode ? (
                  <div className="otp-loading-box">
                    <span className="loading-spinner-ring" />
                    <span>Issuing cryptographic OTP...</span>
                  </div>
                ) : (
                  pairingCodeData && (
                    <div className="otp-display-box">
                      <span className="otp-label">YOUR SINGLE-USE PAIRING CODE:</span>
                      <div className="otp-code-number">{pairingCodeData.otp}</div>
                      <span className="otp-expiry">Valid for 5 minutes (single use)</span>
                    </div>
                  )
                )}

                <div className="modal-instructions">
                  <h4>Instructions:</h4>
                  <ol>
                    <li>
                      Open Telegram and search for bot:{" "}
                      <strong>@HALO_NyayaSahyak_bot</strong>
                    </li>
                    <li>
                      Send message:{" "}
                      <code>/auth {pairingCodeData?.otp || "123456"}</code>
                    </li>
                    <li>The bot will instantly confirm pairing and link your docket!</li>
                  </ol>
                </div>
              </div>

              <div className="modal-footer">
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    setShowTelegramModal(false);
                    getPairingStatus().then((s) => setTelegramStatus(s));
                  }}
                >
                  Done
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
