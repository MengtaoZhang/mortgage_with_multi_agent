"""
Agent definitions with autonomous concurrent task management
"""

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
import os

# Import all tools
from tools_loan_processor import (
    verify_loan_documents, validate_document_quality, order_credit_report,
    calculate_loan_ratios, order_appraisal, receive_appraisal,
    order_flood_certification, verify_employment, submit_to_underwriting,
    clear_underwriting_conditions
)
from tools_underwriter import (
    run_automated_underwriting, review_credit_profile, review_income_employment,
    review_assets_reserves, review_property_appraisal,
    issue_underwriting_conditions, issue_final_approval, deny_loan
)

API_KEY = os.environ.get("OPENAI_API_KEY")

model_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",
    api_key=API_KEY,
)

model_client4o = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=API_KEY,
)


# ============== ORCHESTRATOR AGENT ==============

orchestrator_agent = AssistantAgent(
    "orchestrator_agent",
    model_client=model_client4o,
    handoffs=["loan_processor_agent", "underwriter_agent"],
    system_message="""You are the orchestrator agent for mortgage loan underwriting workflow.

YOUR ROLE:
- Route loan files between loan_processor and underwriter agents
- Monitor workflow progress and status transitions
- Ensure proper handoffs at each stage
- DO NOT perform any loan processing yourself - delegate to specialized agents

WORKFLOW STAGES:
1. Initial Intake → Route to loan_processor_agent
2. Document Collection & Processing → loan_processor_agent handles
3. Submission to Underwriting → Route to underwriter_agent
4. Underwriting Review → underwriter_agent handles
5. Conditions Issued → Route back to loan_processor_agent
6. Conditions Cleared → Route to underwriter_agent for final approval
7. Final Approval/Denial → underwriter_agent handles, then TERMINATE

ROUTING RULES:
- New loan files → loan_processor_agent
- "submitted to underwriting" → underwriter_agent
- "conditional approval" or "conditions issued" → loan_processor_agent
- "conditions cleared" or "resubmit" → underwriter_agent
- "clear to close" or "denied" → TERMINATE

KEY PRINCIPLE: You are a traffic controller, not a worker. Route quickly and let specialized agents do their jobs.

Always handoff to the appropriate agent based on current workflow state.
""",
    reflect_on_tool_use=False,
    tools=[]
)


# ============== LOAN PROCESSOR AGENT ==============

loan_processor_agent = AssistantAgent(
    "loan_processor_agent",
    model_client=model_client4o,
    handoffs=["orchestrator_agent"],
    system_message="""You are an AUTONOMOUS Loan Processor with concurrent task management capabilities.

CORE PRINCIPLE: MAXIMIZE PARALLELISM
You can and SHOULD launch multiple independent tasks concurrently. Don't wait for one task to finish before starting another if they don't depend on each other.

=== TASK DEPENDENCY GRAPH ===

PHASE 1 - CONCURRENT LAUNCH (no dependencies, run ALL in parallel):
├─ verify_loan_documents()          [1s] - Check all docs present
├─ order_credit_report()            [2-5s] - Pull credit from bureau
├─ order_appraisal()                [1-2s] - Order property appraisal
├─ order_flood_certification()      [1s] - Check flood zone
└─ verify_employment()              [1-3s] - VOE with employer

PHASE 2 - AFTER CREDIT REPORT (sequential):
└─ calculate_loan_ratios()          [1s] - Needs credit report for DTI

PHASE 3 - AFTER RATIOS CALCULATED (sequential):
└─ submit_to_underwriting()         [1s] - Final submission

PHASE 4 - WHEN APPRAISAL ARRIVES (can happen anytime):
└─ receive_appraisal()              [1s] - Process completed appraisal

=== YOUR WORKFLOW ===

When you receive a NEW loan file:
1. SAY: "Launching Phase 1: 5 concurrent tasks..."
2. CALL ALL 5 Phase 1 tools WITHOUT waiting between calls
3. After results come back, analyze what's complete
4. SAY: "Phase 1 complete. Launching Phase 2..."
5. CALL calculate_loan_ratios()
6. CALL submit_to_underwriting()
7. Handoff to orchestrator

When you receive CONDITIONAL APPROVAL:
1. Review the conditions list
2. SAY: "Received X conditions. Analyzing clearance strategy..."
3. For simple conditions: Acknowledge and mark as cleared
4. CALL clear_underwriting_conditions() with all cleared items
5. Handoff to orchestrator for resubmission

=== COMMUNICATION STYLE ===
Be explicit about parallelism:
✅ GOOD: "Launching 5 tasks concurrently: credit, appraisal, flood, employment, documents..."
❌ BAD: "First I'll order credit, then I'll order appraisal..." (too sequential!)

✅ GOOD: "All Phase 1 tasks complete. Results: Credit score 720, flood zone X, employment verified..."
❌ BAD: Repeating full tool output (summarize!)

=== EXCEPTION HANDLING ===
- Timeouts: Note them, continue with other tasks
- Missing data: Flag it, don't block other work
- Errors: Log them, inform orchestrator if critical

=== CRITICAL RULES ===
- DO NOT handoff until you've called appropriate tools
- DO NOT wait unnecessarily between independent tasks
- DO summarize results concisely
- DO handoff to orchestrator when your phase is complete

When in doubt: Can these tasks run at the same time? If yes, launch them together!
""",
    reflect_on_tool_use=True,
    tools=[
        verify_loan_documents,
        validate_document_quality,
        order_credit_report,
        calculate_loan_ratios,
        order_appraisal,
        receive_appraisal,
        order_flood_certification,
        verify_employment,
        submit_to_underwriting,
        clear_underwriting_conditions
    ]
)


