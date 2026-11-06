"""
Template Registry & Definitions (PRD §6.3 & §6.5)
=================================================
Initial Template Catalogue:
1. BOARD_RES_DIR_APPT_V1: Board Resolution – Additional Director (S.161(1) CA 2013)
2. PETITION_OPPR_MISMGMT_V1: Company Petition – Oppression & Mismanagement (S.241/242 CA 2013)
3. AFFIDAVIT_EVIDENCE_V1: Affidavit of Evidence (Order XIX R.3 CPC)
4. AFFIDAVIT_DIR_DD_V1: Director Due-Diligence Affidavit (S.179 IT Act)
5. NOTICE_DEMAND_138_V1: Statutory Demand Notice (S.138 NI Act)
6. BOARD_RES_GENERIC_V1: Generic Board Resolution
7. MGT14_COVER_V1: MGT-14 filing cover note (S.117 CA 2013)
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class TemplateManifest(BaseModel):
    template_id: str
    title: str
    version: str = "1.0.0"
    statutory_anchor: str
    category: str  # CORPORATE_RESOLUTION | PETITION | AFFIDAVIT | NOTICE | COMPLIANCE
    description: str
    controlling_precedent: Optional[str] = None
    output_formats: List[str] = ["docx", "pdf"]
    verification: Dict[str, Any] = {"enabled": False, "mode": "clause"}
    schema_definition: Dict[str, Any]
    body_template: str


CANONICAL_TEMPLATES: Dict[str, TemplateManifest] = {
    # ─── 1. Board Resolution — Additional Director (S.161(1) CA 2013) ─────────
    "BOARD_RES_DIR_APPT_V1": TemplateManifest(
        template_id="BOARD_RES_DIR_APPT_V1",
        title="Board Resolution — Appointment of Additional Director",
        version="1.0.0",
        statutory_anchor="Section 161(1), Companies Act, 2013",
        category="CORPORATE_RESOLUTION",
        description="Certified true copy of Board Resolution appointing an Additional Director pursuant to Section 161(1) of the Companies Act, 2013.",
        controlling_precedent="Needle Industries (India) Ltd. v. Needle Industries Newey (India) Holding Ltd. (1981) 3 SCC 333",
        schema_definition={
            "template_id": "BOARD_RES_DIR_APPT_V1",
            "statutory_anchor": "Section 161(1), Companies Act, 2013",
            "fields": [
                {"id": "company_cin", "label": "Company CIN", "type": "string", "required": True, "validator": "cin", "placeholder": "U72200MH2013PTC248912"},
                {"id": "company_name", "label": "Company Name", "type": "string", "required": True, "placeholder": "Acme Technologies Private Limited"},
                {"id": "registered_office", "label": "Registered Office Address", "type": "text", "required": True, "placeholder": "Unit 401, Nariman Point, Mumbai - 400021"},
                {"id": "meeting_date", "label": "Board Meeting Date", "type": "date", "required": True, "validator": "date_not_future"},
                {"id": "meeting_venue", "label": "Meeting Venue", "type": "string", "required": True, "placeholder": "Registered Office / Video Conference"},
                {"id": "director_name", "label": "Appointee Full Name", "type": "string", "required": True, "placeholder": "Priya Ramesh Sharma"},
                {"id": "director_din", "label": "Appointee DIN", "type": "string", "required": True, "validator": "din", "placeholder": "08945612"},
                {"id": "effective_date", "label": "Effective Appointment Date", "type": "date", "required": True},
                {"id": "articles_authorise", "label": "Articles of Association authorise appointment of Additional Directors", "type": "boolean", "required": True, "default": True},
                {"id": "co_signatory", "label": "Authorized Signatory / Chairman", "type": "string", "required": True, "placeholder": "Rajesh Kumar (Managing Director, DIN: 01452390)"},
            ],
            "conditional": [
                {
                    "if": {"articles_authorise": False},
                    "then": {"warn": "Section 161(1) of Companies Act, 2013 explicitly mandates that the Articles of Association must confer power on the Board. If not authorised, Articles must first be amended."}
                }
            ]
        },
        body_template="""CERTIFIED TRUE COPY OF THE RESOLUTION PASSED AT THE MEETING OF THE BOARD OF DIRECTORS OF {{ company_name | upper }} HELD ON {{ meeting_date_formatted }} AT {{ meeting_venue }}.

