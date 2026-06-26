import uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.schemas.document import DocumentUploadResponse, DocumentType
from app.schemas.agent_outputs import (
    ProcurementDecisionState,
    AgentStatusEnum,
    AgentExecutionState
)
from app.agents.planner import PlannerAgent

app = FastAPI(title=settings.PROJECT_NAME)

# Set up CORS middleware to allow connections from the frontend (typically localhost:5173 or 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For hackathon ease; lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for simulation and mock integrations
# In a real environment, Developer 3 will hook this to SQLite / database
sessions_db: Dict[str, Dict[str, Any]] = {}
decision_states_db: Dict[str, ProcurementDecisionState] = {}

# Keep track of active tasks to simulate asynchronous execution
active_tasks: Dict[str, str] = {}

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "api_docs": "/docs"
    }

@app.post(f"{settings.API_V1_STR}/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    doc_type: Optional[DocumentType] = Form(None)
):
    # If no session ID is provided, create a new one
    if not session_id:
        session_id = str(uuid.uuid4())
        
    if session_id not in sessions_db:
        sessions_db[session_id] = {
            "uploaded_files": [],
            "doc_types": [],
            "email_content": "",
            "quote_content": "",
            "contract_content": "",
            "meeting_content": ""
        }
        
    filename = file.filename or "unknown_file"
    
    # Infer doc type from file name if not explicitly provided
    if not doc_type:
        fn_lower = filename.lower()
        if "email" in fn_lower:
            doc_type = DocumentType.EMAIL
        elif "quote" in fn_lower or "quotation" in fn_lower:
            doc_type = DocumentType.QUOTATION
        elif "contract" in fn_lower or "agreement" in fn_lower:
            doc_type = DocumentType.CONTRACT
        elif "meeting" in fn_lower or "notes" in fn_lower or "transcript" in fn_lower:
            doc_type = DocumentType.MEETING_NOTES
        else:
            doc_type = DocumentType.EMAIL  # Default fallback
            
    # Read file content for processing
    content_bytes = await file.read()
    content_text = content_bytes.decode("utf-8", errors="ignore")
    
    # Save content to the session context
    sessions_db[session_id]["uploaded_files"].append(filename)
    sessions_db[session_id]["doc_types"].append(doc_type.value)
    
    if doc_type == DocumentType.EMAIL:
        sessions_db[session_id]["email_content"] = content_text
    elif doc_type == DocumentType.QUOTATION:
        sessions_db[session_id]["quote_content"] = content_text
    elif doc_type == DocumentType.CONTRACT:
        sessions_db[session_id]["contract_content"] = content_text
    elif doc_type == DocumentType.MEETING_NOTES:
        sessions_db[session_id]["meeting_content"] = content_text

    return DocumentUploadResponse(
        document_id=str(uuid.uuid4()),
        filename=filename,
        doc_type=doc_type,
        status="uploaded",
        message=f"File successfully uploaded to session '{session_id}'"
    )

async def run_planner_async(session_id: str, context: Dict[str, Any]):
    planner = PlannerAgent()
    try:
        # Run agent chain
        decision_state = await planner.run(context)
        decision_states_db[session_id] = decision_state
        active_tasks[session_id] = "completed"
    except Exception as e:
        active_tasks[session_id] = f"failed: {str(e)}"
        print(f"Async execution error: {e}")

@app.post(f"{settings.API_V1_STR}/analyze/{{session_id}}", response_model=ProcurementDecisionState)
async def start_analysis(session_id: str, background_tasks: BackgroundTasks):
    if session_id not in sessions_db:
        # If session doesn't exist, create a mock session to allow standalone testing
        sessions_db[session_id] = {
            "uploaded_files": ["mock_email.txt", "mock_quote.pdf", "mock_contract.pdf", "mock_meeting.txt"],
            "doc_types": ["email", "quotation", "contract", "meeting_notes"],
            "email_content": "Mock email content",
            "quote_content": "Mock quote content",
            "contract_content": "Mock contract content",
            "meeting_content": "Mock meeting content"
        }

    session_data = sessions_db[session_id]
    context = {
        "session_id": session_id,
        "uploaded_files": session_data["uploaded_files"],
        "doc_types_to_process": session_data["doc_types"],
        "email_content": session_data["email_content"],
        "quote_content": session_data["quote_content"],
        "contract_content": session_data["contract_content"],
        "meeting_content": session_data["meeting_content"],
        "agent_timeline": []
    }
    
    # Initialize basic empty state with PENDING timeline for all agents
    planner = PlannerAgent()
    
    # Build initial status response
    initial_timeline = []
    for doc_type in session_data["doc_types"]:
        if doc_type in planner.extraction_agents:
            initial_timeline.append(AgentExecutionState(
                agent_name=planner.extraction_agents[doc_type].name,
                status=AgentStatusEnum.PENDING
            ))
    for agent in planner.decision_agents:
        initial_timeline.append(AgentExecutionState(
            agent_name=agent.name,
            status=AgentStatusEnum.PENDING
        ))
        
    initial_state = ProcurementDecisionState(
        session_id=session_id,
        uploaded_files=session_data["uploaded_files"],
        agent_timeline=initial_timeline
    )
    
    # Store initial state and trigger background job
    decision_states_db[session_id] = initial_state
    active_tasks[session_id] = "running"
    
    # Run uvicorn background task to execute agents asynchronously
    background_tasks.add_task(run_planner_async, session_id, context)
    
    return initial_state

@app.get(f"{settings.API_V1_STR}/decision/{{session_id}}", response_model=ProcurementDecisionState)
def get_decision_state(session_id: str):
    if session_id not in decision_states_db:
        raise HTTPException(status_code=404, detail="Session not found. Initiate analysis first.")
    return decision_states_db[session_id]

@app.post(f"{settings.API_V1_STR}/decision/{{session_id}}/action")
def submit_human_action(session_id: str, action: str = Form(...), notes: Optional[str] = Form(None)):
    if session_id not in decision_states_db:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    state = decision_states_db[session_id]
    if not state.next_best_action:
        raise HTTPException(status_code=400, detail="Decision recommendations not generated yet.")
        
    # Simulate writing human override back into memory database (Team Member 2 & 3 task)
    return {
        "status": "success",
        "message": f"Decision Action '{action}' recorded for session '{session_id}'.",
        "notes": notes,
        "logged_to_memory": True
    }
