"""
Comprehensive test scenarios with various edge cases and exceptions
"""

from datetime import date, timedelta
from decimal import Decimal
from models import (
    LoanFile, LoanInfo, LoanStatus, Borrower, Employment, Income, Asset,
    PropertyInfo, PropertyType, OccupancyType, Address, EmploymentType,
    FinancialMetrics
)
from file_manager import LoanFileManager
import uuid

file_manager = LoanFileManager()


def create_scenario_clean_approval() -> str:
    """
    Scenario 1: Clean approval - everything perfect

    Borrower profile:
    - Credit score: 750
    - DTI: 35%
    - LTV: 75%
    - Reserves: 6 months
    - Stable employment: 5 years

    Expected outcome: Clear to Close with no conditions
    """

    loan_number = f"LN-{uuid.uuid4().hex[:6].upper()}"

    borrower = Borrower(
        borrower_id="B001",
        first_name="John",
        last_name="Smith",
        ssn="123-45-6789",
        date_of_birth=date(1985, 5, 15),
        email="john.smith@email.com",
        phone="555-0100",
        current_address=Address(
            street="123 Main Street",
            city="Springfield",
            state="IL",
            zip_code="62701",
            country="USA"
        ),
        employment=[
            Employment(
                employer_name="Tech Corp",
                employer_phone="555-0200",
                employment_type=EmploymentType.W2_SALARY,
                job_title="Software Engineer",
                start_date=date(2019, 1, 1),
                is_current=True,
                monthly_income=Decimal("8500"),
                years_in_profession=5.0
            )
        ],
        income=[
            Income(
                income_type="base_salary",
                monthly_amount=Decimal("8500"),
                is_stable=True
            )
        ],
        assets=[
            Asset(
                asset_type="checking",
                institution_name="First National Bank",
                account_number="****1234",
                balance=Decimal("25000"),
                statement_date=date.today() - timedelta(days=5),
                verified=False
            ),
            Asset(
                asset_type="savings",
                institution_name="First National Bank",
                account_number="****5678",
                balance=Decimal("50000"),
                statement_date=date.today() - timedelta(days=5),
                verified=False
            ),
            Asset(
                asset_type="401k",
                institution_name="Fidelity",
                account_number="****9012",
                balance=Decimal("120000"),
                statement_date=date.today() - timedelta(days=30),
                verified=False
            )
        ],
        is_first_time_homebuyer=False,
        marital_status="married"
    )

    property_info = PropertyInfo(
        property_address=Address(
            street="456 Oak Avenue",
            city="Springfield",
            state="IL",
            zip_code="62702",
            country="USA"
        ),
        property_type=PropertyType.SINGLE_FAMILY,
        occupancy_type=OccupancyType.PRIMARY_RESIDENCE,
        year_built=2015,
        square_footage=2200,
        number_of_units=1,
        hoa=False
    )

    loan_info = LoanInfo(
        loan_number=loan_number,
        loan_amount=Decimal("320000"),
        purchase_price=Decimal("400000"),
        down_payment=Decimal("80000"),
        interest_rate=Decimal("6.5"),
        loan_term_months=360,
        loan_type="conventional",
        loan_purpose="purchase",
        lender_name="Premium Lender",
        loan_officer="Jane Doe",
        application_date=date.today()
    )

    loan_file = LoanFile(
        loan_info=loan_info,
        status=LoanStatus.APPLICATION_RECEIVED,
        borrowers=[borrower],
        property_info=property_info,
        financial_metrics=FinancialMetrics()
    )

    file_manager.save_loan_file(loan_file)

    return f"""
📋 SCENARIO 1: CLEAN APPROVAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Loan Number: {loan_number}
Borrower: John Smith
Property: 456 Oak Avenue, Springfield, IL

Profile:
- Expected Credit Score: 750 (Excellent)
- Purchase Price: $400,000
- Loan Amount: $320,000 (80% LTV)
- Down Payment: $80,000 (20%)
- Monthly Income: $8,500
- Estimated DTI: ~35%
- Liquid Assets: $75,000 (6+ months reserves)
- Employment: 5 years stable

Expected Outcome: ✅ Clear to Close (no conditions)

This scenario should demonstrate the HAPPY PATH with full concurrent task execution.
"""