CIN: {{ company_cin }}
Registered Office: {{ registered_office }}

------------------------------------------------------------------------------------------------------------------------
APPOINTMENT OF MS./MR. {{ director_name | upper }} (DIN: {{ director_din }}) AS AN ADDITIONAL DIRECTOR
------------------------------------------------------------------------------------------------------------------------

"RESOLVED THAT pursuant to the provisions of Section 161(1) and other applicable provisions, if any, of the Companies Act, 2013 (including any statutory modification(s) or re-enactment thereof for the time being in force), and the relevant Articles of the Articles of Association of the Company, Ms./Mr. {{ director_name }} (holding Director Identification Number {{ director_din }}), who has consented to act as Director in Form DIR-2 and declared that she/he is not disqualified from being appointed as a director under Section 164 of the Act, be and is hereby appointed as an Additional Director on the Board of Directors of the Company with effect from {{ effective_date_formatted }}.

RESOLVED FURTHER THAT Ms./Mr. {{ director_name }} shall hold office up to the date of the next Annual General Meeting of the Company or the last date on which the Annual General Meeting should have been held, whichever is earlier.

RESOLVED FURTHER THAT {{ co_signatory }}, be and is hereby authorized on behalf of the Company to do all such acts, deeds, and things as may be necessary or expedient to give effect to this resolution, including filing Form DIR-12 with the Registrar of Companies within 30 days of this appointment and making requisite entries in the statutory registers of the Company."

For and on behalf of
{{ company_name | upper }}


________________________________________
{{ co_signatory }}
Date: {{ meeting_date_formatted }}
Place: {{ meeting_venue }}
"""
    ),

    # ─── 2. Petition — Oppression & Mismanagement (S.241/242 CA 2013) ────────
    "PETITION_OPPR_MISMGMT_V1": TemplateManifest(
        template_id="PETITION_OPPR_MISMGMT_V1",
        title="Company Petition — Oppression & Mismanagement (Sec 241/242)",
        version="1.0.0",
        statutory_anchor="Section 241 and 242, Companies Act, 2013",
        category="PETITION",
        description="Formal company petition filed before the National Company Law Tribunal under Sections 241 and 242 of the Companies Act, 2013 alleging oppressive and prejudicial conduct.",
        controlling_precedent="Tata Consultancy Services Ltd. v. Cyrus Investments Pvt. Ltd. (2021) 9 SCC 449",
        schema_definition={
            "template_id": "PETITION_OPPR_MISMGMT_V1",
            "statutory_anchor": "Section 241 and 242, Companies Act, 2013",
            "fields": [
                {"id": "nclt_bench", "label": "NCLT Bench", "type": "select", "required": True, "options": ["NCLT Mumbai Bench", "NCLT New Delhi (Principal Bench)", "NCLT Bengaluru Bench", "NCLT Kolkata Bench", "NCLT Chennai Bench", "NCLT Ahmedabad Bench", "NCLT Chandigarh Bench"]},
                {"id": "case_year", "label": "Filing Year", "type": "string", "required": True, "default": "2026"},
                {"id": "petitioner_name", "label": "Petitioner Name", "type": "string", "required": True, "placeholder": "Vikramaditya Infrastructure Pvt. Ltd."},
                {"id": "petitioner_holding_pct", "label": "Petitioner Shareholding (%)", "type": "number", "required": True, "placeholder": "18.5"},
                {"id": "respondent_company", "label": "Respondent Corporate Debtor / Company", "type": "string", "required": True, "placeholder": "Bharat Commercial Transshipment Ltd."},
                {"id": "company_cin", "label": "Company CIN", "type": "string", "required": True, "validator": "cin", "placeholder": "L60200MH2008PLC184321"},
                {"id": "oppressive_acts", "label": "Summary of Prejudicial & Oppressive Conduct", "type": "text", "required": True, "placeholder": "1. Siphoning of corporate funds through unapproved related-party contracts. 2. Purported rights issue engineered without statutory notice to dilute Petitioner below Section 244 threshold."},
                {"id": "prayer_sought", "label": "Substantive Reliefs / Prayers Sought", "type": "text", "required": True, "placeholder": "Direct forensic investigation into accounts; Supersede existing board and appoint an independent administrator; Nullify illegal share allotment."},
            ]
        },
        body_template="""IN THE NATIONAL COMPANY LAW TRIBUNAL
{{ nclt_bench | upper }}
COMPANY PETITION NO. ______ OF {{ case_year }}

