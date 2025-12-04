# LLM-Specific Features Analysis

## Question: What LLM Features Are We Actually Using?

Beyond basic function calling (which any programming language can do), what unique **Large Language Model capabilities** does this mortgage underwriting system leverage?

---

## TL;DR Summary

### ✅ **LLM Features Actually Used:**
1. **Natural Language Understanding** - Parsing unstructured task descriptions
2. **Parameter Extraction** - Extracting loan numbers from conversational text
3. **Tool Selection Logic** - Choosing between multiple tools (decision_maker)
4. **Instruction Following** - Following complex system message instructions
5. **Text Summarization** - Creating concise summaries of tool results
6. **Contextual Awareness** - Maintaining conversation context across turns

### ❌ **LLM Features NOT Used (But Could Be):**
1. ❌ **Reasoning Over Unstructured Data** - All analysis is hardcoded Python logic
2. ❌ **Dynamic Planning** - Workflow is fixed, not LLM-planned
3. ❌ **Creative Problem Solving** - No adaptive responses to edge cases
4. ❌ **Complex Decision Making** - Decisions are rule-based, not LLM-reasoned
5. ❌ **Multi-Step Reasoning** - No chain-of-thought or step-by-step analysis
6. ❌ **Learning from Examples** - No few-shot prompting or in-context learning

---

## Deep Dive Analysis

### 1. Natural Language Understanding (NLU)

**What the LLM Does:**
```python
# Task message sent by orchestrator:
task_message = "Task for loan LN-ABC123: Get rate quote from Wells Fargo"

# LLM must understand:
# - This is a task assignment
# - The loan number is "LN-ABC123"
# - The action is "Get rate quote from Wells Fargo"
# - It should call query_lender_wellsfargo()
```

**Could Traditional Code Do This?**
```python
# Traditional approach would require:
import re

loan_number = re.search(r'LN-[A-Z0-9]+', task_message).group()
# ✅ Yes, regex can extract loan number

if "Wells Fargo" in task_message and "rate quote" in task_message:
    query_lender_wellsfargo(loan_number)
# ✅ Yes, keyword matching works
```

**Verdict:** ⚠️ **Marginally useful** - Could be replaced with regex/keyword matching, but LLM is more robust to variations in phrasing.

**LLM Value:** Handles variations like:
- "Get rate quote from Wells Fargo for LN-ABC123"
- "Query Wells Fargo about loan LN-ABC123 rates"
- "LN-ABC123 needs a Wells Fargo rate quote"

All these variations work without changing code.

---

### 2. Parameter Extraction

**What the LLM Does:**
```python
# System message:
"Extract the loan_number from the task and call the tool immediately."

# Input variations the LLM handles:
"Process loan LN-ABC123"           → Extracts: "LN-ABC123"
"Loan number is LN-ABC123"         → Extracts: "LN-ABC123"
"Task for loan LN-ABC123: ..."     → Extracts: "LN-ABC123"
"LN-ABC123 needs processing"       → Extracts: "LN-ABC123"
```

**Could Traditional Code Do This?**
```python
# Regex-based extraction:
import re
match = re.search(r'LN-[A-Z0-9]{6}', text)
loan_number = match.group() if match else None
# ✅ Yes, but fragile to format changes
```

**Verdict:** ✅ **Genuinely Useful** - LLM is more robust to variations and doesn't break if format changes slightly.

**LLM Value:**
- Handles typos: "Loan LN ABC123" (missing dash)
- Handles variations: "loan number: LN-ABC123" vs "LN-ABC123 loan"
- Adapts to new formats without code changes

---

### 3. Tool Selection (Decision Making)

**What the LLM Does:**
```python
# Decision Maker system message:
"""
When you receive a task:
1. Extract loan_number from the task message
2. Analyze all reviews in the loan file
3. Make a decision by calling ONE tool:
   - All acceptable → issue_final_approval(loan_number)
   - Minor issues → issue_underwriting_conditions(loan_number, conditions)
   - Unacceptable → deny_loan(loan_number, reasons)
4. Report the decision clearly
"""

# LLM must:
# - Read tool results containing 5 underwriting reviews
# - Understand if reviews are "acceptable", "needs_conditions", or "unacceptable"
# - Choose the appropriate decision tool
```

