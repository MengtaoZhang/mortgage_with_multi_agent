"""
This file is for initializing the mortgage system.
The initialization part indluding:
1. agent initialization
2. pipeline initialization
3. TODO
"""

import os
import re
from typing import Tuple, Dict, Any
from autogen import ConversableAgent, GroupChat, GroupChatManager, register_function

LLM_config = {
    "config_list": [{
        "model": os.getenv("LLM_MODEL", "gpt-5-mini"),           # 或本地模型名
        "api_key": os.getenv("OPENAI_API_KEY", "dummy"),          # 本地网关可忽略
        "base_url": os.getenv("OPENAI_COMPAT_URL")                # 本地网关地址
    }],
    "timeout": 60,
}

processor = ConversableAgent(
    name="LoanProcessor",
    system_message=(
        "Role: Loan Processor.\n"
        "Goal: Validate & structure borrower docs, produce MISMO 3.x LoanFile, "
        "highlight missing items and risks. Never make approval decisions."
    ),
    llm_config=LLM_config,
)

underwriter = ConversableAgent(
    name="Underwriter",
    system_message=(
        "Role: Underwriter.\n"
        "Goal: Assess risk per policy (DTI/LTV/credit/appraisal/disclosures timeline). "
        "Output: Approve/Cond/Decline with explicit reasons. "
        "Ask for Compliance tool results before finalizing."
    ),
    llm_config=LLM_config,
)

compliance = ConversableAgent(
    name="Compliance",
    system_message=(
        "Role: Compliance & Rules.\n"
        "Given a MISMO LoanFile, check each rule (investor/GSE/MI/internal), "
        "return a table: RuleID | Verdict | EvidenceURI | Rationale."
    ),
    llm_config=LLM_config,
)

tool_runner = ConversableAgent(
    name="ToolRunner",
    llm_config=False, human_input_mode="NEVER"
)

print("Agents initialized.")

BASIC_INFO_TEMPLATE = """\
                        MSG_TYPE: BASIC_INFO
                        LOAN_ID: {loan_id}
                        SENDER: Borrower
                        RECIPIENT: LoanOfficer
                        TIMESTAMP: {ts}
                        CONTENT_TYPE: TEXT
                        
                        ----
                        Name: {name}
                        FICO: {fico}
                        Annual_Income: USD {income}
                        Down_Payment: USD {down}
                        Target_Home_Price: USD {price}
                        State: {state}
                        Occupancy: {occ}
                        Product_Preference: {product}
                        Rate_Lock_Intention: {lock_intent}
                        """

def parse_basic_info(basic_info_str: str) -> Dict[str, Any]:
    """Parse key fields from BASIC_INFO string (very tolerant regex)."""
    def grab(pattern, default=""):
        m = re.search(pattern, basic_info_str, re.I)
        return m.group(1).strip() if m else default

    money = lambda s: float(re.sub(r"[^\d.]", "", s or "0") or 0.0)

    fico = int(grab(r"FICO:\s*([0-9]{3})", "740"))
    income = money(grab(r"Annual_Income:\s*USD\s*([0-9,.\s]+)", "90000"))
    down = money(grab(r"Down_Payment:\s*USD\s*([0-9,.\s]+)", "60000"))
    price = money(grab(r"Target_Home_Price:\s*USD\s*([0-9,.\s]+)", "420000"))
    product = grab(r"Product_Preference:\s*([A-Za-z0-9_]+)", "30Y_Fixed")
    state = grab(r"State:\s*([A-Z]{2})", "KS")
    occ = grab(r"Occupancy:\s*([A-Za-z]+)", "Primary")
    lock_intent = grab(r"Rate_Lock_Intention:\s*([YN])", "Y")
    loan_id = grab(r"LOAN_ID:\s*([^\n]+)", "L-TEST-0001")

    # LTV estimate
    ltv = 0.0
    if price > 0:
        ltv = max(0.0, min(1.0, 1.0 - (down / price)))

    return dict(
        loan_id=loan_id, fico=fico, income=income, down=down, price=price,
        product=product, state=state, occ=occ, lock_intent=lock_intent, ltv=ltv
    )