(Under Sections 241 and 242 read with Section 244 of the Companies Act, 2013)

IN THE MATTER OF:
{{ petitioner_name }}
... PETITIONER

VERSUS

1. {{ respondent_company }}
   (CIN: {{ company_cin }})
2. BOARD OF DIRECTORS / MAJORITY SHAREHOLDERS
... RESPONDENTS

COMPANY PETITION UNDER SECTION 241 & 242 OF THE COMPANIES ACT, 2013
========================================================================================================================

THE PETITIONER RESPECTFULLY SHOWETH:

1. JURISDICTION & STANDING UNDER SECTION 244:
   That the Petitioner holds {{ petitioner_holding_pct }}% of the issued and paid-up equity share capital of Respondent No. 1 Company, thereby satisfying the mandatory statutory threshold under Section 244(1)(a) of the Companies Act, 2013 (holding not less than one-tenth of the issued share capital).

2. OPPRESSIVE AND PREJUDICIAL AFFAIRS:
   The affairs of Respondent No. 1 have been and are being conducted in a manner prejudicial and oppressive to the Petitioner and prejudicial to the public interest, in specific violation of fiduciary duties enunciated by the Hon'ble Supreme Court in Tata Consultancy Services Ltd. v. Cyrus Investments Pvt. Ltd. (2021) 9 SCC 449:
   {{ oppressive_acts }}

3. JUST AND EQUITABLE GROUND:
   To wind up the Company would unfairly prejudice the Petitioner and genuine stakeholders, but the facts justify the making of an order under Section 242 providing comprehensive remedial relief.

PRAYER:
WHEREFORE, the Petitioner most humbly prays that this Hon'ble Tribunal may be pleased to:
{{ prayer_sought }}

