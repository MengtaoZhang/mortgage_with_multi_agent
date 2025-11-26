"""
Loan Processor tools with concurrent safety
"""


"""
Loan Processor tools with concurrent safety
"""

import random
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List
import uuid
import copy  # ← ADD THIS for run_automated_underwriting

from src.loan_underwriter.models import (
    LoanFile, LoanStatus, Document, DocumentType, DocumentStatus,
    UnderwritingCondition, ConditionType, ConditionSeverity,
    Appraisal  # ← ADD THIS for order_appraisal
)
from src.loan_underwriter.file_manager import LoanFileManager  # ← This is where file_manager comes from
from src.loan_underwriter.external_systems import (
    CreditBureauSimulator, AppraisalManagementSimulator,
    TitleCompanySimulator, FloodCertificationSimulator,
    EmploymentVerificationSimulator, IRSTranscriptSimulator,
    SystemTimeoutException, SystemMaintenanceException,
    InvalidDataException, InsufficientCreditHistoryException,
    ExternalSystemException
)
file_manager = LoanFileManager()  # ← This is the file_manager used in all functions


async def verify_loan_documents(loan_number: str) -> str:
    """Verify all required loan documents - CONCURRENT SAFE"""

    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        result = []
        result.append(f"📋 DOCUMENT VERIFICATION - Loan #{loan_number}")
        result.append("=" * 60)

        required_docs = {
            DocumentType.URLA: "Uniform Residential Loan Application",
            DocumentType.PAYSTUB: "Recent Pay Stubs (2 months)",
            DocumentType.W2: "W-2 Forms (2 years)",
            DocumentType.BANK_STATEMENT: "Bank Statements (2 months)",
            DocumentType.PURCHASE_AGREEMENT: "Purchase Agreement"
        }

        missing_docs = []
        incomplete_docs = []
        complete_docs = []

        for doc_type, doc_name in required_docs.items():
            matching_docs = [d for d in loan_file.documents if d.document_type == doc_type]

            if not matching_docs:
                missing_docs.append(f"❌ {doc_name}")
                new_doc = Document(
                    document_id=f"DOC-{uuid.uuid4().hex[:8].upper()}",
                    document_type=doc_type,
                    status=DocumentStatus.REQUIRED
                )
                loan_file.documents.append(new_doc)
            else:
                doc = matching_docs[0]
                if doc.status == DocumentStatus.APPROVED:
                    complete_docs.append(f"✅ {doc_name}")
                elif doc.status == DocumentStatus.RECEIVED:
                    incomplete_docs.append(f"⚠️  {doc_name} (received, pending review)")
                else:
                    missing_docs.append(f"❌ {doc_name} (status: {doc.status.value})")

        if complete_docs:
            result.append("\n✅ COMPLETE DOCUMENTS:")
            result.extend(complete_docs)

        if incomplete_docs:
            result.append("\n⚠️  PENDING REVIEW:")
            result.extend(incomplete_docs)

        if missing_docs:
            result.append("\n❌ MISSING DOCUMENTS:")
            result.extend(missing_docs)
            result.append("\n🔔 ACTION REQUIRED: Request missing documents from borrower")

        if missing_docs:
            loan_file.update_status(
                LoanStatus.DOCUMENTS_COLLECTING,
                "loan_processor",
                "Missing required documents"
            )
            result.append("\n📊 Status: DOCUMENTS COLLECTING")
        else:
            loan_file.update_status(
                LoanStatus.DOCUMENTS_COMPLETE,
                "loan_processor",
                "All required documents received"
            )
            result.append("\n📊 Status: DOCUMENTS COMPLETE ✅")

        file_manager.save_loan_file(loan_file)

    return "\n".join(result)


async def validate_document_quality(
    loan_number: str,
    document_type: str,
    quality_checks: Dict[str, bool]
) -> str:
    """Validate document quality - CONCURRENT SAFE"""

    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        doc_type_enum = DocumentType(document_type)
        matching_docs = [d for d in loan_file.documents if d.document_type == doc_type_enum]

        if not matching_docs:
            return f"❌ ERROR: Document type {document_type} not found in loan file"

        doc = matching_docs[0]

        result = []
        result.append(f"🔍 DOCUMENT QUALITY VALIDATION")
        result.append(f"Document: {doc_type_enum.value}")
        result.append(f"Document ID: {doc.document_id}")
        result.append("=" * 60)

        issues = []
        all_passed = True

        for check_name, passed in quality_checks.items():
            if passed:
                result.append(f"✅ {check_name.replace('_', ' ').title()}")
            else:
                result.append(f"❌ {check_name.replace('_', ' ').title()}")
                issues.append(f"{check_name.replace('_', ' ').title()} failed")
                all_passed = False

        if all_passed:
            doc.status = DocumentStatus.APPROVED
            doc.reviewed_by = "loan_processor"
            doc.reviewed_date = datetime.now()
            result.append(f"\n✅ Document APPROVED")
        else:
            doc.status = DocumentStatus.REJECTED
            doc.issues = issues
            result.append(f"\n❌ Document REJECTED")
            result.append(f"\nIssues:")
            for issue in issues:
                result.append(f"  - {issue}")
            result.append(f"\n🔔 ACTION: Request borrower to resubmit document")

        loan_file.add_audit_entry(
            actor="loan_processor",
            action="document_validation",
            details=f"Validated {doc_type_enum.value}: {'APPROVED' if all_passed else 'REJECTED'}"
        )

        file_manager.save_loan_file(loan_file)

    return "\n".join(result)


