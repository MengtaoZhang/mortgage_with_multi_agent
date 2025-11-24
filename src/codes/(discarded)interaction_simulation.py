"""
simulate the interaction among various agents in a defined environment
"""

"""
starting with loan processor and underwriter interaction simulation

Underwriter (UW): 3 interactions
LP→UW: Submit underwriting file
UW→LP: Conditional approval
LP→UW: Resubmit for underwriting
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
import subprocess
from typing import Optional
API_KEY = os.environ.get("OPENAI_API_KEY")

model_client4o = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=API_KEY,
)

from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from typing import Annotated


# ============== TOOLS ==============

def submit_to_underwriting(
        application_complete: Annotated[bool, "All application docs verified"],
        appraisal_received: Annotated[bool, "Appraisal report attached"],
        inspection_received: Annotated[bool, "Inspection report attached (if applicable)"],
        ltv_ratio: Annotated[float, "Loan-to-Value ratio"],
        dti_ratio: Annotated[float, "Debt-to-Income ratio"],
        file_notes: Annotated[str, "Summary of borrower file"]
) -> str:
    """Submit complete loan file to underwriting for review."""
    return f"File submitted to underwriting: LTV={ltv_ratio}%, DTI={dti_ratio}%. Status: Pending Review"


def check_underwriting_conditions(
        ltv_ratio: Annotated[float, "Loan-to-Value ratio"],
        dti_ratio: Annotated[float, "Debt-to-Income ratio"],
        credit_score: Annotated[int, "Borrower credit score"],
        reserves: Annotated[int, "Months of reserves"],
        appraisal_value: Annotated[float, "Appraised property value"],
        loan_amount: Annotated[float, "Requested loan amount"]
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


def resubmit_with_conditions_cleared(
        original_conditions: Annotated[list[str], "Original conditions list"],
        cleared_items: Annotated[dict, "Documents provided for each condition"]
) -> str:
    """Resubmit file after borrower provides condition documents."""
    cleared = [f"{cond}: {cleared_items.get(cond, 'NOT PROVIDED')}"
               for cond in original_conditions]
    return f"Resubmitted to UW with cleared conditions:\n" + "\n".join(cleared)


def issue_final_approval() -> str:
    """Issue Clear to Close (CTC) after all conditions satisfied."""
    return "FINAL APPROVAL ISSUED: Clear to Close (CTC). File ready for funding."


# ============== LLM CONFIG ==============

llm_config = {
    "config_list": [
        {
            "model": "gpt-4o",  # or "gpt-4", "gpt-3.5-turbo", etc.
            "api_key": API_KEY,  # or use environment variable
            # "base_url": "your-base-url",  # Optional: for Azure or custom endpoints
        }
    ],
    "temperature": 0.7,
}

# ============== AGENTS ==============

loan_processor_agent = AssistantAgent(
    name="loan_processor_agent",
    llm_config=llm_config,
    system_message="""You are a Loan Processor.

    Your responsibilities:
    1. COLLECT & VERIFY: Ensure all required documents are received from borrower
       - Application (URLA), pay stubs, W-2/1099, bank statements, tax returns
       - Appraisal report (URAR + comps)
       - Inspection report (if applicable)

    2. STRUCTURE FILE: Build complete loan package with:
       - Calculate LTV ratio (Loan Amount / Appraised Value)
       - Calculate DTI ratio (Monthly Debts / Monthly Income)
       - OCR and consistency checks
       - Risk assessment notes

    3. SUBMIT TO UNDERWRITING: Once file is complete, call submit_to_underwriting tool

    4. MANAGE CONDITIONS: When underwriter returns conditions:
       - Request missing documents from borrower
       - Receive condition documents
       - Call resubmit_with_conditions_cleared tool
       - Wait for final review

    5. TERMINATE CONDITIONS:
       - Use TERMINATE if file is approved (CTC received)
       - Use TERMINATE if borrower fails to provide conditions within deadline
       - Use TERMINATE if underwriter declines the loan

    Always verify completeness before submitting. If documents are missing, 
    request them BEFORE submitting to underwriting.
    """,
)

# Register tools for loan processor
loan_processor_agent.register_for_llm(
    name="submit_to_underwriting",
    description="Submit complete loan file to underwriting for review"
)(submit_to_underwriting)

loan_processor_agent.register_for_llm(
    name="resubmit_with_conditions_cleared",
    description="Resubmit file after borrower provides condition documents"
)(resubmit_with_conditions_cleared)

underwriter_agent = AssistantAgent(
    name="underwriter_agent",
    llm_config=llm_config,
    system_message="""You are an Underwriter.

    Your responsibilities:
    1. COMPLIANCE REVIEW: When loan_processor submits a file:
       - Call check_underwriting_conditions tool with file metrics
       - Verify DTI ratio (max ~43% for conventional)
       - Verify LTV ratio (>80% requires PMI)
       - Check credit score (min 620 for conventional)
       - Check reserves (min 2 months PITI)
       - Review appraisal for value accuracy

    2. ISSUE CONDITIONS or APPROVAL:
       - If conditions exist: Return CONDITIONAL_APPROVAL with list of required docs
         (e.g., VOE, LOE, reserves proof, repair bids)
       - Return to loan_processor to collect conditions

       - If all checks pass: Call issue_final_approval tool
       - Return CTC status

    3. RESUBMISSION REVIEW: When loan_processor resubmits with cleared conditions:
       - Verify each condition has been satisfied
       - If all clear: Call issue_final_approval
       - If still incomplete: Return additional conditions

    4. DECLINE SCENARIOS:
       - DTI > 50% with no compensating factors
       - Credit score < 580
       - Appraisal significantly below loan amount
       - Use TERMINATE with decline reason

    Use TERMINATE only when:
    - Final approval (CTC) is issued
    - Loan is declined with documented reason

    Always provide clear, specific condition requirements.
    """,
)

# Register tools for underwriter
underwriter_agent.register_for_llm(
    name="check_underwriting_conditions",
    description="Run automated underwriting rules (DTI/LTV/credit checks)"
)(check_underwriting_conditions)

underwriter_agent.register_for_llm(
    name="issue_final_approval",
    description="Issue Clear to Close (CTC) after all conditions satisfied"
)(issue_final_approval)

# Create a user proxy to execute the tool calls
user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    code_execution_config=False,
)

# Register tool execution
user_proxy.register_for_execution(name="submit_to_underwriting")(submit_to_underwriting)
user_proxy.register_for_execution(name="check_underwriting_conditions")(check_underwriting_conditions)
user_proxy.register_for_execution(name="resubmit_with_conditions_cleared")(resubmit_with_conditions_cleared)
user_proxy.register_for_execution(name="issue_final_approval")(issue_final_approval)

# ============== GROUP CHAT ==============

group_chat = GroupChat(
    agents=[loan_processor_agent, underwriter_agent, user_proxy],
    messages=[],
    max_round=20,

# ADD THIS for controlled workflow
    allowed_or_disallowed_speaker_transitions={
        loan_processor_agent: [underwriter_agent, user_proxy],
        underwriter_agent: [loan_processor_agent, user_proxy],
        user_proxy: [loan_processor_agent, underwriter_agent],
    },
    speaker_transitions_type="allowed",
)

manager = GroupChatManager(
    groupchat=group_chat,
    llm_config=llm_config,
)

# ============== START CONVERSATION ==============

if __name__ == "__main__":
    chat_result = user_proxy.initiate_chat(
        manager,
        message="""
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
    )