**Example Decision Logic:**
```
Tool Results Available to LLM:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Review 1 (Credit):   status="acceptable" ✅
Review 2 (Income):   status="acceptable" ✅
Review 3 (Assets):   status="needs_conditions" ⚠️
                     finding="Large deposit unexplained - $50K"
Review 4 (Property): status="acceptable" ✅
Review 5 (AUS):      decision="Approve/Eligible" ✅

LLM Reasoning:
"Most reviews acceptable, but assets needs clarification.
 One condition needed: explain large deposit.
 Should call: issue_underwriting_conditions()"

LLM Tool Call:
issue_underwriting_conditions(
    loan_number="LN-ABC123",
    conditions=["Provide Letter of Explanation for $50K deposit"]
)
```

**Could Traditional Code Do This?**
```python
# Rule-based approach:
def decide(reviews):
    if all(r.status == "acceptable" for r in reviews):
        return "approve"
    elif any(r.status == "unacceptable" for r in reviews):
        return "deny"
    else:
        return "conditions"

# ✅ Yes, simple rule matching works
```

**Verdict:** ⚠️ **Currently Underutilized** - The decision logic COULD be complex LLM reasoning, but in your current implementation:
- Review statuses are pre-computed in Python tools
- LLM just pattern-matches "acceptable" vs "unacceptable"
- No deep reasoning about WHY something is acceptable

**Potential LLM Value (Not Currently Used):**
```python
# What LLM COULD do (but doesn't currently):
"""
Review the following credit report and make a lending decision:
- Credit Score: 650 (borderline)
- Payment History: 2 late payments in last 24 months (30 days late)
- Credit Utilization: 45% (high)
- Derogatory Marks: 1 collection account ($500, medical, 18 months ago)
- Recent Inquiries: 4 in last 6 months (car shopping)

Question: Is this acceptable credit for a conventional mortgage?
Consider: Medical collection may be excusable, recent inquiries may be
legitimate car shopping, but high utilization and late payments are concerning.

Your decision:
"""

# LLM could reason through nuances that rule-based code cannot
```

---

### 4. Instruction Following

**What the LLM Does:**
```python
# System message for broker:
"""
You are a Mortgage Broker specializing in Wells Fargo.

CRITICAL: You MUST call the query_lender_wellsfargo tool.
Extract the loan_number from the task and call the tool immediately.

When you receive a task:
1. Extract loan_number from the task message
2. Call query_lender_wellsfargo(loan_number)
3. Report the result concisely

Be concise and focused.
"""

# LLM follows multi-step instructions in order
```

**Could Traditional Code Do This?**
```python
# Function-based approach:
def mortgage_broker_workflow(task):
    loan_number = extract_loan_number(task)
    result = query_lender_wellsfargo(loan_number)
    return create_concise_report(result)

# ✅ Yes, procedural code follows steps exactly
```

**Verdict:** ❌ **Not Particularly Useful** - Following a fixed sequence of steps is what traditional code does best. LLM adds overhead without benefit here.

**Where Instruction Following WOULD Be Useful:**
```python
# Complex, conditional instructions:
"""
You are a senior underwriter reviewing a complex scenario.

1. First, review the credit report for any derogatory marks
   - If bankrupty/foreclosure found → immediate denial
   - If late payments → assess severity (30-day vs 90-day)

2. Then, review income stability
   - If self-employed → require 2 years tax returns
   - If W-2 employed → verify 2 years same employer
   - If recent job change → assess if same field

3. Make a preliminary decision:
   - If both credit and income strong → approve
   - If one concern → issue conditions
   - If multiple concerns → suspend for manual review
   - If major red flags → deny

4. Draft a memo explaining your reasoning to the loan officer
"""

# This requires conditional logic, context awareness, and judgment
# LLM excels at this; rule-based code becomes unwieldy
```

