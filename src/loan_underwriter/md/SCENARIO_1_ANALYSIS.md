# Scenario 1: Clean Approval - Complete Process Analysis

## Executive Summary
This document provides a comprehensive analysis of the mortgage underwriting system's Scenario 1 (Clean Approval - Happy Path) workflow, including control flow diagrams, step-by-step process explanations, validation assertions, and autogen framework mechanics.

---

## 1. Control Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INITIATES SCENARIO 1                     │
│                        (Input: 1 in main menu)                       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SCENARIO CREATION PHASE                           │
│  File: scenarios.py, Function: create_scenario_clean_approval()      │
├─────────────────────────────────────────────────────────────────────┤
│  1. Generate unique loan_number (LN-XXXXXX)                          │
│  2. Create Borrower object with:                                     │
│     - Credit score: 750 (excellent)                                  │
│     - Employment: 5 years stable                                     │
│     - Monthly income: $8,500                                         │
│     - Assets: $195,000 total                                         │
│  3. Create PropertyInfo object                                       │
│  4. Create LoanInfo object:                                          │
│     - Loan amount: $320,000                                          │
│     - Purchase price: $400,000                                       │
│     - LTV: 80%                                                       │
│  5. Create LoanFile with status: APPLICATION_RECEIVED                │
│  6. Save to file system: ./loan_files/active/{loan_number}.json     │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW INITIALIZATION                           │
│  File: main.py, Function: run_workflow()                             │
├─────────────────────────────────────────────────────────────────────┤
│  1. Create Swarm team with 3 agents                                  │
│  2. Set termination conditions                                       │
│  3. Prepare initial_task message                                     │
│  4. Start team.run_stream()                                          │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR AGENT                              │
│  File: agents.py, orchestrator_agent                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Receives: "New loan application received..."                        │
│  Decision: Route to loan_processor_agent                             │
│  Action: HANDOFF → loan_processor_agent                              │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   LOAN PROCESSOR AGENT - PHASE 1                     │
│  File: agents.py, loan_processor_agent                               │
├─────────────────────────────────────────────────────────────────────┤
│  CONCURRENT EXECUTION (5 tools in parallel):                         │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ 1. verify_loan_documents(loan_number)           [1s]     │      │
│  │    ├─ Checks required documents                          │      │
│  │    ├─ Updates document status                            │      │
│  │    └─ Status: DOCUMENTS_COMPLETE                         │      │
│  │                                                           │      │
│  │ 2. order_credit_report(loan_number)             [2-5s]   │      │
│  │    ├─ Calls CreditBureauSimulator                        │      │
│  │    ├─ Retrieves credit score: 750                        │      │
│  │    ├─ Gets credit history                                │      │
│  │    └─ Saves credit report to loan file                   │      │
│  │                                                           │      │
│  │ 3. order_appraisal(loan_number)                 [1-2s]   │      │
│  │    ├─ Calls AppraisalManagementSimulator                 │      │
│  │    ├─ Orders property appraisal                          │      │
│  │    └─ Status: APPRAISAL_ORDERED                          │      │
│  │                                                           │      │
│  │ 4. order_flood_certification(loan_number)       [1s]     │      │
│  │    ├─ Calls FloodCertificationSimulator                  │      │
│  │    ├─ Checks flood zone (ZIP: 62702 → Zone X)           │      │
│  │    └─ Result: No flood insurance required                │      │
│  │                                                           │      │
│  │ 5. verify_employment(loan_number)               [1-3s]   │      │
│  │    ├─ Calls EmploymentVerificationSimulator              │      │
│  │    ├─ Verifies employment at Tech Corp                   │      │
│  │    └─ Confirms stable 5-year employment                  │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                      │
│  All 5 tasks complete simultaneously (max 5s total)                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   LOAN PROCESSOR AGENT - PHASE 2                     │
├─────────────────────────────────────────────────────────────────────┤
│  SEQUENTIAL EXECUTION (depends on credit report):                    │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ 6. calculate_loan_ratios(loan_number)           [1s]     │      │
│  │    ├─ Calculates DTI (Debt-to-Income ratio)              │      │
│  │    ├─ Monthly payment: ~$2,400                           │      │
│  │    ├─ Monthly income: $8,500                             │      │
│  │    ├─ DTI: ~35% (Excellent)                              │      │
│  │    ├─ LTV: 80% (Good)                                    │      │
│  │    └─ Reserves: 6+ months (Strong)                       │      │
│  └──────────────────────────────────────────────────────────┘      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   LOAN PROCESSOR AGENT - PHASE 3                     │
├─────────────────────────────────────────────────────────────────────┤
│  SEQUENTIAL EXECUTION (depends on ratios):                           │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ 7. submit_to_underwriting(loan_number)          [1s]     │      │
│  │    ├─ Validates all required data present                │      │
│  │    ├─ Updates status: SUBMITTED_TO_UNDERWRITING          │      │
│  │    ├─ Records submission timestamp                       │      │
│  │    └─ Prepares file for underwriter review               │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                      │
│  Action: HANDOFF → orchestrator_agent                                │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR AGENT                              │
├─────────────────────────────────────────────────────────────────────┤
│  Receives: "Loan submitted to underwriting"                          │
│  Decision: Route to underwriter_agent                                │
│  Action: HANDOFF → underwriter_agent                                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    UNDERWRITER AGENT - PHASE 1                       │
│  File: agents.py, underwriter_agent                                  │
├─────────────────────────────────────────────────────────────────────┤
│  SEQUENTIAL EXECUTION (must go first):                               │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ 1. run_automated_underwriting(loan_number)      [2-4s]   │      │
│  │    ├─ Simulates DU/LP (Desktop Underwriter)              │      │
│  │    ├─ Analyzes credit (750), DTI (35%), LTV (80%)        │      │
│  │    ├─ Recommendation: APPROVE/ACCEPT                     │      │
│  │    └─ Risk level: LOW                                    │      │
│  └──────────────────────────────────────────────────────────┘      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    UNDERWRITER AGENT - PHASE 2                       │
├─────────────────────────────────────────────────────────────────────┤
│  CONCURRENT EXECUTION (4 reviews in parallel):                       │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ 2. review_credit_profile(loan_number)           [1s]     │      │
│  │    ├─ Credit score: 750 ✓ (>= 620 required)             │      │
│  │    ├─ Payment history: Clean ✓                           │      │
│  │    ├─ Inquiries: Normal ✓                                │      │
│  │    └─ Conclusion: APPROVED                               │      │
│  │                                                           │      │
│  │ 3. review_income_employment(loan_number)        [1s]     │      │
│  │    ├─ Employment: 5 years stable ✓                       │      │
│  │    ├─ Income: $8,500/month verified ✓                    │      │
│  │    ├─ DTI: 35% ✓ (<= 50% required)                       │      │
│  │    └─ Conclusion: APPROVED                               │      │
│  │                                                           │      │
│  │ 4. review_assets_reserves(loan_number)          [1s]     │      │
│  │    ├─ Liquid assets: $75,000 ✓                           │      │
│  │    ├─ Reserves: 6+ months ✓ (>= 2 required)             │      │
│  │    ├─ Source of funds: Verified ✓                        │      │
│  │    └─ Conclusion: APPROVED                               │      │
│  │                                                           │      │
│  │ 5. review_property_appraisal(loan_number)       [1s]     │      │
│  │    ├─ Appraisal value: $400,000 ✓                        │      │
│  │    ├─ Matches purchase price ✓                           │      │
│  │    ├─ Condition: Good ✓                                  │      │
│  │    └─ Conclusion: APPROVED                               │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                      │
│  All 4 reviews complete simultaneously (max 1s total)                │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    UNDERWRITER AGENT - PHASE 3                       │
├─────────────────────────────────────────────────────────────────────┤
│  DECISION MAKING:                                                    │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ Analysis:                                                 │      │
│  │  ✓ All reviews passed                                    │      │
│  │  ✓ No conditions identified                              │      │
│  │  ✓ No issues found                                       │      │
│  │  ✓ Risk level: LOW                                       │      │
│  │                                                           │      │
│  │ Decision: FINAL APPROVAL                                 │      │
│  │                                                           │      │
│  │ 6. issue_final_approval(loan_number)            [1s]     │      │
│  │    ├─ Updates status: CLEAR_TO_CLOSE                     │      │
│  │    ├─ Records approval timestamp                         │      │
│  │    ├─ Generates approval letter                          │      │
│  │    └─ Notifies all parties                               │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                      │
│  Action: HANDOFF → orchestrator_agent                                │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR AGENT                              │
├─────────────────────────────────────────────────────────────────────┤
│  Receives: "Final approval issued"                                   │
│  Status: CLEAR_TO_CLOSE                                              │
│  Decision: Workflow complete                                         │
│  Action: Respond "TERMINATE"                                         │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      WORKFLOW COMPLETION                             │
│  File: main.py, run_workflow()                                       │
├─────────────────────────────────────────────────────────────────────┤
│  1. Detect TERMINATE message                                         │
│  2. Print workflow completion summary                                │
│  3. Display file location                                            │
│  4. Show storage statistics                                          │
│  5. Show write count for loan                                        │
│  6. Return control to user                                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Step-by-Step Process Explanation

