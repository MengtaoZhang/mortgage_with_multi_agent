"""
Underwriter tools with concurrent safety
"""

import random
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List
import uuid
import copy  # ← ADD THIS for run_automated_underwriting

from models import (
    LoanFile, LoanStatus, UnderwritingCondition, UnderwritingDecision,
    ConditionType, ConditionSeverity, DocumentType, DocumentStatus
)
from file_manager import file_manager  # ← Import singleton instance
from external_systems import (
    AutomatedUnderwritingSimulator, SystemTimeoutException,
    ExternalSystemException
)

async def run_automated_underwriting(loan_number: str) -> str:
    """Run automated underwriting - TRUE CONCURRENT SAFE"""

    print(f"    🔧 [TOOL CALLED] run_automated_underwriting({loan_number})")

    # ========== PHASE 1: Load data (LOCKED) ==========
    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        # We need to pass the entire loan_file to the simulator
        # so we'll make a deep copy to work with outside the lock
        import copy
        loan_file_copy = copy.deepcopy(loan_file)
    # Lock released

    # ========== PHASE 2: External API call (NO LOCK) ==========
    result = []
    result.append(f"🤖 RUNNING AUTOMATED UNDERWRITING SYSTEM")
    result.append(f"Loan #{loan_number}")
    result.append("=" * 60)

    try:
        result.append(f"📡 Submitting to Desktop Underwriter (DU)...")

        # This takes 2-4 seconds but doesn't block other loans!
        au_response = AutomatedUnderwritingSimulator.run_automated_underwriting(loan_file_copy)

        result.append(f"✅ Automated underwriting complete")
        result.append(f"Transaction ID: {au_response.transaction_id}")
        result.append(f"System: {au_response.response_data['system']}")
        result.append(f"Casefile ID: {au_response.response_data['casefile_id']}")
        result.append("")

        result.append(f"📊 RECOMMENDATION: {au_response.recommendation.upper()}")
        result.append("=" * 60)

        if au_response.recommendation == "approve":
            result.append(f"✅ APPROVE/ELIGIBLE")
            result.append(f"   Loan meets automated underwriting guidelines")
        elif au_response.recommendation == "refer":
            result.append(f"⚠️  REFER - Manual Underwriting Required")
            result.append(f"   Additional review needed by underwriter")
        elif au_response.recommendation == "caution":
            result.append(f"🚨 CAUTION - High Risk")
            result.append(f"   Significant compensating factors required")
        else:
            result.append(f"❌ INELIGIBLE")
            result.append(f"   Does not meet automated guidelines")

        if au_response.findings:
            result.append(f"\n📋 FINDINGS:")
            for finding in au_response.findings:
                result.append(f"  - {finding}")

        if au_response.required_documents:
            result.append(f"\n📄 REQUIRED DOCUMENTS:")
            for doc in au_response.required_documents:
                result.append(f"  - {doc}")

        result.append(f"\n💰 PRICING:")
        result.append(f"  Loan Level Price Adjustment: {au_response.loan_level_price_adjustment}%")
        result.append(f"  Reserves Required: {au_response.reserves_required} months")

        # Check reserves from the copy
        if loan_file_copy.financial_metrics.reserves_months:
            if loan_file_copy.financial_metrics.reserves_months >= au_response.reserves_required:
                result.append(
                    f"  ✅ Borrower has {loan_file_copy.financial_metrics.reserves_months:.1f} months (sufficient)")
            else:
                result.append(
                    f"  ❌ Borrower has {loan_file_copy.financial_metrics.reserves_months:.1f} months (insufficient)")
                result.append(
                    f"     Additional {au_response.reserves_required - loan_file_copy.financial_metrics.reserves_months:.1f} months needed")

        # ========== PHASE 3: Update file (LOCKED) ==========
        async with file_manager.acquire_loan_lock(loan_number):
            loan_file = file_manager.load_loan_file(loan_number)
            if not loan_file:
                return f"❌ ERROR: Loan file {loan_number} not found"

            if not loan_file.underwriting_decisions:
                loan_file.underwriting_decisions = []

            au_decision = UnderwritingDecision(
                decision_id=f"DEC-{uuid.uuid4().hex[:8].upper()}",
                decision_date=datetime.now(),
                underwriter_name="automated_underwriting_system",
                decision_type="automated_findings",
                decision_reason=f"DU Recommendation: {au_response.recommendation}",
                automated_findings={
                    "recommendation": au_response.recommendation,
                    "findings": au_response.findings,
                    "required_documents": au_response.required_documents,
                    "llpa": float(au_response.loan_level_price_adjustment),
                    "reserves_required": au_response.reserves_required
                }
            )
            loan_file.underwriting_decisions.append(au_decision)

            loan_file.update_status(
                LoanStatus.UNDERWRITING_INITIAL_REVIEW,
                "underwriter_agent",
                f"Automated underwriting: {au_response.recommendation}"
            )

            loan_file.add_audit_entry(
                actor="underwriter_agent",
                action="automated_underwriting",
                details=f"DU Recommendation: {au_response.recommendation}"
            )

            file_manager.save_loan_file(loan_file)
            print(f"    [WRITE-COUNT] AU loan={loan_number} writes={file_manager.get_write_count(loan_number)}")
            result.append(f"\n✅ Automated underwriting results recorded")

    except SystemTimeoutException as e:
        result.append(f"\n⏱️  TIMEOUT: {str(e)}")
        result.append(f"🔔 ACTION: Retry automated underwriting")

        async with file_manager.acquire_loan_lock(loan_number):
            loan_file = file_manager.load_loan_file(loan_number)
            if loan_file:
                loan_file.add_audit_entry(
                    actor="underwriter_agent",
                    action="automated_underwriting_failed",
                    details=str(e)
                )
                file_manager.save_loan_file(loan_file)

    except Exception as e:
        err = f"Unexpected AUS error: {e}"
        print(f"    [AUS-ERROR] {err}")
        async with file_manager.acquire_loan_lock(loan_number):
            loan_file = file_manager.load_loan_file(loan_number)
            if loan_file:
                loan_file.add_audit_entry(
                    actor="underwriter_agent",
                    action="automated_underwriting_failed",
                    details=err
                )
                file_manager.save_loan_file(loan_file)
        result.append(f"\n❌ ERROR: {err}")

    return "\n".join(result)