def build_rate_scenario(basic_info_str: str) -> str:
    """Produce a RATE_QUOTE_REQUEST string (all-text) from BASIC_INFO."""
    d = parse_basic_info(basic_info_str)
    ltv_pct = f"{round(d['ltv']*100, 1)}%"
    scenario = f"""\
                MSG_TYPE: RATE_QUOTE_REQUEST
                LOAN_ID: {d['loan_id']}
                SENDER: LoanOfficer
                RECIPIENT: MortgageBroker
                TIMESTAMP: 2025-10-15T11:20:00Z
                CONTENT_TYPE: TEXT
                
                ----
                Scenario: {d['product']} | LTV {ltv_pct} | FICO {bucket_fico(d['fico'])} | DTI 38-43%
                Points_Budget: 0.000-0.375
                PMI_Preferred: Borrower_Paid
                Lock_Days: 45
                """
    return scenario

def bucket_fico(fico: int) -> str:
    if fico >= 780: return "780+"
    if fico >= 760: return "760-779"
    if fico >= 740: return "740-759"
    if fico >= 720: return "720-739"
    return "660-719"

def monthly_payment(principal: float, annual_rate: float, years: int) -> float:
    """P&I payment; simple finance math."""
    r = annual_rate / 12.0
    n = years * 12
    if r == 0:
        return principal / n
    return principal * (r * (1 + r)**n) / ((1 + r)**n - 1)

def rate_quote_engine(rate_request_str: str, basic_info_str: str) -> str:
    """
    Produce a RATE_QUOTE_RESPONSE string-table (all-text).
    Very simple pricing model driven by FICO & LTV buckets.
    """
    d = parse_basic_info(basic_info_str)
    product_years = 30 if "30" in d["product"] else 15

    # base rate by FICO/LTV buckets (toy model)
    base = 6.50
    if d["fico"] >= 780: base -= 0.20
    elif d["fico"] >= 760: base -= 0.10
    elif d["fico"] <= 699: base += 0.25

    if d["ltv"] > 0.90: base += 0.25
    elif d["ltv"] > 0.80: base += 0.125

    # three “lenders” with tiny deltas
    lenders = [
        ("AcmeBank", base - 0.125, 0.250),
        ("BetaBank", base,          0.000),
        ("CivicCU",  base + 0.050,  0.125),
    ]

    loan_amt = max(0.0, d["price"] - d["down"])
    rows = ["# Lender | Product | Rate | Points | APR | PMI | Lock | Est_Payment"]
    for name, rate, points in lenders:
        apr = rate + 0.10  # toy APR
        pmi = "USD 150/mo" if d["ltv"] > 0.80 else "USD 0/mo"
        pay = monthly_payment(loan_amt, rate/100.0, product_years)
        rows.append(f"{name} | {d['product']} | {rate:.3f}% | {points:.3f} | {apr:.2f}% | {pmi} | 45d | USD {pay:,.0f}")

    return f"""\
MSG_TYPE: RATE_QUOTE_RESPONSE
LOAN_ID: {d['loan_id']}
SENDER: MortgageBroker
RECIPIENT: LoanOfficer
TIMESTAMP: 2025-10-15T11:25:00Z
CONTENT_TYPE: TABLE

----
{chr(10).join(rows)}
"""


