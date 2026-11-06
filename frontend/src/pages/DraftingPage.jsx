/**
 * src/pages/DraftingPage.jsx
 * ──────────────────────────
 * Grounded Legal Auto-Drafting Studio & Smart Forms Workspace — PRD Phase 2 (v2.1)
 *
 * Implements:
 * - Smart Forms Directory with instant search and category filtering
 * - Dedicated Form Workspace Window (similar to Case Workspace)
 * - Unified AI Intake Assistant: Chat Q&A + Document Upload (Aadhaar, PAN, Cheque, Bills)
 * - Multilingual Engine: English, हिंदी Devnagari, and Bilingual (द्विभाषी)
 * - Real-Time Live Court-Ready Document Preview
 * - Direct 1-Click Export to .DOCX and .PDF with embedded SHA-256 seal
 */

import React, { useState, useEffect, useRef } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  FileText,
  Search,
  CheckCircle2,
  Download,
  Eye,
  RefreshCw,
  ArrowRight,
  ArrowLeft,
  Shield,
  Layers,
  Clock,
  Briefcase,
  AlertTriangle,
  Copy,
  ExternalLink,
  Sparkles,
  Paperclip,
  Upload,
  Send,
  Languages,
  Bot,
  User as UserIcon,
  X,
  FileCheck,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import AppShell from "../components/AppShell";
import DynamicFormRenderer from "../components/DynamicFormRenderer";
import { getCurrentUser } from "../api/client";
import {
  listTemplates,
  getTemplate,
  createDraft,
  getDraft,
  autosaveDraftInputs,
  generateDraft,
  getDraftPreview,
  exportDraft,
  smartIntake,
} from "../api/draftingApi";
import { listMatters } from "../api/workspaceApi";
import "./DraftingPage.css";

const CATEGORIES = [
  { id: "ALL", label: "All Templates" },
  { id: "AGREEMENT", label: "Agreements & Leases" },
  { id: "NOTICE", label: "Statutory Notices" },
  { id: "CORPORATE_RESOLUTION", label: "Board Resolutions" },
  { id: "PETITION", label: "NCLT Petitions" },
  { id: "AFFIDAVIT", label: "Affidavits" },
  { id: "COMPLIANCE", label: "ROC Compliance" },
];

function readFileAsTextOrBase64(file) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    if (
      file.type.includes("text") ||
      file.name.endsWith(".txt") ||
      file.name.endsWith(".json") ||
      file.name.endsWith(".csv")
    ) {
      reader.onload = () => resolve(reader.result);
      reader.readAsText(file);
    } else {
      reader.onload = () => resolve(reader.result);
      reader.readAsDataURL(file);
    }
  });
}

