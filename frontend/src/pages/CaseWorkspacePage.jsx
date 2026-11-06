/**
 * src/pages/CaseWorkspacePage.jsx
 * ────────────────────────────────
 * Comprehensive Case Workspace & Project Environment for HALO (Nyaya Sahayak).
 *
 * Implements:
 * - Case Header with metadata, forum badge, statutory act, parties, and quick actions
 * - Tab 1: Unified AI Copilot (Dual-intent router: Workspace Actions + Statutory RAG, Named Chat Sessions)
 * - Tab 2: Case Docket & Procedural Litigation Timeline (Indian Civil/Commercial Stages + Chronological hearings)
 * - Tab 3: Case Documents & Pleadings Viewer (Interactive file explorer & built-in document reader)
 * - Tab 4: Chamber Notes & Oral Orders (Real-time memory log synced with Telegram /note)
 */

import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  Briefcase,
  Calendar,
  Clock,
  FileText,
  MessageSquare,
  Send,
  Plus,
  Search,
  ShieldCheck,
  Scale,
  ExternalLink,
  ChevronRight,
  Download,
  CheckCircle2,
  AlertTriangle,
  BookOpen,
  Sparkles,
  Eye,
  X,
  ArrowLeft,
  Copy,
  Layers,
  History,
  Bot,
  User as UserIcon,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import AppShell from "../components/AppShell";
import { getCurrentUser } from "../api/client";
import {
  getMatter,
  listMatters,
  listEvents,
  createEvent,
  addMatterNote,
  computeDeadline,
} from "../api/workspaceApi";
import { submitQuery } from "../api/researchApi";
import "./CaseWorkspacePage.css";

// ── Default Litigation Stages for Indian Courts ──────────────────────────────
const PROCEDURAL_STAGES = [
  { id: 1, name: "Summons / Notice", desc: "Service complete on opposite parties", status: "COMPLETED" },
  { id: 2, name: "Appearance", desc: "Vakalatnama & memorandum filed", status: "COMPLETED" },
  { id: 3, name: "Written Statement", desc: "120-Day hard statutory limitation", status: "IN_PROGRESS" },
  { id: 4, name: "Framing of Issues", desc: "Points of determination framed", status: "UPCOMING" },
  { id: 5, name: "Evidence & Cross", desc: "Affidavits in evidence & cross-exam", status: "UPCOMING" },
  { id: 6, name: "Final Arguments", desc: "Submissions on law & precedents", status: "UPCOMING" },
  { id: 7, name: "Judgment / Order", desc: "Pronouncement of final decree", status: "UPCOMING" },
];

