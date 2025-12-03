# Mortgage Underwriting Document Workflow Summary

## Overview
This document provides a comprehensive summary of all documents that agents access, verify, and process throughout the mortgage underwriting workflow.

---

## Document Processing Workflow

### Phase 0: Rate Shopping
**Documents Accessed:** None
**Agent Actions:** Brokers query lenders for rate quotes (no document processing)

---

### Phase 1: Loan Processing

#### 1.1 Document Verification (`loan_processor_1`)

**Tool:** `verify_loan_documents()`

**Core Required Documents Checked:**

| Document Type | Full Name | Requirements | Purpose |
|---------------|-----------|--------------|---------|
| **URLA** | Uniform Residential Loan Application (Form 1003) | Completed and signed | Primary loan application form with borrower information, income, assets, liabilities |
| **PAYSTUB** | Recent Pay Stubs | Last 2 months | Verify current income and employment |
| **W2** | W-2 Wage and Tax Statements | Last 2 years | Verify stable income history |
| **BANK_STATEMENT** | Bank Account Statements | Last 2 months | Verify assets for down payment and reserves |
| **PURCHASE_AGREEMENT** | Real Estate Purchase Contract | Fully executed | Property details, purchase price, terms |

**Document Statuses Tracked:**
- `REQUIRED` - Document needed but not submitted
- `REQUESTED` - Requested from borrower
- `RECEIVED` - Submitted but not reviewed
- `UNDER_REVIEW` - Currently being reviewed
- `APPROVED` - Verified and accepted ✅
- `REJECTED` - Not acceptable
- `MISSING` - Required but not provided
- `EXPIRED` - Out of date (e.g., paystub older than 30 days)

**Processing Logic:**
```
FOR each required document:
  IF document missing:
    → Add to loan file with status: REQUIRED
    → Flag as missing
  ELSE IF document status = APPROVED:
    → Mark as complete ✅
  ELSE IF document status = RECEIVED:
    → Flag as pending review ⚠️
  ELSE:
    → Flag as missing with current status

IF any missing/pending:
  → Update loan status: DOCUMENTS_COLLECTING
ELSE:
  → Update loan status: DOCUMENTS_COMPLETE ✅

SAVE loan file (Write #1 in Phase 1)
```

---

#### 1.2 Credit Report (`loan_processor_2`)

**Tool:** `order_credit_report()`

**Documents Generated:**

| Document | Content | Storage |
|----------|---------|---------|
| **Credit Report** | • Credit score (FICO)<br>• Payment history<br>• Credit inquiries<br>• Derogatory marks<br>• Credit utilization<br>• Public records<br>• Collections | Stored in `loan_file.credit_report` object |

**Tri-Bureau Credit Report Includes:**
- **Experian** score
- **TransUnion** score
- **Equifax** score
- **Representative Score:** Middle of three scores used for underwriting

**Data Points Captured:**
```python
CreditReport:
  - bureau_name: str
  - report_date: date
  - credit_score: int (300-850)
  - report_number: str
  - payment_history: str
  - derogatory_marks: int
  - inquiries_6mo: int
  - credit_utilization: float (%)
  - public_records: List[str]
  - tradelines: List[Tradeline]
```