async def review_credit_profile(loan_number: str) -> str:
    """Review credit profile - CONCURRENT SAFE"""

    print(f"    🔧 [TOOL CALLED] review_credit_profile({loan_number})")

    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        result = []
        result.append(f"💳 MANUAL CREDIT REVIEW")
        result.append(f"Loan #{loan_number}")
        result.append("=" * 60)

        borrower = loan_file.borrowers[0] if loan_file.borrowers else None
        if not borrower or not borrower.credit_report:
            return f"❌ ERROR: Credit report not available"

        credit = borrower.credit_report

        result.append(f"\n📊 CREDIT SCORE ANALYSIS:")
        result.append(f"  Score: {credit.credit_score}")

        if credit.credit_score >= 740:
            result.append(f"  ✅ EXCELLENT - Very Low Risk")
        elif credit.credit_score >= 680:
            result.append(f"  ✅ GOOD - Low Risk")
        elif credit.credit_score >= 620:
            result.append(f"  ⚠️  FAIR - Acceptable (conventional minimum)")
        elif credit.credit_score >= 580:
            result.append(f"  🚨 POOR - High Risk (FHA minimum)")
        else:
            result.append(f"  ❌ VERY POOR - May not qualify")

        result.append(f"\n📋 TRADELINE ANALYSIS:")
        result.append(f"  Total Accounts: {len(credit.tradelines)}")

        active_tradelines = [t for t in credit.tradelines if t.closed_date is None]
        result.append(f"  Active Accounts: {len(active_tradelines)}")

        late_payments = [t for t in credit.tradelines if t.payment_status != "current"]
        if late_payments:
            result.append(f"  ⚠️  Accounts with Late Payments: {len(late_payments)}")
            for trade in late_payments[:3]:
                result.append(f"     - {trade.account_type}: {trade.payment_status}")
        else:
            result.append(f"  ✅ All accounts current")

        result.append(f"\n💰 DEBT ANALYSIS:")
        result.append(f"  Total Monthly Debt: ${credit.total_monthly_debt:,.2f}")

        by_type = {}
        for trade in active_tradelines:
            by_type[trade.account_type] = by_type.get(trade.account_type, Decimal(0)) + trade.monthly_payment

        for debt_type, amount in by_type.items():
            result.append(f"    {debt_type.title()}: ${amount:,.2f}")

        result.append(f"\n🔍 CREDIT INQUIRIES:")
        result.append(f"  Total Inquiries (6 months): {len(credit.inquiries)}")

        if len(credit.inquiries) > 3:
            result.append(f"  ⚠️  Multiple inquiries detected - LOE required")
        elif len(credit.inquiries) > 0:
            result.append(f"  ✅ Normal inquiry activity")

        if credit.derogatory_items:
            result.append(f"\n🚨 DEROGATORY ITEMS:")
            for item in credit.derogatory_items:
                result.append(f"  - {item}")
            result.append(f"  🔔 ACTION: Request Letter of Explanation")
        else:
            result.append(f"\n✅ NO DEROGATORY ITEMS")

        if credit.public_records:
            result.append(f"\n🚨 PUBLIC RECORDS:")
            for record in credit.public_records:
                result.append(f"  - {record}")
        else:
            result.append(f"✅ NO PUBLIC RECORDS")

        result.append(f"\n{'='*60}")
        result.append(f"CREDIT ASSESSMENT:")

        credit_issues = []
        if credit.credit_score < 620:
            credit_issues.append("Credit score below conventional minimum")
        if late_payments:
            credit_issues.append("Recent late payments")
        if len(credit.inquiries) > 3:
            credit_issues.append("Multiple credit inquiries")
        if credit.derogatory_items:
            credit_issues.append("Derogatory items present")

        if not credit_issues:
            result.append(f"✅ CREDIT APPROVED - No significant issues")
        else:
            result.append(f"⚠️  CREDIT CONCERNS:")
            for issue in credit_issues:
                result.append(f"  - {issue}")

        loan_file.add_audit_entry(
            actor="underwriter_agent",
            action="credit_review",
            details=f"Credit score: {credit.credit_score}, Issues: {len(credit_issues)}"
        )

        file_manager.save_loan_file(loan_file)

    return "\n".join(result)


