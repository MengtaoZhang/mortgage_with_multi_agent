"""
Concurrent Multi-Agent Architecture - Main Runtime

TRUE concurrent execution using asyncio.gather() for parallel task execution.

For ONE loan, multiple agents work on different subtasks simultaneously.
"""

import asyncio
import os
from dotenv import load_dotenv

from agents_concurrent import process_loan_concurrent
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
    print("MORTGAGE UNDERWRITING - CONCURRENT MULTI-AGENT ARCHITECTURE")
    print("="*80)
    print("Architecture: TRUE Concurrent Execution with asyncio.gather()")
    print("")
    print("Agent Types:")
    print("  • 5 Mortgage Brokers (rate-shopping)")
    print("  • 6 Loan Processors (task-specialized)")
    print("  • 5 Underwriters (review-specialized)")
    print("  • 1 Decision Maker")
    print("")
    print("How It Works (for ONE loan):")
    print("")
    print("PHASE 0 - ALL 5 Mortgage Brokers (TRUE CONCURRENT):")
    print("  Coordinator uses asyncio.gather() to run ALL 5 at once:")
    print("    • mortgage_broker_1 → 'Query Wells Fargo'")
    print("    • mortgage_broker_2 → 'Query Bank of America'")
    print("    • mortgage_broker_3 → 'Query Chase'")
    print("    • mortgage_broker_4 → 'Query Quicken Loans'")
    print("    • mortgage_broker_5 → 'Query US Bank'")
    print("  All 5 execute IN PARALLEL simultaneously!")
    print("")
    print("PHASE 1 - ALL 6 Loan Processors (TRUE CONCURRENT):")
    print("  Coordinator uses asyncio.gather() to run ALL 6 at once:")
    print("    • loan_processor_1 → 'Verify documents'")
    print("    • loan_processor_2 → 'Order credit report'")
    print("    • loan_processor_3 → 'Order appraisal'")
    print("    • loan_processor_4 → 'Order flood cert'")
    print("    • loan_processor_5 → 'Verify employment'")
    print("    • loan_processor_6 → 'Calculate ratios & submit'")
    print("  All 6 execute IN PARALLEL simultaneously!")
    print("")
    print("PHASE 2 - ALL 5 Underwriters (TRUE CONCURRENT):")
    print("  Coordinator uses asyncio.gather() to run ALL 5 at once:")
    print("    • underwriter_5 → 'Run automated underwriting'")
    print("    • underwriter_1 → 'Review credit'")
    print("    • underwriter_2 → 'Review income'")
    print("    • underwriter_3 → 'Review assets'")
    print("    • underwriter_4 → 'Review property'")
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
    """Run concurrent workflow for a single loan"""

    print("\n" + "="*80)
    print(f"🚀 PROCESSING LOAN: {loan_number}")
    print("="*80)
    print("\nExpected Workflow:")
    print("-" * 80)
    print("PHASE 0: asyncio.gather() runs ALL 5 mortgage brokers IN PARALLEL")
    print("  → All 5 execute simultaneously (true concurrency)")
    print("")
    print("PHASE 1: asyncio.gather() runs ALL 6 loan processors IN PARALLEL")
    print("  → All 6 execute simultaneously (true concurrency)")
    print("")
    print("PHASE 2: asyncio.gather() runs ALL 5 underwriters IN PARALLEL")
    print("  → All 5 execute simultaneously (true concurrency)")
    print("")
    print("PHASE 3: decision_maker makes final decision")
    print("\n" + "="*80 + "\n")

    try:
        # Run the concurrent workflow
        results = await process_loan_concurrent(loan_number)

        print("\n" + "="*80)
        print("✅ CONCURRENT WORKFLOW COMPLETED")
        print("="*80)
        print(f"\n📁 Loan file: ./loan_files/active/{loan_number}.json")

        # Show statistics
        file_manager.print_storage_stats()
        write_count = file_manager._write_counts.get(loan_number, 0)
        print(f"\n📝 Total file writes for this loan: {write_count}")

        print(f"\n🔥 TRUE Concurrent Execution:")
        print(f"   • Phase 0: ALL 5 brokers ran IN PARALLEL (asyncio.gather)")
        print(f"   • Phase 1: ALL 6 processors ran IN PARALLEL (asyncio.gather)")
        print(f"   • Phase 2: ALL 5 underwriters ran IN PARALLEL (asyncio.gather)")
        print(f"   • All on the SAME loan: {loan_number}")
        print(f"   • Actual parallelism achieved!")

        return results

    except Exception as e:
        print(f"\n❌ ERROR during workflow execution:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Main entry point"""

    print("\n" + "="*80)
    print("INITIALIZING CONCURRENT AGENT TEAM")
    print("="*80)

    print(f"\n✅ Created 17 agents:")
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
                confirm = input(f"\n▶️  Process loan {loan_number} with concurrent workflow? (y/n): ")
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
    ║      CONCURRENT MULTI-AGENT ARCHITECTURE                         ║
    ║                                                                  ║
    ║  Agent Types:                                                    ║
    ║    • 5 Mortgage Brokers (rate-shopping)                          ║
    ║    • 6 Loan Processors (task-specialized)                        ║
    ║    • 5 Underwriters (review-specialized)                         ║
    ║    • 1 Decision Maker                                            ║
    ║                                                                  ║
    ║  Architecture:                                                   ║
    ║    • Multiple agents of SAME type handle DIFFERENT subtasks      ║
    ║    • All work on ONE loan concurrently                           ║
    ║    • Direct message assignment per subtask                       ║
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