PETITIONER
Through Advocate for Petitioner
Place: {{ nclt_bench }}
Date: {{ current_date_formatted }}
"""
    ),

    # ─── 3. Affidavit of Evidence (Order XIX R.3 CPC) ────────────────────────
    "AFFIDAVIT_EVIDENCE_V1": TemplateManifest(
        template_id="AFFIDAVIT_EVIDENCE_V1",
        title="Affidavit of Evidence (Order XIX Rule 3, CPC)",
        version="1.0.0",
        statutory_anchor="Order XIX Rule 3, Code of Civil Procedure, 1908",
        category="AFFIDAVIT",
        description="Formal sworn deposition affidavit for civil proceedings and interlocutory applications.",
        controlling_precedent="Satyadhyan Ghosal v. Deorajin Debi, AIR 1960 SC 941",
        schema_definition={
            "template_id": "AFFIDAVIT_EVIDENCE_V1",
            "statutory_anchor": "Order XIX Rule 3, Code of Civil Procedure, 1908",
            "fields": [
                {"id": "court", "label": "Court / Forum", "type": "string", "required": True, "default": "IN THE HIGH COURT OF DELHI AT NEW DELHI"},
                {"id": "case_no", "label": "Suit / Case Number", "type": "string", "required": True, "placeholder": "CS (COMM) No. 420 of 2024"},
                {"id": "cause_title", "label": "Cause Title", "type": "string", "required": True, "placeholder": "ABC Logistics Ltd. v. XYZ Freight Corp."},
                {"id": "deponent_name", "label": "Deponent Full Name", "type": "string", "required": True, "placeholder": "Rajesh Kumar"},
                {"id": "deponent_age", "label": "Deponent Age", "type": "number", "required": True, "placeholder": "45"},
                {"id": "deponent_parent", "label": "Father's / Mother's Name", "type": "string", "required": True, "placeholder": "Shri S. P. Kumar"},
                {"id": "deponent_address", "label": "Deponent Address", "type": "text", "required": True, "placeholder": "A-12, Barakhamba Road, Connaught Place, New Delhi - 110001"},
                {"id": "deponent_role", "label": "Deponent Capacity", "type": "string", "required": True, "placeholder": "Authorized Representative / Director"},
                {"id": "affirmation_place", "label": "Place of Affirmation", "type": "string", "required": True, "default": "New Delhi"},
                {"id": "facts_statement", "label": "Sworn Statements of Fact", "type": "text", "required": True, "placeholder": "1. That I am fully conversant with the facts. 2. That the defendant committed material breach of invoice payments totaling INR 48,50,000."},
            ]
        },
        body_template="""{{ court | upper }}
{{ case_no }}
IN THE MATTER OF:
{{ cause_title }}

AFFIDAVIT OF EVIDENCE UNDER ORDER XIX RULE 3, CODE OF CIVIL PROCEDURE, 1908
========================================================================================================================

I, {{ deponent_name }}, aged about {{ deponent_age }} years, son/daughter of {{ deponent_parent }}, residing at {{ deponent_address }}, do hereby solemnly affirm and declare on oath as under:

1. That I am the {{ deponent_role }} of the Petitioner/Plaintiff and am fully conversant with the facts and circumstances of the present case, and as such, competent to swear and depose to this affidavit.

2. That the statements made in paragraphs below are true and correct to my knowledge derived from official books, accounts, and correspondence:
{{ facts_statement }}

3. That under the doctrine affirmed by the Supreme Court in Satyadhyan Ghosal v. Deorajin Debi, AIR 1960 SC 941, the issues decided herein operate with finality between the parties.

DEPONENT

VERIFICATION:
Verified at {{ affirmation_place }} on this {{ current_date_formatted }} that the contents of the above affidavit are true and correct to my knowledge, no part of it is false, and nothing material has been concealed therefrom.

DEPONENT
"""
    ),

    # ─── 4. Director Due-Diligence Affidavit (Sec 179 IT Act) ─────────────────
    "AFFIDAVIT_DIR_DD_V1": TemplateManifest(
        template_id="AFFIDAVIT_DIR_DD_V1",
        title="Director Due-Diligence Affidavit (Sec 179 Income Tax Act)",
        version="1.0.0",
        statutory_anchor="Section 179, Income Tax Act, 1961",
        category="AFFIDAVIT",
        description="Statutory affidavit establishing affirmative due diligence against personal tax liability.",
        controlling_precedent="Pr. CIT v. Siemens Ltd., (2017) 394 ITR 1 (SC)",
        schema_definition={
            "template_id": "AFFIDAVIT_DIR_DD_V1",
            "statutory_anchor": "Section 179, Income Tax Act, 1961",
            "fields": [
                {"id": "court", "label": "Appellate Authority / Forum", "type": "string", "required": True, "default": "BEFORE THE PRINCIPAL COMMISSIONER OF INCOME TAX (APPEALS), NEW DELHI"},
                {"id": "assessment_year", "label": "Assessment Year", "type": "string", "required": True, "placeholder": "2022-23"},
                {"id": "deponent_name", "label": "Director Name", "type": "string", "required": True, "placeholder": "Anil Deshmukh"},
                {"id": "deponent_din", "label": "Director DIN", "type": "string", "required": True, "validator": "din", "placeholder": "02345678"},
                {"id": "deponent_pan", "label": "Director PAN", "type": "string", "required": True, "validator": "pan", "placeholder": "ABCDE1234F"},
                {"id": "company_name", "label": "Corporate Debtor / Assessee Company", "type": "string", "required": True, "placeholder": "Zenith Infra Limited"},
                {"id": "due_diligence_facts", "label": "Affirmative Due Diligence Facts", "type": "text", "required": True, "placeholder": "Appointed solely as a non-executive nominee director; had no cheque-signing or day-to-day statutory remittance authority; recorded written dissents regarding delayed tax filings."},
            ]
        },
        body_template="""{{ court | upper }}