async def order_credit_report(loan_number: str, max_retries: int = 2) -> str:
    """Order credit report - TRUE CONCURRENT SAFE"""

    # ========== PHASE 1: Load data (LOCKED) ==========
    for attempt in range(1, max_retries + 1):
        async with file_manager.acquire_loan_lock(loan_number):
            loan_file = file_manager.load_loan_file(loan_number)
            if not loan_file:
                return f"❌ ERROR: Loan file {loan_number} not found"

            if not loan_file.borrowers:
                return f"❌ ERROR: No borrower information in loan file"

            borrower = loan_file.borrowers[0]

            # Extract only what we need for the API call
            borrower_data = {
                "ssn": borrower.ssn,
                "first_name": borrower.first_name,
                "last_name": borrower.last_name
            }
    # Lock released here! Other tasks can now access the file

    # ========== PHASE 2: External API call (NO LOCK - concurrent!) ==========
    result = []
    result.append(f"💳 ORDERING CREDIT REPORT")
    result.append(f"Borrower: {borrower_data['first_name']} {borrower_data['last_name']}")
    result.append(f"SSN: ***-**-{borrower_data['ssn'][-4:]}")
    result.append("=" * 60)

    try:
        result.append(f"📡 Contacting credit bureau...")

        # This takes 2-5 seconds but doesn't block other tasks!
        credit_response = CreditBureauSimulator.pull_credit_report(
            borrower_ssn=borrower_data["ssn"],
            borrower_name=f"{borrower_data['first_name']} {borrower_data['last_name']}",
            pull_type="hard"
        )

        result.append(f"✅ Credit report received successfully")
        result.append(f"Transaction ID: {credit_response.transaction_id}")
        result.append("")

        credit_report = credit_response.credit_report

        result.append(f"📊 CREDIT REPORT SUMMARY:")
        result.append(f"  Credit Score: {credit_report.credit_score}")
        result.append(f"  Bureau: {credit_report.bureau}")
        result.append(f"  Report Date: {credit_report.report_date.strftime('%Y-%m-%d')}")
        result.append(f"  Tradelines: {len(credit_report.tradelines)}")
        result.append(f"  Inquiries: {len(credit_report.inquiries)}")
        result.append(f"  Total Monthly Debt: ${credit_report.total_monthly_debt:,.2f}")

        flags = []
        if credit_report.credit_score < 620:
            flags.append("⚠️  Credit score below 620 - may require LOE")
        if credit_report.credit_score < 580:
            flags.append("🚨 Credit score below 580 - HIGH RISK")
        if len(credit_report.inquiries) > 3:
            flags.append("⚠️  Multiple credit inquiries - LOE required")
        if credit_report.derogatory_items:
            flags.append(f"⚠️  {len(credit_report.derogatory_items)} derogatory item(s) found")

        if flags:
            result.append("\n🚩 FLAGS:")
            result.extend(flags)

        # ========== PHASE 3: Update file (LOCKED) ==========
        async with file_manager.acquire_loan_lock(loan_number):
            # IMPORTANT: Re-load the file to get fresh copy
            # (other tasks might have modified it while we were calling the API)
            loan_file = file_manager.load_loan_file(loan_number)
            if not loan_file:
                return f"❌ ERROR: Loan file {loan_number} not found"

            # Update the file with credit report
            loan_file.borrowers[0].credit_report = credit_report

            # Add flags
            if flags:
                loan_file.flags.extend(flags)

            # Add credit document
            credit_doc = Document(
                document_id=f"DOC-{uuid.uuid4().hex[:8].upper()}",
                document_type=DocumentType.CREDIT_REPORT,
                status=DocumentStatus.APPROVED,
                received_date=datetime.now(),
                reviewed_by="loan_processor",
                reviewed_date=datetime.now(),
                metadata={
                    "credit_score": credit_report.credit_score,
                    "bureau": credit_report.bureau,
                    "report_id": credit_report.report_id
                }
            )
            loan_file.documents.append(credit_doc)

            # Update status
            loan_file.update_status(
                LoanStatus.CREDIT_ORDERED,
                "loan_processor",
                f"Credit report received - Score: {credit_report.credit_score}"
            )

            # Save file
            file_manager.save_loan_file(loan_file)
            result.append(f"\n✅ Credit report added to loan file")
        # Lock released

    except SystemTimeoutException as e:
        result.append(f"\n⏱️  TIMEOUT: {str(e)}")
        result.append(f"🔔 ACTION: Retry credit pull in 5 minutes")

        # Save error to audit trail
        async with file_manager.acquire_loan_lock(loan_number):
            loan_file = file_manager.load_loan_file(loan_number)
            if loan_file:
                loan_file.add_audit_entry(
                    actor="loan_processor",
                    action="credit_order_failed",
                    details=f"Timeout: {str(e)}"
                )
                file_manager.save_loan_file(loan_file)

    except SystemMaintenanceException as e:
        result.append(f"\n🔧 MAINTENANCE: {str(e)}")
        result.append(f"🔔 ACTION: Retry after maintenance window")

        async with file_manager.acquire_loan_lock(loan_number):
            loan_file = file_manager.load_loan_file(loan_number)
            if loan_file:
                loan_file.add_audit_entry(
                    actor="loan_processor",
                    action="credit_order_failed",
                    details=f"Maintenance: {str(e)}"
                )
                file_manager.save_loan_file(loan_file)

    except InsufficientCreditHistoryException as e:
        result.append(f"\n❌ INSUFFICIENT CREDIT: {str(e)}")
        result.append(f"🔔 ACTION: Request alternative credit documentation")
        result.append(f"   - Utility payment history")
        result.append(f"   - Rent payment history")
        result.append(f"   - Manual underwriting may be required")

        async with file_manager.acquire_loan_lock(loan_number):
            loan_file = file_manager.load_loan_file(loan_number)
            if loan_file:
                loan_file.flags.append("Insufficient credit history - alternative docs needed")
                loan_file.add_audit_entry(
                    actor="loan_processor",
                    action="credit_order_failed",
                    details=f"Insufficient history: {str(e)}"
                )
                file_manager.save_loan_file(loan_file)

    return "\n".join(result)

async def calculate_loan_ratios(loan_number: str) -> str:
    """Calculate financial ratios - CONCURRENT SAFE"""

    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        result = []
        result.append(f"🧮 FINANCIAL RATIO CALCULATIONS")
        result.append(f"Loan #{loan_number}")
        result.append("=" * 60)

        loan_info = loan_file.loan_info
        borrower = loan_file.borrowers[0] if loan_file.borrowers else None

        # LTV CALCULATION
        result.append("\n📊 LOAN-TO-VALUE (LTV) RATIO:")

        loan_amount = loan_info.loan_amount
        purchase_price = loan_info.purchase_price or Decimal("0")

        property_value = purchase_price
        if loan_file.appraisal and loan_file.appraisal.appraised_value:
            property_value = loan_file.appraisal.appraised_value
            result.append(f"  Using Appraised Value: ${property_value:,.2f}")
        else:
            result.append(f"  Using Purchase Price: ${property_value:,.2f}")

        if property_value > 0:
            ltv_ratio = (loan_amount / property_value) * 100
            loan_file.financial_metrics.ltv_ratio = ltv_ratio

            result.append(f"  Loan Amount: ${loan_amount:,.2f}")
            result.append(f"  Property Value: ${property_value:,.2f}")
            result.append(f"  LTV Ratio: {ltv_ratio:.2f}%")

            if ltv_ratio > 80:
                result.append(f"  ⚠️  LTV > 80% - PMI REQUIRED")
                loan_file.financial_metrics.pmi_required = True
                pmi_rate = Decimal("0.005")
                pmi_monthly = (loan_amount * pmi_rate) / 12
                loan_file.financial_metrics.pmi_amount = pmi_monthly
                result.append(f"  Estimated PMI: ${pmi_monthly:,.2f}/month")
        else:
            result.append(f"  ❌ Cannot calculate - property value is 0")

        # DTI CALCULATION
        result.append("\n📊 DEBT-TO-INCOME (DTI) RATIO:")

        if borrower and borrower.credit_report:
            monthly_income = sum(inc.monthly_amount for inc in borrower.income) if borrower.income else Decimal("0")
            total_monthly_debt = borrower.credit_report.total_monthly_debt

            if property_value > 0:
                rate = Decimal("0.07") / 12
                n_payments = 360
                principal_interest = loan_amount * (rate * (1 + rate)**n_payments) / ((1 + rate)**n_payments - 1)

                property_tax = (property_value * Decimal("0.012")) / 12
                insurance = Decimal("100")
                pmi = loan_file.financial_metrics.pmi_amount or Decimal("0")
                hoa = loan_file.property_info.hoa_fees or Decimal("0")

                housing_payment = principal_interest + property_tax + insurance + pmi + hoa
                loan_file.financial_metrics.monthly_housing_payment = housing_payment

                result.append(f"  Housing Payment (PITI):")
                result.append(f"    Principal & Interest: ${principal_interest:,.2f}")
                result.append(f"    Property Tax: ${property_tax:,.2f}")
                result.append(f"    Insurance: ${insurance:,.2f}")
                if pmi > 0:
                    result.append(f"    PMI: ${pmi:,.2f}")
                if hoa > 0:
                    result.append(f"    HOA: ${hoa:,.2f}")
                result.append(f"    TOTAL: ${housing_payment:,.2f}")

                if monthly_income > 0:
                    front_end_ratio = (housing_payment / monthly_income) * 100
                    loan_file.financial_metrics.front_end_ratio = front_end_ratio
                    result.append(f"\n  Front-End Ratio: {front_end_ratio:.2f}%")
                    if front_end_ratio > 28:
                        result.append(f"    ⚠️  Front-end ratio > 28%")

                total_debt = total_monthly_debt + housing_payment
            else:
                total_debt = total_monthly_debt

            loan_file.financial_metrics.total_monthly_debt = total_debt
            loan_file.financial_metrics.monthly_income = monthly_income

            result.append(f"\n  Gross Monthly Income: ${monthly_income:,.2f}")
            result.append(f"  Existing Monthly Debt: ${total_monthly_debt:,.2f}")
            result.append(f"  Total Monthly Obligations: ${total_debt:,.2f}")

            if monthly_income > 0:
                dti_ratio = (total_debt / monthly_income) * 100
                loan_file.financial_metrics.dti_ratio = dti_ratio

                result.append(f"  DTI Ratio: {dti_ratio:.2f}%")

                if dti_ratio <= 43:
                    result.append(f"  ✅ DTI within conventional guidelines (≤43%)")
                elif dti_ratio <= 50:
                    result.append(f"  ⚠️  DTI elevated (43-50%) - compensating factors needed")
                else:
                    result.append(f"  🚨 DTI exceeds guidelines (>50%) - HIGH RISK")
            else:
                result.append(f"  ❌ Cannot calculate - monthly income is 0")
        else:
            result.append(f"  ❌ Cannot calculate - credit report not available")

        # RESERVES CALCULATION
        result.append("\n📊 RESERVES:")

        if borrower and borrower.assets:
            liquid_assets = sum(
                asset.balance for asset in borrower.assets
                if asset.asset_type in ["checking", "savings", "money_market"]
            )
            total_assets = sum(asset.balance for asset in borrower.assets)

            loan_file.financial_metrics.total_assets = total_assets

            result.append(f"  Liquid Assets: ${liquid_assets:,.2f}")
            result.append(f"  Total Assets: ${total_assets:,.2f}")

            housing_payment = loan_file.financial_metrics.monthly_housing_payment or Decimal("0")
            if housing_payment > 0:
                reserves_months = liquid_assets / housing_payment
                loan_file.financial_metrics.reserves_months = reserves_months

                result.append(f"  Monthly Housing Payment: ${housing_payment:,.2f}")
                result.append(f"  Reserves: {reserves_months:.1f} months")

                if reserves_months >= 6:
                    result.append(f"  ✅ Strong reserves (≥6 months)")
                elif reserves_months >= 2:
                    result.append(f"  ✅ Adequate reserves (≥2 months)")
                else:
                    result.append(f"  ⚠️  Low reserves (<2 months)")
        else:
            result.append(f"  ❌ No asset information available")

        # CASH TO CLOSE
        result.append("\n📊 CASH TO CLOSE:")

        down_payment = loan_info.down_payment or Decimal("0")
        closing_costs = purchase_price * Decimal("0.03") if purchase_price > 0 else Decimal("0")

        cash_to_close = down_payment + closing_costs
        loan_file.financial_metrics.cash_to_close = cash_to_close

        result.append(f"  Down Payment: ${down_payment:,.2f}")
        result.append(f"  Estimated Closing Costs: ${closing_costs:,.2f}")
        result.append(f"  Total Cash to Close: ${cash_to_close:,.2f}")

        loan_file.add_audit_entry(
            actor="loan_processor",
            action="financial_calculations",
            details=f"Calculated ratios: LTV={loan_file.financial_metrics.ltv_ratio:.2f}%, DTI={loan_file.financial_metrics.dti_ratio:.2f}%"
        )

        file_manager.save_loan_file(loan_file)
        result.append(f"\n✅ Financial metrics updated in loan file")

    return "\n".join(result)