**Processing:**
- Contacts credit bureau API (simulated)
- Handles timeouts with retry logic (max 2 retries)
- Updates `loan_file.borrowers[0].credit_score`
- Saves credit report to loan file (Write #2 in Phase 1)

---

#### 1.3 Property Appraisal (`loan_processor_3`)

**Tool:** `order_appraisal()`

**Documents Generated:**

| Document | Content | Purpose |
|----------|---------|---------|
| **Appraisal Report** | • Property valuation<br>• Comparable sales (comps)<br>• Property condition<br>• Required repairs<br>• Market analysis | Verify property value supports loan amount |

**Appraisal Report Structure:**
```python
Appraisal:
  - appraisal_id: str
  - appraiser_name: str
  - appraiser_license: str
  - order_date: date
  - inspection_date: date
  - completion_date: date
  - appraised_value: Decimal
  - property_condition: str (Excellent/Good/Fair/Poor)
  - comparable_sales: List[CompSale]
  - repairs_required: List[str]
  - subject_property_photos: List[str]
```

**Key Metrics Calculated:**
- **As-Is Value:** Current property value
- **Subject To Repairs Value:** Value after required repairs
- **LTV (Loan-to-Value):** `Loan Amount / Appraised Value × 100%`

**Processing:**
- Orders appraisal through AMC (Appraisal Management Company)
- Assigns licensed appraiser
- Schedules property inspection
- Receives completed appraisal report
- Saves to `loan_file.appraisal` (Write #3 in Phase 1)

---

#### 1.4 Flood Certification (`loan_processor_4`)

**Tool:** `order_flood_certification()`

**Documents Generated:**

| Document | Content | Purpose |
|----------|---------|---------|
| **Flood Certification** | • FEMA flood zone designation<br>• Flood insurance requirement<br>• Community participation status | Determine flood insurance requirements |

**Flood Certificate Data:**
```python
FloodCertification:
  - cert_id: str
  - property_address: Address
  - flood_zone: str (e.g., "Zone X", "Zone AE")
  - in_flood_zone: bool
  - flood_insurance_required: bool
  - community_name: str
  - community_number: str
  - map_number: str
  - determination_date: date
  - certificate_date: date
```

**FEMA Flood Zones:**
- **Zone X:** Minimal flood risk ❌ (no insurance required)
- **Zone A/AE:** High-risk flood area ⚠️ (insurance REQUIRED)
- **Zone V/VE:** High-risk coastal area 🌊 (insurance REQUIRED)

**Processing:**
- Queries FEMA flood maps database
- Determines flood zone for property address
- Checks if property is in Special Flood Hazard Area (SFHA)
- Creates flood certification document
- Adds to `loan_file.documents` with status APPROVED (Write #4 in Phase 1)

---

#### 1.5 Employment Verification (`loan_processor_5`)

**Tool:** `verify_employment()`

**Documents Generated:**

| Document | Content | Purpose |
|----------|---------|---------|
| **Verification of Employment (VOE)** | • Employer confirmation<br>• Job title<br>• Employment dates<br>• Current status<br>• Income verification<br>• Probability of continuation | Confirm stable employment and income |

**VOE Form Data:**
```python
EmploymentVerification:
  - employer_name: str
  - employer_contact: str
  - employee_name: str
  - position: str
  - hire_date: date
  - employment_status: str (Active/Terminated/Leave)
  - base_salary: Decimal
  - overtime_available: bool
  - probability_of_continued_employment: str
  - verification_date: date
  - verified_by: str
```

**Verification Methods:**
1. **Direct Contact:** Phone call to employer HR
2. **Third-Party Service:** The Work Number, Equifax
3. **Manual VOE Form:** Employer completes and returns form

**Processing:**
- Contacts employer or verification service
- Confirms employment dates, position, and income
- Updates `loan_file.borrowers[0].employment[0].verified = True`
- Adds VOE document to loan file (Write #5 in Phase 1)

---

#### 1.6 Financial Calculations (`loan_processor_6`)

**Tool:** `calculate_loan_ratios()`

**Documents Used (Input):**
- W-2 forms → Annual income
- Paystubs → Monthly income
- Bank statements → Assets and reserves
- Credit report → Monthly debt obligations
- Appraisal → Property value

**Metrics Calculated:**

| Metric | Formula | Guideline | Purpose |
|--------|---------|-----------|---------|
| **DTI** (Debt-to-Income) | `(Total Monthly Debts / Gross Monthly Income) × 100%` | ≤ 43% for conventional | Measure ability to repay |
| **LTV** (Loan-to-Value) | `(Loan Amount / Appraised Value) × 100%` | ≤ 80% for no PMI | Measure loan risk |
| **Housing Ratio** | `(PITI / Gross Monthly Income) × 100%` | ≤ 28% | Measure housing affordability |
| **Reserves** | `Liquid Assets / Monthly PITI Payment` | ≥ 2 months | Measure financial cushion |

**Financial Metrics Object:**
```python
FinancialMetrics:
  - dti_ratio: Decimal (e.g., 35.0 = 35%)
  - front_end_ratio: Decimal (housing ratio)
  - ltv_ratio: Decimal (e.g., 80.0 = 80%)
  - cltv_ratio: Decimal (combined LTV if 2nd mortgage)
  - reserves_months: Decimal (e.g., 6.0 = 6 months)
  - monthly_payment: Decimal
  - calculated_date: datetime
```

**PITI Breakdown:**
- **P** - Principal (loan payment)
- **I** - Interest
- **T** - Property Taxes
- **I** - Homeowners Insurance

**Processing:**
- Reads all financial data from loan file
- Calculates all ratios and metrics
- Updates `loan_file.financial_metrics`
- Submits to underwriting (changes status to `SUBMITTED_TO_UNDERWRITING`)
- Saves loan file (Write #6 in Phase 1)

---

### Phase 2: Underwriting Review

All underwriters ACCESS documents but don't generate new ones. They REVIEW and ADD FINDINGS to `loan_file.underwriting_reviews`.

#### 2.1 Credit Review (`underwriter_1`)

**Tool:** `review_credit_profile()`

**Documents Reviewed:**
- ✓ Credit Report (from Phase 1)
- ✓ Letter of Explanation (LOE) - if derogatory marks exist
- ✓ Bankruptcy Discharge - if applicable
- ✓ Credit Supplement - if needed

**Review Criteria:**
- Credit score ≥ 620 (conventional minimum)
- Payment history: Late payments in last 2 years?
- Credit utilization < 30%
- Derogatory marks: Collections, charge-offs, judgments?
- Recent inquiries: Too many in last 6 months?
- Public records: Bankruptcies, foreclosures, tax liens?

**Review Output:**
```python
UnderwritingReview:
  - review_type: "credit"
  - reviewer: "underwriter_1"
  - review_date: datetime
  - status: "acceptable" | "needs_conditions" | "unacceptable"
  - findings: List[str]
  - conditions_issued: List[UnderwritingCondition]
```

**Saves review to loan file (Write #7 in Phase 2)**

---

#### 2.2 Income Review (`underwriter_2`)

**Tool:** `review_income_employment()`

**Documents Reviewed:**
- ✓ W-2 Forms (2 years)
- ✓ Paystubs (2 months)
- ✓ Employment Verification (VOE)
- ✓ Tax Returns (if self-employed)
- ✓ 1099 Forms (if contractor/freelance)
- ✓ Profit & Loss Statement (if self-employed)

**Review Criteria:**
- Employment stability: Same job ≥ 2 years?
- Income stability: Consistent or increasing?
- Employment gaps: Unexplained gaps?
- Job tenure: Recent job changes?
- Income calculation: W-2 method vs. tax return method
- Overtime/bonus: 2-year history and likely to continue?

**Income Calculation Methods:**

**W-2 Employee:**
```
Monthly Income = (Base Salary + Avg Bonus + Avg Overtime) / 12
```

**Self-Employed:**
```
Monthly Income = (Tax Return Net Income + Add-Backs - Deductions) / 12
```

**Review Output:** Saves to `loan_file.underwriting_reviews` (Write #8 in Phase 2)

---

#### 2.3 Assets Review (`underwriter_3`)

**Tool:** `review_assets_reserves()`

**Documents Reviewed:**
- ✓ Bank Statements (2 months, all pages)
- ✓ Investment Account Statements
- ✓ 401(k)/IRA Statements
- ✓ Gift Letter (if down payment gift)
- ✓ Proof of Sale (if selling current home)
- ✓ Earnest Money Deposit Receipt

**Review Criteria:**
- **Source of Funds:** Down payment + closing costs verified?
- **Seasoned Funds:** In account ≥ 60 days?
- **Large Deposits:** Any unexplained deposits > $1,000?
- **Reserves:** Liquid assets after closing ≥ 2 months PITI?
- **Gift Funds:** Properly documented with donor letter?
- **Asset Verification:** Recent statements (< 60 days old)?

**Asset Categories:**

| Asset Type | Liquid? | % Available | Seasoning Required |
|------------|---------|-------------|-------------------|
| Checking/Savings | Yes | 100% | Yes (60 days) |
| Stocks/Bonds | Yes | 70% (vested) | Yes |
| 401(k)/IRA | No* | 60% (penalty) | Yes |
| Crypto | Maybe | 0% (typically) | Yes |
| Gift Funds | Yes | 100% | No (with letter) |

**Reserves Calculation:**
```
Liquid Assets After Closing:
  = (Checking + Savings + 70% × Stocks + 60% × Retirement)
  - Down Payment
  - Closing Costs

Reserves in Months = Liquid Assets / Monthly PITI
```

**Review Output:** Saves to `loan_file.underwriting_reviews` (Write #9 in Phase 2)

---

#### 2.4 Property Review (`underwriter_4`)

**Tool:** `review_property_appraisal()`

**Documents Reviewed:**
- ✓ Appraisal Report (full report)
- ✓ Purchase Agreement
- ✓ Title Report
- ✓ HOA Documents (if condo/townhome)
- ✓ Property Insurance Quote
- ✓ Property Photos

**Review Criteria:**
- **Value:** Appraised value ≥ purchase price?
- **Condition:** Property condition acceptable?
- **Repairs:** Required repairs exceed guidelines?
- **Comparables:** Comps appropriate and recent?
- **Property Type:** Meets lending guidelines?
- **Occupancy:** Primary residence vs investment?
- **Market Conditions:** Declining market?

**Appraisal Review Checkpoints:**

| Checkpoint | Acceptable | Requires Conditions |
|------------|------------|-------------------|
| Appraised Value | ≥ Purchase Price | < Purchase Price (buyer brings more down) |
| Property Condition | Good/Excellent | Fair (repairs < $5K) or Poor (> $5K repairs) |
| Repairs Required | None or < $500 | $500 - $5,000 (escrow) or > $5,000 (must complete) |
| Comparable Sales | 3+ comps, < 6 months old | 1-2 comps or > 6 months old |

**Condition Scenarios:**

**Scenario A: Low Appraisal**
```
Purchase Price: $400,000
Appraised Value: $380,000
LTV Calculation: Based on LOWER value ($380,000)

Required Action:
- Borrower brings additional $20,000 down payment, OR
- Renegotiate purchase price down to $380,000, OR
- Cancel transaction
```

**Scenario B: Required Repairs**
```
Appraised Value: $400,000 "as-is"
Repairs Required: $3,000 (roof, HVAC)

Options:
1. Seller completes repairs before closing
2. Escrow $3,000 × 1.5 = $4,500 at closing
3. Reduce purchase price by $3,000
```

**Review Output:** Saves to `loan_file.underwriting_reviews` (Write #10 in Phase 2)

---

#### 2.5 Automated Underwriting (`underwriter_5`)

**Tool:** `run_automated_underwriting()`

**System:** Desktop Underwriter (DU) or Loan Prospector (LP)

**Documents/Data Input to AUS:**
- ✓ Complete loan application (URLA)
- ✓ Credit report
- ✓ Income documentation
- ✓ Asset statements
- ✓ Appraisal data
- ✓ Property information
- ✓ Employment history

**AUS Analysis:**
```
Input: All loan file data
Process: Risk-based algorithmic assessment
Output: Automated findings and recommendation
```

**Automated Underwriting Decisions:**

| Decision | Meaning | Required Action |
|----------|---------|----------------|
| **Approve/Eligible** | Meets all automated guidelines | Manual review for accuracy |
| **Approve/Ineligible** | Approved but not eligible for sale to GSE | Portfolio or manual underwriting |
| **Refer/Caution** | Needs manual underwriting review | Full manual underwrite required |
| **Refer/Eligible** | Eligible but requires review | Manual review certain aspects |
| **Decline** | Does not meet automated criteria | Denial or find alternative program |

**Findings Generated:**
```python
AUS Findings:
  - Credit: "Approve" | "Review" | "Refer"
  - Income: "Approve" | "Review" | "Refer"
  - Assets: "Approve" | "Review" | "Refer"
  - Property: "Approve" | "Review" | "Refer"
  - Overall: "Approve/Eligible" | "Refer/Caution"
  - Required Documents: List[DocumentType]
  - Recommended Conditions: List[str]
```

**Processing:**
- Submits complete loan file to AUS
- Receives automated findings
- Updates `loan_file.au_decision`
- Adds review to `loan_file.underwriting_reviews` (Write #11 in Phase 2)

---

### Phase 3: Final Decision

#### 3.1 Decision Making (`decision_maker`)

**Tool:** `issue_final_approval()` OR `issue_underwriting_conditions()` OR `deny_loan()`

**Documents Reviewed:**
- ✓ ALL underwriting reviews (5 reviews from Phase 2)
- ✓ AUS decision
- ✓ Complete loan file

**Decision Matrix:**

| Credit | Income | Assets | Property | AUS | Decision |
|--------|--------|--------|----------|-----|----------|
| ✓ | ✓ | ✓ | ✓ | Approve | **Clear to Close** |
| ✓ | ✓ | ⚠️ | ✓ | Approve | **Approved w/ Conditions** |
| ✓ | ⚠️ | ⚠️ | ✓ | Refer | **Suspended (needs docs)** |
| ❌ | ✓ | ✓ | ✓ | Refer | **Denial** |
| ❌ | ❌ | ❌ | ⚠️ | Decline | **Denial** |

**Decision 1: Clear to Close**
```python
issue_final_approval(loan_number, approval_notes)

Updates:
  - loan_file.status = CLEAR_TO_CLOSE
  - loan_file.final_decision.approved = True
  - loan_file.final_decision.approved_amount = loan_amount
  - loan_file.final_decision.approved_rate = best_rate
  - loan_file.final_decision.conditions = [] (no conditions)
  - loan_file.final_decision.decision_date = today

Saves loan file (Write #12 - FINAL)
```

**Decision 2: Approved with Conditions**
```python
issue_underwriting_conditions(loan_number, conditions)

Sample Conditions:
  1. "Provide most recent paystub dated within 10 days of closing"
  2. "Verify no new debt inquiries"
  3. "Obtain updated bank statement showing reserves"
  4. "Complete property repairs per appraisal"
  5. "Provide homeowners insurance policy"

Updates:
  - loan_file.status = APPROVED_WITH_CONDITIONS
  - loan_file.current_conditions = List[UnderwritingCondition]
  - Each condition has severity: REQUIRED | PRIOR_TO_DOCS | PRIOR_TO_FUNDING

Saves loan file (Write #12)
```

**Decision 3: Denial**
```python
deny_loan(loan_number, denial_reasons)

Sample Denial Reasons:
  - "Credit score 580 below minimum 620 requirement"
  - "DTI 55% exceeds maximum 43%"
  - "Insufficient reserves (0 months, need 2 months)"
  - "Undisclosed debt found on credit report"
  - "Unstable employment history"

Updates:
  - loan_file.status = DENIED
  - loan_file.final_decision.approved = False
  - loan_file.final_decision.denial_reasons = List[str]
  - loan_file.final_decision.denial_date = today

Requires: Adverse Action Notice sent to borrower

Saves loan file (Write #12)
```

---

## Complete Document Checklist

### Initial Application Documents
- [ ] Uniform Residential Loan Application (URLA/1003)
- [ ] Government-issued ID (Driver's License, Passport)
- [ ] Social Security Card
- [ ] Authorization to pull credit

### Income Documents
- [ ] Recent Pay Stubs (last 2 months)
- [ ] W-2 Forms (last 2 years)
- [ ] Tax Returns (if self-employed, last 2 years)
- [ ] 1099 Forms (if applicable)
- [ ] Profit & Loss Statement (if self-employed, YTD)
- [ ] Business Tax Returns (if self-employed, 2 years)

### Asset Documents
- [ ] Bank Statements (all accounts, last 2 months, all pages)
- [ ] Investment Account Statements (last 2 months)
- [ ] 401(k)/IRA Statements (most recent)
- [ ] Gift Letter (if applicable, with donor bank statement)
- [ ] Earnest Money Deposit Receipt

### Employment Documents
- [ ] Employment Verification Letter (VOE)
- [ ] Offer Letter (if new job)
- [ ] Contact info for employer HR

### Property Documents
- [ ] Purchase Agreement (fully executed)
- [ ] Property Insurance Quote
- [ ] HOA Documents (if condo/townhome)
  - [ ] HOA Budget
  - [ ] HOA Bylaws
  - [ ] HOA Master Insurance Policy

### Ordered During Processing
- [x] Credit Report (ordered by lender)
- [x] Appraisal Report (ordered by lender)
- [x] Flood Certification (ordered by lender)
- [x] Title Report (ordered by lender)
- [x] Verification of Employment (ordered by lender)

### Additional Documents (as needed)
- [ ] Letter of Explanation (LOE) - for any credit issues
- [ ] Divorce Decree (if divorced, showing alimony/child support)
- [ ] Bankruptcy Discharge Papers (if applicable)
- [ ] Foreclosure Documents (if applicable)
- [ ] Student Loan Payment Verification
- [ ] Child Support/Alimony Order
- [ ] Rental Property Lease Agreements (if applicable)

---

## Document Flow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    SCENARIO CREATION (Initial)                   │
│  ✓ Creates loan file with borrower, property, loan info         │
│  ✓ Documents list: [] (empty initially)                          │
│  📝 WRITE #1: Scenario creation                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 1: LOAN PROCESSING                        │
├─────────────────────────────────────────────────────────────────┤
│  1️⃣  verify_loan_documents()                                     │
│      ✓ Checks: URLA, Paystubs, W-2, Bank Stmts, Purchase Agr    │
│      ✓ Adds missing docs with status: REQUIRED                   │
│      📝 WRITE #2                                                  │
├─────────────────────────────────────────────────────────────────┤
│  2️⃣  order_credit_report()                                       │
│      ✓ Generates: Credit report with score, tradelines           │
│      ✓ Updates: loan_file.credit_report                          │
│      📝 WRITE #3                                                  │
├─────────────────────────────────────────────────────────────────┤
│  3️⃣  order_appraisal()                                           │
│      ✓ Generates: Appraisal report with value, condition         │
│      ✓ Updates: loan_file.appraisal                              │
│      📝 WRITE #4                                                  │
├─────────────────────────────────────────────────────────────────┤
│  4️⃣  order_flood_certification()                                 │
│      ✓ Generates: Flood cert with zone, insurance requirement    │
│      ✓ Adds to: loan_file.documents                              │
│      📝 WRITE #5                                                  │
├─────────────────────────────────────────────────────────────────┤
│  5️⃣  verify_employment()                                         │
│      ✓ Generates: VOE form with employer verification            │
│      ✓ Updates: employment[0].verified = True                    │
│      ✓ Adds to: loan_file.documents                              │
│      📝 WRITE #6                                                  │
├─────────────────────────────────────────────────────────────────┤
│  6️⃣  calculate_loan_ratios()                                     │
│      ✓ Uses: W-2, Paystubs, Bank Stmts, Credit, Appraisal        │
│      ✓ Calculates: DTI, LTV, Housing Ratio, Reserves             │
│      ✓ Updates: loan_file.financial_metrics                      │
│      📝 WRITE #7                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 2: UNDERWRITING                           │
├─────────────────────────────────────────────────────────────────┤
│  1️⃣  review_credit_profile()                                     │
│      ✓ Reviews: Credit report, score, tradelines                 │
│      ✓ Adds: UnderwritingReview(type="credit")                   │
│      📝 WRITE #8                                                  │
├─────────────────────────────────────────────────────────────────┤
│  2️⃣  review_income_employment()                                  │
│      ✓ Reviews: W-2, Paystubs, VOE, Tax Returns                  │
│      ✓ Adds: UnderwritingReview(type="income")                   │
│      📝 WRITE #9                                                  │
├─────────────────────────────────────────────────────────────────┤
│  3️⃣  review_assets_reserves()                                    │
│      ✓ Reviews: Bank statements, investments, 401k               │
│      ✓ Adds: UnderwritingReview(type="assets")                   │
│      📝 WRITE #10                                                 │
├─────────────────────────────────────────────────────────────────┤
│  4️⃣  review_property_appraisal()                                 │
│      ✓ Reviews: Appraisal, Purchase Agreement, Title             │
│      ✓ Adds: UnderwritingReview(type="property")                 │
│      📝 WRITE #11                                                 │
├─────────────────────────────────────────────────────────────────┤
│  5️⃣  run_automated_underwriting()                                │
│      ✓ Submits: Complete loan file to AUS (DU/LP)                │
│      ✓ Receives: Automated decision + findings                   │
│      ✓ Updates: loan_file.au_decision                            │
│      ✓ Adds: UnderwritingReview(type="automated_underwriting")   │
│      📝 WRITE #12                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 3: FINAL DECISION                         │
├─────────────────────────────────────────────────────────────────┤
│  decision_maker analyzes ALL reviews + AUS decision:             │
│                                                                   │
│  IF all acceptable:                                               │
│    → issue_final_approval()                                      │
│    → Status: CLEAR_TO_CLOSE ✅                                    │
│    → Conditions: [] (none)                                        │
│                                                                   │
│  ELSE IF minor issues:                                            │
│    → issue_underwriting_conditions()                             │
│    → Status: APPROVED_WITH_CONDITIONS ⚠️                          │
│    → Conditions: [List of required items]                        │
│                                                                   │
│  ELSE:                                                            │
│    → deny_loan()                                                 │
│    → Status: DENIED ❌                                            │
│    → Reasons: [List of denial reasons]                           │
│                                                                   │
│  📝 WRITE #13 (FINAL)                                             │
└─────────────────────────────────────────────────────────────────┘

Expected Total: 13 file writes for complete happy path workflow
```

---

## Document Storage Locations in LoanFile

```python
LoanFile {
  # Core Documents List
  documents: List[Document] = [
    Document(type="urla", status="approved"),
    Document(type="paystub", status="approved"),
    Document(type="w2", status="approved"),
    Document(type="bank_statement", status="approved"),
    Document(type="purchase_agreement", status="approved"),
    Document(type="flood_certification", status="approved"),
    Document(type="employment_verification", status="approved"),
    ...
  ]

  # Specialized Document Objects
  credit_report: CreditReport { score, tradelines, ... }
  appraisal: Appraisal { value, condition, comps, ... }
  title_report: TitleReport { ... }
  flood_cert: FloodCertification { zone, required, ... }

  # Financial Metrics (derived from documents)
  financial_metrics: FinancialMetrics {
    dti_ratio: 35.0,
    ltv_ratio: 80.0,
    reserves_months: 6.0,
    ...
  }

  # Underwriting Reviews (analysis of documents)
  underwriting_reviews: List[UnderwritingReview] = [
    Review(type="credit", status="acceptable"),
    Review(type="income", status="acceptable"),
    Review(type="assets", status="acceptable"),
    Review(type="property", status="acceptable"),
    Review(type="automated_underwriting", status="acceptable"),
  ]

  # Final Decision
  final_decision: {
    approved: True,
    approved_amount: $320,000,
    approved_rate: 6.75%,
    conditions: [],
    decision_date: "2025-12-01"
  }
}
```

---

## Key Insights

### Current System Behavior (From Log Analysis):

1. **Tools called multiple times** (4x per tool on average)
   - Caused by `MaxMessageTermination(5)` allowing multi-turn conversations
   - Each turn triggers tool call due to `tool_choice="required"`
   - LLM calls tool, gets result, but continues conversation instead of terminating

2. **Only 1 file write tracked**
   - Despite ~35+ tool executions
   - Tools ARE running (confirmed by logs)
   - Tools SHOULD be saving (code inspection confirms `file_manager.save_loan_file()` calls)
   - **Root cause unknown - requires investigation**

3. **Documents in actual file** (LN-3DCEE4):
   - Only contains: flood_certification (4x) and employment_verification (4x)
   - Missing: URLA, W-2, paystubs, bank statements, purchase agreement
   - Missing: credit_report, appraisal, financial_metrics
   - Missing: underwriting_reviews, final_decision
   - **File appears incomplete despite successful workflow completion**

### Recommended Investigation:

1. Check if `file_manager.save_loan_file()` is actually executing
2. Verify file write increments are working
3. Add more granular logging around file save operations
4. Consider reducing `MaxMessageTermination` to 2 to prevent redundant tool calls

---

## Summary

This mortgage underwriting system processes **18+ document types** across **4 phases**:

- **Phase 0:** No documents (rate shopping only)
- **Phase 1:** Generates/verifies 6 key documents (URLA, W-2, paystubs, bank statements, credit, appraisal, flood, employment)
- **Phase 2:** Reviews all documents, adds 5 underwriting analyses
- **Phase 3:** Makes final decision based on all document reviews

**Expected writes:** 13 (1 scenario + 6 Phase 1 + 5 Phase 2 + 1 Phase 3)
**Actual writes:** 1 (discrepancy to be investigated)