### Phase 0: Initialization (User Input = 1)

**Location:** `main.py:main()` → `create_scenario(1)` → `scenarios.py:create_scenario_clean_approval()`

1. **Scenario Creation**
   - Generates unique loan number: `LN-XXXXXX` (6 random hex chars)
   - Creates borrower profile with excellent credentials:
     - John Smith, SSN: 123-45-6789, DOB: 1985-05-15
     - Employment: Software Engineer at Tech Corp (5 years)
     - Income: $8,500/month
     - Assets: $195,000 total ($25k checking, $50k savings, $120k 401k)
   - Creates property info: 456 Oak Avenue, Springfield, IL
   - Creates loan info: $320,000 loan, $400,000 purchase price, 6.5% rate
   - Saves to file system: `./loan_files/active/{loan_number}.json`
   - Returns loan number to main

2. **Workflow Initialization**
   - User confirms workflow execution
   - `run_workflow(loan_number)` is called
   - Creates Swarm team with 3 agents
   - Sets termination condition: `HandoffTermination(target="user") | TextMentionTermination("TERMINATE")`
   - Max turns: 50
   - Prepares initial task message with instructions

### Phase 1: Orchestrator Routes to Loan Processor

**Location:** `main.py:run_workflow()` → `team.run_stream(task=initial_task)`

3. **Orchestrator Agent Receives Task**
   - Reads initial task: "New loan application received..."
   - Analyzes instructions: "Route to loan_processor_agent to begin"
   - Makes decision: Handoff to loan_processor_agent
   - **HANDOFF MECHANISM**: Creates HandoffMessage(source="orchestrator_agent", target="loan_processor_agent")

### Phase 2: Loan Processor - Concurrent Document Collection

**Location:** `agents.py:loan_processor_agent` + `tools_loan_processor.py`

4. **Loan Processor Receives Handoff**
   - Agent system message guides behavior: "MAXIMIZE PARALLELISM"
   - Recognizes Phase 1 tasks (no dependencies)
   - Announces: "Launching Phase 1: 5 concurrent tasks..."

5. **Concurrent Tool Execution** (ALL happen simultaneously)

   a. **verify_loan_documents(loan_number)** [~1s]
      - File: `tools_loan_processor.py:34`
      - Acquires file lock: `file_manager.acquire_loan_lock(loan_number)`
      - Loads loan file from JSON
      - Checks required documents: URLA, Paystubs, W-2, Bank Statements, Purchase Agreement
      - For missing docs: Creates Document object with status REQUIRED
      - Updates loan status to DOCUMENTS_COMPLETE (all present in scenario 1)
      - Saves loan file
      - Releases lock
      - Returns: Document verification summary

   b. **order_credit_report(loan_number)** [~2-5s]
      - File: `tools_loan_processor.py:~200`
      - Acquires file lock
      - Calls external system: `CreditBureauSimulator.pull_credit_report(ssn)`
      - External system may throw exceptions:
        - `SystemTimeoutException` (10% chance)
        - `SystemMaintenanceException` (5% chance)
        - `InsufficientCreditHistoryException` (rare)
      - For Scenario 1: Returns credit score 750, clean history
      - Creates Document(document_type=CREDIT_REPORT, status=RECEIVED)
      - Updates loan status to CREDIT_ORDERED
      - Saves credit data to loan file
      - Releases lock
      - Returns: Credit report summary

   c. **order_appraisal(loan_number)** [~1-2s]
      - File: `tools_loan_processor.py:~300`
      - Acquires file lock
      - Calls: `AppraisalManagementSimulator.order_appraisal(property_address, loan_amount)`
      - Creates Appraisal object with status ORDERED
      - Updates loan status to APPRAISAL_ORDERED
      - Saves to loan file
      - Releases lock
      - Returns: Appraisal order confirmation

   d. **order_flood_certification(loan_number)** [~1s]
      - File: `tools_loan_processor.py:~400`
      - Acquires file lock
      - Calls: `FloodCertificationSimulator.check_flood_zone(zip_code)`
      - For ZIP 62702 (Springfield, IL): Returns Zone X (low risk)
      - Creates Document(document_type=FLOOD_CERTIFICATION)
      - Saves to loan file
      - Releases lock
      - Returns: Flood zone determination

   e. **verify_employment(loan_number)** [~1-3s]
      - File: `tools_loan_processor.py:~500`
      - Acquires file lock
      - Calls: `EmploymentVerificationSimulator.verify_employment(employer_phone, borrower_name)`
      - May throw `SystemTimeoutException` (10% chance)
      - For Scenario 1: Confirms 5 years at Tech Corp, $8,500/month income
      - Creates Document(document_type=EMPLOYMENT_VERIFICATION)
      - Saves to loan file
      - Releases lock
      - Returns: Employment verification summary

   **Key Point:** All 5 tools execute concurrently. Total time = max(individual times) ≈ 5 seconds, NOT sum(individual times) ≈ 15 seconds.

6. **Phase 1 Results Analysis**
   - Agent receives all 5 tool results
   - Summarizes: "All Phase 1 tasks complete. Results: Credit 750, employment verified, documents complete, flood zone low risk, appraisal ordered"

### Phase 3: Loan Processor - Sequential Ratio Calculation

7. **calculate_loan_ratios(loan_number)** [~1s]
   - File: `tools_loan_processor.py:~600`
   - **Dependency:** Requires credit report from Phase 1
   - Acquires file lock
   - Retrieves credit report data
   - Calculates financial metrics:
     - Principal & Interest (P&I): ~$2,050
     - Property tax: ~$333/month
     - Insurance: ~$100/month
     - HOA: $0
     - Total PITIA: ~$2,483
     - DTI: $2,483 / $8,500 = 29.2% (Excellent, <43% guideline)
     - LTV: $320,000 / $400,000 = 80% (Good)
     - Reserves: $75,000 / $2,483 = 30 months (Excellent, >6 months)
   - Updates loan_file.financial_metrics
   - Saves to loan file
   - Releases lock
   - Returns: Financial ratios summary

### Phase 4: Loan Processor - Submit to Underwriting

