"""
Simulated external system integrations with realistic responses and exceptions
"""

import random
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
import time

from models import (
    CreditBureauResponse, CreditReport, CreditTradeline, CreditInquiry,
    AutomatedUnderwritingResponse, FloodCertificationResponse,
    ExternalSystemResponse, LoanFile, Document, DocumentType, DocumentStatus
)


# ============== EXCEPTION CLASSES ==============

class ExternalSystemException(Exception):
    """Base exception for external system errors"""
    pass


class SystemTimeoutException(ExternalSystemException):
    """System timeout"""
    pass


class SystemMaintenanceException(ExternalSystemException):
    """System under maintenance"""
    pass


class InvalidDataException(ExternalSystemException):
    """Invalid request data"""
    pass


class InsufficientCreditHistoryException(ExternalSystemException):
    """Insufficient credit history"""
    pass


# ============== CREDIT BUREAU SIMULATOR ==============

class CreditBureauSimulator:
    """Simulates Experian/Equifax/TransUnion credit bureau APIs"""

    @staticmethod
    def pull_credit_report(
            borrower_ssn: str,
            borrower_name: str,
            pull_type: str = "hard"
    ) -> CreditBureauResponse:
        """
        Simulate credit bureau pull

        Exceptions:
        - 5% chance of timeout
        - 2% chance of maintenance window
        - 1% chance of insufficient credit history
        """

        # Simulate network delay
        time.sleep(random.uniform(0.5, 2.0))

        # Random exceptions
        rand = random.random()
        if rand < 0.05:
            raise SystemTimeoutException("Credit bureau timeout - please retry")
        elif rand < 0.07:
            raise SystemMaintenanceException("Credit bureau under maintenance (2AM-4AM EST)")
        elif rand < 0.08:
            raise InsufficientCreditHistoryException("Borrower has insufficient credit history")

        # Generate simulated credit report
        credit_score = random.randint(580, 820)

        # Generate tradelines
        tradelines = []
        num_tradelines = random.randint(3, 12)

        for i in range(num_tradelines):
            account_type = random.choice([
                "mortgage", "auto", "credit_card", "student_loan", "personal_loan"
            ])
            tradelines.append(CreditTradeline(
                account_type=account_type,
                creditor_name=f"{account_type.title()} Creditor {i + 1}",
                account_number=f"****{random.randint(1000, 9999)}",
                balance=Decimal(str(random.randint(0, 50000))),
                monthly_payment=Decimal(str(random.randint(50, 1500))),
                payment_status="current" if random.random() > 0.1 else "30_days_late",
                opened_date=date.today() - timedelta(days=random.randint(365, 3650)),
                closed_date=None if random.random() > 0.3 else date.today() - timedelta(days=random.randint(1, 365))
            ))

        # Generate inquiries (potential red flag if too many)
        inquiries = []
        num_inquiries = random.randint(0, 5)
        for i in range(num_inquiries):
            inquiry_date = date.today() - timedelta(days=random.randint(1, 180))
            inquiries.append(CreditInquiry(
                creditor_name=f"Creditor {i + 1}",
                inquiry_date=inquiry_date,
                inquiry_type="hard" if random.random() > 0.3 else "soft",
                explanation_required=num_inquiries > 3  # Red flag if > 3 inquiries
            ))

        # Calculate total monthly debt
        total_monthly_debt = sum(t.monthly_payment for t in tradelines if t.closed_date is None)

        # Generate derogatory items based on credit score
        derogatory_items = []
        if credit_score < 620:
            derogatory_items = random.sample([
                "Collection account - Medical $2,500",
                "30-day late payment in last 12 months",
                "60-day late payment 18 months ago"
            ], k=random.randint(1, 2))

        credit_report = CreditReport(
            report_id=f"CR-{random.randint(100000, 999999)}",
            report_date=datetime.now(),
            bureau="TriMerge",
            credit_score=credit_score,
            tradelines=tradelines,
            inquiries=inquiries,
            derogatory_items=derogatory_items,
            public_records=[],
            total_monthly_debt=total_monthly_debt
        )

        return CreditBureauResponse(
            success=True,
            system_name="CreditBureau",
            transaction_id=f"TXN-{random.randint(100000, 999999)}",
            credit_report=credit_report,
            pull_type=pull_type,
            response_data={
                "bureau": "TriMerge",
                "score": credit_score,
                "tradeline_count": len(tradelines)
            }
        )


# ============== AUTOMATED UNDERWRITING SIMULATOR ==============