# At the top of the file
from src.loan_underwriter.file_manager import LoanFileManager

file_manager = LoanFileManager()


async def order_appraisal(loan_number: str) -> str:  # ← NOT @staticmethod, NOT in a class
    """Order property appraisal - TRUE CONCURRENT SAFE"""

    # ========== PHASE 1: Load data (LOCKED) ==========
    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        # Extract property data
        property_data = {
            "loan_number": loan_number,  # ← ADD THIS
            "street": loan_file.property_info.property_address.street,
            "city": loan_file.property_info.property_address.city,
            "state": loan_file.property_info.property_address.state,
            "purchase_price": loan_file.loan_info.purchase_price or Decimal("0")
        }
    # Lock released

    # ========== PHASE 2: External API call (NO LOCK) ==========
    result = []
    result.append(f"🏠 ORDERING APPRAISAL")
    result.append(f"Property: {property_data['street']}")
    result.append(f"{property_data['city']}, {property_data['state']}")
    result.append("=" * 60)

    try:
        result.append(f"📡 Contacting Appraisal Management Company...")

        # Call the SIMULATOR (which is in external_systems.py)
        appraisal_response = AppraisalManagementSimulator.order_appraisal(
            loan_number=property_data['loan_number'],  # ← FIX: Add loan_number
            property_address=f"{property_data['street']}, {property_data['city']}",
            purchase_price=property_data['purchase_price']
            # ← FIX: Remove loan_amount (not in simulator signature)
        )

        result.append(f"✅ Appraisal ordered successfully")
        result.append(f"Transaction ID: {appraisal_response.transaction_id}")
        result.append(f"Order ID: {appraisal_response.response_data['order_id']}")
        result.append(f"Appraisal Fee: ${appraisal_response.response_data['fee']:.2f}")
        result.append(f"Estimated Completion: {appraisal_response.response_data['estimated_completion']}")

        if appraisal_response.response_data.get('appraiser_assigned'):
            result.append(f"✅ Appraiser assigned")
        else:
            result.append(f"⏳ Appraiser assignment pending")

        if appraisal_response.warnings:
            result.append(f"\n⚠️  WARNINGS:")
            for warning in appraisal_response.warnings:
                result.append(f"  - {warning}")

        # ========== PHASE 3: Update file (LOCKED) ==========
        async with file_manager.acquire_loan_lock(loan_number):
            loan_file = file_manager.load_loan_file(loan_number)
            if not loan_file:
                return f"❌ ERROR: Loan file {loan_number} not found"

            from models import Appraisal
            loan_file.appraisal = Appraisal(
                appraisal_id=appraisal_response.response_data['order_id'],
                ordered_date=datetime.now(),
                status="ordered"
            )

            appraisal_doc = Document(
                document_id=f"DOC-{uuid.uuid4().hex[:8].upper()}",
                document_type=DocumentType.APPRAISAL,
                status=DocumentStatus.REQUESTED,
                metadata={
                    "order_id": appraisal_response.response_data['order_id'],
                    "estimated_completion": appraisal_response.response_data['estimated_completion']
                }
            )
            loan_file.documents.append(appraisal_doc)

            loan_file.update_status(
                LoanStatus.APPRAISAL_ORDERED,
                "loan_processor",
                f"Appraisal ordered - Order ID: {appraisal_response.response_data['order_id']}"
            )

            file_manager.save_loan_file(loan_file)
            result.append(f"\n✅ Appraisal record added to loan file")

    except ExternalSystemException as e:
        result.append(f"\n❌ ERROR: {str(e)}")
        result.append(f"🔔 ACTION: Follow up with AMC or consider alternative appraiser")

        async with file_manager.acquire_loan_lock(loan_number):
            loan_file = file_manager.load_loan_file(loan_number)
            if loan_file:
                loan_file.add_audit_entry(
                    actor="loan_processor",
                    action="appraisal_order_failed",
                    details=str(e)
                )
                file_manager.save_loan_file(loan_file)

    return "\n".join(result)