**Your Current System:** Linear steps, no conditionals → LLM overkill

---

### 5. Text Summarization

**What the LLM Does:**
```python
# Tool returns detailed structured report:
tool_result = """
💳 MANUAL CREDIT REVIEW
Loan #LN-ABC123
============================================================

📊 CREDIT SCORE ANALYSIS:
  Score: 750
  ✅ EXCELLENT - Very Low Risk

📋 TRADELINE ANALYSIS:
  Total Accounts: 15
  Active Accounts: 12
  Closed Accounts: 3

🔍 PAYMENT HISTORY:
  On-time payments: 100%
  Late payments (30 days): 0
  Late payments (60 days): 0
  Late payments (90+ days): 0

✅ RECOMMENDATION: ACCEPTABLE
"""

# LLM's job: Summarize this for user
# LLM output: "Credit review completed. Score: 750 (Excellent).
#              100% on-time payments. Status: Acceptable."
```

**Could Traditional Code Do This?**
```python
# Template-based summarization:
summary = f"Credit review completed. Score: {score} ({rating}). " \
          f"{on_time_pct}% on-time payments. Status: {status}."
# ✅ Yes, template works perfectly
```

**Verdict:** ❌ **Overkill** - The tool already returns formatted text. LLM just passes it through or reformats it slightly. Template engine would be faster and cheaper.

**Where Summarization WOULD Be Valuable:**
```python
# Unstructured input needing intelligent summary:
appraisal_narrative = """
Subject property is a 2,400 sq ft single family residence built in 1985.
The property is located in a stable, middle-class neighborhood with good
schools and amenities. Comparable sales in the area range from $380K to $420K.
The subject property has been well maintained with recent updates to the
kitchen (2021) and bathrooms (2019). However, the roof is original (1985)
and will need replacement within 2-3 years. HVAC system is 8 years old,
functioning properly. Foundation shows minor settling cracks, typical for
the area, but no structural concerns. The property appraised at $400K,
which is well supported by recent sales. Neighborhood is experiencing
moderate appreciation of 3-4% annually.
"""

# LLM Summary:
"Property appraised at $400K, supported by comps. Well-maintained with
recent updates. Roof needs replacement soon (original 1985). No major
concerns. Stable neighborhood with moderate appreciation."

# This requires understanding what's important vs. trivial → LLM excels
```

**Your Current System:** Tools already format output nicely → LLM just passes through

---

### 6. Contextual Awareness (Multi-Turn Conversation)

**What the LLM Does:**
```python
# Turn 1:
Orchestrator: "Task for loan LN-ABC123: Review credit profile"
Agent: [calls review_credit_profile()] → receives detailed report
Agent: "Credit review complete. Score: 750, Excellent credit."

# Turn 2 (if MaxMessageTermination > 1):
Agent: [LLM has context of previous turn]
Agent: [May call tool again or provide additional analysis]
```

**Could Traditional Code Do This?**
```python
# Stateful conversation:
class Agent:
    def __init__(self):
        self.conversation_history = []

    def process(self, message):
        self.conversation_history.append(message)
        # Access previous messages
        context = self.conversation_history[-3:]  # Last 3 messages
        # ✅ Yes, manual state management works
```

**Verdict:** ⚠️ **Currently Causing Problems** - Your logs show agents calling tools 4x because of multi-turn conversations. The LLM keeps the conversation going when it should stop.

**Where Multi-Turn WOULD Be Useful:**
```python
# Interactive clarification:
User: "Review the Johnson loan"
Agent: "I found 3 loans for Johnson. Which one?
        - LN-001: John Johnson, $300K purchase
        - LN-002: Sarah Johnson, $500K refi
        - LN-003: Mike Johnson, $250K purchase"
User: "The purchase in Austin"
Agent: "That's LN-001 (John Johnson, Austin property). Reviewing now..."

# LLM maintains context and resolves ambiguity
```

