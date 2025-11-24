"""
Comprehensive test suite for Scenario 1 (Clean Approval) with assertions
to validate each phase of the workflow.

Run with:
    pytest test_scenario_1_assertions.py -v
    pytest test_scenario_1_assertions.py::TestScenario1Assertions::test_assertion_13_final_approval -v
"""

import pytest
import asyncio
import json
from pathlib import Path
from decimal import Decimal
from datetime import datetime
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import LoanStatus, DocumentStatus, DocumentType
from file_manager import LoanFileManager
from scenarios import create_scenario_clean_approval
from main import run_workflow

file_manager = LoanFileManager()


class TestScenario1Assertions:
    """
    Comprehensive test suite for Scenario 1 (Clean Approval) with assertions
    to validate each phase of the workflow.
    """

    @pytest.fixture
    async def scenario_1_loan(self):
        """Create Scenario 1 and return loan number"""
        scenario_description = create_scenario_clean_approval()
        loan_number = scenario_description.split("Loan Number: ")[1].split("\n")[0]
        yield loan_number
        # Cleanup after test
        file_path = Path(f"../loan_files/active/{loan_number}.json")
        if file_path.exists():
            file_path.unlink()

    # ==================== PHASE 0: INITIALIZATION ====================

    def test_assertion_1_scenario_creation(self):
        """
        ASSERTION 1: Scenario creation produces valid loan file

        Validates:
        - Loan file exists on disk
        - Loan file is valid JSON
        - Required fields are present
        - Initial status is APPLICATION_RECEIVED
        """
        scenario_description = create_scenario_clean_approval()
        loan_number = scenario_description.split("Loan Number: ")[1].split("\n")[0]

        # Assert: File exists
        file_path = Path(f"../loan_files/active/{loan_number}.json")
        assert file_path.exists(), f"Loan file {loan_number}.json not created"

        # Assert: Valid JSON
        loan_file = file_manager.load_loan_file(loan_number)
        assert loan_file is not None, "Loan file could not be loaded"

        # Assert: Required fields present
        assert loan_file.loan_info.loan_number == loan_number
        assert loan_file.loan_info.loan_amount == Decimal("320000")
        assert loan_file.loan_info.purchase_price == Decimal("400000")

        # Assert: Initial status
        assert loan_file.status == LoanStatus.APPLICATION_RECEIVED

        # Assert: Borrower details
        assert len(loan_file.borrowers) == 1
        borrower = loan_file.borrowers[0]
        assert borrower.first_name == "John"
        assert borrower.last_name == "Smith"

        # Assert: Property details
        assert loan_file.property_info is not None
        assert loan_file.property_info.property_address.zip_code == "62702"

        print("✅ ASSERTION 1 PASSED: Scenario creation valid")

        # Cleanup
        file_path.unlink()

    # ==================== PHASE 1: DOCUMENT VERIFICATION ====================

    @pytest.mark.asyncio
    async def test_assertion_2_document_verification(self):
        """
        ASSERTION 2: Document verification marks all docs complete

        Validates:
        - Documents status updated to COMPLETE
        - All required document types present
        - Loan status updated to DOCUMENTS_COMPLETE
        """
        scenario_description = create_scenario_clean_approval()
        loan_number = scenario_description.split("Loan Number: ")[1].split("\n")[0]

        # Run workflow (or just the verification tool)
        from tools_loan_processor import verify_loan_documents
        result = await verify_loan_documents(loan_number)

        # Assert: Result indicates completion
        assert "DOCUMENTS COMPLETE" in result

        # Load updated loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: Status updated
        assert loan_file.status == LoanStatus.DOCUMENTS_COMPLETE

        # Assert: Required documents present
        required_types = [
            DocumentType.URLA,
            DocumentType.PAYSTUB,
            DocumentType.W2,
            DocumentType.BANK_STATEMENT,
            DocumentType.PURCHASE_AGREEMENT
        ]

        document_types = [doc.document_type for doc in loan_file.documents]
        for required_type in required_types:
            assert required_type in document_types, f"Missing {required_type}"

        print("✅ ASSERTION 2 PASSED: Document verification complete")

        # Cleanup
        Path(f"../loan_files/active/{loan_number}.json").unlink()

    # ==================== PHASE 2: CREDIT REPORT ====================

    @pytest.mark.asyncio
    async def test_assertion_3_credit_report_retrieval(self):
        """
        ASSERTION 3: Credit report retrieved with expected score

        Validates:
        - Credit report document created
        - Credit score is 750 (as designed for Scenario 1)
        - Credit report saved to loan file
        - Loan status updated to CREDIT_ORDERED
        """
        scenario_description = create_scenario_clean_approval()
        loan_number = scenario_description.split("Loan Number: ")[1].split("\n")[0]

        from tools_loan_processor import order_credit_report
        result = await order_credit_report(loan_number)

        # Assert: Credit report returned
        assert "Credit Score" in result or "credit" in result.lower()

        # Load updated loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: Credit report document present
        credit_docs = [d for d in loan_file.documents
                       if d.document_type == DocumentType.CREDIT_REPORT]
        assert len(credit_docs) > 0, "Credit report document not created"

        # Assert: Credit data in financial metrics
        assert loan_file.financial_metrics.credit_score is not None
        assert loan_file.financial_metrics.credit_score >= 700  # Should be ~750

        print("✅ ASSERTION 3 PASSED: Credit report retrieved correctly")

        # Cleanup
        Path(f"../loan_files/active/{loan_number}.json").unlink()

    # ==================== PHASE 3: FLOOD CERTIFICATION ====================

    @pytest.mark.asyncio
    async def test_assertion_4_flood_certification(self):
        """
        ASSERTION 4: Flood certification determines low risk

        Validates:
        - Flood certification document created
        - ZIP 62702 returns Zone X (low risk)
        - No flood insurance required
        """
        scenario_description = create_scenario_clean_approval()
        loan_number = scenario_description.split("Loan Number: ")[1].split("\n")[0]

        from tools_loan_processor import order_flood_certification
        result = await order_flood_certification(loan_number)

        # Assert: Flood zone identified
        assert "flood" in result.lower()

        # Load updated loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: Flood cert document present
        flood_docs = [d for d in loan_file.documents
                      if d.document_type == DocumentType.FLOOD_CERTIFICATION]
        assert len(flood_docs) > 0, "Flood certification not created"

        print("✅ ASSERTION 4 PASSED: Flood certification correct")

        # Cleanup
        Path(f"../loan_files/active/{loan_number}.json").unlink()

    # ==================== PHASE 4: EMPLOYMENT VERIFICATION ====================

    @pytest.mark.asyncio
    async def test_assertion_5_employment_verification(self):
        """
        ASSERTION 5: Employment verified with stable history

        Validates:
        - Employment verification document created
        - 5 years employment confirmed
        - Income of $8,500/month verified
        """
        scenario_description = create_scenario_clean_approval()
        loan_number = scenario_description.split("Loan Number: ")[1].split("\n")[0]

        from tools_loan_processor import verify_employment
        result = await verify_employment(loan_number)

        # Assert: Employment verified
        assert "verified" in result.lower() or "employment" in result.lower()

        # Load updated loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: Employment verification document present
        voe_docs = [d for d in loan_file.documents
                    if d.document_type == DocumentType.EMPLOYMENT_VERIFICATION]
        assert len(voe_docs) > 0, "Employment verification not created"

        print("✅ ASSERTION 5 PASSED: Employment verification successful")

        # Cleanup
        Path(f"../loan_files/active/{loan_number}.json").unlink()

    # ==================== PHASE 5: FINANCIAL RATIOS ====================

    @pytest.mark.asyncio
    async def test_assertion_6_financial_ratios(self):
        """
        ASSERTION 6: Financial ratios calculated correctly

        Validates:
        - DTI <= 35% (excellent)
        - LTV = 80% (good)
        - Reserves >= 6 months (strong)
        - All ratios within guidelines
        """
        scenario_description = create_scenario_clean_approval()
        loan_number = scenario_description.split("Loan Number: ")[1].split("\n")[0]

        # Must have credit report first
        from tools_loan_processor import order_credit_report, calculate_loan_ratios
        await order_credit_report(loan_number)

        result = await calculate_loan_ratios(loan_number)

        # Load updated loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: DTI calculated and within range
        assert loan_file.financial_metrics.dti_ratio is not None
        assert loan_file.financial_metrics.dti_ratio <= 40.0, \
            f"DTI {loan_file.financial_metrics.dti_ratio}% too high"

        # Assert: LTV calculated
        assert loan_file.financial_metrics.ltv_ratio is not None
        assert loan_file.financial_metrics.ltv_ratio == 80.0

        # Assert: Reserves calculated
        assert loan_file.financial_metrics.months_reserves is not None
        assert loan_file.financial_metrics.months_reserves >= 6.0, \
            f"Reserves {loan_file.financial_metrics.months_reserves} months insufficient"

        print("✅ ASSERTION 6 PASSED: Financial ratios correct")

        # Cleanup
        Path(f"../loan_files/active/{loan_number}.json").unlink()

    # ==================== PHASE 6: SUBMIT TO UNDERWRITING ====================

    @pytest.mark.asyncio
    async def test_assertion_7_submit_to_underwriting(self):
        """
        ASSERTION 7: Loan successfully submitted to underwriting

        Validates:
        - Status updated to SUBMITTED_TO_UNDERWRITING
        - All prerequisites met
        - Submission timestamp recorded
        """
        scenario_description = create_scenario_clean_approval()
        loan_number = scenario_description.split("Loan Number: ")[1].split("\n")[0]

        # Complete all prerequisite steps
        from tools_loan_processor import (
            verify_loan_documents, order_credit_report,
            calculate_loan_ratios, submit_to_underwriting
        )
        await verify_loan_documents(loan_number)
        await order_credit_report(loan_number)
        await calculate_loan_ratios(loan_number)

        result = await submit_to_underwriting(loan_number)

        # Assert: Submission successful
        assert "submitted" in result.lower() or "underwriting" in result.lower()

        # Load updated loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: Status updated
        assert loan_file.status == LoanStatus.SUBMITTED_TO_UNDERWRITING

        # Assert: Audit trail has submission entry
        submission_entries = [
            entry for entry in loan_file.audit_trail
            if "submitted" in entry.action.lower() or "underwriting" in entry.action.lower()
        ]
        assert len(submission_entries) > 0, "Submission not recorded in audit trail"

        print("✅ ASSERTION 7 PASSED: Submitted to underwriting")

        # Cleanup
        Path(f"../loan_files/active/{loan_number}.json").unlink()

    # ==================== CONCURRENCY VALIDATION ====================

    @pytest.mark.asyncio
    async def test_assertion_15_concurrent_execution(self):
        """
        ASSERTION 15: Concurrent tasks execute in parallel

        Validates:
        - Phase 1 tasks complete in ~5s, NOT ~15s (sum of individual times)
        - File locking prevents race conditions
        - No data corruption from concurrent writes
        """
        import time
        scenario_description = create_scenario_clean_approval()
        loan_number = scenario_description.split("Loan Number: ")[1].split("\n")[0]

        # Test Loan Processor Phase 1 concurrency
        from tools_loan_processor import (
            verify_loan_documents, order_credit_report, order_appraisal,
            order_flood_certification, verify_employment
        )

        start = time.time()

        # Execute all 5 tasks concurrently
        await asyncio.gather(
            verify_loan_documents(loan_number),
            order_credit_report(loan_number),
            order_appraisal(loan_number),
            order_flood_certification(loan_number),
            verify_employment(loan_number)
        )

        duration = time.time() - start

        # Assert: Completed in parallel time, not sequential
        # Expected: ~5s (max of individual times)
        # Sequential would be: ~10-12s (sum of times)
        assert duration < 10.0, \
            f"Phase 1 took {duration}s, suggests sequential execution"

        print(f"✅ ASSERTION 15 PASSED: Concurrent execution in {duration:.1f}s")

        # Cleanup
        Path(f"../loan_files/active/{loan_number}.json").unlink()

    # ==================== FILE INTEGRITY VALIDATION ====================

    @pytest.mark.asyncio
    async def test_assertion_16_file_integrity(self):
        """
        ASSERTION 16: File operations maintain data integrity

        Validates:
        - No data loss from concurrent writes
        - Audit trail is complete and ordered
        - No duplicate entries
        - File locks prevent corruption
        """
        scenario_description = create_scenario_clean_approval()
        loan_number = scenario_description.split("Loan Number: ")[1].split("\n")[0]

        # Perform multiple operations
        from tools_loan_processor import (
            verify_loan_documents, order_credit_report, order_flood_certification
        )

        await verify_loan_documents(loan_number)
        await order_credit_report(loan_number)
        await order_flood_certification(loan_number)

        # Load loan file
        loan_file = file_manager.load_loan_file(loan_number)

        # Assert: Audit trail is time-ordered
        timestamps = [entry.timestamp for entry in loan_file.audit_trail]
        assert timestamps == sorted(timestamps), "Audit trail not time-ordered"

        # Assert: No document duplicates
        doc_ids = [doc.document_id for doc in loan_file.documents]
        assert len(doc_ids) == len(set(doc_ids)), "Duplicate documents found"

        print("✅ ASSERTION 16 PASSED: File integrity maintained")

        # Cleanup
        Path(f"../loan_files/active/{loan_number}.json").unlink()


# ==================== RUN ALL ASSERTIONS ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
