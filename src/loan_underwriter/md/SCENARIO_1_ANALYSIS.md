# Scenario 1: Clean Approval (Happy Path) — Current Architecture

This describes how Scenario 1 runs today using the orchestrator + concurrent agents in `main_orchestrator.py` / `agents_with_coordinator.py`.

## Overview
- Entry: `main_orchestrator.py` menu → `create_scenario_clean_approval()` creates `LoanFile` (status `application_received`) and saves `./loan_files/active/LN-XXXXXX.json`.
- Architecture: 1 orchestrator agent + 5 brokers + 6 processors + 5 underwriters + 1 decision maker.
- Concurrency: each phase runs all agents in parallel via `asyncio.gather`, per-loan locks guard file writes.
- Client: `ToolRequiredOpenAIClient` forces tool execution (`tool_choice="required"`).

## Phase Breakdown (Single Loan)
1) **Rate Shopping (Brokers, concurrent x5)**  
   Tools: `query_lender_*` (Wells Fargo, BofA, Chase, Quicken, US Bank).  
   Output: writes rate quotes to the loan file.

2) **Processing (Processors, concurrent x6)**  
   - `verify_loan_documents`  
   - `order_credit_report` (adds credit_report, status → `credit_ordered`)  
   - `order_appraisal` (creates appraisal record, status → `appraisal_ordered`)  
   - `order_flood_certification`  
   - `verify_employment`  
   - `calculate_loan_ratios` (+ `submit_to_underwriting` in tool set; status may advance)

3) **Underwriting (Underwriters, concurrent x5)**  
   - `review_credit_profile` (requires credit_report)  
   - `review_income_employment`  
   - `review_assets_reserves`  
   - `review_property_appraisal` (requires appraisal)  
   - `run_automated_underwriting` (writes automated findings, updates status → `underwriting_initial_review`)

4) **Final Decision (Decision maker, sequential)**  
   - `issue_final_approval` (default notes provided; status → `clear_to_close`) or conditions/denial tools.

## Control Flow (Code)
- `OrchestratorAgent._execute_concurrent_tasks` builds coroutines and runs `await asyncio.gather(...)`.
- `_send_message_to_agent` uses a cached `RoundRobinGroupChat` per agent (`MaxMessageTermination(5)`) and awaits `team.run(task=...)`. It logs start/finish with timestamps to show overlap.
- File writes go through the singleton `file_manager` with per-loan async locks and write-count logging.

### Control Flow Diagram (High Level)
```
User CLI
   │
   ├─ select Scenario 1
   │
   ├─ create_scenario_clean_approval()
   │       │
   │       └─ save loan_files/active/LN-XXXXXX.json (status=application_received)
   │
   └─ OrchestratorAgent.on_messages()
           │
           ├─ Phase 0 (asyncio.gather) → 5 brokers → rate quotes
           ├─ Phase 1 (asyncio.gather) → 6 processors
           │       ├─ credit, appraisal, flood, employment, docs, ratios
           │       └─ multiple writes via file_manager (per-loan lock)
           ├─ Phase 2 (asyncio.gather) → 5 underwriters
           │       ├─ credit/income/assets/property/AUS reviews
           │       └─ status → underwriting_initial_review
           └─ Phase 3 (sequential) → decision_maker
                   └─ issue_final_approval → status=clear_to_close
```

### Data & Locking Path (Per Tool Call)
```
agent task -> team.run() -> tool call
   -> file_manager.acquire_loan_lock(loan_number) [async lock]
       -> load_loan_file()
       -> mutate loan_file
       -> save_loan_file()  # increments write count, logs [WRITE]
   -> lock released
```

### Agent Topology & Data Flow (Abstract)
```
            [User CLI]
                │ selects scenario
                ▼
      [Scenario Creator (scenarios.py)]
                │ writes initial loan file
                ▼
        [OrchestratorAgent (1)]
                │ directs phases
   ┌────────────┼────────────┐
   │            │            │
   ▼            ▼            ▼
[Brokers x5] [Processors x6] [Underwriters x5]
   │ (Phase 0)   │ (Phase 1)   │ (Phase 2)
   │             │             │
   └─────writes via file_manager (per-loan lock)─────► loan_files/active/LN-XXXXXX.json
                                │
                                ▼
                       [Decision Maker x1]
                                │ (Phase 3)
                                └─ final status/decision persisted
```

## Recent Fixes / Gotchas
- **Single file_manager**: imports are aliased so `file_manager`, `loan_underwriter.file_manager`, and `src.loan_underwriter.file_manager` share one instance; otherwise write counts and state diverge.
- **Status updates**: `LoanFile.status` stores raw enum values (`use_enum_values=True`); `update_status` now handles both strings and Enums to avoid `.value` errors.
- **Instrumentation**: `[WRITE]` and `[WRITE-COUNT]` logs show persistence; `_ts()` timestamps prove concurrency.

## Expected End State (Clean Approval)
- `status: clear_to_close`
- Populated: `rate_quotes`, `credit_report`, `appraisal`, `financial_metrics`, `underwriting_decisions` (automated + final approval), updated `documents` (credit, appraisal, flood, employment), audit trail entries for each phase.
- Write counts: multiple writes (~15–18) visible in logs and `_write_counts`.

## Validation Tips
- Confirm random completion order within phases (proves concurrency).  
- Check `loan_files/active/LN-XXXXXX.json` for the fields above.  
- Verify `_write_counts` at end of run matches the `[WRITE]` log counts.  
