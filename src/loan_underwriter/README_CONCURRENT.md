# Concurrent Multi-Agent Architecture

## TRUE Concurrent Execution with asyncio.gather()

This architecture achieves **actual parallelism** where multiple agents execute simultaneously.

---

## Quick Start

### Option 1: Using the Run Script (Easiest)

```bash
./run_concurrent.sh
```

### Option 2: Using PYTHONPATH

```bash
cd /Users/mengtaozhang/Documents/PycharmProjects/mortgage_with_multi_agent
PYTHONPATH=/Users/mengtaozhang/Documents/PycharmProjects/mortgage_with_multi_agent python src/loan_underwriter/main_concurrent.py
```

---

## Testing

To run the quick test:

```bash
cd /Users/mengtaozhang/Documents/PycharmProjects/mortgage_with_multi_agent
PYTHONPATH=/Users/mengtaozhang/Documents/PycharmProjects/mortgage_with_multi_agent python src/loan_underwriter/test_concurrent.py
```

---

## What Makes This Concurrent?

### **asyncio.gather() = TRUE Parallelism**

```python
# Phase 0: All 5 brokers start AT THE SAME TIME
phase0_results = await asyncio.gather(
    run_agent_task(mortgage_broker_1, ...),
    run_agent_task(mortgage_broker_2, ...),
    run_agent_task(mortgage_broker_3, ...),
    run_agent_task(mortgage_broker_4, ...),
    run_agent_task(mortgage_broker_5, ...),
)

# Phase 1: All 6 processors start AT THE SAME TIME
phase1_results = await asyncio.gather(
    run_agent_task(loan_processor_1, ...),
    run_agent_task(loan_processor_2, ...),
    run_agent_task(loan_processor_3, ...),
    run_agent_task(loan_processor_4, ...),
    run_agent_task(loan_processor_5, ...),
    run_agent_task(loan_processor_6, ...),
)
```

### **Evidence of Parallelism**

Agents complete in **random order**, not sequential:

```
Phase 0:
✓ mortgage_broker_3 completed  (finished first!)
✓ mortgage_broker_1 completed
✓ mortgage_broker_5 completed
✓ mortgage_broker_2 completed
✓ mortgage_broker_4 completed  (finished last)

Phase 1:
✓ loan_processor_6 completed  (finished first!)
✓ loan_processor_3 completed
✓ loan_processor_5 completed
✓ loan_processor_2 completed
✓ loan_processor_1 completed
✓ loan_processor_4 completed  (finished last)
```

If they were sequential, they would ALWAYS complete in order 1→2→3→4→5→6.

---

## Performance

- **Phase 0**: ~2s (all 5 brokers in parallel)
- **Phase 1**: ~5s (all 6 processors in parallel)
- **Phase 2**: ~3s (all 5 underwriters in parallel)
- **Total**: ~10s

Compare to sequential execution: ~40s (4x faster!)

---

## Architecture

- **17 agents total**:
  - 5 mortgage brokers (each queries 1 lender)
  - 6 loan processors (each handles 1 task)
  - 5 underwriters (each handles 1 review)
  - 1 decision maker

- **Direct message assignment**: Each agent gets explicit task instructions

- **TRUE concurrent execution**: asyncio.gather() runs agents in parallel

---

## Files

- `agents_concurrent.py` - Agent definitions + coordinator function
- `main_concurrent.py` - Interactive runtime
- `test_concurrent.py` - Quick test script
- `run_concurrent.sh` - Convenient run script
- `md/CONCURRENT_ARCHITECTURE.md` - Detailed documentation

---

## Key Advantages

✅ TRUE parallelism (not sequential)
✅ Fast execution (~10s vs 40s)
✅ Direct message assignment
✅ Clean architecture (1 agent = 1 task)
✅ Simple workflow (4 phases: rate shopping → processing → underwriting → decision)

---

For detailed documentation, see: `md/CONCURRENT_ARCHITECTURE.md`