async def review_income_employment(loan_number: str) -> str:
    """Review income and employment - CONCURRENT SAFE"""

    print(f"    🔧 [TOOL CALLED] review_income_employment({loan_number})")

    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        result = []
        result.append(f"💼 INCOME & EMPLOYMENT REVIEW")
        result.append(f"Loan #{loan_number}")
        result.append("=" * 60)

        borrower = loan_file.borrowers[0] if loan_file.borrowers else None
        if not borrower:
            return f"❌ ERROR: No borrower information"

        result.append(f"\n👔 EMPLOYMENT HISTORY:")

        if not borrower.employment:
            result.append(f"  ❌ No employment information")
            return "\n".join(result)

        total_months = 0
        for emp in borrower.employment:
            start = emp.start_date
            end = emp.end_date or date.today()
            months = (end.year - start.year) * 12 + (end.month - start.month)
            total_months += months

            result.append(f"\n  Employer: {emp.employer_name}")
            result.append(f"    Position: {emp.job_title}")
            result.append(f"    Type: {emp.employment_type.value}")
            result.append(f"    Duration: {start} to {end.strftime('%Y-%m-%d') if emp.end_date else 'Present'} ({months} months)")
            result.append(f"    Monthly Income: ${emp.monthly_income:,.2f}")
            result.append(f"    Verified: {'Yes' if emp.verified else 'No'}")

        result.append(f"\n  Total Employment History: {total_months} months ({total_months/12:.1f} years)")

        if total_months >= 24:
            result.append(f"  ✅ Meets 2-year employment requirement")
        else:
            result.append(f"  ⚠️  Less than 2 years - need to review job stability")

        result.append(f"\n💰 INCOME ANALYSIS:")

        if not borrower.income:
            result.append(f"  ⚠️  No detailed income breakdown")
            total_income = sum(emp.monthly_income for emp in borrower.employment if emp.is_current)
            result.append(f"  Total from employment: ${total_income:,.2f}")
        else:
            result.append(f"  Income Sources:")
            total_income = Decimal(0)
            for inc in borrower.income:
                result.append(f"    {inc.income_type}: ${inc.monthly_amount:,.2f}")
                if inc.is_stable:
                    total_income += inc.monthly_amount
                else:
                    result.append(f"      ⚠️  Flagged as unstable - may not be counted")

        result.append(f"\n  Total Qualifying Income: ${total_income:,.2f}")

        verified_employment = [e for e in borrower.employment if e.verified]
        if verified_employment:
            result.append(f"  ✅ {len(verified_employment)}/{len(borrower.employment)} employment(s) verified")
        else:
            result.append(f"  ⚠️  Employment not yet verified - VOE required")

        self_employed = [e for e in borrower.employment if e.employment_type.value == "self_employed"]
        if self_employed:
            result.append(f"\n  ⚠️  SELF-EMPLOYMENT DETECTED:")
            result.append(f"     - 2 years tax returns required")
            result.append(f"     - Year-to-date P&L required")
            result.append(f"     - CPA verification may be needed")

        result.append(f"\n{'='*60}")
        result.append(f"INCOME/EMPLOYMENT ASSESSMENT:")

        income_issues = []
        if total_months < 24:
            income_issues.append("Less than 2 years employment history")
        if not verified_employment:
            income_issues.append("Employment not verified")
        if self_employed:
            income_issues.append("Self-employment requires additional documentation")

        if not income_issues:
            result.append(f"✅ INCOME/EMPLOYMENT APPROVED")
        else:
            result.append(f"⚠️  ISSUES TO ADDRESS:")
            for issue in income_issues:
                result.append(f"  - {issue}")

        loan_file.add_audit_entry(
            actor="underwriter_agent",
            action="income_review",
            details=f"Total income: ${total_income}, Employment months: {total_months}"
        )

        file_manager.save_loan_file(loan_file)

    return "\n".join(result)


