"""
Concurrent Multi-Agent Architecture using AutoGen Agent SDK

TRUE concurrent execution using:
- RoutedAgent for specialized agents
- asyncio.gather() for parallel task execution
- Direct message assignment for explicit task delegation

For ONE loan, multiple agents of the SAME type handle DIFFERENT subtasks concurrently.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import os

from tools_loan_processor import (
    verify_loan_documents, order_credit_report, order_appraisal,
    order_flood_certification, verify_employment, calculate_loan_ratios,
    submit_to_underwriting
)
from tools_underwriter import (
    run_automated_underwriting, review_credit_profile, review_income_employment,
    review_assets_reserves, review_property_appraisal, issue_final_approval,
    issue_underwriting_conditions, deny_loan
)
from tools_mortgage_broker import (
    query_lender_wellsfargo, query_lender_bankofamerica, query_lender_chase,
    query_lender_quicken, query_lender_usbank
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


# ========== MESSAGE TYPES ==========

@dataclass
class LoanTask:
    """Task message sent to individual agents"""
    loan_number: str
    task_type: str
    instructions: str


@dataclass
class TaskResult:
    """Result returned by individual agents"""
    agent_id: str
    task_type: str
    loan_number: str
    result: str
    success: bool


# ========== INDIVIDUAL MORTGAGE BROKER AGENTS ==========

# Each broker queries one specific lender for rate quotes
# They work CONCURRENTLY to get the best rates

mortgage_broker_for_wells_fargo = AssistantAgent(
    name="mortgage_broker_for_wells_fargo",
    model_client=model_client,
    system_message="""You are a Mortgage Broker specializing in Wells Fargo.

When you receive a task to get a rate quote for a loan:
1. Call query_lender_wellsfargo(loan_number)
2. Report the rate quote concisely
3. You work CONCURRENTLY with other brokers

Be concise and focused on your task.""",
    tools=[query_lender_wellsfargo]
)

mortgage_broker_for_bank_of_america = AssistantAgent(
    name="mortgage_broker_for_bank_of_america",
    model_client=model_client,
    system_message="""You are a Mortgage Broker specializing in Bank of America.

When you receive a task to get a rate quote for a loan:
1. Call query_lender_bankofamerica(loan_number)
2. Report the rate quote concisely
3. You work CONCURRENTLY with other brokers

Be concise and focused on your task.""",
    tools=[query_lender_bankofamerica]
)

mortgage_broker_for_chase = AssistantAgent(
    name="mortgage_broker_for_chase",
    model_client=model_client,
    system_message="""You are a Mortgage Broker specializing in Chase.

When you receive a task to get a rate quote for a loan:
1. Call query_lender_chase(loan_number)
2. Report the rate quote concisely
3. You work CONCURRENTLY with other brokers

Be concise and focused on your task.""",
    tools=[query_lender_chase]
)

mortgage_broker_quicken_loans = AssistantAgent(
    name="mortgage_broker_quicken_loans",
    model_client=model_client,
    system_message="""You are a Mortgage Broker specializing in Quicken Loans.

When you receive a task to get a rate quote for a loan:
1. Call query_lender_quicken(loan_number)
2. Report the rate quote concisely
3. You work CONCURRENTLY with other brokers

Be concise and focused on your task.""",
    tools=[query_lender_quicken]
)

mortgage_broker_for_us_bank = AssistantAgent(
    name="mortgage_broker_for_us_bank",
    model_client=model_client,
    system_message="""You are a Mortgage Broker specializing in US Bank.

When you receive a task to get a rate quote for a loan:
1. Call query_lender_usbank(loan_number)
2. Report the rate quote concisely
3. You work CONCURRENTLY with other brokers

Be concise and focused on your task.""",
    tools=[query_lender_usbank]
)

# ========== INDIVIDUAL LOAN PROCESSOR AGENTS ==========

# Each processor is a simple AssistantAgent with ONE tool
# They don't need to be RoutedAgent since they just execute tools

loan_processor_for_document_verification = AssistantAgent(
    name="loan_processor_for_document_verification",
    model_client=model_client,
    system_message="""You are a Document Verification Specialist.

When you receive a task to verify documents for a loan:
1. Call verify_loan_documents(loan_number)
2. Report the result concisely
3. You work CONCURRENTLY with other processors

Be concise and focused on your task.""",
    tools=[verify_loan_documents]
)

loan_processor_for_credit_report = AssistantAgent(
    name="loan_processor_for_credit_report",
    model_client=model_client,
    system_message="""You are a Credit Report Specialist.

When you receive a task to order credit report for a loan:
1. Call order_credit_report(loan_number)
2. Report the result concisely
3. You work CONCURRENTLY with other processors

Be concise and focused on your task.""",
    tools=[order_credit_report]
)

loan_processor_for_appraisal = AssistantAgent(
    name="loan_processor_for_appraisal",
    model_client=model_client,
    system_message="""You are an Appraisal Specialist.

