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

export default function DynamicFormRenderer({
  schema,
  values = {},
  onChange,
  errors = {},
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

          return (
            <div
              key={f.id}
              className={`form-field-group ${isFullWidth ? "full-width" : ""}`}
            >
              <label htmlFor={f.id} className="form-field-label">
                <span>
                  {f.label}
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
                  placeholder={f.placeholder || `Enter ${f.label.toLowerCase()}...`}
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
                  <option value="">-- Select {f.label} --</option>
                  {(f.options || []).map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
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
                    {f.label}
                  </span>
                </label>
              ) : (
                /* Standard text, number, date inputs */
                <input
                  id={f.id}
                  type={f.type === "number" ? "number" : f.type === "date" ? "date" : "text"}
                  className={`form-input-text ${errorMsg ? "has-error" : ""}`}
                  placeholder={f.placeholder || `Enter ${f.label.toLowerCase()}`}
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