async def review_assets_reserves(loan_number: str) -> str:
    """Review assets and reserves - CONCURRENT SAFE"""

    print(f"    🔧 [TOOL CALLED] review_assets_reserves({loan_number})")

    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        result = []
        result.append(f"💎 ASSETS & RESERVES REVIEW")
        result.append(f"Loan #{loan_number}")
        result.append("=" * 60)

        borrower = loan_file.borrowers[0] if loan_file.borrowers else None
        if not borrower or not borrower.assets:
            result.append(f"❌ No asset information available")
            return "\n".join(result)

        result.append(f"\n📊 ASSET BREAKDOWN:")

        liquid_assets = Decimal(0)
        retirement_assets = Decimal(0)
        other_assets = Decimal(0)

        for asset in borrower.assets:
            result.append(f"\n  {asset.institution_name}")
            result.append(f"    Type: {asset.asset_type}")
            result.append(f"    Account: ***{asset.account_number[-4:]}")
            result.append(f"    Balance: ${asset.balance:,.2f}")
            result.append(f"    Statement Date: {asset.statement_date}")
            result.append(f"    Verified: {'Yes' if asset.verified else 'No'}")

            if asset.asset_type in ["checking", "savings", "money_market"]:
                liquid_assets += asset.balance
            elif asset.asset_type in ["401k", "ira", "retirement"]:
                retirement_assets += asset.balance
            else:
                other_assets += asset.balance

            if asset.large_deposits:
                result.append(f"    ⚠️  LARGE DEPOSITS DETECTED:")
                for deposit in asset.large_deposits:
                    result.append(f"       ${deposit.get('amount', 0):,.2f} on {deposit.get('date', 'unknown')}")
                result.append(f"       🔔 Sourcing and seasoning required")

            if asset.seasoning_issues:
                result.append(f"    ⚠️  SEASONING ISSUES:")
                for issue in asset.seasoning_issues:
                    result.append(f"       - {issue}")

        result.append(f"\n{'='*60}")
        result.append(f"ASSET SUMMARY:")
        result.append(f"  Liquid Assets: ${liquid_assets:,.2f}")
        result.append(f"  Retirement Assets: ${retirement_assets:,.2f}")
        result.append(f"  Other Assets: ${other_assets:,.2f}")
        result.append(f"  Total Assets: ${liquid_assets + retirement_assets + other_assets:,.2f}")

        housing_payment = loan_file.financial_metrics.monthly_housing_payment or Decimal(0)

        if housing_payment > 0:
            reserves_months = liquid_assets / housing_payment
            result.append(f"\n💰 RESERVES CALCULATION:")
            result.append(f"  Liquid Assets: ${liquid_assets:,.2f}")
            result.append(f"  Monthly PITI: ${housing_payment:,.2f}")
            result.append(f"  Reserves: {reserves_months:.1f} months")

            required_reserves = 2
            if loan_file.property_info.occupancy_type.value == "investment":
                required_reserves = 6
            elif loan_file.financial_metrics.dti_ratio and loan_file.financial_metrics.dti_ratio > 45:
                required_reserves = 6

            result.append(f"  Required: {required_reserves} months")

            if reserves_months >= required_reserves:
                result.append(f"  ✅ SUFFICIENT RESERVES")
            else:
                shortage = (required_reserves - reserves_months) * housing_payment
                result.append(f"  ❌ INSUFFICIENT - Need ${shortage:,.2f} more")

        cash_to_close = loan_file.financial_metrics.cash_to_close or Decimal(0)
        total_available = liquid_assets

        result.append(f"\n💵 CASH TO CLOSE:")
        result.append(f"  Required: ${cash_to_close:,.2f}")
        result.append(f"  Available: ${total_available:,.2f}")

        if total_available >= cash_to_close:
            result.append(f"  ✅ SUFFICIENT FUNDS")
        else:
            shortage = cash_to_close - total_available
            result.append(f"  ❌ SHORT ${shortage:,.2f}")

        result.append(f"\n{'='*60}")
        result.append(f"ASSETS ASSESSMENT:")

        asset_issues = []
        if reserves_months < required_reserves:
            asset_issues.append("Insufficient reserves")
        if total_available < cash_to_close:
            asset_issues.append("Insufficient cash to close")

        for asset in borrower.assets:
            if not asset.verified:
                asset_issues.append(f"Asset at {asset.institution_name} not verified")
            if asset.large_deposits:
                asset_issues.append(f"Large deposits need sourcing at {asset.institution_name}")

        if not asset_issues:
            result.append(f"✅ ASSETS APPROVED")
        else:
            result.append(f"⚠️  ISSUES TO ADDRESS:")
            for issue in asset_issues:
                result.append(f"  - {issue}")

        loan_file.add_audit_entry(
            actor="underwriter_agent",
            action="assets_review",
            details=f"Liquid assets: ${liquid_assets}, Reserves: {reserves_months:.1f} months"
        )

        file_manager.save_loan_file(loan_file)

    return "\n".join(result)