class AutomatedUnderwritingSimulator:
    """Simulates Fannie Mae DU / Freddie Mac LPA"""

    @staticmethod
    def run_automated_underwriting(loan_file: LoanFile) -> AutomatedUnderwritingResponse:
        """
        Simulate automated underwriting system (DU/LP)

        Exceptions:
        - 3% chance of timeout
        - High DTI (>50%) results in "Refer"
        - Low credit score (<620) results in "Caution"
        """

        # Simulate processing delay
        time.sleep(random.uniform(1.0, 3.0))

        # Random timeout
        if random.random() < 0.03:
            raise SystemTimeoutException("Automated underwriting system timeout")

        metrics = loan_file.financial_metrics
        credit_score = (loan_file.borrowers[0].credit_report.credit_score
                        if loan_file.borrowers and loan_file.borrowers[0].credit_report
                        else 700)

        # Determine recommendation
        if metrics.dti_ratio and metrics.dti_ratio > 50:
            recommendation = "refer"
        elif credit_score < 620:
            recommendation = "caution"
        elif metrics.ltv_ratio and metrics.ltv_ratio > 95:
            recommendation = "refer"
        elif credit_score >= 740 and metrics.dti_ratio and metrics.dti_ratio <= 43:
            recommendation = "approve"
        else:
            recommendation = random.choice(["approve", "approve", "refer"])

        # Generate findings
        findings = []
        required_docs = []

        if metrics.dti_ratio and metrics.dti_ratio > 43:
            findings.append(f"DTI ratio {metrics.dti_ratio}% exceeds guidelines")
            required_docs.append("VOE - Verify stable employment")

        if metrics.ltv_ratio and metrics.ltv_ratio > 80:
            findings.append(f"LTV ratio {metrics.ltv_ratio}% requires PMI")
            required_docs.append("PMI certificate")

        if credit_score < 680:
            findings.append(f"Credit score {credit_score} below preferred threshold")
            required_docs.append("LOE - Explain credit inquiries")

        # Calculate LLPA (Loan Level Price Adjustment)
        llpa = Decimal("0")
        if credit_score < 700:
            llpa += Decimal("0.5")
        if metrics.ltv_ratio and metrics.ltv_ratio > 80:
            llpa += Decimal("0.25")

        # Determine reserves required
        reserves_required = 2  # months
        if metrics.dti_ratio and metrics.dti_ratio > 45:
            reserves_required = 6
        elif loan_file.property_info.occupancy_type.value == "investment":
            reserves_required = 6

        return AutomatedUnderwritingResponse(
            success=True,
            system_name="AutomatedUnderwriting_DU",
            transaction_id=f"AU-{random.randint(100000, 999999)}",
            recommendation=recommendation,
            findings=findings,
            required_documents=required_docs,
            loan_level_price_adjustment=llpa,
            reserves_required=reserves_required,
            response_data={
                "system": "Desktop Underwriter",
                "version": "11.0",
                "casefile_id": f"CF{random.randint(1000000, 9999999)}"
            }
        )


# ============== FLOOD CERTIFICATION SIMULATOR ==============

class FloodCertificationSimulator:
    """Simulates flood certification service"""

    # High-risk zip codes (simulated)
    HIGH_RISK_ZONES = {
        "33139": "Miami Beach, FL",
        "70117": "New Orleans, LA",
        "77551": "Galveston, TX",
        "08260": "Wildwood, NJ",
        "23451": "Virginia Beach, VA"
    }

    @staticmethod
    def check_flood_zone(property_address: str, zip_code: str) -> FloodCertificationResponse:
        """
        Simulate flood certification check

        Exceptions:
        - 2% chance of timeout
        - Certain zip codes are high-risk
        - Climate change risk assessment included
        """

        time.sleep(random.uniform(0.3, 1.0))

        # Random timeout
        if random.random() < 0.02:
            raise SystemTimeoutException("Flood certification service timeout")

        # Check if in high-risk zone
        in_flood_zone = zip_code in FloodCertificationSimulator.HIGH_RISK_ZONES

        # Assign flood zone designation
        if in_flood_zone:
            flood_zone = random.choice(["AE", "VE", "A"])  # High risk zones
        else:
            flood_zone = random.choice(["X", "X", "X", "C"])  # Low risk zones

        # Insurance requirement
        flood_insurance_required = flood_zone in ["A", "AE", "VE", "V"]

        # Future climate risk score (1-10, with 10 being highest risk)
        # This simulates 10-year climate change projection
        if in_flood_zone:
            future_risk_score = random.randint(7, 10)
            warnings = [
                f"Property in {FloodCertificationSimulator.HIGH_RISK_ZONES[zip_code]}",
                f"Climate models predict increased flooding risk over next 10 years",
                f"Future risk score: {future_risk_score}/10"
            ]
        else:
            future_risk_score = random.randint(1, 4)
            warnings = []

        # Add warning if future risk is concerning
        if future_risk_score >= 7:
            warnings.append("⚠️ HIGH FUTURE FLOOD RISK - Consider climate change impact")

        return FloodCertificationResponse(
            success=True,
            system_name="FloodCertification",
            transaction_id=f"FLOOD-{random.randint(100000, 999999)}",
            in_flood_zone=in_flood_zone,
            flood_zone_designation=flood_zone,
            community_number=f"{random.randint(100000, 999999)}",
            flood_insurance_required=flood_insurance_required,
            base_flood_elevation=f"{random.randint(5, 25)} ft" if in_flood_zone else None,
            future_risk_score=future_risk_score,
            response_data={
                "fema_panel": f"{random.randint(1000, 9999)}{chr(random.randint(65, 90))}",
                "certification_date": datetime.now().isoformat()
            },
            warnings=warnings
        )


