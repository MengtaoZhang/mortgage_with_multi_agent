# Test Suite for Scenario 1 (Clean Approval)

## Setup

1. **Install pytest-asyncio** (already done):
   ```bash
   pip install pytest-asyncio
   ```

2. **Navigate to the correct directory**:
   ```bash
   cd /Users/mengtaozhang/Documents/PycharmProjects/mortgage_with_multi_agent/src/loan_underwriter
   ```

## Running Tests

### Run all tests:
```bash
pytest test/test_scenario_1_assertions.py -v
```

### Run a specific test:
```bash
# Test scenario creation
pytest test/test_scenario_1_assertions.py::TestScenario1Assertions::test_assertion_1_scenario_creation -v

# Test concurrent execution
pytest test/test_scenario_1_assertions.py::TestScenario1Assertions::test_assertion_15_concurrent_execution -v

# Test file integrity
pytest test/test_scenario_1_assertions.py::TestScenario1Assertions::test_assertion_16_file_integrity -v
```

### Run with detailed output:
```bash
pytest test/test_scenario_1_assertions.py -vv -s
```

### Run from PyCharm:
1. Right-click on `test_scenario_1_assertions.py`
2. Select "Run 'pytest in test_scenario_1_assertions.py'"
3. Or click the green play button next to each test method

## Test Summary

| Test | What It Validates |
|------|-------------------|
| `test_assertion_1_scenario_creation` | Loan file created with correct data |
| `test_assertion_2_document_verification` | All documents marked complete |
| `test_assertion_3_credit_report_retrieval` | Credit score 750 retrieved |
| `test_assertion_4_flood_certification` | Zone X (low risk) determined |
| `test_assertion_5_employment_verification` | 5 years employment confirmed |
| `test_assertion_6_financial_ratios` | DTI ≤35%, LTV 80%, Reserves ≥6mo |
| `test_assertion_7_submit_to_underwriting` | Status SUBMITTED_TO_UNDERWRITING |
| `test_assertion_15_concurrent_execution` | Parallel execution verified (~5s not ~15s) |
| `test_assertion_16_file_integrity` | No corruption from concurrent access |

## Troubleshooting

### Error: "async def functions are not natively supported"
**Solution:** Make sure pytest-asyncio is installed:
```bash
pip install pytest-asyncio
```

### Error: "Loan file not created"
**Solution:** Make sure you're running from the correct directory:
```bash
cd /Users/mengtaozhang/Documents/PycharmProjects/mortgage_with_multi_agent/src/loan_underwriter
```

### Error: Import errors
**Solution:** The test file automatically adds the parent directory to the Python path. If you still have import errors, check that you're in the `loan_underwriter` directory.

## What Was Fixed

### Issue 1: Wrong file paths
**Before:**
```python
file_path = Path(f"../loan_files/active/{loan_number}.json")
```

**After:**
```python
file_path = Path(f"./loan_files/active/{loan_number}.json")
```

### Issue 2: Missing pytest-asyncio
**Before:**
```
async def functions are not natively supported
```

**After:**
```bash
pip install pytest-asyncio
```

Added to test file:
```python
pytestmark = pytest.mark.asyncio
```

Added `pytest.ini` configuration:
```ini
[pytest]
asyncio_mode = auto
```

## Expected Output

When all tests pass, you should see:
```
test/test_scenario_1_assertions.py::TestScenario1Assertions::test_assertion_1_scenario_creation PASSED
✅ ASSERTION 1 PASSED: Scenario creation valid
test/test_scenario_1_assertions.py::TestScenario1Assertions::test_assertion_2_document_verification PASSED
✅ ASSERTION 2 PASSED: Document verification complete
test/test_scenario_1_assertions.py::TestScenario1Assertions::test_assertion_3_credit_report_retrieval PASSED
✅ ASSERTION 3 PASSED: Credit report retrieved correctly
test/test_scenario_1_assertions.py::TestScenario1Assertions::test_assertion_4_flood_certification PASSED
✅ ASSERTION 4 PASSED: Flood certification correct
test/test_scenario_1_assertions.py::TestScenario1Assertions::test_assertion_5_employment_verification PASSED
✅ ASSERTION 5 PASSED: Employment verification successful
test/test_scenario_1_assertions.py::TestScenario1Assertions::test_assertion_6_financial_ratios PASSED
✅ ASSERTION 6 PASSED: Financial ratios correct
test/test_scenario_1_assertions.py::TestScenario1Assertions::test_assertion_7_submit_to_underwriting PASSED
✅ ASSERTION 7 PASSED: Submitted to underwriting
test/test_scenario_1_assertions.py::TestScenario1Assertions::test_assertion_15_concurrent_execution PASSED
✅ ASSERTION 15 PASSED: Concurrent execution in 5.2s
test/test_scenario_1_assertions.py::TestScenario1Assertions::test_assertion_16_file_integrity PASSED
✅ ASSERTION 16 PASSED: File integrity maintained

======================== 9 passed in 30.45s =========================
```
