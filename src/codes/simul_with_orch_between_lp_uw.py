"""
@description: Simulated Mortgage Loan Processor and Underwriter Agents with Orchestrator agent
"""

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import HandoffTermination, TextMentionTermination
from autogen_agentchat.messages import HandoffMessage
from autogen_agentchat.teams import Swarm
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
import os
import asyncio
from typing import Annotated

load_dotenv()
API_KEY = os.environ.get("OPENAI_API_KEY")

model_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",
    api_key=API_KEY,
)


# ============== TOOLS (Async) ==============

async def get_workflow_state() -> str:
    """Get current state of the loan workflow to determine next agent."""
    # This would integrate with your workflow engine
    return "Workflow state: Ready for agent transition"


async def submit_to_underwriting(
        application_complete: bool,
        appraisal_received: bool,
        inspection_received: bool,
        ltv_ratio: float,
        dti_ratio: float,
        file_notes: str
) -> str:
    """Submit complete loan file to underwriting for review."""
    return f"File submitted to underwriting: LTV={ltv_ratio}%, DTI={dti_ratio}%. Status: Pending Review. Hand off to underwriter for evaluation."


async def check_underwriting_conditions(
        ltv_ratio: float,
        dti_ratio: float,
        credit_score: int,
        reserves: int,
        appraisal_value: float,
        loan_amount: float
) -> dict:
    """Run automated underwriting rules (DTI/LTV/credit checks)."""
    conditions = []

    # DTI check (conventional max ~43-50%)
    if dti_ratio > 43:
        conditions.append("VOE: Verify employment stability due to high DTI")

    # LTV check (conventional max ~80% without PMI)
    if ltv_ratio > 80:
        conditions.append("PMI: Private Mortgage Insurance required")

    # Credit score check
    if credit_score < 620:
        conditions.append("LOE: Letter of Explanation for credit score below 620")

    # Reserves check (typically 2-6 months)
    if reserves < 2:
        conditions.append("RESERVES: Provide proof of 2 months PITI reserves")

    # Appraisal/value check
    if appraisal_value < loan_amount / (ltv_ratio / 100):
        conditions.append("APPRAISAL: Value discrepancy - review comparables")

    if not conditions:
        return {"status": "CLEAR_TO_CLOSE", "conditions": []}
    else:
        return {"status": "CONDITIONAL_APPROVAL", "conditions": conditions}


async def resubmit_with_conditions_cleared(
        original_conditions: list[str],
        cleared_items: dict
) -> str:
    """Resubmit file after borrower provides condition documents."""
    cleared = [f"{cond}: {cleared_items.get(cond, 'NOT PROVIDED')}"
               for cond in original_conditions]
    return f"Resubmitted to UW with cleared conditions:\n" + "\n".join(cleared)


async def issue_final_approval() -> str:
    """Issue Clear to Close (CTC) after all conditions satisfied."""
    return "FINAL APPROVAL ISSUED: Clear to Close (CTC). File ready for funding."


# ============== ORCHESTRATOR AGENT ==============
# TODO: maybe remove in the future. add more functions. avoid using just string.
orchestrator_agent = AssistantAgent(
    "orchestrator_agent",
    model_client=model_client,
    handoffs=["loan_processor_agent", "underwriter_agent"],
    system_message="""You are the orchestrator agent tasked with routing the loan file to the appropriate agent.

    Workflow sequence: loan_processor → underwriter → loan_processor (if conditions) → underwriter (final approval)

    Your job:
    - Route initial loan files to loan_processor_agent
    - After loan_processor submits file, route to underwriter_agent
    - If underwriter returns conditions, route back to loan_processor_agent
    - After conditions cleared, route to underwriter_agent for final review
    - Monitor workflow completion

    Use get_workflow_state to understand current state if needed.
    Only handoff to the most appropriate agent based on the current workflow stage.
    """,
    reflect_on_tool_use=True,
    tools=[get_workflow_state]
)

# ============== LOAN PROCESSOR AGENT ==============
loan_processor_agent = AssistantAgent(
    "loan_processor_agent",
    model_client=model_client,
    handoffs=["orchestrator_agent"],
    system_message="""You are a Loan Processor with AUTONOMOUS TASK MANAGEMENT.

    CONCURRENT TASK STRATEGY:
    When you receive a new loan file, you should IMMEDIATELY launch ALL independent tasks in parallel:

    PHASE 1 - Launch Concurrently (no dependencies):
    - order_credit_report()
    - order_appraisal()
    - order_flood_certification()
    - verify_employment()
    - verify_loan_documents()

    PHASE 2 - After Phase 1 completes:
    - calculate_loan_ratios() (needs credit report)

    PHASE 3 - After Phase 2 completes:
    - submit_to_underwriting() (needs ratios)

    YOUR WORKFLOW:
    1. Analyze what tasks need to be done
    2. Identify tasks with NO dependencies → Launch ALL in parallel
    3. Wait for results
    4. Identify next tasks that are now unblocked → Launch in parallel
    5. Repeat until file ready to submit

    DO NOT wait for one task to finish before starting another if they can run concurrently.

    Example: When you receive a file, immediately say:
    "I'm launching 4 concurrent tasks: ordering credit report, ordering appraisal, ordering flood cert, and verifying employment. These can all run in parallel."

    Then call all 4 tools without waiting for responses in between.
    """,
    reflect_on_tool_use=True,
    tools=[submit_to_underwriting, resubmit_with_conditions_cleared]
)