async def review_property_appraisal(loan_number: str) -> str:
    """Review property appraisal - CONCURRENT SAFE"""

    print(f"    🔧 [TOOL CALLED] review_property_appraisal({loan_number})")

    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        result = []
        result.append(f"🏠 PROPERTY APPRAISAL REVIEW")
        result.append(f"Loan #{loan_number}")
        result.append("=" * 60)

        if not loan_file.appraisal:
            result.append(f"❌ No appraisal on file")
            result.append(f"🔔 ACTION: Order appraisal or suspend file")
            return "\n".join(result)

        appraisal = loan_file.appraisal

        if appraisal.status != "completed":
            result.append(f"⏳ Appraisal Status: {appraisal.status}")
            result.append(f"🔔 Waiting for appraisal completion")
            return "\n".join(result)

        result.append(f"\n📄 APPRAISAL DETAILS:")
        result.append(f"  Appraiser: {appraisal.appraiser_name}")
        result.append(f"  License: {appraisal.appraiser_license}")
        result.append(f"  Date: {appraisal.completed_date.strftime('%Y-%m-%d')}")
        result.append(f"  Appraised Value: ${appraisal.appraised_value:,.2f}")
        result.append(f"  As-Is Value: ${appraisal.as_is_value:,.2f}")
        result.append(f"  Condition: {appraisal.condition.title()}")

        purchase_price = loan_file.loan_info.purchase_price or Decimal(0)
        result.append(f"\n💰 VALUE ANALYSIS:")
        result.append(f"  Purchase Price: ${purchase_price:,.2f}")
        result.append(f"  Appraised Value: ${appraisal.appraised_value:,.2f}")

        value_diff = appraisal.appraised_value - purchase_price
        value_diff_pct = (value_diff / purchase_price * 100) if purchase_price > 0 else 0

        result.append(f"  Difference: ${value_diff:,.2f} ({value_diff_pct:+.2f}%)")

        if value_diff >= 0:
            result.append(f"  ✅ Appraised value supports transaction")
        else:
            result.append(f"  🚨 APPRAISAL BELOW PURCHASE PRICE")
            result.append(f"     Options:")
            result.append(f"     1. Borrower increases down payment by ${abs(value_diff):,.2f}")
            result.append(f"     2. Renegotiate purchase price")
            result.append(f"     3. Request reconsideration of value")

        if appraisal.comparable_sales:
            result.append(f"\n🏘️  COMPARABLE SALES:")
            for i, comp in enumerate(appraisal.comparable_sales, 1):
                result.append(f"  {i}. {comp['address']}")
                result.append(f"     Price: ${comp['sale_price']:,.2f} | Distance: {comp['proximity']}")

        result.append(f"\n🔍 PROPERTY CONDITION:")
        result.append(f"  Overall Condition: {appraisal.condition.title()}")

        if appraisal.condition in ["excellent", "good"]:
            result.append(f"  ✅ Property in acceptable condition")
        elif appraisal.condition == "average":
            result.append(f"  ⚠️  Average condition - review for issues")
        else:
            result.append(f"  ⚠️  Below average condition - repairs likely needed")

        if appraisal.issues:
            result.append(f"\n⚠️  ISSUES NOTED:")
            for issue in appraisal.issues:
                result.append(f"  - {issue}")

        if appraisal.repairs_required:
            result.append(f"\n🔧 REQUIRED REPAIRS:")
            for repair in appraisal.repairs_required:
                result.append(f"  - {repair}")
            result.append(f"  Estimated Cost: ${appraisal.estimated_repair_cost:,.2f}")
            result.append(f"\n  🔔 ACTION: Obtain contractor bids and negotiate with seller")

        result.append(f"\n{'='*60}")
        result.append(f"APPRAISAL ASSESSMENT:")

        appraisal_issues = []
        if value_diff < 0:
            appraisal_issues.append("Value below purchase price")
        if appraisal.condition in ["fair", "poor"]:
            appraisal_issues.append("Property condition concerns")
        if appraisal.repairs_required:
            appraisal_issues.append("Repairs required before closing")

        if not appraisal_issues:
            result.append(f"✅ APPRAISAL APPROVED")
        else:
            result.append(f"⚠️  ISSUES TO ADDRESS:")
            for issue in appraisal_issues:
                result.append(f"  - {issue}")

        loan_file.add_audit_entry(
            actor="underwriter_agent",
            action="appraisal_review",
            details=f"Appraised value: ${appraisal.appraised_value}, Condition: {appraisal.condition}"
        )

        file_manager.save_loan_file(loan_file)

    return "\n".join(result)


