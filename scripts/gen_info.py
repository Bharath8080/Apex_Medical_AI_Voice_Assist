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
    """Adds Page X of Y and running header/footer to every page."""
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
        
        # Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(0.6 * inch, 10.4 * inch, "Apex Care Hospital • Clinical Knowledge Base & Standard Operating Procedures")
            self.drawRightString(7.9 * inch, 10.4 * inch, "RAG Knowledge Manual")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(0.6 * inch, 10.32 * inch, 7.9 * inch, 10.32 * inch)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(0.6 * inch, 0.65 * inch, 7.9 * inch, 0.65 * inch)
        self.drawString(0.6 * inch, 0.5 * inch, "Apex Care Hospital & Medical Center • Standard Clinical Knowledge Base")
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
    
    c_primary = colors.HexColor("#0f2b5c")
    c_secondary = colors.HexColor("#0284c7")
    c_text = colors.HexColor("#1e293b")
    c_bg_light = colors.HexColor("#f8fafc")
    c_border = colors.HexColor("#cbd5e1")
    c_alert_text = colors.HexColor("#991b1b")

    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_primary,
        spaceAfter=3,
    )

    subtitle_style = ParagraphStyle(
        'MainSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=c_secondary,
        spaceAfter=10,
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=c_secondary,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True,
    )

    body = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=c_text,
        spaceAfter=5,
    )

    bullet = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=12,
        textColor=c_text,
        leftIndent=12,
        spaceAfter=3,
    )

    alert_box = ParagraphStyle(
        'AlertBoxText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11.5,
        textColor=c_alert_text,
    )

    story = []

    # DOCUMENT COVER HEADER
    story.append(Paragraph("Apex Care Hospital & Medical Center", title_style))
    story.append(Paragraph("<b>Hospital Policies & Clinical Knowledge Guide</b>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=0, spaceAfter=8))

    # SECTION 1: FACILITY OVERVIEW, MISSION & OPERATIONAL TIMINGS
    story.append(Paragraph("1. Facility Overview, Mission & Operational Policies", h1_style))
    story.append(Paragraph("<b>1.1 Organizational Structure & Purpose:</b>", h2_style))
    story.append(Paragraph("Apex Care Multi-Specialty Hospital operates as an integrated tertiary care health system dedicated to evidence-based medical treatment, patient safety, and compassionate clinical care across inpatient, outpatient, and emergency services.", body))
    story.append(Paragraph("• <b>Primary Campus Layout:</b> Main Medical Center (Inpatient Wards, Intensive Care Units, Surgical Theaters, 24/7 Emergency Level 1 Trauma Center, and Outpatient Specialty Pavilions).", bullet))
    story.append(Paragraph("• <b>Outpatient Clinical Shifts:</b> Monday to Friday: Morning Session (8:00 AM – 1:00 PM), Afternoon Session (2:00 PM – 7:30 PM). Saturday: Morning Clinic (8:00 AM – 2:00 PM).", bullet))
    story.append(Paragraph("• <b>Sunday & Public Holiday Coverage:</b> Regular elective outpatient clinics are closed. 24/7 Level 1 Trauma, Emergency Resuscitation, Urgent Care, and all Inpatient Care units operate without interruption 365 days a year.", bullet))
    story.append(Paragraph("• <b>Virtual Consultation & Telehealth Window:</b> Telehealth clinical support operates Monday through Sunday from 7:00 AM to 10:00 PM for follow-ups, minor ailment triage, and lab review.", bullet))
    story.append(Paragraph("• <b>Overhead Emergency Alerts:</b> Staff must recognize key hospital emergency signals: <i>Code Blue</i> (Cardiac/Respiratory Arrest), <i>Code Red</i> (Fire Event), <i>Code Pink</i> (Infant/Child Abduction), <i>Code Black</i> (Bomb/Threat), <i>Code Stroke</i> (Acute Neuro Assessment), <i>Code Silver</i> (Weapon/Hostage), <i>Code Orange</i> (Hazardous Chemical Spill), <i>Code Triage</i> (External Mass Casualty).", bullet))
    story.append(Spacer(1, 4))

    # SECTION 2: PATIENT REGISTRATION & INTAKE POLICIES
    story.append(Paragraph("2. Patient Registration, Documentation & Intake Policies", h1_style))
    story.append(Paragraph("<b>2.1 Identity Verification & Demographic Intake:</b>", h2_style))
    story.append(Paragraph("All patients presenting for care must be formally registered in the Electronic Health Record (EHR) system prior to medical examination. Registration establishes an encrypted, lifetime Unique Patient Identification (UID) number (Format: <i>APEX-XXXXXXX</i>).", body))
    story.append(Paragraph("1. <b>Mandatory Demographic Elements:</b> Full legal name, date of birth, biological sex, gender identity, preferred language, residential address, mobile phone, email address, emergency contact person, relationship, and legal guardian details (for pediatric patients).", bullet))
    story.append(Paragraph("2. <b>Required Identification Documents:</b>", bullet))
    story.append(Paragraph("   - Government-issued photo identification: State Driver's License, Real ID, US/Foreign Passport, Permanent Resident Card, or Military ID.", bullet))
    story.append(Paragraph("   - Primary and Secondary Health Insurance Cards (Front and Back digital capture).", bullet))
    story.append(Paragraph("   - Previous physician medical summaries, prior diagnostic discs (DICOM format), immunization records (for minors), or current medication lists.", bullet))
    story.append(Paragraph("3. <b>Pediatric & Minor Registration:</b> Patients under 18 years of age must be registered alongside a parent or court-appointed legal guardian with custody documentation on file.", bullet))
    story.append(Paragraph("4. <b>Unresponsive Emergency Patients (John/Jane Doe):</b> Trauma patients arriving unconscious without identification are assigned a temporary emergency UID (<i>EMER-YYYYMMDD-XXXX</i>) by ER Triage, reconciled once identity is legally verified.", bullet))
    story.append(Paragraph("5. <b>International & Tourist Patients:</b> Foreign travelers must present a valid passport and international travel insurance guarantee of payment letter. Multilingual staff and embassy coordination are facilitated via the International Patient Relations desk.", bullet))

    story.append(Paragraph("<b>2.2 Mandatory Intake Documentation Forms:</b>", h2_style))
    story.append(Paragraph("• <b>Form G-101 (General Consent for Medical Treatment):</b> Grants authorization for routine diagnostic examinations, nursing care, blood sampling, and emergency stabilization.", bullet))
    story.append(Paragraph("• <b>Form H-202 (Medical History & Medication Reconciliation):</b> Comprehensive disclosure of chronic illnesses (Diabetes, Hypertension, Asthma), prior surgeries, active prescription/OTC drugs, and food/drug allergies.", bullet))
    story.append(Paragraph("• <b>Form P-303 (HIPAA Privacy Acknowledgment & Proxy Designation):</b> Legal record specifying individuals authorized to receive medical or financial information.", bullet))
    story.append(Paragraph("• <b>Form F-404 (Financial Responsibility & Assignment of Benefits):</b> Establishes patient agreement for non-covered insurance balances, deductibles, and co-pays.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 3: APPOINTMENT REFERRALS & SPECIALIST ACCESS GUIDELINES
    story.append(Paragraph("3. Appointment Referral Rules & Specialist Access Policies", h1_style))
    story.append(Paragraph("<b>3.1 Referral Requirements by Clinical Specialty:</b>", h2_style))
    story.append(Paragraph("To ensure appropriate clinical utilization, outpatient departments enforce specific referral tiers:", body))
    story.append(Paragraph("• <b>Open Access Specialties (Direct Booking Permitted):</b> General Internal Medicine, Family Practice, General Pediatrics, Dermatology, Routine Obstetrics & Gynecology, Preventive Wellness Exams, and General Dentistry.", bullet))
    story.append(Paragraph("• <b>Referral-Mandatory Specialties:</b> Cardiology (Invasive/Interventional), Neurology & Neurosurgery, Medical/Surgical Oncology, Rheumatology, Endocrinology, Nephrology, and Pain Management. Patients must possess a written referral from a primary care provider detailing medical history and preliminary lab findings.", bullet))
    story.append(Paragraph("• <b>Second Opinion Policy:</b> Patients requesting second opinions for oncology or surgical recommendations must provide complete histology slides, operative notes, and radiological imaging at least 72 hours prior to scheduled consultation.", bullet))
    story.append(Paragraph("• <b>Clinical Slot Durations:</b> Standard New Patient Consultation = 30 minutes; Established Follow-up = 15 minutes; Procedural Consultations = 45 minutes.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 4: CHECK-IN, TRIAGE FLOW & WAITING LOUNGE RULES
    story.append(Paragraph("4. Patient Check-In, Clinical Triage Flow & Waiting Rules", h1_style))
    story.append(Paragraph("<b>4.1 Two-Identifier Check-In Verification:</b>", h2_style))
    story.append(Paragraph("Receptionists must always confirm at least two distinct patient identifiers (Full Legal Name and Date of Birth, or Registered Mobile Number) before changing patient status to 'Arrived' in the EHR. Never state the name aloud to prompt confirmation.", body))

    story.append(Paragraph("<b>4.2 Emergency Severity Index (ESI) Triage Classification:</b>", h2_style))
    story.append(Paragraph("Patients presenting with acute symptoms are evaluated by the Triage Registered Nurse using the standard 5-level ESI framework:", body))
    
    esi_data = [
        [Paragraph("<b>ESI Category</b>", body), Paragraph("<b>Clinical Description & Acuity</b>", body), Paragraph("<b>Target Response Time</b>", body)],
        [Paragraph("<b>Level 1: Resuscitation</b>", body), Paragraph("Immediate life threat: Cardiac/respiratory arrest, severe polytrauma, anaphylaxis.", body), Paragraph("Immediate (0 minutes)", body)],
        [Paragraph("<b>Level 2: Emergent</b>", body), Paragraph("High risk: Acute chest pain, stroke symptoms, severe pain (9/10), altered sensorium.", body), Paragraph("&lt; 10 minutes", body)],
        [Paragraph("<b>Level 3: Urgent</b>", body), Paragraph("Stable vitals requiring 2+ diagnostic resources (e.g., Acute abdominal pain, fracture).", body), Paragraph("&lt; 30 minutes", body)],
        [Paragraph("<b>Level 4: Less Urgent</b>", body), Paragraph("Requires 1 resource (e.g., Simple skin laceration needing sutures, uncomplicated UTI).", body), Paragraph("&lt; 60 minutes", body)],
        [Paragraph("<b>Level 5: Non-Urgent</b>", body), Paragraph("No diagnostic resources required (e.g., Medication refill request, minor rash).", body), Paragraph("&lt; 120 minutes", body)],
    ]
    t_esi = Table(esi_data, colWidths=[1.8 * inch, 3.4 * inch, 1.8 * inch])
    t_esi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_bg_light),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('PADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_esi)
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>4.3 Late Arrival Policy & Standby Queue:</b>", h2_style))
    story.append(Paragraph("• <b>15-Minute Grace Period:</b> Patients arriving within 15 minutes of scheduled time maintain their slot.", bullet))
    story.append(Paragraph("• <b>Arrivals 15–30 Minutes Late:</b> The patient is transitioned to the Standby Queue and accommodated during the provider's next available clinic buffer.", bullet))
    story.append(Paragraph("• <b>Arrivals Exceeding 30 Minutes:</b> Appointment is rescheduled to a future date unless the triage nurse identifies acute clinical urgency.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 5: INSURANCE VERIFICATION, TPA & FINANCIAL POLICIES
    story.append(Paragraph("5. Insurance Verification, TPA Cashless & Financial Policies", h1_style))
    story.append(Paragraph("<b>5.1 Payer Guidelines & Insurance Concepts:</b>", h2_style))
    story.append(Paragraph("• <b>In-Network Insurance Verification:</b> Apex Care accepts all major health plans including BlueCross BlueShield, Aetna, Cigna, UnitedHealthcare, Medicare Part B, New York Medicaid, and Humana.", bullet))
    story.append(Paragraph("• <b>Key Insurance Terminology:</b>", bullet))
    story.append(Paragraph("  - <i>Co-Payment (Co-Pay):</i> A fixed dollar amount determined by the insurer, due upon check-in at the front desk.", bullet))
    story.append(Paragraph("  - <i>Deductible:</i> The annual out-of-pocket expenditure required before insurance coverage cost-sharing begins.", bullet))
    story.append(Paragraph("  - <i>Coinsurance:</i> The percentage split of covered medical expenses paid by the patient after reaching their annual deductible.", bullet))
    story.append(Paragraph("• <b>TPA Cashless Pre-Authorization:</b> For planned inpatient surgeries, pre-authorization must be submitted at least 48 business hours prior. For emergency admissions, pre-authorization is initiated within 4 hours of bed assignment.", bullet))

    story.append(Paragraph("<b>5.2 Financial Hardship & Installment Payment Plans:</b>", h2_style))
    story.append(Paragraph("• <b>Zero-Interest Hardship Plans:</b> Uninsured patients or patients with self-pay balances exceeding $500 are eligible for the Apex Community Health Assistance Program, granting 6 to 24-month zero-interest payment installments.", bullet))
    story.append(Paragraph("• <b>No Surprises Act Compliance:</b> Uninsured or self-pay patients have the statutory right to receive a formal <b>Good Faith Estimate (GFE)</b> of total expected charges prior to scheduled treatment.", bullet))
    story.append(Paragraph("• <b>Accepted Payment Modes:</b> Visa, MasterCard, American Express, Discover, Apple Pay, Google Pay, HSA/FSA Debit Cards, Cashier's Checks, and Cash.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 6: DIAGNOSTIC TEST PREPARATION GUIDELINES
    story.append(Paragraph("6. Diagnostic Test Preparation Protocols & Patient Guidelines", h1_style))
    story.append(Paragraph("Staff and AI agents must provide accurate preparation instructions when explaining diagnostic orders:", body))
    
    prep_data = [
        [Paragraph("<b>Diagnostic Test / Procedure</b>", body), Paragraph("<b>Mandatory Patient Preparation Protocol</b>", body), Paragraph("<b>Clinical Precautions & Restrictions</b>", body)],
        [Paragraph("<b>Fasting Blood Glucose & Lipid Profile</b>", body), Paragraph("Strict water-only fasting for 10 to 12 hours prior to blood draw.", body), Paragraph("No coffee, tea, juice, gum, or tobacco. Morning blood pressure medication permitted with sips of water.", body)],
        [Paragraph("<b>Oral Glucose Tolerance Test (OGTT - 75g)</b>", body), Paragraph("8–10 hours fasting. Blood samples drawn at fasting, 1-hour, and 2-hour post glucose drink.", body), Paragraph("Patient must remain seated quietly in lab waiting area throughout 2-hour test. No walking or eating.", body)],
        [Paragraph("<b>Abdominal Ultrasound (Liver, Gallbladder, Pancreas)</b>", body), Paragraph("Fasting for 6 to 8 hours prior. Avoid fatty foods for dinner the preceding evening.", body), Paragraph("Water permitted in small sips. Carbonated beverages strictly prohibited to prevent acoustic bowel gas shadow.", body)],
        [Paragraph("<b>Pelvic, Obstetric & Renal Ultrasound</b>", body), Paragraph("Full bladder required: Drink 1.0 to 1.2 liters of plain water 1 hour prior to appointment.", body), Paragraph("Do NOT empty bladder before examination. Distended bladder acts as an acoustic window for pelvic imaging.", body)],
        [Paragraph("<b>Contrast-Enhanced CT Scan (IV Contrast)</b>", body), Paragraph("4 hours fasting prior. Serum Creatinine test (within 30 days) mandatory to verify kidney clearance.", body), Paragraph("Patients taking Metformin must withhold medication for 48 hours post-contrast under clinical supervision.", body)],
        [Paragraph("<b>Magnetic Resonance Imaging (MRI)</b>", body), Paragraph("Metal-free loose cotton clothing. No fasting required unless abdominal/pelvic MRI.", body), Paragraph("Strict Contraindications: Cardiac pacemakers, ferromagnetic aneurysm clips, cochlear implants, metal fragments in eye.", body)],
        [Paragraph("<b>Mammography (Breast Screening)</b>", body), Paragraph("Schedule exam 7–10 days after onset of menstrual cycle when breast tissue is least sensitive.", body), Paragraph("Do NOT apply deodorant, antiperspirant, body powder, perfume, or lotion to underarms or chest on exam day.", body)],
        [Paragraph("<b>Resting ECG & 24-Hour Holter Monitor</b>", body), Paragraph("Wear front-buttoning shirt. Avoid chest lotions or body oils on appointment day.", body), Paragraph("Maintain detailed activity and symptom diary. Keep monitor completely dry (no showering with device).", body)],
        [Paragraph("<b>Treadmill Stress Test (TMT / Exercise ECG)</b>", body), Paragraph("Light meal 2 hours prior. Wear supportive sports walking shoes and athletic clothing.", body), Paragraph("Hold Beta-Blockers or Digoxin for 24 hours prior only if specifically directed by attending cardiologist.", body)],
        [Paragraph("<b>Upper Endoscopy (EGD) & Colonoscopy</b>", body), Paragraph("Endoscopy: 8 hours fasting. Colonoscopy: Clear liquid diet 24h prior + complete prescribed bowel prep solution.", body), Paragraph("Mandatory: Must be accompanied by a responsible adult driver to escort patient home following sedation.", body)],
        [Paragraph("<b>Pulmonary Function Test (PFT / Spirometry)</b>", body), Paragraph("No heavy meals 2 hours prior. Avoid vigorous exercise for 1 hour before test.", body), Paragraph("Withhold short-acting bronchodilator inhalers (e.g., Albuterol) for 4 to 6 hours prior as instructed by physician.", body)],
    ]
    t_prep = Table(prep_data, colWidths=[2.2 * inch, 2.7 * inch, 2.3 * inch])
    t_prep.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_bg_light),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('PADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(t_prep)
    story.append(Spacer(1, 4))

    # SECTION 7: MEDICAL RECORDS & RELEASE OF INFORMATION (ROI)
    story.append(Paragraph("7. Medical Records Management & Release of Information (ROI)", h1_style))
    story.append(Paragraph("<b>7.1 Diagnostic Report Turnaround Standards:</b>", h2_style))
    story.append(Paragraph("• <b>Routine Hematology & Biochemistry (CBC, CMP, Lipid, Urinalysis):</b> Same-day delivery by 5:00 PM for specimens collected before 11:30 AM.", bullet))
    story.append(Paragraph("• <b>Specialized Hormone & Thyroid Panels:</b> Finalized within 24 to 36 hours.", bullet))
    story.append(Paragraph("• <b>Plain X-Ray & Routine Ultrasound:</b> Radiologist-verified report available within 24 business hours.", bullet))
    story.append(Paragraph("• <b>MRI, CT Scan & Nuclear Scans:</b> Diagnostic radiologist report available within 48 to 72 hours.", bullet))
    story.append(Paragraph("• <b>Surgical Histopathology & Biopsy:</b> 3 to 5 business days (Complex oncology immunohistochemistry: 7 business days).", bullet))
    story.append(Paragraph("• <b>Digital Patient Portal Delivery:</b> All finalized diagnostic reports and clinical notes are uploaded automatically to the secure patient web portal (<i>apexcare.health/portal</i>).", bullet))

    story.append(Paragraph("<b>7.2 Official Release of Information Protocol:</b>", h2_style))
    story.append(Paragraph("• <b>HIPAA Form R-10 Requirement:</b> Medical records cannot be released without a signed <b>Form R-10 (Authorization for Release of Protected Health Information)</b> detailing specific date ranges and recipient entities.", bullet))
    story.append(Paragraph("• <b>Standard Processing Window:</b> Routine requests are fulfilled within 3 to 5 business days. Urgent clinical transfers to another hospital are processed within 4 hours.", bullet))
    story.append(Paragraph("• <b>Deceased Patient Records:</b> May only be released to the court-appointed Executor of Estate upon presentation of certified Letters of Testamentary and State Death Certificate.", bullet))
    story.append(Paragraph("• <b>Correction & Amendment of Records:</b> Patients have the statutory right to request corrections to erroneous medical documentation by filing Form A-12 (Medical Record Amendment Request). The clinical privacy officer reviews and issues written determinations within 60 calendar days.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 8: PRESCRIPTION REFILLS & PHARMACY POLICIES
    story.append(Paragraph("8. Prescription Refills, Controlled Substances & Pharmacy Rules", h1_style))
    story.append(Paragraph("<b>8.1 Refill Authorization Guidelines:</b>", h2_style))
    story.append(Paragraph("• <b>48-Hour Advance Notice Requirement:</b> Patients must request medication refills at least 48 business hours prior to exhausting current supplies.", bullet))
    story.append(Paragraph("• <b>6-Month Clinical Review Rule:</b> For chronic maintenance therapies (antihypertensives, cholesterol medications, insulin), patients must have completed an in-person medical evaluation within the previous 6 months. If >6 months have elapsed, a 30-day bridge supply is authorized only alongside a confirmed clinic booking.", bullet))
    story.append(Paragraph("• <b>Schedule II-IV Controlled Substances (Opioids, Benzodiazepines, Stimulants):</b> Refills for controlled medications are legally prohibited via automated voice, phone, or portal messages. Controlled substances mandate an in-person physician evaluation and State Prescription Monitoring Program (PMP) review.", bullet))
    story.append(Paragraph("• <b>24/7 Outpatient Pharmacy:</b> Located in the Main Lobby, Ground Floor. Provides bedside discharge medication delivery and free local courier delivery for chronic maintenance orders.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 9: INPATIENT ADMISSIONS, VISITING HOURS & DISCHARGE
    story.append(Paragraph("9. Inpatient Admissions, Visiting Hours & Discharge Protocol", h1_style))
    story.append(Paragraph("<b>9.1 Admission Workflow & Inpatient Deposits:</b>", h2_style))
    story.append(Paragraph("• <b>Elective Admissions:</b> Patient reports to Inpatient Admission Desk with Attending Physician Admission Order, Photo ID, and Insurance Pre-authorization Approval.", bullet))
    story.append(Paragraph("• <b>Self-Pay Inpatient Deposit Policy:</b> General Ward: $1,000 deposit; Private Room: $2,500 deposit; Intensive Care Unit (ICU): $5,000 deposit required upon admission, reconciled upon discharge.", bullet))

    story.append(Paragraph("<b>9.2 Ward Visiting Hours & Guidelines:</b>", h2_style))
    story.append(Paragraph("• <b>General Inpatient Wards:</b> Daily visiting hours are: `10:00 AM – 1:00 PM` and `4:00 PM – 8:00 PM`. Maximum 2 visitors per patient at any one time.", bullet))
    story.append(Paragraph("• <b>Intensive Care Units (ICU / CCU / NICU):</b> Strictly: `11:00 AM – 12:00 PM` and `5:00 PM – 6:00 PM`. Maximum 1 immediate adult family member. Mandatory hand hygiene, sterile gowning, and mask required.", bullet))
    story.append(Paragraph("• <b>Neonatal ICU (NICU) & Pediatric Units:</b> Parents and legal guardians have 24/7 unrestricted visiting privileges with Guardian Security Pass.", bullet))
    story.append(Paragraph("• <b>Maternity / Labor & Delivery:</b> One designated birth partner permitted 24/7; general family visitors: 2:00 PM – 7:00 PM.", bullet))
    story.append(Paragraph("• <b>Child Visitor Restriction:</b> Children under 12 years of age are not permitted in inpatient units or ICUs to minimize cross-infection risk.", bullet))
    story.append(Paragraph("• <b>Discharge Checkout Time:</b> Standard inpatient checkout is 12:00 Noon. Discharges after 2:00 PM incur a half-day room charge.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 10: HIPAA PRIVACY & FRONT DESK OPERATIONAL SECURITY
    story.append(Paragraph("10. HIPAA Privacy Compliance & Front Desk Security Habits", h1_style))
    story.append(Paragraph("<b>10.1 Front Desk Operational Privacy Habits:</b>", h2_style))
    story.append(Paragraph("• <b>Controlled Voice Volume:</b> Receptionists must speak in quiet, measured tones. Never state a patient's diagnosis, medical specialty, treatment room, or lab test aloud across a waiting lobby.", bullet))
    story.append(Paragraph("• <b>Public Sign-In Sheet Protocol:</b> Sign-in sheets must only record Patient Legal Name, Time of Arrival, and Provider Name. The medical reason for visit, symptoms, or clinical complaint must NEVER appear on public sign-in sheets.", bullet))
    story.append(Paragraph("• <b>Workstation Screen Security:</b> Monitors facing public counters must be fitted with 3M polarized privacy filters. Workstations must auto-lock after 60 seconds of inactivity.", bullet))
    story.append(Paragraph("• <b>Paper Document Security:</b> Printed patient charts, labels, lab slips, and insurance cards must remain face down. Documents containing PHI must be deposited in locked blue shredder consoles (Bin Blue-H).", bullet))
    story.append(Paragraph("• <b>Telephone & Voicemail Guidelines:</b> When leaving phone messages, state only the hospital name, receptionist name, and callback number. Never mention test results, disease names, or doctor specialties on voicemail.", bullet))
    story.append(Paragraph("• <b>Breach Response Notification:</b> Any suspected unauthorized disclosure or loss of Protected Health Information (PHI) must be reported to the Hospital Privacy Officer within 1 hour of discovery.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 11: SCOPE OF PRACTICE & EMERGENCY CLINICAL ESCALATION
    story.append(Paragraph("11. Scope of Practice & Emergency Clinical Escalations", h1_style))
    story.append(Paragraph("<b>STRICT NON-CLINICAL BOUNDARY FOR RECEPTIONISTS & AI AGENTS:</b> Reception staff and AI voice bots are non-clinical entities. Under no circumstances may a receptionist or AI agent diagnose illnesses, interpret laboratory values, advise whether symptoms are dangerous, adjust drug dosages, or recommend home remedies.", alert_box))
    story.append(Spacer(1, 4))
    
    story.append(Paragraph("<b>11.1 Red-Flag Symptoms Requiring Immediate Emergency Transfer:</b>", h2_style))
    story.append(Paragraph("When a patient or caller presents with any of the following symptoms, immediately initiate Code Transfer to Emergency Trauma (Ext 911 / 999) or advise calling 911:", body))
    story.append(Paragraph("• Crushing chest pain, pressure, or tightness radiating to jaw, neck, or left arm.", bullet))
    story.append(Paragraph("• Acute stroke symptoms (FAST: Face drooping, Arm weakness, Slurred speech, Time to call emergency).", bullet))
    story.append(Paragraph("• Severe sudden shortness of breath, stridor, or cyanosis (blue lips/fingers).", bullet))
    story.append(Paragraph("• Sudden severe headache ('worst headache of life') or sudden visual loss.", bullet))
    story.append(Paragraph("• Suspected drug overdose, poisoning, or acute chemical ingestion.", bullet))
    story.append(Paragraph("• Severe physical trauma, compound fractures, or uncontrolled arterial bleeding.", bullet))
    story.append(Paragraph("• Acute psychiatric crisis, active suicidal ideation, or violent agitation.", bullet))

    story.append(Paragraph("<b>11.2 Administrative Escalation Hierarchy:</b>", h2_style))
    story.append(Paragraph("• Billing Discrepancies & Disputed Charges → Senior Patient Billing Advocate.", bullet))
    story.append(Paragraph("• Aggressive / Verbally Abusive Visitors → Hospital Security Control Room.", bullet))
    story.append(Paragraph("• Clinical Complaints & Malpractice Claims → Patient Relations Ombudsman & Legal Counsel.", bullet))
    story.append(Paragraph("• Media Inquiries & VIP Patients → Public Relations & Hospital Administration Office.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 12: PATIENT RIGHTS, ADVOCACY & ACCESSIBILITY
    story.append(Paragraph("12. Patient Rights, Advocacy, Grievances & Accessibility", h1_style))
    story.append(Paragraph("<b>12.1 Patient Rights & Transparency:</b>", h2_style))
    story.append(Paragraph("• <b>Right to Informed Consent:</b> Right to receive full explanations of diagnostic findings, treatment options, potential risks, and alternative therapies in plain language.", bullet))
    story.append(Paragraph("• <b>Right to Refuse Care:</b> Patients have the moral and legal right to decline any test, medication, or procedure after being informed of clinical consequences.", bullet))
    story.append(Paragraph("• <b>Good Faith Estimate (GFE) Rights:</b> Under the federal No Surprises Act, uninsured or self-pay patients have the legal right to receive a written Good Faith Estimate of expected total charges prior to scheduled care.", bullet))
    story.append(Paragraph("• <b>Formal Grievance Filing:</b> Patients may submit confidential written grievances to the Patient Ombudsman (Email: <i>advocacy@apexcare.health</i>). Formal investigation and written response provided within 7 business days.", bullet))

    story.append(Paragraph("<b>12.2 Language Interpretation & ADA Accessibility:</b>", h2_style))
    story.append(Paragraph("• <b>Language Interpretation Services:</b> Apex Care provides 24/7 free medical interpretation in over 40 languages (Spanish, Mandarin, Cantonese, Russian, Arabic, French, Bengali, Hindi, Korean, etc.) via dedicated video/phone interpretation terminals.", bullet))
    story.append(Paragraph("• <b>Hearing & Vision Impairments:</b> Certified American Sign Language (ASL) video interpreters available 24/7. Braille signage and large-print forms provided upon request.", bullet))
    story.append(Paragraph("• <b>Service Animals:</b> Certified service dogs assisting individuals with disabilities are permitted in all public and outpatient areas in compliance with ADA Title III.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 13: SOFT SKILLS & CONFLICT DE-ESCALATION STANDARDS
    story.append(Paragraph("13. Communication Soft Skills & De-Escalation Standards", h1_style))
    story.append(Paragraph("<b>13.1 The LAST Conflict De-Escalation Model:</b>", h2_style))
    story.append(Paragraph("Staff and communication systems apply the <b>LAST</b> framework during stressful patient interactions:", body))
    story.append(Paragraph("1. <b>L - Listen:</b> Allow the patient to explain their concerns or symptoms without interruption.", bullet))
    story.append(Paragraph("2. <b>A - Apologize:</b> Offer a sincere, empathetic acknowledgment: <i>'I understand how stressful waiting can be when you feel unwell; let me assist you right away.'</i>", bullet))
    story.append(Paragraph("3. <b>S - Solve:</b> Provide concrete, actionable assistance: <i>'Let me verify your queue status with clinical staff immediately or assist you with comfortable seating.'</i>", bullet))
    story.append(Paragraph("4. <b>T - Thank:</b> Conclude with courtesy: <i>'Thank you for your patience while we ensure every patient receives safe and thorough care.'</i>", bullet))
    story.append(Spacer(1, 4))

    # SECTION 14: NO-SHOW, CANCELLATION & RESCHEDULING POLICIES
    story.append(Paragraph("14. No-Show, Cancellation & Rescheduling Policies", h1_style))
    story.append(Paragraph("• <b>Cancellation Notice Requirements:</b> Patients are requested to cancel or reschedule appointments at least 24 hours in advance for routine clinics, and at least 2 hours prior for same-day urgent appointments.", bullet))
    story.append(Paragraph("• <b>Tiered No-Show Policy:</b>", bullet))
    story.append(Paragraph("  - <i>1st Unexcused No-Show:</i> Automated reminder sent via SMS and Email offering immediate self-rescheduling link. No financial penalty.", bullet))
    story.append(Paragraph("  - <i>2nd Consecutive No-Show:</i> $25 administrative no-show fee applied to account (non-billable to insurance).", bullet))
    story.append(Paragraph("  - <i>3rd Consecutive No-Show:</i> Patient booking privileges converted to Standby-Only mode. Future routine appointments require clinical supervisor approval and a $50 deposit credited toward co-pay.", bullet))
    story.append(Paragraph("• <b>Provider Cancellation Protocol:</b> If a physician is called into emergency surgery or unavailable, the clinic staff must notify affected patients within 60 minutes and offer priority rescheduling within 48 hours or transfer to a covering associate.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 15: INFECTION CONTROL, PPE & ISOLATION PROCEDURES
    story.append(Paragraph("15. Infection Control, PPE Protocols & Isolation Procedures", h1_style))
    story.append(Paragraph("<b>15.1 Front Desk Infection Screening Guidelines:</b>", h2_style))
    story.append(Paragraph("• <b>Respiratory Symptom Triage:</b> Any patient presenting with active fever (>100.4°F / 38.0°C), productive cough, or shortness of breath must be provided a surgical mask immediately at the entrance kiosk and directed to the Negative-Pressure Triage Bay.", bullet))
    story.append(Paragraph("• <b>Standard Hand Hygiene (5 Moments):</b> Before touching a patient, before clean/aseptic procedures, after body fluid exposure risk, after touching a patient, and after touching patient surroundings.", bullet))
    story.append(Paragraph("• <b>Inpatient Isolation Categories:</b>", bullet))
    story.append(Paragraph("  - <i>Contact Isolation (MRSA, C. difficile, VRE):</i> Yellow sign on door; mandatory gloves and gown prior to room entry.", bullet))
    story.append(Paragraph("  - <i>Droplet Isolation (Influenza, RSV, Pertussis):</i> Green sign on door; surgical mask and eye protection required within 6 feet.", bullet))
    story.append(Paragraph("  - <i>Airborne Isolation (Tuberculosis, Measles, Varicella):</i> Blue sign on door; negative-pressure isolation room and certified N95 respirator mask mandatory.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 16: PATIENT CONSENT POLICIES & DOCUMENTATION
    story.append(Paragraph("16. Patient Consent Policies & Documentation", h1_style))
    story.append(Paragraph("<b>Three Levels of Consent Recognized:</b>", h2_style))
    story.append(Paragraph("1. <b>Implied Consent:</b> Routine non-invasive checks (e.g., rolling up sleeve for blood pressure measurement or opening mouth for throat exam).", bullet))
    story.append(Paragraph("2. <b>Express / Written Consent:</b> Required for surgical procedures, biopsy, chemotherapy, moderate sedation, and contrast-enhanced imaging.", bullet))
    story.append(Paragraph("3. <b>Advance Directives & Proxy Consent:</b> Living Wills, Healthcare Proxy, and Medical Power of Attorney for patients unable to make clinical decisions independently.", bullet))
    story.append(Paragraph("<b>Storage:</b> All signed consent forms are digitally scanned into the EHR within 2 hours of signing.", body))
    story.append(Spacer(1, 4))

    # SECTION 17: IMMUNIZATION, VACCINATIONS & TRAVEL MEDICINE
    story.append(Paragraph("17. Clinical Immunization, Vaccinations & Travel Medicine", h1_style))
    story.append(Paragraph("<b>17.1 Routine Pediatric & Adult Vaccination Schedules:</b>", h2_style))
    story.append(Paragraph("Apex Care Immunization Clinic administers all CDC/WHO recommended vaccines:", body))
    
    vax_data = [
        [Paragraph("<b>Vaccine Category</b>", body), Paragraph("<b>Target Population & Schedule</b>", body), Paragraph("<b>Coverage & Self-Pay Policy</b>", body)],
        [Paragraph("<b>Infanrix / DTaP & Polio (IPV)</b>", body), Paragraph("Infants at 2, 4, 6, and 15–18 months; booster at 4–6 years.", body), Paragraph("Covered 100% (ACA Preventative) / $45 base", body)],
        [Paragraph("<b>MMR (Measles, Mumps, Rubella)</b>", body), Paragraph("Dose 1: 12–15 months; Dose 2: 4–6 years. Adult boosters available.", body), Paragraph("Covered 100% / $65 base", body)],
        [Paragraph("<b>Hepatitis B (Recombivax HB)</b>", body), Paragraph("3-dose series: Birth, 1–2 months, and 6–18 months.", body), Paragraph("Covered 100% / $50 per dose", body)],
        [Paragraph("<b>Annual Quadrivalent Influenza (Flu)</b>", body), Paragraph("All individuals 6 months and older. Administered Sept–March.", body), Paragraph("Covered 100% / $35 walk-in", body)],
        [Paragraph("<b>Shingrix (Shingles Vaccine)</b>", body), Paragraph("Adults 50 years and older (2 doses separated by 2–6 months).", body), Paragraph("Covered 100% for Medicare / $185 per dose", body)],
        [Paragraph("<b>Pneumococcal (Prevnar 20 / Pneumovax 23)</b>", body), Paragraph("Adults 65+ or adults 19–64 with chronic medical conditions.", body), Paragraph("Covered 100% / $160 base", body)],
        [Paragraph("<b>Travel Vaccines (Yellow Fever, Typhoid, Rabies)</b>", body), Paragraph("International travelers; appointment required 4–6 weeks prior.", body), Paragraph("Self-pay: Yellow Fever ($220), Typhoid ($95)", body)],
    ]
    t_vax = Table(vax_data, colWidths=[2.3 * inch, 2.7 * inch, 2.2 * inch])
    t_vax.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_bg_light),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('PADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(t_vax)
    story.append(Spacer(1, 4))

    # SECTION 18: SPECIALTY CLINICS, DAYCARE & REHABILITATION
    story.append(Paragraph("18. Specialty Clinics, Daycare Surgery & Rehabilitation Services", h1_style))
    story.append(Paragraph("<b>18.1 Daycare Surgery & Endoscopy Center:</b>", h2_style))
    story.append(Paragraph("• Covers outpatient procedures: Cataract surgery, laparoscopic cholecystectomy, arthroscopic joint repairs, hernia repairs, colonoscopies, and biopsies.", bullet))
    story.append(Paragraph("• <b>Discharge Criteria:</b> Patient must be fully conscious, stable vitals for 2 hours, able to tolerate oral liquids, void urine, and be accompanied by a responsible adult driver.", bullet))

    story.append(Paragraph("<b>18.2 Physical Therapy & Rehabilitation Pavilion:</b>", h2_style))
    story.append(Paragraph("• Services: Post-surgical orthopedic rehabilitation, stroke neuro-rehabilitation, cardiac rehab, sports injury therapy, and pediatric physical therapy.", bullet))
    story.append(Paragraph("• Session details: 45-minute customized physical therapy session (most major insurances provide coverage with physician prescription).", bullet))

    story.append(Paragraph("<b>18.3 Outpatient Hemodialysis Unit:</b>", h2_style))
    story.append(Paragraph("• Operates 3 daily shifts: Morning (6:30 AM), Afternoon (12:00 PM), Evening (5:30 PM). 24/7 acute emergency dialysis available in ICU.", bullet))
    story.append(Paragraph("• Pre-dialysis check: Weight verification, dry weight calculation, vascular access (AV Fistula / Graft) bruit and thrill check by Dialysis RN.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 19: FACILITY RULES, PARKING & CAMPUS AMENITIES
    story.append(Paragraph("19. Facility Rules, Parking Validation & Campus Amenities", h1_style))
    story.append(Paragraph("• <b>100% Smoke & Vaping Free Campus:</b> Tobacco, e-cigarettes, and cannabis are strictly banned across all indoor facilities, garages, and perimeter grounds.", bullet))
    story.append(Paragraph("• <b>Photography & Recording Ban:</b> Photography and audio/video recording are strictly prohibited in clinical areas, examination rooms, waiting lounges, and ICU corridors to safeguard patient privacy.", bullet))
    story.append(Paragraph("• <b>Parking Garage & Validation:</b> Automated multi-level garage ($3.00/hour). Free validation provided at registration for appointments exceeding 1 hour, chemotherapy, dialysis, or day surgeries.", bullet))
    story.append(Paragraph("• <b>Valet Parking Service:</b> Available at Main Entrance Monday to Friday 6:30 AM – 8:00 PM.", bullet))
    story.append(Paragraph("• <b>Spiritual Care & Quiet Rooms:</b> Multi-faith Prayer and Meditation Sanctuary located on Ground Floor West Wing (Open 24/7). Chaplain services available on call.", bullet))
    story.append(Paragraph("• <b>Wheelchair Assistance:</b> Complimentary wheelchairs and escort assistance available at all campus entrance drop-off zones.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 20: TELEHEALTH CLINICAL GUIDELINES & VIRTUAL CONSULTATIONS
    story.append(Paragraph("20. Telehealth Clinical Guidelines & Virtual Consultations", h1_style))
    story.append(Paragraph("<b>20.1 Telehealth Eligibility & Operational Scope:</b>", h2_style))
    story.append(Paragraph("• <b>Eligible Virtual Encounters:</b> Routine chronic disease follow-ups (Hypertension, stable Diabetes), lab and diagnostic test result reviews, dermatology image evaluations, nutritional counseling, and mild upper respiratory triage.", bullet))
    story.append(Paragraph("• <b>Conditions Ineligible for Telehealth (Mandatory In-Person):</b> Acute chest pain, shortness of breath, severe abdominal pain, acute trauma, suspected fractures, any condition requiring physical palpation or auscultation, and requests for initial controlled substance prescriptions.", bullet))
    story.append(Paragraph("• <b>Technical & Identity Requirements:</b> Patients must connect via an encrypted WebRTC video terminal (ApexCare App). Government photo ID must be displayed on screen during patient check-in. Virtual encounters may not be recorded without bilateral written consent.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 21: MEDICAL RECORD RETENTION & ARCHIVAL POLICIES
    story.append(Paragraph("21. Medical Record Retention, Archival & Destruction Laws", h1_style))
    story.append(Paragraph("<b>21.1 Legal Retention Thresholds:</b>", h2_style))
    story.append(Paragraph("• <b>Adult Medical Records:</b> Retained in active EHR storage for a minimum of 7 years from the date of last clinical encounter.", bullet))
    story.append(Paragraph("• <b>Pediatric & Minor Records:</b> Retained for 7 years past the minor's 21st birthday (or until age 28), whichever is longer, in compliance with state medical board statutes.", bullet))
    story.append(Paragraph("• <b>Diagnostic Mammography Records:</b> Maintained permanently (minimum 10 years if prior exams exist; permanently if no subsequent mammograms performed).", bullet))
    story.append(Paragraph("• <b>Certified Document Destruction:</b> Physical records reaching statutory expiration are shredded via NAID-certified cross-cut incineration with a permanent Certificate of Destruction logged in the compliance register.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 22: CLINICAL SAFETY INCIDENTS & PATIENT GRIEVANCE MEDIATION
    story.append(Paragraph("22. Clinical Safety Incidents & Ombudsman Mediation Protocol", h1_style))
    story.append(Paragraph("<b>22.1 Incident Reporting & Near-Miss Policy:</b>", h2_style))
    story.append(Paragraph("• Any adverse event, medication discrepancy, patient fall, or near-miss must be recorded in the confidential Safety Intelligence System (SIS) within 2 hours of occurrence.", bullet))
    story.append(Paragraph("• <b>Ombudsman Resolution Timeline:</b> Formal grievances submitted by patients or designated family representatives undergo multidisciplinary review with a written resolution issued within 7 business days.", bullet))
    story.append(Paragraph("• <b>External Appeal Rights:</b> Patients dissatisfied with internal resolutions maintain the statutory right to file appeals with the State Department of Health and The Joint Commission Office of Quality and Patient Safety.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 23: NEONATAL, MATERNITY & INFANT SECURITY PROTOCOLS
    story.append(Paragraph("23. Neonatal, Maternity & Infant Security Protocols", h1_style))
    story.append(Paragraph("<b>23.1 Infant Security & Electronic Tagging System:</b>", h2_style))
    story.append(Paragraph("• <b>Electronic Newborn Security:</b> All newborns receive tamper-resistant electronic radio-frequency security bracelets (Hugs & Kisses Tag) matched to mother and birth partner immediately post-delivery.", bullet))
    story.append(Paragraph("• <b>Maternity Unit Access:</b> The Labor, Delivery, and Postpartum Unit (Floor 4) operates as a locked unit. Access is permitted strictly through video intercom verification at Security Station M-4.", bullet))
    story.append(Paragraph("• <b>Code Pink Response:</b> In the event of an unauthorized infant transport attempt, all elevators and perimeter exits auto-lock within 5 seconds, and hospital-wide security containment is triggered.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 24: SPECIMEN COLLECTION & SPECIAL DIAGNOSTIC PROTOCOLS
    story.append(Paragraph("24. Special Diagnostic Specimen Collection Guidelines", h1_style))
    story.append(Paragraph("<b>24.1 Specialized Non-Blood Specimen Guidelines:</b>", h2_style))
    story.append(Paragraph("• <b>24-Hour Urine Collection:</b> Patient must discard the first morning void on Day 1, then collect all subsequent urine for exactly 24 hours into the specialized amber preservative container kept refrigerated or on ice. Return immediately to Counter 4 on Day 2.", bullet))
    story.append(Paragraph("• <b>Sputum Culture & AFB (Tuberculosis Screening):</b> Early morning deep cough specimen collected before eating or brushing teeth. Rinse mouth with water only (no mouthwash). Deliver to lab within 2 hours of collection.", bullet))
    story.append(Paragraph("• <b>Stool Occult Blood (FOBT / FIT Card):</b> Avoid red meat, melons, horseradish, and Vitamin C supplements for 3 days prior to sample collection to prevent false-positive results.", bullet))
    story.append(Paragraph("• <b>Semen Analysis / Fertility Testing:</b> Requires mandatory 2 to 7 days of sexual abstinence prior to collection. Sample must be delivered to the andrology lab within 45 minutes maintaining body temperature.", bullet))
    story.append(Spacer(1, 4))

    # SECTION 25: LABORATORY CRITICAL VALUES & BLOOD TRANSFUSION PROTOCOLS
    story.append(Paragraph("25. Critical Laboratory Alerts & Blood Transfusion Protocols", h1_style))
    story.append(Paragraph("<b>25.1 Critical Panic Value Escalation:</b>", h2_style))
    story.append(Paragraph("• <b>Immediate Verbal Notification (15-Minute Mandate):</b> Diagnostic laboratory staff must immediately telephone the attending physician or on-call hospitalist upon confirming critical panic lab values (e.g., Serum Potassium > 6.0 mEq/L or < 2.5 mEq/L, Blood Glucose < 45 mg/dL or > 500 mg/dL, Hemoglobin < 6.5 g/dL, or positive blood cultures).", bullet))
    story.append(Paragraph("• <b>Read-Back Verification:</b> The receiving nurse or clinician must verbally read back the complete patient legal name, UID, test name, and numerical result to ensure zero transcription errors.", bullet))
    story.append(Paragraph("• <b>Blood Transfusion & Crossmatch Validity:</b> Pre-transfusion Type and Screen crossmatch specimens are valid for a maximum of 72 hours. Blood product administration mandates informed written consent (Form B-204) and dual-nurse bedside barcode verification.", bullet))
    story.append(Spacer(1, 8))

    # Concluding Administrative Notice
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=6, spaceAfter=4))
    story.append(Paragraph("<font size='7.5' color='#64748b'><b>Document Control:</b> Apex Care Hospital SOP-KB-2026-v3.6 • Approved by Chief Medical Officer & Director of Administrative Operations • Official Static RAG Knowledge Base Document</font>", styles['Normal']))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated Clean RAG-Only Hospital Guide PDF at: {output_path}")

if __name__ == "__main__":
    generate_comprehensive_pdf()