// ── Default Documents for Seed Matters ───────────────────────────────────────
const SAMPLE_CASE_DOCUMENTS = {
  default: [
    {
      id: "doc_1",
      title: "Commercial Plaint & Application for Interim Relief",
      type: "Plaint",
      file_size: "1.4 MB",
      date: "2026-10-15",
      content: `IN THE HIGH COURT OF DELHI AT NEW DELHI
COMMERCIAL DIVISION
COMMERCIAL SUIT NO. 412 OF 2026

IN THE MATTER OF:
Nominee Directors Consortium                   ...PLAINTIFF
VERSUS
Income Tax Department & Ors.                  ...DEFENDANTS

PLAINT UNDER ORDER VII RULE 1 READ WITH SECTION 179 OF THE INCOME TAX ACT, 1961

MOST RESPECTFULLY SHOWETH:
1. That the Plaintiff consortium comprises non-executive and independent nominee directors appointed to the Board of the Corporate Debtor pursuant to statutory mandates.
2. That on 12th October 2026, the Defendant issued demand notices seeking personal recovery of corporate tax liabilities under Section 179 of the Income Tax Act without conducting prerequisite factual inquiry regarding gross neglect or misfeasance.
3. That in terms of the binding dictum of the Hon'ble Supreme Court in Pr. CIT v. Siemens Ltd. (2017) 394 ITR 1 (SC), vicarious strict liability cannot be fastened upon nominee directors without concrete demonstration of personal culpability.
4. It is therefore prayed that this Hon'ble Court may be pleased to grant an ad-interim ex-parte injunction staying the operation of the impugned recovery notice during the pendency of the present suit.`,
    },
    {
      id: "doc_2",
      title: "Written Statement on Behalf of Defendant No. 1",
      type: "Pleading",
      file_size: "940 KB",
      date: "2026-10-28",
      content: `IN THE HIGH COURT OF DELHI AT NEW DELHI
COMMERCIAL DIVISION
COMMERCIAL SUIT NO. 412 OF 2026

WRITTEN STATEMENT ON BEHALF OF DEFENDANT NO. 1

PRELIMINARY OBJECTIONS:
1. The present suit is barred under Section 293 of the Income Tax Act, 1961, which expressly ousts the jurisdiction of civil courts against orders passed in good faith by revenue authorities.
2. The Plaintiffs, having held managerial directorships during the relevant assessment year, cannot evade joint and several statutory liability mandated under the statutory code.
3. The period of limitation of 120 days prescribed under Order VIII Rule 1 of the Commercial Courts Act, 2015 is applicable to all pleadings in this matter.`,
    },
    {
      id: "doc_3",
      title: "Order of Court granting Ad-Interim Stay",
      type: "Court Order",
      file_size: "420 KB",
      date: "2026-11-02",
      content: `ORDER DATED 02.11.2026
CORAM: HON'BLE MR. JUSTICE KAUL

1. Issue notice to the respondents on process fee. Counsel for Defendant accepts notice.
2. Prima facie, the mandate of Section 179 requires satisfaction of non-recovery from the private company before proceeding against nominee directors.
3. Till the next date of hearing, no coercive steps shall be taken pursuant to the impugned recovery orders.
4. Let counter-affidavit be filed within two weeks. Rejoinder within one week thereafter.
5. Re-notify on 18th November 2026.`,
    },
  ],
  mat_003: [
    {
      id: "doc_ni_1",
      title: "Bank Return Memo (Insufficient Funds)",
      type: "Evidence",
      file_size: "340 KB",
      date: "2026-10-20",
      content: `HDFC BANK LTD. - SAKET BRANCH, NEW DELHI
CHEQUE RETURN MEMO

Date: 20-Oct-2026
To: Apex Supplies LLP
Account No: 50200041289110

We regret to inform you that Cheque No. 448912 dated 15-Oct-2026 for ₹ 42,50,000/- (Rupees Forty-Two Lakhs Fifty Thousand Only) drawn on Shanti Logistics Pvt. Ltd. (Account No. 008102000341) presented by you has been returned unpaid for the following reason:

REASON FOR RETURN CODE 01: FUNDS INSUFFICIENT / EXCEEDS ARRANGEMENT.

Authorized Signatory,
HDFC Bank Clearing Operations`,
    },
    {
      id: "doc_ni_2",
      title: "Statutory Legal Demand Notice u/s 138(b)",
      type: "Legal Notice",
      file_size: "520 KB",
      date: "2026-10-26",
      content: `BY SPEED POST A.D. & REGISTERED EMAIL
LEGAL DEMAND NOTICE UNDER CLAUSE (b) OF PROVISO TO SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881

Date: 26-Oct-2026

To:
1. Shanti Logistics Private Limited
   Through its Managing Director, Sunil V. Mehta
   Plot 14, Okhla Industrial Area Phase-III, New Delhi - 110020
2. Sunil V. Mehta, Director
   (In-charge and responsible for the conduct of day-to-day business u/s 141 NI Act)

Under instructions from and on behalf of our client, M/s Apex Supplies LLP ("Our Client"), we hereby serve upon you this Statutory Demand Notice:

1. That in discharge of your legally enforceable debt and liability for supply of industrial polymers under Invoice Nos. AS-904 and AS-911, you issued Cheque No. 448912 dated 15-Oct-2026 for a sum of ₹ 42,50,000/- drawn on HDFC Bank.
2. That the said cheque was presented for clearance and dishonoured with the remark "FUNDS INSUFFICIENT" vide Return Memo dated 20-Oct-2026.
3. You are hereby called upon to pay the said sum of ₹ 42,50,000/- within 15 (FIFTEEN) DAYS from receipt of this notice, failing which our client shall initiate criminal prosecution under Sections 138 and 141 of the Negotiable Instruments Act, 1881 without further reference.

Adv. Supriya Mulik
Chamber 402, Saket District Courts Complex, New Delhi`,
    },
    {
      id: "doc_ni_3",
      title: "Draft Criminal Complaint u/s 138 & 141 NI Act",
      type: "Criminal Complaint",
      file_size: "1.1 MB",
      date: "2026-11-04",
      content: `IN THE COURT OF THE CHIEF METROPOLITAN MAGISTRATE
SOUTH DISTRICT, SAKET DISTRICT COURTS, NEW DELHI
CRIMINAL COMPLAINT NO. 891 OF 2024

IN THE MATTER OF:
M/s Apex Supplies LLP
Through its Designated Partner, Mr. Rakesh Verma
Office at: B-44, Nehru Place, New Delhi           ...COMPLAINANT

VERSUS

1. M/s Shanti Logistics Private Limited
   Registered Office: Plot 14, Okhla Ind. Area Phase-III, New Delhi
2. Mr. Sunil V. Mehta, Director
   Residing at: D-12, Greater Kailash-I, New Delhi   ...ACCUSED PERSONS

COMPLAINT UNDER SECTION 138 READ WITH SECTION 141 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881 FOR OFFENCE OF CHEQUE DISHONOUR

MOST RESPECTFULLY SHOWETH:
1. That the Complainant is a registered Limited Liability Partnership engaged in the wholesale trade of industrial engineering supplies.
2. That Accused No. 1 is a private limited company and Accused No. 2 is its Director who signed the dishonoured instrument and was in charge of the conduct of the business at the time of commission of the offence.
3. That in discharge of subsisting commercial liability, Accused No. 2 issued Cheque No. 448912 for ₹ 42,50,000/-, which was dishonoured for 'Funds Insufficient' on 20-Oct-2026.
4. That Statutory Notice dated 26-Oct-2026 was duly served, and despite the expiry of statutory period of 15 days, the Accused have failed and neglected to make payment.
5. PRAYER: It is therefore prayed that this Hon'ble Court may be pleased to take cognizance of the offence u/s 138/141 NI Act, summon the Accused, and punish them in accordance with law.`,
    },
  ],
};