When you receive a task to order appraisal for a loan:
1. Call order_appraisal(loan_number)
2. Report the result concisely
3. You work CONCURRENTLY with other processors

Be concise and focused on your task.""",
    tools=[order_appraisal]
)

loan_processor_for_flood_certification = AssistantAgent(
    name="loan_processor_for_flood_certification",
    model_client=model_client,
    system_message="""You are a Flood Certification Specialist.

When you receive a task to order flood certification for a loan:
1. Call order_flood_certification(loan_number)
2. Report the result concisely
3. You work CONCURRENTLY with other processors

Be concise and focused on your task.""",
    tools=[order_flood_certification]
)

loan_processor_for_employment_verification = AssistantAgent(
    name="loan_processor_for_employment_verification",
    model_client=model_client,
    system_message="""You are an Employment Verification Specialist.

When you receive a task to verify employment for a loan:
1. Call verify_employment(loan_number)
2. Report the result concisely
3. You work CONCURRENTLY with other processors

Be concise and focused on your task.""",
    tools=[verify_employment]
)

loan_processor_for_financial_analysis = AssistantAgent(
    name="loan_processor_for_financial_analysis",
    model_client=model_client4o,
    system_message="""You are a Financial Analysis Specialist.

When you receive a task to calculate ratios and submit for a loan:
1. Call calculate_loan_ratios(loan_number)
2. Call submit_to_underwriting(loan_number)
3. Report the result concisely
4. You work CONCURRENTLY with other processors (may wait for credit data internally)

Be concise and focused on your task.""",
    tools=[calculate_loan_ratios, submit_to_underwriting]
)

# ========== INDIVIDUAL UNDERWRITER AGENTS ==========

underwriter_for_credit_review = AssistantAgent(
    name="underwriter_for_credit_review",
    model_client=model_client,
    system_message="""You are a Credit Review Specialist.

When you receive a task to review credit for a loan:
1. Call review_credit_profile(loan_number)
2. Report the result concisely
3. You work CONCURRENTLY with other underwriters

Be concise and focused on your review.""",
    tools=[review_credit_profile]
)

underwriter_for_income_review = AssistantAgent(
    name="underwriter_for_income_review",
    model_client=model_client,
    system_message="""You are an Income Review Specialist.

When you receive a task to review income for a loan:
1. Call review_income_employment(loan_number)
2. Report the result concisely
3. You work CONCURRENTLY with other underwriters

Be concise and focused on your review.""",
    tools=[review_income_employment]
)

underwriter_for_asset_review = AssistantAgent(
    name="underwriter_for_asset_review",
    model_client=model_client,
    system_message="""You are an Asset Review Specialist.

When you receive a task to review assets for a loan:
1. Call review_assets_reserves(loan_number)
2. Report the result concisely
3. You work CONCURRENTLY with other underwriters

Be concise and focused on your review.""",
    tools=[review_assets_reserves]
)

underwriter_for_property_review = AssistantAgent(
    name="underwriter_for_property_review",
    model_client=model_client,
    system_message="""You are a Property Review Specialist.

When you receive a task to review property for a loan:
1. Call review_property_appraisal(loan_number)
2. Report the result concisely
3. You work CONCURRENTLY with other underwriters

Be concise and focused on your review.""",
    tools=[review_property_appraisal]
)

underwriter_for_automated_underwriting = AssistantAgent(
    name="underwriter_for_automated_underwriting",
    model_client=model_client4o,
    system_message="""You are an Automated Underwriting Specialist.

When you receive a task to run automated underwriting for a loan:
1. Call run_automated_underwriting(loan_number)
2. Report the result concisely
3. You work CONCURRENTLY with other underwriters (may wait for submission internally)

Be concise and focused on your task.""",
    tools=[run_automated_underwriting]
)

# ========== DECISION MAKER ==========

decision_maker = AssistantAgent(
    name="decision_maker",
    model_client=model_client4o,
    system_message="""You are the Final Decision Maker.

When you receive a task to make a decision for a loan:
1. Analyze all reviews in the loan file
2. Make a decision:
   - All acceptable → issue_final_approval(loan_number)
   - Minor issues → issue_underwriting_conditions(loan_number, conditions)
   - Unacceptable → deny_loan(loan_number, reasons)
3. Report the decision clearly