8. **submit_to_underwriting(loan_number)** [~1s]
   - File: `tools_loan_processor.py:~700`
   - **Dependency:** Requires calculate_loan_ratios and verify_loan_documents
   - Acquires file lock
   - Validates submission requirements:
     - Credit report present ✓
     - Financial ratios calculated ✓
     - Documents complete ✓
     - Employment verified ✓
   - Updates loan status to SUBMITTED_TO_UNDERWRITING
   - Records submission timestamp
   - Creates audit trail entry
   - Saves to loan file
   - Releases lock
   - Returns: Submission confirmation

9. **Loan Processor Handoff**
   - Agent announces: "All tasks complete. Submitting to underwriting."
   - **HANDOFF MECHANISM**: Creates HandoffMessage(source="loan_processor_agent", target="orchestrator_agent")

### Phase 5: Orchestrator Routes to Underwriter

10. **Orchestrator Receives Handoff**
    - Analyzes message: "Loan submitted to underwriting"
    - Checks loan status: SUBMITTED_TO_UNDERWRITING
    - Makes decision: Route to underwriter_agent
    - **HANDOFF MECHANISM**: Creates HandoffMessage(source="orchestrator_agent", target="underwriter_agent")

### Phase 6: Underwriter - Automated Underwriting

**Location:** `agents.py:underwriter_agent` + `tools_underwriter.py`

11. **Underwriter Receives Handoff**
    - Agent system message guides: "PARALLEL RISK ASSESSMENT"
    - Recognizes Phase 1 task (automated UW must go first)
    - Announces: "Running automated underwriting..."

12. **run_automated_underwriting(loan_number)** [~2-4s]
    - File: `tools_underwriter.py:~50`
    - Acquires file lock
    - Simulates Desktop Underwriter (DU) / Loan Prospector (LP)
    - Analyzes key factors:
      - Credit score: 750 → Score: 10/10
      - DTI: 29.2% → Score: 10/10
      - LTV: 80% → Score: 9/10
      - Reserves: 30 months → Score: 10/10
      - Employment: 5 years → Score: 10/10
    - Calculates overall risk score: 9.8/10 (Excellent)
    - Recommendation: "APPROVE/ACCEPT"
    - Risk level: LOW
    - Updates loan status to UNDERWRITING_INITIAL_REVIEW
    - Saves recommendation to loan file
    - Releases lock
    - Returns: AUS recommendation summary

### Phase 7: Underwriter - Concurrent Manual Reviews

13. **Concurrent Review Execution** (ALL happen simultaneously)

    a. **review_credit_profile(loan_number)** [~1s]
       - File: `tools_underwriter.py:~150`
       - Acquires file lock
       - Analyzes credit report:
         - Score 750 ✓ (≥620 required for conventional)
         - Payment history: 36 months on-time ✓
         - Derogatory marks: 0 ✓
         - Inquiries: 2 (normal) ✓
         - Debt: Manageable ✓
       - Conclusion: APPROVED - Excellent credit profile
       - Releases lock
       - Returns: Credit review summary

    b. **review_income_employment(loan_number)** [~1s]
       - File: `tools_underwriter.py:~200`
       - Acquires file lock
       - Analyzes employment:
         - Stability: 5 years same employer ✓
         - Income: $8,500/month verified ✓
         - DTI: 29.2% ✓ (≤50% max)
         - Employment type: W-2 Salary (most stable) ✓
         - Job continuity: No gaps ✓
       - Conclusion: APPROVED - Stable income and employment
       - Releases lock
       - Returns: Income review summary

    c. **review_assets_reserves(loan_number)** [~1s]
       - File: `tools_underwriter.py:~250`
       - Acquires file lock
       - Analyzes assets:
         - Liquid assets: $75,000 ✓
         - Reserves: 30 months ✓ (≥2 required)
         - Source: Verified bank statements ✓
         - Seasoning: Funds aged >2 months ✓
       - Conclusion: APPROVED - Excellent reserves
       - Releases lock
       - Returns: Assets review summary

    d. **review_property_appraisal(loan_number)** [~1s]
       - File: `tools_underwriter.py:~300`
       - Acquires file lock
       - Analyzes appraisal:
         - Appraised value: $400,000 ✓
         - Purchase price: $400,000 ✓
         - Variance: 0% (perfect match) ✓
         - Property condition: Good ✓
         - Comparable sales: Strong ✓
       - Conclusion: APPROVED - Value supported
       - Releases lock
       - Returns: Appraisal review summary

    **Key Point:** All 4 reviews execute concurrently. Total time ≈ 1 second.

14. **Phase 2 Results Synthesis**
    - Agent receives all 4 review results
    - Summarizes: "All reviews complete. Summary: Credit excellent, income verified and stable, assets sufficient with 30 months reserves, appraisal at value."

### Phase 8: Underwriter - Final Decision

15. **Decision Making Logic**
    - Evaluates all review results:
      - Credit: APPROVED ✓
      - Income: APPROVED ✓
      - Assets: APPROVED ✓
      - Property: APPROVED ✓
      - AUS: APPROVE/ACCEPT ✓
    - No conditions identified
    - No issues found
    - Decision: FINAL APPROVAL

16. **issue_final_approval(loan_number)** [~1s]
    - File: `tools_underwriter.py:~400`
    - Acquires file lock
    - Creates approval document:
      - Approval date: Current timestamp
      - Approved loan amount: $320,000
      - Approved rate: 6.5%
      - Conditions: None
      - Clear to close: YES
    - Updates loan status to CLEAR_TO_CLOSE
    - Records approval in audit trail
    - Generates approval letter
    - Saves to loan file
    - Releases lock
    - Returns: Final approval confirmation

17. **Underwriter Handoff**
    - Agent announces: "Final approval issued. Clear to close."
    - **HANDOFF MECHANISM**: Creates HandoffMessage(source="underwriter_agent", target="orchestrator_agent")

### Phase 9: Orchestrator Terminates Workflow

18. **Orchestrator Receives Final Handoff**
    - Analyzes message: "Final approval issued"
    - Checks loan status: CLEAR_TO_CLOSE
    - Recognizes completion condition
    - Responds: "The loan has been approved. Clear to close. TERMINATE"
    - **TERMINATION MECHANISM**: Message contains "TERMINATE" keyword

### Phase 10: Workflow Completion

19. **Main Loop Detects Termination**
    - File: `main.py:run_workflow()`
    - Detects TextMentionTermination("TERMINATE")
    - Exits team.run_stream()
    - Prints completion summary
    - Shows file location: `./loan_files/active/{loan_number}.json`
    - Displays storage statistics
    - Shows write count for loan
    - Returns control to user

---

## 3. Assertions for Correctness Validation

### Test File Structure

