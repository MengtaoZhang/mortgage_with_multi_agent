"""
Agent Pool Architecture with Direct Message Assignment

This demonstrates concurrent loan processing using:
- Multiple loan_processor agents (pool of 3)
- Multiple underwriter agents (pool of 3)
- Direct message assignment by coordinator
- Handoffs maintained for agent interaction
"""

import asyncio
import os
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import Swarm
from autogen_agentchat.ui import Console
from dotenv import load_dotenv

from agents_pool import create_agent_pool_team, NUM_LOAN_PROCESSORS, NUM_UNDERWRITERS
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


def display_menu():
    print("\n" + "="*80)
    print("MORTGAGE UNDERWRITING - AGENT POOL ARCHITECTURE")
    print("="*80)
    print(f"Architecture: Agent Pool with Direct Message Assignment")
    print("")
    print(f"Agent Pool Configuration:")
    print(f"  • {NUM_LOAN_PROCESSORS} Loan Processor agents (can process {NUM_LOAN_PROCESSORS} loans concurrently)")
    print(f"  • {NUM_UNDERWRITERS} Underwriter agents (can underwrite {NUM_UNDERWRITERS} loans concurrently)")
    print(f"  • 1 Coordinator (assigns loans to specific agents)")
    print("")
    print("How It Works:")
    print("  1. Coordinator receives loan(s)")
    print("  2. Coordinator assigns to SPECIFIC processor (direct message)")
    print("     Example: 'loan_processor_1, process loan LN-ABC'")
    print("  3. LoanProcessor works on loan (tools run in parallel)")
    print("  4. LoanProcessor handoffs to SPECIFIC underwriter")
    print("  5. Underwriter reviews loan (reviews run in parallel)")
    print("  6. Underwriter handoffs back to Coordinator")
    print("  7. Coordinator reports final decision")
    print("")
    print("Concurrency:")
    print("  • Multiple loans can be processed simultaneously")
    print("  • Each loan assigned to different agent instance")
    print("  • Agents use handoffs to interact (message passing)")
    print("  • Direct assignment enables load distribution")
    print("")
    print("="*80)
    print(list_all_scenarios())
    print("\nSelect option:")
    print("  1. Process Single Loan (Clean Approval)")
    print("  2. Process Single Loan (Conditional Approval)")
    print("  3. Process 3 Loans Concurrently (demonstrate pool)")
    print("  9. Show Storage Statistics")
    print("  0. Exit")
    print("="*80)


async def run_single_loan(team, loan_number: str):
    """Process a single loan through the agent pool"""

    print("\n" + "="*80)
    print(f"🚀 PROCESSING SINGLE LOAN: {loan_number}")
    print("="*80)
    print("\nWorkflow:")
    print("  Coordinator → assigns to loan_processor_1")
    print("  loan_processor_1 → processes loan (5 tools in parallel)")
    print("  loan_processor_1 → handoffs to underwriter_1")
    print("  underwriter_1 → reviews loan (4 reviews in parallel)")
    print("  underwriter_1 → handoffs to coordinator")
    print("  Coordinator → TERMINATE")
    print("\n" + "="*80 + "\n")

    task = f"""
New loan application received.
Loan Number: {loan_number}

Please assign this loan to an available loan processor using direct message assignment.

The loan file is ready at: ./loan_files/active/{loan_number}.json

Assign to a SPECIFIC processor, for example:
"loan_processor_1, please process loan {loan_number}"
"""

    result = await Console(team.run_stream(task=task))

    print("\n" + "="*80)
    print("✅ SINGLE LOAN PROCESSING COMPLETED")
    print("="*80)
    print(f"\n📁 Loan file: ./loan_files/active/{loan_number}.json")

    return result