async def receive_appraisal(loan_number: str) -> str:
    """Receive and process completed appraisal - CONCURRENT SAFE"""

    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        if not loan_file.appraisal:
            return f"❌ ERROR: No appraisal ordered for this loan"

        result = []
        result.append(f"📨 RECEIVING APPRAISAL")
        result.append(f"Appraisal ID: {loan_file.appraisal.appraisal_id}")
        result.append("=" * 60)

        purchase_price = loan_file.loan_info.purchase_price or Decimal("400000")
        property_condition = random.choice(["excellent", "good", "average", "average", "fair"])

        appraisal_data = AppraisalManagementSimulator.complete_appraisal(
            purchase_price=purchase_price,
            property_condition=property_condition
        )

        loan_file.appraisal.completed_date = datetime.now()
        loan_file.appraisal.appraiser_name = f"Licensed Appraiser #{random.randint(1000, 9999)}"
        loan_file.appraisal.appraiser_license = f"AL-{random.randint(10000, 99999)}"
        loan_file.appraisal.appraised_value = Decimal(str(appraisal_data['appraised_value']))
        loan_file.appraisal.as_is_value = Decimal(str(appraisal_data['as_is_value']))
        loan_file.appraisal.condition = appraisal_data['condition']
        loan_file.appraisal.comparable_sales = appraisal_data['comparable_sales']
        loan_file.appraisal.issues = appraisal_data['issues']
        loan_file.appraisal.repairs_required = appraisal_data['repairs_required']
        loan_file.appraisal.estimated_repair_cost = Decimal(str(appraisal_data['estimated_repair_cost']))
        loan_file.appraisal.status = "completed"

        result.append(f"✅ Appraisal received and processed")
        result.append(f"Appraiser: {loan_file.appraisal.appraiser_name}")
        result.append(f"License: {loan_file.appraisal.appraiser_license}")
        result.append("")

        result.append(f"📊 APPRAISAL SUMMARY:")
        result.append(f"  Purchase Price: ${purchase_price:,.2f}")
        result.append(f"  Appraised Value: ${loan_file.appraisal.appraised_value:,.2f}")
        result.append(f"  Property Condition: {loan_file.appraisal.condition.title()}")

        value_difference = loan_file.appraisal.appraised_value - purchase_price
        if value_difference < 0:
            result.append(f"\n🚨 VALUE DISCREPANCY:")
            result.append(f"  Appraised value is ${abs(value_difference):,.2f} BELOW purchase price")
            result.append(f"  🔔 ACTION: Borrower must either:")
            result.append(f"     1. Increase down payment by ${abs(value_difference):,.2f}")
            result.append(f"     2. Renegotiate purchase price")
            result.append(f"     3. Request appraisal review/reconsideration")
            loan_file.flags.append(f"Appraisal ${abs(value_difference):,.2f} below purchase price")
        elif value_difference > 0:
            result.append(f"  ✅ Appraised value is ${value_difference:,.2f} above purchase price")
        else:
            result.append(f"  ✅ Appraised value matches purchase price")

        if loan_file.appraisal.comparable_sales:
            result.append(f"\n  Comparable Sales:")
            for i, comp in enumerate(loan_file.appraisal.comparable_sales[:3], 1):
                result.append(f"    {i}. {comp['address']}: ${comp['sale_price']:,.2f} ({comp['proximity']})")

        if loan_file.appraisal.issues:
            result.append(f"\n⚠️  ISSUES IDENTIFIED:")
            for issue in loan_file.appraisal.issues:
                result.append(f"  - {issue}")

        if loan_file.appraisal.repairs_required:
            result.append(f"\n🔧 REPAIRS REQUIRED:")
            for repair in loan_file.appraisal.repairs_required:
                result.append(f"  - {repair}")
            result.append(f"  Estimated Cost: ${loan_file.appraisal.estimated_repair_cost:,.2f}")
            result.append(f"\n  🔔 ACTION: Obtain repair bids and negotiate with seller")

        appraisal_docs = [d for d in loan_file.documents if d.document_type == DocumentType.APPRAISAL]
        if appraisal_docs:
            doc = appraisal_docs[0]
            doc.status = DocumentStatus.APPROVED
            doc.received_date = datetime.now()
            doc.reviewed_by = "loan_processor"
            doc.reviewed_date = datetime.now()
            doc.metadata['appraised_value'] = float(loan_file.appraisal.appraised_value)
            doc.metadata['condition'] = loan_file.appraisal.condition

        loan_amount = loan_file.loan_info.loan_amount
        new_ltv = (loan_amount / loan_file.appraisal.appraised_value) * 100
        loan_file.financial_metrics.ltv_ratio = new_ltv

        result.append(f"\n📊 Updated LTV Ratio: {new_ltv:.2f}%")

        loan_file.add_audit_entry(
            actor="loan_processor",
            action="appraisal_received",
            details=f"Appraised value: ${loan_file.appraisal.appraised_value:,.2f}, Condition: {loan_file.appraisal.condition}"
        )

        file_manager.save_loan_file(loan_file)
        result.append(f"\n✅ Appraisal added to loan file and LTV recalculated")

    return "\n".join(result)


async def order_flood_certification(loan_number: str) -> str:
    """Order flood certification - TRUE CONCURRENT SAFE"""

    # ========== PHASE 1: Load data (LOCKED) ==========
    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        # Extract property address
        property_address = loan_file.property_info.property_address
        address_data = {
            "street": property_address.street,
            "city": property_address.city,
            "state": property_address.state,
            "zip_code": property_address.zip_code
        }
    # Lock released

    # ========== PHASE 2: External API call (NO LOCK) ==========
    result = []
    result.append(f"🌊 ORDERING FLOOD CERTIFICATION")
    result.append(f"Property: {address_data['street']}")
    result.append(f"{address_data['city']}, {address_data['state']} {address_data['zip_code']}")
    result.append("=" * 60)

    try:
        result.append(f"📡 Contacting flood certification service...")

        flood_response = FloodCertificationSimulator.check_flood_zone(
            property_address=f"{address_data['street']}, {address_data['city']}",
            zip_code=address_data['zip_code']
        )

        result.append(f"✅ Flood certification received")
        result.append(f"Transaction ID: {flood_response.transaction_id}")
        result.append("")

        result.append(f"📊 FLOOD CERTIFICATION RESULTS:")
        result.append(f"  FEMA Panel: {flood_response.response_data['fema_panel']}")
        result.append(f"  Flood Zone: {flood_response.flood_zone_designation}")
        result.append(f"  In Flood Zone: {'YES' if flood_response.in_flood_zone else 'NO'}")
        result.append(f"  Flood Insurance Required: {'YES' if flood_response.flood_insurance_required else 'NO'}")

        if flood_response.base_flood_elevation:
            result.append(f"  Base Flood Elevation: {flood_response.base_flood_elevation}")

        result.append(f"\n  🌡️ Future Climate Risk Score: {flood_response.future_risk_score}/10")

        if flood_response.future_risk_score >= 7:
            result.append(f"  🚨 HIGH FUTURE RISK - Climate change impact significant")
        elif flood_response.future_risk_score >= 5:
            result.append(f"  ⚠️ MODERATE FUTURE RISK - Monitor climate trends")
        else:
            result.append(f"  ✅ LOW FUTURE RISK")

        if flood_response.warnings:
            result.append(f"\n⚠️  WARNINGS:")
            for warning in flood_response.warnings:
                result.append(f"  - {warning}")

        # ========== PHASE 3: Update file (LOCKED) ==========
        async with file_manager.acquire_loan_lock(loan_number):
            loan_file = file_manager.load_loan_file(loan_number)
            if not loan_file:
                return f"❌ ERROR: Loan file {loan_number} not found"

            loan_file.property_info.flood_zone = flood_response.flood_zone_designation
            loan_file.property_info.flood_insurance_required = flood_response.flood_insurance_required

            if flood_response.flood_insurance_required:
                loan_file.flags.append("Flood insurance required")
                result.append(f"\n🔔 ACTION: Borrower must obtain flood insurance policy")

            flood_doc = Document(
                document_id=f"DOC-{uuid.uuid4().hex[:8].upper()}",
                document_type=DocumentType.FLOOD_CERTIFICATION,
                status=DocumentStatus.APPROVED,
                received_date=datetime.now(),
                reviewed_by="loan_processor",
                reviewed_date=datetime.now(),
                metadata={
                    "flood_zone": flood_response.flood_zone_designation,
                    "insurance_required": flood_response.flood_insurance_required,
                    "future_risk_score": flood_response.future_risk_score
                }
            )
            loan_file.documents.append(flood_doc)

            loan_file.add_audit_entry(
                actor="loan_processor",
                action="flood_cert_ordered",
                details=f"Zone: {flood_response.flood_zone_designation}, Insurance Required: {flood_response.flood_insurance_required}"
            )

            file_manager.save_loan_file(loan_file)
            result.append(f"\n✅ Flood certification added to loan file")

    except SystemTimeoutException as e:
        result.append(f"\n⏱️  TIMEOUT: {str(e)}")
        result.append(f"🔔 ACTION: Retry flood certification")

    return "\n".join(result)