async def issue_underwriting_conditions(
        loan_number: str,
        conditions: List[str]  # ← Simple list of descriptions
) -> str:
    """
    Issue underwriting conditions - CONCURRENT SAFE

    Args:
        loan_number: The loan number
        conditions: List of condition descriptions
            Example: ["VOE required for Tech Corp", "Verify bank assets", "LOE for credit inquiries"]
    """

    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        result = []
        result.append(f"📋 ISSUING UNDERWRITING CONDITIONS")
        result.append(f"Loan #{loan_number}")
        result.append("=" * 60)

        new_conditions = []

        for description in conditions:
            # Auto-detect condition type from description
            cond_type = ConditionType.OTHER  # Default
            if "VOE" in description.upper() or "EMPLOY" in description.upper():
                cond_type = ConditionType.VOE
            elif "VOA" in description.upper() or "ASSET" in description.upper():
                cond_type = ConditionType.VOA
            elif "LOE" in description.upper() or "LETTER" in description.upper():
                cond_type = ConditionType.LOE
            elif "APPRAISAL" in description.upper():
                cond_type = ConditionType.APPRAISAL
            elif "TITLE" in description.upper():
                cond_type = ConditionType.TITLE

            condition = UnderwritingCondition(
                condition_id=f"COND-{uuid.uuid4().hex[:8].upper()}",
                condition_type=cond_type,
                severity=ConditionSeverity.REQUIRED,  # Default to REQUIRED
                category="underwriting",  # Default category
                description=description,  # Use the string as-is
                reason="Underwriter review",  # Default reason
                due_date=(datetime.now() + timedelta(days=7)).date(),
                created_date=datetime.now()
            )
            new_conditions.append(condition)
            loan_file.current_conditions.append(condition)

            result.append(f"\n✓ Condition: {condition.condition_id}")
            result.append(f"  Type: {condition.condition_type.value.upper()}")
            result.append(f"  Severity: {condition.severity.value}")
            result.append(f"  Category: {condition.category}")
            result.append(f"  Description: {condition.description}")
            result.append(f"  Reason: {condition.reason}")
            result.append(f"  Due Date: {condition.due_date}")

        result.append(f"\n{'=' * 60}")
        result.append(f"Total Conditions Issued: {len(new_conditions)}")

        decision = UnderwritingDecision(
            decision_id=f"DEC-{uuid.uuid4().hex[:8].upper()}",
            decision_date=datetime.now(),
            underwriter_name="underwriter_agent",
            decision_type="approve_with_conditions",
            decision_reason=f"Conditional approval - {len(new_conditions)} conditions issued",
            conditions=new_conditions
        )
        loan_file.underwriting_decisions.append(decision)

        loan_file.update_status(
            LoanStatus.UNDERWRITING_SUSPENDED,
            "underwriter_agent",
            f"Conditional approval - {len(new_conditions)} conditions issued"
        )

        loan_file.underwriter_name = "underwriter_agent"

        file_manager.save_loan_file(loan_file)

        result.append(f"\n✅ Conditions issued and file suspended")
        result.append(f"🔄 File returned to loan processor for condition clearance")

        return "\n".join(result)

