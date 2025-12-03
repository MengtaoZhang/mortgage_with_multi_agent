"""
Main orchestration with storage monitoring
"""

import asyncio
import os
from autogen_agentchat.conditions import HandoffTermination, TextMentionTermination
from autogen_agentchat.messages import HandoffMessage
from autogen_agentchat.teams import Swarm
from autogen_agentchat.ui import Console
from dotenv import load_dotenv

from agents import orchestrator_agent, loan_processor_agent, underwriter_agent
from file_manager import file_manager  # Import singleton instance
from scenarios import (
    create_scenario_clean_approval,
    create_scenario_conditional_approval,
    create_scenario_appraisal_low,
    create_scenario_high_risk_denial,
    create_scenario_flood_zone_high_risk,
    list_all_scenarios
)

load_dotenv()

if not os.environ.get("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in environment variables")

termination = HandoffTermination(target="user") | TextMentionTermination("TERMINATE")

team = Swarm(
    [orchestrator_agent, loan_processor_agent, underwriter_agent],
    termination_condition=termination,
    max_turns=50
)


def display_menu():
    print("\n" + "="*80)
    print("MORTGAGE UNDERWRITING SYSTEM - AUTONOMOUS AGENT DEMO")
    print("="*80)
    print(list_all_scenarios())
    print("\nSelect a scenario to run:")
    print("  1. Clean Approval (Happy Path)")
    print("  2. Conditional Approval (Moderate Risk)")
    print("  3. Low Appraisal (Value Issue)")
    print("  4. High Risk Denial (Poor Credit/High DTI)")
    print("  5. Flood Zone High Risk (Climate Impact)")
    print("  9. Show Storage Statistics")
    print("  0. Exit")
    print("="*80)


def create_scenario(choice: int) -> str:
    scenarios = {
        1: create_scenario_clean_approval,
        2: create_scenario_conditional_approval,
        3: create_scenario_appraisal_low,
        4: create_scenario_high_risk_denial,
        5: create_scenario_flood_zone_high_risk
    }

    if choice in scenarios:
        scenario_description = scenarios[choice]()
        print(scenario_description)
        loan_number = scenario_description.split("Loan Number: ")[1].split("\n")[0]
        return loan_number
    else:
        return None


async def run_workflow(loan_number: str) -> None:
    """Run the complete underwriting workflow"""

    print("\n" + "="*80)
    print(f"🚀 STARTING WORKFLOW FOR LOAN #{loan_number}")
    print("="*80)
    print("\n📊 WORKFLOW STAGES:")
    print("  1. Orchestrator routes to Loan Processor")
    print("  2. Loan Processor: Concurrent document collection & verification")
    print("  3. Loan Processor: Calculate ratios → Submit to underwriting")
    print("  4. Orchestrator routes to Underwriter")
    print("  5. Underwriter: Automated UW → Concurrent manual reviews")
    print("  6. Underwriter: Issue decision (Approve/Condition/Deny)")
    print("  7. If conditions: Route back to LP → Clear → Route to UW")
    print("  8. Final approval or denial → TERMINATE")
    print("\n" + "="*80 + "\n")

    initial_task = f"""
New loan application received and ready for processing.

Loan Number: {loan_number}

The loan file has been created and saved. Please route this to the appropriate agent to begin processing.

All loan details are stored in the file system at: ./loan_files/active/{loan_number}.json

The loan processor should:
1. Verify documents
2. Order credit report, appraisal, flood cert, and verify employment (ALL CONCURRENTLY)
3. Calculate financial ratios
4. Submit to underwriting

Route to loan_processor_agent to begin.
"""

    try:
        task_result = await Console(team.run_stream(task=initial_task))
        last_message = task_result.messages[-1]

        while isinstance(last_message, HandoffMessage) and last_message.target == "user":
            user_message = input("\n👤 User input needed: ")

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

        print("\n" + "="*80)
        print("✅ WORKFLOW COMPLETED")
        print("="*80)
        print(f"\n📁 Final loan file saved at: ./loan_files/active/{loan_number}.json")
        print(f"📊 Review the file to see complete audit trail and all decisions made")

        # Show storage statistics
        file_manager.print_storage_stats()

        # Show write count for this loan
        write_count = file_manager._write_counts.get(loan_number, 0)
        print(f"📝 Total file writes for this loan: {write_count}")

    except Exception as e:
        print(f"\n❌ ERROR during workflow execution:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Main entry point"""

    while True:
        display_menu()

        try:
            choice = int(input("\n👉 Enter your choice (0-9): "))

            if choice == 0:
                print("\n👋 Exiting... Thank you!")
                break

            if choice == 9:
                file_manager.print_storage_stats()
                continue

            loan_number = create_scenario(choice)

            if loan_number:
                confirm = input(f"\n▶️  Run workflow for loan {loan_number}? (y/n): ")
                if confirm.lower() == 'y':
                    await run_workflow(loan_number)

                    another = input("\n🔄 Run another scenario? (y/n): ")
                    if another.lower() != 'y':
                        print("\n👋 Exiting... Thank you!")
                        break
            else:
                print("\n❌ Invalid choice. Please select 1-5 or 9.")

        except ValueError:
            print("\n❌ Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║        MORTGAGE UNDERWRITING - AUTONOMOUS AGENTS SYSTEM          ║
    ║                                                                  ║
    ║  Features:                                                       ║
    ║    • Concurrent task execution                                   ║
    ║    • Thread-safe file operations                                 ║
    ║    • Automatic backup & audit trail rotation                     ║
    ║    • Storage monitoring & optimization                           ║
    ║    • External system simulation (with exceptions)                ║
    ║    • Complete audit trail                                        ║
    ║    • Pydantic data validation                                    ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(main())