async def verify_employment(loan_number: str, employment_index: int = 0) -> str:
    """Verify borrower employment - TRUE CONCURRENT SAFE"""

    # ========== PHASE 1: Load data (LOCKED) ==========
    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        if not loan_file.borrowers or not loan_file.borrowers[0].employment:
            return f"❌ ERROR: No employment information in loan file"

        borrower = loan_file.borrowers[0]
        if employment_index >= len(borrower.employment):
            return f"❌ ERROR: Employment index {employment_index} out of range"

        employment = borrower.employment[employment_index]

        # Extract employment data
        employment_data = {
            "employer_name": employment.employer_name,
            "employee_name": f"{borrower.first_name} {borrower.last_name}",
            "reported_income": employment.monthly_income
        }
    # Lock released

    # ========== PHASE 2: External API call (NO LOCK) ==========
    result = []
    result.append(f"💼 VERIFYING EMPLOYMENT")
    result.append(f"Borrower: {employment_data['employee_name']}")
    result.append(f"Employer: {employment_data['employer_name']}")
    result.append("=" * 60)

    try:
        result.append(f"📡 Contacting employer for verification...")

        # Call the SIMULATOR (in external_systems.py)
        voe_response = EmploymentVerificationSimulator.verify_employment(
            employer_name=employment_data['employer_name'],
            employee_name=employment_data['employee_name'],
            reported_income=employment_data['reported_income']
        )

        result.append(f"✅ Employment verified")
        result.append(f"Transaction ID: {voe_response.transaction_id}")
        result.append("")

        result.append(f"📊 VERIFICATION RESULTS:")
        result.append(f"  Employment Status: {voe_response.response_data['employment_status']}")
        result.append(f"  Hire Date: {voe_response.response_data['hire_date']}")
        result.append(f"  Employment Type: {voe_response.response_data['employment_type']}")
        result.append(f"  Reported Income: ${employment_data['reported_income']:,.2f}/month")
        result.append(f"  Verified Income: ${voe_response.response_data['verified_income']:,.2f}/month")

        warnings = []
        if voe_response.warnings:
            result.append(f"\n⚠️  WARNINGS:")
            for warning in voe_response.warnings:
                result.append(f"  - {warning}")
                warnings.append(warning)

        # ========== PHASE 3: Update file (LOCKED) ==========
        async with file_manager.acquire_loan_lock(loan_number):
            loan_file = file_manager.load_loan_file(loan_number)
            if not loan_file:
                return f"❌ ERROR: Loan file {loan_number} not found"

            # Update employment verification
            loan_file.borrowers[0].employment[employment_index].verified = True
            loan_file.borrowers[0].employment[employment_index].verification_date = datetime.now()
            loan_file.borrowers[0].employment[employment_index].verification_method = "VOE - Employer Direct Contact"

            # Add flags
            if warnings:
                loan_file.flags.extend(warnings)

            # Add VOE document
            voe_doc = Document(
                document_id=f"DOC-{uuid.uuid4().hex[:8].upper()}",
                document_type=DocumentType.EMPLOYMENT_VERIFICATION,
                status=DocumentStatus.APPROVED,
                received_date=datetime.now(),
                reviewed_by="loan_processor",
                reviewed_date=datetime.now(),
                metadata={
                    "employer": employment_data['employer_name'],
                    "verified_income": voe_response.response_data['verified_income'],
                    "hire_date": voe_response.response_data['hire_date']
                }
            )
            loan_file.documents.append(voe_doc)

            loan_file.add_audit_entry(
                actor="loan_processor",
                action="employment_verified",
                details=f"Employer: {employment_data['employer_name']}, Income: ${voe_response.response_data['verified_income']}"
            )

            file_manager.save_loan_file(loan_file)
            result.append(f"\n✅ Employment verification added to loan file")

    except SystemTimeoutException as e:
        result.append(f"\n❌ ERROR: {str(e)}")
        result.append(f"🔔 ACTION: Request manual VOE form from borrower")

    return "\n".join(result)

async def submit_to_underwriting(loan_number: str) -> str:
    """Submit complete loan file to underwriting - CONCURRENT SAFE"""

    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        result = []
        result.append(f"📤 SUBMITTING TO UNDERWRITING")
        result.append(f"Loan #{loan_number}")
        result.append("=" * 60)

        validation_errors = []
        validation_warnings = []

        required_doc_types = [
            DocumentType.URLA,
            DocumentType.PAYSTUB,
            DocumentType.W2,
            DocumentType.BANK_STATEMENT,
            DocumentType.CREDIT_REPORT
        ]

        result.append(f"\n✓ DOCUMENT CHECKLIST:")
        for doc_type in required_doc_types:
            matching_docs = [d for d in loan_file.documents if d.document_type == doc_type]
            if not matching_docs:
                validation_errors.append(f"Missing required document: {doc_type.value}")
                result.append(f"  ❌ {doc_type.value}")
            elif matching_docs[0].status != DocumentStatus.APPROVED:
                validation_warnings.append(f"Document not approved: {doc_type.value}")
                result.append(f"  ⚠️  {doc_type.value} (status: {matching_docs[0].status.value})")
            else:
                result.append(f"  ✅ {doc_type.value}")

        result.append(f"\n✓ FINANCIAL METRICS:")
        metrics = loan_file.financial_metrics

        if metrics.ltv_ratio is None:
            validation_errors.append("LTV ratio not calculated")
            result.append(f"  ❌ LTV ratio: Not calculated")
        else:
            result.append(f"  ✅ LTV ratio: {metrics.ltv_ratio:.2f}%")

        if metrics.dti_ratio is None:
            validation_errors.append("DTI ratio not calculated")
            result.append(f"  ❌ DTI ratio: Not calculated")
        else:
            result.append(f"  ✅ DTI ratio: {metrics.dti_ratio:.2f}%")

        result.append(f"\n✓ CREDIT INFORMATION:")
        if not loan_file.borrowers or not loan_file.borrowers[0].credit_report:
            validation_errors.append("Credit report not available")
            result.append(f"  ❌ Credit report: Not available")
        else:
            credit_score = loan_file.borrowers[0].credit_report.credit_score
            result.append(f"  ✅ Credit report: Score {credit_score}")

        result.append(f"\n✓ PROPERTY APPRAISAL:")
        if not loan_file.appraisal or loan_file.appraisal.status != "completed":
            validation_warnings.append("Appraisal not completed")
            result.append(f"  ⚠️  Appraisal: Not completed (can submit pending)")
        else:
            result.append(f"  ✅ Appraisal: ${loan_file.appraisal.appraised_value:,.2f}")

        result.append(f"\n{'=' * 60}")

        if validation_errors:
            result.append(f"\n❌ SUBMISSION BLOCKED - CRITICAL ERRORS:")
            for error in validation_errors:
                result.append(f"  - {error}")
            result.append(f"\n🔔 ACTION: Resolve errors before submitting")

            return "\n".join(result)

        if validation_warnings:
            result.append(f"\n⚠️  WARNINGS (proceeding anyway):")
            for warning in validation_warnings:
                result.append(f"  - {warning}")

        result.append(f"\n✅ VALIDATION PASSED - SUBMITTING TO UNDERWRITING")
        result.append(f"")
        result.append(f"📊 SUBMISSION PACKAGE:")
        result.append(f"  Borrower: {loan_file.borrowers[0].first_name} {loan_file.borrowers[0].last_name}")
        result.append(f"  Loan Amount: ${loan_file.loan_info.loan_amount:,.2f}")
        result.append(f"  Property: {loan_file.property_info.property_address.street}")
        result.append(f"  LTV: {metrics.ltv_ratio:.2f}%")
        result.append(f"  DTI: {metrics.dti_ratio:.2f}%")
        result.append(f"  Credit Score: {loan_file.borrowers[0].credit_report.credit_score}")
        result.append(
            f"  Documents: {len([d for d in loan_file.documents if d.status == DocumentStatus.APPROVED])} approved")

        loan_file.update_status(
            LoanStatus.SUBMITTED_TO_UNDERWRITING,
            "loan_processor",
            "Complete file submitted to underwriting"
        )

        loan_file.processor_name = "loan_processor_agent"

        file_manager.save_loan_file(loan_file)

        result.append(f"\n✅ File submitted successfully - handed off to underwriter")
        result.append(f"\n🔄 Next Step: Underwriter will review file and issue decision")

    return "\n".join(result)


