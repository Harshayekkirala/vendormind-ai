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
from pydantic import BaseModel
import hashlib
import os
import secrets
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, Security

# Hashing utility
def hash_password(password: str, salt: str = None) -> tuple:
    if salt is None:
        salt = secrets.token_hex(16)
    salt_bytes = bytes.fromhex(salt)
    pwd_bytes = password.encode("utf-8")
    hashed = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, 100000)
    return hashed.hex(), salt

class UserSignupRequest(BaseModel):
    username: str
    password: str
    full_name: str = None

class UserLoginRequest(BaseModel):
    username: str
    password: str

class AnalyzeRequest(BaseModel):
    selected_vendors: List[str]
    requirements: Dict[str, Any]

class PolicyCreateRequest(BaseModel):
    code: str
    category: str
    text: str

# HTTP Bearer security scheme
security_scheme = HTTPBearer(auto_error=False)

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = credentials.credentials
    
    from app.core.database import get_db_conn
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.*, s.expires_at 
            FROM user_sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = %s;
        """, (token,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=401, detail="Invalid session token.")
            
        exp = row["expires_at"]
        if isinstance(exp, str):
            exp = datetime.strptime(exp.split(".")[0], "%Y-%m-%d %H:%M:%S")
            
        if exp < datetime.now():
            raise HTTPException(status_code=401, detail="Session expired.")
            
        return {
            "id": row["id"],
            "username": row["username"],
            "full_name": row["full_name"]
        }

def ensure_vendor_documents_and_get_raw_data(session_id: str, selected_vendors: List[str]) -> Dict[str, Any]:
    from app.core.database import get_db_conn
    
    if session_id not in sessions_db:
        sessions_db[session_id] = {}
        
    if "vendors" not in sessions_db[session_id]:
        sessions_db[session_id]["vendors"] = {}
        
    vendors_raw = sessions_db[session_id]["vendors"]
    
    for name in selected_vendors:
        if name not in vendors_raw:
            raise HTTPException(
                status_code=400,
                detail=f"Vendor '{name}' has no uploaded documents. Please upload at least one document (Email, Quote, Contract, or Meeting Notes) for this vendor."
            )
            
        v_data = vendors_raw[name]
        has_content = any([
            v_data.get("email_content", "").strip(),
            v_data.get("quote_content", "").strip(),
            v_data.get("contract_content", "").strip(),
            v_data.get("meeting_content", "").strip()
        ])
        
        if not has_content:
            raise HTTPException(
                status_code=400,
                detail=f"Vendor '{name}' has no uploaded documents. Please upload at least one document (Email, Quote, Contract, or Meeting Notes) for this vendor."
            )
            
    return vendors_raw

app = FastAPI(title=settings.PROJECT_NAME)

@app.on_event("startup")
def startup_db_init():
    from app.core.database import get_db_conn, create_tables
    try:
        with get_db_conn() as conn:
            create_tables(conn)
            print("INFO: Database verification and migrations run successfully on startup.")
    except Exception as e:
        print(f"ERROR: Startup database migration failed: {e}")

# Set up CORS middleware to allow connections from the frontend (typically localhost:5173 or 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For hackathon ease; lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post(f"{settings.API_V1_STR}/auth/signup")
def auth_signup(req: UserSignupRequest):
    from app.core.database import get_db_conn
    hashed_pwd, salt = hash_password(req.password)
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, hashed_password, salt, full_name)
                VALUES (%s, %s, %s, %s);
            """, (req.username.strip(), hashed_pwd, salt, req.full_name))
            conn.commit()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Username already exists or registration error: {e}"
        )
    return {"status": "success", "message": "User registered successfully."}