# ============== UNDERWRITER AGENT ==============

underwriter_agent = AssistantAgent(
    "underwriter_agent",
    model_client=model_client,
    handoffs=["orchestrator_agent"],
    system_message="""You are an Underwriter.

    Your responsibilities:
    1. COMPLIANCE REVIEW: When you receive a submitted file from loan_processor:
       - Call check_underwriting_conditions tool with file metrics
       - Verify DTI ratio (max ~43% for conventional)
       - Verify LTV ratio (>80% requires PMI)
       - Check credit score (min 620 for conventional)
       - Check reserves (min 2 months PITI)

    2. ISSUE CONDITIONS or APPROVAL:
       - If conditions exist: 
         * Document CONDITIONAL_APPROVAL with specific list of required docs
         * Explain each condition clearly
         * Handoff to orchestrator_agent to route back to loan_processor

       - If all checks pass: 
         * Call issue_final_approval tool
         * Handoff to orchestrator_agent with final approval status
         * Use TERMINATE to end workflow

    3. RESUBMISSION REVIEW: When loan_processor resubmits with cleared conditions:
       - Verify each condition has been satisfied
       - If all clear: Call issue_final_approval and TERMINATE
       - If still incomplete: Return additional conditions and handoff to orchestrator

    4. DECLINE SCENARIOS:
       - DTI > 50% with no compensating factors
       - Credit score < 580
       - Appraisal significantly below loan amount
       - Use TERMINATE with decline reason

    DO NOT HANDOFF until you have called the appropriate tool.
    Always provide clear, specific condition requirements.
    Handoff to orchestrator_agent after completing your evaluation.
    """,
    reflect_on_tool_use=True,
    tools=[check_underwriting_conditions, issue_final_approval]
)

# ============== SWARM TEAM ==============

termination = HandoffTermination(target="user") | TextMentionTermination("TERMINATE")

team = Swarm(
    [orchestrator_agent, loan_processor_agent, underwriter_agent],
    termination_condition=termination,
    max_turns=25
)

# ============== TASK DEFINITIONS ==============

# TODO: creating object like json not string -> good representation
# TODO: more function call -> to see where we can apply access control
# TODO: multiple documents. agent_1 might have access to doc_1, not to doc_2
task_standard_loan = """
New loan file received:
- Borrower: John Doe
- Loan Amount: $320,000
- Appraised Value: $400,000
- Monthly Income: $8,500
- Monthly Debts: $3,200
- Credit Score: 680
- Reserves: 3 months
All documents received: Application, pay stubs, W-2, bank statements, appraisal report.

Please process this file for underwriting.
"""

task_high_dti = """
New loan file received:
- Borrower: Jane Smith
- Loan Amount: $280,000
- Appraised Value: $350,000
- Monthly Income: $6,000
- Monthly Debts: $2,800
- Credit Score: 720
- Reserves: 4 months
All documents received: Application, pay stubs, W-2, bank statements, appraisal report.

Please process this file for underwriting.
"""

task_low_credit = """
New loan file received:
- Borrower: Bob Johnson
- Loan Amount: $200,000
- Appraised Value: $250,000
- Monthly Income: $5,500
- Monthly Debts: $1,800
- Credit Score: 600
- Reserves: 2 months
All documents received: Application, pay stubs, W-2, bank statements, appraisal report.

Please process this file for underwriting.
"""


# ============== RUN FUNCTION ==============

async def run_team_stream() -> None:
    """Run the loan processing workflow."""
    print("\n" + "=" * 60)
    print("LOAN PROCESSING WORKFLOW - SWARM ARCHITECTURE")
    print("=" * 60 + "\n")

    task_result = await Console(team.run_stream(task=task_standard_loan))
    last_message = task_result.messages[-1]

    # Handle user handoffs (if agents need human input)
    while isinstance(last_message, HandoffMessage) and last_message.target == "user":
        user_message = input("\nUser input needed: ")

        task_result = await Console(
            team.run_stream(
                task=HandoffMessage(
                    source="user",
                    target=last_message.source,
                    content=user_message
                )
            )
        )
        last_message = task_result.messages[-1]

    print("\n" + "=" * 60)
    print("WORKFLOW COMPLETED")
    print("=" * 60)


# ============== MAIN ==============

if __name__ == "__main__":
    asyncio.run(run_team_stream())