Assume all prerequisite reviews are complete.""",
    tools=[issue_final_approval, issue_underwriting_conditions, deny_loan]
)


# ========== COORDINATOR FUNCTION ==========

async def run_agent_task(agent: AssistantAgent, loan_number: str, task_description: str) -> str:
    """
    Run a single agent task asynchronously.

    This function sends a message to an agent and gets its response.
    Used by the coordinator to execute tasks concurrently.
    """
    print(f"  → {agent.name}: {task_description}")

    # Create task message
    message = f"Task for loan {loan_number}: {task_description}"

    # Run the agent (single turn)
    response = await agent.on_messages(
        [TextMessage(content=message, source="coordinator")],
        cancellation_token=None
    )

    # Extract response content
    if hasattr(response, 'chat_message'):
        result = response.chat_message.content
    elif hasattr(response, 'content'):
        result = response.content
    else:
        result = str(response)

    print(f"  ✓ {agent.name} completed")

    return result


async def process_loan_concurrent(loan_number: str) -> Dict[str, Any]:
    """
    Main coordinator function that processes a loan with TRUE concurrent execution.

    Uses asyncio.gather() to run multiple agents in parallel.
    """

    print(f"\n{'='*80}")
    print(f"🚀 PROCESSING LOAN: {loan_number} (TRUE CONCURRENT EXECUTION)")
    print(f"{'='*80}\n")

    results = {}

    # ========== PHASE 0: ALL 5 Mortgage Brokers Query Lenders CONCURRENTLY ==========
    print("PHASE 0: Assigning ALL 5 mortgage brokers to get rate quotes CONCURRENTLY")
    print("-" * 80)

    phase0_results = await asyncio.gather(
        run_agent_task(mortgage_broker_for_wells_fargo, loan_number, "Get rate quote from Wells Fargo"),
        run_agent_task(mortgage_broker_for_bank_of_america, loan_number, "Get rate quote from Bank of America"),
        run_agent_task(mortgage_broker_for_chase, loan_number, "Get rate quote from Chase"),
        run_agent_task(mortgage_broker_quicken_loans, loan_number, "Get rate quote from Quicken Loans"),
        run_agent_task(mortgage_broker_for_us_bank, loan_number, "Get rate quote from US Bank"),
    )

    results['phase0'] = phase0_results
    print(f"\n✅ PHASE 0 COMPLETE: All 5 brokers got rate quotes concurrently\n")

    # ========== PHASE 1: ALL 6 Loan Processing Tasks CONCURRENTLY ==========
    print("PHASE 1: Assigning ALL 6 loan processing tasks CONCURRENTLY")
    print("-" * 80)

    phase1_results = await asyncio.gather(
        run_agent_task(loan_processor_for_document_verification, loan_number, "Verify documents"),
        run_agent_task(loan_processor_for_credit_report, loan_number, "Order credit report"),
        run_agent_task(loan_processor_for_appraisal, loan_number, "Order appraisal"),
        run_agent_task(loan_processor_for_flood_certification, loan_number, "Order flood certification"),
        run_agent_task(loan_processor_for_employment_verification, loan_number, "Verify employment"),
        run_agent_task(loan_processor_for_financial_analysis, loan_number, "Calculate ratios and submit to underwriting"),
    )

    results['phase1'] = phase1_results
    print(f"\n✅ PHASE 1 COMPLETE: All 6 processors executed concurrently\n")

    # ========== PHASE 2: ALL 5 Underwriting Tasks CONCURRENTLY ==========
    print("PHASE 2: Assigning ALL 5 underwriting tasks CONCURRENTLY")
    print("-" * 80)

    phase2_results = await asyncio.gather(
        run_agent_task(underwriter_for_automated_underwriting, loan_number, "Run automated underwriting"),
        run_agent_task(underwriter_for_credit_review, loan_number, "Review credit profile"),
        run_agent_task(underwriter_for_income_review, loan_number, "Review income and employment"),
        run_agent_task(underwriter_for_asset_review, loan_number, "Review assets and reserves"),
        run_agent_task(underwriter_for_property_review, loan_number, "Review property and appraisal"),
    )

    results['phase2'] = phase2_results
    print(f"\n✅ PHASE 2 COMPLETE: All 5 underwriters executed concurrently\n")

    # ========== PHASE 3: Final Decision ==========
    print("PHASE 3: Making final decision")
    print("-" * 80)

    decision_result = await run_agent_task(
        decision_maker,
        loan_number,
        "Review all underwriting results and make final decision"
    )

    results['phase3'] = decision_result
    print(f"\n✅ PHASE 3 COMPLETE: Final decision made\n")

    print(f"{'='*80}")
    print(f"✅ LOAN {loan_number} PROCESSING COMPLETE")
    print(f"{'='*80}\n")

    return results


# ========== EXPORT ==========

def create_concurrent_team():
    """Return all agents for reference"""
    return {
        'mortgage_brokers': [
            mortgage_broker_for_wells_fargo, mortgage_broker_for_bank_of_america, mortgage_broker_for_chase,
            mortgage_broker_quicken_loans, mortgage_broker_for_us_bank
        ],
        'loan_processors': [
            loan_processor_for_document_verification, loan_processor_for_credit_report, loan_processor_for_appraisal,
            loan_processor_for_flood_certification, loan_processor_for_employment_verification, loan_processor_for_financial_analysis
        ],
        'underwriters': [
            underwriter_for_credit_review, underwriter_for_income_review, underwriter_for_asset_review,
            underwriter_for_property_review, underwriter_for_automated_underwriting
        ],
        'decision_maker': decision_maker,
        'process_loan': process_loan_concurrent
    }


__all__ = ['create_concurrent_team', 'process_loan_concurrent']
