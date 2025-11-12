"""
Mortgage Closing Workflow - Title & Escrow + Realtor + Seller + Borrower
Steps 32-43 from the mortgage workflow diagram
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
from typing import Dict, List

load_dotenv()
API_KEY = os.environ.get("OPENAI_API_KEY")

model_client4o = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=API_KEY,
)


# ============== NOTIFICATION SIMULATION ==============

def simulate_notification(recipient: str, message_type: str, content: str) -> str:
    """Simulate sending email/notification to non-agent participants (Borrower/Seller)"""
    notification = f"""
    ╔════════════════════════════════════════════════════════════╗
    ║  📧 {message_type.upper()} NOTIFICATION                    
    ╠════════════════════════════════════════════════════════════╣
    ║  TO: {recipient}                                           
    ║                                                            
    ║  {content}
    ╚════════════════════════════════════════════════════════════╝
    """
    print(notification)
    return f"✅ Notification sent to {recipient} successfully"


# ============== TOOLS ==============

async def send_funding_instructions(
        loan_amount: float,
        property_address: str,
        borrower_name: str,
        closing_date: str,
        loan_number: str
) -> str:
    """Loan Officer sends funding and closing instructions to Title & Escrow."""
    instructions = f"""
    FUNDING INSTRUCTIONS - Loan #{loan_number}
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Borrower: {borrower_name}
    Property: {property_address}
    Loan Amount: ${loan_amount:,.2f}
    Scheduled Closing: {closing_date}

    Instructions:
    - Prepare Closing Disclosure (CD)
    - Coordinate signing appointments
    - Verify clear title
    - Obtain seller payoff information
    - Prepare settlement statements
    - Arrange recording with county
    """
    return f"✅ Funding instructions sent to Title & Escrow.\n{instructions}"


async def coordinate_signing_schedule(
        borrower_name: str,
        seller_name: str,
        property_address: str,
        proposed_date: str,
        proposed_time: str
) -> str:
    """Realtor coordinates signing schedule with Title & Escrow."""
    schedule = f"""
    SIGNING COORDINATION REQUEST
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Property: {property_address}
    Proposed Date: {proposed_date}
    Proposed Time: {proposed_time}

    Parties:
    - Buyer: {borrower_name}
    - Seller: {seller_name}

    Realtor confirms both parties are available.
    Awaiting Title Officer confirmation.
    """
    return f"✅ Signing schedule coordinated.\n{schedule}"


async def send_closing_disclosure(
        borrower_name: str,
        loan_amount: float,
        closing_costs: float,
        cash_to_close: float,
        closing_date: str,
        signing_location: str
) -> str:
    """Title Officer sends Closing Disclosure to Borrower."""
    cd_content = f"""
    📄 CLOSING DISCLOSURE (CD)

    Dear {borrower_name},

    Your loan is ready to close! Please review the following details:

    Loan Amount: ${loan_amount:,.2f}
    Total Closing Costs: ${closing_costs:,.2f}
    Cash to Close: ${cash_to_close:,.2f}

    Signing Appointment:
    Date: {closing_date}
    Location: {signing_location}

    Please bring:
    - Government-issued photo ID
    - Cashier's check or wire confirmation for ${cash_to_close:,.2f}

    Review this document carefully. You have 3 business days to review before closing.

    Best regards,
    Title & Escrow Department
    """

    simulate_notification(borrower_name, "Closing Disclosure", cd_content)
    return f"✅ Closing Disclosure sent to {borrower_name}"


async def send_seller_settlement_statement(
        seller_name: str,
        sale_price: float,
        payoff_amount: float,
        closing_costs: float,
        net_proceeds: float,
        closing_date: str,
        signing_location: str
) -> str:
    """Title Officer sends Seller Settlement Statement."""
    settlement_content = f"""
    📄 SELLER SETTLEMENT STATEMENT

    Dear {seller_name},

    Your property sale is ready to close!

    Sale Price: ${sale_price:,.2f}
    Less: Existing Loan Payoff: -${payoff_amount:,.2f}
    Less: Closing Costs: -${closing_costs:,.2f}
    ════════════════════════════════════
    Net Proceeds to You: ${net_proceeds:,.2f}

    Signing Appointment:
    Date: {closing_date}
    Location: {signing_location}

    Required Documents from You:
    1. Current mortgage payoff statement
    2. HOA demand letter (if applicable)
    3. Signed deed
    4. Wire transfer instructions for proceeds

    Please bring photo ID to signing.

    Best regards,
    Title & Escrow Department
    """

    simulate_notification(seller_name, "Settlement Statement", settlement_content)
    return f"✅ Seller Settlement Statement sent to {seller_name}"


async def request_seller_documents(
        seller_name: str,
        property_address: str
) -> str:
    """Title Officer requests required documents from Seller."""
    request_content = f"""
    📋 DOCUMENT REQUEST

    Dear {seller_name},

    To complete the closing for {property_address}, please provide:

    Required Documents:
    1. ✓ Mortgage Payoff Statement (from your lender)
    2. ✓ HOA Demand Letter (if property is in HOA)
    3. ✓ Signed Deed (will prepare for your signature)
    4. ✓ Wire Instructions (for receiving your proceeds)

    Please submit these documents within 2 business days.

    You can email documents to: closing@titleescrow.com
    Or upload via secure portal: https://titleescrow.com/upload

    Thank you,
    Title & Escrow Department
    """

    simulate_notification(seller_name, "Document Request", request_content)
    return f"✅ Document request sent to {seller_name}"


async def receive_seller_documents(
        seller_name: str,
        payoff_amount: float,
        hoa_amount: float,
        has_deed: bool,
        wire_routing: str,
        wire_account: str
) -> Dict:
    """Simulate receiving seller documents (seller is not an agent)."""

    # Simulate seller providing documents
    seller_response = f"""
    📥 SELLER DOCUMENTS RECEIVED

    From: {seller_name}

    Documents Submitted:
    ✓ Mortgage Payoff: ${payoff_amount:,.2f}
    ✓ HOA Demand: ${hoa_amount:,.2f}
    ✓ Deed: {"Signed" if has_deed else "Pending"}
    ✓ Wire Info: {wire_routing} / {wire_account}
    """

    print(seller_response)

    return {
        "status": "received",
        "payoff_amount": payoff_amount,
        "hoa_amount": hoa_amount,
        "has_deed": has_deed,
        "wire_routing": wire_routing,
        "wire_account": wire_account
    }


async def verify_funds_and_title(
        loan_amount: float,
        buyer_funds: float,
        seller_payoff: float,
        property_address: str
) -> str:
    """Title Officer verifies funds and confirms clear title."""

    total_funds_available = loan_amount + buyer_funds
    total_required = seller_payoff

    verification = f"""
    FUNDS & TITLE VERIFICATION
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Property: {property_address}

    FUNDS VERIFICATION:
    Lender Funding: ${loan_amount:,.2f}
    Buyer Cash: ${buyer_funds:,.2f}
    Total Available: ${total_funds_available:,.2f}

    Seller Payoff Required: ${seller_payoff:,.2f}
    Surplus: ${total_funds_available - total_required:,.2f}

    TITLE VERIFICATION:
    ✓ Title search completed
    ✓ No liens or encumbrances found
    ✓ Title insurance policy prepared
    ✓ Clear to close

    STATUS: ✅ VERIFIED - Ready for recording
    """

    if total_funds_available >= total_required:
        return f"✅ Funds and title verified successfully.\n{verification}"
    else:
        return f"❌ INSUFFICIENT FUNDS - Short ${total_required - total_funds_available:,.2f}\n{verification}"


async def confirm_funding_and_recording(
        property_address: str,
        recording_number: str,
        recording_date: str
) -> str:
    """Title Officer confirms funding and recording completion to Realtor."""
    confirmation = f"""
    FUNDING & RECORDING CONFIRMATION
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Property: {property_address}
    Recording #: {recording_number}
    Recording Date: {recording_date}

    Status: ✅ RECORDED

    Actions Completed:
    ✓ Deed recorded with county
    ✓ Funds disbursed to seller
    ✓ Title policy issued to buyer
    ✓ Lender documents recorded

    The property is now officially transferred to the buyer.
    Realtor may deliver keys and possession.
    """
    return f"✅ Funding and recording confirmed.\n{confirmation}"


async def wire_seller_proceeds(
        seller_name: str,
        net_proceeds: float,
        wire_routing: str,
        wire_account: str
) -> str:
    """Title Officer wires net proceeds to Seller."""
    wire_content = f"""
    💰 PROCEEDS WIRE TRANSFER

    Dear {seller_name},

    Your net proceeds have been wired!

    Amount: ${net_proceeds:,.2f}
    Bank Routing: {wire_routing}
    Account: ...{wire_account[-4:]}

    Wire should arrive within 1-2 business hours.

    Thank you for your business!
    Title & Escrow Department
    """

    simulate_notification(seller_name, "Wire Transfer", wire_content)
    return f"✅ Wire sent to {seller_name}: ${net_proceeds:,.2f}"


async def send_funding_confirmation_to_lender(
        loan_officer_name: str,
        loan_number: str,
        property_address: str,
        recording_number: str
) -> str:
    """Title Officer sends funding confirmation and archival docs to Loan Officer."""
    confirmation = f"""
    FUNDING CONFIRMATION & ARCHIVAL
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Loan #: {loan_number}
    Property: {property_address}
    Recording #: {recording_number}

    Documents Archived:
    ✓ Closing Disclosure (MCD)
    ✓ Note and Deed of Trust
    ✓ Title Policy
    ✓ Recording Confirmation
    ✓ Settlement Statement

    Status: ✅ LOAN CLOSED & FUNDED

    All documents uploaded to MISMO archive system.
    """
    return f"✅ Funding confirmation sent to {loan_officer_name}.\n{confirmation}"


async def deliver_keys_to_buyer(
        borrower_name: str,
        property_address: str,
        possession_date: str
) -> str:
    """Realtor delivers keys to Borrower after recording."""
    keys_content = f"""
    🔑 KEYS & POSSESSION

    Congratulations {borrower_name}!

    Your property has been recorded and you now officially own:
    {property_address}

    Possession Date: {possession_date}

    Attached:
    - Keys to front door, back door, garage
    - Garage door opener codes
    - HOA contact information
    - Utility contact information

    Welcome to your new home! 🏡

    Best wishes,
    Your Realtor
    """

    simulate_notification(borrower_name, "Keys & Possession", keys_content)
    return f"✅ Keys delivered to {borrower_name}"


async def send_welcome_package(
        borrower_name: str,
        loan_number: str,
        property_address: str,
        servicing_company: str,
        first_payment_date: str
) -> str:
    """Loan Officer sends welcome package to Borrower."""
    welcome_content = f"""
    🎉 CONGRATULATIONS ON YOUR NEW HOME!

    Dear {borrower_name},

    Welcome to homeownership! Your loan has been successfully closed.

    Loan Details:
    Loan Number: {loan_number}
    Property: {property_address}

    Loan Servicing:
    Your loan is serviced by: {servicing_company}
    First Payment Due: {first_payment_date}

    Important Information:
    - Set up autopay at: www.{servicing_company.lower().replace(' ', '')}.com
    - Download the mobile app for easy payments
    - Your escrow account will pay property taxes and insurance
    - Keep your homeowner's insurance active

    Resources:
    - Mortgage statements: Online portal
    - Customer service: 1-800-XXX-XXXX
    - Tax forms: Available each January

    Thank you for choosing us for your home loan!

    Sincerely,
    Your Loan Officer Team
    """

    simulate_notification(borrower_name, "Welcome Package", welcome_content)
    return f"✅ Welcome package sent to {borrower_name}"


# ============== ORCHESTRATOR AGENT ==============

orchestrator_agent = AssistantAgent(
    "orchestrator_agent",
    model_client=model_client4o,
    handoffs=["loan_officer_agent", "title_escrow_agent", "realtor_agent"],
    system_message="""You are the orchestrator agent for the mortgage closing workflow.

    Workflow sequence:
    1. loan_officer_agent → Initiates closing by sending funding instructions
    2. title_escrow_agent → Receives instructions, prepares closing documents
    3. realtor_agent → Coordinates signing schedule with title officer
    4. title_escrow_agent → Sends documents to borrower/seller, receives responses
    5. title_escrow_agent → Verifies funds and title
    6. title_escrow_agent → Confirms recording to realtor
    7. realtor_agent → Delivers keys to borrower
    8. loan_officer_agent → Sends welcome package

    Your job:
    - Route between loan_officer, title_escrow, and realtor agents
    - Monitor workflow progress through the closing stages
    - Ensure proper handoffs at each stage

    Only handoff to the most appropriate agent based on current workflow stage.
    """,
    reflect_on_tool_use=True,
    tools=[]
)

# ============== LOAN OFFICER AGENT ==============

loan_officer_agent = AssistantAgent(
    "loan_officer_agent",
    model_client=model_client4o,
    handoffs=["orchestrator_agent"],
    system_message="""You are a Loan Officer managing the closing process.

    RESPONSIBILITIES:

    1. INITIATE CLOSING:
       - When you receive a loan ready for closing, call send_funding_instructions
       - Provide: loan amount, property address, borrower name, closing date, loan number
       - Handoff to orchestrator to route to title_escrow_agent

    2. RECEIVE CONFIRMATION:
       - When title officer confirms funding and recording is complete
       - Call send_welcome_package to congratulate borrower
       - Use TERMINATE to end the workflow

    DO NOT handoff until you have called the appropriate tool.
    Always handoff to orchestrator_agent after completing your actions.
    """,
    reflect_on_tool_use=True,
    tools=[send_funding_instructions, send_welcome_package]
)

# ============== TITLE & ESCROW AGENT ==============

title_escrow_agent = AssistantAgent(
    "title_escrow_agent",
    model_client=model_client4o,
    handoffs=["orchestrator_agent"],
    system_message="""You are a Title & Escrow Officer managing the closing process.

    RESPONSIBILITIES:

    1. RECEIVE FUNDING INSTRUCTIONS (from Loan Officer):
       - Review the funding instructions
       - Acknowledge receipt
       - Prepare to coordinate with realtor
       - Handoff to orchestrator

    2. COORDINATE WITH REALTOR:
       - Once realtor provides signing schedule, acknowledge it
       - Proceed to send closing documents

    3. SEND CLOSING DOCUMENTS:
       - Call send_closing_disclosure (to borrower - this is a notification)
       - Call send_seller_settlement_statement (to seller - this is a notification)
       - Call request_seller_documents (to seller - this is a notification)
       - These are notifications, not handoffs

    4. RECEIVE SELLER DOCUMENTS:
       - Call receive_seller_documents (simulates seller providing docs)
       - This returns seller's payoff info, HOA, deed, wire instructions

    5. VERIFY FUNDS & TITLE:
       - Call verify_funds_and_title
       - Ensure all funds are available and title is clear

    6. CONFIRM RECORDING:
       - Call confirm_funding_and_recording (to realtor)
       - Call wire_seller_proceeds (to seller - this is a notification)
       - Call send_funding_confirmation_to_lender (to loan officer)

    7. HANDOFF:
       - After sending confirmations, handoff to orchestrator
       - Orchestrator will route to realtor for key delivery

    DO NOT handoff until you have completed all your tools in sequence.
    Document each step clearly.
    """,
    reflect_on_tool_use=True,
    tools=[
        send_closing_disclosure,
        send_seller_settlement_statement,
        request_seller_documents,
        receive_seller_documents,
        verify_funds_and_title,
        confirm_funding_and_recording,
        wire_seller_proceeds,
        send_funding_confirmation_to_lender
    ]
)

# ============== REALTOR AGENT ==============

realtor_agent = AssistantAgent(
    "realtor_agent",
    model_client=model_client4o,
    handoffs=["orchestrator_agent"],
    system_message="""You are a Realtor coordinating the closing process.

    RESPONSIBILITIES:

    1. COORDINATE SIGNING SCHEDULE:
       - When you receive notification that title is preparing closing
       - Call coordinate_signing_schedule
       - Provide proposed date, time, and confirm both parties are available
       - Handoff to orchestrator to route back to title officer

    2. DELIVER KEYS:
       - After title officer confirms recording is complete
       - Call deliver_keys_to_buyer (this is a notification to borrower)
       - Handoff to orchestrator to route to loan officer for welcome package

    3. TERMINATION:
       - After delivering keys, your job is done
       - Handoff to orchestrator

    DO NOT handoff until you have called the appropriate tool.
    Always handoff to orchestrator_agent after completing your actions.
    """,
    reflect_on_tool_use=True,
    tools=[
        coordinate_signing_schedule,
        deliver_keys_to_buyer
    ]
)

# ============== SWARM TEAM ==============

termination = HandoffTermination(target="user") | TextMentionTermination("TERMINATE")

team = Swarm(
    [orchestrator_agent, loan_officer_agent, title_escrow_agent, realtor_agent],
    termination_condition=termination,
    max_turns=30
)

# ============== TASK DEFINITIONS ==============

task_standard_closing = """
Loan is approved and ready for closing!