# ============== APPRAISAL MANAGEMENT SIMULATOR ==============

class AppraisalManagementSimulator:
    """Simulates appraisal ordering and management"""

    # @staticmethod
    # async def order_appraisal(loan_number: str,
    #                           property_address: str,
    #                           purchase_price) -> str:
    #     """Order property appraisal - TRUE CONCURRENT SAFE"""
    #
    #     # ========== PHASE 1: Load data (LOCKED) ==========
    #     async with file_manager.acquire_loan_lock(loan_number):
    #         loan_file = file_manager.load_loan_file(loan_number)
    #         if not loan_file:
    #             return f"❌ ERROR: Loan file {loan_number} not found"
    #
    #         # Extract property data
    #         property_data = {
    #             "street": loan_file.property_info.property_address.street,
    #             "city": loan_file.property_info.property_address.city,
    #             "state": loan_file.property_info.property_address.state,
    #             "purchase_price": loan_file.loan_info.purchase_price or Decimal("0"),
    #             "loan_amount": loan_file.loan_info.loan_amount
    #         }
    #     # Lock released
    #
    #     # ========== PHASE 2: External API call (NO LOCK) ==========
    #     result = []
    #     result.append(f"🏠 ORDERING APPRAISAL")
    #     result.append(f"Property: {property_data['street']}")
    #     result.append(f"{property_data['city']}, {property_data['state']}")
    #     result.append("=" * 60)
    #
    #     try:
    #         result.append(f"📡 Contacting Appraisal Management Company...")
    #
    #         appraisal_response = AppraisalManagementSimulator.order_appraisal(
    #             property_address=f"{property_data['street']}, {property_data['city']}",
    #             purchase_price=property_data['purchase_price'],
    #             loan_amount=property_data['loan_amount']
    #         )
    #
    #         result.append(f"✅ Appraisal ordered successfully")
    #         result.append(f"Transaction ID: {appraisal_response.transaction_id}")
    #         result.append(f"Order ID: {appraisal_response.response_data['order_id']}")
    #         result.append(f"Appraisal Fee: ${appraisal_response.response_data['fee']:.2f}")
    #         result.append(f"Estimated Completion: {appraisal_response.response_data['estimated_completion']}")
    #
    #         if appraisal_response.response_data.get('appraiser_assigned'):
    #             result.append(f"✅ Appraiser assigned")
    #         else:
    #             result.append(f"⏳ Appraiser assignment pending")
    #
    #         if appraisal_response.warnings:
    #             result.append(f"\n⚠️  WARNINGS:")
    #             for warning in appraisal_response.warnings:
    #                 result.append(f"  - {warning}")
    #
    #         # ========== PHASE 3: Update file (LOCKED) ==========
    #         async with file_manager.acquire_loan_lock(loan_number):
    #             loan_file = file_manager.load_loan_file(loan_number)
    #             if not loan_file:
    #                 return f"❌ ERROR: Loan file {loan_number} not found"
    #
    #             from models import Appraisal
    #             loan_file.appraisal = Appraisal(
    #                 appraisal_id=appraisal_response.response_data['order_id'],
    #                 ordered_date=datetime.now(),
    #                 status="ordered"
    #             )
    #
    #             appraisal_doc = Document(
    #                 document_id=f"DOC-{uuid.uuid4().hex[:8].upper()}",
    #                 document_type=DocumentType.APPRAISAL,
    #                 status=DocumentStatus.REQUESTED,
    #                 metadata={
    #                     "order_id": appraisal_response.response_data['order_id'],
    #                     "estimated_completion": appraisal_response.response_data['estimated_completion']
    #                 }
    #             )
    #             loan_file.documents.append(appraisal_doc)
    #
    #             loan_file.update_status(
    #                 LoanStatus.APPRAISAL_ORDERED,
    #                 "loan_processor",
    #                 f"Appraisal ordered - Order ID: {appraisal_response.response_data['order_id']}"
    #             )
    #
    #             file_manager.save_loan_file(loan_file)
    #             result.append(f"\n✅ Appraisal record added to loan file")
    #
    #     except ExternalSystemException as e:
    #         result.append(f"\n❌ ERROR: {str(e)}")
    #         result.append(f"🔔 ACTION: Follow up with AMC or consider alternative appraiser")
    #
    #         async with file_manager.acquire_loan_lock(loan_number):
    #             loan_file = file_manager.load_loan_file(loan_number)
    #             if loan_file:
    #                 loan_file.add_audit_entry(
    #                     actor="loan_processor",
    #                     action="appraisal_order_failed",
    #                     details=str(e)
    #                 )
    #                 file_manager.save_loan_file(loan_file)
    #
    #     return "\n".join(result)@staticmethod
    #

    @staticmethod
    def order_appraisal(loan_number: str,  # ← Accept parameters
                        property_address: str,
                        purchase_price) -> ExternalSystemResponse:
        """
        Simulate ordering an appraisal from AMC
        Returns simulated response - NO file operations!
        """
        # Simulate delay
        import time
        time.sleep(random.uniform(1.0, 2.0))

        # Generate fake data
        order_id = f"APR-{random.randint(100000, 999999)}"
        transaction_id = f"TXN-{random.randint(100000, 999999)}"

        response_data = {
            'order_id': order_id,
            'loan_number': loan_number,  # ← USE the parameters
            'property_address': property_address,  # ← USE the parameters
            'purchase_price': float(purchase_price),  # ← USE the parameters
            'fee': 500.00,
            'estimated_completion': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'appraiser_assigned': random.choice([True, False])
        }

        # Return simulated response
        return ExternalSystemResponse(
            success=True,
            system_name="Employment Verification Service",
            transaction_id=transaction_id,
            response_data=response_data,
            warnings=[]
        )


    @staticmethod
    def complete_appraisal(
            purchase_price: Decimal,
            property_condition: str = "average"
    ) -> Dict:
        """
        Simulate completed appraisal

        Returns appraisal that may come in below purchase price
        """

        # 15% chance appraisal comes in low
        if random.random() < 0.15:
            # 5-10% below purchase price
            appraised_value = purchase_price * Decimal(str(random.uniform(0.90, 0.95)))
            issues = ["Appraised value below purchase price - renegotiation required"]
        else:
            # At or slightly above purchase price
            appraised_value = purchase_price * Decimal(str(random.uniform(0.98, 1.02)))
            issues = []

        # Add condition-based issues
        if property_condition == "fair" or property_condition == "poor":
            issues.append("Property requires repairs")
            repairs_required = [
                "Roof repair - estimated $5,000",
                "HVAC system replacement - estimated $8,000"
            ]
            estimated_repair_cost = Decimal("13000")
        else:
            repairs_required = []
            estimated_repair_cost = Decimal("0")

        # Generate comparable sales
        comparable_sales = []
        for i in range(3):
            comp_price = float(purchase_price) * random.uniform(0.95, 1.05)
            comparable_sales.append({
                "address": f"{random.randint(100, 999)} Comparable St #{i + 1}",
                "sale_price": round(comp_price, 2),
                "sale_date": (date.today() - timedelta(days=random.randint(30, 180))).isoformat(),
                "proximity": f"{random.uniform(0.1, 2.0):.1f} miles"
            })

        return {
            "appraised_value": float(appraised_value),
            "as_is_value": float(appraised_value),
            "condition": property_condition,
            "comparable_sales": comparable_sales,
            "issues": issues,
            "repairs_required": repairs_required,
            "estimated_repair_cost": float(estimated_repair_cost),
            "status": "completed"
        }


