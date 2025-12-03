# Document Access Control Model

## Overview
This document defines which agent types can access which documents, when they can access them, and what level of access (read vs write) they have during each phase of the mortgage underwriting workflow.

---

## Agent Types & Roles

| Agent Type | Count | Primary Responsibility |
|------------|-------|------------------------|
| **Mortgage Broker** | 5 | Initial document collection, rate shopping |
| **Loan Processor** | 6 | Document processing, verification, ordering reports |
| **Underwriter** | 5 | Risk analysis, document review, decision support |
| **Decision Maker** | 1 | Final approval/denial decision |

---

## Access Control Principles

### Principle 1: **Phase-Based Access**
Access rights change as the loan progresses through phases:
- **Phase 0 (Rate Shopping):** Brokers read initial docs
- **Phase 1 (Processing):** Processors read/write, brokers read-only
- **Phase 2 (Underwriting):** Underwriters read-only, processors read-only
- **Phase 3 (Decision):** Decision maker read-only, all others read-only

### Principle 2: **Least Privilege**
Agents only have access to documents necessary for their specific tasks.

### Principle 3: **Immutability After Submission**
Once documents are submitted to the next phase, previous phase agents lose write access.

### Principle 4: **Audit Trail**
All document access is logged for compliance and tracking.

---

## Phase 0: Rate Shopping

### Mortgage Brokers (5 agents)

| Document | Read | Write | Notes |
|----------|------|-------|-------|
| **URLA** | ✅ | ❌ | Read borrower info for rate quotes |
| **Credit Authorization** | ✅ | ❌ | Verify authorization to pull credit |
| Purchase Price | ✅ | ❌ | From URLA - needed for rate quotes |
| Loan Amount | ✅ | ❌ | From URLA - needed for rate quotes |
| Property Info | ✅ | ❌ | From URLA - loan type determination |
| **All other docs** | ❌ | ❌ | Not needed for rate shopping |

**Access Duration:** Phase 0 only
**After Phase 0:** Read-only access to URLA (cannot modify)

### Output Generated:
- **Rate Quotes** (5 lenders) - stored as JSON strings, not file writes

---

## Phase 1: Loan Processing

### Loan Processor 1: Document Verification

| Document | Read | Write | Phase Restriction |
|----------|------|-------|-------------------|
| **URLA** | ✅ | ✅ | Can request updates if incomplete |
| **Paystubs** | ✅ | ✅ | Can mark as approved/rejected |
| **W-2 Forms** | ✅ | ✅ | Can mark as approved/rejected |
| **Bank Statements** | ✅ | ✅ | Can mark as approved/rejected |
| **Purchase Agreement** | ✅ | ✅ | Can mark as approved/rejected |
| Government ID | ✅ | ✅ | Can verify validity |
| Social Security Card | ✅ | ✅ | Can verify SSN match |

**After Phase 1 ends:** ⚠️ Read-only access (no more modifications)

**Why:** Once submitted to underwriting, source documents are locked to maintain integrity.

---

### Loan Processor 2: Credit Report Specialist

| Document | Read | Write | Purpose |
|----------|------|-------|---------|
| **Credit Authorization** | ✅ | ❌ | Verify permission to pull credit |
| **URLA** | ✅ | ❌ | Get borrower SSN, personal info |
| **Credit Report** | ✅ | ✅ | **GENERATES this document** |
| Paystubs | ❌ | ❌ | Not needed for credit ordering |
| W-2 | ❌ | ❌ | Not needed for credit ordering |

**Generated Document:**
- **Credit Report** - Tri-bureau report with score, tradelines, payment history

**After Phase 1 ends:** ⚠️ Read-only to Credit Report (cannot re-pull credit)

**Why:** Credit report is a point-in-time snapshot. Cannot be modified after generation.

---

### Loan Processor 3: Appraisal Specialist

| Document | Read | Write | Purpose |
|----------|------|-------|---------|
| **Purchase Agreement** | ✅ | ❌ | Get property address, purchase price |
| **URLA** | ✅ | ❌ | Get property details |
| **Appraisal Report** | ✅ | ✅ | **GENERATES this document** |
| Property Insurance | ❌ | ❌ | Not needed for appraisal ordering |
| HOA Documents | ❌ | ❌ | Not needed for appraisal ordering |

**Generated Document:**
- **Appraisal Report** - Property valuation, condition, comps