def select_intent_plan(rate_quote_response: str, preference: str = "min_payment") -> str:
    """
    Pick one row from the response table and produce an INTENT_PLAN (string).
    preference: "min_payment" | "min_rate" | "zero_points"
    """
    # parse rows
    lines = [ln for ln in rate_quote_response.splitlines() if "|" in ln and not ln.strip().startswith("#")]
    offers = []
    for ln in lines:
        parts = [p.strip() for p in ln.split("|")]
        if len(parts) < 8:  # Lender, Product, Rate, Points, APR, PMI, Lock, Est_Payment
            continue
        lender, product, rate, points, apr, pmi, lock, pay = parts
        rate_v = float(rate.replace("%",""))
        pts_v  = float(points)
        pay_v  = float(re.sub(r"[^\d.]", "", pay))
        offers.append((lender, product, rate_v, pts_v, apr, pmi, lock, pay_v, ln))

    if not offers:
        body = "Selection: NONE\nReason: No valid offers parsed."
    else:
        if preference == "min_rate":
            best = min(offers, key=lambda x: x[2])
        elif preference == "zero_points":
            zero = [o for o in offers if abs(o[3]) < 1e-6]
            best = (min(zero, key=lambda x: x[2]) if zero else min(offers, key=lambda x: x[2]))
        else:
            best = min(offers, key=lambda x: x[7])  # min payment

        lender, product, rate_v, pts_v, apr, pmi, lock, pay_v, raw = best
        body = f"""\
Selection: {lender} | {product}
Target_Rate: {rate_v:.3f}%
Points: {pts_v:.3f}
Lock: {lock}
Est_Payment: USD {pay_v:,.0f}
PMI_Indicative: {pmi}
Offer_Raw: {raw}
"""

    return f"""\
MSG_TYPE: INTENT_PLAN
SENDER: LoanOfficer
RECIPIENT: Borrower
TIMESTAMP: 2025-10-15T11:28:00Z
CONTENT_TYPE: TEXT

----
{body.strip()}
"""

def build_rate_lock_request(intent_plan_str: str, loan_id: str, lock_days: int = 45) -> str:
    """Turn the intent plan into a RATE_LOCK_REQUEST string."""
    lender = re.search(r"Selection:\s*([^\|]+)\|", intent_plan_str)
    product = re.search(r"Selection:\s*[^|]+\|\s*(.*)", intent_plan_str)
    rate = re.search(r"Target_Rate:\s*([\d.]+)%", intent_plan_str)
    points = re.search(r"Points:\s*([-.\d]+)", intent_plan_str)

    lender_v = lender.group(1).strip() if lender else "TBD"
    product_v = product.group(1).strip() if product else "30Y_Fixed"
    rate_v = rate.group(1) if rate else "6.500"
    points_v = points.group(1) if points else "0.000"

    return f"""\
            MSG_TYPE: RATE_LOCK_REQUEST
            LOAN_ID: {loan_id}
            SENDER: LoanOfficer
            RECIPIENT: MortgageBroker
            TIMESTAMP: 2025-10-15T11:30:00Z
            CONTENT_TYPE: TEXT
            
            ----
            Lender: {lender_v}
            Product: {product_v}
            Target_Rate: {rate_v}%
            Points: {points_v}
            Lock_Days: {lock_days}
            """

def build_doc_checklist(basic_info_str: str, product_hint: str = "30Y_Fixed") -> str:
    """
    Create a simple DOC_CHECKLIST (string). No domain files; purely text rules.
    """
    d = parse_basic_info(basic_info_str)
    items = [
        "Photo_ID (front/back)",
        "Income_Proof: recent pay stubs (2), last year's W-2/1099",
        "Bank_Statements: last 2 months",
        "Employment_Verification (VOE) consent",
        "Homeowner_Insurance_quote (optional pre-closing)",
    ]
    if d["ltv"] > 0.80:
        items.append("PMI disclosures & quote")
    if d["income"] < 60000:
        items.append("Letter_of_Explanation (income fluctuations)")

    body = " | ".join(items)
    return f"""\
            MSG_TYPE: DOC_CHECKLIST
            LOAN_ID: {d['loan_id']}
            SENDER: LoanOfficer
            RECIPIENT: Borrower
            TIMESTAMP: 2025-10-15T11:31:00Z
            CONTENT_TYPE: TEXT
            
            ----
            {body}
            """

def select_next(last_speaker, groupchat):
    order = ["LoanOfficer", "MortgageBroker", "LoanOfficer", "Borrower"]
    if last_speaker is None:
        next_name = "LoanOfficer"
    else:
        name = last_speaker.name
        idx = order.index(name) if name in order else -1
        next_name = order[(idx + 1) % len(order)] if idx >= 0 else "LoanOfficer"
    # return selected agent from current groupchat.agents
    return next(a for a in groupchat.agents if a.name == next_name)