def create_scenario_conditional_approval() -> str:
    """
    Scenario 2: Conditional approval - some issues to resolve

    Issues:
    - High DTI (47%)
    - Multiple credit inquiries
    - Recent job change (4 months ago)
    - Lower reserves

    Expected outcome: Approve with conditions (VOE, LOE, additional reserves)
    """

    loan_number = f"LN-{uuid.uuid4().hex[:6].upper()}"

    borrower = Borrower(
        borrower_id="B002",
        first_name="Sarah",
        last_name="Johnson",
        ssn="987-65-4321",
        date_of_birth=date(1990, 8, 22),
        email="sarah.j@email.com",
        phone="555-0300",
        current_address=Address(
            street="789 Pine Street",
            city="Portland",
            state="OR",
            zip_code="97201",
            country="USA"
        ),
        employment=[
            Employment(
                employer_name="New Company LLC",
                employer_phone="555-0400",
                employment_type=EmploymentType.W2_SALARY,
                job_title="Marketing Manager",
                start_date=date.today() - timedelta(days=120),  # 4 months ago
                is_current=True,
                monthly_income=Decimal("6500"),
                years_in_profession=3.0
            ),
            Employment(
                employer_name="Old Company Inc",
                employment_type=EmploymentType.W2_SALARY,
                job_title="Marketing Specialist",
                start_date=date(2020, 1, 1),
                end_date=date.today() - timedelta(days=125),
                is_current=False,
                monthly_income=Decimal("5500"),
                years_in_profession=3.0
            )
        ],
        income=[
            Income(
                income_type="base_salary",
                monthly_amount=Decimal("6500"),
                is_stable=True
            )
        ],
        assets=[
            Asset(
                asset_type="checking",
                institution_name="Metro Bank",
                account_number="****2468",
                balance=Decimal("8000"),
                statement_date=date.today() - timedelta(days=3),
                verified=False
            ),
            Asset(
                asset_type="savings",
                institution_name="Metro Bank",
                account_number="****1357",
                balance=Decimal("15000"),
                statement_date=date.today() - timedelta(days=3),
                verified=False
            )
        ],
        is_first_time_homebuyer=True,
        marital_status="single"
    )

    property_info = PropertyInfo(
        property_address=Address(
            street="321 Birch Lane",
            city="Portland",
            state="OR",
            zip_code="97202",
            country="USA"
        ),
        property_type=PropertyType.CONDO,
        occupancy_type=OccupancyType.PRIMARY_RESIDENCE,
        year_built=2018,
        square_footage=1400,
        number_of_units=1,
        hoa=True,
        hoa_fees=Decimal("250")
    )

    loan_info = LoanInfo(
        loan_number=loan_number,
        loan_amount=Decimal("280000"),
        purchase_price=Decimal("320000"),
        down_payment=Decimal("40000"),
        interest_rate=Decimal("6.75"),
        loan_term_months=360,
        loan_type="conventional",
        loan_purpose="purchase",
        lender_name="Premium Lender",
        loan_officer="Jane Doe",
        application_date=date.today()
    )

    loan_file = LoanFile(
        loan_info=loan_info,
        status=LoanStatus.APPLICATION_RECEIVED,
        borrowers=[borrower],
        property_info=property_info,
        financial_metrics=FinancialMetrics()
    )

    file_manager.save_loan_file(loan_file)

    return f"""
📋 SCENARIO 2: CONDITIONAL APPROVAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Loan Number: {loan_number}
Borrower: Sarah Johnson
Property: 321 Birch Lane, Portland, OR

Profile:
- Expected Credit Score: 680-720 (Good)
- Purchase Price: $320,000
- Loan Amount: $280,000 (87.5% LTV - PMI required)
- Down Payment: $40,000 (12.5%)
- Monthly Income: $6,500
- Estimated DTI: ~47% (HIGH)
- Liquid Assets: $23,000 (~3 months reserves)
- Employment: Recent job change (4 months ago)
- First-time homebuyer
- HOA: $250/month

Issues:
⚠️  High DTI (47% - above 43% guideline)
⚠️  Recent employment change (VOE needed)
⚠️  Lower reserves for high DTI
⚠️  Expected multiple credit inquiries
⚠️  LTV >80% (PMI required)

Expected Outcome: ⚠️  Approve with Conditions
- VOE (verify employment stability)
- LOE (explain job change and credit inquiries)
- Proof of additional reserves OR pay down debt

This scenario tests CONDITION ISSUANCE and CLEARANCE workflow.
"""