**Your Current System:** Single-task execution, no ambiguity → multi-turn is causing issues

---

## What's Missing: Advanced LLM Features NOT Used

### 1. ❌ Chain-of-Thought Reasoning

**What It Is:**
```python
# Ask LLM to show its reasoning step-by-step:
prompt = """
Analyze this loan application and explain your reasoning:

Borrower: Jane Smith
Credit Score: 680 (GOOD but not excellent)
Income: $85,000/year (stable W-2)
DTI: 42% (close to 43% maximum)
LTV: 95% (high, only 5% down)
Reserves: 1 month (low, guideline is 2 months)
Property: $400K condo in downtown area

Think step-by-step:
1. What are the strengths of this application?
2. What are the weaknesses?
3. What are the compensating factors?
4. What's your recommendation?
"""

# LLM Response:
"""
Let me analyze this step-by-step:

1. Strengths:
   - Credit score 680 is above conventional minimum (620)
   - Income is stable W-2 employment
   - Property is in a desirable downtown location

2. Weaknesses:
   - DTI at 42% is very close to the 43% maximum (only 1% cushion)
   - LTV at 95% means only 5% down payment (high risk)
   - Reserves at 1 month is below the 2-month guideline

3. Compensating Factors:
   - Credit score is good, showing responsible financial management
   - W-2 employment is more stable than self-employment
   - Downtown location may have strong appreciation potential

4. Recommendation:
   I recommend CONDITIONAL APPROVAL with the following conditions:
   - Require additional reserves (bring to 2 months minimum)
   - Consider mortgage insurance given high LTV
   - Verify employment is secure (letter from employer)

   The borderline DTI combined with high LTV and low reserves creates
   cumulative risk, but with additional reserves, this could be acceptable.
"""
```

**Value:** Deep analytical reasoning that balances multiple factors

**Your Current System:** All analysis is boolean (acceptable/not acceptable), no nuanced reasoning

---

### 2. ❌ Dynamic Planning

**What It Is:**
```python
# LLM plans its own workflow based on situation:
prompt = """
You're processing a loan application with the following situation:
- Borrower recently changed jobs (3 months ago)
- Previous employment: 5 years as software engineer
- New employment: Still software engineer, but different company
- Income increased from $80K to $95K

What steps do you need to take to verify this employment situation?
List your plan:
"""

# LLM Response:
"""
Given the recent job change, here's my verification plan:

1. Verify previous employment (5 years):
   - Contact previous employer to confirm dates and income
   - Confirm job title was software engineer

2. Verify new employment (3 months):
   - Contact current employer to confirm start date
   - Verify current income of $95K
   - Obtain letter stating employment is permanent (not contract)

3. Assess job continuity:
   - Confirm both positions are in same field (software engineering)
   - Verify income progression is reasonable ($80K → $95K)
   - Check if job change was voluntary (career advancement vs. termination)

4. Calculate income:
   - Since new job is < 2 years, may need to use lower income ($80K)
   - If employer letter confirms permanent role and income is stable,
     may be able to use $95K with underwriter approval

5. Document everything:
   - VOE from both employers
   - Offer letter from new employer
   - Letter of Explanation from borrower about job change

I'll execute steps 1-5 in order and report back.
"""
```

**Value:** Adaptive workflow based on specific situation, not one-size-fits-all

**Your Current System:** Fixed workflow (Phase 0 → 1 → 2 → 3), no adaptation

---

### 3. ❌ Few-Shot Learning (In-Context Learning)