**After Phase 1 ends:** ⚠️ Read-only to Appraisal (cannot modify valuation)

**Why:** Appraisal is an independent third-party assessment. Must remain unaltered.

---

### Loan Processor 4: Flood Certification Specialist

| Document | Read | Write | Purpose |
|----------|------|-------|---------|
| **Purchase Agreement** | ✅ | ❌ | Get property address |
| **URLA** | ✅ | ❌ | Get property address if not in purchase agreement |
| **Flood Certification** | ✅ | ✅ | **GENERATES this document** |
| Appraisal | ❌ | ❌ | Not needed for flood cert |

**Generated Document:**
- **Flood Certification** - FEMA flood zone, insurance requirement

**After Phase 1 ends:** ⚠️ Read-only (flood zone doesn't change)

**Why:** FEMA determination is official. Cannot be modified.

---

### Loan Processor 5: Employment Verification Specialist

| Document | Read | Write | Purpose |
|----------|------|-------|---------|
| **URLA** | ✅ | ❌ | Get employer name, contact info |
| **Paystubs** | ✅ | ❌ | Verify income matches VOE |
| **W-2 Forms** | ✅ | ❌ | Verify historical income |
| **Employment Verification (VOE)** | ✅ | ✅ | **GENERATES this document** |
| Offer Letter | ✅ | ❌ | If new job, verify start date |

**Generated Document:**
- **Verification of Employment** - Employer confirmation of job, income, tenure

**After Phase 1 ends:** ⚠️ Read-only (employment verified at point in time)

**Why:** VOE is an official employer statement. Cannot be altered after receipt.

---

### Loan Processor 6: Financial Calculations Specialist

| Document | Read | Write | Purpose |
|----------|------|-------|---------|
| **W-2 Forms** | ✅ | ❌ | Calculate annual income |
| **Paystubs** | ✅ | ❌ | Calculate monthly income |
| **Bank Statements** | ✅ | ❌ | Calculate reserves |
| **Credit Report** | ✅ | ❌ | Calculate monthly debt obligations |
| **Appraisal Report** | ✅ | ❌ | Calculate LTV |
| **URLA** | ✅ | ✅ | Update with calculated ratios |
| **Financial Metrics** | ✅ | ✅ | **GENERATES/UPDATES this section** |

**Generated/Updated:**
- **Financial Metrics** - DTI, LTV, Housing Ratio, Reserves

**After Phase 1 ends:** ⚠️ Read-only (calculations locked)

**Why:** Financial snapshot at time of submission. Ratios cannot change unless new docs submitted.

---

### Mortgage Brokers Access During Phase 1:

| Document | Read | Write | Notes |
|----------|------|-------|-------|
| **URLA** | ✅ | ❌ | Read-only (no longer collecting application) |
| **All other docs** | ❌ | ❌ | No access during processing phase |

**Why:** Brokers completed their role in Phase 0. No longer need document access.

---

## Phase 2: Underwriting Review

### Underwriter 1: Credit Review Specialist

| Document | Read | Write | Purpose |
|----------|------|-------|---------|
| **Credit Report** | ✅ | ❌ | Primary review document |
| **Letter of Explanation (LOE)** | ✅ | ❌ | If credit issues exist |
| **Bankruptcy Discharge** | ✅ | ❌ | If applicable |
| **Foreclosure Documents** | ✅ | ❌ | If applicable |
| **URLA** | ✅ | ❌ | Cross-reference credit info |
| **Underwriting Review** | ❌ | ✅ | **CREATES review findings** |
| **Conditions** | ❌ | ✅ | Can issue credit-related conditions |

**Cannot Access:** W-2, Paystubs, Bank Statements (not needed for credit review)

**Generates:**
- **Credit Review** - Analysis of credit profile with findings
- **Conditions** - Credit-related conditions if needed

**After Phase 2:** ⚠️ Read-only to own review (cannot modify after submission)

---

### Underwriter 2: Income & Employment Review Specialist

| Document | Read | Write | Purpose |
|----------|------|-------|---------|
| **W-2 Forms** | ✅ | ❌ | Primary income verification |
| **Paystubs** | ✅ | ❌ | Current income verification |
| **Employment Verification (VOE)** | ✅ | ❌ | Employment confirmation |
| **Tax Returns** | ✅ | ❌ | If self-employed |
| **1099 Forms** | ✅ | ❌ | If contractor |
| **P&L Statement** | ✅ | ❌ | If self-employed |
| **URLA** | ✅ | ❌ | Cross-reference employment info |
| **Underwriting Review** | ❌ | ✅ | **CREATES review findings** |
| **Conditions** | ❌ | ✅ | Can issue income-related conditions |

**Cannot Access:** Bank Statements, Credit Report, Appraisal (not needed for income review)

**Generates:**
- **Income Review** - Analysis of income stability and adequacy
- **Conditions** - Income-related conditions if needed

---

### Underwriter 3: Assets & Reserves Review Specialist

| Document | Read | Write | Purpose |
|----------|------|-------|---------|
| **Bank Statements** | ✅ | ❌ | Primary asset verification |
| **Investment Statements** | ✅ | ❌ | Asset verification |
| **401(k)/IRA Statements** | ✅ | ❌ | Retirement assets |
| **Gift Letter** | ✅ | ❌ | If gift funds used |
| **Earnest Money Receipt** | ✅ | ❌ | Verify deposit paid |
| **Financial Metrics** | ✅ | ❌ | Check calculated reserves |
| **URLA** | ✅ | ❌ | Cross-reference asset info |
| **Underwriting Review** | ❌ | ✅ | **CREATES review findings** |
| **Conditions** | ❌ | ✅ | Can issue asset-related conditions |

**Cannot Access:** Paystubs, W-2, Credit Report (not needed for asset review)

**Generates:**
- **Assets Review** - Analysis of down payment source and reserves
- **Conditions** - Asset-related conditions if needed

---

### Underwriter 4: Property Review Specialist

| Document | Read | Write | Purpose |
|----------|------|-------|---------|
| **Appraisal Report** | ✅ | ❌ | Primary review document |
| **Purchase Agreement** | ✅ | ❌ | Verify purchase price vs appraisal |
| **Title Report** | ✅ | ❌ | Property ownership verification |
| **Property Insurance** | ✅ | ❌ | Insurance adequacy |
| **HOA Documents** | ✅ | ❌ | If condo/townhome |
| **Flood Certification** | ✅ | ❌ | Flood insurance requirement |
| **Financial Metrics** | ✅ | ❌ | Check LTV calculation |
| **URLA** | ✅ | ❌ | Cross-reference property info |
| **Underwriting Review** | ❌ | ✅ | **CREATES review findings** |
| **Conditions** | ❌ | ✅ | Can issue property-related conditions |

**Cannot Access:** W-2, Paystubs, Bank Statements, Credit Report (not needed)

**Generates:**
- **Property Review** - Analysis of property value and condition
- **Conditions** - Property-related conditions if needed

---

### Underwriter 5: Automated Underwriting Specialist

| Document | Read | Write | Purpose |
|----------|------|-------|---------|
| **ALL DOCUMENTS** | ✅ | ❌ | Submits complete file to AUS |
| URLA | ✅ | ❌ | Application data |
| Credit Report | ✅ | ❌ | Credit data |
| W-2, Paystubs | ✅ | ❌ | Income data |
| Bank Statements | ✅ | ❌ | Asset data |
| Appraisal | ✅ | ❌ | Property data |
| Employment Verification | ✅ | ❌ | Employment data |
| Financial Metrics | ✅ | ❌ | Calculated ratios |
| **AUS Decision** | ❌ | ✅ | **GENERATES AUS decision** |
| **Underwriting Review** | ❌ | ✅ | **CREATES review findings** |

**Generates:**
- **AUS Decision** - Desktop Underwriter/Loan Prospector findings
- **Automated Underwriting Review** - AUS recommendation and findings

**Why Full Access:** AUS needs complete loan file for risk assessment.

---

### Loan Processors Access During Phase 2:

| Document | Read | Write | Notes |
|----------|------|-------|-------|
| **ALL documents** | ✅ | ❌ | Read-only access (no modifications) |

**Why:** Processors may need to reference documents to answer underwriter questions, but cannot modify documents under review.

### Mortgage Brokers Access During Phase 2:

| Document | Read | Write | Notes |
|----------|------|-------|-------|
| **ALL documents** | ❌ | ❌ | No access during underwriting |

**Why:** Brokers have no role in underwriting phase.

---

## Phase 3: Final Decision

### Decision Maker

| Document | Read | Write | Purpose |
|----------|------|-------|---------|
| **ALL Underwriting Reviews** | ✅ | ❌ | Review all 5 underwriting analyses |
| **AUS Decision** | ✅ | ❌ | Review automated findings |
| **Credit Report** | ✅ | ❌ | Reference if needed |
| **Financial Metrics** | ✅ | ❌ | Verify ratios |
| **Appraisal** | ✅ | ❌ | Verify value |
| **URLA** | ✅ | ❌ | Borrower information |
| **ALL other documents** | ✅ | ❌ | Read-only access to all docs |
| **Final Decision** | ❌ | ✅ | **CREATES final decision** |
| **Approval Letter** | ❌ | ✅ | **GENERATES if approved** |
| **Denial Letter** | ❌ | ✅ | **GENERATES if denied** |
| **Conditions List** | ❌ | ✅ | **CREATES if conditional approval** |

**Generates:**
- **Final Decision** - Approval, Conditional Approval, or Denial
- **Decision Letter** - Official notification to borrower
- **Conditions** - List of items needed for clear to close (if conditional)

---

### All Other Agents During Phase 3:

| Agent Type | Document Access | Purpose |
|------------|----------------|---------|
| **Mortgage Brokers** | ❌ No access | Role completed |
| **Loan Processors** | ✅ Read-only to ALL | May need to clear conditions |
| **Underwriters** | ✅ Read-only to ALL | May need to review condition responses |

---

## Access Control Summary Table

### Who Can Access What Documents?

| Document Type | Brokers (Phase 0) | Processors (Phase 1) | Underwriters (Phase 2) | Decision Maker (Phase 3) |
|--------------|-------------------|---------------------|----------------------|------------------------|
| **URLA** | Read | Read/Write | Read | Read |
| **Paystubs** | ❌ | Read/Write | Read (U2 only) | Read |
| **W-2 Forms** | ❌ | Read/Write | Read (U2 only) | Read |
| **Bank Statements** | ❌ | Read/Write | Read (U3 only) | Read |
| **Purchase Agreement** | ❌ | Read/Write | Read (U4 only) | Read |
| **Credit Report** | ❌ | Generate (P2) | Read (U1 only) | Read |
| **Appraisal** | ❌ | Generate (P3) | Read (U4 only) | Read |
| **Flood Cert** | ❌ | Generate (P4) | Read (U4 only) | Read |
| **Employment VOE** | ❌ | Generate (P5) | Read (U2 only) | Read |
| **Financial Metrics** | ❌ | Generate (P6) | Read (All) | Read |
| **Underwriting Reviews** | ❌ | ❌ | Generate (Each U) | Read |
| **Final Decision** | ❌ | ❌ | ❌ | Generate |

Legend:
- ✅ Read = Can view document
- ✅ Read/Write = Can view and modify document
- ✅ Generate = Can create new document
- ❌ = No access
- (U1, U2, etc.) = Specific underwriter only
- (P2, P3, etc.) = Specific processor only

---

## Access Transitions: When Access Changes

### Example: W-2 Form Access Lifecycle

| Phase | Mortgage Brokers | Loan Processors | Underwriters | Decision Maker |
|-------|-----------------|----------------|--------------|---------------|
| **Phase 0** (Rate Shopping) | ❌ No access | ❌ Not yet submitted | ❌ Not yet submitted | ❌ Not yet submitted |
| **Phase 1** (Processing) | ❌ No access | ✅ **Read/Write**<br>(Can verify, approve, request updates) | ❌ Not yet submitted | ❌ Not yet submitted |
| **After Phase 1** (Submitted to UW) | ❌ No access | ⚠️ **Read-only**<br>(Can view but not modify) | ✅ **Read-only**<br>(Underwriter 2 reviews) | ❌ Not yet |
| **Phase 2** (Underwriting) | ❌ No access | ⚠️ **Read-only** | ✅ **Read-only**<br>(U2 analyzes income) | ❌ Not yet |
| **Phase 3** (Decision) | ❌ No access | ⚠️ **Read-only** | ⚠️ **Read-only** | ✅ **Read-only** |
| **After Approval/Denial** | ❌ No access | ⚠️ **Read-only** | ⚠️ **Read-only** | ⚠️ **Read-only** |

**Key Insight:** Once a document is submitted to the next phase, all previous phase agents lose write access.

---

### Example: Credit Report Access Lifecycle

| Phase | Mortgage Brokers | Loan Processor 2 | Other Processors | Underwriter 1 | Decision Maker |
|-------|-----------------|-----------------|------------------|--------------|---------------|
| **Phase 1** (Processing) | ❌ | ✅ **Generate & Write**<br>Orders and receives report | ⚠️ **Read-only**<br>(Can view for their tasks) | ❌ Not yet | ❌ Not yet |
| **After Phase 1** (Submitted to UW) | ❌ | ⚠️ **Read-only**<br>(Cannot re-pull credit) | ⚠️ **Read-only** | ✅ **Read-only** | ❌ Not yet |
| **Phase 2** (Underwriting) | ❌ | ⚠️ **Read-only** | ⚠️ **Read-only** | ✅ **Read-only**<br>(Reviews credit) | ❌ Not yet |
| **Phase 3** (Decision) | ❌ | ⚠️ **Read-only** | ⚠️ **Read-only** | ⚠️ **Read-only** | ✅ **Read-only** |

**Key Insight:** The agent who generates a document (Processor 2 for credit report) loses write access after submission, ensuring document integrity.

---

### Example: Underwriting Review Access Lifecycle

| Phase | Loan Processors | Underwriter 1 | Other Underwriters | Decision Maker |
|-------|----------------|--------------|-------------------|---------------|
| **Phase 2** (Underwriting) | ❌ Cannot see reviews | ✅ **Generate & Write**<br>Creates credit review | ⚠️ **Read-only**<br>(Can see other reviews) | ❌ Not yet |
| **After U1 completes review** | ❌ | ⚠️ **Read-only**<br>(Cannot modify own review) | ⚠️ **Read-only** | ❌ Not yet |
| **Phase 3** (Decision) | ⚠️ **Read-only**<br>(Can see reviews) | ⚠️ **Read-only** | ⚠️ **Read-only** | ✅ **Read-only**<br>(Reviews all analyses) |

**Key Insight:** Once an underwriter submits their review, they cannot modify it. This prevents changing opinions after decision is made.

---

## Why Access Restrictions Matter

### 1. **Document Integrity**
Once a document is submitted for review, it should not be modified. This ensures:
- Underwriters review the same documents that processors verified
- No alterations after initial submission
- Audit trail integrity

### 2. **Separation of Duties**
Different agents handle different tasks:
- **Processors** collect and verify documents
- **Underwriters** analyze and assess risk
- **Decision Maker** makes final approval/denial

Preventing overlap reduces conflicts of interest.

### 3. **Regulatory Compliance**
Mortgage lending is heavily regulated. Access controls ensure:
- Fair Lending compliance (no bias in document handling)
- Privacy protection (agents only see needed documents)
- Audit capability (who accessed what and when)

### 4. **Data Privacy**
Borrowers' sensitive financial information should be:
- Limited to agents who need it for their specific task
- Protected from unnecessary exposure
- Logged for security monitoring

---

## Current System vs Recommended System

### Current System (As Implemented):
```python
# ALL agents can do this at ANY time:
loan_file = file_manager.load_loan_file(loan_number)  # Read access
loan_file.documents.append(new_doc)                   # Write access
loan_file.credit_report = new_report                  # Write access
file_manager.save_loan_file(loan_file)                # Save access
```

**Problems:**
- ❌ No access control
- ❌ Any agent can modify any document at any time
- ❌ No phase-based restrictions
- ❌ No audit of who accessed what

---

### Recommended System:

```python
# Example 1: Loan Processor 2 in Phase 1 (HAS access)
async def order_credit_report(loan_number: str, agent_id: str, phase: str):
    # Check access
    if not access_control.can_write(agent_id, "credit_report", phase):
        raise PermissionDenied("Cannot write credit_report in phase {phase}")

    # Load loan file
    loan_file = file_manager.load_loan_file_with_audit(
        loan_number,
        agent_id,
        action="read",
        documents=["URLA", "credit_authorization"]
    )

    # Generate credit report
    credit_report = await credit_bureau.fetch_report(loan_file.borrowers[0])

    # Save with audit
    loan_file.credit_report = credit_report
    file_manager.save_loan_file_with_audit(
        loan_file,
        agent_id,
        action="write",
        documents=["credit_report"]
    )
```

```python
# Example 2: Mortgage Broker in Phase 1 (NO access)
async def view_loan_status(loan_number: str, agent_id: str, phase: str):
    # Check access
    if not access_control.can_read(agent_id, "credit_report", phase):
        raise PermissionDenied("Brokers cannot access credit_report in Phase 1")

    # Access denied - broker cannot see credit report during processing
```

```python
# Example 3: Loan Processor in Phase 2 (Read-only)
async def answer_underwriter_question(loan_number: str, agent_id: str, phase: str):
    # Check access
    if not access_control.can_read(agent_id, "paystubs", phase):
        raise PermissionDenied("No access to paystubs in Phase 2")

    # Can read but cannot modify
    loan_file = file_manager.load_loan_file_with_audit(
        loan_number,
        agent_id,
        action="read",
        documents=["paystubs"]
    )

    # Try to modify - BLOCKED
    if access_control.can_write(agent_id, "paystubs", phase):
        loan_file.documents[0].status = "approved"  # Would work in Phase 1
    else:
        raise PermissionDenied("Read-only access to paystubs in Phase 2")
```

---

## Implementation Recommendation

### Add Access Control Layer:

```python
class AccessControl:
    """Role-based access control for document management"""

    PERMISSIONS = {
        # Agent Type: { phase: { document: permission } }
        "mortgage_broker": {
            "phase_0": {
                "urla": "read",
                "credit_authorization": "read",
            },
            "phase_1": {},  # No access
            "phase_2": {},  # No access
            "phase_3": {},  # No access
        },
        "loan_processor": {
            "phase_0": {},  # Not active yet
            "phase_1": {
                "urla": "write",
                "paystubs": "write",
                "w2": "write",
                "bank_statements": "write",
                "purchase_agreement": "write",
                "credit_report": "write",  # Only processor_2
                "appraisal": "write",       # Only processor_3
                "flood_cert": "write",      # Only processor_4
                "employment_voe": "write",  # Only processor_5
                "financial_metrics": "write", # Only processor_6
            },
            "phase_2": {
                # All documents become read-only
                "urla": "read",
                "paystubs": "read",
                "w2": "read",
                "bank_statements": "read",
                "credit_report": "read",
                "appraisal": "read",
                "flood_cert": "read",
                "employment_voe": "read",
                "financial_metrics": "read",
            },
            "phase_3": {
                # Still read-only
                "*": "read",
            }
        },
        "underwriter": {
            "phase_0": {},  # Not active yet
            "phase_1": {},  # Not active yet
            "phase_2": {
                # All documents read-only for review
                "*": "read",
                # Can write their own review
                "underwriting_review": "write",
                "conditions": "write",
            },
            "phase_3": {
                # All read-only
                "*": "read",
            }
        },
        "decision_maker": {
            "phase_0": {},
            "phase_1": {},
            "phase_2": {},
            "phase_3": {
                # All documents read-only
                "*": "read",
                # Can write final decision
                "final_decision": "write",
                "approval_letter": "write",
                "denial_letter": "write",
                "conditions_list": "write",
            }
        }
    }

    @staticmethod
    def can_read(agent_type: str, document: str, phase: str) -> bool:
        """Check if agent can read document in current phase"""
        perms = AccessControl.PERMISSIONS.get(agent_type, {}).get(phase, {})
        perm = perms.get(document) or perms.get("*")
        return perm in ["read", "write"]

    @staticmethod
    def can_write(agent_type: str, document: str, phase: str) -> bool:
        """Check if agent can write document in current phase"""
        perms = AccessControl.PERMISSIONS.get(agent_type, {}).get(phase, {})
        perm = perms.get(document) or perms.get("*")
        return perm == "write"
```

---

## Key Takeaways

1. **Brokers:** Limited access, only Phase 0, read-only to URLA for rate shopping
2. **Processors:** Full access in Phase 1, read-only after submission to underwriting
3. **Underwriters:** Read-only access to all docs, write access only to own reviews
4. **Decision Maker:** Read-only to all docs and reviews, write access only to final decision

5. **Once submitted to next phase, documents are locked** (immutable)
6. **Each agent type sees only documents needed for their specific task**
7. **All access should be audited** for compliance and security
8. **Current system has NO access control** - all agents can access everything

Would you like me to implement the access control system in the codebase?