IN THE MATTER OF RECOVERY PROCEEDINGS UNDER SECTION 179 OF THE INCOME TAX ACT, 1961
ASSESSMENT YEAR: {{ assessment_year }}
IN RE: {{ company_name }}

AFFIDAVIT OF DUE DILIGENCE BY FORMER / NOMINEE DIRECTOR
========================================================================================================================

I, {{ deponent_name }}, (DIN: {{ deponent_din }}, PAN: {{ deponent_pan }}), do hereby solemnly affirm and state as under:

1. That I was appointed as a non-executive director on the Board of {{ company_name }} and was never in operational control of statutory remittances or corporate finance.

2. That the non-recovery of any assessed tax dues cannot be attributed to any gross neglect, misfeasance, or breach of fiduciary duty on my part.

3. AFFIRMATIVE DUE DILIGENCE PURSUANT TO SUPREME COURT DICTA:
   In terms of the binding jurisprudence laid down in Pr. CIT v. Siemens Ltd. (2017) 394 ITR 1 (SC), personal vicarious liability under Section 179 cannot be fastened on a director who proves non-culpability and exercise of due diligence:
{{ due_diligence_facts }}

DEPONENT

VERIFICATION:
Verified at New Delhi on {{ current_date_formatted }} that the statements made herein are true to the best of my knowledge and records.

DEPONENT
"""
    ),

    # ─── 5. Statutory Demand Notice (Sec 138 NI Act) ─────────────────────────
    "NOTICE_DEMAND_138_V1": TemplateManifest(
        template_id="NOTICE_DEMAND_138_V1",
        title="Statutory Demand Notice (Section 138 NI Act)",
        version="1.0.0",
        statutory_anchor="Section 138 & 142, Negotiable Instruments Act, 1881",
        category="NOTICE",
        description="Mandatory pre-litigation legal demand notice for dishonour of cheque.",
        controlling_precedent="Dashrath Rupsingh Rathod v. State of Maharashtra, (2014) 9 SCC 129",
        schema_definition={
            "template_id": "NOTICE_DEMAND_138_V1",
            "statutory_anchor": "Section 138 & 142, Negotiable Instruments Act, 1881",
            "fields": [
                {"id": "payee_name", "label": "Client / Payee Name", "type": "string", "required": True, "placeholder": "Apex Industrial Supplies LLP"},
                {"id": "drawer_name", "label": "Accused / Drawer Name", "type": "string", "required": True, "placeholder": "Sunil V. Mehta"},
                {"id": "drawer_address", "label": "Drawer Address", "type": "text", "required": True, "placeholder": "B-44, Industrial Area, Okhla Phase II, New Delhi - 110020"},
                {"id": "cheque_no", "label": "Cheque Number", "type": "string", "required": True, "placeholder": "409218"},
                {"id": "cheque_date", "label": "Cheque Date", "type": "date", "required": True, "validator": "date_not_future"},
                {"id": "cheque_amount", "label": "Cheque Amount (INR)", "type": "number", "required": True, "placeholder": "1500000"},
                {"id": "bank_name", "label": "Drawee Bank & Branch", "type": "string", "required": True, "placeholder": "HDFC Bank, Connaught Place Branch"},
                {"id": "dishonour_date", "label": "Bank Return Memo Date", "type": "date", "required": True, "validator": "date_not_future"},
                {"id": "dishonour_reason", "label": "Reason for Dishonour", "type": "select", "required": True, "options": ["Funds Insufficient", "Account Closed", "Stop Payment by Drawer", "Signatures Differ"]},
                {"id": "advocate_name", "label": "Advocate Sending Notice", "type": "string", "required": True, "placeholder": "Adv. Prithviraj Patil"},
            ]
        },
        body_template="""LEGAL DEMAND NOTICE UNDER SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881