async def clear_underwriting_conditions(
        loan_number: str,
        cleared_conditions: List[str]
) -> str:
    """Clear underwriting conditions - CONCURRENT SAFE"""

    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        result = []
        result.append(f"✅ CLEARING UNDERWRITING CONDITIONS")
        result.append(f"Loan #{loan_number}")
        result.append("=" * 60)

        if not loan_file.current_conditions:
            result.append("\n❌ No conditions on file to clear")
            return "\n".join(result)

        cleared_count = 0
        not_found_count = 0

        # For each description, find matching conditions
        for description in cleared_conditions:
            found = False
            for condition in loan_file.current_conditions:
                # Match by description similarity
                if condition.status != "cleared" and (
                        description.lower() in condition.description.lower() or
                        condition.description.lower() in description.lower()
                ):
                    condition.status = "cleared"
                    condition.cleared_date = datetime.now()
                    condition.cleared_by = "loan_processor"
                    cleared_count += 1
                    found = True

                    result.append(f"\n✅ Cleared: {condition.condition_id}")
                    result.append(f"   {condition.description}")
                    break

            if not found:
                not_found_count += 1
                result.append(f"\n❌ Condition not found: {description[:50]}...")

        result.append(f"\n{'=' * 60}")
        result.append(f"Conditions Cleared: {cleared_count}")
        result.append(f"Conditions Not Found: {not_found_count}")

        remaining = len([c for c in loan_file.current_conditions if c.status != "cleared"])
        result.append(f"Remaining Conditions: {remaining}")

        # Check if all cleared
        if remaining == 0:
            result.append(f"\n✅ ALL CONDITIONS CLEARED")
            result.append(f"🔄 Ready to resubmit to underwriting for final approval")

            loan_file.update_status(
                LoanStatus.UNDERWRITING_IN_PROGRESS,
                "loan_processor",
                "All conditions cleared - ready for final approval"
            )

        file_manager.save_loan_file(loan_file)

        return "\n".join(result)


# ... (previous code above) ...

async def order_appraisal(loan_number: str) -> str:
    """Order property appraisal - CONCURRENT SAFE"""

    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        result = []
        result.append(f"🏠 ORDERING APPRAISAL")
        result.append(f"Property: {loan_file.property_info.property_address.street}")
        result.append(
            f"{loan_file.property_info.property_address.city}, {loan_file.property_info.property_address.state}")
        result.append("=" * 60)

        property_data = {
            "loan_number": loan_number,  # ← ADD THIS
            "street": loan_file.property_info.property_address.street,
            "city": loan_file.property_info.property_address.city,
            "state": loan_file.property_info.property_address.state,
            "purchase_price": loan_file.loan_info.purchase_price or Decimal("0")
        }

        try:
            result.append(f"📡 Contacting Appraisal Management Company...")

            appraisal_response = AppraisalManagementSimulator.order_appraisal(
                loan_number=property_data['loan_number'],  # ← FIX: Add loan_number
                property_address=f"{loan_file.property_info.property_address.street}, {loan_file.property_info.property_address.city}",
                purchase_price=loan_file.loan_info.purchase_price or Decimal("0")
            )

            result.append(f"✅ Appraisal ordered successfully")
            result.append(f"Transaction ID: {appraisal_response.transaction_id}")
            result.append(f"Order ID: {appraisal_response.response_data['order_id']}")
            result.append(f"Appraisal Fee: ${appraisal_response.response_data['fee']:.2f}")
            result.append(f"Estimated Completion: {appraisal_response.response_data['estimated_completion']}")

            if appraisal_response.response_data.get('appraiser_assigned'):
                result.append(f"✅ Appraiser assigned")
            else:
                result.append(f"⏳ Appraiser assignment pending")

            if appraisal_response.warnings:
                result.append(f"\n⚠️  WARNINGS:")
                for warning in appraisal_response.warnings:
                    result.append(f"  - {warning}")

            from models import Appraisal
            loan_file.appraisal = Appraisal(
                appraisal_id=appraisal_response.response_data['order_id'],
                ordered_date=datetime.now(),
                status="ordered"
            )

            appraisal_doc = Document(
                document_id=f"DOC-{uuid.uuid4().hex[:8].upper()}",
                document_type=DocumentType.APPRAISAL,
                status=DocumentStatus.REQUESTED,
                metadata={
                    "order_id": appraisal_response.response_data['order_id'],
                    "estimated_completion": appraisal_response.response_data['estimated_completion']
                }
            )
            loan_file.documents.append(appraisal_doc)

            loan_file.update_status(
                LoanStatus.APPRAISAL_ORDERED,
                "loan_processor",
                f"Appraisal ordered - Order ID: {appraisal_response.response_data['order_id']}"
            )

            file_manager.save_loan_file(loan_file)
            result.append(f"\n✅ Appraisal record added to loan file")

        except ExternalSystemException as e:
            result.append(f"\n❌ ERROR: {str(e)}")
            result.append(f"🔔 ACTION: Follow up with AMC or consider alternative appraiser")
            loan_file.add_audit_entry(
                actor="loan_processor",
                action="appraisal_order_failed",
                details=str(e)
            )
            file_manager.save_loan_file(loan_file)

    return "\n".join(result)


async def receive_appraisal(loan_number: str) -> str:
    """Receive and process completed appraisal - CONCURRENT SAFE"""

    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        if not loan_file.appraisal:
            return f"❌ ERROR: No appraisal ordered for this loan"

        result = []
        result.append(f"📨 RECEIVING APPRAISAL")
        result.append(f"Appraisal ID: {loan_file.appraisal.appraisal_id}")
        result.append("=" * 60)

        purchase_price = loan_file.loan_info.purchase_price or Decimal("400000")
        property_condition = random.choice(["excellent", "good", "average", "average", "fair"])

        appraisal_data = AppraisalManagementSimulator.complete_appraisal(
            purchase_price=purchase_price,
            property_condition=property_condition
        )

        loan_file.appraisal.completed_date = datetime.now()
        loan_file.appraisal.appraiser_name = f"Licensed Appraiser #{random.randint(1000, 9999)}"
        loan_file.appraisal.appraiser_license = f"AL-{random.randint(10000, 99999)}"
        loan_file.appraisal.appraised_value = Decimal(str(appraisal_data['appraised_value']))
        loan_file.appraisal.as_is_value = Decimal(str(appraisal_data['as_is_value']))
        loan_file.appraisal.condition = appraisal_data['condition']
        loan_file.appraisal.comparable_sales = appraisal_data['comparable_sales']
        loan_file.appraisal.issues = appraisal_data['issues']
        loan_file.appraisal.repairs_required = appraisal_data['repairs_required']
        loan_file.appraisal.estimated_repair_cost = Decimal(str(appraisal_data['estimated_repair_cost']))
        loan_file.appraisal.status = "completed"

        result.append(f"✅ Appraisal received and processed")
        result.append(f"Appraiser: {loan_file.appraisal.appraiser_name}")
        result.append(f"License: {loan_file.appraisal.appraiser_license}")
        result.append("")

        result.append(f"📊 APPRAISAL SUMMARY:")
        result.append(f"  Purchase Price: ${purchase_price:,.2f}")
        result.append(f"  Appraised Value: ${loan_file.appraisal.appraised_value:,.2f}")
        result.append(f"  Property Condition: {loan_file.appraisal.condition.title()}")

        value_difference = loan_file.appraisal.appraised_value - purchase_price
        if value_difference < 0:
            result.append(f"\n🚨 VALUE DISCREPANCY:")
            result.append(f"  Appraised value is ${abs(value_difference):,.2f} BELOW purchase price")
            result.append(f"  🔔 ACTION: Borrower must either:")
            result.append(f"     1. Increase down payment by ${abs(value_difference):,.2f}")
            result.append(f"     2. Renegotiate purchase price")
            result.append(f"     3. Request appraisal review/reconsideration")
            loan_file.flags.append(f"Appraisal ${abs(value_difference):,.2f} below purchase price")
        elif value_difference > 0:
            result.append(f"  ✅ Appraised value is ${value_difference:,.2f} above purchase price")
        else:
            result.append(f"  ✅ Appraised value matches purchase price")

        if loan_file.appraisal.comparable_sales:
            result.append(f"\n  Comparable Sales:")
            for i, comp in enumerate(loan_file.appraisal.comparable_sales[:3], 1):
                result.append(f"    {i}. {comp['address']}: ${comp['sale_price']:,.2f} ({comp['proximity']})")

        if loan_file.appraisal.issues:
            result.append(f"\n⚠️  ISSUES IDENTIFIED:")
            for issue in loan_file.appraisal.issues:
                result.append(f"  - {issue}")

        if loan_file.appraisal.repairs_required:
            result.append(f"\n🔧 REPAIRS REQUIRED:")
            for repair in loan_file.appraisal.repairs_required:
                result.append(f"  - {repair}")
            result.append(f"  Estimated Cost: ${loan_file.appraisal.estimated_repair_cost:,.2f}")
            result.append(f"\n  🔔 ACTION: Obtain repair bids and negotiate with seller")

        appraisal_docs = [d for d in loan_file.documents if d.document_type == DocumentType.APPRAISAL]
        if appraisal_docs:
            doc = appraisal_docs[0]
            doc.status = DocumentStatus.APPROVED
            doc.received_date = datetime.now()
            doc.reviewed_by = "loan_processor"
            doc.reviewed_date = datetime.now()
            doc.metadata['appraised_value'] = float(loan_file.appraisal.appraised_value)
            doc.metadata['condition'] = loan_file.appraisal.condition

        loan_amount = loan_file.loan_info.loan_amount
        new_ltv = (loan_amount / loan_file.appraisal.appraised_value) * 100
        loan_file.financial_metrics.ltv_ratio = new_ltv

        result.append(f"\n📊 Updated LTV Ratio: {new_ltv:.2f}%")

        loan_file.add_audit_entry(
            actor="loan_processor",
            action="appraisal_received",
            details=f"Appraised value: ${loan_file.appraisal.appraised_value:,.2f}, Condition: {loan_file.appraisal.condition}"
        )

        file_manager.save_loan_file(loan_file)
        result.append(f"\n✅ Appraisal added to loan file and LTV recalculated")

    return "\n".join(result)