async def issue_final_approval(loan_number: str, approval_notes: str = "Automated approval by decision_maker") -> str:
    """Issue Clear to Close - CONCURRENT SAFE. approval_notes optional for tool callers."""

    print(f"    🔧 [TOOL CALLED] issue_final_approval({loan_number})")

    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        result = []
        result.append(f"✅ ISSUING FINAL APPROVAL")
        result.append(f"Loan #{loan_number}")
        result.append("=" * 60)

        pending_conditions = [c for c in loan_file.current_conditions if c.status != "cleared"]

        if pending_conditions:
            result.append(f"\n❌ CANNOT ISSUE APPROVAL - PENDING CONDITIONS:")
            for cond in pending_conditions:
                result.append(f"  - {cond.condition_id}: {cond.description}")
            result.append(f"\n🔔 All conditions must be cleared before final approval")
            return "\n".join(result)

        decision = UnderwritingDecision(
            decision_id=f"DEC-{uuid.uuid4().hex[:8].upper()}",
            decision_date=datetime.now(),
            underwriter_name="underwriter_agent",
            decision_type="approve",
            decision_reason="Final approval - Clear to Close",
            notes=approval_notes
        )
        loan_file.underwriting_decisions.append(decision)

        loan_file.update_status(
            LoanStatus.CLEAR_TO_CLOSE,
            "underwriter_agent",
            "Final approval issued - Clear to Close"
        )

        file_manager.save_loan_file(loan_file)
        print(f"    [WRITE-COUNT] FINAL APPROVAL loan={loan_number} writes={file_manager.get_write_count(loan_number)}")

        result.append(f"\n🎉 CLEAR TO CLOSE")
        result.append(f"Decision ID: {decision.decision_id}")
        result.append(f"Underwriter: {decision.underwriter_name}")
        result.append(f"Date: {decision.decision_date.strftime('%Y-%m-%d %H:%M:%S')}")
        result.append(f"\nNotes: {approval_notes}")
        result.append(f"\n✅ Loan approved and ready for closing")
        result.append(f"🔄 File sent to closing department")

    return "\n".join(result)


async def deny_loan(loan_number: str, denial_reason: str) -> str:
    """Deny loan application - CONCURRENT SAFE"""

    async with file_manager.acquire_loan_lock(loan_number):
        loan_file = file_manager.load_loan_file(loan_number)
        if not loan_file:
            return f"❌ ERROR: Loan file {loan_number} not found"

        result = []
        result.append(f"❌ LOAN DENIAL")
        result.append(f"Loan #{loan_number}")
        result.append("=" * 60)

        decision = UnderwritingDecision(
            decision_id=f"DEC-{uuid.uuid4().hex[:8].upper()}",
            decision_date=datetime.now(),
            underwriter_name="underwriter_agent",
            decision_type="deny",
            decision_reason=denial_reason
        )
        loan_file.underwriting_decisions.append(decision)

        loan_file.update_status(
            LoanStatus.DENIED,
            "underwriter_agent",
            f"Loan denied: {denial_reason}"
        )

        file_manager.save_loan_file(loan_file)

        result.append(f"\nDecision ID: {decision.decision_id}")
        result.append(f"Underwriter: {decision.underwriter_name}")
        result.append(f"Date: {decision.decision_date.strftime('%Y-%m-%d %H:%M:%S')}")
        result.append(f"\nDenial Reason:")
        result.append(f"{denial_reason}")
        result.append(f"\n❌ Loan application denied")
        result.append(f"📧 Adverse action notice will be sent to borrower")

    return "\n".join(result)