```python
# File: test_scenario_1_assertions.py

import pytest
import asyncio
import json
from pathlib import Path
from decimal import Decimal
from datetime import datetime

from models import LoanStatus, DocumentStatus, DocumentType
from file_manager import LoanFileManager
from scenarios import create_scenario_clean_approval
from main import run_workflow

file_manager = LoanFileManager()

class TestScenario1Assertions:
    """
    Comprehensive test suite for Scenario 1 (Clean Approval) with assertions
    to validate each phase of the workflow.
    """

    @pytest.fixture
    async def scenario_1_loan(self):
        """Create Scenario 1 and return loan number"""
        scenario_description = create_scenario_clean_approval()
        loan_number = scenario_description.split("Loan Number: ")[1].split("\n")[0]
        yield loan_number
        # Cleanup after test
        file_path = Path(f"./loan_files/active/{loan_number}.json")
        if file_path.exists():
            file_path.unlink()

    # ==================== PHASE 0: INITIALIZATION ====================

    def test_assertion_1_scenario_creation(self, scenario_1_loan):
        """
        ASSERTION 1: Scenario creation produces valid loan file

        Validates:
        - Loan file exists on disk
        - Loan file is valid JSON
        - Required fields are present
        - Initial status is APPLICATION_RECEIVED
        """
        loan_number = scenario_1_loan

        # Assert: File exists
        file_path = Path(f"./loan_files/active/{loan_number}.json")
        assert file_path.exists(), f"Loan file {loan_number}.json not created"

        # Assert: Valid JSON
        loan_file = file_manager.load_loan_file(loan_number)
        assert loan_file is not None, "Loan file could not be loaded"

        # Assert: Required fields present
        assert loan_file.loan_info.loan_number == loan_number
        assert loan_file.loan_info.loan_amount == Decimal("320000")
        assert loan_file.loan_info.purchase_price == Decimal("400000")

        # Assert: Initial status
        assert loan_file.status == LoanStatus.APPLICATION_RECEIVED

        # Assert: Borrower details
        assert len(loan_file.borrowers) == 1
        borrower = loan_file.borrowers[0]
        assert borrower.first_name == "John"
        assert borrower.last_name == "Smith"

        # Assert: Property details
        assert loan_file.property_info is not None
        assert loan_file.property_info.property_address.zip_code == "62702"

        print("✅ ASSERTION 1 PASSED: Scenario creation valid")

    # ==================== PHASE 1: DOCUMENT VERIFICATION ====================

    async def test_assertion_2_document_verification(self, scenario_1_loan):
        """
        ASSERTION 2: Document verification marks all docs complete

        Validates:
        - Documents status updated to COMPLETE
        - All required document types present
        - Loan status updated to DOCUMENTS_COMPLETE
        """
        loan_number = scenario_1_loan

        # Run workflow (or just the verification tool)
        from tools_loan_processor import verify_loan_documents
        result = await verify_loan_documents(loan_number)

        # Assert: Result indicates completion
        assert "DOCUMENTS COMPLETE" in result

        # Load updated loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: Status updated
        assert loan_file.status == LoanStatus.DOCUMENTS_COMPLETE

        # Assert: Required documents present
        required_types = [
            DocumentType.URLA,
            DocumentType.PAYSTUB,
            DocumentType.W2,
            DocumentType.BANK_STATEMENT,
            DocumentType.PURCHASE_AGREEMENT
        ]

        document_types = [doc.document_type for doc in loan_file.documents]
        for required_type in required_types:
            assert required_type in document_types, f"Missing {required_type}"

        print("✅ ASSERTION 2 PASSED: Document verification complete")

    # ==================== PHASE 2: CREDIT REPORT ====================

    async def test_assertion_3_credit_report_retrieval(self, scenario_1_loan):
        """
        ASSERTION 3: Credit report retrieved with expected score

        Validates:
        - Credit report document created
        - Credit score is 750 (as designed for Scenario 1)
        - Credit report saved to loan file
        - Loan status updated to CREDIT_ORDERED
        """
        loan_number = scenario_1_loan

        from tools_loan_processor import order_credit_report
        result = await order_credit_report(loan_number)

        # Assert: Credit report returned
        assert "Credit Score" in result
        assert "750" in result

        # Load updated loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: Credit report document present
        credit_docs = [d for d in loan_file.documents
                       if d.document_type == DocumentType.CREDIT_REPORT]
        assert len(credit_docs) > 0, "Credit report document not created"

        # Assert: Credit data in financial metrics
        assert loan_file.financial_metrics.credit_score is not None
        assert loan_file.financial_metrics.credit_score == 750

        print("✅ ASSERTION 3 PASSED: Credit report retrieved correctly")

    # ==================== PHASE 3: FLOOD CERTIFICATION ====================

    async def test_assertion_4_flood_certification(self, scenario_1_loan):
        """
        ASSERTION 4: Flood certification determines low risk

        Validates:
        - Flood certification document created
        - ZIP 62702 returns Zone X (low risk)
        - No flood insurance required
        """
        loan_number = scenario_1_loan

        from tools_loan_processor import order_flood_certification
        result = await order_flood_certification(loan_number)

        # Assert: Flood zone identified
        assert "Zone X" in result or "Low Risk" in result
        assert "no flood insurance required" in result.lower()

        # Load updated loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: Flood cert document present
        flood_docs = [d for d in loan_file.documents
                      if d.document_type == DocumentType.FLOOD_CERTIFICATION]
        assert len(flood_docs) > 0, "Flood certification not created"

        print("✅ ASSERTION 4 PASSED: Flood certification correct")

    # ==================== PHASE 4: EMPLOYMENT VERIFICATION ====================

    async def test_assertion_5_employment_verification(self, scenario_1_loan):
        """
        ASSERTION 5: Employment verified with stable history

        Validates:
        - Employment verification document created
        - 5 years employment confirmed
        - Income of $8,500/month verified
        """
        loan_number = scenario_1_loan

        from tools_loan_processor import verify_employment
        result = await verify_employment(loan_number)

        # Assert: Employment verified
        assert "verified" in result.lower()
        assert "5 years" in result or "5.0 years" in result

        # Load updated loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: Employment verification document present
        voe_docs = [d for d in loan_file.documents
                    if d.document_type == DocumentType.EMPLOYMENT_VERIFICATION]
        assert len(voe_docs) > 0, "Employment verification not created"

        print("✅ ASSERTION 5 PASSED: Employment verification successful")

    # ==================== PHASE 5: FINANCIAL RATIOS ====================

    async def test_assertion_6_financial_ratios(self, scenario_1_loan):
        """
        ASSERTION 6: Financial ratios calculated correctly

        Validates:
        - DTI <= 35% (excellent)
        - LTV = 80% (good)
        - Reserves >= 6 months (strong)
        - All ratios within guidelines
        """
        loan_number = scenario_1_loan

        # Must have credit report first
        from tools_loan_processor import order_credit_report, calculate_loan_ratios
        await order_credit_report(loan_number)

        result = await calculate_loan_ratios(loan_number)

        # Load updated loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: DTI calculated and within range
        assert loan_file.financial_metrics.dti_ratio is not None
        assert loan_file.financial_metrics.dti_ratio <= 36.0, \
            f"DTI {loan_file.financial_metrics.dti_ratio}% too high"

        # Assert: LTV calculated
        assert loan_file.financial_metrics.ltv_ratio is not None
        assert loan_file.financial_metrics.ltv_ratio == 80.0

        # Assert: Reserves calculated
        assert loan_file.financial_metrics.months_reserves is not None
        assert loan_file.financial_metrics.months_reserves >= 6.0, \
            f"Reserves {loan_file.financial_metrics.months_reserves} months insufficient"

        print("✅ ASSERTION 6 PASSED: Financial ratios correct")

    # ==================== PHASE 6: SUBMIT TO UNDERWRITING ====================

    async def test_assertion_7_submit_to_underwriting(self, scenario_1_loan):
        """
        ASSERTION 7: Loan successfully submitted to underwriting

        Validates:
        - Status updated to SUBMITTED_TO_UNDERWRITING
        - All prerequisites met
        - Submission timestamp recorded
        """
        loan_number = scenario_1_loan

        # Complete all prerequisite steps
        from tools_loan_processor import (
            verify_loan_documents, order_credit_report,
            calculate_loan_ratios, submit_to_underwriting
        )
        await verify_loan_documents(loan_number)
        await order_credit_report(loan_number)
        await calculate_loan_ratios(loan_number)

        result = await submit_to_underwriting(loan_number)

        # Assert: Submission successful
        assert "submitted" in result.lower()

        # Load updated loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: Status updated
        assert loan_file.status == LoanStatus.SUBMITTED_TO_UNDERWRITING

        # Assert: Audit trail has submission entry
        submission_entries = [
            entry for entry in loan_file.audit_trail
            if "submitted" in entry.action.lower()
        ]
        assert len(submission_entries) > 0, "Submission not recorded in audit trail"

        print("✅ ASSERTION 7 PASSED: Submitted to underwriting")

    # ==================== PHASE 7: AUTOMATED UNDERWRITING ====================

    async def test_assertion_8_automated_underwriting(self, scenario_1_loan):
        """
        ASSERTION 8: Automated underwriting returns APPROVE

        Validates:
        - AUS runs successfully
        - Recommendation is APPROVE/ACCEPT
        - Risk level is LOW
        - Score >= 9.0/10
        """
        loan_number = scenario_1_loan

        # Complete prerequisite steps
        from tools_loan_processor import (
            verify_loan_documents, order_credit_report,
            calculate_loan_ratios, submit_to_underwriting
        )
        from tools_underwriter import run_automated_underwriting

        await verify_loan_documents(loan_number)
        await order_credit_report(loan_number)
        await calculate_loan_ratios(loan_number)
        await submit_to_underwriting(loan_number)

        result = await run_automated_underwriting(loan_number)

        # Assert: AUS returned recommendation
        assert "APPROVE" in result or "ACCEPT" in result

        # Load updated loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: AUS data saved
        assert loan_file.automated_underwriting is not None
        assert loan_file.automated_underwriting.recommendation in ["APPROVE", "ACCEPT"]
        assert loan_file.automated_underwriting.risk_level == "LOW"

        # Assert: Score is excellent
        assert loan_file.automated_underwriting.overall_score >= 9.0

        print("✅ ASSERTION 8 PASSED: AUS approved loan")

    # ==================== PHASE 8: CREDIT REVIEW ====================

    async def test_assertion_9_credit_review(self, scenario_1_loan):
        """
        ASSERTION 9: Credit review passes without issues

        Validates:
        - Credit score >= 620
        - No derogatory marks
        - Payment history clean
        - Review conclusion: APPROVED
        """
        loan_number = scenario_1_loan

        # Setup
        from tools_loan_processor import order_credit_report
        from tools_underwriter import run_automated_underwriting, review_credit_profile

        await order_credit_report(loan_number)
        await run_automated_underwriting(loan_number)

        result = await review_credit_profile(loan_number)

        # Assert: Review passed
        assert "APPROVED" in result

        # Load updated loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: Credit score meets minimum
        assert loan_file.financial_metrics.credit_score >= 620

        print("✅ ASSERTION 9 PASSED: Credit review approved")

    # ==================== PHASE 9: INCOME/EMPLOYMENT REVIEW ====================

    async def test_assertion_10_income_review(self, scenario_1_loan):
        """
        ASSERTION 10: Income/employment review passes

        Validates:
        - Employment verified
        - DTI <= 50%
        - Income stable
        - Review conclusion: APPROVED
        """
        loan_number = scenario_1_loan

        # Setup
        from tools_loan_processor import (
            order_credit_report, calculate_loan_ratios, verify_employment
        )
        from tools_underwriter import (
            run_automated_underwriting, review_income_employment
        )

        await order_credit_report(loan_number)
        await calculate_loan_ratios(loan_number)
        await verify_employment(loan_number)
        await run_automated_underwriting(loan_number)

        result = await review_income_employment(loan_number)

        # Assert: Review passed
        assert "APPROVED" in result

        # Load updated loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: DTI within limits
        assert loan_file.financial_metrics.dti_ratio <= 50.0

        print("✅ ASSERTION 10 PASSED: Income review approved")

    # ==================== PHASE 10: ASSETS/RESERVES REVIEW ====================

    async def test_assertion_11_assets_review(self, scenario_1_loan):
        """
        ASSERTION 11: Assets/reserves review passes

        Validates:
        - Reserves >= 2 months
        - Assets verified
        - Review conclusion: APPROVED
        """
        loan_number = scenario_1_loan

        # Setup
        from tools_loan_processor import order_credit_report, calculate_loan_ratios
        from tools_underwriter import (
            run_automated_underwriting, review_assets_reserves
        )

        await order_credit_report(loan_number)
        await calculate_loan_ratios(loan_number)
        await run_automated_underwriting(loan_number)

        result = await review_assets_reserves(loan_number)

        # Assert: Review passed
        assert "APPROVED" in result

        # Load updated loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: Reserves meet minimum
        assert loan_file.financial_metrics.months_reserves >= 2.0

        print("✅ ASSERTION 11 PASSED: Assets review approved")

    # ==================== PHASE 11: APPRAISAL REVIEW ====================

    async def test_assertion_12_appraisal_review(self, scenario_1_loan):
        """
        ASSERTION 12: Appraisal review passes

        Validates:
        - Appraisal supports purchase price
        - Value adequate
        - Review conclusion: APPROVED
        """
        loan_number = scenario_1_loan

        # Setup
        from tools_loan_processor import order_appraisal, receive_appraisal
        from tools_underwriter import (
            run_automated_underwriting, review_property_appraisal
        )

        await order_appraisal(loan_number)
        # Simulate appraisal completion
        await receive_appraisal(loan_number)
        await run_automated_underwriting(loan_number)

        result = await review_property_appraisal(loan_number)

        # Assert: Review passed
        assert "APPROVED" in result

        print("✅ ASSERTION 12 PASSED: Appraisal review approved")

    # ==================== PHASE 12: FINAL APPROVAL ====================

    async def test_assertion_13_final_approval(self, scenario_1_loan):
        """
        ASSERTION 13: Final approval issued

        Validates:
        - Status updated to CLEAR_TO_CLOSE
        - Approval document created
        - No conditions issued
        - Workflow can terminate
        """
        loan_number = scenario_1_loan

        # Complete full workflow
        from tools_loan_processor import (
            verify_loan_documents, order_credit_report, calculate_loan_ratios,
            order_appraisal, receive_appraisal, order_flood_certification,
            verify_employment, submit_to_underwriting
        )
        from tools_underwriter import (
            run_automated_underwriting, review_credit_profile,
            review_income_employment, review_assets_reserves,
            review_property_appraisal, issue_final_approval
        )

        # Loan Processor Phase
        await verify_loan_documents(loan_number)
        await order_credit_report(loan_number)
        await order_appraisal(loan_number)
        await receive_appraisal(loan_number)
        await order_flood_certification(loan_number)
        await verify_employment(loan_number)
        await calculate_loan_ratios(loan_number)
        await submit_to_underwriting(loan_number)

        # Underwriter Phase
        await run_automated_underwriting(loan_number)
        await review_credit_profile(loan_number)
        await review_income_employment(loan_number)
        await review_assets_reserves(loan_number)
        await review_property_appraisal(loan_number)

        result = await issue_final_approval(loan_number)

        # Assert: Approval issued
        assert "CLEAR TO CLOSE" in result or "APPROVED" in result

        # Load final loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: Status is CLEAR_TO_CLOSE
        assert loan_file.status == LoanStatus.CLEAR_TO_CLOSE

        # Assert: No pending conditions
        pending_conditions = [
            c for c in loan_file.underwriting_conditions
            if c.status != "cleared"
        ]
        assert len(pending_conditions) == 0, \
            f"Found {len(pending_conditions)} uncleared conditions"

        # Assert: Approval recorded in audit trail
        approval_entries = [
            entry for entry in loan_file.audit_trail
            if "approval" in entry.action.lower()
        ]
        assert len(approval_entries) > 0, "Approval not in audit trail"

        print("✅ ASSERTION 13 PASSED: Final approval issued")

    # ==================== END-TO-END INTEGRATION TEST ====================

    async def test_assertion_14_end_to_end_workflow(self):
        """
        ASSERTION 14: Complete end-to-end workflow for Scenario 1

        Validates:
        - Workflow completes without errors
        - All phases execute in correct order
        - Final status is CLEAR_TO_CLOSE
        - Termination occurs naturally
        - Total execution time reasonable (<60 seconds)
        """
        import time

        # Create scenario
        scenario_description = create_scenario_clean_approval()
        loan_number = scenario_description.split("Loan Number: ")[1].split("\n")[0]

        start_time = time.time()

        # Run full workflow
        try:
            await run_workflow(loan_number)
        except Exception as e:
            pytest.fail(f"Workflow failed with exception: {str(e)}")

        end_time = time.time()
        duration = end_time - start_time

        # Assert: Completed in reasonable time
        assert duration < 60.0, f"Workflow took {duration}s (>60s limit)"

        # Load final loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: Final status correct
        assert loan_file.status == LoanStatus.CLEAR_TO_CLOSE

        # Assert: Audit trail shows complete workflow
        assert len(loan_file.audit_trail) >= 10, \
            "Audit trail too short, workflow incomplete"

        # Assert: All required documents present
        assert len(loan_file.documents) >= 5

        # Assert: Financial metrics calculated
        assert loan_file.financial_metrics.dti_ratio is not None
        assert loan_file.financial_metrics.ltv_ratio is not None
        assert loan_file.financial_metrics.months_reserves is not None

        print(f"✅ ASSERTION 14 PASSED: End-to-end workflow complete in {duration:.1f}s")

        # Cleanup
        Path(f"./loan_files/active/{loan_number}.json").unlink()

    # ==================== CONCURRENCY VALIDATION ====================

    async def test_assertion_15_concurrent_execution(self, scenario_1_loan):
        """
        ASSERTION 15: Concurrent tasks execute in parallel

        Validates:
        - Phase 1 tasks complete in ~5s, NOT ~15s (sum of individual times)
        - Phase 2 reviews complete in ~1s, NOT ~4s
        - File locking prevents race conditions
        - No data corruption from concurrent writes
        """
        import time
        loan_number = scenario_1_loan

        # Test Loan Processor Phase 1 concurrency
        from tools_loan_processor import (
            verify_loan_documents, order_credit_report, order_appraisal,
            order_flood_certification, verify_employment
        )

        start = time.time()

        # Execute all 5 tasks "concurrently" (simulated)
        await asyncio.gather(
            verify_loan_documents(loan_number),
            order_credit_report(loan_number),
            order_appraisal(loan_number),
            order_flood_certification(loan_number),
            verify_employment(loan_number)
        )

        duration = time.time() - start

        # Assert: Completed in parallel time, not sequential
        # Expected: ~5s (max of individual times)
        # Sequential would be: ~10-12s (sum of times)
        assert duration < 8.0, \
            f"Phase 1 took {duration}s, suggests sequential execution"

        print(f"✅ ASSERTION 15 PASSED: Concurrent execution in {duration:.1f}s")

    # ==================== FILE INTEGRITY VALIDATION ====================

    async def test_assertion_16_file_integrity(self, scenario_1_loan):
        """
        ASSERTION 16: File operations maintain data integrity

        Validates:
        - No data loss from concurrent writes
        - Audit trail is complete and ordered
        - No duplicate entries
        - File locks prevent corruption
        """
        loan_number = scenario_1_loan

        # Perform multiple operations
        from tools_loan_processor import (
            verify_loan_documents, order_credit_report, order_flood_certification
        )

        await verify_loan_documents(loan_number)
        await order_credit_report(loan_number)
        await order_flood_certification(loan_number)

        # Load loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: Audit trail entries are unique
        audit_actions = [entry.action for entry in loan_file.audit_trail]
        assert len(audit_actions) == len(set(audit_actions)), \
            "Duplicate audit trail entries found"

        # Assert: Audit trail is time-ordered
        timestamps = [entry.timestamp for entry in loan_file.audit_trail]
        assert timestamps == sorted(timestamps), "Audit trail not time-ordered"

        # Assert: No document duplicates
        doc_ids = [doc.document_id for doc in loan_file.documents]
        assert len(doc_ids) == len(set(doc_ids)), "Duplicate documents found"

        print("✅ ASSERTION 16 PASSED: File integrity maintained")


# ==================== RUN ALL ASSERTIONS ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
```