export default function DraftingPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preselectTemplateId = searchParams.get("template");

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Gallery state
  const [templates, setTemplates] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Workspace / View state: 'gallery' | 'workspace'
  const [viewMode, setViewMode] = useState("gallery");
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [templateDetail, setTemplateDetail] = useState(null);
  const [matters, setMatters] = useState([]);
  const [selectedMatterId, setSelectedMatterId] = useState("");

  // Target Language: 'en' | 'hi' | 'bilingual'
  const [targetLanguage, setTargetLanguage] = useState("en");

  // Form values & validation
  const [formValues, setFormValues] = useState({});
  const [formErrors, setFormErrors] = useState({});
  const [currentDraftId, setCurrentDraftId] = useState(null);
  const [saveStatus, setSaveStatus] = useState("saved"); // 'saving' | 'saved' | 'idle'
  const [completionPercent, setCompletionPercent] = useState(0);

  // Left Pane Active Sub-tab: 'ai_intake' | 'form_inputs'
  const [leftTab, setLeftTab] = useState("ai_intake");

  // AI Intake Chat Stream
  const [intakeMessages, setIntakeMessages] = useState([]);
  const [intakeInput, setIntakeInput] = useState("");
  const [attachedFile, setAttachedFile] = useState(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  // Live Preview State
  const [previewHtml, setPreviewHtml] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [exportingFormat, setExportingFormat] = useState(null);

  const autosaveTimerRef = useRef(null);
  const chatBottomRef = useRef(null);
  const fileInputRef = useRef(null);

  // 1. Initial Data Load
  useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        const [userData, tmpls, matterList] = await Promise.all([
          getCurrentUser().catch(() => null),
          listTemplates(),
          listMatters().catch(() => []),
        ]);
        setUser(userData);
        setTemplates(tmpls || []);
        setMatters(matterList || []);

        if (preselectTemplateId) {
          const match = (tmpls || []).find((t) => t.id === preselectTemplateId);
          if (match) {
            handleSelectTemplate(match);
          }
        }
      } catch (err) {
        setError(err.message || "Failed to load drafting studio data.");
      } finally {
        setLoading(false);
      }
    }
    init();
  }, [preselectTemplateId]);

  // Scroll chat to bottom on new messages
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [intakeMessages]);

  // 2. Select Template & Open Dedicated Form Workspace Window
  async function handleSelectTemplate(tmpl) {
    try {
      setLoading(true);
      setError(null);
      setSelectedTemplate(tmpl);
      const detail = await getTemplate(tmpl.id);
      setTemplateDetail(detail);

      // Default language from schema if present
      const langField = detail.schema_definition?.fields?.find((f) => f.id === "target_language");
      const defaultLang = langField?.default || "en";
      setTargetLanguage(defaultLang);

      // Prepopulate default field values from schema
      const initial = { target_language: defaultLang };
      if (detail.schema_definition?.fields) {
        detail.schema_definition.fields.forEach((f) => {
          if (f.default !== undefined) initial[f.id] = f.default;
        });
      }
      setFormValues(initial);
      setFormErrors({});

      // Create draft record
      const draftRes = await createDraft(tmpl.id, tmpl.name, selectedMatterId || null, initial);
      const draftId = draftRes.draft?.id || null;
      setCurrentDraftId(draftId);

      // Load initial live preview HTML
      if (draftId) {
        setPreviewLoading(true);
        try {
          const initialHtml = await getDraftPreview(draftId);
          setPreviewHtml(initialHtml);
        } catch (previewErr) {
          console.warn("Initial preview error:", previewErr);
        } finally {
          setPreviewLoading(false);
        }
      }

      // Generate initial AI welcome message tailored to this specific legal instrument
      let initialAiGreeting = "";
      if (tmpl.id.includes("RENT")) {
        initialAiGreeting =
          `👋 **Welcome to the Smart Rent & Lease Studio!**\n\n` +
          `I will help you draft an airtight, court-ready **Residential & Commercial Lease Agreement** pursuant to the *Transfer of Property Act, 1882*.\n\n` +
          `**How you can proceed:**\n` +
          `• **Type or answer prompts**: e.g., *"Landlord is Ramesh Sharma, monthly rent ₹35,000, 11 months tenure, deposit ₹70,000"*.\n` +
          `• **Upload documents**: Drop electricity bills, rent receipts, or Aadhaar/PAN cards below (or click 📎) to auto-extract details.\n` +
          `• **Switch language**: Select English, हिंदी Devnagari, or Bilingual anytime above!`;
      } else if (tmpl.id.includes("138")) {
        initialAiGreeting =
          `👋 **Welcome to the Section 138 Cheque Bounce Notice Studio!**\n\n` +
          `I will assist you in generating a statutory **15-Day Demand Notice** pursuant to *Section 138 proviso (b) of the Negotiable Instruments Act, 1881*.\n\n` +
          `**How you can proceed:**\n` +
          `• **Upload photos / scan**: Drop a photo of the dishonoured cheque leaf and bank return memo.\n` +
          `• **Or type directly**: Provide drawer name, cheque number, amount, date of dishonour, and return memo reason.\n` +
          `• All mandatory statutory recitals will be verified and formatted with live preview on the right.`;
      } else if (tmpl.id.includes("NDA")) {
        initialAiGreeting =
          `👋 **Welcome to the Commercial NDA Studio!**\n\n` +
          `We will prepare a comprehensive **Non-Disclosure Agreement (NDA)** pursuant to the *Indian Contract Act, 1872* with trade secret protection and injunctive relief covenants.\n\n` +
          `**How you can proceed:**\n` +
          `• Tell me the Disclosing and Receiving parties, term of confidentiality, and purpose of disclosure.\n` +
          `• Or upload a term sheet / preliminary engagement letter to auto-populate.`;
      } else if (tmpl.id.includes("CONSULTANT")) {
        initialAiGreeting =
          `👋 **Welcome to the Independent Consultant Agreement Studio!**\n\n` +
          `Let's draft an independent contractor engagement agreement with intellectual property assignment and fee covenants.\n\n` +
          `**How you can proceed:**\n` +
          `• Provide client company details, consultant name, scope of services, and agreed fee amount.\n` +
          `• Or upload a statement of work (SOW) or offer letter to extract parameters automatically.`;
      } else {
        initialAiGreeting =
          `👋 **Welcome to the Smart Drafting Studio for ${tmpl.name}!**\n\n` +
          `Governed by **${tmpl.statutory_anchor}**.\n\n` +
          `You can converse in natural language, upload supporting documents, or switch to the structured form view anytime.`;
      }

      setIntakeMessages([
        {
          id: `ai_init_${Date.now()}`,
          sender: "ai",
          text: initialAiGreeting,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);

      // Calculate initial completion
      const reqFields = (detail.schema_definition?.fields || []).filter((f) => f.required);
      const filledReq = reqFields.filter((f) => initial[f.id] !== undefined && initial[f.id] !== "");
      setCompletionPercent(
        reqFields.length > 0 ? Math.round((filledReq.length / reqFields.length) * 100) : 100
      );

      setViewMode("workspace");
    } catch (err) {
      setError("Failed to open form workspace: " + err.message);
    } finally {
      setLoading(false);
    }
  }

  // 3. Switch Language (English / Hindi / Bilingual)
  async function handleLanguageChange(lang) {
    setTargetLanguage(lang);
    const nextValues = { ...formValues, target_language: lang };
    setFormValues(nextValues);

    if (currentDraftId) {
      setPreviewLoading(true);
      try {
        await autosaveDraftInputs(currentDraftId, nextValues);
        const updatedHtml = await getDraftPreview(currentDraftId);
        setPreviewHtml(updatedHtml);
      } catch (err) {
        console.warn("Failed to update language preview:", err);
      } finally {
        setPreviewLoading(false);
      }
    }
  }

  // 4. Handle Direct Field Changes with Autosave
  function handleFieldChange(fieldId, value) {
    const next = { ...formValues, [fieldId]: value };
    setFormValues(next);

    if (formErrors[fieldId]) {
      setFormErrors((prev) => {
        const copy = { ...prev };
        delete copy[fieldId];
        return copy;
      });
    }

    // Trigger debounced autosave & preview refresh
    setSaveStatus("saving");
    if (autosaveTimerRef.current) clearTimeout(autosaveTimerRef.current);

    autosaveTimerRef.current = setTimeout(async () => {
      if (!currentDraftId) return;
      try {
        await autosaveDraftInputs(currentDraftId, next);
        setSaveStatus("saved");
        const updatedPreview = await getDraftPreview(currentDraftId);
        setPreviewHtml(updatedPreview);
      } catch {
        setSaveStatus("idle");
      }
    }, 800);
  }

  // 5. Send Message / Document to AI Intake Assistant
  async function handleSendIntakeMessage(overrideText = null, overrideFile = null) {
    const textToSend = overrideText !== null ? overrideText : intakeInput.trim();
    const fileToUpload = overrideFile || attachedFile;

    if (!textToSend && !fileToUpload) return;

    setIsExtracting(true);
    setError(null);

    // Add user message to chat UI immediately
    const userMsg = {
      id: `u_${Date.now()}`,
      sender: "user",
      text: textToSend,
      file: fileToUpload ? { name: fileToUpload.name, size: fileToUpload.size } : null,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setIntakeMessages((prev) => [...prev, userMsg]);
    setIntakeInput("");
    setAttachedFile(null);

    try {
      let fileContent = "";
      let fileName = "";
      if (fileToUpload) {
        fileName = fileToUpload.name;
        fileContent = await readFileAsTextOrBase64(fileToUpload);
      }

      // Call backend Smart Intake endpoint
      const intakeRes = await smartIntake(
        selectedTemplate.id,
        textToSend,
        fileContent,
        fileName,
        formValues,
        targetLanguage
      );

      const updatedInputs = intakeRes.updated_inputs || {};
      setFormValues(updatedInputs);
      if (intakeRes.completion_percent !== undefined) {
        setCompletionPercent(intakeRes.completion_percent);
      }

      // Save to draft version and refresh live preview immediately
      if (currentDraftId) {
        await autosaveDraftInputs(currentDraftId, updatedInputs);
        const updatedPreview = await getDraftPreview(currentDraftId);
        setPreviewHtml(updatedPreview);
      }

      // Add AI response to chat
      const aiMsg = {
        id: `ai_${Date.now()}`,
        sender: "ai",
        text: intakeRes.ai_response,
        extracted: intakeRes.newly_extracted_fields || [],
        missing: intakeRes.missing_fields || [],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setIntakeMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      setError("AI intake failed: " + err.message);
    } finally {
      setIsExtracting(false);
    }
  }

  // 6. Handle File Drag & Drop
  function handleDragOver(e) {
    e.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave(e) {
    e.preventDefault();
    setIsDragging(false);
  }

  function handleFileDrop(e) {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
      handleSendIntakeMessage("", files[0]);
    }
  }

  function handleFileInputChange(e) {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleSendIntakeMessage("", files[0]);
    }
    e.target.value = "";
  }

  // 7. Direct Export Download (PDF / DOCX)
  async function handleDownloadExport(format) {
    if (!currentDraftId) return;
    setExportingFormat(format);
    try {
      // Ensure latest values are saved
      await autosaveDraftInputs(currentDraftId, formValues);
      const res = await exportDraft(currentDraftId, format, true);
      if (res.download_url) {
        window.open(res.download_url, "_blank");
      }
    } catch (err) {
      alert(`Export to ${format.toUpperCase()} failed: ` + err.message);
    } finally {
      setExportingFormat(null);
    }
  }

  // Filter templates for Catalog view
  const filteredTemplates = templates.filter((t) => {
    const matchCat =
      selectedCategory === "ALL" ||
      t.category === selectedCategory ||
      (selectedCategory === "AGREEMENT" && (t.category === "AGREEMENT" || t.id.includes("RENT") || t.id.includes("NDA") || t.id.includes("CONSULTANT")));
    const matchSearch =
      !searchQuery ||
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.statutory_anchor?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.description?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchCat && matchSearch;
  });

  return (
    <AppShell user={user}>
      <div className="drafting-page-root">
        {error && (
          <div className="drafting-alert error-alert">
            <AlertTriangle size={18} />
            <span>{error}</span>
            <button className="alert-close-btn" onClick={() => setError(null)}>
              <X size={14} />
            </button>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════════════
            VIEW 1: TEMPLATES CATALOG & SMART FORMS DIRECTORY
        ═══════════════════════════════════════════════════════════════════ */}
        {viewMode === "gallery" && (
          <div className="drafting-gallery-view">
            {/* Header Dossier */}
            <div className="catalog-header-bar">
              <div>
                <h1 className="catalog-title">Legal Forms & Auto-Drafting Studio</h1>
                <p className="catalog-subtitle">
                  Court-ready statutory pleadings, commercial agreements, and corporate resolutions. Fill automatically via intelligent conversational intake or document upload with 1-click DOCX & PDF exports.
                </p>
              </div>
              <div className="catalog-stats-pill">
                <FileCheck size={16} />
                <span>{templates.length || 10} Court-Approved Templates</span>
              </div>
            </div>

            {/* Search & Category Filter Controls */}
            <div className="gallery-toolbar">
              <div className="gallery-search-wrap">
                <Search size={18} className="search-icon" />
                <input
                  type="text"
                  placeholder="Search forms by title, statutory act (e.g., Rent Agreement, Section 138, NDA, Companies Act)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="gallery-search-input"
                />
                {searchQuery && (
                  <button className="search-clear-btn" onClick={() => setSearchQuery("")}>
                    <X size={16} />
                  </button>
                )}
              </div>

              <div className="gallery-pills">
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat.id}
                    className={`gallery-pill ${selectedCategory === cat.id ? "active" : ""}`}
                    onClick={() => setSelectedCategory(cat.id)}
                  >
                    {cat.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Template Cards Grid */}
            <div className="template-cards-grid">
              {filteredTemplates.map((tmpl) => (
                <div key={tmpl.id} className="template-card">
                  <div className="template-card-header">
                    <span className="template-cat-badge">
                      {tmpl.category === "AGREEMENT"
                        ? "Agreement & Lease"
                        : tmpl.category.replace("_", " ")}
                    </span>
                    <span className="template-lang-pill">🌐 EN • HI • द्विभाषी</span>
                  </div>

                  <h3 className="template-card-title">{tmpl.name}</h3>
                  <p className="template-card-anchor">🏛️ {tmpl.statutory_anchor}</p>
                  <p className="template-card-desc">{tmpl.description}</p>

                  <div className="template-card-footer">
                    <span className="template-format-tag">DOCX • PDF</span>
                    <button
                      className="btn btn-primary"
                      onClick={() => handleSelectTemplate(tmpl)}
                    >
                      Open Smart Workspace <ArrowRight size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════════════
            VIEW 2: DEDICATED FORM WORKSPACE WINDOW (Split View)
        ═══════════════════════════════════════════════════════════════════ */}
        {viewMode === "workspace" && selectedTemplate && (
          <div className="form-workspace-window">
            {/* ── Breadcrumb Bar ── */}
            <div className="workspace-breadcrumb-bar">
              <button
                className="breadcrumb-back-link"
                onClick={() => {
                  setViewMode("gallery");
                  setSelectedTemplate(null);
                  setCurrentDraftId(null);
                }}
              >
                <ArrowLeft size={14} style={{ marginRight: 6 }} />
                Back to Forms Catalog
              </button>
              <span className="breadcrumb-divider">/</span>
              <span className="breadcrumb-category">
                {selectedTemplate.category === "AGREEMENT" ? "Agreements" : "Legal Forms"}
              </span>
              <span className="breadcrumb-divider">/</span>
              <span className="breadcrumb-current-title">{selectedTemplate.name}</span>
            </div>

            {/* ── Workspace Header Dossier (Modeled after Case Workspace) ── */}
            <header className="workspace-header-dossier">
              <div className="dossier-left">
                <div className="dossier-title-row">
                  <h1 className="dossier-main-title">{selectedTemplate.name}</h1>
                  <span className="dossier-status-badge">
                    <Sparkles size={12} style={{ marginRight: 4 }} />
                    AI Intake Active
                  </span>
                </div>

                <div className="dossier-meta-row">
                  <div className="dossier-meta-item">
                    <span className="meta-tag-label">Governing Provision:</span>
                    <span className="meta-tag-value">🏛️ {selectedTemplate.statutory_anchor}</span>
                  </div>

                  {/* Multilingual Switcher Pills */}
                  <div className="dossier-meta-item language-switch-item">
                    <span className="meta-tag-label">Document Language:</span>
                    <div className="lang-switcher-pills">
                      <button
                        className={`lang-pill-btn ${targetLanguage === "en" ? "active" : ""}`}
                        onClick={() => handleLanguageChange("en")}
                      >
                        English
                      </button>
                      <button
                        className={`lang-pill-btn ${targetLanguage === "hi" ? "active" : ""}`}
                        onClick={() => handleLanguageChange("hi")}
                      >
                        हिंदी (Hindi)
                      </button>
                      <button
                        className={`lang-pill-btn ${targetLanguage === "bilingual" ? "active" : ""}`}
                        onClick={() => handleLanguageChange("bilingual")}
                      >
                        द्विभाषी (Bilingual)
                      </button>
                    </div>
                  </div>

                  {/* Progress Meter */}
                  <div className="dossier-meta-item progress-meter-item">
                    <span className="meta-tag-label">Form Completion:</span>
                    <div className="completion-bar-wrap">
                      <div
                        className="completion-bar-fill"
                        style={{ width: `${completionPercent}%` }}
                      />
                    </div>
                    <span className="completion-text">{completionPercent}%</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons: Direct 1-Click Exports */}
              <div className="dossier-right-actions">
                <button
                  className="btn btn-secondary btn-export"
                  onClick={() => handleDownloadExport("docx")}
                  disabled={exportingFormat === "docx"}
                  title="Download editable Microsoft Word document"
                >
                  <FileText size={16} />
                  <span>{exportingFormat === "docx" ? "Exporting..." : "Download DOCX"}</span>
                </button>

                <button
                  className="btn btn-primary btn-export"
                  onClick={() => handleDownloadExport("pdf")}
                  disabled={exportingFormat === "pdf"}
                  title="Download court-admissible PDF with cryptographic SHA-256 seal"
                >
                  <Download size={16} />
                  <span>{exportingFormat === "pdf" ? "Exporting..." : "Download PDF"}</span>
                </button>
              </div>
            </header>

            {/* ── Two-Pane Split Workbench ── */}
            <div className="workspace-split-workbench">
              {/* ════════════ LEFT PANE: AI INTAKE & DIRECT EDIT ════════════ */}
              <div className="split-pane split-pane-left">
                {/* Sub-tab Navigation */}
                <div className="pane-subtabs-bar">
                  <button
                    className={`pane-subtab-btn ${leftTab === "ai_intake" ? "active" : ""}`}
                    onClick={() => setLeftTab("ai_intake")}
                  >
                    <Bot size={15} />
                    <span>AI Smart Intake & Upload</span>
                  </button>

                  <button
                    className={`pane-subtab-btn ${leftTab === "form_inputs" ? "active" : ""}`}
                    onClick={() => setLeftTab("form_inputs")}
                  >
                    <Layers size={15} />
                    <span>Structured Form Fields</span>
                    <span className="subtab-count">
                      {templateDetail?.schema_definition?.fields?.length || 8}
                    </span>
                  </button>

                  <div className="autosave-indicator">
                    {saveStatus === "saving" && <span>💾 Saving...</span>}
                    {saveStatus === "saved" && <span>✓ Saved</span>}
                  </div>
                </div>

                {/* Sub-tab 1: Conversational AI Intake + Drag & Drop Upload */}
                {leftTab === "ai_intake" && (
                  <div className="intake-tab-content">
                    {/* Chat Messages Stream */}
                    <div className="intake-chat-feed">
                      {intakeMessages.map((msg) => (
                        <div
                          key={msg.id}
                          className={`chat-bubble-wrap bubble-${msg.sender === "user" ? "user" : "ai"}`}
                        >
                          <div className="chat-avatar">
                            {msg.sender === "user" ? <UserIcon size={14} /> : <Bot size={14} />}
                          </div>

                          <div className="chat-bubble">
                            {msg.file && (
                              <div className="chat-attached-file-badge">
                                <Paperclip size={13} />
                                <span>{msg.file.name}</span>
                                <span className="file-size-tag">
                                  ({Math.round(msg.file.size / 1024)} KB)
                                </span>
                              </div>
                            )}

                            <div className="markdown-prose">
                              <ReactMarkdown>{msg.text}</ReactMarkdown>
                            </div>

                            {msg.extracted && msg.extracted.length > 0 && (
                              <div className="extracted-fields-pill-row">
                                <span className="extracted-label">Extracted:</span>
                                {msg.extracted.map((fName) => (
                                  <span key={fName} className="extracted-field-tag">
                                    ✓ {fName}
                                  </span>
                                ))}
                              </div>
                            )}

                            <span className="chat-timestamp">{msg.timestamp}</span>
                          </div>
                        </div>
                      ))}

                      {isExtracting && (
                        <div className="chat-bubble-wrap bubble-ai">
                          <div className="chat-avatar">
                            <Bot size={14} />
                          </div>
                          <div className="chat-bubble extracting-indicator">
                            <span className="loading-spinner-ring" />
                            <span>Parsing document and verifying legal parameters...</span>
                          </div>
                        </div>
                      )}
                      <div ref={chatBottomRef} />
                    </div>

                    {/* Quick Suggestion Prompt Chips */}
                    <div className="intake-suggestion-chips">
                      {selectedTemplate.id.includes("RENT") && (
                        <>
                          <button
                            type="button"
                            className="suggestion-chip"
                            onClick={() =>
                              handleSendIntakeMessage(
                                "Monthly rent ₹25,000, 11 months tenure, security deposit ₹50,000"
                              )
                            }
                          >
                            ₹25k Rent / 11m Tenure
                          </button>
                          <button
                            type="button"
                            className="suggestion-chip"
                            onClick={() =>
                              handleSendIntakeMessage(
                                "Lock-in period 1 month, notice period 30 days"
                              )
                            }
                          >
                            1m Lock-in / 30d Notice
                          </button>
                        </>
                      )}

                      {selectedTemplate.id.includes("138") && (
                        <>
                          <button
                            type="button"
                            className="suggestion-chip"
                            onClick={() =>
                              handleSendIntakeMessage(
                                "Cheque returned with memo 'Funds Insufficient' on 20-Oct-2026"
                              )
                            }
                          >
                            Dishonour: Funds Insufficient
                          </button>
                          <button
                            type="button"
                            className="suggestion-chip"
                            onClick={() =>
                              handleSendIntakeMessage("Statutory 15-day demand notice window")
                            }
                          >
                            15-Day Demand Notice
                          </button>
                        </>
                      )}

                      {selectedTemplate.id.includes("NDA") && (
                        <button
                          type="button"
                          className="suggestion-chip"
                          onClick={() =>
                            handleSendIntakeMessage(
                              "Mutual confidentiality for a period of 2 years under Delhi jurisdiction"
                            )
                          }
                        >
                          Mutual NDA / 2 Years
                        </button>
                      )}

                      <button
                        type="button"
                        className="suggestion-chip"
                        onClick={() => handleLanguageChange(targetLanguage === "hi" ? "en" : "hi")}
                      >
                        {targetLanguage === "hi" ? "Switch to English" : "Switch to हिंदी"}
                      </button>
                    </div>

                    {/* Drag & Drop File Upload Strip */}
                    <div
                      className={`intake-dropzone-strip ${isDragging ? "dragging" : ""}`}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleFileDrop}
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <Upload size={16} className="dropzone-icon" />
                      <span>
                        Drag & drop <strong>Aadhaar, PAN, Cheque, Bill or Draft</strong> here, or{" "}
                        <span className="browse-link">browse</span>
                      </span>
                      <input
                        type="file"
                        ref={fileInputRef}
                        style={{ display: "none" }}
                        onChange={handleFileInputChange}
                        accept=".txt,.pdf,.png,.jpg,.jpeg,.json,.csv"
                      />
                    </div>

                    {/* Chat Input Bar with 📎 Attachment */}
                    <form
                      className="intake-input-bar"
                      onSubmit={(e) => {
                        e.preventDefault();
                        handleSendIntakeMessage();
                      }}
                    >
                      <button
                        type="button"
                        className="input-attach-btn"
                        title="Attach Document (Aadhaar, Cheque photo, Return memo, Bill)"
                        onClick={() => fileInputRef.current?.click()}
                      >
                        <Paperclip size={18} />
                      </button>

                      <input
                        type="text"
                        placeholder="Type legal details or answer questions (e.g., Landlord is Ramesh Sharma, monthly rent ₹35,000)..."
                        value={intakeInput}
                        onChange={(e) => setIntakeInput(e.target.value)}
                        className="intake-text-input"
                        disabled={isExtracting}
                      />

                      <button
                        type="submit"
                        className="input-send-btn"
                        disabled={isExtracting || (!intakeInput.trim() && !attachedFile)}
                      >
                        <Send size={16} />
                      </button>
                    </form>
                  </div>
                )}

                {/* Sub-tab 2: Direct Structured Form Field Inputs */}
                {leftTab === "form_inputs" && templateDetail && (
                  <div className="inputs-tab-content">
                    {/* Matter Link Selector */}
                    <div className="matter-attachment-bar">
                      <Briefcase size={15} />
                      <label>Attach to Client Matter:</label>
                      <select
                        className="matter-select-input"
                        value={selectedMatterId}
                        onChange={(e) => setSelectedMatterId(e.target.value)}
                      >
                        <option value="">-- Standalone Instrument (No Matter Attached) --</option>
                        {matters.map((m) => (
                          <option key={m.id} value={m.id}>
                            {m.matter_name} ({m.forum_type})
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="dynamic-form-wrap">
                      <DynamicFormRenderer
                        schema={templateDetail.schema_definition}
                        values={formValues}
                        onChange={handleFieldChange}
                        errors={formErrors}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* ════════════ RIGHT PANE: REAL-TIME COURT-READY PREVIEW ════════════ */}
              <div className="split-pane split-pane-right">
                <div className="preview-pane-header">
                  <div className="preview-title-wrap">
                    <Eye size={16} className="preview-icon" />
                    <h3>Live Legal Document Preview</h3>
                    <span className="preview-lang-badge">
                      {targetLanguage === "hi"
                        ? "हिंदी (Devnagari)"
                        : targetLanguage === "bilingual"
                        ? "Bilingual (द्विभाषी)"
                        : "English"}
                    </span>
                  </div>

                  <div className="preview-actions-strip">
                    <button
                      className="btn btn-secondary btn-xs"
                      onClick={async () => {
                        if (!currentDraftId) return;
                        setPreviewLoading(true);
                        try {
                          const updated = await getDraftPreview(currentDraftId);
                          setPreviewHtml(updated);
                        } finally {
                          setPreviewLoading(false);
                        }
                      }}
                      title="Refresh Preview"
                    >
                      <RefreshCw size={13} className={previewLoading ? "spin" : ""} />
                      <span>Refresh</span>
                    </button>

                    <button
                      className="btn btn-secondary btn-xs"
                      onClick={() => handleDownloadExport("docx")}
                      disabled={exportingFormat === "docx"}
                    >
                      <FileText size={13} />
                      <span>DOCX</span>
                    </button>

                    <button
                      className="btn btn-primary btn-xs"
                      onClick={() => handleDownloadExport("pdf")}
                      disabled={exportingFormat === "pdf"}
                    >
                      <Download size={13} />
                      <span>PDF</span>
                    </button>
                  </div>
                </div>

                {/* Preview Document Viewport */}
                <div className="preview-viewport-card">
                  {previewLoading ? (
                    <div className="preview-loading-overlay">
                      <span className="loading-spinner-ring" />
                      <p>Rendering court-admissible layout...</p>
                    </div>
                  ) : previewHtml ? (
                    <iframe
                      title="Live Document Preview"
                      srcDoc={previewHtml}
                      className="preview-iframe-element"
                    />
                  ) : (
                    <div className="preview-placeholder">
                      <FileText size={48} color="#94a3b8" />
                      <p>Answer questions or upload a document to generate live preview.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