async def order_flood_certification(loan_number: str) -> str:
    """Order flood certification - CONCURRENT SAFE"""

    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        result = []
        result.append(f"🌊 ORDERING FLOOD CERTIFICATION")
        property_address = loan_file.property_info.property_address
        result.append(f"Property: {property_address.street}")
        result.append(f"{property_address.city}, {property_address.state} {property_address.zip_code}")
        result.append("=" * 60)

        try:
            result.append(f"📡 Contacting flood certification service...")

            flood_response = FloodCertificationSimulator.check_flood_zone(
                property_address=f"{property_address.street}, {property_address.city}",
                zip_code=property_address.zip_code
            )

            result.append(f"✅ Flood certification received")
            result.append(f"Transaction ID: {flood_response.transaction_id}")
            result.append("")

            result.append(f"📊 FLOOD CERTIFICATION RESULTS:")
            result.append(f"  FEMA Panel: {flood_response.response_data['fema_panel']}")
            result.append(f"  Flood Zone: {flood_response.flood_zone_designation}")
            result.append(f"  In Flood Zone: {'YES' if flood_response.in_flood_zone else 'NO'}")
            result.append(f"  Flood Insurance Required: {'YES' if flood_response.flood_insurance_required else 'NO'}")

            if flood_response.base_flood_elevation:
                result.append(f"  Base Flood Elevation: {flood_response.base_flood_elevation}")

            result.append(f"\n  🌡️ Future Climate Risk Score: {flood_response.future_risk_score}/10")

            if flood_response.future_risk_score >= 7:
                result.append(f"  🚨 HIGH FUTURE RISK - Climate change impact significant")
            elif flood_response.future_risk_score >= 5:
                result.append(f"  ⚠️ MODERATE FUTURE RISK - Monitor climate trends")
            else:
                result.append(f"  ✅ LOW FUTURE RISK")

            if flood_response.warnings:
                result.append(f"\n⚠️  WARNINGS:")
                for warning in flood_response.warnings:
                    result.append(f"  - {warning}")

            loan_file.property_info.flood_zone = flood_response.flood_zone_designation
            loan_file.property_info.flood_insurance_required = flood_response.flood_insurance_required

            if flood_response.flood_insurance_required:
                loan_file.flags.append("Flood insurance required")
                result.append(f"\n🔔 ACTION: Borrower must obtain flood insurance policy")

            flood_doc = Document(
                document_id=f"DOC-{uuid.uuid4().hex[:8].upper()}",
                document_type=DocumentType.FLOOD_CERTIFICATION,
                status=DocumentStatus.APPROVED,
                received_date=datetime.now(),
                reviewed_by="loan_processor",
                reviewed_date=datetime.now(),
                metadata={
                    "flood_zone": flood_response.flood_zone_designation,
                    "insurance_required": flood_response.flood_insurance_required,
                    "future_risk_score": flood_response.future_risk_score
                }
            )
            loan_file.documents.append(flood_doc)

            loan_file.add_audit_entry(
                actor="loan_processor",
                action="flood_cert_ordered",
                details=f"Zone: {flood_response.flood_zone_designation}, Insurance Required: {flood_response.flood_insurance_required}"
            )

            file_manager.save_loan_file(loan_file)
            result.append(f"\n✅ Flood certification added to loan file")

        except SystemTimeoutException as e:
            result.append(f"\n⏱️  TIMEOUT: {str(e)}")
            result.append(f"🔔 ACTION: Retry flood certification")

    return "\n".join(result)

