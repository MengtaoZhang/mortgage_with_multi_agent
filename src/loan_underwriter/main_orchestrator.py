"""
Orchestrator Agent Architecture - Main Runtime

Pure agent architecture with TRUE concurrent execution.

Architecture:
- 1 OrchestratorAgent (orchestrator)
- 3 worker agent types: mortgage_broker, loan_processor, underwriter
- Orchestrator sends directed messages to workers concurrently via asyncio.gather()
"""

import asyncio
import os
from dotenv import load_dotenv

from agents_with_coordinator import process_loan_with_orchestrator
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
    print("MORTGAGE UNDERWRITING - ORCHESTRATOR AGENT ARCHITECTURE")
    print("="*80)
    print("Architecture: Pure Agent Architecture with TRUE Concurrent Execution")
    print("")
    print("Agent Types:")
    print("  • 1 OrchestratorAgent (orchestrator)")
    print("  • 5 Mortgage Brokers (rate-shopping)")
    print("  • 6 Loan Processors (task-specialized)")
    print("  • 5 Underwriters (review-specialized)")
    print("  • 1 Decision Maker")
    print("")
    print("How It Works (for ONE loan):")
    print("")
    print("PHASE 0 - Rate Shopping (TRUE CONCURRENT):")
    print("  Orchestrator uses asyncio.gather() to send messages to ALL 5 brokers:")
    print("    • mortgage_broker_1 → 'Query Wells Fargo'")
    print("    • mortgage_broker_2 → 'Query Bank of America'")
    print("    • mortgage_broker_3 → 'Query Chase'")
    print("    • mortgage_broker_4 → 'Query Quicken Loans'")
    print("    • mortgage_broker_5 → 'Query US Bank'")
    print("  All 5 execute IN PARALLEL simultaneously!")
    print("")
    print("PHASE 1 - Loan Processing (TRUE CONCURRENT):")
    print("  Orchestrator uses asyncio.gather() to send messages to ALL 6 processors:")
    print("    • loan_processor_1 → 'Verify documents'")
    print("    • loan_processor_2 → 'Order credit report'")
    print("    • loan_processor_3 → 'Order appraisal'")
    print("    • loan_processor_4 → 'Order flood cert'")
    print("    • loan_processor_5 → 'Verify employment'")
    print("    • loan_processor_6 → 'Calculate ratios & submit'")
    print("  All 6 execute IN PARALLEL simultaneously!")
    print("")
    print("PHASE 2 - Underwriting (TRUE CONCURRENT):")
    print("  Orchestrator uses asyncio.gather() to send messages to ALL 5 underwriters:")
    print("    • underwriter_1 → 'Review credit'")
    print("    • underwriter_2 → 'Review income'")
    print("    • underwriter_3 → 'Review assets'")
    print("    • underwriter_4 → 'Review property'")
    print("    • underwriter_5 → 'Run automated underwriting'")
    print("  All 5 execute IN PARALLEL simultaneously!")
    print("")
    print("PHASE 3 - Final Decision:")
    print("  • decision_maker → Issue approval/conditions/denial")
    print("")
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


async def run_workflow(loan_number: str):
    """Run orchestrator workflow for a single loan"""

    print("\n" + "="*80)
    print(f"🚀 PROCESSING LOAN: {loan_number}")
    print("="*80)
    print("\nExpected Workflow:")
    print("-" * 80)
    print("PHASE 0: Orchestrator sends messages to ALL 5 brokers IN PARALLEL")
    print("  → All 5 execute simultaneously (true concurrency)")
    print("")
    print("PHASE 1: Orchestrator sends messages to ALL 6 processors IN PARALLEL")
    print("  → All 6 execute simultaneously (true concurrency)")
    print("")
    print("PHASE 2: Orchestrator sends messages to ALL 5 underwriters IN PARALLEL")
    print("  → All 5 execute simultaneously (true concurrency)")
    print("")
    print("PHASE 3: decision_maker makes final decision")
    print("\n" + "="*80 + "\n")

    try:
        # Run the orchestrator workflow
        results = await process_loan_with_orchestrator(loan_number)

        print("\n" + "="*80)
        print("✅ ORCHESTRATOR WORKFLOW COMPLETED")
        print("="*80)
        print(f"\n📁 Loan file: ./loan_files/active/{loan_number}.json")

        # Show statistics
        file_manager.print_storage_stats()
        # Explicitly show the in-memory write counts to reconcile with logs
        print(f"\n🧮 In-memory write counts: {file_manager._write_counts}")
        write_count = file_manager.get_write_count(loan_number)
        print(f"\n📝 Total file writes for this loan: {write_count}")

        print(f"\n🔥 TRUE Concurrent Execution:")
        print(f"   • OrchestratorAgent orchestrated all phases")
        print(f"   • Phase 0: ALL 5 brokers ran IN PARALLEL (asyncio.gather)")
        print(f"   • Phase 1: ALL 6 processors ran IN PARALLEL (asyncio.gather)")
        print(f"   • Phase 2: ALL 5 underwriters ran IN PARALLEL (asyncio.gather)")
        print(f"   • All on the SAME loan: {loan_number}")
        print(f"   • Pure agent architecture - orchestrator is an agent!")

        return results

    except Exception as e:
        print(f"\n❌ ERROR during workflow execution:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Main entry point"""

    print("\n" + "="*80)
    print("INITIALIZING ORCHESTRATOR AGENT TEAM")
    print("="*80)

    print(f"\n✅ Created 17 agents:")
    print(f"   • 1 OrchestratorAgent (orchestrates everything)")
    print(f"   • 5 Mortgage Brokers (ALL execute concurrently in Phase 0)")
    print(f"   • 6 Loan Processors (ALL execute concurrently in Phase 1)")
    print(f"   • 5 Underwriters (ALL execute concurrently in Phase 2)")
    print(f"   • 1 Decision Maker")

    print(f"\n✅ Team ready for TRUE concurrent processing")

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
                confirm = input(f"\n▶️  Process loan {loan_number} with orchestrator workflow? (y/n): ")
                if confirm.lower() == 'y':
                    await run_workflow(loan_number)

                    another = input("\n🔄 Process another loan? (y/n): ")
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
    ║      ORCHESTRATOR AGENT ARCHITECTURE                             ║
    ║                                                                  ║
    ║  Agent Types:                                                    ║
    ║    • 1 OrchestratorAgent (orchestrator)                          ║
    ║    • 5 Mortgage Brokers (rate-shopping)                          ║
    ║    • 6 Loan Processors (task-specialized)                        ║
    ║    • 5 Underwriters (review-specialized)                         ║
    ║    • 1 Decision Maker                                            ║
    ║                                                                  ║
    ║  Architecture:                                                   ║
    ║    • Pure agent architecture (orchestrator is an agent)          ║
    ║    • Multiple agents of SAME type handle DIFFERENT subtasks      ║
    ║    • All work on ONE loan concurrently                           ║
    ║    • Directed message assignment per subtask                     ║
    ║    • TRUE concurrent execution via asyncio.gather()              ║
    ║                                                                  ║
    ║  Concurrency Model:                                              ║
    ║    • Phase 0: asyncio.gather() - ALL 5 brokers run in parallel   ║
    ║    • Phase 1: asyncio.gather() - ALL 6 processors run in parallel║
    ║    • Phase 2: asyncio.gather() - ALL 5 underwriters run in parallel║
    ║    • Actual parallelism - not sequential!                        ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(main())