@app.post(f"{settings.API_V1_STR}/auth/login")
def auth_login(req: UserLoginRequest):
    from app.core.database import get_db_conn
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s;", (req.username.strip(),))
            user = cursor.fetchone()
            
            if not user:
                raise HTTPException(status_code=401, detail="Invalid username or password.")
                
            hashed_input, _ = hash_password(req.password, user["salt"])
            if hashed_input != user["hashed_password"]:
                raise HTTPException(status_code=401, detail="Invalid username or password.")
                
            token = secrets.token_hex(32)
            expires_at = datetime.now() + timedelta(days=1)
            
            cursor.execute("""
                INSERT INTO user_sessions (user_id, token, expires_at)
                VALUES (%s, %s, %s);
            """, (user["id"], token, expires_at))
            conn.commit()
            
            return {
                "token": token,
                "username": user["username"],
                "full_name": user["full_name"],
                "status": "success"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database login error: {e}")

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
    doc_type: Optional[DocumentType] = Form(None),
    vendor_name: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
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
    if filename.lower().endswith(".pdf"):
        from app.core.pdf import extract_text_from_pdf
        content_text = extract_text_from_pdf(content_bytes)
    else:
        content_text = content_bytes.decode("utf-8", errors="ignore")
    
    # Save content to the session context
    if vendor_name:
        if "vendors" not in sessions_db[session_id]:
            sessions_db[session_id]["vendors"] = {}
        if vendor_name not in sessions_db[session_id]["vendors"]:
            sessions_db[session_id]["vendors"][vendor_name] = {
                "uploaded_files": [],
                "doc_types": [],
                "email_content": "",
                "quote_content": "",
                "contract_content": "",
                "meeting_content": ""
            }
        target = sessions_db[session_id]["vendors"][vendor_name]
    else:
        target = sessions_db[session_id]
        
    target["uploaded_files"].append(filename)
    if hasattr(doc_type, "value"):
        target["doc_types"].append(doc_type.value)
    else:
        target["doc_types"].append(str(doc_type))
    
    if doc_type == DocumentType.EMAIL:
        target["email_content"] = content_text
    elif doc_type == DocumentType.QUOTATION:
        target["quote_content"] = content_text
    elif doc_type == DocumentType.CONTRACT:
        target["contract_content"] = content_text
    elif doc_type == DocumentType.MEETING_NOTES:
        target["meeting_content"] = content_text

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
async def start_analysis(
    session_id: str,
    background_tasks: BackgroundTasks,
    payload: Optional[AnalyzeRequest] = None,
    current_user: dict = Depends(get_current_user)
):
    if payload and payload.selected_vendors:
        if session_id not in sessions_db:
            sessions_db[session_id] = {
                "uploaded_files": [],
                "doc_types": [],
                "email_content": "",
                "quote_content": "",
                "contract_content": "",
                "meeting_content": ""
            }

        # Multi-vendor flow
        vendors_raw = ensure_vendor_documents_and_get_raw_data(session_id, payload.selected_vendors)
        print("DEBUG MULTI-VENDOR RAW DATA:")
        try:
            import json
            debug_info = {}
            for v_name, v_data in vendors_raw.items():
                debug_info[v_name] = {
                    "uploaded_files": v_data.get("uploaded_files"),
                    "quote_content_length": len(v_data.get("quote_content", "")),
                    "quote_content_snippet": v_data.get("quote_content")[:200] if v_data.get("quote_content") else "None",
                    "contract_content_snippet": v_data.get("contract_content")[:200] if v_data.get("contract_content") else "None"
                }
            with open(r"C:\Users\harsh\.gemini\antigravity-ide\brain\d613013a-c4f5-4855-802b-46616c296246\scratch\debug_log.txt", "w", encoding="utf-8") as f:
                json.dump(debug_info, f, indent=2)
        except Exception as e:
            print(f"Error writing debug file: {e}")
        
        # Check and dynamically register new vendors in PostgreSQL table
        from app.core.database import get_db_conn
        try:
            with get_db_conn() as conn:
                cursor = conn.cursor()
                for name in payload.selected_vendors:
                    cursor.execute("SELECT id FROM vendors WHERE name = %s AND user_id = %s;", (name, current_user["id"]))
                    vendor = cursor.fetchone()
                    if not vendor:
                        cursor.execute("""
                            INSERT INTO vendors (name, category, performance_score, risk_level, is_blacklisted, status, user_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s);
                        """, (
                            name, 
                            payload.requirements.get("category", "Software"), 
                            5.0, 
                            "Low", 
                            0, 
                            "Active",
                            current_user["id"]
                        ))
                conn.commit()
        except Exception as e:
            print(f"Error dynamically registering new vendors in DB: {e}")
        context = {
            "session_id": session_id,
            "multi_vendors": payload.selected_vendors,
            "requirements": payload.requirements,
            "rejected_vendors": [],
            "vendors_raw_data": vendors_raw,
            "agent_timeline": []
        }
        # Persist requirements to database initially
        from app.core.database import save_session_state
        save_session_state(session_id, payload.requirements, [])
    else:
        # Single-vendor fallback flow
        session_data = sessions_db[session_id]
        if not session_data.get("uploaded_files"):
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

    # Save context reference for re-evaluations
    sessions_db[session_id]["context"] = context
    
    # Initialize basic empty state with PENDING timeline for all agents
    planner = PlannerAgent()
    initial_timeline = []
    
    if payload:
        # Add special Multi-Vendor progress tracking rows
        for name in payload.selected_vendors:
            initial_timeline.append(AgentExecutionState(
                agent_name=f"{name}: Cognitive Analysis Suite",
                status=AgentStatusEnum.PENDING
            ))
        initial_timeline.append(AgentExecutionState(
            agent_name="Multi-Vendor Recommendation Agent",
            status=AgentStatusEnum.PENDING
        ))
    else:
        for doc_type in context.get("doc_types_to_process", []):
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
        uploaded_files=sessions_db[session_id].get("uploaded_files", []),
        agent_timeline=initial_timeline
    )
    
    # Store initial state and trigger background job
    decision_states_db[session_id] = initial_state
    active_tasks[session_id] = "running"
    
    # Run uvicorn background task to execute agents asynchronously
    background_tasks.add_task(run_planner_async, session_id, context)
    
    return initial_state