# ============== TITLE COMPANY SIMULATOR ==============

class TitleCompanySimulator:
    """Simulates title search and reports"""

    @staticmethod
    def order_title_search(property_address: str) -> ExternalSystemResponse:
        """Order title search"""

        time.sleep(random.uniform(0.5, 1.0))

        # 2% chance of delay
        warnings = []
        if random.random() < 0.02:
            warnings.append("Complex ownership history - search may take 5-7 business days")

        return ExternalSystemResponse(
            success=True,
            system_name="TitleCompany",
            transaction_id=f"TITLE-{random.randint(100000, 999999)}",
            response_data={
                "order_id": f"TS-{random.randint(100000, 999999)}",
                "estimated_completion": (datetime.now() + timedelta(days=random.randint(3, 7))).date().isoformat()
            },
            warnings=warnings
        )

    @staticmethod
    def complete_title_search() -> Dict:
        """
        Simulate completed title search

        5% chance of title issues
        """

        # 5% chance of liens or exceptions
        if random.random() < 0.05:
            is_clear = False
            liens = [random.choice([
                "Unpaid property tax lien - $3,500",
                "Mechanic's lien from contractor - $8,000",
                "HOA lien for unpaid fees - $1,200"
            ])]
            exceptions = ["Easement for utility access"]
        else:
            is_clear = True
            liens = []
            exceptions = ["Standard exceptions apply"]

        return {
            "vesting": "John and Mary Doe, as Joint Tenants",
            "liens": liens,
            "exceptions": exceptions,
            "is_clear": is_clear
        }


