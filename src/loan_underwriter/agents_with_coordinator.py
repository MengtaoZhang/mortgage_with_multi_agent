"""
Concurrent Multi-Agent Architecture with OrchestratorAgent

Architecture:
- 1 OrchestratorAgent (orchestrator using asyncio.gather())
- 3 worker agent types: mortgage_broker, loan_processor, underwriter
- Orchestrator sends directed messages to workers concurrently
- Workers return results to orchestrator
"""

import asyncio
import time
from typing import Any, Dict, List, Sequence
from autogen_agentchat.agents import AssistantAgent, BaseChatAgent
from autogen_agentchat.base import Response, TaskResult
from autogen_agentchat.messages import ChatMessage, TextMessage
from autogen_core import CancellationToken
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

from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ChatCompletionClient, CreateResult
from typing import Sequence, Any
from autogen_core.tools import Tool, ToolSchema

class ToolRequiredOpenAIClient(OpenAIChatCompletionClient):
    async def create(
        self,
        messages,
        *,
        tools: Sequence[Tool | ToolSchema] | None = None,
        tool_choice: Any = "auto",
        **kwargs: Any,
    ) -> CreateResult:
        # Debug logging
        print(f"    [ToolClient] tools={tools is not None}, len={len(tools) if tools else 0}, choice={tool_choice}")

        # If tools are provided and caller didn't explicitly override,
        # force tool_choice="required"
        if tools is not None and len(tools) > 0 and tool_choice == "auto":
            tool_choice = "required"
            print(f"    [ToolClient] ✓ Forcing tool_choice='required'")

        return await super().create(
            messages,
            tools=tools,
            tool_choice=tool_choice,
            **kwargs,
        )


# Base timestamp for relative logging (proves overlap)
_orch_start = time.perf_counter()


def _ts() -> str:
    """Return relative timestamp since module import for log clarity."""
    return f"t+{time.perf_counter() - _orch_start:.3f}s"

# model_client = OpenAIChatCompletionClient(
#     model="gpt-4o-mini",
#     api_key=API_KEY,
# )

model_client = ToolRequiredOpenAIClient(
    model="gpt-4o-mini",
    api_key=API_KEY,
)

model_client4o = ToolRequiredOpenAIClient(
    model="gpt-4o",
    api_key=API_KEY,
)


# ========== WORKER AGENTS ==========

# Mortgage Broker Agents (5 instances)
mortgage_broker_1 = AssistantAgent(
    name="mortgage_broker_1",
    model_client=model_client,
    system_message="""You are a Mortgage Broker specializing in Wells Fargo.

CRITICAL: You MUST call the query_lender_wellsfargo tool. Extract the loan_number from the task and call the tool immediately.

When you receive a task:
1. Extract loan_number from the task message
2. Call query_lender_wellsfargo(loan_number)
3. Report the result concisely

Be concise and focused.""",
    tools=[query_lender_wellsfargo, func_2, fun_3]
)

mortgage_broker_2 = AssistantAgent(
    name="mortgage_broker_2",
    model_client=model_client,
    system_message="""You are a Mortgage Broker specializing in Bank of America.

CRITICAL: You MUST call the query_lender_bankofamerica tool. Extract the loan_number from the task and call the tool immediately.

When you receive a task:
1. Extract loan_number from the task message
2. Call query_lender_bankofamerica(loan_number)
3. Report the result concisely

Be concise and focused.""",
    tools=[query_lender_bankofamerica]
)

mortgage_broker_3 = AssistantAgent(
    name="mortgage_broker_3",
    model_client=model_client,
    system_message="""You are a Mortgage Broker specializing in Chase.

CRITICAL: You MUST call the query_lender_chase tool. Extract the loan_number from the task and call the tool immediately.

When you receive a task:
1. Extract loan_number from the task message
2. Call query_lender_chase(loan_number)
3. Report the result concisely

Be concise and focused.""",
    tools=[query_lender_chase]
)

mortgage_broker_4 = AssistantAgent(
    name="mortgage_broker_4",
    model_client=model_client,
    system_message="""You are a Mortgage Broker specializing in Quicken Loans.

CRITICAL: You MUST call the query_lender_quicken tool. Extract the loan_number from the task and call the tool immediately.

When you receive a task:
1. Extract loan_number from the task message
2. Call query_lender_quicken(loan_number)
3. Report the result concisely

Be concise and focused.""",
    tools=[query_lender_quicken]
)

mortgage_broker_5 = AssistantAgent(
    name="mortgage_broker_5",
    model_client=model_client,
    system_message="""You are a Mortgage Broker specializing in US Bank.

CRITICAL: You MUST call the query_lender_usbank tool. Extract the loan_number from the task and call the tool immediately.

When you receive a task:
1. Extract loan_number from the task message
2. Call query_lender_usbank(loan_number)
3. Report the result concisely

Be concise and focused.""",
    tools=[query_lender_usbank]
)

