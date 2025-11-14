# Add new file: task_coordinator.py
import asyncio
from typing import Dict, List, Set
from dataclasses import dataclass

from resources.loan_underwriter.tools_loan_processor import order_credit_report, order_appraisal, \
    order_flood_certification, verify_employment, calculate_loan_ratios, submit_to_underwriting
from resources.loan_underwriter.tools_underwriter import run_automated_underwriting, review_credit_profile, \
    review_income_employment, review_assets_reserves, review_property_appraisal, issue_underwriting_conditions


@dataclass
class Task:
    name: str
    tool_function: callable
    dependencies: List[str]
    concurrent_safe: bool
    estimated_duration: str


class TaskCoordinator:
    """Manages task dependencies and concurrent execution"""

    LOAN_PROCESSOR_TASKS = {
        "order_credit_report": Task(
            name="order_credit_report",
            tool_function=order_credit_report,
            dependencies=[],
            concurrent_safe=True,
            estimated_duration="2-5s"
        ),
        "order_appraisal": Task(
            name="order_appraisal",
            tool_function=order_appraisal,
            dependencies=[],
            concurrent_safe=True,
            estimated_duration="1-2s"
        ),
        "order_flood_certification": Task(
            name="order_flood_certification",
            tool_function=order_flood_certification,
            dependencies=[],
            concurrent_safe=True,
            estimated_duration="1s"
        ),
        "verify_employment": Task(
            name="verify_employment",
            tool_function=verify_employment,
            dependencies=[],
            concurrent_safe=True,
            estimated_duration="1-3s"
        ),
        "calculate_loan_ratios": Task(
            name="calculate_loan_ratios",
            tool_function=calculate_loan_ratios,
            dependencies=["order_credit_report"],
            concurrent_safe=False,
            estimated_duration="1s"
        ),
        "submit_to_underwriting": Task(
            name="submit_to_underwriting",
            tool_function=submit_to_underwriting,
            dependencies=["calculate_loan_ratios", "verify_loan_documents"],
            concurrent_safe=False,
            estimated_duration="1s"
        )
    }

    UNDERWRITER_TASKS = {
        "run_automated_underwriting": Task(
            name="run_automated_underwriting",
            tool_function=run_automated_underwriting,
            dependencies=[],
            concurrent_safe=False,
            estimated_duration="2-4s"
        ),
        "review_credit_profile": Task(
            name="review_credit_profile",
            tool_function=review_credit_profile,
            dependencies=["run_automated_underwriting"],
            concurrent_safe=True,
            estimated_duration="1s"
        ),
        "review_income_employment": Task(
            name="review_income_employment",
            tool_function=review_income_employment,
            dependencies=["run_automated_underwriting"],
            concurrent_safe=True,
            estimated_duration="1s"
        ),
        "review_assets_reserves": Task(
            name="review_assets_reserves",
            tool_function=review_assets_reserves,
            dependencies=["run_automated_underwriting"],
            concurrent_safe=True,
            estimated_duration="1s"
        ),
        "review_property_appraisal": Task(
            name="review_property_appraisal",
            tool_function=review_property_appraisal,
            dependencies=["run_automated_underwriting"],
            concurrent_safe=True,
            estimated_duration="1s"
        ),
        "issue_underwriting_conditions": Task(
            name="issue_underwriting_conditions",
            tool_function=issue_underwriting_conditions,
            dependencies=["review_credit_profile", "review_income_employment",
                          "review_assets_reserves", "review_property_appraisal"],
            concurrent_safe=False,
            estimated_duration="1s"
        )
    }

    @staticmethod
    def get_concurrent_tasks(completed_tasks: Set[str], all_tasks: Dict[str, Task]) -> List[Task]:
        """
        Get all tasks that can run concurrently now

        Returns tasks where:
        1. All dependencies are in completed_tasks
        2. concurrent_safe = True
        """
        available = []
        for task_name, task in all_tasks.items():
            if task_name in completed_tasks:
                continue

            # Check if all dependencies met
            deps_met = all(dep in completed_tasks for dep in task.dependencies)

            if deps_met and task.concurrent_safe:
                available.append(task)

        return available

    @staticmethod
    async def execute_concurrent_tasks(tasks: List[Task], loan_number: str) -> Dict[str, str]:
        """Execute multiple tasks concurrently"""
        results = await asyncio.gather(
            *[task.tool_function(loan_number) for task in tasks],
            return_exceptions=True
        )

        return {task.name: result for task, result in zip(tasks, results)}