async def submit_to_underwriting(loan_number: str) -> str:
    """Submit complete loan file to underwriting - CONCURRENT SAFE"""

    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        result = []
        result.append(f"📤 SUBMITTING TO UNDERWRITING")
        result.append(f"Loan #{loan_number}")
        result.append("=" * 60)

        validation_errors = []
        validation_warnings = []

        required_doc_types = [
            DocumentType.URLA,
            DocumentType.PAYSTUB,
            DocumentType.W2,
            DocumentType.BANK_STATEMENT,
            DocumentType.CREDIT_REPORT
        ]

        result.append(f"\n✓ DOCUMENT CHECKLIST:")
        for doc_type in required_doc_types:
            matching_docs = [d for d in loan_file.documents if d.document_type == doc_type]
            if not matching_docs:
                validation_errors.append(f"Missing required document: {doc_type.value}")
                result.append(f"  ❌ {doc_type.value}")
            elif matching_docs[0].status != DocumentStatus.APPROVED:
                validation_warnings.append(f"Document not approved: {doc_type.value}")
                result.append(f"  ⚠️  {doc_type.value} (status: {matching_docs[0].status.value})")
            else:
                result.append(f"  ✅ {doc_type.value}")

        result.append(f"\n✓ FINANCIAL METRICS:")
        metrics = loan_file.financial_metrics

        if metrics.ltv_ratio is None:
            validation_errors.append("LTV ratio not calculated")
            result.append(f"  ❌ LTV ratio: Not calculated")
        else:
            result.append(f"  ✅ LTV ratio: {metrics.ltv_ratio:.2f}%")

        if metrics.dti_ratio is None:
            validation_errors.append("DTI ratio not calculated")
            result.append(f"  ❌ DTI ratio: Not calculated")
        else:
            result.append(f"  ✅ DTI ratio: {metrics.dti_ratio:.2f}%")

        result.append(f"\n✓ CREDIT INFORMATION:")
        if not loan_file.borrowers or not loan_file.borrowers[0].credit_report:
            validation_errors.append("Credit report not available")
            result.append(f"  ❌ Credit report: Not available")
        else:
            credit_score = loan_file.borrowers[0].credit_report.credit_score
            result.append(f"  ✅ Credit report: Score {credit_score}")

        result.append(f"\n✓ PROPERTY APPRAISAL:")
        if not loan_file.appraisal or loan_file.appraisal.status != "completed":
            validation_warnings.append("Appraisal not completed")
            result.append(f"  ⚠️  Appraisal: Not completed (can submit pending)")
        else:
            result.append(f"  ✅ Appraisal: ${loan_file.appraisal.appraised_value:,.2f}")

        result.append(f"\n{'=' * 60}")

        if validation_errors:
            result.append(f"\n❌ SUBMISSION BLOCKED - CRITICAL ERRORS:")
            for error in validation_errors:
                result.append(f"  - {error}")
            result.append(f"\n🔔 ACTION: Resolve errors before submitting")

            return "\n".join(result)

        if validation_warnings:
            result.append(f"\n⚠️  WARNINGS (proceeding anyway):")
            for warning in validation_warnings:
                result.append(f"  - {warning}")

        result.append(f"\n✅ VALIDATION PASSED - SUBMITTING TO UNDERWRITING")
        result.append(f"")
        result.append(f"📊 SUBMISSION PACKAGE:")
        result.append(f"  Borrower: {loan_file.borrowers[0].first_name} {loan_file.borrowers[0].last_name}")
        result.append(f"  Loan Amount: ${loan_file.loan_info.loan_amount:,.2f}")
        result.append(f"  Property: {loan_file.property_info.property_address.street}")
        result.append(f"  LTV: {metrics.ltv_ratio:.2f}%")
        result.append(f"  DTI: {metrics.dti_ratio:.2f}%")
        result.append(f"  Credit Score: {loan_file.borrowers[0].credit_report.credit_score}")
        result.append(
            f"  Documents: {len([d for d in loan_file.documents if d.status == DocumentStatus.APPROVED])} approved")

        loan_file.update_status(
            LoanStatus.SUBMITTED_TO_UNDERWRITING,
            "loan_processor",
            "Complete file submitted to underwriting"
        )

        loan_file.processor_name = "loan_processor_agent"

        file_manager.save_loan_file(loan_file)

        result.append(f"\n✅ File submitted successfully - handed off to underwriter")
        result.append(f"\n🔄 Next Step: Underwriter will review file and issue decision")

    return "\n".join(result)


async def collect_documents(
        loan_number: str,
        document_types: List[str]
) -> str:
    """
    Collect missing documents from borrower (simulates borrower upload)
    """

    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        result = []
        result.append(f"📥 COLLECTING DOCUMENTS FROM BORROWER")
        result.append(f"Loan #{loan_number}")
        result.append("=" * 60)
        result.append(f"⏰ Simulating borrower document upload...")

        # ✅ IMPROVED: More flexible matching
        type_mapping = {
            # Exact matches
            "URLA": DocumentType.URLA,
            "PAYSTUB": DocumentType.PAYSTUB,
            "PAYSTUBS": DocumentType.PAYSTUB,
            "W2": DocumentType.W2,
            "W2S": DocumentType.W2,
            "BANK_STATEMENT": DocumentType.BANK_STATEMENT,
            "BANK_STATEMENTS": DocumentType.BANK_STATEMENT,
            "PURCHASE_AGREEMENT": DocumentType.PURCHASE_AGREEMENT,

            # ✅ NEW: Fuzzy matches for natural language
            "UNIFORM RESIDENTIAL LOAN APPLICATION": DocumentType.URLA,
            "LOAN APPLICATION": DocumentType.URLA,
            "1003": DocumentType.URLA,

            "PAY STUB": DocumentType.PAYSTUB,
            "PAY STUBS": DocumentType.PAYSTUB,
            "RECENT PAY STUBS": DocumentType.PAYSTUB,
            "PAYSTUB (2 MONTHS)": DocumentType.PAYSTUB,

            "W-2": DocumentType.W2,
            "W-2 FORM": DocumentType.W2,
            "W-2 FORMS": DocumentType.W2,
            "W2 FORM": DocumentType.W2,
            "W2 FORMS": DocumentType.W2,

            "BANK STATEMENT": DocumentType.BANK_STATEMENT,
            "BANK STATEMENTS": DocumentType.BANK_STATEMENT,
            "BANK STATEMENTS (2 MONTHS)": DocumentType.BANK_STATEMENT,

            "PURCHASE AGREEMENT": DocumentType.PURCHASE_AGREEMENT,
            "SALES CONTRACT": DocumentType.PURCHASE_AGREEMENT,

            "LOE": DocumentType.LOE,
            "LETTER OF EXPLANATION": DocumentType.LOE,
            "LETTER OF EXPLANATION FOR CREDIT INQUIRIES": DocumentType.LOE,
            "EXPLANATION LETTER": DocumentType.LOE,

            "VOA": DocumentType.VOA,
            "ASSET VERIFICATION": DocumentType.VOA,
            "SAVINGS ACCOUNT VERIFICATION": DocumentType.VOA,
            "401K ACCOUNT VERIFICATION": DocumentType.VOA,
            "CHECKING ACCOUNT VERIFICATION": DocumentType.VOA,
            "BANK VERIFICATION": DocumentType.VOA,
        }

        collected_count = 0

        for doc_type_str in document_types:
            # Normalize: uppercase, strip extra spaces/punctuation
            doc_type_normalized = doc_type_str.upper().strip()
            doc_type_normalized = doc_type_normalized.replace("(", "").replace(")", "")
            doc_type_normalized = doc_type_normalized.replace("  ", " ")

            # Try exact match first
            if doc_type_normalized in type_mapping:
                doc_type = type_mapping[doc_type_normalized]

                # Check if we already have this document type
                has_doc = any(d.document_type == doc_type for d in loan_file.documents)
                if has_doc:
                    result.append(f"\n⚠️  Already have: {doc_type.value.upper()}")
                    continue

                # Create the document
                new_doc = Document(
                    document_id=f"DOC-{uuid.uuid4().hex[:8].upper()}",
                    document_type=doc_type,
                    status=DocumentStatus.APPROVED,
                    received_date=date.today(),
                    reviewed_by="loan_processor",
                    reviewed_date=datetime.now(),
                    metadata={"source": "borrower_upload_simulation"}
                )

                loan_file.documents.append(new_doc)
                collected_count += 1

                result.append(f"\n✅ Received: {doc_type.value.upper()}")
                result.append(f"   Document ID: {new_doc.document_id}")
            else:
                # ✅ NEW: Try substring matching
                found = False
                for key, doc_type in type_mapping.items():
                    if key in doc_type_normalized or doc_type_normalized in key:
                        # Check if we already have it
                        has_doc = any(d.document_type == doc_type for d in loan_file.documents)
                        if has_doc:
                            result.append(f"\n⚠️  Already have: {doc_type.value.upper()}")
                            found = True
                            break

                        # Create the document
                        new_doc = Document(
                            document_id=f"DOC-{uuid.uuid4().hex[:8].upper()}",
                            document_type=doc_type,
                            status=DocumentStatus.APPROVED,
                            received_date=date.today(),
                            reviewed_by="loan_processor",
                            reviewed_date=datetime.now(),
                            metadata={"source": "borrower_upload_simulation"}
                        )

                        loan_file.documents.append(new_doc)
                        collected_count += 1
                        found = True

                        result.append(f"\n✅ Received: {doc_type.value.upper()}")
                        result.append(f"   Document ID: {new_doc.document_id}")
                        break

                if not found:
                    result.append(f"\n⚠️  Unknown document type: {doc_type_str}")

        result.append(f"\n{'=' * 60}")
        result.append(f"Documents Collected: {collected_count}")

        loan_file.add_audit_entry(
            actor="loan_processor",
            action="documents_collected",
            details=f"Collected {collected_count} documents from borrower"
        )

        file_manager.save_loan_file(loan_file)

        return "\n".join(result)