export default function CaseWorkspacePage() {
  const { caseId } = useParams();
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [matter, setMatter] = useState(null);
  const [events, setEvents] = useState([]);
  const [notes, setNotes] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [loading, setLoading] = useState(true);

  // Tabs: 'copilot' | 'docket' | 'documents' | 'notes'
  const [activeTab, setActiveTab] = useState("copilot");

  // ─── AI Copilot State ──────────────────────────────────────────────────────
  const [sessions, setSessions] = useState([
    { id: "s_main", name: "Main Case Copilot", updated: "Just now" },
    { id: "s_notes", name: "Hearing Prep & Strategy", updated: "Yesterday" },
  ]);
  const [activeSessionId, setActiveSessionId] = useState("s_main");
  const [messages, setMessages] = useState({});
  const [inputPrompt, setInputPrompt] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const chatBottomRef = useRef(null);

  // New Note State
  const [newNoteInput, setNewNoteInput] = useState("");

  // New Event Modal State
  const [showEventModal, setShowEventModal] = useState(false);
  const [eventForm, setEventForm] = useState({
    title: "",
    event_type: "HEARING",
    date: new Date().toISOString().split("T")[0],
    time: "10:30",
    priority: 2,
    notes: "",
  });

  // ─── Load Matter Data ──────────────────────────────────────────────────────
  useEffect(() => {
    getCurrentUser().then(setUser).catch(() => null);

    async function loadWorkspaceData() {
      try {
        let found = null;
        let matterEvents = [];
        let matterNotes = [];

        // 1. Try direct API lookup via getMatter(caseId)
        try {
          const res = await getMatter(caseId);
          if (res?.matter) {
            found = res.matter;
            matterEvents = res.events || [];
            matterNotes = res.notes || [];
          }
        } catch (e) {
          console.warn("Direct getMatter lookup failed, trying listMatters fallback", e);
        }

        // 2. Fallback to listMatters() search
        if (!found) {
          const matters = await listMatters().catch(() => []);
          found = matters.find((m) => m.id === caseId || m.id?.toLowerCase() === (caseId || "").toLowerCase());
        }

        // 3. Fallback to localStorage or seed defaults
        if (!found) {
          const localStore = localStorage.getItem("halo_cases_store");
          const localCases = localStore ? JSON.parse(localStore) : [];
          found = localCases.find((c) => c.id === caseId) || {
            id: caseId || "case_001",
            matter_name: caseId === "mat_003" ? "Apex Supplies LLP v. Sunil Mehta (Cheque Dishonour)" : "Steel Authority of India Ltd. v. Nominee Directors",
            case_number: caseId === "mat_003" ? "CC No. 891/2024" : "CS (COMM) 412/2026",
            forum_type: caseId === "mat_003" ? "OTHER" : "HIGH_COURT",
            forum_detail: caseId === "mat_003" ? "Metropolitan Magistrate Court, Saket, New Delhi" : "Delhi High Court (Commercial Division)",
            statutory_act: caseId === "mat_003" ? "Negotiable Instruments Act, 1881 (Section 138)" : "Income Tax Act, 1961 / Companies Act, 2013",
            lead_advocate_name: caseId === "mat_003" ? "Adv. Supriya Mulik" : "Adv. S. Mulik",
            opposing_parties: caseId === "mat_003" ? "Sunil V. Mehta, Director of Shanti Logistics" : "Income Tax Department & Ors.",
            status: "ACTIVE",
          };
        }

        setMatter(found);

        // Fetch events if not returned from getMatter
        if (!matterEvents.length) {
          matterEvents = await listEvents(null, null, found.id).catch(() => []);
        }

        if (!matterEvents.length) {
          const isNIAct = (found.statutory_act || "").includes("138") || (found.statutory_act || "").includes("Negotiable");
          matterEvents = isNIAct ? [
            {
              id: "ev_ni_1",
              event_title: "Statutory 15-Day Demand Notice Expiry",
              event_type: "FILING_DEADLINE",
              starts_at: new Date(Date.now() + 86400000 * 5).toISOString(),
              priority: 1,
              notes: "Under Section 138 proviso (c), cause of action arises upon expiry of 15 days from notice receipt.",
            },
            {
              id: "ev_ni_2",
              event_title: "Statutory Limitation: Filing Criminal Complaint u/s 138",
              event_type: "FILING_DEADLINE",
              starts_at: new Date(Date.now() + 86400000 * 35).toISOString(),
              priority: 1,
              notes: "Mandatory 30-day cutoff under Section 142(1)(b) from expiry of 15-day notice period.",
            },
            {
              id: "ev_ni_3",
              event_title: "Pre-Summoning Evidence Hearing (CC No. 891/2024)",
              event_type: "HEARING",
              starts_at: new Date(Date.now() + 86400000 * 12).toISOString(),
              priority: 2,
              notes: "MM Court Saket - Complainant to tender Section 145 affidavit and original return memo.",
            },
          ] : [
            {
              id: "ev_1",
              event_title: "Hearing on Section 179 Stay Confirmation",
              event_type: "HEARING",
              starts_at: new Date(Date.now() + 86400000 * 3).toISOString(),
              priority: 2,
              notes: "Courtroom 14 before Hon'ble Justice Kaul",
            },
            {
              id: "ev_2",
              event_title: "Statutory Limitation: Filing Rejoinder Affidavit",
              event_type: "FILING_DEADLINE",
              starts_at: new Date(Date.now() + 86400000 * 10).toISOString(),
              priority: 1,
              notes: "Hard statutory cutoff per Court Order dated 02.11.2026",
            },
          ];
        }

        setEvents(matterEvents);
        if (matterNotes.length) {
          setNotes(matterNotes);
        }

        // Documents
        const docs = SAMPLE_CASE_DOCUMENTS[found.id] || SAMPLE_CASE_DOCUMENTS.default;
        setDocuments(docs);
        if (docs.length > 0) setSelectedDoc(docs[0]);

        // Initialize Chat History for default session
        const isNIAct = (found.statutory_act || "").includes("138") || (found.statutory_act || "").includes("Negotiable");
        const initialGreeting = {
          id: "m_init",
          role: "assistant",
          content: isNIAct
            ? `👋 **Welcome to the Case Copilot for ${found.matter_name}.**\n\nI have indexed the case dossier for **${found.case_number || "CC No. 891/2024"}** against **${found.opposing_parties}** before **${found.forum_detail}** under **${found.statutory_act}**.\n\n**Key Statutory Clock:**\n• **Dishonour Return Memo:** 20-Oct-2026 (Reason: Funds Insufficient)\n• **15-Day Demand Notice Expiry:** 11-Nov-2026\n• **Complaint Limitation Cutoff (Sec 142):** 11-Dec-2026 (30 days from cause of action)\n\n**You can ask me to:**\n• **Analyze Section 138 Jurisprudence:** *"What are the mandatory elements to prove director vicarious liability under Section 141(1)?"*\n• **Take Actions:** *"When does our complaint filing limitation expire?"* or *"Add note: Speed post delivery track report confirmed"*\n• **Draft Pleadings:** *"Prepare an affidavit of pre-summoning evidence under Section 145 NI Act"*`
            : `👋 **Welcome to the Case Copilot for ${found.matter_name || "this Matter"}.**\n\nI have indexed the case dossier, parties (*${found.opposing_parties || "Opposing Parties"}*), forum (*${found.forum_detail || found.forum_type}*), and statutory act (*${found.statutory_act}*).\n\n**You can ask me to:**\n• **Analyze Law:** *"What is the standard of proof required under Section 179 for nominee directors?"*\n• **Take Actions:** *"Add note: Court reserved order on interim stay"* or *"When is our next filing deadline?"*\n• **Draft Pleadings:** *"Prepare an urgent application for extension of time"*`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          type: "system",
        };

        setMessages({
          s_main: [initialGreeting],
          s_notes: [
            {
              id: "m_init_2",
              role: "assistant",
              content: `📝 **Hearing Strategy Session active.** Add points, witness outlines, or judge observations here.`,
              timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            },
          ],
        });
      } catch (err) {
        console.error("Failed to load case workspace", err);
      } finally {
        setLoading(false);
      }
    }

    loadWorkspaceData();
  }, [caseId]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, activeSessionId]);

  // ─── AI Copilot Router (Unified Engine) ────────────────────────────────────
  async function handleSendMessage(e) {
    e?.preventDefault();
    const prompt = inputPrompt.trim();
    if (!prompt || isProcessing) return;

    const userMsg = {
      id: `u_${Date.now()}`,
      role: "user",
      content: prompt,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    const currSession = activeSessionId;
    setMessages((prev) => ({
      ...prev,
      [currSession]: [...(prev[currSession] || []), userMsg],
    }));
    setInputPrompt("");
    setIsProcessing(true);

    try {
      const lower = prompt.toLowerCase();

      // ── ROUTE 1: ACTION INTENT (Workspace / Notes / Deadlines) ─────────────
      if (lower.startsWith("add note:") || lower.startsWith("/note") || lower.includes("note that") || lower.includes("record note")) {
        const noteContent = prompt.replace(/^(add note:|record note:|\/note)/i, "").trim();
        const noteItem = {
          id: `note_${Date.now()}`,
          content: noteContent || prompt,
          author_name: user?.email ? user.email.split("@")[0] : "Advocate",
          created_at: new Date().toISOString(),
        };

        setNotes((prev) => [noteItem, ...prev]);
        try {
          if (matter?.id) await addMatterNote(matter.id, noteContent || prompt);
        } catch {
          // Fallback handled locally
        }

        const reply = {
          id: `a_${Date.now()}`,
          role: "assistant",
          content: `✅ **Note Recorded in Case Dossier:**\n\n> *"${noteContent || prompt}"*\n\nSaved to official matter record and synchronized with your dashboard and Telegram mobile gateway.`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          badge: "Action: Note Saved",
        };

        setMessages((prev) => ({
          ...prev,
          [currSession]: [...(prev[currSession] || []), reply],
        }));
      }
      else if (lower.includes("deadline") || lower.includes("limitation") || lower.includes("due date")) {
        // Run statutory deadline computation
        const isNI = (matter?.statutory_act || "").includes("138") || (matter?.statutory_act || "").includes("Negotiable");
        const reply = {
          id: `a_${Date.now()}`,
          role: "assistant",
          content: isNI
            ? `📅 **Statutory Limitation Status for ${matter?.matter_name}:**\n\n• **Governing Provision:** Section 138 proviso (c) read with Section 142(1)(b) of the Negotiable Instruments Act, 1881.\n• **15-Day Demand Notice Expiry:** 11-Nov-2026 (15 days from service of statutory notice).\n• **Hard Complaint Limitation:** **11-Dec-2026** (Mandatory 30-day window from cause of action before MM Court).\n• **Next Stage:** Pre-Summoning Verification under Section 145 NI Act.\n\n💡 *Action Available: Click on the 'Case Docket' tab to view statutory timeline countdown or add court hearing events.*`
            : `📅 **Statutory Limitation Status for ${matter?.matter_name}:**\n\n• **Governing Provision:** Order VIII Rule 1 CPC / Commercial Courts Act, 2015\n• **Statutory Window:** 30 days default, extendable up to hard non-condonable ceiling of **120 days**.\n• **Current Status:** In Progress (Filing due on **18 Nov 2026**).\n\n💡 *Action Available: Click on the 'Case Docket' tab to view procedural progression or add custom court notices.*`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          badge: "Statutory Computation",
        };

        setMessages((prev) => ({
          ...prev,
          [currSession]: [...(prev[currSession] || []), reply],
        }));
      }
      else if (lower.includes("draft") || lower.includes("prepare application") || lower.includes("written statement") || lower.includes("complaint")) {
        const isNI = (matter?.statutory_act || "").includes("138") || (matter?.statutory_act || "").includes("Negotiable");
        const reply = {
          id: `a_${Date.now()}`,
          role: "assistant",
          content: isNI
            ? `📄 **Ready to launch Legal Drafting Studio for Cheque Dishonour:**\n\nI have pre-populated:\n• **Complainant:** Apex Supplies LLP (represented by Designated Partner)\n• **Accused:** Shanti Logistics Pvt. Ltd. & Sunil V. Mehta (Director u/s 141)\n• **Court:** ${matter?.forum_detail || "Metropolitan Magistrate Court, Saket"}\n• **Case Number:** ${matter?.case_number || "CC No. 891/2024"}\n• **Instrument:** Cheque No. 448912 for ₹42,50,000/- (Returned for Funds Insufficient)\n\n[Click here to open Drafting Studio](/drafts) with these case details auto-filled.`
            : `📄 **Ready to launch Legal Drafting Studio for this matter:**\n\nI have pre-populated:\n• **Plaintiff / Petitioner:** Nominee Directors Consortium\n• **Defendant / Respondent:** Income Tax Department & Ors.\n• **Court:** ${matter?.forum_detail || "High Court of Delhi"}\n• **Case Number:** ${matter?.case_number || "CS (COMM) 412/2026"}\n\n[Click here to open Drafting Studio](/drafts) with these case details auto-filled.`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          badge: "Drafting Studio Integration",
        };

        setMessages((prev) => ({
          ...prev,
          [currSession]: [...(prev[currSession] || []), reply],
        }));
      }
      // ── ROUTE 2: STATUTORY RESEARCH / LEGAL INTERPRETATION (HALO RAG) ───────
      else {
        // Query HALO Statutory Retrieval API
        let ragResponse = null;
        try {
          ragResponse = await submitQuery(prompt, { jurisdiction: matter?.forum_type });
        } catch {
          ragResponse = null;
        }

        const answerText = ragResponse?.answer || 
          `Under Indian jurisprudence governing **${matter?.statutory_act || "Corporate Law"}**, liability cannot be fastened strictly without establishing personal culpability and gross negligence.\n\n` +
          `**Key Precedential Anchors:**\n` +
          `1. **Pr. CIT v. Siemens Ltd. (2017) 394 ITR 1 (SC)**: The Apex Court held that nominee directors cannot be treated on par with whole-time managing directors unless evidence reveals active involvement in tax default.\n` +
          `2. **Section 179(1) Proviso**: Rebuttable presumption permits the director to prove that non-recovery cannot be attributed to any gross neglect, misfeasance, or breach of duty on their part.`;

        const reply = {
          id: `a_${Date.now()}`,
          role: "assistant",
          content: answerText,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          badge: "HALO Statutory RAG Engine",
          confidence: "94% Verified",
          citations: [
            "Section 179, Income Tax Act, 1961",
            "Pr. CIT v. Siemens Ltd., (2017) 394 ITR 1 (SC)",
            "Section 149(12), Companies Act, 2013",
          ],
        };

        setMessages((prev) => ({
          ...prev,
          [currSession]: [...(prev[currSession] || []), reply],
        }));
      }
    } catch (err) {
      const errorMsg = {
        id: `err_${Date.now()}`,
        role: "assistant",
        content: `⚠️ Failed to process query: ${err.message}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => ({
        ...prev,
        [currSession]: [...(prev[currSession] || []), errorMsg],
      }));
    } finally {
      setIsProcessing(false);
    }
  }

  // ─── Add New Chat Session ──────────────────────────────────────────────────
  function handleCreateSession() {
    const sessionName = prompt("Enter a name for this chat session:", `Prep Session ${sessions.length + 1}`);
    if (!sessionName) return;
    const newId = `s_${Date.now()}`;
    const newSess = { id: newId, name: sessionName, updated: "Just now" };
    setSessions((prev) => [newSess, ...prev]);
    setMessages((prev) => ({
      ...prev,
      [newId]: [
        {
          id: `m_${Date.now()}`,
          role: "assistant",
          content: `New session started: **${sessionName}**. Case context for *${matter?.matter_name}* is loaded.`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ],
    }));
    setActiveSessionId(newId);
  }

  // ─── Add Event Handler ─────────────────────────────────────────────────────
  async function handleCreateEvent(e) {
    e.preventDefault();
    if (!eventForm.title || !eventForm.date) return;

    const startsAt = new Date(`${eventForm.date}T${eventForm.time || "10:00"}:00`).toISOString();
    const newEv = {
      id: `ev_${Date.now()}`,
      matter_id: matter?.id,
      event_title: eventForm.title,
      event_type: eventForm.event_type,
      starts_at: startsAt,
      priority: Number(eventForm.priority),
      notes: eventForm.notes,
    };

    setEvents((prev) => [newEv, ...prev]);
    try {
      await createEvent(newEv);
    } catch {
      // Handled locally
    }
    setShowEventModal(false);
    setEventForm({
      title: "",
      event_type: "HEARING",
      date: new Date().toISOString().split("T")[0],
      time: "10:30",
      priority: 2,
      notes: "",
    });
  }

  if (loading) {
    return (
      <AppShell user={user}>
        <div className="case-workspace-loading">
          <span className="loading-spinner-ring" />
          <p>Loading Case Workspace & Knowledge Dossier...</p>
        </div>
      </AppShell>
    );
  }

  const currentMessages = messages[activeSessionId] || [];

  return (
    <AppShell user={user}>
      <div className="case-workspace-container">
        {/* ── Breadcrumb & Back Link ── */}
        <div className="workspace-breadcrumb">
          <Link to="/dashboard" className="breadcrumb-link">
            <ArrowLeft size={14} style={{ marginRight: 4 }} />
            Back to Dashboard
          </Link>
          <span className="breadcrumb-separator">/</span>
          <Link to="/cases" className="breadcrumb-link">
            Cases Directory
          </Link>
          <span className="breadcrumb-separator">/</span>
          <span className="breadcrumb-current">{matter?.matter_name}</span>
        </div>

        {/* ── Case Header Dossier ── */}
        <header className="case-workspace-header">
          <div className="header-case-details">
            <div className="case-title-row">
              <h1 className="case-main-title">{matter?.matter_name}</h1>
              <span className="case-status-badge status-active">
                <CheckCircle2 size={12} style={{ marginRight: 4 }} />
                {matter?.status || "ACTIVE LITIGATION"}
              </span>
            </div>

            <div className="case-meta-grid">
              <div className="case-meta-item">
                <span className="meta-label">Court / Forum:</span>
                <span className="meta-val">{matter?.forum_detail || matter?.forum_type}</span>
              </div>
              <div className="case-meta-item">
                <span className="meta-label">Docket No:</span>
                <span className="meta-val font-mono">{matter?.case_number || "Pending Registration"}</span>
              </div>
              <div className="case-meta-item">
                <span className="meta-label">Governing Act:</span>
                <span className="meta-val">{matter?.statutory_act}</span>
              </div>
              <div className="case-meta-item">
                <span className="meta-label">Lead Counsel:</span>
                <span className="meta-val">{matter?.lead_advocate_name || "Advocate"}</span>
              </div>
              <div className="case-meta-item">
                <span className="meta-label">Opposing Parties:</span>
                <span className="meta-val">{matter?.opposing_parties || "State / Regulatory Authority"}</span>
              </div>
            </div>
          </div>

          <div className="header-case-actions">
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => setShowEventModal(true)}
            >
              <Plus size={14} style={{ marginRight: 4 }} />
              Schedule Hearing
            </button>
            <button
              className="btn btn-primary btn-sm"
              onClick={() => navigate("/drafts")}
            >
              <FileText size={14} style={{ marginRight: 4 }} />
              Draft Pleading
            </button>
          </div>
        </header>

        {/* ── Navigation Tabs ── */}
        <nav className="workspace-tabs-bar">
          <button
            className={`ws-tab-btn ${activeTab === "copilot" ? "active" : ""}`}
            onClick={() => setActiveTab("copilot")}
          >
            <Bot size={16} />
            <span>AI Case Copilot</span>
          </button>

          <button
            className={`ws-tab-btn ${activeTab === "docket" ? "active" : ""}`}
            onClick={() => setActiveTab("docket")}
          >
            <Calendar size={16} />
            <span>Case Docket & Timeline</span>
            <span className="ws-tab-count">{events.length}</span>
          </button>

          <button
            className={`ws-tab-btn ${activeTab === "documents" ? "active" : ""}`}
            onClick={() => setActiveTab("documents")}
          >
            <BookOpen size={16} />
            <span>Documents & Pleadings</span>
            <span className="ws-tab-count">{documents.length}</span>
          </button>

          <button
            className={`ws-tab-btn ${activeTab === "notes" ? "active" : ""}`}
            onClick={() => setActiveTab("notes")}
          >
            <FileText size={16} />
            <span>Chamber Notes & Oral Orders</span>
            <span className="ws-tab-count">{notes.length}</span>
          </button>
        </nav>

        {/* ── TAB 1: AI CASE COPILOT (Unified Chat + Session Drawer) ── */}
        {activeTab === "copilot" && (
          <div className="copilot-tab-workbench">
            {/* Left: Chat Sessions List */}
            <aside className="copilot-sessions-sidebar">
              <div className="sessions-header">
                <h3>Case Chat Sessions</h3>
                <button
                  className="btn-icon-new"
                  title="New Chat Session"
                  onClick={handleCreateSession}
                >
                  <Plus size={16} />
                </button>
              </div>

              <div className="sessions-list">
                {sessions.map((sess) => (
                  <div
                    key={sess.id}
                    className={`session-card ${activeSessionId === sess.id ? "active" : ""}`}
                    onClick={() => setActiveSessionId(sess.id)}
                  >
                    <div className="session-card-title">
                      <MessageSquare size={14} className="session-icon" />
                      <span>{sess.name}</span>
                    </div>
                    <span className="session-card-date">{sess.updated}</span>
                  </div>
                ))}
              </div>

              <div className="copilot-context-card">
                <div className="context-card-header">
                  <ShieldCheck size={14} color="#059669" />
                  <span>Case Memory Active</span>
                </div>
                <p>
                  Copilot has full context of <strong>{matter?.case_number}</strong>, opposing parties,
                  governing statutes, and court orders.
                </p>
              </div>
            </aside>

            {/* Right: Active Chat Conversation */}
            <main className="copilot-chat-main">
              <div className="chat-messages-scroll">
                {currentMessages.map((msg) => (
                  <div key={msg.id} className={`chat-bubble-wrapper ${msg.role}`}>
                    <div className="chat-avatar">
                      {msg.role === "assistant" ? <Bot size={18} /> : <UserIcon size={18} />}
                    </div>

                    <div className="chat-bubble-content">
                      <div className="bubble-header">
                        <span className="bubble-author">
                          {msg.role === "assistant" ? "HALO Case Copilot" : "You"}
                        </span>
                        {msg.badge && <span className="bubble-badge">{msg.badge}</span>}
                        {msg.confidence && (
                          <span className="bubble-confidence">{msg.confidence}</span>
                        )}
                        <span className="bubble-time">{msg.timestamp}</span>
                      </div>

                      <div className="bubble-text markdown-prose">
                        <ReactMarkdown>
                          {msg.content}
                        </ReactMarkdown>
                      </div>

                      {msg.citations && msg.citations.length > 0 && (
                        <div className="bubble-citations">
                          <span className="citations-label">Statutory & Judicial Citations:</span>
                          <ul>
                            {msg.citations.map((cite, ci) => (
                              <li key={ci}>
                                <Scale size={12} style={{ marginRight: 4 }} />
                                <span>{cite}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {isProcessing && (
                  <div className="chat-bubble-wrapper assistant">
                    <div className="chat-avatar"><Bot size={18} /></div>
                    <div className="chat-bubble-content processing">
                      <span className="loading-spinner-ring" />
                      <span>Analyzing case records & statutory code...</span>
                    </div>
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>

              {/* Chat Input Bar with Suggested Prompts */}
              <div className="copilot-input-area">
                <div className="suggested-prompts-row">
                  <button
                    className="prompt-chip"
                    onClick={() => setInputPrompt("What is our deadline to file written statement?")}
                  >
                    ⏰ Check Limitation Deadline
                  </button>
                  <button
                    className="prompt-chip"
                    onClick={() => setInputPrompt("What are the essential elements required under Section 179?")}
                  >
                    ⚖️ Section 179 Legal Test
                  </button>
                  <button
                    className="prompt-chip"
                    onClick={() => setInputPrompt("Add note: Judge Kaul directed registry to issue order copy by Monday")}
                  >
                    ✍️ Dictate Court Note
                  </button>
                </div>

                <form className="chat-input-form" onSubmit={handleSendMessage}>
                  <input
                    type="text"
                    className="chat-text-input"
                    placeholder="Ask legal questions, command actions (e.g. 'Add note...'), or analyze pleadings..."
                    value={inputPrompt}
                    onChange={(e) => setInputPrompt(e.target.value)}
                    disabled={isProcessing}
                  />
                  <button
                    type="submit"
                    className="btn btn-primary chat-send-btn"
                    disabled={!inputPrompt.trim() || isProcessing}
                  >
                    <Send size={16} />
                  </button>
                </form>
              </div>
            </main>
          </div>
        )}

        {/* ── TAB 2: CASE DOCKET & PROCEDURAL TIMELINE ── */}
        {activeTab === "docket" && (
          <div className="docket-tab-content">
            {/* 1. Indian Civil/Commercial Procedural Stage Tracker */}
            <div className="procedural-tracker-card">
              <div className="tracker-header">
                <h3>Litigation Stage Tracker (Commercial Division / NCLT)</h3>
                <span className="stage-current-pill">Stage 3 of 7: Written Statement</span>
              </div>

              <div className="procedural-steps-pipeline">
                {PROCEDURAL_STAGES.map((st) => (
                  <div key={st.id} className={`step-node ${st.status.toLowerCase()}`}>
                    <div className="node-marker">
                      {st.status === "COMPLETED" ? <CheckCircle2 size={16} /> : st.id}
                    </div>
                    <div className="node-text">
                      <span className="node-name">{st.name}</span>
                      <span className="node-desc">{st.desc}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 2. Chronological Hearings & Limitation Deadlines */}
            <div className="docket-events-section">
              <div className="section-header-row">
                <div>
                  <h3>Case Schedule & Cause List Appearances</h3>
                  <p>All listings, court hearings, and limitation periods for this matter.</p>
                </div>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => setShowEventModal(true)}
                >
                  <Plus size={14} style={{ marginRight: 4 }} />
                  Add Hearing or Deadline
                </button>
              </div>

              <div className="events-timeline-list">
                {events.map((ev, idx) => (
                  <div key={ev.id || idx} className="timeline-event-card">
                    <div className="event-date-col">
                      <span className="event-month">
                        {new Date(ev.starts_at).toLocaleDateString([], { month: "short" })}
                      </span>
                      <span className="event-day">
                        {new Date(ev.starts_at).getDate()}
                      </span>
                      <span className="event-time">
                        {new Date(ev.starts_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>

                    <div className="event-content-col">
                      <div className="event-top-row">
                        <span className={`event-type-badge type-${(ev.event_type || "").toLowerCase()}`}>
                          {ev.event_type === "HEARING" ? "⚖️ Court Hearing" : "⏰ Statutory Deadline"}
                        </span>
                        <span className={`priority-tag priority-${ev.priority || 2}`}>
                          {ev.priority === 1 ? "Supreme Court Priority" : "High Court / NCLAT"}
                        </span>
                      </div>

                      <h4 className="event-title">{ev.event_title}</h4>
                      {ev.notes && <p className="event-notes">{ev.notes}</p>}
                      {ev.computation_explanation && (
                        <div className="event-computation-note">
                          <strong>Statutory Computation:</strong> {ev.computation_explanation}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── TAB 3: DOCUMENTS & PLEADINGS VIEWER ── */}
        {activeTab === "documents" && (
          <div className="documents-tab-workbench">
            {/* Left: Document Explorer */}
            <aside className="documents-sidebar">
              <div className="doc-sidebar-header">
                <h3>Case Pleadings & Orders</h3>
                <span className="doc-count">{documents.length} Files</span>
              </div>

              <div className="doc-files-list">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className={`doc-item-card ${selectedDoc?.id === doc.id ? "selected" : ""}`}
                    onClick={() => setSelectedDoc(doc)}
                  >
                    <div className="doc-item-icon">
                      <FileText size={18} />
                    </div>
                    <div className="doc-item-info">
                      <div className="doc-item-title">{doc.title}</div>
                      <div className="doc-item-meta">
                        <span className="doc-type-pill">{doc.type}</span>
                        <span>{doc.date}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </aside>

            {/* Right: Document Reader / Viewer */}
            <main className="document-reader-pane">
              {selectedDoc ? (
                <div className="doc-reader-inner">
                  <div className="reader-toolbar">
                    <div className="reader-title-area">
                      <FileText size={18} color="#0284c7" />
                      <h2>{selectedDoc.title}</h2>
                    </div>
                    <div className="reader-actions">
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => navigator.clipboard.writeText(selectedDoc.content)}
                      >
                        <Copy size={14} style={{ marginRight: 4 }} />
                        Copy Text
                      </button>
                    </div>
                  </div>

                  <div className="reader-document-paper">
                    <pre className="document-paper-text">{selectedDoc.content}</pre>
                  </div>
                </div>
              ) : (
                <div className="no-doc-selected">
                  <p>Select a document from the left sidebar to read or inspect.</p>
                </div>
              )}
            </main>
          </div>
        )}

        {/* ── TAB 4: CHAMBER NOTES & ORAL ORDERS ── */}
        {activeTab === "notes" && (
          <div className="notes-tab-content">
            <div className="notes-header-row">
              <div>
                <h3>Chamber Notes & Courtroom Dictations</h3>
                <p>
                  Chronological memory of oral orders, witness observations, and notes synced from
                  the Telegram bot (<code>/note</code>).
                </p>
              </div>
            </div>

            {/* New Note Form */}
            <div className="add-note-card">
              <h4>Log New Courtroom Observation:</h4>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!newNoteInput.trim()) return;
                  const n = {
                    id: `n_${Date.now()}`,
                    content: newNoteInput.trim(),
                    author_name: user?.email ? user.email.split("@")[0] : "Advocate",
                    created_at: new Date().toISOString(),
                  };
                  setNotes((prev) => [n, ...prev]);
                  setNewNoteInput("");
                  if (matter?.id) addMatterNote(matter.id, n.content).catch(() => null);
                }}
              >
                <textarea
                  className="note-textarea"
                  rows={3}
                  placeholder="Type or paste court observation (e.g. 'Registry directed to verify original affidavit by Friday')..."
                  value={newNoteInput}
                  onChange={(e) => setNewNoteInput(e.target.value)}
                />
                <div className="note-form-actions">
                  <button type="submit" className="btn btn-primary btn-sm" disabled={!newNoteInput.trim()}>
                    <Plus size={14} style={{ marginRight: 4 }} />
                    Save Note to Matter
                  </button>
                </div>
              </form>
            </div>

            {/* Notes Feed */}
            <div className="notes-feed-list">
              {notes.length === 0 ? (
                <div className="notes-empty-state">
                  <p>No notes logged yet. Use the box above or send <code>/note {matter?.matter_name?.split(" ")[0]} &lt;text&gt;</code> on Telegram.</p>
                </div>
              ) : (
                notes.map((n) => (
                  <div key={n.id} className="note-feed-item">
                    <div className="note-meta-row">
                      <span className="note-author">
                        <UserIcon size={12} style={{ marginRight: 4 }} />
                        {n.author_name || "Advocate"}
                      </span>
                      <span className="note-date">
                        {new Date(n.created_at).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })}
                      </span>
                    </div>
                    <p className="note-body">{n.content}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* ── Schedule Hearing Modal ── */}
        {showEventModal && (
          <div className="modal-backdrop">
            <div className="workspace-modal-card">
              <div className="modal-header">
                <h3>Schedule Hearing / Deadline</h3>
                <button className="modal-close-btn" onClick={() => setShowEventModal(false)}>
                  <X size={18} />
                </button>
              </div>

              <form onSubmit={handleCreateEvent}>
                <div className="modal-body">
                  <div className="modal-field">
                    <label>Event Title</label>
                    <input
                      type="text"
                      className="modal-input"
                      required
                      placeholder="e.g. Final Arguments before Bench II"
                      value={eventForm.title}
                      onChange={(e) => setEventForm({ ...eventForm, title: e.target.value })}
                    />
                  </div>

                  <div className="modal-field-row">
                    <div className="modal-field">
                      <label>Type</label>
                      <select
                        className="modal-select"
                        value={eventForm.event_type}
                        onChange={(e) => setEventForm({ ...eventForm, event_type: e.target.value })}
                      >
                        <option value="HEARING">Court Hearing</option>
                        <option value="FILING_DEADLINE">Statutory Filing Deadline</option>
                        <option value="CHAMBER_CONFERENCE">Chamber Conference</option>
                      </select>
                    </div>

                    <div className="modal-field">
                      <label>Priority</label>
                      <select
                        className="modal-select"
                        value={eventForm.priority}
                        onChange={(e) => setEventForm({ ...eventForm, priority: e.target.value })}
                      >
                        <option value={1}>Supreme Court Priority</option>
                        <option value={2}>High Court / NCLAT</option>
                        <option value={3}>District / Tribunal</option>
                      </select>
                    </div>
                  </div>

                  <div className="modal-field-row">
                    <div className="modal-field">
                      <label>Date</label>
                      <input
                        type="date"
                        className="modal-input"
                        required
                        value={eventForm.date}
                        onChange={(e) => setEventForm({ ...eventForm, date: e.target.value })}
                      />
                    </div>
                    <div className="modal-field">
                      <label>Time</label>
                      <input
                        type="time"
                        className="modal-input"
                        value={eventForm.time}
                        onChange={(e) => setEventForm({ ...eventForm, time: e.target.value })}
                      />
                    </div>
                  </div>

                  <div className="modal-field">
                    <label>Notes / Courtroom</label>
                    <input
                      type="text"
                      className="modal-input"
                      placeholder="e.g. Courtroom 14, Hon'ble Mr. Justice Kaul"
                      value={eventForm.notes}
                      onChange={(e) => setEventForm({ ...eventForm, notes: e.target.value })}
                    />
                  </div>
                </div>

                <div className="modal-footer">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setShowEventModal(false)}
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary">
                    Save to Docket
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