def create_scenario_appraisal_low() -> str:
    """
    Scenario 3: Appraisal comes in low

    Issue: Appraisal $20k below purchase price

    Expected outcome: Conditional approval with value issue to resolve
    """

    loan_number = f"LN-{uuid.uuid4().hex[:6].upper()}"

    borrower = Borrower(
        borrower_id="B003",
        first_name="Michael",
        last_name="Chen",
        ssn="111-22-3333",
        date_of_birth=date(1982, 3, 10),
        email="m.chen@email.com",
        phone="555-0500",
        current_address=Address(
            street="555 Maple Drive",
            city="Austin",
            state="TX",
            zip_code="78701",
            country="USA"
        ),
        employment=[
            Employment(
                employer_name="Austin Tech Solutions",
                employer_phone="555-0600",
                employment_type=EmploymentType.W2_SALARY,
                job_title="Senior Developer",
                start_date=date(2017, 6, 1),
                is_current=True,
                monthly_income=Decimal("9500"),
                years_in_profession=7.0
            )
        ],
        income=[
            Income(
                income_type="base_salary",
                monthly_amount=Decimal("9500"),
                is_stable=True
            )
        ],
        assets=[
            Asset(
                asset_type="checking",
                institution_name="Texas Bank",
                account_number="****3698",
                balance=Decimal("30000"),
                statement_date=date.today() - timedelta(days=7),
                verified=False
            ),
            Asset(
                asset_type="savings",
                institution_name="Texas Bank",
                account_number="****7412",
                balance=Decimal("60000"),
                statement_date=date.today() - timedelta(days=7),
                verified=False
            )
        ],
        marital_status="married"
    )

    property_info = PropertyInfo(
        property_address=Address(
            street="888 Downtown Plaza",
            city="Austin",
            state="TX",
            zip_code="78702",
            country="USA"
        ),
        property_type=PropertyType.CONDO,
        occupancy_type=OccupancyType.PRIMARY_RESIDENCE,
        year_built=2020,
        square_footage=1800,
        number_of_units=1,
        hoa=True,
        hoa_fees=Decimal("300")
    )

    loan_info = LoanInfo(
        loan_number=loan_number,
        loan_amount=Decimal("360000"),
        purchase_price=Decimal("450000"),  # Appraisal will come in at $430k
        down_payment=Decimal("90000"),
        interest_rate=Decimal("6.25"),
        loan_term_months=360,
        loan_type="conventional",
        loan_purpose="purchase",
        lender_name="Premium Lender",
        loan_officer="Jane Doe",
        application_date=date.today()
    )

    loan_file = LoanFile(
        loan_info=loan_info,
        status=LoanStatus.APPLICATION_RECEIVED,
        borrowers=[borrower],
        property_info=property_info,
        financial_metrics=FinancialMetrics()
    )

    file_manager.save_loan_file(loan_file)

    return f"""
📋 SCENARIO 3: LOW APPRAISAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Loan Number: {loan_number}
Borrower: Michael Chen
Property: 888 Downtown Plaza, Austin, TX

Profile:
- Expected Credit Score: 740 (Very Good)
- Purchase Price: $450,000
- EXPECTED Appraisal: ~$430,000 (📉 $20k LOW)
- Loan Amount: $360,000
- Current LTV: 80%
- Revised LTV after appraisal: 83.7%
- Monthly Income: $9,500
- Estimated DTI: ~38%
- Liquid Assets: $90,000 (strong reserves)
- Employment: 7 years stable

Issue:
🚨 Appraisal will come in $20,000 below purchase price

Options to resolve:
1. Borrower increases down payment by $20k
2. Renegotiate purchase price down to $430k
3. Meet in the middle (seller reduces, buyer adds)
4. Request appraisal review/reconsideration

Expected Outcome: ⚠️  Approve with Conditions
- Address appraisal value discrepancy
- Provide resolution before closing

This scenario tests APPRAISAL REVIEW and VALUE DISCREPANCY handling.
"""