# Loan Processor Agents (6 instances)
loan_processor_1 = AssistantAgent(
    name="loan_processor_1",
    model_client=model_client,
    system_message="""You are a Document Verification Specialist.

CRITICAL: You MUST call the verify_loan_documents tool. Extract the loan_number from the task and call the tool immediately.

When you receive a task:
1. Extract loan_number from the task message
2. Call verify_loan_documents(loan_number)
3. Report the result concisely

Be concise and focused.""",
    tools=[verify_loan_documents]
)

loan_processor_2 = AssistantAgent(
    name="loan_processor_2",
    model_client=model_client,
    system_message="""You are a Credit Report Specialist.

CRITICAL: You MUST call the order_credit_report tool. Extract the loan_number from the task and call the tool immediately.

When you receive a task:
1. Extract loan_number from the task message
2. Call order_credit_report(loan_number)
3. Report the result concisely

Be concise and focused.""",
    tools=[order_credit_report]
)

loan_processor_3 = AssistantAgent(
    name="loan_processor_3",
    model_client=model_client,
    system_message="""You are an Appraisal Specialist.

CRITICAL: You MUST call the order_appraisal tool. Extract the loan_number from the task and call the tool immediately.

When you receive a task:
1. Extract loan_number from the task message
2. Call order_appraisal(loan_number)
3. Report the result concisely

Be concise and focused.""",
    tools=[order_appraisal]
)

loan_processor_4 = AssistantAgent(
    name="loan_processor_4",
    model_client=model_client,
    system_message="""You are a Flood Certification Specialist.

CRITICAL: You MUST call the order_flood_certification tool. Extract the loan_number from the task and call the tool immediately.

When you receive a task:
1. Extract loan_number from the task message
2. Call order_flood_certification(loan_number)
3. Report the result concisely

Be concise and focused.""",
    tools=[order_flood_certification]
)

loan_processor_5 = AssistantAgent(
    name="loan_processor_5",
    model_client=model_client,
    system_message="""You are an Employment Verification Specialist.

CRITICAL: You MUST call the verify_employment tool. Extract the loan_number from the task and call the tool immediately.

When you receive a task:
1. Extract loan_number from the task message
2. Call verify_employment(loan_number)
3. Report the result concisely

Be concise and focused.""",
    tools=[verify_employment]
)

loan_processor_6 = AssistantAgent(
    name="loan_processor_6",
    model_client=model_client,
    system_message="""You are a Financial Analysis Specialist.

CRITICAL: You MUST call the tools. Extract the loan_number from the task and call the tools immediately.

When you receive a task:
1. Extract loan_number from the task message
2. Call calculate_loan_ratios(loan_number)
3. Call submit_to_underwriting(loan_number)
4. Report the result concisely

Be concise and focused.""",
    tools=[calculate_loan_ratios, submit_to_underwriting]
)

# Underwriter Agents (5 instances)
underwriter_1 = AssistantAgent(
    name="underwriter_1",
    model_client=model_client,
    system_message="""You are a Credit Review Specialist.

CRITICAL: You MUST call the review_credit_profile tool. Extract the loan_number from the task and call the tool immediately.

When you receive a task:
1. Extract loan_number from the task message
2. Call review_credit_profile(loan_number)
3. Report the result concisely

Be concise and focused.""",
    tools=[review_credit_profile]
)

underwriter_2 = AssistantAgent(
    name="underwriter_2",
    model_client=model_client,
    system_message="""You are an Income Review Specialist.

CRITICAL: You MUST call the review_income_employment tool. Extract the loan_number from the task and call the tool immediately.

When you receive a task:
1. Extract loan_number from the task message
2. Call review_income_employment(loan_number)
3. Report the result concisely

Be concise and focused.""",
    tools=[review_income_employment]
)

underwriter_3 = AssistantAgent(
    name="underwriter_3",
    model_client=model_client,
    system_message="""You are an Asset Review Specialist.

CRITICAL: You MUST call the review_assets_reserves tool. Extract the loan_number from the task and call the tool immediately.

When you receive a task:
1. Extract loan_number from the task message
2. Call review_assets_reserves(loan_number)
3. Report the result concisely

Be concise and focused.""",
    tools=[review_assets_reserves]
)

underwriter_4 = AssistantAgent(
    name="underwriter_4",
    model_client=model_client,
    system_message="""You are a Property Review Specialist.

CRITICAL: You MUST call the review_property_appraisal tool. Extract the loan_number from the task and call the tool immediately.

When you receive a task:
1. Extract loan_number from the task message
2. Call review_property_appraisal(loan_number)
3. Report the result concisely

Be concise and focused.""",
    tools=[review_property_appraisal]
)