### Summary of Assertions

| # | Assertion | Phase | What It Validates |
|---|-----------|-------|-------------------|
| 1 | Scenario Creation | 0 | Loan file created with correct data |
| 2 | Document Verification | 1 | All documents marked complete |
| 3 | Credit Report | 2 | Credit score 750 retrieved |
| 4 | Flood Certification | 3 | Zone X (low risk) determined |
| 5 | Employment Verification | 4 | 5 years employment confirmed |
| 6 | Financial Ratios | 5 | DTI ≤35%, LTV 80%, Reserves ≥6mo |
| 7 | Submit to UW | 6 | Status SUBMITTED_TO_UNDERWRITING |
| 8 | Automated UW | 7 | AUS returns APPROVE/LOW RISK |
| 9 | Credit Review | 8 | Manual review approves credit |
| 10 | Income Review | 9 | Manual review approves income |
| 11 | Assets Review | 10 | Manual review approves assets |
| 12 | Appraisal Review | 11 | Manual review approves property |
| 13 | Final Approval | 12 | Status CLEAR_TO_CLOSE, no conditions |
| 14 | End-to-End | All | Complete workflow <60s |
| 15 | Concurrency | 2,8 | Parallel execution verified |
| 16 | File Integrity | All | No corruption from concurrent access |