def create_scenario_high_risk_denial() -> str:
    """
    Scenario 4: High risk - likely denial

    Issues:
    - Low credit score (585)
    - Very high DTI (55%)
    - Minimal reserves
    - Recent derogatory items

    Expected outcome: Denied
    """

    loan_number = f"LN-{uuid.uuid4().hex[:6].upper()}"

    borrower = Borrower(
        borrower_id="B004",
        first_name="Robert",
        last_name="Williams",
        ssn="444-55-6666",
        date_of_birth=date(1988, 11, 5),
        email="r.williams@email.com",
        phone="555-0700",
        current_address=Address(
            street="999 Elm Street",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            country="USA"
        ),
        employment=[
            Employment(
                employer_name="Retail Store",
                employer_phone="555-0800",
                employment_type=EmploymentType.W2_HOURLY,
                job_title="Store Manager",
                start_date=date(2022, 3, 1),
                is_current=True,
                monthly_income=Decimal("4500"),
                years_in_profession=2.0
            )
        ],
        income=[
            Income(
                income_type="base_salary",
                monthly_amount=Decimal("4500"),
                is_stable=True
            )
        ],
        assets=[
            Asset(
                asset_type="checking",
                institution_name="Local Credit Union",
                account_number="****9876",
                balance=Decimal("2500"),
                statement_date=date.today() - timedelta(days=2),
                verified=False
            ),
            Asset(
                asset_type="savings",
                institution_name="Local Credit Union",
                account_number="****5432",
                balance=Decimal("3000"),
                statement_date=date.today() - timedelta(days=2),
                verified=False
            )
        ],
        is_first_time_homebuyer=True,
        marital_status="single"
    )

    property_info = PropertyInfo(
        property_address=Address(
            street="147 Desert Road",
            city="Phoenix",
            state="AZ",
            zip_code="85002",
            country="USA"
        ),
        property_type=PropertyType.SINGLE_FAMILY,
        occupancy_type=OccupancyType.PRIMARY_RESIDENCE,
        year_built=1995,
        square_footage=1200,
        number_of_units=1,
        hoa=False
    )

    loan_info = LoanInfo(
        loan_number=loan_number,
        loan_amount=Decimal("195000"),
        purchase_price=Decimal("200000"),
        down_payment=Decimal("5000"),
        interest_rate=Decimal("7.5"),
        loan_term_months=360,
        loan_type="FHA",
        loan_purpose="purchase",
        lender_name="Premium Lender",
        loan_officer="Jane Doe",
        application_date=date.today()
    )

    loan_file = LoanFile(
        loan_info=loan_info,
        status=LoanStatus.APPLICATION_RECEIVED,
        borrowers=[borrower],
        property_info=property_info,
        financial_metrics=FinancialMetrics()
    )

    file_manager.save_loan_file(loan_file)

    return f"""
📋 SCENARIO 4: HIGH RISK - LIKELY DENIAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Loan Number: {loan_number}
Borrower: Robert Williams
Property: 147 Desert Road, Phoenix, AZ

Profile:
- Expected Credit Score: 585 (❌ POOR - FHA minimum)
- Purchase Price: $200,000
- Loan Amount: $195,000 (97.5% LTV - FHA)
- Down Payment: $5,000 (2.5% - FHA minimum)
- Monthly Income: $4,500
- Estimated DTI: ~55% (❌ EXCESSIVE)
- Liquid Assets: $5,500 (<1 month reserves)
- Employment: 2 years (marginal)
- First-time homebuyer
- Loan Type: FHA

Critical Issues:
🚨 Credit score at FHA minimum (585)
🚨 Expected derogatory items on credit
🚨 DTI 55% (exceeds 50% maximum)
🚨 Minimal reserves (<1 month)
🚨 High LTV with weak credit
🚨 Limited income for housing payment

Expected Outcome: ❌ DENIED
Reasons:
- DTI exceeds maximum acceptable ratio
- Insufficient compensating factors
- High risk profile
- Reserves inadequate for risk level

This scenario tests DENIAL workflow and ADVERSE ACTION documentation.
"""