**What It Is:**
```python
# Teach LLM by example:
prompt = """
Review the following credit scenarios and make a recommendation.

Example 1:
Credit Score: 750
Late Payments: None
Collections: None
Recommendation: APPROVE - Excellent credit

Example 2:
Credit Score: 620
Late Payments: 2 (30-day, medical bills)
Collections: 1 ($500 medical, paid)
Recommendation: APPROVE WITH CONDITIONS - Obtain Letter of Explanation
for late payments and collection. Medical issues are often excusable.

Example 3:
Credit Score: 590
Late Payments: 5 (including 90-day late)
Collections: 3 (total $5,000, unpaid)
Recommendation: DENY - Below minimum credit score, pattern of late
payments, significant unpaid collections indicate high risk.

Now review this scenario:
Credit Score: 640
Late Payments: 1 (60-day late, 2 years ago)
Collections: 1 ($300 medical, paid 1 year ago)

Your recommendation:
"""

# LLM learns the pattern and applies to new scenario
```

**Value:** Teach by example instead of rigid rules, adapts to organization's standards

**Your Current System:** No examples, just hardcoded thresholds

---

### 4. ❌ Handling Ambiguity & Edge Cases

**What It Is:**
```python
# LLM handles scenarios not explicitly programmed:
scenario = """
Borrower's income sources:
- W-2 salary: $60,000/year (steady)
- Rental income from investment property: $18,000/year
- Side business (Etsy shop): $12,000/year (sporadic)

Question: How should we calculate qualifying income?

Traditional Rule-Based Code:
if income_type == "W-2":
    qualifying_income = w2_income
elif income_type == "self_employed":
    qualifying_income = avg_tax_returns_2_years
else:
    raise ValueError("Unknown income type")

# Fails! This scenario has MULTIPLE income types

LLM Reasoning:
"W-2 income of $60K is straightforward - fully qualifying.
Rental income of $18K requires verification of lease agreements and
property expenses. Typically use 75% of gross rents after expenses.
Etsy side business at $12K is sporadic - would need 2 years tax returns
showing consistent income to qualify. If only 1 year or inconsistent,
exclude it from qualifying income.

Recommended qualifying income calculation:
- W-2: $60,000 (100%)
- Rental: $18,000 × 75% = $13,500 (after expense factor)
- Etsy: $0 (insufficient history)
Total: $73,500 annually / 12 = $6,125 monthly qualifying income"
```

**Value:** Handles novel situations without explicit programming

**Your Current System:** Handles only predefined scenarios, no edge case reasoning

---

### 5. ❌ Natural Language Explanation

**What It Is:**
```python
# Generate human-readable explanations of complex decisions:
llm_explanation = """
Why was this loan denied?

This loan application was denied for the following reasons:

1. Insufficient Income (Primary Factor)
   Your debt-to-income ratio of 55% exceeds our maximum guideline of 43%.
   This means 55% of your monthly income goes to debt payments, leaving
   insufficient funds for your mortgage payment and living expenses.

   Your monthly income: $5,000
   Your monthly debts: $2,750
   Proposed mortgage payment: $1,850
   Total obligations: $4,600 (92% of income)

2. Credit Concerns (Secondary Factor)
   Your credit score of 590 is below our minimum requirement of 620 for
   conventional financing. Additionally, you have:
   - 3 collections totaling $3,500
   - 2 late payments in the last 12 months

3. Limited Reserves
   You have $500 in savings after down payment and closing costs.
   Our guidelines require 2 months of mortgage payments in reserve
   ($3,700), which you do not meet.

What you can do:
- Pay down debt to improve your DTI
- Work on improving credit score (pay collections, build on-time history)
- Save additional reserves
- Consider a co-borrower with income

We can revisit your application in 6-12 months after addressing these items.
"""

# vs. Code-Generated Message:
code_msg = """
Loan denied.
Reasons:
- DTI: 55% > 43%
- Credit: 590 < 620
- Reserves: $500 < $3,700 required
"""
```

**Value:** Human-friendly, empathetic communication with actionable advice

**Your Current System:** Tool results are formatted text, but not explanatory or actionable

---

## Current System Analysis

### What You're Actually Using LLMs For:

| Feature | Usage in Your System | Could Be Replaced By | Worth Using LLM? |
|---------|---------------------|---------------------|------------------|
| **Natural Language Understanding** | Parsing "Task for loan LN-XXX: ..." | Regex + keywords | ⚠️ Marginal |
| **Parameter Extraction** | Extracting loan_number from text | Regex | ✅ Yes (robustness) |
| **Tool Selection** | Choosing approve/conditions/deny | If-else rules | ⚠️ Underutilized |
| **Instruction Following** | Following step-by-step prompts | Procedural code | ❌ Overkill |
| **Text Summarization** | Reformatting tool output | Templates | ❌ Overkill |
| **Multi-Turn Context** | Conversation memory | State variables | ❌ Causing problems |

### What You're NOT Using (But Could Be Valuable):

| Feature | Potential Use Case | Value |
|---------|-------------------|-------|
| **Chain-of-Thought Reasoning** | Analyze complex loan scenarios with multiple risk factors | 🔥 High |
| **Dynamic Planning** | Adapt workflow based on loan complexity | 🔥 High |
| **Few-Shot Learning** | Learn from examples instead of hardcoded rules | 🔥 High |
| **Ambiguity Resolution** | Handle edge cases not explicitly programmed | 🔥 High |
| **Natural Explanations** | Generate borrower-friendly denial/condition letters | 🔥 High |
| **Document Analysis** | Read and understand PDFs (bank statements, tax returns) | 🔥 Very High |
| **Anomaly Detection** | Find suspicious patterns in financials | 🔥 Very High |

---

## Honest Assessment

### Current State: "LLM as Fancy Router"

Your system is essentially using GPT-4o-mini as a **smart router** that:
1. Parses natural language task descriptions
2. Extracts parameters
3. Calls the appropriate function
4. Returns results

**This is 95% traditional code** with a thin LLM wrapper for flexibility.

### Why This Might Be Intentional (Good Reasons):

✅ **Regulatory Compliance**: Mortgage lending is heavily regulated. Having deterministic, auditable Python logic is safer than opaque LLM decisions.

✅ **Reliability**: Rule-based code never hallucinates. LLM might say "credit score 750" when it's actually 650.

✅ **Speed**: Python is faster than LLM inference (milliseconds vs seconds).

✅ **Cost**: Function calls are free; LLM tokens cost money.

✅ **Debuggability**: Easy to trace why a decision was made with code; hard with LLM reasoning.

### Where You're Missing LLM Value:

❌ **No Deep Reasoning**: All analysis is boolean (pass/fail), no nuanced judgment

❌ **No Adaptability**: Can't handle scenarios outside predefined rules

❌ **No Learning**: System doesn't improve from examples or feedback

❌ **No Natural Communication**: Could generate much better borrower communications

❌ **No Document Understanding**: Could analyze actual PDFs instead of structured data

---

## Recommendations: How to Add Real LLM Value

### 1. Document Analysis (Huge Opportunity)

**Current:** Structured JSON data only
**Better:** Analyze actual documents

```python
async def analyze_bank_statement_pdf(loan_number: str, pdf_path: str) -> str:
    """LLM analyzes actual bank statement PDF"""

    # Extract text from PDF
    pdf_text = extract_pdf_text(pdf_path)

    # LLM prompt:
    prompt = f"""
    Analyze this bank statement for mortgage lending purposes:

    {pdf_text}

    Extract and verify:
    1. Account holder name - does it match borrower?
    2. Statement period (should be last 60 days)
    3. Ending balance
    4. Average daily balance over the period
    5. Any large deposits over $1,000 (need sourcing)
    6. Any NSFs, overdrafts, or red flags
    7. Sufficient funds for down payment and reserves?

    Format as structured report.
    """

    llm_analysis = await llm.analyze(prompt)
    return llm_analysis

# VALUE: Replaces manual document review, saves hours of human time
```

### 2. Intelligent Decision Making (High Value)

**Current:** Binary rules
**Better:** Contextual judgment