(REGISTERED POST A.D. & SPEED POST)

Date: {{ current_date_formatted }}

TO,
{{ drawer_name }}
{{ drawer_address }}

UNDER INSTRUCTIONS FROM AND ON BEHALF OF MY CLIENT:
{{ payee_name }} ("My Client")

SIR/MADAM,

Under instructions from my aforesaid Client, I hereby serve upon you the following Statutory Notice under Section 138 of the Negotiable Instruments Act, 1881:

1. That in discharge of your legally enforceable debt and liability towards My Client, you drew Cheque No. {{ cheque_no }} dated {{ cheque_date_formatted }} for an amount of {{ formatted_currency }} ({{ amount_in_words }}) drawn on {{ bank_name }}.

2. That upon presentation by My Client through their bankers, the said cheque was dishonoured and returned unpaid by your bank with return memo dated {{ dishonour_date_formatted }} citing reason: "{{ dishonour_reason }}".

3. That the intimation of dishonour was received by My Client within the statutory period of 30 days.

4. I HEREBY CALL UPON YOU to pay the aforesaid sum of {{ formatted_currency }} to My Client within FIFTEEN (15) DAYS of the receipt of this notice, failing which My Client shall initiate criminal prosecution against you under Section 138 and 142 of the Negotiable Instruments Act, 1881 and Section 420 of the Indian Penal Code, holding you liable for imprisonment and punitive damages.

Yours faithfully,

________________________________________
{{ advocate_name }}
Advocate for the Complainant / Payee
"""
    ),

    # ─── 6. Generic Board Resolution ─────────────────────────────────────────
    "BOARD_RES_GENERIC_V1": TemplateManifest(
        template_id="BOARD_RES_GENERIC_V1",
        title="Generic Board Resolution",
        version="1.0.0",
        statutory_anchor="Section 173 & 179, Companies Act, 2013",
        category="CORPORATE_RESOLUTION",
        description="Standard certified true copy of Board Resolution for corporate authorizations, bank accounts, or contracts.",
        schema_definition={
            "template_id": "BOARD_RES_GENERIC_V1",
            "statutory_anchor": "Section 173 & 179, Companies Act, 2013",
            "fields": [
                {"id": "company_cin", "label": "Company CIN", "type": "string", "required": True, "validator": "cin", "placeholder": "U72200MH2013PTC248912"},
                {"id": "company_name", "label": "Company Name", "type": "string", "required": True, "placeholder": "Acme Ventures Private Limited"},
                {"id": "resolution_subject", "label": "Resolution Subject", "type": "string", "required": True, "placeholder": "Opening of Current Bank Account with Kotak Mahindra Bank"},
                {"id": "meeting_date", "label": "Meeting Date", "type": "date", "required": True, "validator": "date_not_future"},
                {"id": "resolution_body", "label": "Text of Resolutions Passed", "type": "text", "required": True, "placeholder": "RESOLVED THAT a banking account be opened in the name of the Company..."},
                {"id": "signatory", "label": "Authorized Signatory", "type": "string", "required": True, "placeholder": "Director / Company Secretary"},
            ]
        },
        body_template="""CERTIFIED TRUE COPY OF THE RESOLUTION PASSED AT THE BOARD MEETING OF {{ company_name | upper }} HELD ON {{ meeting_date_formatted }}.