underwriter_5 = AssistantAgent(
    name="underwriter_5",
    model_client=model_client,
    system_message="""You are an Automated Underwriting Specialist.

CRITICAL: You MUST call the run_automated_underwriting tool. Extract the loan_number from the task and call the tool immediately.

When you receive a task:
1. Extract loan_number from the task message
2. Call run_automated_underwriting(loan_number)
3. Report the result concisely

Be concise and focused.""",
    tools=[run_automated_underwriting]
)

# Decision Maker (integrated into underwriter for simplicity)
decision_maker = AssistantAgent(
    name="decision_maker",
    model_client=model_client,
    system_message="""You are the Final Decision Maker.

CRITICAL: You MUST call one of the decision tools. Extract the loan_number from the task and call the appropriate tool immediately.

When you receive a task:
1. Extract loan_number from the task message
2. Analyze all reviews in the loan file
3. Make a decision by calling ONE tool:
   - All acceptable → issue_final_approval(loan_number)
   - Minor issues → issue_underwriting_conditions(loan_number, conditions)
   - Unacceptable → deny_loan(loan_number, reasons)
4. Report the decision clearly

Be concise and focused.""",
    tools=[issue_final_approval, issue_underwriting_conditions, deny_loan]
)


# ========== ORCHESTRATOR AGENT ==========