def create_scenario_flood_zone_high_risk() -> str:
    """
    Scenario 5: Property in high-risk flood zone

    Issue: Property in flood zone with high climate risk
    Requires flood insurance

    Expected outcome: Conditional approval with flood insurance requirement
    """

    loan_number = f"LN-{uuid.uuid4().hex[:6].upper()}"

    borrower = Borrower(
        borrower_id="B005",
        first_name="Jennifer",
        last_name="Martinez",
        ssn="777-88-9999",
        date_of_birth=date(1986, 7, 18),
        email="j.martinez@email.com",
        phone="555-0900",
        current_address=Address(
            street="222 Bay Street",
            city="Miami Beach",
            state="FL",
            zip_code="33139",  # High-risk flood zone
            country="USA"
        ),
        employment=[
            Employment(
                employer_name="Miami Hospital",
                employer_phone="555-1000",
                employment_type=EmploymentType.W2_SALARY,
                job_title="Nurse Practitioner",
                start_date=date(2018, 1, 15),
                is_current=True,
                monthly_income=Decimal("7800"),
                years_in_profession=6.0
            )
        ],
        income=[
            Income(
                income_type="base_salary",
                monthly_amount=Decimal("7800"),
                is_stable=True
            )
        ],
        assets=[
            Asset(
                asset_type="checking",
                institution_name="Coastal Bank",
                account_number="****1111",
                balance=Decimal("20000"),
                statement_date=date.today() - timedelta(days=4),
                verified=False
            ),
            Asset(
                asset_type="savings",
                institution_name="Coastal Bank",
                account_number="****2222",
                balance=Decimal("45000"),
                statement_date=date.today() - timedelta(days=4),
                verified=False
            )
        ],
        marital_status="single"
    )

    property_info = PropertyInfo(
        property_address=Address(
            street="456 Ocean Drive",
            city="Miami Beach",
            state="FL",
            zip_code="33139",  # High-risk flood zone
            country="USA"
        ),
        property_type=PropertyType.CONDO,
        occupancy_type=OccupancyType.PRIMARY_RESIDENCE,
        year_built=2010,
        square_footage=1600,
        number_of_units=1,
        hoa=True,
        hoa_fees=Decimal("400")
    )

    loan_info = LoanInfo(
        loan_number=loan_number,
        loan_amount=Decimal("340000"),
        purchase_price=Decimal("425000"),
        down_payment=Decimal("85000"),
        interest_rate=Decimal("6.5"),
        loan_term_months=360,
        loan_type="conventional",
        loan_purpose="purchase",
        lender_name="Premium Lender",
        loan_officer="Jane Doe",
        application_date=date.today()
    )

    loan_file = LoanFile(
        loan_info=loan_info,
        status=LoanStatus.APPLICATION_RECEIVED,
        borrowers=[borrower],
        property_info=property_info,
        financial_metrics=FinancialMetrics()
    )

    file_manager.save_loan_file(loan_file)

    return f"""
📋 SCENARIO 5: HIGH-RISK FLOOD ZONE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Loan Number: {loan_number}
Borrower: Jennifer Martinez
Property: 456 Ocean Drive, Miami Beach, FL 33139

Profile:
- Expected Credit Score: 720 (Good)
- Purchase Price: $425,000
- Loan Amount: $340,000 (80% LTV)
- Down Payment: $85,000 (20%)
- Monthly Income: $7,800
- Estimated DTI: ~40%
- Liquid Assets: $65,000 (strong reserves)
- Employment: 6 years stable
- Property: Miami Beach (HIGH FLOOD RISK)

Critical Issue:
🌊 ZIP CODE 33139 - HIGH-RISK FLOOD ZONE
   - FEMA Flood Zone: AE or VE (high risk)
   - Flood insurance: REQUIRED
   - Climate change risk score: 8-10/10
   - Future flooding risk: SIGNIFICANT

Expected Flood Certification Results:
⚠️  Property in Special Flood Hazard Area (SFHA)
⚠️  Flood insurance mandatory
⚠️  High climate change impact over 10 years
⚠️  Annual premium: ~$2,000-$5,000

Expected Outcome: ⚠️  Approve with Conditions
- Flood insurance policy required before closing
- Borrower must acknowledge flood risk
- Higher overall housing payment with flood insurance

This scenario tests FLOOD CERTIFICATION and CLIMATE RISK assessment.
"""


def list_all_scenarios() -> str:
    """List all available scenarios"""

    return """
╔════════════════════════════════════════════════════════════════════╗
║                    AVAILABLE TEST SCENARIOS                         ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  1. CLEAN APPROVAL                                                 ║
║     Perfect borrower, no issues, straight to CTC                   ║
║     Tests: Happy path, concurrent task execution                   ║
║                                                                    ║
║  2. CONDITIONAL APPROVAL                                           ║
║     High DTI, recent job change, needs conditions                  ║
║     Tests: Condition issuance and clearance workflow               ║
║                                                                    ║
║  3. LOW APPRAISAL                                                  ║
║     Appraisal $20k below purchase price                            ║
║     Tests: Appraisal review, value discrepancy handling            ║
║                                                                    ║
║  4. HIGH RISK - DENIAL                                             ║
║     Poor credit (585), excessive DTI (55%), minimal reserves       ║
║     Tests: Denial workflow, adverse action                         ║
║                                                                    ║
║  5. FLOOD ZONE HIGH RISK                                           ║
║     Property in Miami Beach flood zone, climate risk               ║
║     Tests: Flood certification, climate impact assessment          ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
"""

# TODO:tests to get same results
# TODO: diagrams show the flow of each scenario. workflow diagrams. branches and results.
# TODO: what function/code do to demonstrate each scenario.
# TODO: write a document what have done.
# TODO: mongoDB as extra bonus. not priority
# TODO: save requirements