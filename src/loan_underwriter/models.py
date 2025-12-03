"""
Pydantic models for mortgage loan underwriting system
"""

from pydantic import BaseModel, Field, validator, ConfigDict
from typing import List, Optional, Dict, Literal, Any
from datetime import datetime, date
from enum import Enum
from decimal import Decimal


# ============== ENUMS ==============

class LoanStatus(str, Enum):
    """Loan processing status"""
    APPLICATION_RECEIVED = "application_received"
    DOCUMENTS_COLLECTING = "documents_collecting"
    DOCUMENTS_COMPLETE = "documents_complete"
    INITIAL_REVIEW_COMPLETE = "initial_review_complete"
    CREDIT_ORDERED = "credit_ordered"
    APPRAISAL_ORDERED = "appraisal_ordered"
    SUBMITTED_TO_UNDERWRITING = "submitted_to_underwriting"
    UNDERWRITING_RECEIVED = "underwriting_received"
    UNDERWRITING_INITIAL_REVIEW = "underwriting_initial_review"
    UNDERWRITING_SUSPENDED = "underwriting_suspended"
    CONDITIONS_PENDING = "conditions_pending"
    CONDITIONS_SUBMITTED = "conditions_submitted"
    CONDITIONS_REVIEW = "conditions_review"
    APPROVED = "approved"
    CLEAR_TO_CLOSE = "clear_to_close"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"


class DocumentType(str, Enum):
    """Document types"""
    URLA = "urla"  # Uniform Residential Loan Application
    PAYSTUB = "paystub"
    W2 = "w2"
    TAX_RETURN = "tax_return"
    BANK_STATEMENT = "bank_statement"
    ASSET_STATEMENT = "asset_statement"
    CREDIT_REPORT = "credit_report"
    APPRAISAL = "appraisal"
    TITLE_REPORT = "title_report"
    EMPLOYMENT_VERIFICATION = "employment_verification"
    LETTER_OF_EXPLANATION = "letter_of_explanation"
    GIFT_LETTER = "gift_letter"
    DIVORCE_DECREE = "divorce_decree"
    BANKRUPTCY_DISCHARGE = "bankruptcy_discharge"
    FLOOD_CERTIFICATION = "flood_certification"
    HOMEOWNERS_INSURANCE = "homeowners_insurance"
    PURCHASE_AGREEMENT = "purchase_agreement"
    LOE = "loe"


class DocumentStatus(str, Enum):
    """Document processing status"""
    REQUIRED = "required"
    REQUESTED = "requested"
    RECEIVED = "received"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    MISSING = "missing"
    EXPIRED = "expired"


class ConditionType(str, Enum):
    """Underwriting condition types"""
    VOE = "voe"  # Verification of Employment
    VOD = "vod"  # Verification of Deposit
    VOM = "vom"  # Verification of Mortgage
    LOE = "loe"  # Letter of Explanation
    VOA = "voa"  # Verification of Assets
    PAYSTUB = "paystub"
    BANK_STATEMENT = "bank_statement"
    TAX_RETURN = "tax_return"
    CREDIT_SUPPLEMENT = "credit_supplement"
    APPRAISAL_UPDATE = "appraisal_update"
    TITLE_UPDATE = "title_update"
    INSURANCE = "insurance"
    RESERVES = "reserves"
    GIFT_DOCUMENTATION = "gift_documentation"
    REPAIR_BID = "repair_bid"
    HOA_DOCS = "hoa_docs"
    OTHER = "other"
    APPRAISAL = "appraisal"


class ConditionSeverity(str, Enum):
    """Condition severity levels"""
    REQUIRED = "required"  # Must be cleared before CTC
    PRIOR_TO_DOCS = "prior_to_docs"  # Before loan documents
    PRIOR_TO_FUNDING = "prior_to_funding"  # Before funding
    POST_CLOSING = "post_closing"  # After closing


class EmploymentType(str, Enum):
    """Employment types"""
    W2_SALARY = "w2_salary"
    W2_HOURLY = "w2_hourly"
    SELF_EMPLOYED = "self_employed"
    COMMISSIONED = "commissioned"
    RETIRED = "retired"
    UNEMPLOYED = "unemployed"
    OTHER = "other"


class PropertyType(str, Enum):
    """Property types"""
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTI_FAMILY = "multi_family"
    MANUFACTURED = "manufactured"
    LAND = "land"


class OccupancyType(str, Enum):
    """Occupancy types"""
    PRIMARY_RESIDENCE = "primary_residence"
    SECOND_HOME = "second_home"
    INVESTMENT = "investment"


# ============== DOCUMENT MODELS ==============

class Document(BaseModel):
    """Document tracking model"""
    model_config = ConfigDict(use_enum_values=True)

    document_id: str = Field(..., description="Unique document identifier")
    document_type: DocumentType
    status: DocumentStatus = DocumentStatus.REQUIRED
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    received_date: Optional[datetime] = None
    reviewed_date: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    expiration_date: Optional[date] = None
    pages: Optional[int] = None
    issues: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============== BORROWER MODELS ==============