class OrchestratorAgent(BaseChatAgent):
    """
    Orchestrator Agent that orchestrates the entire loan workflow.

    Uses asyncio.gather() to send directed messages to worker agents concurrently.
    """

    def __init__(self, name: str = "orchestrator"):
        super().__init__(name, "Orchestrator Agent for Mortgage Loan Processing")

        # Store references to all worker agents
        self.brokers = [
            mortgage_broker_1, mortgage_broker_2, mortgage_broker_3,
            mortgage_broker_4, mortgage_broker_5
        ]

        self.processors = [
            loan_processor_1, loan_processor_2, loan_processor_3,
            loan_processor_4, loan_processor_5, loan_processor_6
        ]

        self.underwriters = [
            underwriter_1, underwriter_2, underwriter_3,
            underwriter_4, underwriter_5
        ]

        self.decision_maker = decision_maker

        # Cache teams for tool execution (created once, reused many times)
        from autogen_agentchat.teams import RoundRobinGroupChat
        from autogen_agentchat.conditions import MaxMessageTermination

        self._agent_teams = {}
        all_agents = self.brokers + self.processors + self.underwriters + [self.decision_maker]

        # Pre-create a single-agent team for each worker agent
        for agent in all_agents:
            self._agent_teams[agent.name] = RoundRobinGroupChat(
                [agent],
                termination_condition=MaxMessageTermination(5)
            )

    async def on_messages(
        self,
        messages: Sequence[ChatMessage],
        cancellation_token: CancellationToken | None = None
    ) -> Response:
        """
        Main workflow orchestration.

        Processes messages and coordinates all phases of loan processing.
        """
        # Extract loan number from message
        last_message = messages[-1]
        if isinstance(last_message, TextMessage):
            content = last_message.content
            if "loan" in content.lower():
                # Extract loan number (e.g., "Process loan LN-ABC123")
                parts = content.split()
                loan_number = parts[-1] if parts else "UNKNOWN"
            else:
                loan_number = content
        else:
            loan_number = "UNKNOWN"

        print(f"\n{'='*80}")
        print(f"🚀 ORCHESTRATOR: Processing loan {loan_number}")
        print(f"{'='*80}\n")

        results = {}

        # ========== PHASE 0: Rate Shopping ==========
        print(f"{_ts()} PHASE 0: Coordinating ALL 5 mortgage brokers CONCURRENTLY")
        print("-" * 80)

        broker_tasks = [
            ("Get rate quote from Wells Fargo", self.brokers[0]),
            ("Get rate quote from Bank of America", self.brokers[1]),
            ("Get rate quote from Chase", self.brokers[2]),
            ("Get rate quote from Quicken Loans", self.brokers[3]),
            ("Get rate quote from US Bank", self.brokers[4]),
        ]

        phase0_results = await self._execute_concurrent_tasks(
            loan_number, broker_tasks, "mortgage_broker"
        )
        results['phase0'] = phase0_results
        print(f"\n✅ PHASE 0 COMPLETE: All 5 brokers executed concurrently\n")

        # ========== PHASE 1: Loan Processing ==========
        print(f"{_ts()} PHASE 1: Coordinating ALL 6 loan processors CONCURRENTLY")
        print("-" * 80)

        processor_tasks = [
            ("Verify documents", self.processors[0]),
            ("Order credit report", self.processors[1]),
            ("Order appraisal", self.processors[2]),
            ("Order flood certification", self.processors[3]),
            ("Verify employment", self.processors[4]),
            ("Calculate ratios and submit to underwriting", self.processors[5]),
        ]

        phase1_results = await self._execute_concurrent_tasks(
            loan_number, processor_tasks, "loan_processor"
        )
        results['phase1'] = phase1_results
        print(f"\n✅ PHASE 1 COMPLETE: All 6 processors executed concurrently\n")

        # ========== PHASE 2: Underwriting ==========
        print(f"{_ts()} PHASE 2: Coordinating ALL 5 underwriters CONCURRENTLY")
        print("-" * 80)

        underwriter_tasks = [
            ("Review credit profile", self.underwriters[0]),
            ("Review income and employment", self.underwriters[1]),
            ("Review assets and reserves", self.underwriters[2]),
            ("Review property and appraisal", self.underwriters[3]),
            ("Run automated underwriting", self.underwriters[4]),
        ]

        phase2_results = await self._execute_concurrent_tasks(
            loan_number, underwriter_tasks, "underwriter"
        )
        results['phase2'] = phase2_results
        print(f"\n✅ PHASE 2 COMPLETE: All 5 underwriters executed concurrently\n")

        # ========== PHASE 3: Final Decision ==========
        print(f"{_ts()} PHASE 3: Making final decision")
        print("-" * 80)

        decision_result = await self._send_message_to_agent(
            self.decision_maker,
            loan_number,
            "Review all underwriting results and make final decision"
        )
        results['phase3'] = decision_result
        print(f"\n✅ PHASE 3 COMPLETE: Final decision made\n")

        print(f"{'='*80}")
        print(f"{_ts()} ✅ ORCHESTRATOR: Loan {loan_number} processing complete")
        print(f"{'='*80}\n")

        # Create final response
        response_message = TextMessage(
            content=f"Loan {loan_number} processing complete. Decision: {decision_result}",
            source=self.name
        )

        return Response(chat_message=response_message)

    async def _execute_concurrent_tasks(
        self,
        loan_number: str,
        tasks: List[tuple],
        agent_type: str
    ) -> List[str]:
        """
        Execute multiple agent tasks concurrently using asyncio.gather().

        Args:
            loan_number: The loan number being processed
            tasks: List of (task_description, agent) tuples
            agent_type: Type of agents being executed

        Returns:
            List of result strings from all agents
        """
        # Create all coroutines
        coroutines = [
            self._send_message_to_agent(agent, loan_number, task_desc)
            for task_desc, agent in tasks
        ]

        # Execute all concurrently
        results = await asyncio.gather(*coroutines)

        return results

    async def _send_message_to_agent(
        self,
        agent: AssistantAgent,
        loan_number: str,
        task_description: str
    ) -> str:
        """
        Send a message to a single agent and get its response.

        Uses the cached team for this agent - the team handles tool execution.

        Args:
            agent: The agent to send message to
            loan_number: The loan number
            task_description: Description of the task

        Returns:
            The agent's response as a string
        """
        print(f"  → {agent.name}: {task_description}")
        start = time.perf_counter()
        print(f"    {_ts()} {agent.name} START")

        # Get the cached team for this agent
        team = self._agent_teams[agent.name]

        # Run the task - the team's runtime handles tool execution automatically
        task_message = f"Task for loan {loan_number}: {task_description}"
        result = await team.run(task=task_message)

        duration = time.perf_counter() - start
        print(f"    {_ts()} {agent.name} DONE in {duration:.3f}s")

        # Extract the last message content
        if result.messages:
            return result.messages[-1].content
        return "No response"

    async def on_reset(self, cancellation_token: CancellationToken | None = None) -> None:
        """Reset the coordinator agent."""
        pass

    @property
    def produced_message_types(self) -> List[type[ChatMessage]]:
        """Return the types of messages this agent produces."""
        return [TextMessage]


# ========== ENTRY POINT ==========

async def process_loan_with_orchestrator(loan_number: str) -> Dict[str, Any]:
    """
    Process a loan using the OrchestratorAgent.

    Args:
        loan_number: The loan number to process

    Returns:
        Dictionary with results from all phases
    """
    orchestrator = OrchestratorAgent()

    # Send initial message to orchestrator
    initial_message = TextMessage(
        content=f"Process loan {loan_number}",
        source="user"
    )

    response = await orchestrator.on_messages([initial_message], cancellation_token=None)

    return {
        "loan_number": loan_number,
        "status": "complete",
        "response": response.chat_message.content if hasattr(response, 'chat_message') else str(response)
    }


__all__ = ['OrchestratorAgent', 'process_loan_with_orchestrator']