if __name__ == '__main__':
    borrower = ConversableAgent(
        name="Borrower",
        system_message=(
            "You are the borrower. Provide basic info only when asked. "
            "Keep answers concise. Do not invent lender offers."
        ),
        llm_config=LLM_config,
    )

    loan_officer = ConversableAgent(
        name="LoanOfficer",
        system_message=(
            "Role: Loan Officer.\n"
            "Goal: From BASIC_INFO, build a RATE_QUOTE_REQUEST (call build_rate_scenario), "
            "send to MortgageBroker, receive RATE_QUOTE_RESPONSE, choose an INTENT_PLAN "
            "(call select_intent_plan), then produce RATE_LOCK_REQUEST and DOC_CHECKLIST. "
            "Output artifacts as plain strings."
        ),
        llm_config=LLM_config,
        is_termination_msg=lambda x: isinstance(x, str) and "ARTIFACTS_COMPLETE" in x
    )

    mortgage_broker = ConversableAgent(
        name="MortgageBroker",
        system_message=(
            "Role: Mortgage Broker.\n"
            "When receiving RATE_QUOTE_REQUEST, call rate_quote_engine to produce "
            "a RATE_QUOTE_RESPONSE (plain text table)."
        ),
        llm_config=LLM_config,
    )

    tool_runner = ConversableAgent(name="ToolRunner", llm_config=False, human_input_mode="NEVER")

    # Register tools: all string-in/string-out
    register_function(build_rate_scenario, caller=loan_officer, executor=tool_runner,
                      name="build_rate_scenario", description="Build RATE_QUOTE_REQUEST string from BASIC_INFO.")
    register_function(rate_quote_engine, caller=mortgage_broker, executor=tool_runner,
                      name="rate_quote_engine", description="Produce RATE_QUOTE_RESPONSE table string.")
    register_function(select_intent_plan, caller=loan_officer, executor=tool_runner,
                      name="select_intent_plan", description="Select an offer; return INTENT_PLAN string.")
    register_function(build_rate_lock_request, caller=loan_officer, executor=tool_runner,
                      name="build_rate_lock_request", description="Create RATE_LOCK_REQUEST string from INTENT_PLAN.")
    register_function(build_doc_checklist, caller=loan_officer, executor=tool_runner,
                      name="build_doc_checklist", description="Create DOC_CHECKLIST string from BASIC_INFO.")

    # Borrower seeds BASIC_INFO (string-only)
    BASIC_INFO = BASIC_INFO_TEMPLATE.format(
        loan_id="L-2025-0001", ts="2025-10-15T11:10:00Z",
        name="Zhang, Mengtao", fico=742, income="98,500", down="60,000", price="420,000",
        state="KS", occ="Primary", product="30Y_Fixed", lock_intent="Y"
    )

    gc = GroupChat(
        agents=[borrower, loan_officer, mortgage_broker],
        messages=[],
        max_round=12,
        speaker_selection_method=lambda last_speaker, groupchat: select_next(last_speaker, groupchat)
    )

    manager = GroupChatManager(groupchat=gc, llm_config=LLM_config)

    # Kick off with BASIC_INFO message from Borrower to LO
    loan_officer.initiate_chat(
        manager,
        message=(
                "I have received the following BASIC_INFO from the Borrower. "
                "1) Call `build_rate_scenario` with it; "
                "2) Send the resulting RATE_QUOTE_REQUEST to MortgageBroker; "
                "3) After receiving RATE_QUOTE_RESPONSE, call `select_intent_plan` (min_payment); "
                "4) Then call `build_rate_lock_request`; "
                "5) Then call `build_doc_checklist`; "
                "6) Finally print 'ARTIFACTS_COMPLETE' and echo the three artifacts.\n\n"
                + BASIC_INFO
        )
    )