---

## 4. Autogen Framework Mechanics

### 4.1 Overview

The system uses **Autogen AgentChat** with the **Swarm** team pattern. Key components:

1. **Agents**: AssistantAgent instances with specific roles
2. **Handoffs**: Inter-agent communication via HandoffMessage
3. **Tools**: Function tools that agents can call
4. **Termination**: Conditions that end the workflow
5. **Model Client**: OpenAI GPT-4o/mini backend

### 4.2 Agent Initialization

**File:** `agents.py`

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Create model client (shared)
model_client4o = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=API_KEY,
)

# Create orchestrator agent
orchestrator_agent = AssistantAgent(
    name="orchestrator_agent",
    model_client=model_client4o,
    handoffs=["loan_processor_agent", "underwriter_agent"],  # Can handoff to these
    system_message="You are the orchestrator...",  # Instructions
    tools=[]  # No tools, just routing
)

# Create loan processor agent
loan_processor_agent = AssistantAgent(
    name="loan_processor_agent",
    model_client=model_client4o,
    handoffs=["orchestrator_agent"],  # Can only handoff back to orchestrator
    system_message="You are a loan processor...",
    tools=[  # Tools this agent can call
        verify_loan_documents,
        order_credit_report,
        calculate_loan_ratios,
        submit_to_underwriting,
        # ... more tools
    ]
)

# Create underwriter agent
underwriter_agent = AssistantAgent(
    name="underwriter_agent",
    model_client=model_client4o,
    handoffs=["orchestrator_agent"],
    system_message="You are an underwriter...",
    tools=[
        run_automated_underwriting,
        review_credit_profile,
        issue_final_approval,
        deny_loan,
        # ... more tools
    ]
)
```

### 4.3 Team Creation

**File:** `main.py`

```python
from autogen_agentchat.teams import Swarm
from autogen_agentchat.conditions import HandoffTermination, TextMentionTermination

# Create termination conditions
termination = (
    HandoffTermination(target="user") |  # Terminate if agent hands off to user
    TextMentionTermination("TERMINATE")  # Terminate if message contains "TERMINATE"
)