class Address(BaseModel):
    """Address model"""
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"


class Employment(BaseModel):
    """Employment information"""
    model_config = ConfigDict(use_enum_values=True)

    employer_name: str
    employer_phone: Optional[str] = None
    employment_type: EmploymentType
    job_title: str
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = True
    monthly_income: Decimal = Field(..., gt=0)
    years_in_profession: Optional[float] = None
    verified: bool = False
    verification_date: Optional[datetime] = None
    verification_method: Optional[str] = None


class Income(BaseModel):
    """Income source"""
    income_type: str  # base, bonus, commission, overtime, rental, etc.
    monthly_amount: Decimal
    is_stable: bool = True
    documentation: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class Asset(BaseModel):
    """Asset/Account information"""
    asset_type: str  # checking, savings, 401k, stocks, etc.
    institution_name: str
    account_number: str
    balance: Decimal
    statement_date: date
    verified: bool = False
    large_deposits: List[Dict] = Field(default_factory=list)
    seasoning_issues: List[str] = Field(default_factory=list)


class CreditInquiry(BaseModel):
    """Credit inquiry"""
    creditor_name: str
    inquiry_date: date
    inquiry_type: str  # hard or soft
    explanation_required: bool = False
    explanation: Optional[str] = None


class CreditTradeline(BaseModel):
    """Credit account tradeline"""
    account_type: str  # mortgage, auto, credit_card, student_loan, etc.
    creditor_name: str
    account_number: str
    balance: Decimal
    monthly_payment: Decimal
    payment_status: str  # current, 30_days_late, etc.
    opened_date: date
    closed_date: Optional[date] = None


class CreditReport(BaseModel):
    """Credit report model"""
    report_id: str
    report_date: datetime
    bureau: str  # Experian, Equifax, TransUnion
    credit_score: int = Field(..., ge=300, le=850)
    tradelines: List[CreditTradeline] = Field(default_factory=list)
    inquiries: List[CreditInquiry] = Field(default_factory=list)
    derogatory_items: List[str] = Field(default_factory=list)
    public_records: List[str] = Field(default_factory=list)
    total_monthly_debt: Decimal = Decimal("0")


class Borrower(BaseModel):
    """Borrower information"""
    borrower_id: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    ssn: str  # Should be encrypted in production
    date_of_birth: date
    email: str
    phone: str
    current_address: Address
    previous_addresses: List[Address] = Field(default_factory=list)
    employment: List[Employment] = Field(default_factory=list)
    income: List[Income] = Field(default_factory=list)
    assets: List[Asset] = Field(default_factory=list)
    credit_report: Optional[CreditReport] = None
    is_first_time_homebuyer: bool = False
    citizenship_status: str = "us_citizen"
    marital_status: str = "single"


# ============== PROPERTY MODELS ==============

class PropertyInfo(BaseModel):
    """Property information"""
    model_config = ConfigDict(use_enum_values=True)

    property_address: Address
    property_type: PropertyType
    occupancy_type: OccupancyType
    year_built: Optional[int] = None
    square_footage: Optional[int] = None
    number_of_units: int = 1
    hoa: bool = False
    hoa_fees: Optional[Decimal] = None
    flood_zone: Optional[str] = None
    flood_insurance_required: bool = False


class Appraisal(BaseModel):
    """Appraisal report"""
    appraisal_id: str
    ordered_date: datetime
    completed_date: Optional[datetime] = None
    appraiser_name: Optional[str] = None
    appraiser_license: Optional[str] = None
    appraised_value: Optional[Decimal] = None
    as_is_value: Optional[Decimal] = None
    condition: Optional[str] = None  # excellent, good, average, fair, poor
    comparable_sales: List[Dict] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    repairs_required: List[str] = Field(default_factory=list)
    estimated_repair_cost: Optional[Decimal] = None
    status: str = "ordered"  # ordered, scheduled, in_progress, completed


class TitleReport(BaseModel):
    """Title report"""
    title_id: str
    ordered_date: datetime
    completed_date: Optional[datetime] = None
    title_company: str
    vesting: Optional[str] = None
    liens: List[str] = Field(default_factory=list)
    exceptions: List[str] = Field(default_factory=list)
    is_clear: bool = False


# ============== LOAN MODELS ==============

class LoanInfo(BaseModel):
    """Loan details"""
    loan_number: str = Field(..., description="Unique loan identifier")
    loan_amount: Decimal = Field(..., gt=0)
    purchase_price: Optional[Decimal] = None
    down_payment: Optional[Decimal] = None
    interest_rate: Optional[Decimal] = None
    loan_term_months: int = 360  # 30 years default
    loan_type: str = "conventional"  # conventional, FHA, VA, USDA
    loan_purpose: str = "purchase"  # purchase, refinance, cash_out
    lender_name: str = "Default Lender"
    loan_officer: str
    application_date: date
    lock_expiration_date: Optional[date] = None