Loan Details:
- Borrower: John and Mary Doe
- Seller: Robert Smith
- Loan Number: LN-2024-12345
- Property Address: 123 Maple Street, Springfield, IL 62701
- Loan Amount: $320,000
- Sale Price: $400,000
- Buyer's Down Payment: $80,000 (already verified)
- Closing Date: 2025-11-20
- Proposed Signing Time: 2:00 PM

Seller Information:
- Existing Mortgage Payoff: $250,000
- HOA Fees: $500
- Seller Closing Costs: $8,000
- Net Proceeds to Seller: $141,500

Closing Costs:
- Buyer Closing Costs: $12,000
- Cash to Close (from buyer): $92,000 (down payment + closing costs)

Please initiate the closing process and coordinate all parties to complete the transaction.
"""

# ============== RUN FUNCTION ==============

async def run_team_stream() -> None:
    """Run the closing workflow."""
    print("\n" + "=" * 70)
    print("MORTGAGE CLOSING WORKFLOW - TITLE & ESCROW + REALTOR + SELLER")
    print("=" * 70 + "\n")

    task_result = await Console(team.run_stream(task=task_standard_closing))
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

    print("\n" + "=" * 70)
    print("CLOSING WORKFLOW COMPLETED")
    print("=" * 70)


# ============== MAIN ==============

if __name__ == "__main__":
    asyncio.run(run_team_stream())