# Create Swarm team
team = Swarm(
    participants=[orchestrator_agent, loan_processor_agent, underwriter_agent],
    termination_condition=termination,
    max_turns=50  # Safety limit
)
```

### 4.4 Workflow Execution

**File:** `main.py:run_workflow()`

```python
# Prepare initial task
initial_task = f"""
New loan application received and ready for processing.
Loan Number: {loan_number}
Route to loan_processor_agent to begin.
"""

# Start the team (asynchronous streaming)
task_result = await Console(team.run_stream(task=initial_task))
```

**What happens:**
1. `team.run_stream()` sends `initial_task` to the first agent (determined by Swarm logic, typically orchestrator)
2. Orchestrator agent receives the message
3. Agent's LLM (GPT-4o) processes the message with its system_message as context
4. LLM decides to handoff to loan_processor_agent
5. Swarm framework routes to loan_processor_agent
6. Loop continues until termination condition met

### 4.5 How Handoffs Work

**Mechanism:** HandoffMessage

**Example Flow:**

1. **Orchestrator decides to handoff:**
   ```python
   # Inside orchestrator agent's LLM response:
   # "I will transfer this to the loan processor agent."
   # Autogen detects the handoff intent and creates:
   HandoffMessage(
       source="orchestrator_agent",
       target="loan_processor_agent",
       content="New loan application received. Loan Number: LN-ABC123"
   )
   ```

2. **Swarm routes the message:**
   - Checks if "loan_processor_agent" is in orchestrator's `handoffs` list ✓
   - Finds loan_processor_agent in team participants ✓
   - Delivers message to loan_processor_agent

3. **Loan processor receives handoff:**
   - Reads message content: "New loan application..."
   - Reads own system_message: "You are a loan processor..."
   - LLM decides next action: Call tools

4. **After completing work, loan processor hands back:**
   ```python
   HandoffMessage(
       source="loan_processor_agent",
       target="orchestrator_agent",
       content="All tasks complete. Submitted to underwriting."
   )
   ```

**Key Points:**
- Handoffs are **explicit**: Agent must list valid targets in `handoffs` parameter
- Handoffs are **controlled by LLM**: The model decides when to handoff based on system message instructions
- Handoffs are **validated**: Swarm checks handoff is allowed before routing

### 4.6 How Tool Calls Work

**Mechanism:** Function Tools

**Example Flow:**

1. **Agent has tools registered:**
   ```python
   loan_processor_agent = AssistantAgent(
       ...,
       tools=[order_credit_report, verify_loan_documents]
   )
   ```

2. **Agent decides to call tool:**
   - LLM reads system message: "Launch Phase 1: 5 concurrent tasks..."
   - LLM generates tool call request:
   ```json
   {
       "tool_calls": [
           {
               "name": "order_credit_report",
               "arguments": {
                   "loan_number": "LN-ABC123"
               }
           }
       ]
   }
   ```

3. **Autogen executes tool:**
   - Finds function `order_credit_report` in agent's tools
   - Calls function: `order_credit_report("LN-ABC123")`
   - Function executes (async):
     ```python
     async def order_credit_report(loan_number: str) -> str:
         async with file_manager.acquire_loan_lock(loan_number):
             # ... acquire lock
             loan_file = file_manager.load_loan_file(loan_number)
             # ... call external system
             credit_data = CreditBureauSimulator.pull_credit_report(ssn)
             # ... save to loan file
             file_manager.save_loan_file(loan_file)
         return "Credit score: 750, ..."
     ```

4. **Tool result returned to agent:**
   - Function returns string: "Credit score: 750, ..."
   - Autogen adds result to conversation context
   - LLM sees tool result and continues decision-making

5. **Agent can call multiple tools:**
   ```json
   {
       "tool_calls": [
           {"name": "order_credit_report", "arguments": {"loan_number": "LN-ABC123"}},
           {"name": "order_appraisal", "arguments": {"loan_number": "LN-ABC123"}},
           {"name": "order_flood_certification", "arguments": {"loan_number": "LN-ABC123"}}
       ]
   }
   ```
   - **Concurrent execution:** Autogen executes all tool calls in parallel using asyncio
   - All results returned together
   - Agent sees all results and makes next decision

**Key Points:**
- Tools are **async functions**: Support concurrent execution
- Tools are **registered per agent**: Only that agent can call them
- Tools use **file locking**: `file_manager.acquire_loan_lock()` prevents race conditions
- Tools return **strings**: Results are added to conversation context for LLM

### 4.7 Concurrent Tool Execution

**How Autogen handles concurrent tool calls:**

1. **Agent makes multiple tool call requests:**
   ```python
   # LLM generates:
   tool_calls = [
       call_1 = {"name": "order_credit_report", "arguments": {...}},
       call_2 = {"name": "order_appraisal", "arguments": {...}},
       call_3 = {"name": "verify_employment", "arguments": {...}}
   ]
   ```

2. **Autogen executes concurrently:**
   ```python
   # Autogen internal code (simplified):
   results = await asyncio.gather(
       order_credit_report(**call_1["arguments"]),
       order_appraisal(**call_2["arguments"]),
       verify_employment(**call_3["arguments"]),
       return_exceptions=True
   )
   ```

3. **File locking prevents conflicts:**
   ```python
   # Inside each tool:
   async with file_manager.acquire_loan_lock(loan_number):
       # Only one tool can access this loan file at a time
       loan_file = file_manager.load_loan_file(loan_number)
       # ... modify loan_file
       file_manager.save_loan_file(loan_file)
   # Lock released automatically
   ```

   **Lock mechanism** (`file_manager.py`):
   ```python
   class LoanFileManager:
       def __init__(self):
           self._locks = {}  # {loan_number: asyncio.Lock}

       @contextmanager
       async def acquire_loan_lock(self, loan_number: str):
           if loan_number not in self._locks:
               self._locks[loan_number] = asyncio.Lock()

           async with self._locks[loan_number]:
               yield  # Execute tool code
           # Lock released here
   ```

**Result:**
- Tools execute in parallel (total time = max time, not sum time)
- No data corruption (locks prevent concurrent writes)
- No race conditions (one tool at a time per loan file)

### 4.8 Termination Detection

**File:** `main.py:run_workflow()`

```python
# Set up termination condition
termination = HandoffTermination(target="user") | TextMentionTermination("TERMINATE")

# Run workflow
task_result = await Console(team.run_stream(task=initial_task))

# Check termination reason
last_message = task_result.messages[-1]

if isinstance(last_message, HandoffMessage) and last_message.target == "user":
    # Agent handed off to user (needs human input)
    user_message = input("\n👤 User input needed: ")
    # Continue workflow...
elif "TERMINATE" in last_message.content:
    # Workflow complete
    print("✅ WORKFLOW COMPLETED")
```

**How orchestrator terminates:**

```python
# orchestrator_agent system_message instructs:
"""
ALWAYS TERMINATE ON:
- Final approval → "The loan has been approved. Clear to close. TERMINATE"
- Loan denial → "The loan has been denied. Adverse action notice issued. TERMINATE"
"""

# When underwriter hands back with approval:
orchestrator_agent receives: HandoffMessage(
    source="underwriter_agent",
    content="Final approval issued. Status: CLEAR_TO_CLOSE"
)

# Orchestrator LLM responds:
"The loan has been approved. Clear to close. TERMINATE"