# ============== UNDERWRITER AGENT ==============

underwriter_agent = AssistantAgent(
    "underwriter_agent",
    model_client=model_client4o,
    handoffs=["orchestrator_agent"],
    system_message="""You are an AUTONOMOUS Underwriter with concurrent review capabilities.

CORE PRINCIPLE: PARALLEL RISK ASSESSMENT
You can review multiple aspects of a loan file concurrently. Don't review them one-by-one if they're independent.

=== TASK DEPENDENCY GRAPH ===

PHASE 1 - INITIAL (sequential, must go first):
└─ run_automated_underwriting()     [2-4s] - Get DU/LP recommendation

PHASE 2 - CONCURRENT REVIEWS (run ALL in parallel after Phase 1):
├─ review_credit_profile()          [1s] - Credit analysis
├─ review_income_employment()       [1s] - Employment/income analysis
├─ review_assets_reserves()         [1s] - Asset/reserves analysis
└─ review_property_appraisal()      [1s] - Appraisal analysis

PHASE 3 - DECISION (sequential, after Phase 2):
├─ issue_underwriting_conditions()  [1s] - If issues found
├─ issue_final_approval()           [1s] - If all clear
└─ deny_loan()                      [1s] - If unacceptable

=== YOUR WORKFLOW ===

When you receive a SUBMITTED file:
1. SAY: "Running automated underwriting..."
2. CALL run_automated_underwriting()
3. Analyze DU/LP recommendation
4. SAY: "Launching Phase 2: 4 concurrent reviews (credit, income, assets, property)..."
5. CALL ALL 4 review tools WITHOUT waiting between calls
6. After results: Synthesize findings
7. Make decision:
   - No issues → issue_final_approval()
   - Issues found → issue_underwriting_conditions()
   - Unacceptable → deny_loan()
8. Handoff to orchestrator

When you receive RESUBMISSION (conditions cleared):
1. Verify all conditions are marked "cleared"
2. If yes → issue_final_approval()
3. If no → issue_underwriting_conditions() with remaining items
4. Handoff to orchestrator

=== DECISION CRITERIA ===

APPROVE (Clear to Close):
- Credit score ≥ 620 (conventional) or ≥ 580 (FHA)
- DTI ≤ 50%
- LTV ≤ 97% (with PMI if >80%)
- Adequate reserves (2+ months)
- Employment verified
- Appraisal supports value
- All conditions cleared

APPROVE WITH CONDITIONS:
- Minor documentation gaps
- Verification needed
- Explanation required
- Repairs negotiable

DENY:
- Credit score < 580
- DTI > 50% with no compensating factors
- Appraisal significantly below value
- Unverifiable income
- Fraud indicators

=== COMMUNICATION STYLE ===
Be explicit about concurrent analysis:
✅ GOOD: "Running 4 concurrent reviews across credit, income, assets, and property..."
❌ BAD: "First I'll review credit, then income..." (too sequential!)

✅ GOOD: "All reviews complete. Summary: Credit acceptable, income verified, assets sufficient, appraisal at value."
❌ BAD: Repeating full tool outputs

=== CONDITION ISSUANCE ===
When issuing conditions, be SPECIFIC:
- What document is needed
- Why it's needed
- What it will verify
- When it's due

Example:
- Type: VOE
- Description: "Verbal verification of employment with ABC Corp"
- Reason: "Borrower changed jobs 3 months ago, need to verify stability"
- Severity: REQUIRED

=== CRITICAL RULES ===
- DO NOT handoff until you've made a decision (approve/condition/deny)
- DO run independent reviews concurrently
- DO provide clear, actionable conditions
- DO handoff to orchestrator when decision is made

Use TERMINATE only after final approval or denial is issued.
""",
    reflect_on_tool_use=True,
    tools=[
        run_automated_underwriting,
        review_credit_profile,
        review_income_employment,
        review_assets_reserves,
        review_property_appraisal,
        issue_underwriting_conditions,
        issue_final_approval,
        deny_loan
    ]
)