@app.get(f"{settings.API_V1_STR}/decision/{{session_id}}", response_model=ProcurementDecisionState)
def get_decision_state(session_id: str, current_user: dict = Depends(get_current_user)):
    if session_id not in decision_states_db:
        raise HTTPException(status_code=404, detail="Session not found. Initiate analysis first.")
    return decision_states_db[session_id]

@app.post(f"{settings.API_V1_STR}/decision/{{session_id}}/action")
async def submit_human_action(
    session_id: str,
    action: str,
    background_tasks: BackgroundTasks,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    # Retrieve vendor name and budget from session state if available
    vendor_name = "Unknown Vendor"
    budget_val = "125,000"
    action_text = "Review required"
    
    if session_id in decision_states_db:
        state = decision_states_db[session_id]
        if state.recommended_vendor_name:
            vendor_name = state.recommended_vendor_name
        elif state.quote_data and state.quote_data.vendor_name:
            vendor_name = state.quote_data.vendor_name
            
        if state.quote_data and state.quote_data.total_amount:
            budget_val = f"{state.quote_data.total_amount:,.2f}"
            
        if state.next_best_action and state.next_best_action.recommendations:
            action_text = state.next_best_action.recommendations[0].action if hasattr(state.next_best_action.recommendations[0], "action") else state.next_best_action.recommendations[0].get("action", "Review required")
            
    # Combine details for the audit log
    recommendation_log = notes if notes else action_text
 
    # Write rejection loop logic
    if action == "Rejected" and session_id in decision_states_db:
        state = decision_states_db[session_id]
        # Check if it is a multi-vendor session and we can suggest alternative
        if state.recommended_vendor_name and state.comparison_matrix:
            if state.recommended_vendor_name not in state.rejected_vendors:
                state.rejected_vendors.append(state.recommended_vendor_name)
                
            # Update database
            from app.core.database import save_session_state
            save_session_state(session_id, state.requirements, state.rejected_vendors)
            
            # Re-evaluate session asynchronously using background tasks
            context = sessions_db[session_id].get("context")
            if context:
                context["rejected_vendors"] = state.rejected_vendors
                
                # Update current timeline item to RUNNING so polling frontend detects it
                if state.agent_timeline:
                    for row in state.agent_timeline:
                        if row.agent_name == "Multi-Vendor Recommendation Agent":
                            row.status = AgentStatusEnum.RUNNING
                
                active_tasks[session_id] = "running"
                background_tasks.add_task(run_planner_async, session_id, context)
 
    # Log action to audit trail
    from app.core.database import get_db_conn
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_trail (session_id, vendor_name, action, notes, user_id)
                VALUES (%s, %s, %s, %s, %s);
            """, (session_id, vendor_name, action, f"Budget: ${budget_val} | {recommendation_log}", current_user["id"]))
            conn.commit()
    except Exception as e:
        print(f"Error saving to audit_trail: {e}")
        
    return {
        "status": "success",
        "message": f"Decision Action '{action}' recorded persistently.",
        "logged_to_db": True
    }
 
@app.get(f"{settings.API_V1_STR}/audit-trail")
def get_audit_trail(current_user: dict = Depends(get_current_user)):
    from app.core.database import get_db_conn
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, vendor_name as vendor, 'Software' as category,
                       notes as recommendation, action as status, timestamp
                FROM audit_trail
                WHERE user_id = %s
                ORDER BY timestamp DESC;
            """, (current_user["id"],))
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                note_str = row["recommendation"] or ""
                budget_str = "125,000"
                rec_str = note_str
                
                if "Budget: $" in note_str and " | " in note_str:
                    parts = note_str.split(" | ", 1)
                    budget_str = parts[0].replace("Budget: $", "")
                    rec_str = parts[1]
                    
                ts = row["timestamp"]
                if ts and not isinstance(ts, str):
                    ts_str = ts.strftime("%Y-%m-%d %H:%M")
                else:
                    ts_str = ts[:16].replace('T', ' ') if ts else ""
                    
                result.append({
                    "session_id": row["session_id"][:15],
                    "vendor": row["vendor"],
                    "category": row["category"],
                    "budget": budget_str,
                    "recommendation": rec_str,
                    "status": row["status"],
                    "timestamp": ts_str
                })
            return result
    except Exception as e:
        print(f"Error querying audit trail: {e}")
        return []

