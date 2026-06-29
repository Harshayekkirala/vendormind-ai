import asyncio
import sys
from pathlib import Path

# Add backend directory to path so imports work out-of-the-box
sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.agents.planner import PlannerAgent
from app.schemas.agent_outputs import AgentStatusEnum

async def test_planner_chain():
    print("[START] Starting VendorMind AI Agent Pipeline Test...\n")
    
    # Setup test context
    context = {
        "session_id": "test_session_123",
        "uploaded_files": ["rfq_email_draft.txt", "quote_valves_v3.pdf", "standard_contract.pdf", "kickoff_notes.txt"],
        "doc_types_to_process": ["email", "quotation", "contract", "meeting_notes"],
        "email_content": "Dear vendor, we would like a 10% volume discount on units > 50...",
        "quote_content": "100 Units of API Licenses. Price: $125,000 USD...",
        "contract_content": "Payment terms Net 45. Penalty 0.5% per week of delay...",
        "meeting_content": "Agreed to waive $5,000 onboarding fee if signed before end of Q3..."
    }
    
    planner = PlannerAgent()
    
    # Run the pipeline
    start_time = asyncio.get_event_loop().time()
    result_state = await planner.run(context)
    end_time = asyncio.get_event_loop().time()
    
    print(f"\n[SUCCESS] Pipeline execution completed in {end_time - start_time:.2f} seconds.")
    print(f"Session ID: {result_state.session_id}")
    print(f"Uploaded Files: {result_state.uploaded_files}")
    
    print("\n[TIMELINE] AGENT TIMELINE PROGRESS:")
    print("=" * 60)
    for state in result_state.agent_timeline:
        status_symbol = "[PENDING]"
        if state.status == AgentStatusEnum.COMPLETED:
            status_symbol = "[  OK   ]"
        elif state.status == AgentStatusEnum.FAILED:
            status_symbol = "[ FAIL  ]"
        elif state.status == AgentStatusEnum.RUNNING:
            status_symbol = "[  RUN  ]"
        elif state.status == AgentStatusEnum.SKIPPED:
            status_symbol = "[ SKIP  ]"
        
        duration_str = f"({state.duration_ms}ms)" if state.duration_ms is not None else ""
        err_str = f" - Error: {state.error_message}" if state.error_message else ""
        print(f"{status_symbol} {state.agent_name:<34} : {state.status.value.upper():<10} {duration_str}{err_str}")
    print("=" * 60)
    
    print("\n[RESULTS] KEY RESULTS:")
    print(f"Price                    : {result_state.quote_data.total_amount if result_state.quote_data else 'None'}")
    print(f"Payment Schedule         : {result_state.contract_data.payment_schedule if result_state.contract_data else 'None'}")
    print(f"Risk Category            : {result_state.risk_assessment.risk_level if result_state.risk_assessment else 'None'} ({result_state.risk_assessment.overall_risk if result_state.risk_assessment else 0}%)")
    print(f"Reason Summary           : {result_state.reasoning.situation_summary[:120] if result_state.reasoning else 'None'}...")
    
    if result_state.next_best_action and result_state.next_best_action.recommendations:
        rec = result_state.next_best_action.recommendations[0]
        print(f"Recommendation           : {rec.get('action')}")
        print(f"Confidence               : {rec.get('confidence')}%")
    else:
        print("Recommendation           : None")
        print("Confidence               : 0%")

if __name__ == "__main__":
    asyncio.run(test_planner_chain())
