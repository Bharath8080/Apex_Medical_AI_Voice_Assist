import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748b"))

        if self._pageNumber > 1:
            self.drawString(0.6 * inch, 10.4 * inch, "Apex Care Hospital • Receptionist Knowledge Guide")
            self.drawRightString(7.9 * inch, 10.4 * inch, "Front Desk Reference Manual")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(0.6 * inch, 10.32 * inch, 7.9 * inch, 10.32 * inch)

        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(0.6 * inch, 0.65 * inch, 7.9 * inch, 0.65 * inch)
        self.drawString(0.6 * inch, 0.5 * inch, "Apex Care Hospital & Medical Center • Front Desk Receptionist Guide")
        self.drawRightString(7.9 * inch, 0.5 * inch, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def generate_comprehensive_pdf(output_path="data/guide.pdf"):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
    )

    styles = getSampleStyleSheet()

    c_primary   = colors.HexColor("#0f2b5c")
    c_secondary = colors.HexColor("#0284c7")
    c_text      = colors.HexColor("#1e293b")
    c_bg_light  = colors.HexColor("#f8fafc")
    c_border    = colors.HexColor("#cbd5e1")
    c_alert     = colors.HexColor("#991b1b")

    title_style = ParagraphStyle('MainTitle', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=c_primary, spaceAfter=3)

    subtitle_style = ParagraphStyle('MainSubtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10, leading=14, textColor=c_secondary, spaceAfter=10)

    h1_style = ParagraphStyle('SectionH1', parent=styles['Heading2'],
        fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=c_primary,
        spaceBefore=14, spaceAfter=6, keepWithNext=True)

    h2_style = ParagraphStyle('SectionH2', parent=styles['Heading3'],
        fontName='Helvetica-Bold', fontSize=9.5, leading=13, textColor=c_secondary,
        spaceBefore=8, spaceAfter=3, keepWithNext=True)

    body = ParagraphStyle('CustomBody', parent=styles['BodyText'],
        fontName='Helvetica', fontSize=8.5, leading=12.5, textColor=c_text, spaceAfter=5)

    bullet = ParagraphStyle('CustomBullet', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=12, textColor=c_text, leftIndent=12, spaceAfter=3)

    alert_box = ParagraphStyle('AlertBox', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8, leading=11.5, textColor=c_alert)

    story = []

    # COVER
    story.append(Paragraph("Apex Care Hospital & Medical Center", title_style))
    story.append(Paragraph("<b>Front Desk Receptionist Knowledge Guide</b>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=0, spaceAfter=8))

    # -------------------------------------------------------------------------
    # SECTION 1: FACILITY OVERVIEW & HOURS
    # -------------------------------------------------------------------------
    story.append(Paragraph("1. Facility Overview & Operating Hours", h1_style))

    story.append(Paragraph("• <b>Outpatient Clinic Hours:</b> Monday–Friday: 8:00 AM – 1:00 PM and 2:00 PM – 7:30 PM. Saturday: 8:00 AM – 2:00 PM.", bullet))
    story.append(Paragraph("• <b>Sunday & Public Holidays:</b> Elective outpatient clinics are closed. Emergency, Trauma, Urgent Care, and all Inpatient units operate 24/7, 365 days a year.", bullet))
    story.append(Paragraph("• <b>Telehealth Hours:</b> Monday–Sunday, 7:00 AM – 10:00 PM for follow-ups, minor ailment triage, and lab result reviews.", bullet))
    story.append(Paragraph("• <b>24/7 Pharmacy:</b> Located in the Main Lobby, Ground Floor. Offers bedside discharge delivery and courier delivery for chronic maintenance medications.", bullet))
    story.append(Spacer(1, 4))

    # -------------------------------------------------------------------------
    # SECTION 2: PATIENT REGISTRATION & INTAKE
    # -------------------------------------------------------------------------
    story.append(Paragraph("2. Patient Registration & Intake", h1_style))
    story.append(Paragraph("<b>2.1 Identity Verification:</b>", h2_style))
    story.append(Paragraph("All patients must be registered in the EHR before medical examination. A unique Patient ID (Format: <i>APEX-XXXXXXX</i>) is assigned on first registration.", body))
    story.append(Paragraph("• <b>Required Documents:</b> Government-issued photo ID (Driver's License, Passport, Military ID), primary and secondary insurance cards (front & back).", bullet))
    story.append(Paragraph("• <b>Pediatric Patients:</b> Must be accompanied by a parent or legal guardian with custody documentation.", bullet))
    story.append(Paragraph("• <b>International Patients:</b> Valid passport and travel insurance guarantee of payment letter required. International Patient Relations desk coordinates embassy support.", bullet))

    story.append(Paragraph("<b>2.2 Mandatory Intake Forms:</b>", h2_style))
    story.append(Paragraph("• <b>Form G-101</b> – General Consent for Medical Treatment.", bullet))
    story.append(Paragraph("• <b>Form H-202</b> – Medical History & Medication Reconciliation (chronic conditions, allergies, current medications).", bullet))
    story.append(Paragraph("• <b>Form P-303</b> – HIPAA Privacy Acknowledgment & Proxy Designation.", bullet))
    story.append(Paragraph("• <b>Form F-404</b> – Financial Responsibility & Assignment of Benefits (deductibles, co-pays).", bullet))
    story.append(Spacer(1, 4))

    # -------------------------------------------------------------------------
    # SECTION 3: APPOINTMENT SCHEDULING & REFERRALS
    # -------------------------------------------------------------------------
    story.append(Paragraph("3. Appointment Scheduling & Referral Policies", h1_style))
    story.append(Paragraph("• <b>Direct Booking (No Referral Needed):</b> General Medicine, Family Practice, Pediatrics, Dermatology, Obstetrics & Gynecology, Preventive Wellness Exams, General Dentistry.", bullet))
    story.append(Paragraph("• <b>Referral Required:</b> Cardiology, Neurology, Oncology, Rheumatology, Endocrinology, Nephrology, Pain Management. Patient must bring a written referral from a primary care provider.", bullet))
    story.append(Paragraph("• <b>Slot Durations:</b> New Patient Consultation = 30 min | Follow-up = 15 min | Procedural Consultation = 45 min.", bullet))
    story.append(Paragraph("• <b>Cancellation Policy:</b> Patients should cancel at least 24 hours in advance for routine appointments, or 2 hours for same-day urgent slots.", bullet))
    story.append(Paragraph("• <b>No-Show Policy:</b> 1st no-show: reminder sent, no penalty. 2nd consecutive: $25 admin fee. 3rd consecutive: booking restricted to Standby-Only mode with $50 deposit.", bullet))
    story.append(Paragraph("• <b>Provider Cancellation:</b> Affected patients are notified within 60 minutes and offered priority rescheduling within 48 hours.", bullet))
    story.append(Spacer(1, 4))

    # -------------------------------------------------------------------------
    # SECTION 4: PATIENT CHECK-IN & LATE ARRIVAL
    # -------------------------------------------------------------------------
    story.append(Paragraph("4. Patient Check-In & Late Arrival Policy", h1_style))
    story.append(Paragraph("• <b>Two-Identifier Verification:</b> Always confirm Full Legal Name AND Date of Birth (or registered mobile number) before marking patient as 'Arrived'. Never state the name aloud to prompt confirmation.", bullet))
    story.append(Paragraph("• <b>15-Minute Grace Period:</b> Patients arriving within 15 minutes of their appointment keep their slot.", bullet))
    story.append(Paragraph("• <b>15–30 Minutes Late:</b> Patient moved to Standby Queue, accommodated during provider's next available buffer slot.", bullet))
    story.append(Paragraph("• <b>Over 30 Minutes Late:</b> Appointment is rescheduled unless clinical urgency is identified by triage staff.", bullet))
    story.append(Spacer(1, 4))

    # -------------------------------------------------------------------------
    # SECTION 5: INSURANCE, BILLING & PAYMENTS
    # -------------------------------------------------------------------------
    story.append(Paragraph("5. Insurance Verification, Billing & Payment Policies", h1_style))
    story.append(Paragraph("<b>5.1 Accepted Insurance Plans:</b>", h2_style))
    story.append(Paragraph("Apex Care accepts: BlueCross BlueShield, Aetna, Cigna, UnitedHealthcare, Medicare Part B, New York Medicaid, and Humana.", body))
    story.append(Paragraph("• <b>Co-Pay:</b> Fixed dollar amount set by the insurer, collected at check-in.", bullet))
    story.append(Paragraph("• <b>Deductible:</b> Annual out-of-pocket amount before insurance cost-sharing begins.", bullet))
    story.append(Paragraph("• <b>Coinsurance:</b> Percentage of costs the patient pays after meeting their deductible.", bullet))
    story.append(Paragraph("• <b>TPA Cashless Pre-Authorization:</b> Planned inpatient surgeries require pre-auth at least 48 business hours prior. Emergency admissions: pre-auth initiated within 4 hours of bed assignment.", bullet))

    story.append(Paragraph("<b>5.2 Financial Hardship & Payment Options:</b>", h2_style))
    story.append(Paragraph("• <b>Zero-Interest Payment Plans:</b> Uninsured patients or self-pay balances over $500 qualify for 6–24 month installment plans under the Apex Community Health Assistance Program.", bullet))
    story.append(Paragraph("• <b>Good Faith Estimate (GFE):</b> Uninsured/self-pay patients have the legal right to a written GFE of expected charges before scheduled treatment (No Surprises Act).", bullet))
    story.append(Paragraph("• <b>Accepted Payment Methods:</b> Visa, MasterCard, Amex, Discover, Apple Pay, Google Pay, HSA/FSA Debit Cards, Cashier's Checks, and Cash.", bullet))
    story.append(Spacer(1, 4))

    # -------------------------------------------------------------------------
    # SECTION 6: DIAGNOSTIC TEST PREP (PATIENT INSTRUCTIONS)
    # -------------------------------------------------------------------------
    story.append(Paragraph("6. Diagnostic Test Preparation – Patient Instructions", h1_style))
    story.append(Paragraph("Receptionists provide the following preparation instructions when patients ask about upcoming tests:", body))

    prep_data = [
        [Paragraph("<b>Test / Procedure</b>", body), Paragraph("<b>Patient Preparation</b>", body), Paragraph("<b>Key Restrictions</b>", body)],
        [Paragraph("<b>Fasting Blood Glucose & Lipid Panel</b>", body), Paragraph("Water-only fast for 10–12 hours before the blood draw.", body), Paragraph("No coffee, tea, juice, gum, or tobacco. Morning BP medication allowed with a sip of water.", body)],
        [Paragraph("<b>Abdominal Ultrasound</b>", body), Paragraph("Fast 6–8 hours prior. Avoid fatty foods the night before.", body), Paragraph("Small sips of water allowed. No carbonated drinks.", body)],
        [Paragraph("<b>Pelvic / Obstetric Ultrasound</b>", body), Paragraph("Drink 1.0–1.2 liters of water 1 hour before appointment.", body), Paragraph("Do NOT empty bladder before the scan.", body)],
        [Paragraph("<b>MRI Scan</b>", body), Paragraph("Wear loose, metal-free clothing. No fasting needed (unless abdominal MRI).", body), Paragraph("Inform staff of pacemakers, metal implants, or cochlear devices.", body)],
        [Paragraph("<b>Mammography</b>", body), Paragraph("Best scheduled 7–10 days after menstrual cycle onset.", body), Paragraph("No deodorant, powder, or lotion on underarms/chest on exam day.", body)],
        [Paragraph("<b>CT Scan (with IV Contrast)</b>", body), Paragraph("Fast 4 hours prior. Creatinine test required (within 30 days).", body), Paragraph("Metformin must be withheld 48 hours post-contrast if prescribed.", body)],
        [Paragraph("<b>Upper Endoscopy / Colonoscopy</b>", body), Paragraph("Endoscopy: 8h fast. Colonoscopy: clear liquids 24h + full bowel prep.", body), Paragraph("Must be accompanied by a responsible adult driver home.", body)],
    ]
    t_prep = Table(prep_data, colWidths=[2.2 * inch, 2.7 * inch, 2.3 * inch])
    t_prep.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_bg_light),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('PADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(t_prep)
    story.append(Spacer(1, 4))

    # -------------------------------------------------------------------------
    # SECTION 7: MEDICAL RECORDS & REPORT TURNAROUND
    # -------------------------------------------------------------------------
    story.append(Paragraph("7. Medical Records & Report Turnaround Times", h1_style))
    story.append(Paragraph("• <b>Routine Blood Tests (CBC, CMP, Lipids, Urinalysis):</b> Same-day results by 5:00 PM if collected before 11:30 AM.", bullet))
    story.append(Paragraph("• <b>Hormone & Thyroid Panels:</b> 24–36 hours.", bullet))
    story.append(Paragraph("• <b>X-Ray & Routine Ultrasound:</b> Radiologist report within 24 business hours.", bullet))
    story.append(Paragraph("• <b>MRI, CT & Nuclear Scans:</b> Report within 48–72 hours.", bullet))
    story.append(Paragraph("• <b>Digital Portal:</b> All reports and clinical notes auto-uploaded to <i>apexcare.health/portal</i>.", bullet))
    story.append(Paragraph("• <b>Releasing Records:</b> Requires signed Form R-10 (HIPAA Authorization). Standard processing: 3–5 business days. Urgent hospital transfers: within 4 hours.", bullet))
    story.append(Spacer(1, 4))

    # -------------------------------------------------------------------------
    # SECTION 8: INPATIENT ADMISSIONS, VISITING HOURS & DISCHARGE
    # -------------------------------------------------------------------------
    story.append(Paragraph("8. Inpatient Admissions, Visiting Hours & Discharge", h1_style))
    story.append(Paragraph("<b>8.1 Admission Process:</b>", h2_style))
    story.append(Paragraph("• <b>Elective Admissions:</b> Patient reports to Inpatient Admission Desk with physician's admission order, photo ID, and insurance pre-authorization approval.", bullet))
    story.append(Paragraph("• <b>Self-Pay Deposits:</b> General Ward: $1,000 | Private Room: $2,500 | ICU: $5,000 — collected at admission, reconciled at discharge.", bullet))

    story.append(Paragraph("<b>8.2 Visiting Hours:</b>", h2_style))
    story.append(Paragraph("• <b>General Wards:</b> 10:00 AM – 1:00 PM and 4:00 PM – 8:00 PM. Max 2 visitors at a time.", bullet))
    story.append(Paragraph("• <b>ICU / CCU / NICU:</b> 11:00 AM – 12:00 PM and 5:00 PM – 6:00 PM. Max 1 immediate adult family member. Hand hygiene, gown, and mask required.", bullet))
    story.append(Paragraph("• <b>NICU & Pediatric Units:</b> Parents and legal guardians have 24/7 access with Guardian Security Pass.", bullet))
    story.append(Paragraph("• <b>Maternity / Labor & Delivery:</b> One birth partner 24/7; general family visitors 2:00 PM – 7:00 PM.", bullet))
    story.append(Paragraph("• <b>Children Under 12:</b> Not permitted in inpatient units or ICUs.", bullet))
    story.append(Paragraph("• <b>Discharge Checkout:</b> Standard checkout by 12:00 Noon. Discharges after 2:00 PM incur a half-day room charge.", bullet))
    story.append(Spacer(1, 4))

    # -------------------------------------------------------------------------
    # SECTION 9: HIPAA PRIVACY & FRONT DESK CONDUCT
    # -------------------------------------------------------------------------
    story.append(Paragraph("9. HIPAA Privacy & Front Desk Conduct", h1_style))
    story.append(Paragraph("• <b>Quiet Voice:</b> Never announce a patient's diagnosis, specialty, room number, or test aloud in the waiting area.", bullet))
    story.append(Paragraph("• <b>Sign-In Sheets:</b> Record only name, arrival time, and provider. Never write medical reason for visit or symptoms.", bullet))
    story.append(Paragraph("• <b>Screen Security:</b> Monitors facing public areas must use privacy filters. Workstations auto-lock after 60 seconds of inactivity.", bullet))
    story.append(Paragraph("• <b>Phone Messages:</b> Leave only hospital name, receptionist name, and callback number. Never mention diagnoses, test names, or specialist types on voicemail.", bullet))
    story.append(Paragraph("• <b>Privacy Breach:</b> Any suspected PHI disclosure must be reported to the Hospital Privacy Officer within 1 hour.", bullet))
    story.append(Spacer(1, 4))

    # -------------------------------------------------------------------------
    # SECTION 10: PATIENT RIGHTS & ACCESSIBILITY
    # -------------------------------------------------------------------------
    story.append(Paragraph("10. Patient Rights & Accessibility Services", h1_style))
    story.append(Paragraph("• <b>Right to Informed Consent:</b> Patients receive full explanation of procedures, risks, and alternatives in plain language before agreeing to any treatment.", bullet))
    story.append(Paragraph("• <b>Right to Refuse:</b> Patients may decline any test or procedure after understanding clinical consequences.", bullet))
    story.append(Paragraph("• <b>Grievance Filing:</b> Patients may submit complaints to the Patient Ombudsman at <i>advocacy@apexcare.health</i>. Written response within 7 business days.", bullet))
    story.append(Paragraph("• <b>Language Interpretation:</b> Free 24/7 medical interpretation in 40+ languages (Spanish, Mandarin, Arabic, Hindi, French, etc.) via video/phone terminals.", bullet))
    story.append(Paragraph("• <b>ASL & Braille:</b> Certified ASL video interpreters available 24/7. Braille signage and large-print forms on request.", bullet))
    story.append(Paragraph("• <b>Service Animals:</b> Certified service dogs permitted in all public and outpatient areas (ADA Title III).", bullet))
    story.append(Spacer(1, 4))

    # -------------------------------------------------------------------------
    # SECTION 11: EMERGENCY ESCALATION (RECEPTIONIST SCOPE ONLY)
    # -------------------------------------------------------------------------
    story.append(Paragraph("11. Emergency Escalation & Scope of Practice", h1_style))
    story.append(Paragraph("<b>IMPORTANT – Non-Clinical Boundary:</b> Receptionists and AI voice agents must never diagnose illnesses, interpret lab values, assess whether symptoms are dangerous, adjust medications, or recommend home remedies.", alert_box))
    story.append(Spacer(1, 4))
    story.append(Paragraph("If a caller or patient describes any of the following, immediately direct them to Emergency (Ext 911 / 999) or advise calling 911:", body))
    story.append(Paragraph("• Chest pain, pressure, or tightness radiating to jaw, neck, or arm.", bullet))
    story.append(Paragraph("• Stroke symptoms: Face drooping, Arm weakness, Speech difficulty (FAST).", bullet))
    story.append(Paragraph("• Severe sudden shortness of breath or blue lips/fingers.", bullet))
    story.append(Paragraph("• Worst headache of their life, or sudden vision loss.", bullet))
    story.append(Paragraph("• Suspected poisoning or drug overdose.", bullet))
    story.append(Paragraph("• Active suicidal ideation or violent behavior.", bullet))

    story.append(Paragraph("<b>Administrative Escalations:</b>", h2_style))
    story.append(Paragraph("• Billing disputes → Senior Patient Billing Advocate.", bullet))
    story.append(Paragraph("• Aggressive or abusive visitors → Hospital Security Control Room.", bullet))
    story.append(Paragraph("• Clinical complaints / malpractice concerns → Patient Relations Ombudsman.", bullet))
    story.append(Paragraph("• Media inquiries / VIP patients → Public Relations & Hospital Administration.", bullet))
    story.append(Spacer(1, 4))

    # -------------------------------------------------------------------------
    # SECTION 12: DE-ESCALATION & COMMUNICATION
    # -------------------------------------------------------------------------
    story.append(Paragraph("12. Patient Communication & De-Escalation (LAST Model)", h1_style))
    story.append(Paragraph("Apply the <b>LAST</b> framework during difficult patient interactions:", body))
    story.append(Paragraph("1. <b>L – Listen:</b> Let the patient explain fully without interruption.", bullet))
    story.append(Paragraph("2. <b>A – Apologize:</b> Acknowledge empathetically: <i>'I understand how stressful this must be — let me help you right away.'</i>", bullet))
    story.append(Paragraph("3. <b>S – Solve:</b> Provide concrete help: <i>'Let me check your queue status with clinical staff immediately.'</i>", bullet))
    story.append(Paragraph("4. <b>T – Thank:</b> Close with courtesy: <i>'Thank you for your patience while we ensure everyone receives safe, thorough care.'</i>", bullet))
    story.append(Spacer(1, 4))

    # -------------------------------------------------------------------------
    # SECTION 13: FACILITY AMENITIES & CAMPUS INFO
    # -------------------------------------------------------------------------
    story.append(Paragraph("13. Facility Amenities & Campus Information", h1_style))
    story.append(Paragraph("• <b>Smoke-Free Campus:</b> Tobacco, e-cigarettes, and cannabis are strictly prohibited in all indoor and outdoor hospital areas.", bullet))
    story.append(Paragraph("• <b>Parking:</b> Multi-level garage at $3.00/hour. Free validation at registration for appointments over 1 hour, chemotherapy, dialysis, or day surgeries.", bullet))
    story.append(Paragraph("• <b>Valet Parking:</b> Available at Main Entrance, Monday–Friday 6:30 AM – 8:00 PM.", bullet))
    story.append(Paragraph("• <b>Wheelchair Assistance:</b> Complimentary wheelchairs and escort available at all entrance drop-off zones.", bullet))
    story.append(Paragraph("• <b>Prayer & Quiet Room:</b> Multi-faith sanctuary on Ground Floor West Wing, open 24/7. Chaplain services on call.", bullet))
    story.append(Paragraph("• <b>Photography Ban:</b> Photography and recording prohibited in clinical areas, waiting lounges, and ICU corridors.", bullet))
    story.append(Spacer(1, 4))

    # -------------------------------------------------------------------------
    # SECTION 14: TELEHEALTH APPOINTMENTS
    # -------------------------------------------------------------------------
    story.append(Paragraph("14. Telehealth & Virtual Consultations", h1_style))
    story.append(Paragraph("• <b>Eligible for Telehealth:</b> Chronic disease follow-ups (stable Hypertension, Diabetes), lab result reviews, dermatology image evaluations, nutritional counseling, mild upper respiratory triage.", bullet))
    story.append(Paragraph("• <b>Must Be In-Person:</b> Acute chest pain, shortness of breath, severe abdominal pain, trauma, fractures, physical examination needs, or first-time controlled substance prescriptions.", bullet))
    story.append(Paragraph("• <b>Technical Requirements:</b> Encrypted video via ApexCare App. Government photo ID shown on screen during virtual check-in. Sessions cannot be recorded without bilateral written consent.", bullet))
    story.append(Spacer(1, 4))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    generate_comprehensive_pdf()