# ============== IRS TRANSCRIPT SIMULATOR ==============

class IRSTranscriptSimulator:
    """Simulates IRS 4506-T tax transcript service"""

    @staticmethod
    def request_tax_transcript(
            borrower_ssn: str,
            tax_years: List[int]
    ) -> ExternalSystemResponse:
        """
        Request IRS tax transcript

        Exceptions:
        - 10% chance of IRS processing delay
        - 2% chance of transcript not found
        """

        time.sleep(random.uniform(1.0, 2.0))

        rand = random.random()
        if rand < 0.10:
            raise SystemTimeoutException("IRS system delay - transcripts may take 10 business days")
        elif rand < 0.12:
            raise InvalidDataException("Tax transcript not found - verify SSN and tax years filed")

        # Simulate transcript data
        transcripts = []
        for year in tax_years:
            transcripts.append({
                "tax_year": year,
                "agi": float(random.randint(50000, 150000)),
                "wages": float(random.randint(50000, 140000)),
                "filing_status": random.choice(["Single", "Married Filing Jointly"]),
                "dependents": random.randint(0, 3)
            })

        return ExternalSystemResponse(
            success=True,
            system_name="IRS_4506T",
            transaction_id=f"IRS-{random.randint(100000, 999999)}",
            response_data={
                "transcripts": transcripts,
                "verification_date": datetime.now().isoformat()
            }
        )


# ============== EMPLOYMENT VERIFICATION SIMULATOR ==============

class EmploymentVerificationSimulator:
    """Simulates employment verification service"""

    @staticmethod
    def verify_employment(employer_name: str,
                          employee_name: str,
                          reported_income) -> ExternalSystemResponse:
        """
        Simulate employment verification
        NO file operations - just return fake data
        """

        # Simulate processing delay
        time.sleep(random.uniform(1.0, 3.0))

        # Generate fake response
        transaction_id = f"VOE-{random.randint(100000, 999999)}"

        # Simulate verification with slight income variance
        verified_income = float(reported_income) * random.uniform(0.95, 1.05)

        response_data = {
            'employer_name': employer_name,
            'employee_name': employee_name,
            'employment_status': 'active',
            'hire_date': (datetime.now() - timedelta(days=random.randint(365, 2000))).strftime('%Y-%m-%d'),
            'employment_type': random.choice(['full_time', 'part_time', 'contract']),
            'reported_income': float(reported_income),
            'verified_income': round(verified_income, 2),
            'position': 'Employee'
        }

        # Add warnings if income variance is significant
        warnings = []
        if abs(verified_income - float(reported_income)) > float(reported_income) * 0.1:
            warnings.append(
                f"Income variance detected: Reported ${reported_income:.2f}, Verified ${verified_income:.2f}")

        return ExternalSystemResponse(
            success=True,
            system_name="AppraisalManagementCompany",
            transaction_id=transaction_id,
            response_data=response_data,
            warnings=warnings
        )