```python
async def make_lending_decision(loan_number: str) -> str:
    """LLM makes nuanced lending decision"""

    loan_file = file_manager.load_loan_file(loan_number)

    prompt = f"""
    You are a senior underwriter with 20 years experience.

    Review this complete loan file and make a lending decision:

    BORROWER PROFILE:
    Credit Score: {loan_file.credit_score}
    Payment History: {loan_file.payment_history}
    DTI: {loan_file.dti}%
    LTV: {loan_file.ltv}%
    Reserves: {loan_file.reserves} months
    Employment: {loan_file.employment_history}

    GUIDELINES:
    - Minimum credit score: 620
    - Maximum DTI: 43%
    - Maximum LTV: 95%
    - Minimum reserves: 2 months

    However, use your judgment:
    - Strong compensating factors may offset one weakness
    - Multiple weaknesses require extra scrutiny
    - Consider the full picture, not just individual metrics

    Your decision (Approve, Approve with Conditions, or Deny):
    Reasoning (explain why, considering all factors):
    Conditions (if conditional approval):
    """

    llm_decision = await llm.analyze(prompt)
    return llm_decision

# VALUE: Handles complex scenarios that rigid rules cannot
```

### 3. Exception Handling (Medium Value)

**Current:** Errors break workflow
**Better:** LLM handles unusual situations

```python
async def handle_unusual_income(loan_number: str, income_docs: dict) -> str:
    """LLM analyzes non-standard income scenarios"""

    prompt = f"""
    This borrower has unusual income sources:

    {json.dumps(income_docs, indent=2)}

    Determine:
    1. How to calculate qualifying income
    2. What additional documentation is needed
    3. Any concerns or red flags
    4. Recommendation for underwriter

    Use Fannie Mae guidelines for non-traditional income.
    """

    llm_analysis = await llm.analyze(prompt)
    return llm_analysis

# VALUE: Adapts to edge cases without programming every scenario
```

### 4. Borrower Communication (High Value)

**Current:** Generic messages
**Better:** Personalized explanations

```python
async def generate_denial_letter(loan_number: str) -> str:
    """LLM creates empathetic, actionable denial letter"""

    loan_file = file_manager.load_loan_file(loan_number)
    denial_reasons = loan_file.denial_reasons

    prompt = f"""
    Write a denial letter for this mortgage application:

    Borrower: {loan_file.borrower_name}
    Denial Reasons: {denial_reasons}

    Requirements:
    - Professional but empathetic tone
    - Explain each reason clearly in plain language
    - Provide specific, actionable steps to improve
    - Encourage them to reapply after addressing issues
    - Include fair lending disclaimer

    Write the letter:
    """

    letter = await llm.generate(prompt)
    return letter

# VALUE: Better customer experience, reduces compliance risk
```

---

## Conclusion

### What You're Currently Doing:
**Using LLMs as a flexible interface layer** for routing and parameter extraction.

**Value:** 2/10 - Could mostly be replaced by regex + if-else

**Cost:** Significant (LLM inference on every task)

### What You COULD Be Doing:
**Using LLMs for actual intelligence** in:
- Document analysis (reading PDFs)
- Nuanced decision-making (balancing multiple factors)
- Exception handling (edge cases)
- Natural communication (explanatory letters)
- Anomaly detection (finding suspicious patterns)

**Value:** 9/10 - Truly leverages unique LLM capabilities

**Cost:** Similar (same number of LLM calls, but doing real work)

### Recommendation:

**Keep your current architecture** (clean separation of concerns, auditability) but **add LLM value** where it matters:

1. ✅ **Keep Python logic for**:
   - Rule enforcement (DTI thresholds, credit minimums)
   - Workflow orchestration (Phase 0 → 1 → 2 → 3)
   - File management (locking, persistence)
   - Calculations (DTI, LTV, reserves)

2. ✅ **Use LLM intelligence for**:
   - Reading actual documents (PDFs, images)
   - Complex judgment calls (weighing compensating factors)
   - Edge case handling (unusual income sources)
   - Natural language communication (letters, explanations)
   - Pattern recognition (fraud detection, anomalies)

This would make your system **truly intelligent** instead of just **flexibly procedural**.