def get_vector_embedding(text: str) -> list:
    import google.generativeai as genai
    from app.core.config import settings
    if not settings.GEMINI_API_KEY:
        return [0.0] * 3072
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        response = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return response["embedding"]
    except Exception as e:
        print(f"Error calling Gemini Embeddings API: {e}. Seeding dummy vectors...")
        return [0.0] * 3072

@app.get(f"{settings.API_V1_STR}/policies")
def get_policies(current_user: dict = Depends(get_current_user)):
    from app.core.database import get_db_conn
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, category, text FROM policies ORDER BY code;")
            rows = cursor.fetchall()
            return [{"id": r["id"], "code": r["code"], "category": r["category"], "text": r["text"]} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.post(f"{settings.API_V1_STR}/policies")
def create_policy(payload: PolicyCreateRequest, current_user: dict = Depends(get_current_user)):
    from app.core.database import get_db_conn
    
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM policies WHERE code = %s;", (payload.code,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Policy code '{payload.code}' already exists.")
            
            # Generate embedding
            embedding = get_vector_embedding(payload.text)
            
            # Insert policy with embedding
            cursor.execute("""
                INSERT INTO policies (code, category, text, embedding)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """, (payload.code, payload.category, payload.text, embedding))
            new_id = cursor.fetchone()["id"]
            conn.commit()
            
            return {
                "id": new_id,
                "code": payload.code,
                "category": payload.category,
                "text": payload.text,
                "status": "success",
                "message": "Policy registered and vector embedding generated."
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.delete(f"{settings.API_V1_STR}/policies/{{id}}")
def delete_policy(id: int, current_user: dict = Depends(get_current_user)):
    from app.core.database import get_db_conn
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM policies WHERE id = %s;", (id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Policy not found.")
                
            cursor.execute("DELETE FROM policies WHERE id = %s;", (id,))
            conn.commit()
            return {"status": "success", "message": "Policy successfully deleted."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get(f"{settings.API_V1_STR}/vendors")
def get_vendors(current_user: dict = Depends(get_current_user)):
    from app.core.database import get_db_conn
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, category, performance_score, risk_level, is_blacklisted, status 
                FROM vendors 
                WHERE user_id = %s
                ORDER BY name;
            """, (current_user["id"],))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
 
@app.get(f"{settings.API_V1_STR}/vendors/{{vendor_name}}")
def get_vendor_details(
    vendor_name: str, 
    session_id: Optional[str] = None, 
    current_user: dict = Depends(get_current_user)
):
    from app.core.database import get_db_conn
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            # Fetch vendor info
            cursor.execute("""
                SELECT id, name, category, performance_score, risk_level, is_blacklisted, status 
                FROM vendors 
                WHERE LOWER(name) = LOWER(%s) AND user_id = %s;
            """, (vendor_name.strip(), current_user["id"]))
            vendor = cursor.fetchone()
            
            if not vendor:
                raise HTTPException(status_code=404, detail=f"Vendor '{vendor_name}' not found.")
            
            vendor_id = vendor["id"]
            
            # Fetch catalog
            cursor.execute("""
                SELECT id, item_description, standard_unit_price, typical_lead_time_days 
                FROM vendor_catalog 
                WHERE vendor_id = %s;
            """, (vendor_id,))
            catalog = [dict(row) for row in cursor.fetchall()]
            
            # Fetch purchase history
            cursor.execute("""
                SELECT purchase_id, date, amount, qty, unit_price, status, rating 
                FROM purchase_history 
                WHERE vendor_id = %s 
                ORDER BY date DESC;
            """, (vendor_id,))
            history = [dict(row) for row in cursor.fetchall()]
            
            # Check for session documents
            session_docs = {}
            if session_id and session_id in sessions_db:
                v_session_data = sessions_db[session_id].get("vendors", {}).get(vendor["name"])
                if v_session_data:
                    session_docs = {
                        "uploaded_files": v_session_data.get("uploaded_files", []),
                        "doc_types": v_session_data.get("doc_types", []),
                        "has_email": bool(v_session_data.get("email_content")),
                        "has_quote": bool(v_session_data.get("quote_content")),
                        "has_contract": bool(v_session_data.get("contract_content")),
                        "has_meeting": bool(v_session_data.get("meeting_content")),
                    }
            
            return {
                "profile": dict(vendor),
                "catalog": catalog,
                "purchase_history": history,
                "session_documents": session_docs
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get(f"{settings.API_V1_STR}/vendors/{{vendor_name}}/doc/{{doc_type}}")
def get_vendor_session_document(
    vendor_name: str,
    doc_type: str,
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    # Match vendor by case-insensitive name
    target_vendor_key = None
    vendors_dict = sessions_db[session_id].get("vendors", {})
    for v_key in vendors_dict.keys():
        if v_key.lower() == vendor_name.lower():
            target_vendor_key = v_key
            break
            
    if not target_vendor_key:
        raise HTTPException(status_code=404, detail=f"Vendor '{vendor_name}' not found in active session.")
        
    v_data = vendors_dict[target_vendor_key]
    
    content_key_map = {
        "email": "email_content",
        "quotation": "quote_content",
        "contract": "contract_content",
        "meeting_notes": "meeting_content"
    }
    
    content_key = content_key_map.get(doc_type.lower())
    if not content_key:
        raise HTTPException(status_code=400, detail=f"Invalid document type '{doc_type}'.")
        
    content = v_data.get(content_key, "")
    if not content.strip():
        raise HTTPException(status_code=404, detail=f"Document type '{doc_type}' is empty or not uploaded.")
        
    return {
        "vendor_name": target_vendor_key,
        "doc_type": doc_type,
        "content": content
    }