# Autogen detects "TERMINATE" in response
# TextMentionTermination condition triggered
# team.run_stream() returns
```

### 4.9 System Message Impact

**System messages control agent behavior:**

1. **Orchestrator:** Simple routing logic
   ```python
   system_message="""You are the orchestrator agent.
   Your role is to route efficiently, detect problems, and TERMINATE when necessary.

   ALWAYS TERMINATE ON:
   - Final approval → "TERMINATE"
   - Loan denial → "TERMINATE"
   """
   ```

2. **Loan Processor:** Emphasizes concurrency
   ```python
   system_message="""You are a Loan Processor with concurrent task management.

   CORE PRINCIPLE: MAXIMIZE PARALLELISM

   PHASE 1 - CONCURRENT LAUNCH (no dependencies, run ALL in parallel):
   ├─ verify_loan_documents()
   ├─ order_credit_report()
   ├─ order_appraisal()
   ├─ order_flood_certification()
   └─ verify_employment()

   When you receive a NEW loan file:
   1. SAY: "Launching Phase 1: 5 concurrent tasks..."
   2. CALL ALL 5 Phase 1 tools WITHOUT waiting between calls
   """
   ```

   **Result:** LLM learns to make multiple tool calls simultaneously

3. **Underwriter:** Structured review process
   ```python
   system_message="""You are an Underwriter with concurrent review capabilities.

   PHASE 1 - INITIAL (sequential, must go first):
   └─ run_automated_underwriting()

   PHASE 2 - CONCURRENT REVIEWS (run ALL in parallel after Phase 1):
   ├─ review_credit_profile()
   ├─ review_income_employment()
   ├─ review_assets_reserves()
   └─ review_property_appraisal()

   PHASE 3 - DECISION (sequential, after Phase 2):
   └─ issue_final_approval() OR deny_loan()
   """
   ```

   **Result:** LLM follows structured workflow with dependencies

### 4.10 Complete Interaction Example

**Scenario 1 - Clean Approval (Simplified)**

```
[main.py] Start workflow with initial_task
     ↓
[team.run_stream()] Route to orchestrator_agent
     ↓
[orchestrator_agent] Receives: "New loan application... Route to loan_processor"
     ↓ (LLM decides)
[orchestrator_agent] Generates: HANDOFF → loan_processor_agent
     ↓
[Swarm] Routes HandoffMessage to loan_processor_agent
     ↓
[loan_processor_agent] Receives handoff message
     ↓ (LLM reads system message: "Launch 5 concurrent tasks")
[loan_processor_agent] Generates 5 tool calls:
     ├─ verify_loan_documents(LN-ABC123)
     ├─ order_credit_report(LN-ABC123)
     ├─ order_appraisal(LN-ABC123)
     ├─ order_flood_certification(LN-ABC123)
     └─ verify_employment(LN-ABC123)
     ↓
[Autogen] Executes asyncio.gather() on all 5 tools (parallel)
     ↓
[Each tool] Acquires file lock → Modifies loan file → Releases lock
     ↓
[Autogen] Collects all 5 results and returns to agent
     ↓
[loan_processor_agent] Sees results, decides to calculate ratios
     ↓ (LLM generates tool call)
[loan_processor_agent] Calls: calculate_loan_ratios(LN-ABC123)
     ↓
[Autogen] Executes tool, returns result
     ↓
[loan_processor_agent] Sees result, decides to submit
     ↓ (LLM generates tool call)
[loan_processor_agent] Calls: submit_to_underwriting(LN-ABC123)
     ↓
[Autogen] Executes tool, returns result
     ↓
[loan_processor_agent] Decides work complete
     ↓ (LLM generates handoff)
[loan_processor_agent] Generates: HANDOFF → orchestrator_agent
     ↓
[Swarm] Routes HandoffMessage to orchestrator_agent
     ↓
[orchestrator_agent] Receives: "Submitted to underwriting"
     ↓ (LLM decides)
[orchestrator_agent] Generates: HANDOFF → underwriter_agent
     ↓
[Swarm] Routes HandoffMessage to underwriter_agent
     ↓
[underwriter_agent] Receives handoff message
     ↓ (LLM reads system message: "Run AUS first")
[underwriter_agent] Calls: run_automated_underwriting(LN-ABC123)
     ↓
[Autogen] Executes tool, returns result: "APPROVE"
     ↓
[underwriter_agent] Sees APPROVE, decides to run 4 reviews
     ↓ (LLM generates 4 tool calls)
[underwriter_agent] Generates 4 tool calls:
     ├─ review_credit_profile(LN-ABC123)
     ├─ review_income_employment(LN-ABC123)
     ├─ review_assets_reserves(LN-ABC123)
     └─ review_property_appraisal(LN-ABC123)
     ↓
[Autogen] Executes asyncio.gather() on all 4 tools (parallel)
     ↓
[Each tool] Acquires file lock → Reviews data → Releases lock
     ↓
[Autogen] Collects all 4 results: All "APPROVED"
     ↓
[underwriter_agent] Sees all approved, decides final approval
     ↓ (LLM generates tool call)
[underwriter_agent] Calls: issue_final_approval(LN-ABC123)
     ↓
[Autogen] Executes tool, updates status to CLEAR_TO_CLOSE
     ↓
[underwriter_agent] Decides work complete
     ↓ (LLM generates handoff)
[underwriter_agent] Generates: HANDOFF → orchestrator_agent
     ↓
[Swarm] Routes HandoffMessage to orchestrator_agent
     ↓
[orchestrator_agent] Receives: "Final approval issued. Clear to close."
     ↓ (LLM reads system message: "ALWAYS TERMINATE ON final approval")
[orchestrator_agent] Generates: "The loan has been approved. Clear to close. TERMINATE"
     ↓
[Autogen] Detects TextMentionTermination("TERMINATE")
     ↓
[team.run_stream()] Returns task_result
     ↓
[main.py] Prints completion summary and exits
```

---

## 5. Key Insights

### 5.1 Why This Architecture Works

1. **Separation of Concerns**
   - Orchestrator: Pure routing logic
   - Loan Processor: Document collection and verification
   - Underwriter: Risk assessment and decision-making

2. **Concurrent Execution**
   - Independent tasks run in parallel
   - Reduces total workflow time by ~60%
   - File locking prevents data corruption

3. **Clear Dependencies**
   - System messages explicitly define task dependencies
   - LLM learns to respect dependency order
   - Sequential tasks run after dependencies met

4. **Autonomous Operation**
   - No human intervention required (for Scenario 1)
   - Agents make decisions based on data
   - Termination is automatic

5. **Robust Error Handling**
   - External systems can fail (timeouts, maintenance)
   - Tools handle exceptions gracefully
   - Workflow continues with partial data

### 5.2 Potential Issues to Watch

1. **LLM Non-Determinism**
   - Different runs may produce slightly different results
   - Tool calls might vary in order
   - Solution: Use assertions to validate outcomes, not exact steps

2. **Concurrency Challenges**
   - File locking adds latency
   - Too many concurrent writes can cause contention
   - Solution: Minimize lock duration, batch updates when possible

3. **Handoff Loops**
   - Agents might handoff back and forth indefinitely
   - Solution: Orchestrator tracks handoff count and terminates at limit

4. **Tool Call Failures**
   - External systems might fail repeatedly
   - Solution: Orchestrator detects persistent errors and terminates

---

## 6. Running the Test Suite

```bash
# Install dependencies
pip install pytest pytest-asyncio

# Run all assertions
python test_scenario_1_assertions.py

# Run specific assertion
pytest test_scenario_1_assertions.py::TestScenario1Assertions::test_assertion_13_final_approval -v

# Run end-to-end test
pytest test_scenario_1_assertions.py::TestScenario1Assertions::test_assertion_14_end_to_end_workflow -v
```

---

## Conclusion

This mortgage underwriting system demonstrates a sophisticated multi-agent workflow using Autogen's Swarm pattern. The key innovations are:

1. **Concurrent task execution** reducing workflow time
2. **Thread-safe file operations** preventing data corruption
3. **Structured agent roles** with clear responsibilities
4. **Explicit dependency management** ensuring correct execution order
5. **Autonomous decision-making** without human intervention

The assertion suite provides comprehensive validation at each phase, ensuring the system behaves as expected for the clean approval scenario.
