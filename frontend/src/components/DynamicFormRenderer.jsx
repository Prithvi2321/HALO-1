/**
 * src/components/DynamicFormRenderer.jsx
 * ──────────────────────────────────────
 * Schema-driven dynamic form renderer for HALO Legal Drafting Engine.
 * Conforms to PRD §6.4 & Appendix C contract:
 * - Dynamic generation from template schema JSON
 * - Zero per-template React code
 * - Field-level validation + Indian Law formats (CIN, DIN, PAN, GSTIN, dates)
 * - Conditional warnings and visibility
 */

import React from "react";
import { AlertTriangle, AlertCircle, Info } from "lucide-react";
import "./DynamicFormRenderer.css";

// ─── Inline Indian Law Client Validators ─────────────────────────────────────

const VALIDATORS = {
  cin: {
    pattern: /^[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$/i,
    hint: "21-char CIN (e.g. U72200MH2013PTC248912)",
    validate: (val) =>
      /^[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$/i.test(val?.trim() || "")
        ? null
        : "Invalid CIN format (21 chars: Listing, State, Year, Number).",
  },
  din: {
    pattern: /^\d{8}$/,
    hint: "8 numeric digits (e.g. 08945612)",
    validate: (val) =>
      /^\d{8}$/.test(val?.trim() || "")
        ? null
        : "Invalid DIN format: exactly 8 digits required.",
  },
  pan: {
    pattern: /^[A-Z]{5}\d{4}[A-Z]$/i,
    hint: "10-character PAN (e.g. ABCDE1234F)",
    validate: (val) =>
      /^[A-Z]{5}\d{4}[A-Z]$/i.test(val?.trim() || "")
        ? null
        : "Invalid PAN format: 5 letters, 4 digits, 1 letter.",
  },
  gstin: {
    pattern: /^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$/i,
    hint: "15-character GSTIN (e.g. 27ABCDE1234F1Z5)",
    validate: (val) =>
      /^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$/i.test(val?.trim() || "")
        ? null
        : "Invalid GSTIN format: 15 alphanumeric characters.",
  },
  date_not_future: {
    hint: "Must be today or a past date",
    validate: (val) => {
      if (!val) return null;
      const d = new Date(val);
      const today = new Date();
      today.setHours(23, 59, 59, 999);
      return d > today ? "Date cannot be in the future." : null;
    },
  },
};

const HINDI_FIELD_LABELS = {
  // Corporate & Board Resolutions
  company_cin: "कंपनी सीआईएन (Company CIN)",
  company_name: "कंपनी का नाम (Company Name)",
  registered_office: "कंपनी का पंजीकृत कार्यालय (Registered Office Address)",
  meeting_date: "बोर्ड बैठक की तिथि (Board Meeting Date)",
  meeting_venue: "बैठक का स्थान (Meeting Venue)",
  director_name: "नियुक्त निदेशक का पूरा नाम (Appointee Full Name)",
  director_din: "निदेशक पहचान संख्या (Appointee DIN)",
  effective_date: "प्रभावी तिथि (Effective Date)",
  articles_authorise: "अंतरनियम (AOA) अतिरिक्त निदेशक नियुक्ति अधिकृत करता है (Articles Authorise Appointment)",
  co_signatory: "अधिकृत हस्ताक्षरकर्ता / अध्यक्ष (Authorized Signatory / Chairman)",
  signatory: "अधिकृत हस्ताक्षरकर्ता (Authorized Signatory)",
  resolution_subject: "संकल्प का विषय (Resolution Subject)",
  resolution_body: "पारित संकल्प का पाठ (Text of Resolutions Passed)",
  resolution_date: "संकल्प पारित होने की तिथि (Date of Resolution Passed)",
  roc_jurisdiction: "कंपनी रजिस्ट्रार (ROC) क्षेत्राधिकार (ROC Jurisdiction)",
  professional_name: "प्रमाणित पेशेवर का नाम (Certifying Professional Name)",

  // Petition S.241/242 NCLT
  nclt_bench: "राष्ट्रीय कंपनी विधि अधिकरण पीठ (NCLT Bench)",
  case_year: "दायर करने का वर्ष (Filing Year)",
  petitioner_name: "याचिकाकर्ता का नाम (Petitioner Name)",
  petitioner_holding_pct: "याचिकाकर्ता शेयरधारिता % (Petitioner Shareholding %)",
  respondent_company: "प्रतिवादी कंपनी (Respondent Company)",
  oppressive_acts: "उत्पीड़न एवं कुप्रबंधन का विवरण (Oppressive & Prejudicial Acts)",
  prayer_sought: "प्रार्थित अनुतोष / याचना (Substantive Reliefs / Prayers Sought)",

  // Affidavits
  court: "न्यायालय / अधिकरण (Court / Forum)",
  case_no: "मुकदमा / वाद संख्या (Suit / Case Number)",
  cause_title: "वाद शीर्षक / पक्षकार (Cause Title)",
  deponent_name: "शपथकर्ता का नाम (Deponent Full Name)",
  deponent_age: "शपथकर्ता की आयु (Deponent Age)",
  deponent_parent: "पिता / माता का नाम (Father's / Mother's Name)",
  deponent_address: "शपथकर्ता का स्थाई पता (Deponent Address)",
  deponent_role: "शपथकर्ता की हैसियत / पद (Deponent Capacity)",
  affirmation_place: "शपथ का स्थान (Place of Affirmation)",
  facts_statement: "शपथपूर्वक सत्यापित तथ्य (Sworn Statements of Fact)",
  assessment_year: "कर निर्धारण वर्ष (Assessment Year)",
  deponent_din: "निदेशक पहचान संख्या (Director DIN)",
  deponent_pan: "निदेशक पैन (Director PAN)",
  due_diligence_facts: "सम्यक तत्परता तथ्य (Due Diligence Facts)",

  // Rent Agreement
  landlord_name: "मकान मालिक का पूरा नाम (Landlord Full Name)",
  landlord_pan: "मकान मालिक का पैन / आधार (Landlord PAN)",
  landlord_address: "मकान मालिक का स्थाई पता (Landlord Permanent Address)",
  tenant_name: "किरायेदार का पूरा नाम (Tenant Full Name)",
  tenant_pan: "किरायेदार का पैन / आधार (Tenant PAN / Aadhaar)",
  tenant_address: "किरायेदार का स्थाई पता (Tenant Permanent Address)",
  premises_address: "किराए पर दी जाने वाली संपत्ति का पता (Premises Address)",
  monthly_rent: "मासिक किराया राशि (Monthly Rent ₹)",
  security_deposit: "ब्याज-मुक्त सुरक्षा धरोहर राशि (Security Deposit ₹)",
  commencement_date: "लीज प्रारंभ तिथि (Commencement Date)",
  tenure_months: "अनुबंध अवधि (Tenure Months)",
  lock_in_months: "लॉक-इन अवधि (Lock-In Period Months)",
  notice_period_days: "समाप्ति नोटिस अवधि (Notice Period Days)",
  maintenance_charges: "सोसायटी / मेंटेनेंस शुल्क (Maintenance Charges ₹)",
  target_language: "दस्तावेज़ की भाषा (Document Language)",

  // Cheque Bounce 138 Notice
  payee_name: "शिकायतकर्ता / प्राप्तकर्ता का नाम (Payee Name)",
  drawer_name: "आरोपी / चेक जारीकर्ता का नाम (Drawer Name)",
  drawer_address: "आरोपी का पूरा पता (Drawer Address)",
  cheque_no: "चेक संख्या (Cheque Number)",
  cheque_date: "चेक की तिथि (Cheque Date)",
  cheque_amount: "चेक राशि (Cheque Amount ₹)",
  bank_name: "बैंक एवं शाखा का नाम (Drawee Bank & Branch)",
  dishonour_date: "बैंक रिटर्न मेमो की तिथि (Return Memo Date)",
  dishonour_reason: "चेक अनादर का कारण (Reason for Dishonour)",
  advocate_name: "अधिवक्ता का नाम (Advocate Name)",

  // Commercial NDA
  disclosing_party: "प्रकटीकरण पक्ष / कंपनी (Disclosing Party)",
  disclosing_address: "प्रकटीकरण पक्ष का पता (Disclosing Party Address)",
  receiving_party: "प्राप्तकर्ता पक्ष / प्रतिपक्ष (Receiving Party)",
  receiving_address: "प्राप्तकर्ता पक्ष का पता (Receiving Party Address)",
  purpose: "गोपनीय प्रकटीकरण का उद्देश्य (Purpose of Disclosure)",
  duration_years: "गोपनीयता अवधि (Duration in Years)",
  governing_city: "न्यायालय अधिकार क्षेत्र (Governing Court Jurisdiction)",

  // Consultant Agreement
  client_name: "क्लाइंट / कंपनी का नाम (Client / Company Name)",
  consultant_name: "सलाहकार / कंसल्टेंट का नाम (Consultant Name)",
  consultant_pan: "कंसल्टेंट पैन / जीएसटी (Consultant PAN/GSTIN)",
  scope_of_work: "सेवाओं एवं कार्यों का विस्तृत विवरण (Scope of Work)",
  fee_amount: "व्यावसायिक परामर्श शुल्क (Professional Fee ₹)",
  payment_milestones: "भुगतान शर्तें एवं माइलस्टोन (Payment Milestones)",
};

export default function DynamicFormRenderer({
  schema,
  values = {},
  onChange,
  errors = {},
  targetLanguage = "en",
}) {
  if (!schema || !Array.isArray(schema.fields)) {
    return (
      <div className="conditional-alert-box">
        <Info size={16} />
        <span>No form schema available for this template.</span>
      </div>
    );
  }

  const fields = schema.fields;
  const conditionals = schema.conditional || [];

  // Evaluate conditional warnings based on current values
  const activeWarnings = [];
  conditionals.forEach((cond) => {
    if (cond.if) {
      let matched = true;
      Object.entries(cond.if).forEach(([k, expected]) => {
        if (values[k] !== expected) matched = false;
      });
      if (matched && cond.then?.warn) {
        activeWarnings.push(cond.then.warn);
      }
    }
  });

  return (
    <div className="dynamic-form-container">
      {/* Conditional Statutory Warnings */}
      {activeWarnings.map((warnMsg, idx) => (
        <div key={idx} className="conditional-alert-box">
          <AlertTriangle size={18} style={{ flexShrink: 0 }} />
          <div>
            <strong>Statutory Compliance Warning:</strong> {warnMsg}
          </div>
        </div>
      ))}

      <div className="dynamic-form-grid">
        {fields.map((f) => {
          const val = values[f.id] ?? (f.default ?? "");
          const errorMsg = errors[f.id];
          const isFullWidth = f.type === "text" || f.id.includes("address") || f.id.includes("prayer") || f.id.includes("facts") || f.id.includes("acts");
          const validatorDef = f.validator ? VALIDATORS[f.validator] : null;

          const isHindi = targetLanguage === "hi" || values.target_language === "hi";
          const isBilingual = targetLanguage === "bilingual" || values.target_language === "bilingual";

          const effectiveLabel = (isHindi && HINDI_FIELD_LABELS[f.id])
            ? HINDI_FIELD_LABELS[f.id]
            : (isBilingual && HINDI_FIELD_LABELS[f.id])
            ? `${f.label} / ${HINDI_FIELD_LABELS[f.id].split(" (")[0]}`
            : f.label;

          const effectivePlaceholder = isHindi && HINDI_FIELD_LABELS[f.id]
            ? `कृपया ${HINDI_FIELD_LABELS[f.id].split(" (")[0]} दर्ज करें...`
            : f.placeholder || `Enter ${f.label.toLowerCase()}...`;

          return (
            <div
              key={f.id}
              className={`form-field-group ${isFullWidth ? "full-width" : ""}`}
            >
              <label htmlFor={f.id} className="form-field-label">
                <span>
                  {effectiveLabel}
                  {f.required && <span className="required-star">*</span>}
                </span>
                {f.validator && (
                  <span className="form-field-tag">{f.validator.toUpperCase()}</span>
                )}
              </label>

              {/* Textarea */}
              {f.type === "text" ? (
                <textarea
                  id={f.id}
                  className={`form-textarea ${errorMsg ? "has-error" : ""}`}
                  placeholder={effectivePlaceholder}
                  value={val}
                  rows={4}
                  onChange={(e) => onChange(f.id, e.target.value)}
                />
              ) : f.type === "select" ? (
                /* Select Dropdown */
                <select
                  id={f.id}
                  className={`form-input-select ${errorMsg ? "has-error" : ""}`}
                  value={val}
                  onChange={(e) => onChange(f.id, e.target.value)}
                >
                  <option value="">
                    {isHindi
                      ? `-- चयन करें: ${effectiveLabel.split(" (")[0]} --`
                      : `-- Select ${f.label} --`}
                  </option>
                  {(f.options || []).map((opt, optIdx) => {
                    const optVal = typeof opt === "object" && opt !== null ? opt.value : opt;
                    const optLabel = typeof opt === "object" && opt !== null ? opt.label : opt;
                    return (
                      <option key={optVal || optIdx} value={optVal}>
                        {optLabel}
                      </option>
                    );
                  })}
                </select>
              ) : f.type === "boolean" ? (
                /* Boolean Checkbox Toggle */
                <label className="boolean-toggle-row">
                  <input
                    type="checkbox"
                    id={f.id}
                    checked={Boolean(val)}
                    onChange={(e) => onChange(f.id, e.target.checked)}
                  />
                  <span style={{ fontSize: "0.875rem", color: "var(--halo-text)" }}>
                    {effectiveLabel}
                  </span>
                </label>
              ) : (
                /* Standard text, number, date inputs */
                <input
                  id={f.id}
                  type={f.type === "number" ? "number" : f.type === "date" ? "date" : "text"}
                  className={`form-input-text ${errorMsg ? "has-error" : ""}`}
                  placeholder={effectivePlaceholder}
                  value={val}
                  step={f.type === "number" ? "any" : undefined}
                  onChange={(e) => onChange(f.id, e.target.value)}
                />
              )}

              {/* Inline Validation Error */}
              {errorMsg && (
                <div className="form-field-error">
                  <AlertCircle size={14} />
                  <span>{errorMsg}</span>
                </div>
              )}

              {/* Helpful Format Hint */}
              {!errorMsg && validatorDef?.hint && (
                <span className="form-field-hint">{validatorDef.hint}</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

