# Orchestrator Agent Architecture

## Pure Agent Architecture with TRUE Concurrent Execution

This architecture uses a single **OrchestratorAgent** that coordinates all worker agents via `asyncio.gather()` with directed messages.

---

## Quick Start

### Run the Main Application

```bash
cd /Users/mengtaozhang/Documents/PycharmProjects/mortgage_with_multi_agent
PYTHONPATH=/Users/mengtaozhang/Documents/PycharmProjects/mortgage_with_multi_agent python src/loan_underwriter/main_orchestrator.py
```

---

## Testing

To run the quick test:

```bash
cd /Users/mengtaozhang/Documents/PycharmProjects/mortgage_with_multi_agent
PYTHONPATH=/Users/mengtaozhang/Documents/PycharmProjects/mortgage_with_multi_agent python src/loan_underwriter/test_coordinator.py
```

---

## What Makes This Different?

### **Pure Agent Architecture**

```python
# Orchestrator is a proper agent (extends BaseChatAgent)
class OrchestratorAgent(BaseChatAgent):
    async def on_messages(self, messages, cancellation_token):
        # Phase 0: Send messages to ALL 5 brokers concurrently
        broker_results = await asyncio.gather(
            self._send_message_to_agent(mortgage_broker_1, ...),
            self._send_message_to_agent(mortgage_broker_2, ...),
            self._send_message_to_agent(mortgage_broker_3, ...),
            self._send_message_to_agent(mortgage_broker_4, ...),
            self._send_message_to_agent(mortgage_broker_5, ...),
        )
        # All 5 execute AT THE SAME TIME - true parallelism
```

### **Evidence of Parallelism**

Agents complete in **random order**, not sequential:

```
Phase 0 (Brokers):
✓ mortgage_broker_5 completed  (finished first!)
✓ mortgage_broker_1 completed
✓ mortgage_broker_3 completed
✓ mortgage_broker_2 completed
✓ mortgage_broker_4 completed  (finished last)

Phase 1 (Processors):
✓ loan_processor_3 completed   (finished first!)
✓ loan_processor_6 completed
✓ loan_processor_2 completed
✓ loan_processor_1 completed
✓ loan_processor_5 completed
✓ loan_processor_4 completed   (finished last)
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
  - 1 OrchestratorAgent (orchestrator)
  - 5 mortgage brokers (each queries 1 lender)
  - 6 loan processors (each handles 1 task)
  - 5 underwriters (each handles 1 review)
  - 1 decision maker

- **Directed messages**: Orchestrator sends explicit tasks to each worker

- **TRUE concurrent execution**: asyncio.gather() runs agents in parallel

- **No handoffs between workers**: All communication goes through orchestrator

---

## Files

- `agents_with_coordinator.py` - OrchestratorAgent + all worker agents
- `main_orchestrator.py` - Interactive runtime
- `test_coordinator.py` - Quick test script
- `md/ORCHESTRATOR_ARCHITECTURE.md` - Detailed documentation

---

## Key Advantages

✅ **Pure agent architecture** - Orchestrator is a BaseChatAgent, not a function
✅ **TRUE parallelism** - asyncio.gather() runs agents concurrently (not sequential)
✅ **Fast execution** (~10s vs 40s sequential)
✅ **Directed messages** - Orchestrator explicitly assigns tasks
✅ **Clean architecture** (1 agent = 1 task)
✅ **Simple workflow** (4 phases: rate shopping → processing → underwriting → decision)
✅ **No handoffs between workers** - Simpler than peer-to-peer communication

---

## Comparison with Other Architectures

| Aspect | Function-Based | Orchestrator Agent |
|--------|----------------|-------------------|
| **Orchestrator** | Async function | BaseChatAgent (proper agent) |
| **Concurrency** | asyncio.gather() in function | asyncio.gather() in agent |
| **Architecture** | Hybrid (function + agents) | **Pure agents** |
| **Message passing** | Direct function calls | Agent directed messages |
| **Flexibility** | Limited | **More flexible** |
| **Performance** | ~10s | **~10s (same!)** |

---

## Agent Communication Flow

```
User
  │
  ├─> TextMessage("Process loan LN-ABC123")
  │
  ▼
OrchestratorAgent.on_messages()
  │
  ├─> Phase 0: asyncio.gather([5 broker agents])
  │     └─> Directed messages to all brokers
  │     └─> All brokers execute IN PARALLEL
  │     └─> Results returned to orchestrator
  │
  ├─> Phase 1: asyncio.gather([6 processor agents])
  │     └─> Directed messages to all processors
  │     └─> All processors execute IN PARALLEL
  │     └─> Results returned to orchestrator
  │
  ├─> Phase 2: asyncio.gather([5 underwriter agents])
  │     └─> Directed messages to all underwriters
  │     └─> All underwriters execute IN PARALLEL
  │     └─> Results returned to orchestrator
  │
  └─> Phase 3: decision_maker.on_messages()
        └─> Final decision
        └─> Result returned to orchestrator
```

---

## Code Example

```python
# Create orchestrator and process a loan
from agents_with_coordinator import process_loan_with_orchestrator

# Process a loan
results = await process_loan_with_orchestrator("LN-ABC123")

# Orchestrator internally does:
# 1. Creates OrchestratorAgent instance
# 2. Sends initial message to orchestrator
# 3. Orchestrator coordinates all 4 phases
# 4. Returns final results
```

---

## Summary

The **Orchestrator Agent Architecture** provides:

1. ✅ **Pure agent architecture**: Everything is an agent
2. ✅ **TRUE concurrent execution**: asyncio.gather() runs agents in parallel
3. ✅ **Four agent types**: OrchestratorAgent + 3 worker types
4. ✅ **Task-level parallelism**: Multiple agents of same type work on different subtasks
5. ✅ **ONE loan processing**: All agents work on the SAME loan concurrently
6. ✅ **Directed messages**: Orchestrator explicitly assigns tasks
7. ✅ **Fast performance**: ~10s total (4x faster than sequential)
8. ✅ **Clean architecture**: 1 agent = 1 task
9. ✅ **Rate shopping**: Compare rates from multiple lenders concurrently

**Total agents: 17**
- 1 OrchestratorAgent
- 5 mortgage_broker agents
- 6 loan_processor agents
- 5 underwriter agents

**Key advantage: Pure agent architecture with TRUE parallelism via asyncio.gather()!**

---

For detailed documentation, see: `md/ORCHESTRATOR_ARCHITECTURE.md`