class FinancialMetrics(BaseModel):
    """Calculated financial metrics"""
    ltv_ratio: Optional[Decimal] = None  # Loan to Value
    cltv_ratio: Optional[Decimal] = None  # Combined LTV
    dti_ratio: Optional[Decimal] = None  # Debt to Income
    front_end_ratio: Optional[Decimal] = None  # Housing expense ratio
    monthly_housing_payment: Optional[Decimal] = None
    total_monthly_debt: Optional[Decimal] = None
    monthly_income: Optional[Decimal] = None
    reserves_months: Optional[Decimal] = None
    total_assets: Optional[Decimal] = None
    cash_to_close: Optional[Decimal] = None
    pmi_required: bool = False
    pmi_amount: Optional[Decimal] = None


class UnderwritingCondition(BaseModel):
    """Underwriting condition"""
    model_config = ConfigDict(use_enum_values=True)

    condition_id: str
    condition_type: ConditionType
    severity: ConditionSeverity
    category: str  # employment, assets, credit, property, etc.
    description: str
    reason: str
    due_date: Optional[date] = None
    status: str = "pending"  # pending, in_progress, cleared, waived
    assigned_to: str = "loan_processor"
    created_date: datetime
    cleared_date: Optional[datetime] = None
    clearing_documents: List[str] = Field(default_factory=list)
    clearing_notes: Optional[str] = None


class UnderwritingDecision(BaseModel):
    """Underwriting decision"""
    decision_id: str
    decision_date: datetime
    underwriter_name: str
    decision_type: str  # approve, approve_with_conditions, suspend, deny
    decision_reason: str
    conditions: List[UnderwritingCondition] = Field(default_factory=list)
    notes: Optional[str] = None
    automated_findings: Optional[Dict] = None
    manual_review_notes: Optional[str] = None


class AuditTrail(BaseModel):
    """Audit trail entry"""
    timestamp: datetime
    actor: str  # agent name or system
    action: str
    details: str
    status_before: Optional[str] = None
    status_after: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)


# ============== MAIN LOAN FILE MODEL ==============

class LoanFile(BaseModel):
    """Complete loan file"""
    model_config = ConfigDict(use_enum_values=True)

    # Basic info
    loan_info: LoanInfo
    status: LoanStatus = LoanStatus.APPLICATION_RECEIVED

    # Parties
    borrowers: List[Borrower] = Field(default_factory=list)
    co_borrowers: List[Borrower] = Field(default_factory=list)

    # Property
    property_info: PropertyInfo
    appraisal: Optional[Appraisal] = None
    title_report: Optional[TitleReport] = None

    # Financial
    financial_metrics: FinancialMetrics = Field(default_factory=FinancialMetrics)

    # Documents
    documents: List[Document] = Field(default_factory=list)

    # Underwriting
    underwriting_decisions: List[UnderwritingDecision] = Field(default_factory=list)
    current_conditions: List[UnderwritingCondition] = Field(default_factory=list)

    # Audit
    audit_trail: List[AuditTrail] = Field(default_factory=list)

    # Metadata
    created_date: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    processor_name: Optional[str] = None
    underwriter_name: Optional[str] = None
    notes: Optional[str] = None
    flags: List[str] = Field(default_factory=list)  # red flags, alerts

    def add_audit_entry(self, actor: str, action: str, details: str,
                        status_before: Optional[str] = None,
                        status_after: Optional[str] = None):
        """Add audit trail entry"""
        entry = AuditTrail(
            timestamp=datetime.now(),
            actor=actor,
            action=action,
            details=details,
            status_before=status_before,
            status_after=status_after
        )
        self.audit_trail.append(entry)
        self.last_updated = datetime.now()

    def update_status(self, new_status: LoanStatus, actor: str, reason: str):
        """Update loan status with audit trail"""
        # Handle cases where status is already a raw string because of use_enum_values=True
        old_status = self.status.value if hasattr(self.status, "value") else self.status
        new_status_value = new_status.value if hasattr(new_status, "value") else new_status

        # Store as raw value (consistent with use_enum_values=True)
        self.status = new_status_value
        self.add_audit_entry(
            actor=actor,
            action="status_change",
            details=reason,
            status_before=old_status,
            status_after=new_status_value
        )


# ============== EXTERNAL SYSTEM RESPONSES ==============

class ExternalSystemResponse(BaseModel):
    """Base response from external systems"""
    success: bool
    system_name: str
    transaction_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    response_data: Dict = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class CreditBureauResponse(ExternalSystemResponse):
    """Credit bureau API response"""
    credit_report: Optional[CreditReport] = None
    pull_type: str  # soft, hard, tri_merge


class AutomatedUnderwritingResponse(ExternalSystemResponse):
    """DU/LP/LPA response"""
    recommendation: str  # approve, refer, caution, ineligible
    findings: List[str] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    loan_level_price_adjustment: Optional[Decimal] = None
    reserves_required: Optional[int] = None


class FloodCertificationResponse(ExternalSystemResponse):
    """Flood certification service response"""
    in_flood_zone: bool
    flood_zone_designation: Optional[str] = None
    community_number: Optional[str] = None
    flood_insurance_required: bool
    base_flood_elevation: Optional[str] = None
    future_risk_score: Optional[int] = None  # 1-10, climate change risk