async def run_concurrent_loans(team):
    """Process 3 loans concurrently to demonstrate pool capabilities"""

    print("\n" + "="*80)
    print("🚀 PROCESSING 3 LOANS CONCURRENTLY")
    print("="*80)

    # Create 3 different scenarios
    print("\nCreating 3 test loans...")
    scenario1 = create_scenario_clean_approval()
    loan1 = scenario1.split("Loan Number: ")[1].split("\n")[0]

    scenario2 = create_scenario_conditional_approval()
    loan2 = scenario2.split("Loan Number: ")[1].split("\n")[0]

    scenario3 = create_scenario_clean_approval()
    loan3 = scenario3.split("Loan Number: ")[1].split("\n")[0]

    print(f"\n✅ Created 3 loans:")
    print(f"   • Loan A: {loan1} (Clean Approval)")
    print(f"   • Loan B: {loan2} (Conditional Approval)")
    print(f"   • Loan C: {loan3} (Clean Approval)")

    print("\n" + "="*80)
    print("Expected Workflow:")
    print("="*80)
    print(f"  Coordinator → assigns {loan1} to loan_processor_1")
    print(f"  Coordinator → assigns {loan2} to loan_processor_2")
    print(f"  Coordinator → assigns {loan3} to loan_processor_3")
    print("")
    print("  [All 3 processors work IN PARALLEL]")
    print("")
    print(f"  loan_processor_1 → handoff to underwriter_1")
    print(f"  loan_processor_2 → handoff to underwriter_2")
    print(f"  loan_processor_3 → handoff to underwriter_3")
    print("")
    print("  [All 3 underwriters work IN PARALLEL]")
    print("")
    print("  All underwriters → handoff to coordinator")
    print("  Coordinator → TERMINATE")
    print("\n" + "="*80 + "\n")

    task = f"""
Three new loan applications received for CONCURRENT processing.

Loan Numbers:
- Loan A: {loan1}
- Loan B: {loan2}
- Loan C: {loan3}

Please assign these loans to DIFFERENT loan processors for concurrent processing:
- Assign {loan1} to loan_processor_1
- Assign {loan2} to loan_processor_2
- Assign {loan3} to loan_processor_3

Use direct message assignment for each. All processors can work in parallel.

When all 3 loans complete their underwriting, report final results and TERMINATE.
"""

    result = await Console(team.run_stream(task=task))

    print("\n" + "="*80)
    print("✅ CONCURRENT PROCESSING COMPLETED")
    print("="*80)
    print(f"\n📁 Loan files:")
    print(f"   • ./loan_files/active/{loan1}.json")
    print(f"   • ./loan_files/active/{loan2}.json")
    print(f"   • ./loan_files/active/{loan3}.json")

    return result, [loan1, loan2, loan3]


async def main():
    """Main entry point"""

    # Create agent pool team
    print("\n" + "="*80)
    print("INITIALIZING AGENT POOL")
    print("="*80)

    team_dict = create_agent_pool_team()
    all_agents = team_dict['all_agents']

    print(f"\n✅ Created {len(all_agents)} agents:")
    print(f"   • 1 Coordinator")
    print(f"   • {NUM_LOAN_PROCESSORS} Loan Processors")
    print(f"   • {NUM_UNDERWRITERS} Underwriters")

    # Create Swarm team
    termination = TextMentionTermination("TERMINATE")
    team = Swarm(
        participants=all_agents,
        termination_condition=termination,
        max_turns=100
    )

    print(f"\n✅ Team ready for concurrent processing")

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

            if choice == 1:
                # Single loan - Clean Approval
                scenario = create_scenario_clean_approval()
                loan_number = scenario.split("Loan Number: ")[1].split("\n")[0]
                print(scenario)

                confirm = input(f"\n▶️  Process loan {loan_number}? (y/n): ")
                if confirm.lower() == 'y':
                    await run_single_loan(team, loan_number)

                    file_manager.print_storage_stats()
                    write_count = file_manager._write_counts.get(loan_number, 0)
                    print(f"\n📝 Total file writes: {write_count}")

            elif choice == 2:
                # Single loan - Conditional Approval
                scenario = create_scenario_conditional_approval()
                loan_number = scenario.split("Loan Number: ")[1].split("\n")[0]
                print(scenario)

                confirm = input(f"\n▶️  Process loan {loan_number}? (y/n): ")
                if confirm.lower() == 'y':
                    await run_single_loan(team, loan_number)

                    file_manager.print_storage_stats()
                    write_count = file_manager._write_counts.get(loan_number, 0)
                    print(f"\n📝 Total file writes: {write_count}")

            elif choice == 3:
                # Three loans concurrently
                confirm = input(f"\n▶️  Process 3 loans concurrently? (y/n): ")
                if confirm.lower() == 'y':
                    result, loan_numbers = await run_concurrent_loans(team)

                    file_manager.print_storage_stats()

                    print(f"\n📝 File writes per loan:")
                    for ln in loan_numbers:
                        write_count = file_manager._write_counts.get(ln, 0)
                        print(f"   • {ln}: {write_count} writes")

            else:
                print("\n❌ Invalid choice. Please select 0-3 or 9.")

            if choice in [1, 2, 3]:
                another = input("\n🔄 Run another workflow? (y/n): ")
                if another.lower() != 'y':
                    print("\n👋 Exiting... Thank you!")
                    break

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
    ║          AGENT POOL ARCHITECTURE WITH DIRECT ASSIGNMENT          ║
    ║                                                                  ║
    ║  Architecture:                                                   ║
    ║    • 3 Loan Processor agents (pool)                              ║
    ║    • 3 Underwriter agents (pool)                                 ║
    ║    • 1 Coordinator (assigns work)                                ║
    ║                                                                  ║
    ║  Features:                                                       ║
    ║    • Direct message assignment to specific agents                ║
    ║    • Concurrent processing of multiple loans                     ║
    ║    • Handoffs maintained for agent interaction                   ║
    ║    • Load distribution across agent pool                         ║
    ║    • Tools run in parallel within each agent                     ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(main())
