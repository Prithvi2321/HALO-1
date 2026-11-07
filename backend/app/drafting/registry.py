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
    category: str  # CORPORATE_RESOLUTION | PETITION | AFFIDAVIT | NOTICE | COMPLIANCE | AGREEMENT
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
                {"id": "target_language", "label": "Output Language", "type": "select", "required": False, "default": "en", "options": [{"label": "English (Standard Legal)", "value": "en"}, {"label": "हिंदी (Hindi - Devnagari)", "value": "hi"}, {"label": "द्विभाषी (Bilingual - English + Hindi)", "value": "bilingual"}]},
            ],
            "conditional": [
                {
                    "if": {"articles_authorise": False},
                    "then": {"warn": "Section 161(1) of Companies Act, 2013 explicitly mandates that the Articles of Association must confer power on the Board. If not authorised, Articles must first be amended."}
                }
            ]
        },
        body_template="""{% if target_language == 'hi' %}
{{ company_name | upper }} के निदेशक मंडल (बोर्ड ऑफ डायरेक्टर्स) की बैठक में पारित संकल्प की प्रमाणित प्रतिलिपि
बैठक की तिथि: {{ meeting_date_formatted }} | बैठक का स्थान: {{ meeting_venue }}

सीआईएन (CIN): {{ company_cin }}
पंजीकृत कार्यालय (Registered Office): {{ registered_office }}

------------------------------------------------------------------------------------------------------------------------
सुश्री/श्री {{ director_name | upper }} (DIN: {{ director_din }}) की अतिरिक्त निदेशक (ADDITIONAL DIRECTOR) के रूप में नियुक्ति
------------------------------------------------------------------------------------------------------------------------

"यह संकल्प पारित किया गया कि कंपनी अधिनियम, 2013 की धारा 161(1) तथा अन्य लागू प्रावधानों (यदि कोई हो), तथा कंपनी के अंतर्नियमों (Articles of Association) के सुसंगत अनुच्छेदों के अनुसरण में, सुश्री/श्री {{ director_name }} (निदेशक पहचान संख्या / DIN: {{ director_din }}), जिन्होंने फॉर्म डीआईआर-2 (DIR-2) में निदेशक के रूप में कार्य करने की सहमति प्रदान की है तथा घोषित किया है कि वे अधिनियम की धारा 164 के अधीन निदेशक नियुक्त होने के लिए अयोग्य नहीं हैं, को {{ effective_date_formatted }} से कंपनी के निदेशक मंडल में अतिरिक्त निदेशक के रूप में नियुक्त किया जाता है।

यह आगे संकल्प पारित किया गया कि सुश्री/श्री {{ director_name }} कंपनी की आगामी वार्षिक आम बैठक (AGM) की तिथि तक अथवा उस अंतिम तिथि तक जिस पर वार्षिक आम बैठक आयोजित की जानी चाहिए थी, जो भी पहले हो, पद धारण करेंगे।

यह आगे संकल्प पारित किया गया कि {{ co_signatory }} को कंपनी की ओर से इस संकल्प को प्रभावी बनाने हेतु आवश्यक सभी कार्य, विलेख एवं औपचारिकताएं पूर्ण करने के लिए अधिकृत किया जाता है, जिसमें इस नियुक्ति के 30 दिनों के भीतर कंपनी रजिस्ट्रार (ROC) के समक्ष फॉर्म डीआईआर-12 (DIR-12) दाखिल करना तथा कंपनी के सांविधिक रजिस्टरों में अपेक्षित प्रविष्टियां करना सम्मिलित है।"

कृते एवं कंपनी की ओर से
{{ company_name | upper }}


________________________________________
{{ co_signatory }}
तिथि: {{ meeting_date_formatted }}
स्थान: {{ meeting_venue }}

{% elif target_language == 'bilingual' %}
CERTIFIED TRUE COPY OF BOARD RESOLUTION / निदेशक मंडल के संकल्प की प्रमाणित प्रतिलिपि
APPOINTMENT OF ADDITIONAL DIRECTOR UNDER SECTION 161(1) OF COMPANIES ACT, 2013 / धारा 161(1) कंपनी अधिनियम के अधीन अतिरिक्त निदेशक नियुक्ति
========================================================================================================================

Company / कंपनी: {{ company_name | upper }}
CIN / सीआईएन: {{ company_cin }}
Registered Office / पंजीकृत कार्यालय: {{ registered_office }}
Meeting Date / बैठक तिथि: {{ meeting_date_formatted }} | Venue / स्थान: {{ meeting_venue }}

------------------------------------------------------------------------------------------------------------------------
APPOINTMENT OF MS./MR. {{ director_name | upper }} (DIN: {{ director_din }}) AS AN ADDITIONAL DIRECTOR / सुश्री/श्री {{ director_name }} की नियुक्ति
------------------------------------------------------------------------------------------------------------------------

"RESOLVED THAT pursuant to the provisions of Section 161(1) and other applicable provisions of the Companies Act, 2013, Ms./Mr. {{ director_name }} (DIN: {{ director_din }}) be and is hereby appointed as an Additional Director of the Company with effect from {{ effective_date_formatted }}.
(संकल्प पारित किया गया कि कंपनी अधिनियम, 2013 की धारा 161(1) के अंतर्गत सुश्री/श्री {{ director_name }} (DIN: {{ director_din }}) को {{ effective_date_formatted }} से कंपनी के अतिरिक्त निदेशक के रूप में नियुक्त किया जाता है।)

RESOLVED FURTHER THAT Ms./Mr. {{ director_name }} shall hold office up to the date of the next Annual General Meeting (AGM) of the Company.
(सुश्री/श्री {{ director_name }} कंपनी की आगामी वार्षिक आम बैठक की तिथि तक पद धारण करेंगे।)

RESOLVED FURTHER THAT {{ co_signatory }} be and is hereby authorized to file Form DIR-12 with the Registrar of Companies (ROC) within 30 days and take all necessary steps to give effect to this resolution.
({{ co_signatory }} को आरओसी के समक्ष 30 दिनों में फॉर्म डीआईआर-12 दाखिल करने तथा सभी आवश्यक कदम उठाने हेतु अधिकृत किया जाता है।)"

For and on behalf of / कृते एवं कंपनी की ओर से:
{{ company_name | upper }}


________________________________________
{{ co_signatory }}
Date / दिनांक: {{ meeting_date_formatted }}
Place / स्थान: {{ meeting_venue }}

{% else %}
CERTIFIED TRUE COPY OF THE RESOLUTION PASSED AT THE MEETING OF THE BOARD OF DIRECTORS OF {{ company_name | upper }} HELD ON {{ meeting_date_formatted }} AT {{ meeting_venue }}.

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
{% endif %}"""
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
                {"id": "target_language", "label": "Output Language", "type": "select", "required": False, "default": "en", "options": [{"label": "English (Standard Legal)", "value": "en"}, {"label": "हिंदी (Hindi - Devnagari)", "value": "hi"}, {"label": "द्विभाषी (Bilingual - English + Hindi)", "value": "bilingual"}]},
            ]
        },
        body_template="""{% if target_language == 'hi' %}
राष्ट्रीय कंपनी विधि अधिकरण (NCLT) के समक्ष
{{ nclt_bench | upper }}
कंपनी याचिका संख्या: ______ वर्ष {{ case_year }}

(कंपनी अधिनियम, 2013 की धारा 241 एवं 242 पठित धारा 244 के अधीन)

मामले में:
{{ petitioner_name }}
... याचिकाकर्ता

बनाम

1. {{ respondent_company }}
   (सीआईएन: {{ company_cin }})
2. निदेशक मंडल / बहुमत शेयरधारक
... प्रतिवादीगण

कंपनी अधिनियम, 2013 की धारा 241 एवं 242 के अधीन कंपनी याचिका
========================================================================================================================

याचिकाकर्ता सादर निवेदन करता है:

1. क्षेत्राधिकार एवं धारा 244 के अधीन वैधानिक अहर्ता (Locus Standi):
   यह कि याचिकाकर्ता के पास प्रतिवादी सं. 1 कंपनी की निर्गमित एवं चुकता इक्विटी शेयर पूंजी का {{ petitioner_holding_pct }}% भाग है, जो कंपनी अधिनियम, 2013 की धारा 244(1)(a) के तहत निर्धारित वैधानिक अहर्ता (कम से कम 10% शेयरधारिता) को पूर्णतः संतुष्ट करता है।

2. उत्पीड़नकारी एवं पूर्वाग्रहपूर्ण कार्यकलाप:
   प्रतिवादी सं. 1 के कार्यकलापों का संचालन याचिकाकर्ता तथा जनहित के प्रति अत्यंत पूर्वाग्रहपूर्ण एवं उत्पीड़नकारी रीति से किया गया है, जो माननीय सर्वोच्च न्यायालय द्वारा टाटा कंसल्टेंसी सर्विसेज लि. बनाम साइरस इन्वेस्टमेंट्स प्रा. लि. (2021) 9 SCC 449 में प्रतिपादित सिद्धांतों का खुला उल्लंघन है:
   {{ oppressive_acts }}

3. न्यायसंगत एवं साम्यपूर्ण आधार (Just and Equitable Ground):
   कंपनी का परिसमापन याचिकाकर्ता एवं वैध अंशधारकों के हितों पर अनुचित प्रतिकूल प्रभाव डालेगा, किंतु प्रस्तुत तथ्य धारा 242 के अधीन व्यापक सुधारात्मक अनुतोष प्रदान करने के पूर्ण आधार प्रदान करते हैं।

प्रार्थना / याचना:
अतः याचिकाकर्ता अत्यंत विनम्रतापूर्वक प्रार्थना करता है कि यह माननीय अधिकरण कृपापूर्वक निम्नलिखित अनुतोष प्रदान करने की कृपा करे:
{{ prayer_sought }}

याचिकाकर्ता
द्वारा अधिवक्ता, याचिकाकर्ता
स्थान: {{ nclt_bench }}
दिनांक: {{ current_date_formatted }}

{% elif target_language == 'bilingual' %}
BEFORE THE HON'BLE NATIONAL COMPANY LAW TRIBUNAL / माननीय राष्ट्रीय कंपनी विधि अधिकरण
{{ nclt_bench | upper }}
COMPANY PETITION NO. ______ OF {{ case_year }} / कंपनी याचिका संख्या ______ वर्ष {{ case_year }}

(Under Sections 241 & 242 r/w Section 244 of Companies Act, 2013 / धारा 241 व 242 के अंतर्गत)

IN THE MATTER OF / मामले में:
{{ petitioner_name }} ... PETITIONER / याचिकाकर्ता
VERSUS / बनाम
{{ respondent_company }} (CIN: {{ company_cin }}) & Ors. ... RESPONDENTS / प्रतिवादीगण

COMPANY PETITION UNDER SECTION 241 & 242 / उत्पीड़न एवं कुप्रबंधन याचिका
========================================================================================================================

1. STANDING UNDER SECTION 244 / धारा 244 अहर्ता:
   Petitioner holds {{ petitioner_holding_pct }}% equity share capital satisfying Section 244(1)(a).
   (याचिकाकर्ता के पास {{ petitioner_holding_pct }}% शेयरधारिता है, जो धारा 244(1)(a) की 10% न्यूनतम वैधानिक शर्त को पूरा करती है।)

2. OPPRESSION & MISMANAGEMENT / उत्पीड़नकारी आचरण:
   The affairs of the Respondent Company are being conducted in an oppressive and prejudicial manner:
   (कंपनी के मामलों का संचालन उत्पीड़नकारी एवं पूर्वाग्रहपूर्ण रीति से किया जा रहा है:)
   {{ oppressive_acts }}

3. PRAYERS / याचना:
   WHEREFORE, Petitioner prays that this Hon'ble Tribunal may grant the following reliefs:
   (अतः प्रार्थना है कि माननीय अधिकरण निम्नलिखित अनुतोष प्रदान करने की कृपा करे:)
   {{ prayer_sought }}

PETITIONER / याचिकाकर्ता
Place / स्थान: {{ nclt_bench }} | Date / दिनांक: {{ current_date_formatted }}

{% else %}
IN THE NATIONAL COMPANY LAW TRIBUNAL
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
{% endif %}"""
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
                {"id": "target_language", "label": "Output Language", "type": "select", "required": False, "default": "en", "options": [{"label": "English (Standard Legal)", "value": "en"}, {"label": "हिंदी (Hindi - Devnagari)", "value": "hi"}, {"label": "द्विभाषी (Bilingual - English + Hindi)", "value": "bilingual"}]},
            ]
        },
        body_template="""{% if target_language == 'hi' %}
{{ court | upper }}
{{ case_no }}
मामले में:
{{ cause_title }}

साक्ष्य का शपथ पत्र (सिविल प्रक्रिया संहिता, 1908 के आदेश XIX नियम 3 के अधीन)
========================================================================================================================

मैं, {{ deponent_name }}, आयु लगभग {{ deponent_age }} वर्ष, पुत्र/पुत्री {{ deponent_parent }}, निवासी {{ deponent_address }}, सत्यनिष्ठापूर्वक प्रतिज्ञान करता/करती हूँ एवं शपथ पर निम्नलिखित कथन करता/करती हूँ:

1. यह कि मैं याचिकाकर्ता/वादी का/की {{ deponent_role }} हूँ और वर्तमान वाद के तथ्यों एवं परिस्थितियों से पूर्णतः अवगत हूँ, तथा इस रूप में यह शपथ पत्र प्रस्तुत करने एवं साक्ष्य देने हेतु पूर्ण सक्षम हूँ।

2. यह कि नीचे दिए गए प्रस्तरों में किए गए कथन मेरे अधिकृत अभिलेखों, खातों एवं पत्राचार के आधार पर मेरे ज्ञान में सत्य एवं सही हैं:
{{ facts_statement }}

3. यह कि सर्वोच्च न्यायालय द्वारा सत्यध्यान घोषाल बनाम देवराजिन देबी, AIR 1960 SC 941 में प्रतिपादित विधिक सिद्धांत के अधीन, इस कार्यवाही में निर्णीत बिंदु पक्षकारों के मध्य अंतिम रूप से बाध्यकारी हैं।

शपथकर्ता (DEPONENT)

सत्यापन (VERIFICATION):
आज दिनांक {{ current_date_formatted }} को स्थान {{ affirmation_place }} पर सत्यापित किया जाता है कि उपरोक्त शपथ पत्र की संपूर्ण सामग्री मेरे ज्ञान में सत्य एवं सही है, इसका कोई भी भाग असत्य नहीं है और इसमें से कोई भी तात्विक तथ्य छिपाया नहीं गया है।

शपथकर्ता (DEPONENT)

{% elif target_language == 'bilingual' %}
{{ court | upper }}
{{ case_no }}
IN THE MATTER OF / मामले में: {{ cause_title }}

AFFIDAVIT OF EVIDENCE UNDER ORDER XIX RULE 3 CPC / साक्ष्य का शपथ पत्र (आदेश XIX नियम 3 सीपीसी)
========================================================================================================================

I, {{ deponent_name }}, Age {{ deponent_age }} yrs, S/o or D/o {{ deponent_parent }}, R/o {{ deponent_address }}, do hereby solemnly affirm and state:
(मैं, {{ deponent_name }}, आयु {{ deponent_age }} वर्ष, निवासी {{ deponent_address }}, सत्यनिष्ठापूर्वक शपथ पर कथन करता हूँ:)

1. That I am the {{ deponent_role }} of the Petitioner/Plaintiff and fully conversant with the facts of the case.
   (मैं वादी/याचिकाकर्ता का {{ deponent_role }} हूँ तथा मामले के तथ्यों से भलीभांति परिचित हूँ।)

2. STATEMENT OF FACTS / तथ्यों का विवरण:
{{ facts_statement }}

3. Binding precedent: Satyadhyan Ghosal v. Deorajin Debi, AIR 1960 SC 941.

DEPONENT / शपथकर्ता

VERIFICATION / सत्यापन:
Verified at {{ affirmation_place }} on {{ current_date_formatted }} that contents are true and correct.
(दिनांक {{ current_date_formatted }} को स्थान {{ affirmation_place }} पर सत्यापित किया गया कि समस्त कथन सत्य एवं सही हैं।)

DEPONENT / शपथकर्ता

{% else %}
{{ court | upper }}
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
{% endif %}"""
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
                {"id": "target_language", "label": "Output Language", "type": "select", "required": False, "default": "en", "options": [{"label": "English (Standard Legal)", "value": "en"}, {"label": "हिंदी (Hindi - Devnagari)", "value": "hi"}, {"label": "द्विभाषी (Bilingual - English + Hindi)", "value": "bilingual"}]},
            ]
        },
        body_template="""{% if target_language == 'hi' %}
{{ court | upper }}
आयकर अधिनियम, 1961 की धारा 179 के अधीन वसूली कार्यवाही के संबंध में
कर निर्धारण वर्ष: {{ assessment_year }}
संदर्भ में: {{ company_name }}

पूर्व / नामित निदेशक द्वारा सम्यक तत्परता (DUE DILIGENCE) का शपथ पत्र
========================================================================================================================

मैं, {{ deponent_name }} (DIN: {{ deponent_din }}, PAN: {{ deponent_pan }}), सत्यनिष्ठापूर्वक शपथपूर्वक कथन करता हूँ कि:

1. यह कि मैं {{ company_name }} के निदेशक मंडल में केवल एक गैर-कार्यकारी (Non-Executive) निदेशक के रूप में नियुक्त था और कभी भी सांविधिक भुगतानों अथवा कंपनी के दिन-प्रतिदिन के वित्तीय संचालन के नियंत्रण में नहीं रहा हूँ।

2. यह कि कर बकाए की किसी भी वसूली की विफलता को मेरे किसी भी घोर उपेक्षा, अवचार (Misfeasance) अथवा वैधानिक कर्तव्य भंग का परिणाम नहीं माना जा सकता।

3. सर्वोच्च न्यायालय के निर्णयों के अनुसार सम्यक तत्परता:
   माननीय सर्वोच्च न्यायालय द्वारा पी.आर. सीआईटी बनाम सीमेंस लि. (2017) 394 ITR 1 (SC) में प्रतिपादित विधि के अनुसार, धारा 179 के अधीन व्यक्तिगत दायित्व ऐसे निदेशक पर आरोपित नहीं किया जा सकता जो अपनी निर्दोषिता तथा सम्यक तत्परता (Due Diligence) सिद्ध करता है:
{{ due_diligence_facts }}

शपथकर्ता (DEPONENT)

सत्यापन (VERIFICATION):
नई दिल्ली में दिनांक {{ current_date_formatted }} को सत्यापित किया जाता है कि इसमें दिए गए कथन मेरे सर्वोत्तम ज्ञान एवं अभिलेखों के अनुसार सत्य एवं सही हैं।

शपथकर्ता (DEPONENT)

{% elif target_language == 'bilingual' %}
{{ court | upper }}
PROCEEDINGS UNDER SECTION 179, INCOME TAX ACT, 1961 / धारा 179 आयकर अधिनियम, 1961
ASSESSMENT YEAR / कर निर्धारण वर्ष: {{ assessment_year }} | IN RE / संदर्भ: {{ company_name }}

AFFIDAVIT OF DUE DILIGENCE BY DIRECTOR / निदेशक द्वारा सम्यक तत्परता का शपथ पत्र
========================================================================================================================

I, {{ deponent_name }} (DIN: {{ deponent_din }}, PAN: {{ deponent_pan }}), do solemnly affirm:
(मैं, {{ deponent_name }}, (DIN: {{ deponent_din }}, PAN: {{ deponent_pan }}), शपथपूर्वक कथन करता हूँ:)

1. That I was a non-executive director with no operational control over statutory remittances.
   (मैं कंपनी में केवल एक गैर-कार्यकारी निदेशक था तथा वित्तीय भुगतानों पर मेरा कोई परिचालन नियंत्रण नहीं था।)

2. AFFIRMATIVE DUE DILIGENCE / सम्यक तत्परता के तथ्य (Pr. CIT v. Siemens Ltd. (2017) 394 ITR 1 SC):
{{ due_diligence_facts }}

DEPONENT / शपथकर्ता

VERIFICATION / सत्यापन:
Verified on {{ current_date_formatted }} that statements are true and correct.
(दिनांक {{ current_date_formatted }} को सत्यापित किया गया कि उक्त विवरण सत्य एवं सही है।)

DEPONENT / शपथकर्ता

{% else %}
{{ court | upper }}
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
{% endif %}"""
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
                {"id": "target_language", "label": "Output Language", "type": "select", "required": False, "default": "en", "options": [{"label": "English (Standard Legal)", "value": "en"}, {"label": "हिंदी (Hindi - Devnagari)", "value": "hi"}, {"label": "द्विभाषी (Bilingual - English + Hindi)", "value": "bilingual"}]},
            ]
        },
        body_template="""{% if target_language == 'hi' %}
विधिक मांग सूचना (LEGAL DEMAND NOTICE)
धारा 138 एवं 142, परक्राम्य लिखत अधिनियम, 1881 (पंजीकृत डाक / स्पीड पोस्ट द्वारा)
========================================================================================================================

दिनांक: {{ current_date_formatted }}

सेवा में,
{{ drawer_name }}
{{ drawer_address }}

मेरे पक्षकार (शिकायतकर्ता) की ओर से एवं उनके निर्देशानुसार:
{{ payee_name }} (जिन्हें आगे "मेरे पक्षकार" कहा गया है)

महोदय/महोदया,

अपने उक्त पक्षकार के स्पष्ट निर्देशों के तहत, मैं आपको परक्राम्य लिखत अधिनियम, 1881 की धारा 138 के अधीन निम्नलिखित सांविधिक विधिक मांग सूचना प्रेषित करता हूँ:

1. यह कि आपके द्वारा मेरे पक्षकार के प्रति वैध रूप से प्रवर्तनीय ऋण एवं दायित्व के भुगतान हेतु चेक संख्या {{ cheque_no }} दिनांक {{ cheque_date_formatted }} राशि {{ formatted_currency }} ({{ amount_in_words }}) जारी किया गया था, जो बैंक {{ bank_name }} पर देय था।

2. यह कि मेरे पक्षकार द्वारा उक्त चेक को अपने बैंक के माध्यम से भुगतान हेतु प्रस्तुत करने पर, उक्त चेक आपके बैंक द्वारा रिटर्न मेमो दिनांक {{ dishonour_date_formatted }} के माध्यम से बिना भुगतान किए अनादरित (Dishonour) कर वापस लौटा दिया गया, जिसका कारण "{{ dishonour_reason }}" दर्शाया गया।

3. यह कि चेक अनादर की लिखित सूचना मेरे पक्षकार को सांविधिक 30 दिनों की निर्धारित अवधि के भीतर प्राप्त हुई है।

4. अतः इस सूचना के माध्यम से मैं आपको निर्देशित करता हूँ कि आप इस विधिक सूचना की प्राप्ति के 15 (पंद्रह) दिनों के भीतर उक्त राशि {{ formatted_currency }} का पूर्ण भुगतान मेरे पक्षकार को अनिवार्य रूप से कर दें। 

यदि आप उक्त 15 दिनों की अवधि में भुगतान करने में विफल रहते हैं, तो मेरे पक्षकार आपके विरुद्ध परक्राम्य लिखत अधिनियम, 1881 की धारा 138/142 एवं भारतीय न्याय संहिता / भा.दं.सं. के अधीन सक्षम न्यायालय में आपराधिक परिवाद (Criminal Complaint) दायर करने के लिए पूर्णतः स्वतंत्र होंगे, जिसकी संपूर्ण वैधानिक एवं आर्थिक जिम्मेदारी आपकी स्वयं की होगी।

भवदीय,

________________________________________
{{ advocate_name }}
अधिवक्ता, पक्षकार / शिकायतकर्ता

{% elif target_language == 'bilingual' %}
STATUTORY DEMAND NOTICE / सांविधिक विधिक मांग सूचना
SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881 / परक्राम्य लिखत अधिनियम धारा 138
========================================================================================================================

Date / दिनांक: {{ current_date_formatted }}

TO / प्रेषित:
{{ drawer_name }}
{{ drawer_address }}

UNDER INSTRUCTIONS FROM MY CLIENT / मेरे पक्षकार के निर्देशानुसार:
{{ payee_name }} ("My Client" / "मेरे पक्षकार")

1. CHEQUE DETAILS / चेक का विवरण:
   In discharge of your legally enforceable debt, you issued Cheque No. {{ cheque_no }} dated {{ cheque_date_formatted }} for ₹ {{ cheque_amount }}/- ({{ amount_in_words }}) drawn on {{ bank_name }}.
   (आपके द्वारा वैध ऋण के भुगतान हेतु चेक संख्या {{ cheque_no }} दिनांक {{ cheque_date_formatted }} राशि ₹ {{ cheque_amount }}/- जारी किया गया था।)

2. DISHONOUR / चेक का अनादर:
   The said instrument was dishonoured and returned unpaid vide Bank Memo dated {{ dishonour_date_formatted }} for reason: "{{ dishonour_reason }}".
   (उक्त चेक आपके बैंक द्वारा बैंक मेमो दिनांक {{ dishonour_date_formatted }} के द्वारा "{{ dishonour_reason }}" के कारण अनादरित कर वापस किया गया।)

3. 15-DAY STATUTORY DEMAND / 15-दिवसीय अनिवार्य मांग:
   I hereby call upon you to make the payment of ₹ {{ cheque_amount }}/- within FIFTEEN (15) DAYS from the receipt of this notice.
   (अतः इस सूचना प्राप्ति के 15 दिवस के भीतर उक्त संपूर्ण राशि का भुगतान अनिवार्य रूप से करें अन्यथा आपके विरुद्ध न्यायालय में आपराधिक परिवाद दायर किया जाएगा।)

Yours faithfully / भवदीय,

________________________________________
{{ advocate_name }}
Advocate for the Payee / अधिवक्ता

{% else %}
LEGAL DEMAND NOTICE UNDER SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881
(REGISTERED POST A.D. & SPEED POST)
========================================================================================================================

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
{% endif %}"""
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
                {"id": "target_language", "label": "Output Language", "type": "select", "required": False, "default": "en", "options": [{"label": "English (Standard Legal)", "value": "en"}, {"label": "हिंदी (Hindi - Devnagari)", "value": "hi"}, {"label": "द्विभाषी (Bilingual - English + Hindi)", "value": "bilingual"}]},
            ]
        },
        body_template="""{% if target_language == 'hi' %}
{{ company_name | upper }} के निदेशक मंडल की बैठक में पारित संकल्प की प्रमाणित प्रतिलिपि
बैठक की तिथि: {{ meeting_date_formatted }}

सीआईएन (CIN): {{ company_cin }}

विषय: {{ resolution_subject | upper }}
========================================================================================================================

"{{ resolution_body }}"

सत्यापित सत्य प्रतिलिपि,
कृते {{ company_name | upper }}


________________________________________
{{ signatory }}

{% elif target_language == 'bilingual' %}
CERTIFIED TRUE COPY OF BOARD RESOLUTION / निदेशक मंडल के संकल्प की प्रमाणित प्रतिलिपि
COMPANY / कंपनी: {{ company_name | upper }} | CIN: {{ company_cin }}
MEETING DATE / बैठक तिथि: {{ meeting_date_formatted }}

SUBJECT / विषय: {{ resolution_subject | upper }}
========================================================================================================================

"{{ resolution_body }}"

Certified True Copy / प्रमाणित सत्य प्रतिलिपि,
For / कृते {{ company_name | upper }}


________________________________________
{{ signatory }}

{% else %}
CERTIFIED TRUE COPY OF THE RESOLUTION PASSED AT THE BOARD MEETING OF {{ company_name | upper }} HELD ON {{ meeting_date_formatted }}.

CIN: {{ company_cin }}

SUBJECT: {{ resolution_subject | upper }}
========================================================================================================================

"{{ resolution_body }}"

Certified True Copy,
For {{ company_name | upper }}


________________________________________
{{ signatory }}
{% endif %}"""
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
                {"id": "target_language", "label": "Output Language", "type": "select", "required": False, "default": "en", "options": [{"label": "English (Standard Legal)", "value": "en"}, {"label": "हिंदी (Hindi - Devnagari)", "value": "hi"}, {"label": "द्विभाषी (Bilingual - English + Hindi)", "value": "bilingual"}]},
            ]
        },
        body_template="""{% if target_language == 'hi' %}
फॉर्म एमजीटी-14 (FORM MGT-14) हेतु अनुपालन एवं ज्ञापन पत्र
कंपनी अधिनियम, 2013 की धारा 117(1) के अनुसरण में
========================================================================================================================

सेवा में,
कंपनी रजिस्ट्रार (ROC),
{{ roc_jurisdiction | upper }}

संदर्भ: {{ company_name | upper }} (सीआईएन: {{ company_cin }})

विषय: फॉर्म एमजीटी-14 में संकल्पों एवं अनुबंधों का सांविधिक ई-फाइलिंग

1. सांविधिक समय-सीमा आवश्यकता:
   कंपनी अधिनियम, 2013 की धारा 117(1) के अनुसार, धारा 117(3) के अधीन पारित प्रत्येक संकल्प की प्रति इसके पारित होने के तीस (30) दिनों के भीतर रजिस्ट्रार के समक्ष अनिवार्य रूप से दाखिल की जानी चाहिए।

2. संकल्प का विवरण:
   - संकल्प पारित होने की तिथि: {{ resolution_date_formatted }}
   - सांविधिक उद्देश्य: {{ purpose }}
   - वैधानिक देय तिथि (30 दिन): {{ due_date_formatted }}

3. पेशेवर प्रमाणीकरण:
   अधोहस्ताक्षरी कार्यरत कंपनी सचिव (PCS) ने अभिलेखों, कार्यवृत्त एवं रजिस्टरों का परीक्षण किया है और प्रमाणित करता है कि उक्त संकल्प कंपनी अधिनियम, 2013 के प्रावधानों के अनुरूप है।

प्रमाणित कर्ता:
________________________________________
{{ professional_name }}
दिनांक: {{ current_date_formatted }}

{% elif target_language == 'bilingual' %}
MEMORANDUM & COMPLIANCE COVER NOTE FOR FORM MGT-14 / फॉर्म एमजीटी-14 अनुपालन पत्र
PURSUANT TO SECTION 117(1) COMPANIES ACT, 2013 / धारा 117(1) कंपनी अधिनियम के अंतर्गत
========================================================================================================================

TO / सेवा में:
THE REGISTRAR OF COMPANIES / कंपनी रजिस्ट्रार, {{ roc_jurisdiction | upper }}

IN RE / संदर्भ: {{ company_name | upper }} (CIN: {{ company_cin }})
SUBJECT / विषय: STATUTORY FILING OF FORM MGT-14 / एमजीटी-14 की सांविधिक फाइलिंग

1. RESOLUTION DETAILS / संकल्प का विवरण:
   - Date of Passing / पारित तिथि: {{ resolution_date_formatted }}
   - Purpose / उद्देश्य: {{ purpose }}
   - Due Date (30 Days) / अंतिम देय तिथि: {{ due_date_formatted }}

2. CERTIFICATION / प्रमाणीकरण:
   Certified that the resolution complies with the provisions of Companies Act, 2013.
   (प्रमाणित किया जाता है कि संकल्प कंपनी अधिनियम के प्रावधानों के अनुरूप है।)

Certified by / प्रमाणित कर्ता:
________________________________________
{{ professional_name }}
Date / दिनांक: {{ current_date_formatted }}

{% else %}
MEMORANDUM & COMPLIANCE COVER NOTE FOR FORM MGT-14
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
{% endif %}"""
    ),

    # ─── 8. Residential & Commercial Rent Agreement (Multilingual) ────────────
    "RENT_AGREEMENT_RESIDENTIAL_V1": TemplateManifest(
        template_id="RENT_AGREEMENT_RESIDENTIAL_V1",
        title="Residential & Commercial Rent / Lease Agreement",
        version="1.0.0",
        statutory_anchor="Transfer of Property Act, 1882 & State Rent Control Acts",
        category="AGREEMENT",
        description="Standard 11-month or fixed-term tenancy & lease agreement with automated clauses for rent, security deposit, lock-in period, maintenance, and bilingual English/Hindi execution.",
        controlling_precedent="Anthony v. K.C. Ittoop & Sons (2000) 6 SCC 394 (Registration mandates for lease periods exceeding 11 months)",
        schema_definition={
            "template_id": "RENT_AGREEMENT_RESIDENTIAL_V1",
            "statutory_anchor": "Transfer of Property Act, 1882",
            "fields": [
                {"id": "landlord_name", "label": "Landlord / Lessor Full Name", "type": "string", "required": True, "placeholder": "Ramesh Chandra Sharma"},
                {"id": "landlord_pan", "label": "Landlord PAN", "type": "string", "required": False, "validator": "pan", "placeholder": "ABCDE1234F"},
                {"id": "landlord_address", "label": "Landlord Permanent Address", "type": "text", "required": True, "placeholder": "B-12, Sector 14, Noida, UP - 201301"},
                {"id": "tenant_name", "label": "Tenant / Lessee Full Name", "type": "string", "required": True, "placeholder": "Priya Rajesh Verma"},
                {"id": "tenant_pan", "label": "Tenant PAN / Aadhaar", "type": "string", "required": False, "placeholder": "XYZPK5678Q"},
                {"id": "tenant_address", "label": "Tenant Permanent Address", "type": "text", "required": True, "placeholder": "Flat 304, Green Valley Apts, Indirapuram, Ghaziabad"},
                {"id": "premises_address", "label": "Leased / Rented Premises Address", "type": "text", "required": True, "placeholder": "Flat No. 402, 4th Floor, Lotus Towers, Andheri West, Mumbai - 400053"},
                {"id": "monthly_rent", "label": "Monthly Rent Amount (₹)", "type": "currency", "required": True, "placeholder": "35000"},
                {"id": "security_deposit", "label": "Interest-Free Refundable Security Deposit (₹)", "type": "currency", "required": True, "placeholder": "100000"},
                {"id": "commencement_date", "label": "Lease Commencement Date", "type": "date", "required": True},
                {"id": "tenure_months", "label": "Tenure Period (Months)", "type": "number", "required": True, "default": 11},
                {"id": "lock_in_months", "label": "Lock-In Period (Months)", "type": "number", "required": True, "default": 6},
                {"id": "notice_period_days", "label": "Termination Notice Period (Days)", "type": "number", "required": True, "default": 30},
                {"id": "maintenance_charges", "label": "Society / Maintenance Charges (₹/month)", "type": "currency", "required": False, "default": 0},
                {"id": "target_language", "label": "Output Language", "type": "select", "required": True, "default": "en", "options": [
                    {"label": "English (Standard Legal)", "value": "en"},
                    {"label": "हिंदी (Hindi Devnagari)", "value": "hi"},
                    {"label": "Bilingual (English + हिंदी)", "value": "bilingual"}
                ]}
            ]
        },
        body_template="""{% if target_language == 'hi' %}
किरायानामा / लीज अनुबंध (RENT AGREEMENT)
(हस्तांतरण संपत्ति अधिनियम, 1882 एवं संबंधित किराया नियंत्रण अधिनियम के तहत)
========================================================================================================================

यह किरायानामा आज दिनांक {{ commencement_date_formatted }} को निष्पादित किया गया:

प्रथम पक्ष (मकान मालिक / LESSOR):
श्री/श्रीमती {{ landlord_name }}
पैन: {{ landlord_pan | default('उपलब्ध नहीं') }}
स्थाई पता: {{ landlord_address }}
(जिन्हें आगे "मकान मालिक / प्रथम पक्ष" कहा जाएगा)

एवं

द्वितीय पक्ष (किरायेदार / LESSEE):
श्री/श्रीमती {{ tenant_name }}
पहचान/पैन: {{ tenant_pan | default('उपलब्ध नहीं') }}
स्थाई पता: {{ tenant_address }}
(जिन्हें आगे "किरायेदार / द्वितीय पक्ष" कहा जाएगा)

किराये पर दी गई संपत्ति का विवरण:
{{ premises_address }}

नियम एवं शर्तें (TERMS AND CONDITIONS):
1. अवधि (TENURE): यह अनुबंध {{ commencement_date_formatted }} से कुल {{ tenure_months }} माह की अवधि के लिए वैध रहेगा।
2. मासिक किराया (MONTHLY RENT): द्वितीय पक्ष प्रथम पक्ष को प्रत्येक अंग्रेजी माह की 7 तारीख तक ₹{{ monthly_rent }} प्रति माह की दर से किराया अदा करेगा।
3. सुरक्षा राशि (SECURITY DEPOSIT): द्वितीय पक्ष ने प्रथम पक्ष को ₹{{ security_deposit }} की ब्याज-मुक्त प्रतिभूति जमा राशि सौंपी है, जो परिसर खाली करते समय पूर्णतः वापसी योग्य होगी।
4. लॉक-इन अवधि (LOCK-IN PERIOD): दोनों पक्ष कम से कम {{ lock_in_months }} माह तक यह अनुबंध समाप्त नहीं करेंगे।
5. नोटिस अवधि (NOTICE PERIOD): लॉक-इन के पश्चात कोई भी पक्ष {{ notice_period_days }} दिनों का लिखित नोटिस देकर अनुबंध समाप्त कर सकता है।

साक्षीगण के समक्ष हस्ताक्षर:

प्रथम पक्ष (मकान मालिक): _______________________
{{ landlord_name }}

द्वितीय पक्ष (किरायेदार): _______________________
{{ tenant_name }}
{% elif target_language == 'bilingual' %}
RESIDENTIAL / COMMERCIAL LEASE & RENT AGREEMENT
किराया एवं लीज अनुबंध (BILINGUAL / द्विभाषी)
========================================================================================================================

THIS LEASE AND LICENSE AGREEMENT is executed on this {{ commencement_date_formatted }} at Mumbai / New Delhi:

BETWEEN / प्रथम पक्ष (LESSOR / LANDLORD):
{{ landlord_name }}, PAN: {{ landlord_pan | default('N/A') }}, Residing at: {{ landlord_address }}.
श्री/श्रीमती {{ landlord_name }}, पता: {{ landlord_address }}

AND / द्वितीय पक्ष (LESSEE / TENANT):
{{ tenant_name }}, ID/PAN: {{ tenant_pan | default('N/A') }}, Residing at: {{ tenant_address }}.
श्री/श्रीमती {{ tenant_name }}, पता: {{ tenant_address }}

SUBJECT PREMISES / किराये का परिसर:
All that premises situated at: {{ premises_address }}.
उक्त संपत्ति स्थित: {{ premises_address }}

OPERATIVE COVENANTS / प्रमुख शर्तें:
1. TENURE / अनुबंध अवधि: The tenure shall be for a fixed term of {{ tenure_months }} Months commencing from {{ commencement_date_formatted }}. (यह अनुबंध कुल {{ tenure_months }} माह की अवधि हेतु निष्पादित किया गया है।)
2. MONTHLY RENT / मासिक किराया: The Lessee shall pay to the Lessor a monthly rent of ₹ {{ monthly_rent }}/- per English calendar month. (मासिक किराया राशि ₹ {{ monthly_rent }}/- देय होगी।)
3. SECURITY DEPOSIT / धरोहर राशि: The Lessee has deposited an interest-free refundable security sum of ₹ {{ security_deposit }}/-. (ब्याज-मुक्त सुरक्षा जमा राशि ₹ {{ security_deposit }}/- जमा की गई है।)
4. LOCK-IN PERIOD / लॉक-इन अवधि: A mandatory lock-in period of {{ lock_in_months }} months shall bind both parties. (दोनों पक्षों हेतु {{ lock_in_months }} माह की लॉक-इन बाध्यकारी होगी।)
5. TERMINATION NOTICE / समाप्ति सूचना: Either party may terminate by giving {{ notice_period_days }} days written notice. ({{ notice_period_days }} दिवस का लिखित नोटिस अनिवार्य होगा।)

IN WITNESS WHEREOF the parties have set their hands / दोनों पक्षों के हस्ताक्षर:

LESSOR / मकान मालिक: __________________________
{{ landlord_name }}

LESSEE / किरायेदार: ___________________________
{{ tenant_name }}
{% else %}
RESIDENTIAL / COMMERCIAL LEASE AND RENT AGREEMENT
PURSUANT TO THE TRANSFER OF PROPERTY ACT, 1882
========================================================================================================================

THIS LEASE AGREEMENT is made and entered into on this {{ commencement_date_formatted }} by and between:

LESSOR / LANDLORD:
{{ landlord_name }}
PAN: {{ landlord_pan | default('Not Provided') }}
Permanent Address: {{ landlord_address }}
(hereinafter referred to as the "LESSOR", which expression shall include legal heirs, successors, and assigns) of the FIRST PART;

AND

LESSEE / TENANT:
{{ tenant_name }}
PAN / ID: {{ tenant_pan | default('Not Provided') }}
Permanent Address: {{ tenant_address }}
(hereinafter referred to as the "LESSEE", which expression shall include legal heirs, successors, and assigns) of the SECOND PART.

WHEREAS the Lessor is the absolute lawful owner of the residential/commercial premises situated at:
{{ premises_address }} (hereinafter referred to as the "SCHEDULED PREMISES").

NOW THIS AGREEMENT WITNESSETH AS FOLLOWS:
1. TERM & COMMENCEMENT:
   The tenancy shall be for a fixed period of {{ tenure_months }} MONTHS commencing from {{ commencement_date_formatted }}.

2. MONTHLY RENT & CHARGES:
   The Lessee agrees to pay the Lessor a monthly rent of ₹ {{ monthly_rent }}/- (Rupees {{ monthly_rent }} Only) payable on or before the 7th day of each calendar month.
   {% if maintenance_charges and maintenance_charges != 0 and maintenance_charges != '0' and 'Pending' not in maintenance_charges|string %}Society / Maintenance charges of ₹ {{ maintenance_charges }}/- per month shall be paid additionally.{% endif %}

3. REFUNDABLE SECURITY DEPOSIT:
   The Lessee has paid a sum of ₹ {{ security_deposit }}/- as interest-free refundable security deposit. The said deposit shall be refunded upon vacating the premises, subject to deductions for unpaid utilities or physical damages.

4. LOCK-IN PERIOD & TERMINATION:
   Both parties agree to a mandatory lock-in period of {{ lock_in_months }} MONTHS. Following expiry of the lock-in, either party may terminate this agreement by serving {{ notice_period_days }} DAYS written notice.

5. STATUTORY GOVERNANCE & REGISTRATION:
   In terms of the binding dictum in Anthony v. K.C. Ittoop & Sons (2000) 6 SCC 394, this instrument records the commercial covenants between the parties.

IN WITNESS WHEREOF, the parties hereto have signed and executed this Agreement:

LESSOR: ________________________________________
{{ landlord_name }}

LESSEE: ________________________________________
{{ tenant_name }}
{% endif %}
"""
    ),

    # ─── 9. Commercial Non-Disclosure Agreement (NDA) ────────────────────────
    "NDA_COMMERCIAL_V1": TemplateManifest(
        template_id="NDA_COMMERCIAL_V1",
        title="Commercial Non-Disclosure Agreement (NDA)",
        version="1.0.0",
        statutory_anchor="Section 27, Indian Contract Act, 1872",
        category="AGREEMENT",
        description="Bilateral/Unilateral Non-Disclosure Agreement safeguarding proprietary IP, technical algorithms, source code, financial models, and trade secrets with non-solicitation clauses.",
        controlling_precedent="Niranjan Shankar Golikari v. Century Spg. & Mfg. Co. Ltd. (1967) 2 SCR 378",
        schema_definition={
            "template_id": "NDA_COMMERCIAL_V1",
            "statutory_anchor": "Indian Contract Act, 1872",
            "fields": [
                {"id": "disclosing_party", "label": "Disclosing Party / Company", "type": "string", "required": True, "placeholder": "Acme Technologies Private Limited"},
                {"id": "disclosing_address", "label": "Disclosing Party Address", "type": "text", "required": True, "placeholder": "Cyber City, DLF Phase II, Gurugram, Haryana - 122002"},
                {"id": "receiving_party", "label": "Receiving Party / Counterparty", "type": "string", "required": True, "placeholder": "Apex Logistics Solutions LLP"},
                {"id": "receiving_address", "label": "Receiving Party Address", "type": "text", "required": True, "placeholder": "Nariman Point, Mumbai - 400021"},
                {"id": "purpose", "label": "Purpose of Disclosure", "type": "text", "required": True, "placeholder": "Evaluating a strategic joint-venture partnership and API data integration for legal technologies."},
                {"id": "duration_years", "label": "Confidentiality Duration (Years)", "type": "number", "required": True, "default": 2},
                {"id": "governing_city", "label": "Governing Court Jurisdiction", "type": "string", "required": True, "default": "New Delhi", "placeholder": "New Delhi / Mumbai / Bengaluru"},
                {"id": "effective_date", "label": "Effective Date", "type": "date", "required": True},
                {"id": "target_language", "label": "Output Language", "type": "select", "required": True, "default": "en", "options": [
                    {"label": "English (Standard Legal)", "value": "en"},
                    {"label": "हिंदी (Hindi Devnagari)", "value": "hi"},
                    {"label": "Bilingual (English + हिंदी)", "value": "bilingual"}
                ]}
            ]
        },
        body_template="""{% if target_language == 'hi' %}
गैर-प्रकटीकरण एवं गोपनीयता अनुबंध (NON-DISCLOSURE AGREEMENT)
(भारतीय अनुबंध अधिनियम, 1872 की धारा 27 के तहत)
========================================================================================================================

यह अनुबंध आज दिनांक {{ effective_date_formatted }} को निम्नलिखित पक्षों के मध्य निष्पादित किया गया:

1. {{ disclosing_party }}, जिसका पंजीकृत कार्यालय:
   {{ disclosing_address }}
   (जिन्हें आगे "प्रकटीकरण पक्ष / DISCLOSING PARTY" कहा गया है)

तथा

2. {{ receiving_party }}, जिसका मुख्य कार्यालय:
   {{ receiving_address }}
   (जिन्हें आगे "प्राप्तकर्ता पक्ष / RECEIVING PARTY" कहा गया है)

चूंकि दोनों पक्ष निम्नलिखित व्यावसायिक उद्देश्य हेतु गोपनीय सूचनाएं साझा करना चाहते हैं:
"{{ purpose }}"

अतः अब दोनों पक्ष निम्नलिखित शर्तों पर परस्पर सहमत होते हैं:

1. गोपनीय सूचना की परिभाषा:
   इसके अंतर्गत सभी तकनीकी डेटा, व्यापारिक रहस्य, प्रोप्राइटरी एल्गोरिदम, वित्तीय मॉडल, क्लाइंट डेटा और सॉफ्टवेयर सोर्स कोड सम्मिलित होंगे।

2. गोपनीयता बनाए रखने का दायित्व:
   प्राप्तकर्ता पक्ष यह वचन देता है कि वह सभी गोपनीय सूचनाओं को पूर्णतः सुरक्षित रखेगा तथा प्रकटीकरण पक्ष की पूर्व लिखित अनुमति के बिना किसी तीसरे पक्ष को प्रकट नहीं करेगा।

3. गोपनीयता की अवधि:
   गोपनीयता बनाए रखने की बाध्यता इस अनुबंध के प्रारंभ होने की तिथि से कुल {{ duration_years }} वर्ष की अवधि तक पूर्णतः प्रभावी रहेगी।

4. अधिकार क्षेत्र एवं शासी विधि:
   यह अनुबंध भारतीय विधियों के अधीन शासित होगा तथा किसी भी विवाद की स्थिति में केवल {{ governing_city }} स्थित सक्षम न्यायालयों का ही अनन्य क्षेत्राधिकार होगा।

हस्ताक्षर प्रकटीकरण पक्ष:
________________________________________
प्राधिकृत हस्ताक्षरकर्ता ({{ disclosing_party }})

हस्ताक्षर प्राप्तकर्ता पक्ष:
________________________________________
प्राधिकृत हस्ताक्षरकर्ता ({{ receiving_party }})

{% elif target_language == 'bilingual' %}
MUTUAL NON-DISCLOSURE AGREEMENT / पारस्परिक गोपनीयता अनुबंध
INDIAN CONTRACT ACT, 1872 / भारतीय अनुबंध अधिनियम, 1872
========================================================================================================================

Effective Date / प्रभावी तिथि: {{ effective_date_formatted }}

PARTIES / पक्षकार:
1. {{ disclosing_party }} (Disclosing Party / प्रकटीकरण पक्ष)
   Address: {{ disclosing_address }}
2. {{ receiving_party }} (Receiving Party / प्राप्तकर्ता पक्ष)
   Address: {{ receiving_address }}

PURPOSE / उद्देश्य:
"{{ purpose }}"

1. CONFIDENTIALITY / गोपनीयता:
   The Receiving Party agrees to maintain strict confidentiality of all proprietary IP, trade secrets, and source code.
   (प्राप्तकर्ता पक्ष सभी व्यापारिक रहस्यों एवं बौद्धिक संपदा की पूर्ण गोपनीयता बनाए रखने हेतु बाध्य है।)

2. TERM / अवधि:
   This covenant shall remain in force for a period of {{ duration_years }} Years.
   (यह गोपनीयता दायित्व कुल {{ duration_years }} वर्ष की अवधि तक प्रभावी रहेगा।)

3. JURISDICTION / क्षेत्राधिकार:
   Courts at {{ governing_city }} shall possess exclusive jurisdiction.
   ({{ governing_city }} स्थित सक्षम न्यायालयों का अनन्य अधिकार क्षेत्र होगा।)

Authorized Signatures / प्राधिकृत हस्ताक्षर:
______________________                      ______________________
{{ disclosing_party }}                      {{ receiving_party }}

{% else %}
MUTUAL NON-DISCLOSURE AND CONFIDENTIALITY AGREEMENT
PURSUANT TO THE INDIAN CONTRACT ACT, 1872
========================================================================================================================

THIS AGREEMENT is entered into on {{ effective_date_formatted }} BY AND BETWEEN:

1. {{ disclosing_party }}, having its registered office at:
   {{ disclosing_address }}
   (hereinafter referred to as the "DISCLOSING PARTY")

AND

2. {{ receiving_party }}, having its principal office at:
   {{ receiving_address }}
   (hereinafter referred to as the "RECEIVING PARTY")

WHEREAS the parties wish to explore a business opportunity concerning:
"{{ purpose }}" (the "PURPOSE").

NOW, THEREFORE, the parties agree as follows:
1. CONFIDENTIAL INFORMATION:
   "Confidential Information" includes all technical data, trade secrets, proprietary algorithms, financial models, client dossiers, and software source code disclosed by either party.

2. NON-DISCLOSURE OBLIGATION:
   The Receiving Party agrees to hold all Confidential Information in strict trust and confidence and shall not disclose it to third parties without prior written consent.

3. TERM OF PROTECTION:
   The obligations of confidentiality shall survive for a period of {{ duration_years }} ({{ duration_years | default(2) }}) YEARS from the Effective Date.

4. GOVERNING LAW & JURISDICTION:
   This Agreement shall be governed by the laws of India. The courts at {{ governing_city }} shall have exclusive jurisdiction over any disputes.

IN WITNESS WHEREOF, the authorized representatives have executed this Agreement:

For {{ disclosing_party | upper }}:
________________________________________
Authorized Signatory

For {{ receiving_party | upper }}:
________________________________________
Authorized Signatory
{% endif %}"""
    ),

    # ─── 10. Independent Consultant Agreement ─────────────────────────────────
    "CONSULTANT_AGREEMENT_V1": TemplateManifest(
        template_id="CONSULTANT_AGREEMENT_V1",
        title="Independent Consultant & Professional Services Agreement",
        version="1.0.0",
        statutory_anchor="Indian Contract Act, 1872 & Copyright Act, 1957",
        category="AGREEMENT",
        description="Comprehensive contractor agreement for freelance consultants, legal advisors, and software specialists with full intellectual property assignment.",
        schema_definition={
            "template_id": "CONSULTANT_AGREEMENT_V1",
            "statutory_anchor": "Indian Contract Act, 1872",
            "fields": [
                {"id": "client_name", "label": "Client / Hiring Organization", "type": "string", "required": True, "placeholder": "Nexus Enterprises Private Limited"},
                {"id": "consultant_name", "label": "Consultant / Specialist Name", "type": "string", "required": True, "placeholder": "Vikramaditya Sen"},
                {"id": "consultant_pan", "label": "Consultant PAN / GSTIN", "type": "string", "required": False, "placeholder": "ABCPS9912K"},
                {"id": "scope_of_work", "label": "Detailed Scope of Work", "type": "text", "required": True, "placeholder": "Architecture design, code review, and regulatory audit for fintech deployment."},
                {"id": "fee_amount", "label": "Professional Fee (₹)", "type": "currency", "required": True, "placeholder": "150000"},
                {"id": "payment_milestones", "label": "Payment Terms & Milestones", "type": "string", "required": True, "default": "50% advance upon signing, 50% upon milestone deliverables acceptance"},
                {"id": "effective_date", "label": "Commencement Date", "type": "date", "required": True},
                {"id": "notice_period_days", "label": "Termination Notice Period (Days)", "type": "number", "required": True, "default": 15},
                {"id": "target_language", "label": "Output Language", "type": "select", "required": True, "default": "en", "options": [
                    {"label": "English (Standard Legal)", "value": "en"},
                    {"label": "हिंदी (Hindi Devnagari)", "value": "hi"},
                    {"label": "Bilingual (English + हिंदी)", "value": "bilingual"}
                ]}
            ]
        },
        body_template="""{% if target_language == 'hi' %}
स्वतंत्र परामर्शदाता एवं व्यावसायिक सेवा अनुबंध (INDEPENDENT CONSULTANT AGREEMENT)
(भारतीय अनुबंध अधिनियम, 1872 एवं कॉपीराइट अधिनियम, 1957 की धारा 17 के तहत)
========================================================================================================================

यह अनुबंध आज दिनांक {{ effective_date_formatted }} को निम्नलिखित पक्षों के मध्य निष्पादित किया गया:

क्लाइंट / कंपनी:
{{ client_name }} (जिन्हें आगे "कंपनी / प्रथम पक्ष" कहा गया है)

तथा

स्वतंत्र परामर्शदाता:
{{ consultant_name }} (पैन: {{ consultant_pan | default('उपलब्ध नहीं') }}) (जिन्हें आगे "सलाहकार / द्वितीय पक्ष" कहा गया है)

1. सेवाओं का कार्यक्षेत्र (SCOPE OF SERVICES):
   सलाहकार कंपनी को निम्नलिखित व्यावसायिक एवं तकनीकी सेवाएं प्रदान करेगा:
   "{{ scope_of_work }}"

2. व्यावसायिक परामर्श शुल्क एवं भुगतान (FEES & REMUNERATION):
   कंपनी सलाहकार को कुल ₹ {{ fee_amount }}/- का परामर्श शुल्क आयकर अधिनियम, 1961 की धारा 194J के तहत लागू टीडीएस (TDS) कटौती के पश्चात अदा करेगी।
   भुगतान शर्तें: {{ payment_milestones }}।

3. बौद्धिक संपदा का हस्तांतरण (IP ASSIGNMENT):
   कॉपीराइट अधिनियम, 1957 की धारा 17 के अधीन, कार्य के दौरान तैयार की गई सभी रिपोर्ट, कोड, एल्गोरिदम और तकनीकी दस्तावेज कंपनी की अनन्य संपत्ति ("Work made for hire") माने जाएंगे।

4. अनुबंध समाप्ति (TERMINATION):
   कोई भी पक्ष {{ notice_period_days }} दिनों का लिखित नोटिस देकर इस अनुबंध को समाप्त कर सकता है।

हस्ताक्षर कंपनी:
________________________________________
प्राधिकृत हस्ताक्षरकर्ता ({{ client_name }})

हस्ताक्षर सलाहकार:
________________________________________
{{ consultant_name }}

{% elif target_language == 'bilingual' %}
INDEPENDENT CONSULTANT AGREEMENT / स्वतंत्र परामर्शदाता अनुबंध
INDIAN CONTRACT ACT, 1872 / भारतीय अनुबंध अधिनियम, 1872
========================================================================================================================

Commencement Date / प्रारंभ तिथि: {{ effective_date_formatted }}

PARTIES / पक्षकार:
1. {{ client_name }} (Company / प्रथम पक्ष)
2. {{ consultant_name }} (Consultant / द्वितीय पक्ष, PAN: {{ consultant_pan | default('N/A') }})

1. SERVICES / सेवाएं:
   "{{ scope_of_work }}"

2. PROFESSIONAL FEES / व्यावसायिक परामर्श शुल्क:
   Total Fee: ₹ {{ fee_amount }}/- subject to statutory TDS u/s 194J.
   (कुल परामर्श शुल्क राशि ₹ {{ fee_amount }}/- देय होगी।)
   Milestones / भुगतान शर्तें: {{ payment_milestones }}.

3. IP ASSIGNMENT / बौद्धिक संपदा:
   All deliverables vest solely with the Company pursuant to Section 17 of Copyright Act, 1957.
   (सभी कार्य एवं बौद्धिक संपदा कंपनी की अनन्य संपत्ति होगी।)

Signatures / हस्ताक्षर:
______________________                      ______________________
Company / कंपनी                             Consultant / सलाहकार

{% else %}
INDEPENDENT CONSULTANT & PROFESSIONAL SERVICES AGREEMENT
PURSUANT TO THE INDIAN CONTRACT ACT, 1872 & SECTION 17 OF THE COPYRIGHT ACT, 1957
========================================================================================================================

THIS AGREEMENT is entered into on {{ effective_date_formatted }} between:

CLIENT:
{{ client_name }} (hereinafter referred to as the "COMPANY")

AND

CONSULTANT:
{{ consultant_name }} (PAN: {{ consultant_pan | default('N/A') }}) (hereinafter referred to as the "CONSULTANT").

1. SCOPE OF SERVICES:
   The Consultant shall provide the following professional services:
   "{{ scope_of_work }}"

2. COMPENSATION & FEES:
   The Company agrees to pay the Consultant a professional fee of ₹ {{ fee_amount }}/- subject to statutory TDS deductions under Section 194J of the Income Tax Act, 1961.
   Payment schedule: {{ payment_milestones }}.

3. INTELLECTUAL PROPERTY ASSIGNMENT:
   Pursuant to Section 17 of the Copyright Act, 1957, all inventions, reports, algorithms, and documentation developed during the engagement shall vest solely with the Company as "work made for hire".

4. TERMINATION:
   Either party may terminate this agreement without cause by providing {{ notice_period_days }} days written notice.

EXECUTED BY:

For {{ client_name | upper }}:
________________________________________
Authorized Signatory

CONSULTANT:
________________________________________
{{ consultant_name }}
{% endif %}"""
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

