"""
Agent Pool Architecture: Multiple loan-processors and underwriters

This creates multiple instances of loan_processor and underwriter agents
to handle concurrent loan processing with direct message assignment.
"""

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
import os

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


# ========== AGENT POOL CONFIGURATION ==========

NUM_LOAN_PROCESSORS = 3  # Can process 3 loans concurrently
NUM_UNDERWRITERS = 3      # Can underwrite 3 loans concurrently


# ========== LOAN PROCESSOR SYSTEM MESSAGE ==========

LOAN_PROCESSOR_SYSTEM_MESSAGE = """You are an AUTONOMOUS Loan Processor with concurrent task management.

CORE PRINCIPLE: MAXIMIZE PARALLELISM
Launch multiple independent tasks concurrently.

=== TASK DEPENDENCY GRAPH ===

PHASE 1 - CONCURRENT LAUNCH (run ALL in parallel):
├─ verify_loan_documents()
├─ order_credit_report()
├─ order_appraisal()
├─ order_flood_certification()
└─ verify_employment()

PHASE 2 - AFTER CREDIT REPORT:
└─ calculate_loan_ratios()

PHASE 3 - FINAL:
└─ submit_to_underwriting()

=== YOUR WORKFLOW ===

When you receive a loan assignment:
1. SAY: "Processing loan {loan_number} - Launching Phase 1: 5 concurrent tasks..."
2. CALL ALL 5 Phase 1 tools
3. SAY: "Phase 1 complete. Launching Phase 2..."
4. CALL calculate_loan_ratios()
5. CALL submit_to_underwriting()
6. Transfer to an available underwriter agent

=== CRITICAL RULES ===
- You can process ONE loan at a time
- Maximize parallelism within that loan
- When done, handoff to underwriter
- Be explicit about which loan number you're processing
"""


# ========== UNDERWRITER SYSTEM MESSAGE ==========

UNDERWRITER_SYSTEM_MESSAGE = """You are an AUTONOMOUS Underwriter with concurrent review capabilities.

CORE PRINCIPLE: PARALLEL RISK ASSESSMENT

=== TASK DEPENDENCY GRAPH ===

PHASE 1 - INITIAL:
└─ run_automated_underwriting()

PHASE 2 - CONCURRENT REVIEWS (run ALL in parallel):
├─ review_credit_profile()
├─ review_income_employment()
├─ review_assets_reserves()
└─ review_property_appraisal()

PHASE 3 - DECISION:
├─ issue_underwriting_conditions()
├─ issue_final_approval()
└─ deny_loan()

=== YOUR WORKFLOW ===

When you receive a submitted loan:
1. SAY: "Underwriting loan {loan_number} - Running automated underwriting..."
2. CALL run_automated_underwriting()
3. SAY: "Launching Phase 2: 4 concurrent reviews..."
4. CALL ALL 4 review tools
5. Make decision (approve/condition/deny)
6. Report completion to coordinator

=== DECISION CRITERIA ===
- APPROVE: Credit ≥620, DTI ≤50%, adequate reserves
- CONDITIONAL: Minor issues, need documentation
- DENY: Credit <580, DTI >50%, major issues

=== CRITICAL RULES ===
- You can underwrite ONE loan at a time
- Run reviews in parallel
- Make clear final decision
- Report back to coordinator when done
"""


# ========== CREATE AGENT POOL ==========

def create_loan_processor_pool():
    """Create a pool of loan processor agents"""
    processors = []
    underwriter_names = [f"underwriter_{i+1}" for i in range(NUM_UNDERWRITERS)]

    for i in range(NUM_LOAN_PROCESSORS):
        agent = AssistantAgent(
            name=f"loan_processor_{i+1}",
            model_client=model_client4o,
            handoffs=["coordinator"] + underwriter_names,  # Can handoff to coordinator or any underwriter
            system_message=LOAN_PROCESSOR_SYSTEM_MESSAGE,
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
        processors.append(agent)

    return processors


def create_underwriter_pool():
    """Create a pool of underwriter agents"""
    underwriters = []

    for i in range(NUM_UNDERWRITERS):
        agent = AssistantAgent(
            name=f"underwriter_{i+1}",
            model_client=model_client4o,
            handoffs=["coordinator"],  # Report back to coordinator when done
            system_message=UNDERWRITER_SYSTEM_MESSAGE,
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
        underwriters.append(agent)

    return underwriters


# ========== COORDINATOR AGENT ==========

def create_coordinator(num_processors, num_underwriters):
    """Create coordinator that manages the agent pool"""

    processor_names = [f"loan_processor_{i+1}" for i in range(num_processors)]
    underwriter_names = [f"underwriter_{i+1}" for i in range(num_underwriters)]

    coordinator = AssistantAgent(
        name="coordinator",
        model_client=model_client4o,
        handoffs=processor_names + underwriter_names,
        system_message=f"""You are the Coordinator managing a pool of loan processors and underwriters.

=== AGENT POOL ===

Loan Processors (can process loans concurrently):
{chr(10).join(f'  • {name}' for name in processor_names)}

Underwriters (can underwrite loans concurrently):
{chr(10).join(f'  • {name}' for name in underwriter_names)}

=== YOUR JOB ===

1. **Direct Assignment**: When you receive a loan, assign it to a SPECIFIC available processor
   - Example: "loan_processor_1, process loan LN-ABC123"
   - Use direct handoff to that specific agent

2. **Load Balancing**: Track which agents are busy
   - If processor_1 is busy, assign to processor_2
   - Distribute work evenly across the pool

3. **Monitor Progress**: Track loan status
   - When processor completes, they'll handoff to underwriter
   - When underwriter completes, they'll handoff back to you
   - Report final status

=== WORKFLOW ===

For a single loan:
1. Receive loan number
2. Find available loan_processor (e.g., loan_processor_1)
3. Transfer to that specific processor with message: "Process loan {{loan_number}}"
4. Wait for processor to complete and handoff to underwriter
5. Wait for underwriter to complete and handoff back to you
6. Report: "Loan {{loan_number}} completed with decision: {{decision}}"
7. Respond: "TERMINATE"

For multiple concurrent loans:
1. Assign loan A to loan_processor_1
2. Assign loan B to loan_processor_2
3. Assign loan C to loan_processor_3
4. Each follows their own workflow independently
5. Collect all results
6. Respond: "TERMINATE" when all complete

=== CRITICAL RULES ===

- Use DIRECT HANDOFF to specific agents (not generic handoff)
- Track agent availability in your reasoning
- Don't overload any single agent
- When all loans complete, respond: "TERMINATE"
- Be explicit about assignments: "Assigning loan X to loan_processor_Y"

=== TERMINATION ===

Respond "TERMINATE" when:
- All assigned loans have final decisions (approve/deny/conditional)
- Maximum 30 handoffs reached (safety limit)
- Persistent errors occur

Your role is work distribution and monitoring, not execution.
""",
        reflect_on_tool_use=False,
        tools=[]
    )

    return coordinator


# ========== BUILD COMPLETE TEAM ==========

def create_agent_pool_team():
    """Create the complete agent pool team"""

    processors = create_loan_processor_pool()
    underwriters = create_underwriter_pool()
    coordinator = create_coordinator(NUM_LOAN_PROCESSORS, NUM_UNDERWRITERS)

    all_agents = [coordinator] + processors + underwriters

    return {
        'coordinator': coordinator,
        'processors': processors,
        'underwriters': underwriters,
        'all_agents': all_agents
    }


# Export for easy import
__all__ = [
    'create_agent_pool_team',
    'NUM_LOAN_PROCESSORS',
    'NUM_UNDERWRITERS'
]