CIN: {{ company_cin }}

SUBJECT: {{ resolution_subject | upper }}
========================================================================================================================

"{{ resolution_body }}"

Certified True Copy,
For {{ company_name | upper }}

________________________________________
{{ signatory }}
"""
    ),

    # ─── 7. MGT-14 Filing Cover Note (S.117 CA 2013) ─────────────────────────
    "MGT14_COVER_V1": TemplateManifest(
        template_id="MGT14_COVER_V1",
        title="MGT-14 Filing Cover Note",
        version="1.0.0",
        statutory_anchor="Section 117, Companies Act, 2013",
        category="COMPLIANCE",
        description="Statutory filing cover note and compliance dossier for e-Form MGT-14 submission to the Registrar of Companies within 30 days.",
        schema_definition={
            "template_id": "MGT14_COVER_V1",
            "statutory_anchor": "Section 117, Companies Act, 2013",
            "fields": [
                {"id": "company_cin", "label": "Company CIN", "type": "string", "required": True, "validator": "cin"},
                {"id": "company_name", "label": "Company Name", "type": "string", "required": True},
                {"id": "roc_jurisdiction", "label": "ROC Jurisdiction", "type": "string", "required": True, "placeholder": "Registrar of Companies, Maharashtra, Mumbai"},
                {"id": "resolution_date", "label": "Date of Resolution Passed", "type": "date", "required": True, "validator": "date_not_future"},
                {"id": "purpose", "label": "Purpose of Filing", "type": "string", "required": True, "placeholder": "Filing of Special Resolution passed under Section 180(1)(c) for borrowing limits"},
                {"id": "professional_name", "label": "Certifying Practising Professional", "type": "string", "required": True, "placeholder": "FCS Anand Gupta (CP No. 8912)"},
            ]
        },
        body_template="""MEMORANDUM & COMPLIANCE COVER NOTE FOR FORM MGT-14
PURSUANT TO SECTION 117(1) OF THE COMPANIES ACT, 2013
========================================================================================================================

TO,
THE REGISTRAR OF COMPANIES,
{{ roc_jurisdiction | upper }}

IN RE: {{ company_name | upper }} (CIN: {{ company_cin }})

SUBJECT: STATUTORY FILING OF RESOLUTIONS & AGREEMENTS IN FORM MGT-14

1. STATUTORY TIMELINE REQUIREMENT:
   Pursuant to Section 117(1) of the Companies Act, 2013, a copy of every resolution passed under Section 117(3) must be filed with the Registrar within THIRTY (30) DAYS of the passing thereof.

2. DETAILS OF RESOLUTION:
   - Date of Passing: {{ resolution_date_formatted }}
   - Statutory Purpose: {{ purpose }}
   - Statutory Due Date (30 Days): {{ due_date_formatted }}

3. CERTIFICATION:
   The undersigned Practising Company Secretary has examined the records, minutes, and registers and certifies that the said resolution conforms to the provisions of the Companies Act, 2013.

Certified by:
________________________________________
{{ professional_name }}
Date: {{ current_date_formatted }}
"""
    )
}


def list_templates(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns list of templates, optionally filtered by category."""
    results = []
    for t_id, t in CANONICAL_TEMPLATES.items():
        if category and category != "ALL" and t.category != category:
            continue
        results.append({
            "id": t.template_id,
            "name": t.title,
            "category": t.category,
            "description": t.description,
            "statutory_anchor": t.statutory_anchor,
            "controlling_precedent": t.controlling_precedent,
            "output_formats": t.output_formats,
            "field_count": len(t.schema_definition.get("fields", []))
        })
    return results


def get_template(template_id: str) -> Optional[TemplateManifest]:
    """Retrieves full template package including schema and body template."""
    return CANONICAL_TEMPLATES.get(template_id)

