import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  Upload,
  CheckCircle,
  Clock,
  AlertTriangle,
  Play,
  ShieldAlert,
  Award,
  FileText,
  ArrowRight,
  History,
  Sparkles,
  RefreshCw,
  Lock,
  UserCheck,
  PlusCircle,
  Activity,
  Users
} from "lucide-react";

// API Root URL
const API_BASE_URL = "http://localhost:8000/api/v1";

export default function App() {
  // Navigation
  const [activeTab, setActiveTab] = useState("dashboard");

  // Auth state
  const [token, setToken] = useState(() => localStorage.getItem("vendormind_token") || "");
  const [currentUser, setCurrentUser] = useState(() => localStorage.getItem("vendormind_username") || "");
  const [authTab, setAuthTab] = useState("signin");
  const [usernameInput, setUsernameInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [fullNameInput, setFullNameInput] = useState("");
  const [authError, setAuthError] = useState("");

  // Procurement Inputs
  const [selectedVendors, setSelectedVendors] = useState([]);
  const [newVendorName, setNewVendorName] = useState("");
  const [customRules, setCustomRules] = useState("");
  const [activeUploadVendor, setActiveUploadVendor] = useState("");
  const [activeRiskVendor, setActiveRiskVendor] = useState("");
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("");
  const [department, setDepartment] = useState("");
  const [budget, setBudget] = useState("");
  const [analysisError, setAnalysisError] = useState("");

  // Policy Admin State
  const [policies, setPolicies] = useState([]);
  const [newPolicyCode, setNewPolicyCode] = useState("");
  const [newPolicyCategory, setNewPolicyCategory] = useState("limits");
  const [newPolicyText, setNewPolicyText] = useState("");
  const [policyError, setPolicyError] = useState("");

  // Vendor Directory State
  const [vendorsList, setVendorsList] = useState([]);
  const [selectedDirVendor, setSelectedDirVendor] = useState("");
  const [vendorDetails, setVendorDetails] = useState(null);
  const [previewDocType, setPreviewDocType] = useState(null);
  const [previewDocContent, setPreviewDocContent] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState("");

  const fetchVendorsList = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/vendors`);
      setVendorsList(response.data);
      if (response.data.length > 0 && !selectedDirVendor) {
        setSelectedDirVendor(response.data[0].name);
      }
    } catch (err) {
      console.error("Error fetching vendors list:", err);
    }
  };

  const fetchVendorDetails = async (vendorName) => {
    try {
      setVendorDetails(null);
      setPreviewDocType(null);
      setPreviewDocContent("");
      setPreviewError("");
      const response = await axios.get(`${API_BASE_URL}/vendors/${vendorName}?session_id=${sessionId || ""}`);
      setVendorDetails(response.data);
    } catch (err) {
      console.error("Error fetching vendor details:", err);
    }
  };

  const fetchDocumentPreview = async (vendorName, docType) => {
    if (!sessionId) return;
    setPreviewLoading(true);
    setPreviewError("");
    setPreviewDocType(docType);
    setPreviewDocContent("");
    try {
      const response = await axios.get(`${API_BASE_URL}/vendors/${vendorName}/doc/${docType}?session_id=${sessionId}`);
      setPreviewDocContent(response.data.content);
    } catch (err) {
      setPreviewError("Failed to fetch document preview. It might be empty or not uploaded yet.");
      console.error("Error fetching document preview:", err);
    } finally {
      setPreviewLoading(false);
    }
  };

  const fetchPolicies = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/policies`);
      setPolicies(response.data);
    } catch (err) {
      console.error("Error fetching policies:", err);
    }
  };

  const handleAddPolicy = async (e) => {
    e.preventDefault();
    setPolicyError("");
    if (!newPolicyCode.trim() || !newPolicyText.trim()) {
      setPolicyError("Please fill out all policy fields.");
      return;
    }
    try {
      await axios.post(`${API_BASE_URL}/policies`, {
        code: newPolicyCode.trim(),
        category: newPolicyCategory,
        text: newPolicyText.trim()
      });
      setNewPolicyCode("");
      setNewPolicyText("");
      fetchPolicies();
    } catch (err) {
      setPolicyError(err.response?.data?.detail || "Failed to create policy.");
    }
  };

  const handleDeletePolicy = async (policyId) => {
    if (!window.confirm("Are you sure you want to delete this policy?")) return;
    try {
      await axios.delete(`${API_BASE_URL}/policies/${policyId}`);
      fetchPolicies();
    } catch (err) {
      alert("Failed to delete policy.");
    }
  };

  const handleDownloadPDFReport = () => {
    const printWindow = window.open("", "_blank");
    if (!printWindow) {
      alert("Please allow popups to download the PDF report.");
      return;
    }
    
    const timestampStr = new Date().toLocaleString();
    const recommendedVendor = decisionState.recommended_vendor_name || "N/A";
    
    let comparisonRows = "";
    if (decisionState.comparison_matrix) {
      decisionState.comparison_matrix.forEach(row => {
        comparisonRows += `
          <tr>
            <td><strong>${row.vendor}</strong></td>
            <td>$${row.price?.toLocaleString()}</td>
            <td>${row.compliance}</td>
            <td>${row.lead_time}</td>
            <td>${row.risk_score}% (${row.risk})</td>
            <td>${row.performance} / 5.0</td>
            <td>${row.status}</td>
          </tr>
        `;
      });
    }

    let riskFactorsHtml = "";
    if (decisionState.evaluated_vendors) {
      Object.entries(decisionState.evaluated_vendors).forEach(([vName, vData]) => {
        const factors = vData.risk_assessment?.risk_factors || [];
        if (factors.length > 0) {
          riskFactorsHtml += `<h3>${vName} Risk Profile</h3><ul>`;
          factors.forEach(f => {
            riskFactorsHtml += `<li>${f}</li>`;
          });
          riskFactorsHtml += `</ul>`;
        }
      });
    } else if (decisionState.risk_assessment?.risk_factors) {
      riskFactorsHtml += `<h3>Risk Profile</h3><ul>`;
      decisionState.risk_assessment.risk_factors.forEach(f => {
        riskFactorsHtml += `<li>${f}</li>`;
      });
      riskFactorsHtml += `</ul>`;
    }

    let reasoningHtml = "";
    if (decisionState.reasoning?.cognitive_findings) {
      decisionState.reasoning.cognitive_findings.forEach(find => {
        reasoningHtml += `
          <div class="finding-block">
            <strong>Source:</strong> ${find.source}<br/>
            <strong>Fact:</strong> "${find.fact}"<br/>
            <strong>AI Rationale:</strong> ${find.reasoning_step}
          </div>
        `;
      });
    }

    printWindow.document.write(`
      <html>
        <head>
          <title>Procurement Audit Report - Session ${sessionId}</title>
          <style>
            body {
              font-family: Arial, sans-serif;
              color: #333;
              margin: 40px;
              line-height: 1.5;
            }
            .header {
              border-bottom: 3px solid #00f2fe;
              padding-bottom: 20px;
              margin-bottom: 30px;
              display: flex;
              justify-content: space-between;
              align-items: center;
            }
            .title {
              font-size: 24px;
              font-weight: bold;
              color: #111;
            }
            .meta-section {
              background-color: #f4f6f9;
              padding: 20px;
              border-radius: 6px;
              margin-bottom: 30px;
              display: grid;
              grid-template-columns: 1fr 1fr;
              gap: 12px;
              font-size: 13.5px;
            }
            .section-title {
              font-size: 16px;
              font-weight: bold;
              border-bottom: 1px solid #ddd;
              padding-bottom: 6px;
              margin-top: 30px;
              margin-bottom: 16px;
              text-transform: uppercase;
              letter-spacing: 0.5px;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin-bottom: 30px;
              font-size: 13px;
            }
            th, td {
              border: 1px solid #ddd;
              padding: 10px;
              text-align: left;
            }
            th {
              background-color: #f4f6f9;
              font-weight: bold;
            }
            .finding-block {
              background-color: #fafbfc;
              border-left: 3px solid #00f2fe;
              padding: 12px;
              margin-bottom: 12px;
              border-radius: 0 4px 4px 0;
              font-size: 13px;
            }
            .sign-off-box {
              border: 2px solid #10b981;
              background-color: rgba(16, 185, 129, 0.05);
              padding: 20px;
              border-radius: 8px;
              margin-top: 40px;
              text-align: center;
            }
            .sign-off-title {
              font-size: 18px;
              font-weight: bold;
              color: #10b981;
              margin-bottom: 8px;
            }
            @media print {
              body { margin: 20px; }
              .no-print { display: none; }
            }
          </style>
        </head>
        <body>
          <div class="header">
            <div>
              <div class="title">VendorMind AI</div>
              <div style="font-size: 12px; color: #666; margin-top: 4px;">Automated AI Procurement & Auditing Suite</div>
            </div>
            <div style="text-align: right; font-size: 12px; color: #666;">
              Report generated on: ${timestampStr}
            </div>
          </div>

          <div class="meta-section">
            <div><strong>Audit Session ID:</strong> ${sessionId}</div>
            <div><strong>Procurer Session:</strong> ${currentUser}</div>
            <div><strong>Procurement Category:</strong> ${category || 'Software'}</div>
            <div><strong>Operating Department:</strong> ${department || 'IT'}</div>
            <div><strong>Estimated Project Budget:</strong> $${parseFloat(budget)?.toLocaleString()}</div>
            <div><strong>Primary Recommended Vendor:</strong> ${recommendedVendor}</div>
            <div><strong>Sign-off Lock Tier:</strong> ${decisionState.next_best_action?.final_decision_tier || 'Manager'}</div>
            <div><strong>Compliance Status:</strong> ${decisionState.policy_checks?.compliance_status || 'Compliant'}</div>
          </div>

          <div class="section-title">Multi-Vendor Comparison Matrix</div>
          <table>
            <thead>
              <tr>
                <th>Vendor Name</th>
                <th>Offered Price ($)</th>
                <th>Compliance State</th>
                <th>Delivery Timeline</th>
                <th>Audit Risk Level</th>
                <th>Performance rating</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${comparisonRows}
            </tbody>
          </table>

          <div class="section-title">AI Rationale & Recommendation Details</div>
          <div style="background-color: #fafbfc; border-left: 3px solid #00f2fe; padding: 16px; border-radius: 4px; font-size: 14px; margin-bottom: 24px;">
            <strong>Recommended Deal Action:</strong><br/>
            ${decisionState.next_best_action?.recommendations[0]?.action || 'N/A'}<br/><br/>
            <strong>Core Auditing Reason:</strong><br/>
            ${decisionState.next_best_action?.recommendations[0]?.reason || 'N/A'}
          </div>

          ${riskFactorsHtml ? `<div class="section-title">Identified Risk Audits</div>${riskFactorsHtml}` : ''}

          ${reasoningHtml ? `<div class="section-title">Cognitive Findings Traceability</div>${reasoningHtml}` : ''}

          <div class="sign-off-box">
            <div class="sign-off-title">OFFICIAL DEAL SIGN-OFF RECORD</div>
            <div style="font-size: 14px; margin-bottom: 8px;">
              Decision Action: <strong>${decisionOutcome}</strong>
            </div>
            <div style="font-size: 13px; font-style: italic; color: #555;">
              "Override Comments: ${approvalNotes || 'No overriding comments entered.'}"
            </div>
            <div style="margin-top: 16px; border-top: 1px dashed #ccc; padding-top: 12px; font-size: 11px; color: #777;">
              Digitally signed and committed to the secure system ledger database.
            </div>
          </div>

          <div class="no-print" style="margin-top: 40px; text-align: center;">
            <button onclick="window.print();" style="padding: 10px 20px; font-weight: bold; background-color: #00f2fe; border: none; border-radius: 4px; cursor: pointer;">
              Click to Save / Print PDF Document
            </button>
          </div>
        </body>
      </html>
    `);
    
    printWindow.document.close();
    setTimeout(() => {
      printWindow.focus();
      printWindow.print();
    }, 500);
  };


  // Auth header sync
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
      localStorage.setItem("vendormind_token", token);
      fetchPolicies();
    } else {
      delete axios.defaults.headers.common["Authorization"];
      localStorage.removeItem("vendormind_token");
    }
  }, [token]);

  useEffect(() => {
    if (currentUser) {
      localStorage.setItem("vendormind_username", currentUser);
    } else {
      localStorage.removeItem("vendormind_username");
    }
  }, [currentUser]);

  const handleAddVendor = () => {
    const trimmed = newVendorName.trim();
    if (!trimmed) return;
    if (selectedVendors.includes(trimmed)) {
      alert("Vendor already added!");
      return;
    }
    setSelectedVendors([...selectedVendors, trimmed]);
    setVendorUploadedFiles(prev => ({
      ...prev,
      [trimmed]: { email: null, quotation: null, contract: null, meeting_notes: null }
    }));
    setActiveUploadVendor(trimmed);
    setNewVendorName("");
  };

  const handleRemoveVendor = (vName) => {
    if (selectedVendors.length <= 1) {
      alert("Please keep at least one vendor.");
      return;
    }
    const filtered = selectedVendors.filter(v => v !== vName);
    setSelectedVendors(filtered);
    if (activeUploadVendor === vName) {
      setActiveUploadVendor(filtered[0]);
    }
  };

  // File Upload State (Mapped by active vendor)
  const [vendorUploadedFiles, setVendorUploadedFiles] = useState({
    Suresh: { email: null, quotation: null, contract: null, meeting_notes: null },
    Naresh: { email: null, quotation: null, contract: null, meeting_notes: null }
  });
  
  // Status states
  const [sessionId, setSessionId] = useState("");
  const [loading, setLoading] = useState(false);
  const [offlineMode, setOfflineMode] = useState(false);
  
  // Accumulated decision state from API
  const [decisionState, setDecisionState] = useState(null);
  const [timelineTimer, setTimelineTimer] = useState(null);

  // Human approval inputs
  const [approvalNotes, setApprovalNotes] = useState("");
  const [decisionOutcome, setDecisionOutcome] = useState(null);
  
  // Audit Trail History logs
  const [auditLogs, setAuditLogs] = useState(() => {
    const saved = localStorage.getItem("vendormind_audit_logs");
    return saved ? JSON.parse(saved) : [
      {
        session_id: "721a-e8d9-291b",
        vendor: "ABC Technologies",
        category: "Hardware",
        budget: "98,000",
        recommendation: "Negotiate Price - unit cost exceeds standard by 4%",
        status: "Approved",
        timestamp: "2026-06-25 14:22"
      }
    ];
  });

  useEffect(() => {
    localStorage.setItem("vendormind_audit_logs", JSON.stringify(auditLogs));
  }, [auditLogs]);

  // Clean up timer on unmount
  useEffect(() => {
    return () => {
      if (timelineTimer) clearInterval(timelineTimer);
    };
  }, [timelineTimer]);

  // Fetch audit trail history from backend
  useEffect(() => {
    if (activeTab === "history" && !offlineMode) {
      axios.get(`${API_BASE_URL}/audit-trail`)
        .then(res => {
          setAuditLogs(res.data);
        })
        .catch(err => {
          console.error("Error fetching persistent audit logs:", err);
        });
    } else if (activeTab === "vendors" && !offlineMode) {
      fetchVendorsList();
    }
  }, [activeTab, offlineMode]);

  useEffect(() => {
    if (selectedDirVendor && activeTab === "vendors" && !offlineMode) {
      fetchVendorDetails(selectedDirVendor);
    }
  }, [selectedDirVendor, activeTab, offlineMode]);

  // Handle uploading simulation or API calls
  const handleFileChange = (type, e) => {
    const file = e.target.files[0];
    if (!file) return;
    setVendorUploadedFiles(prev => {
      const vendorData = prev[activeUploadVendor] || { email: null, quotation: null, contract: null, meeting_notes: null };
      return {
        ...prev,
        [activeUploadVendor]: {
          ...vendorData,
          [type]: file
        }
      };
    });
    // Clear input value so that selecting files with the same filename triggers onChange again
    e.target.value = "";
  };

  const handleRemoveFile = (type) => {
    setVendorUploadedFiles(prev => {
      const vendorData = prev[activeUploadVendor] || { email: null, quotation: null, contract: null, meeting_notes: null };
      return {
        ...prev,
        [activeUploadVendor]: {
          ...vendorData,
          [type]: null
        }
      };
    });
  };

  // Trigger analysis pipeline
  const startAnalysis = async () => {
    if (selectedVendors.length === 0) {
      alert("Please add at least one vendor to compare.");
      return;
    }
    if (!category) {
      alert("Please select a procurement category.");
      return;
    }
    if (!priority) {
      alert("Please select a target priority goal (Cost, Delivery, or Quality).");
      return;
    }
    if (!department) {
      alert("Please select a department.");
      return;
    }
    if (!budget || parseFloat(budget) <= 0) {
      alert("Please enter a valid estimated project budget.");
      return;
    }
    
    setLoading(true);
    setDecisionState(null);
    setDecisionOutcome(null);
    setActiveRiskVendor("");
    setAnalysisError("");
    
    const activeSessionId = sessionId || `session_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(activeSessionId);
    setActiveTab("execution");

    try {
      // 1. Upload all selected files to the backend per vendor
      let filesUploaded = 0;
      for (const vName of selectedVendors) {
        const vFiles = vendorUploadedFiles[vName] || {};
        for (const [docType, file] of Object.entries(vFiles)) {
          if (file) {
            const formData = new FormData();
            formData.append("file", file);
            formData.append("session_id", activeSessionId);
            formData.append("doc_type", docType === "meeting_notes" ? "meeting_notes" : docType);
            formData.append("vendor_name", vName);
            
            await axios.post(`${API_BASE_URL}/upload`, formData);
            filesUploaded++;
          }
        }
      }

      // 2. Start the analysis background task
      const analyzeResponse = await axios.post(`${API_BASE_URL}/analyze/${activeSessionId}`, {
        selected_vendors: selectedVendors,
        requirements: {
          category,
          priority,
          department,
          budget: parseFloat(budget) || 125000,
          custom_rules: customRules
        }
      });
      setDecisionState(analyzeResponse.data);
      setOfflineMode(false);

      // 3. Start polling the decision state every 1 second
      const timer = setInterval(async () => {
        try {
          const pollResponse = await axios.get(`${API_BASE_URL}/decision/${activeSessionId}`);
          const state = pollResponse.data;
          setDecisionState(state);
          
          // Check if all agents are finished (none are pending or running)
          const activeTimeline = state.agent_timeline || [];
          const runningOrPending = activeTimeline.some(
            agent => agent.status === "pending" || agent.status === "running"
          );
          
          if (!runningOrPending && activeTimeline.length > 0) {
            clearInterval(timer);
            setLoading(false);
          }
        } catch (pollErr) {
          console.error("Polling error:", pollErr);
        }
      }, 1000);
      
      setTimelineTimer(timer);

    } catch (err) {
      setLoading(false);
      const errMsg = err.response?.data?.detail || "Validation error. Please verify all document uploads.";
      setAnalysisError(errMsg);
      if (err.response && err.response.status === 400) {
        alert(errMsg);
        setActiveTab("dashboard");
      } else {
        console.warn("Backend server offline. Falling back to client-side simulation.", err);
        setOfflineMode(true);
        runOfflineSimulation(activeSessionId);
      }
    }
  };

  // Client-side simulation mode for demo presentations
  const runOfflineSimulation = (activeSessionId) => {
    const agents = [];
    selectedVendors.forEach(name => {
      agents.push({ agent_name: `${name}: Cognitive Analysis Suite`, status: "pending" });
    });
    agents.push({ agent_name: "Multi-Vendor Recommendation Agent", status: "pending" });

    let mockState = {
      session_id: activeSessionId,
      uploaded_files: [],
      agent_timeline: agents,
      requirements: {
        category,
        priority,
        department,
        budget: parseFloat(budget) || 125000,
        custom_rules: customRules
      },
      rejected_vendors: [],
      recommended_vendor_name: selectedVendors[0]
    };

    setDecisionState(mockState);
    
    let currentStep = 0;
    const interval = setInterval(() => {
      if (currentStep < selectedVendors.length) {
        const name = selectedVendors[currentStep];
        mockState.agent_timeline = mockState.agent_timeline.map((agent, idx) => {
          if (idx === currentStep) return { ...agent, status: "running" };
          return agent;
        });
        setDecisionState({ ...mockState });
        
        setTimeout(() => {
          mockState.agent_timeline = mockState.agent_timeline.map((agent, idx) => {
            if (idx === currentStep) return { ...agent, status: "completed", duration_ms: 250 };
            return agent;
          });
          setDecisionState({ ...mockState });
        }, 150);
        
        currentStep++;
      } else if (currentStep === selectedVendors.length) {
        // Run recommendation agent
        mockState.agent_timeline = mockState.agent_timeline.map((agent, idx) => {
          if (idx === selectedVendors.length) return { ...agent, status: "running" };
          return agent;
        });
        setDecisionState({ ...mockState });
        
        setTimeout(() => {
          mockState.agent_timeline = mockState.agent_timeline.map((agent, idx) => {
            if (idx === selectedVendors.length) return { ...agent, status: "completed", duration_ms: 180 };
            return agent;
          });
          
          const matrix = selectedVendors.map((name, idx) => {
            let price = 115000 + idx * 15000;
            if (name === "Suresh") price = 120000;
            if (name === "Naresh") price = 115000;
            if (name === "Kumar") price = 130000;
            if (name === "Rahul") price = 118000;
            
            return {
              vendor: name,
              price: price,
              compliance: name === "Kumar" ? "Non-Compliant" : (name === "Suresh" ? "Conditional" : "Compliant"),
              risk: name === "Naresh" ? "Low" : (name === "Kumar" ? "Medium" : "Low"),
              risk_score: name === "Naresh" ? 15.5 : (name === "Kumar" ? 45.0 : 25.0),
              performance: name === "Naresh" ? 4.9 : (name === "Suresh" ? 4.8 : 3.5),
              lead_time: name === "Naresh" ? "7 days" : "14 days",
              status: idx === 0 ? "Recommended" : "Alternative"
            };
          });
          
          mockState.comparison_matrix = matrix;
          mockState.recommended_vendor_name = selectedVendors[0];
          
          mockState.quote_data = {
            total_amount: matrix[0].price,
            unit_price: matrix[0].price / 100,
            delivery_timeline: matrix[0].lead_time,
            vendor_name: selectedVendors[0]
          };
          
          mockState.policy_checks = {
            compliance_status: matrix[0].compliance,
            purchase_limit_exceeded: matrix[0].price > 100000.0,
            vendor_blacklisted: false,
            relevant_policies: ["Payment terms override check"]
          };
          
          mockState.risk_assessment = {
            overall_risk: matrix[0].risk_score,
            risk_level: matrix[0].risk,
            delivery_risk: 10.0,
            financial_risk: 20.0,
            legal_risk: 12.0,
            risk_factors: ["Lead time complies with SLA limits."]
          };
          
          mockState.reasoning = {
            situation_summary: `Comparative review of ${selectedVendors.join(", ")}. ${selectedVendors[0]} offers the best score based on ${priority} priority.`
          };
          
          mockState.next_best_action = {
            recommendations: [
              {
                action: `Approve contract with ${selectedVendors[0]} for ${category} procurement.`,
                confidence: 95.0,
                reason: `Top ranked vendor with compliance approval, lowest risk and best price term.`,
                evidence: {
                  price_justification: { source: "Quote Agent", fact: `Unit price is highly favorable.` }
                },
                alternative: selectedVendors[1] ? `Switch to ${selectedVendors[1]} as second choice.` : "No alternatives."
              }
            ],
            final_decision_tier: "Tier 1 (Purchaser)"
          };
          
          setDecisionState({ ...mockState });
          clearInterval(interval);
          setLoading(false);
        }, 150);
        currentStep++;
      }
    }, 1000);
    
    setTimelineTimer(interval);
  };

  // Submit human response
  const submitDecision = async (status) => {
    setLoading(true);
    try {
      if (!offlineMode) {
        if (timelineTimer) clearInterval(timelineTimer);
        
        await axios.post(`${API_BASE_URL}/decision/${sessionId}/action`, null, {
          params: { action: status, notes: approvalNotes }
        });
        
        if (status === "Approved") {
          // Fetch updated decision state
          const pollResponse = await axios.get(`${API_BASE_URL}/decision/${sessionId}`);
          setDecisionState(pollResponse.data);
          
          // Fetch fresh logs
          const freshLogs = await axios.get(`${API_BASE_URL}/audit-trail`);
          setAuditLogs(freshLogs.data);
          setDecisionOutcome(status);
          setActiveTab("history");
          setLoading(false);
        } else {
          setApprovalNotes("");
          setActiveTab("execution");
          
          // Start polling the decision state for re-evaluation progress
          const timer = setInterval(async () => {
            try {
              const pollResponse = await axios.get(`${API_BASE_URL}/decision/${sessionId}`);
              const state = pollResponse.data;
              setDecisionState(state);
              
              // Check if all agents are finished (none are pending or running)
              const activeTimeline = state.agent_timeline || [];
              const runningOrPending = activeTimeline.some(
                agent => agent.status === "pending" || agent.status === "running"
              );
              
              if (!runningOrPending && activeTimeline.length > 0) {
                clearInterval(timer);
                setLoading(false);
                alert(`Deal rejected. Dynamic suggest loop recommends: ${state.recommended_vendor_name}`);
              }
            } catch (pollErr) {
              console.error("Polling error:", pollErr);
            }
          }, 1000);
          
          setTimelineTimer(timer);
        }
      } else {
        if (status === "Rejected") {
          const currentRec = decisionState.recommended_vendor_name;
          const nextIndex = selectedVendors.indexOf(currentRec) + 1;
          if (nextIndex < selectedVendors.length) {
            const nextRec = selectedVendors[nextIndex];
            
            const updatedMatrix = decisionState.comparison_matrix.map(row => {
              if (row.vendor === currentRec) return { ...row, status: "Rejected" };
              if (row.vendor === nextRec) return { ...row, status: "Recommended" };
              return row;
            });
            
            setDecisionState(prev => ({
              ...prev,
              recommended_vendor_name: nextRec,
              rejected_vendors: [...prev.rejected_vendors, currentRec],
              comparison_matrix: updatedMatrix,
              quote_data: {
                total_amount: 125000,
                unit_price: 1250.00,
                delivery_timeline: "14 calendar days",
                vendor_name: nextRec
              },
              policy_checks: {
                compliance_status: "Compliant",
                purchase_limit_exceeded: false,
                vendor_blacklisted: false,
                relevant_policies: ["Alternate vendor compliance check"]
              },
              risk_assessment: {
                overall_risk: 25.0,
                risk_level: "Low",
                delivery_risk: 15.0,
                financial_risk: 10.0,
                legal_risk: 12.0,
                risk_factors: ["Terms match Net 30 corporate standards."]
              },
              reasoning: {
                situation_summary: `Alternative suggested: ${nextRec} after primary selection ${currentRec} was rejected.`
              },
              next_best_action: {
                recommendations: [
                  {
                    action: `Approve contract with ${nextRec} for ${category} procurement. (Alternative)`,
                    confidence: 88.0,
                    reason: `Suggested alternative after rejecting ${currentRec}.`,
                    evidence: {
                      price_justification: { source: "Quote Agent", fact: `Alternate quote matches specifications.` }
                    },
                    alternative: selectedVendors[nextIndex + 1] ? `Switch to ${selectedVendors[nextIndex + 1]}.` : "No more options."
                  }
                ],
                final_decision_tier: "Tier 1 (Purchaser)"
              }
            }));
            
            setApprovalNotes("");
            alert(`Deal rejected. Suggested alternative: ${nextRec}`);
          } else {
            alert("All evaluated vendors have been rejected!");
          }
          setLoading(false);
        } else {
          const newLog = {
            session_id: sessionId.substring(0, 15),
            vendor: decisionState.recommended_vendor_name,
            category: category,
            budget: parseFloat(budget).toLocaleString(),
            recommendation: decisionState.next_best_action?.recommendations[0]?.action || "Review required",
            status: status,
            timestamp: new Date().toISOString().replace('T', ' ').substring(0, 16)
          };
          setAuditLogs(prev => [newLog, ...prev]);
          setDecisionOutcome(status);
          setLoading(false);
          setActiveTab("history");
        }
      }
    } catch (err) {
      console.error("Action submit failed", err);
      setLoading(false);
    }
  };

  const getStatusDotColor = (status) => {
    switch (status) {
      case "completed": return "var(--status-completed)";
      case "running": return "var(--status-running)";
      case "skipped": return "var(--status-skipped)";
      case "failed": return "var(--status-failed)";
      default: return "var(--status-pending)";
    }
  };

  if (!token) {
    return (
      <div className="app-container" style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh", background: "var(--bg-primary)" }}>
        <div className="glow-card" style={{ width: "100%", maxWidth: "420px", padding: "32px", display: "flex", flexDirection: "column", gap: "24px" }}>
          
          {/* Logo */}
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
            <div style={{
              width: "48px",
              height: "48px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, var(--accent-blue), var(--accent-cyan))",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 20px rgba(0, 242, 254, 0.3)"
            }}>
              <Sparkles style={{ width: "24px", height: "24px", color: "#000" }} fill="black" />
            </div>
            <h2 style={{ fontSize: "22px", fontWeight: "800", color: "#fff", margin: 0, tracking: "0.05em" }}>VendorMind AI</h2>
            <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>Enterprise Procurement Decision Suite</span>
          </div>

          {/* Tab Toggles */}
          <div style={{ display: "flex", borderBottom: "1px solid var(--border-color)", paddingBottom: "2px" }}>
            <button
              onClick={() => { setAuthTab("signin"); setAuthError(""); }}
              className={`nav-item ${authTab === "signin" ? "active" : ""}`}
              style={{ flex: 1, paddingBottom: "10px", fontSize: "14px", fontWeight: "600", borderBottom: authTab === "signin" ? "2px solid var(--accent-cyan)" : "none", color: authTab === "signin" ? "#fff" : "var(--text-secondary)" }}
            >
              Sign In
            </button>
            <button
              onClick={() => { setAuthTab("signup"); setAuthError(""); }}
              className={`nav-item ${authTab === "signup" ? "active" : ""}`}
              style={{ flex: 1, paddingBottom: "10px", fontSize: "14px", fontWeight: "600", borderBottom: authTab === "signup" ? "2px solid var(--accent-cyan)" : "none", color: authTab === "signup" ? "#fff" : "var(--text-secondary)" }}
            >
              Create Account
            </button>
          </div>

          {/* Form */}
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {authError && (
              <div style={{ backgroundColor: "rgba(255, 75, 75, 0.1)", border: "1px solid var(--status-failed)", padding: "10px", borderRadius: "6px", color: "var(--status-failed)", fontSize: "12px", display: "flex", alignItems: "center", gap: "6px" }}>
                <AlertTriangle style={{ width: "16px", height: "16px" }} />
                {authError}
              </div>
            )}

            {authTab === "signup" && (
              <div className="input-group">
                <label className="input-label">Full Name</label>
                <input
                  type="text"
                  value={fullNameInput}
                  onChange={(e) => setFullNameInput(e.target.value)}
                  className="form-input"
                  placeholder="e.g., Harsha Yekkirala"
                />
              </div>
            )}

            <div className="input-group">
              <label className="input-label">Username / Corporate Email</label>
              <input
                type="text"
                value={usernameInput}
                onChange={(e) => setUsernameInput(e.target.value)}
                className="form-input"
                placeholder="username"
              />
            </div>

            <div className="input-group">
              <label className="input-label">Password</label>
              <input
                type="password"
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                className="form-input"
                placeholder="••••••••"
              />
            </div>

            <button
              onClick={async () => {
                setAuthError("");
                if (!usernameInput || !passwordInput) {
                  setAuthError("Please fill in all credentials.");
                  return;
                }
                try {
                  if (authTab === "signin") {
                    const response = await axios.post(`${API_BASE_URL.replace("/api/v1", "")}/api/v1/auth/login`, {
                      username: usernameInput,
                      password: passwordInput
                    });
                    setToken(response.data.token);
                    setCurrentUser(response.data.full_name || response.data.username);
                  } else {
                    await axios.post(`${API_BASE_URL.replace("/api/v1", "")}/api/v1/auth/signup`, {
                      username: usernameInput,
                      password: passwordInput,
                      full_name: fullNameInput || null
                    });
                    alert("Account registered successfully! Please sign in.");
                    setAuthTab("signin");
                    setFullNameInput("");
                  }
                } catch (err) {
                  setAuthError(err.response?.data?.detail || "Authentication request failed.");
                }
              }}
              className="btn-primary"
              style={{ marginTop: "10px", width: "100%", justifyContent: "center" }}
            >
              {authTab === "signin" ? "Sign In" : "Register Account"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      
      {/* ========================================== */}
      {/* 🧭 SIDEBAR PANEL */}
      {/* ========================================== */}
      <aside className="sidebar">
        <div>
          {/* Brand Logo */}
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "40px" }}>
            <div style={{
              width: "36px",
              height: "36px",
              borderRadius: "8px",
              background: "linear-gradient(135deg, var(--accent-blue), var(--accent-cyan))",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 4px 15px rgba(0, 242, 254, 0.15)"
            }}>
              <Sparkles style={{ width: "20px", height: "20px", color: "#000" }} />
            </div>
            <div>
              <h2 style={{ fontSize: "16px", fontWeight: "700", letterSpacing: "1px", margin: 0 }}>
                VendorMind AI
              </h2>
              <span style={{ fontSize: "9px", color: "var(--accent-cyan)", fontWeight: "700", letterSpacing: "1.5px", textTransform: "uppercase" }}>
                Decision Hub
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="nav-list">
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`nav-item ${activeTab === "dashboard" ? "active" : ""}`}
            >
              <span style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <FileText style={{ width: "16px", height: "16px" }} />
                Upload & Setup
              </span>
            </button>
            <button
              onClick={() => { if (decisionState) setActiveTab("execution"); }}
              disabled={!decisionState}
              className={`nav-item ${activeTab === "execution" ? "active" : ""}`}
            >
              <span style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <Clock style={{ width: "16px", height: "16px" }} />
                Orchestrator
              </span>
              {loading && <span style={{
                width: "6px",
                height: "6px",
                borderRadius: "50%",
                background: "var(--accent-cyan)",
                boxShadow: "0 0 8px var(--accent-cyan)"
              }} />}
            </button>
            <button
              onClick={() => { if (decisionState?.risk_assessment) setActiveTab("risk"); }}
              disabled={!decisionState?.risk_assessment}
              className={`nav-item ${activeTab === "risk" ? "active" : ""}`}
            >
              <span style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <ShieldAlert style={{ width: "16px", height: "16px" }} />
                Risk & Compliance
              </span>
            </button>
            <button
              onClick={() => { if (decisionState?.next_best_action) setActiveTab("recommendations"); }}
              disabled={!decisionState?.next_best_action}
              className={`nav-item ${activeTab === "recommendations" ? "active" : ""}`}
            >
              <span style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <Award style={{ width: "16px", height: "16px" }} />
                Decision Engine
              </span>
            </button>
            <button
              onClick={() => setActiveTab("history")}
              className={`nav-item ${activeTab === "history" ? "active" : ""}`}
            >
              <span style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <History style={{ width: "16px", height: "16px" }} />
                Audit Logs
              </span>
            </button>
            <button
              onClick={() => setActiveTab("vendors")}
              className={`nav-item ${activeTab === "vendors" ? "active" : ""}`}
            >
              <span style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <Users style={{ width: "16px", height: "16px" }} />
                Vendor Directory
              </span>
            </button>
            <button
              onClick={() => setActiveTab("policies_admin")}
              className={`nav-item ${activeTab === "policies_admin" ? "active" : ""}`}
            >
              <span style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <Lock style={{ width: "16px", height: "16px" }} />
                Compliance Policies
              </span>
            </button>
          </nav>
        </div>

        {/* User Session Profile Badge & Logout */}
        {token && (
          <div style={{ borderTop: "1px solid var(--border-color)", paddingTop: "16px", marginBottom: "16px", display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div style={{
                width: "32px",
                height: "32px",
                borderRadius: "50%",
                background: "linear-gradient(135deg, var(--accent-blue), var(--accent-cyan))",
                color: "#000",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: "700",
                fontSize: "12px"
              }}>
                {(currentUser || "P").substring(0, 2).toUpperCase()}
              </div>
              <div style={{ display: "flex", flexDirection: "column" }}>
                <span style={{ fontSize: "12.5px", color: "#fff", fontWeight: "600", maxWidth: "140px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {currentUser || "Procurer"}
                </span>
                <span style={{ fontSize: "9px", color: "var(--accent-cyan)", tracking: "0.05em", textTransform: "uppercase" }}>
                  Active Session
                </span>
              </div>
            </div>
            <button
              onClick={() => {
                setToken("");
                setCurrentUser("");
                setUsernameInput("");
                setPasswordInput("");
                setActiveTab("dashboard");
                setDecisionState(null);
                setDecisionOutcome(null);
              }}
              className="btn-secondary"
              style={{
                padding: "6px 12px",
                fontSize: "11.5px",
                borderColor: "rgba(255, 75, 75, 0.4)",
                color: "var(--status-failed)",
                width: "100%",
                justifyContent: "center"
              }}
            >
              Sign Out
            </button>
          </div>
        )}

        {/* System Health Status */}
        <div style={{ borderTop: "1px solid var(--border-color)", paddingTop: "24px" }}>
          <div style={{ backgroundColor: "rgba(255,255,255,0.01)", border: "1px solid var(--border-color)", borderRadius: "8px", padding: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
              <span style={{ fontSize: "11px", color: "var(--text-secondary)", fontWeight: "600" }}>FastAPI Server</span>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: offlineMode ? '#f59e0b' : '#10b981' }} />
                <span style={{ fontSize: "9px", color: "var(--text-secondary)", fontWeight: "700" }}>{offlineMode ? 'SIMULATOR' : 'ONLINE'}</span>
              </div>
            </div>
            <p style={{ fontSize: "11px", color: "var(--text-muted)", margin: 0, lineHeight: "1.4" }}>
              {offlineMode ? 'Running client-side AI mock generation pipeline.' : 'Successfully connected to backend API.'}
            </p>
          </div>
        </div>
      </aside>

      {/* ========================================== */}
      {/* 🖥️ MAIN VIEW WORKSPACE */}
      {/* ========================================== */}
      <main className="main-workspace">
        
        {/* Main Application Header */}
        <header className="app-header">
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <h1 style={{ fontSize: "18px", letterSpacing: "-0.3px" }}>
              {activeTab === "dashboard" ? "Procurement Analytics Dashboard" : activeTab === "vendors" ? "Vendor Directory & Profiles" : `${activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Workspace`}
            </h1>
            {sessionId && (
              <span style={{ fontSize: "11px", fontFamily: "monospace", backgroundColor: "rgba(255,255,255,0.03)", padding: "4px 8px", borderRadius: "4px", border: "1px solid var(--border-color)", color: "var(--text-secondary)" }}>
                ID: {sessionId}
              </span>
            )}
          </div>
          
          <div>
            <button 
              onClick={() => {
                setSessionId("");
                setDecisionState(null);
                setVendorUploadedFiles({});
                setSelectedVendors([]);
                setActiveUploadVendor("");
                setActiveRiskVendor("");
                setCategory("");
                setPriority("");
                setDepartment("");
                setBudget("");
                setActiveTab("dashboard");
              }}
              className="btn-secondary"
              style={{ display: "flex", alignItems: "center", gap: "6px" }}
            >
              <RefreshCw style={{ width: "12px", height: "12px" }} />
              Reset Session
            </button>
          </div>
        </header>

        {/* Content Workspace Area */}
        <div className="content-area">
          <div className="max-width-wrapper">
            
            {/* ========================================== */}
            {/* TAB 1: UPLOAD & SETUP */}
            {/* ========================================== */}
            {activeTab === "dashboard" && (
              <>
                {analysisError && (
                  <div className="glow-card" style={{
                    border: "1px solid var(--status-failed)",
                    background: "rgba(255, 75, 75, 0.05)",
                    padding: "16px 20px",
                    marginBottom: "24px",
                    borderRadius: "8px",
                    color: "var(--status-failed)",
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    fontSize: "14px",
                    fontWeight: "600"
                  }}>
                    <AlertTriangle style={{ width: "20px", height: "20px", flexShrink: 0 }} />
                    <div style={{ flex: 1 }}>{analysisError}</div>
                    <button 
                      onClick={() => setAnalysisError("")}
                      style={{ background: "none", border: "none", color: "var(--status-failed)", cursor: "pointer", fontSize: "16px", fontWeight: "700" }}
                    >
                      ×
                    </button>
                  </div>
                )}

                {/* Configuration Bar */}
                <div className="glow-card config-bar" style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "20px" }}>
                  <div className="input-group" style={{ gridColumn: "span 3" }}>
                    <label className="input-label" style={{ marginBottom: "8px" }}>Vendors to Compare (Add Dynamically)</label>
                    <div style={{ display: "flex", gap: "10px", marginBottom: "16px" }}>
                      <input
                        type="text"
                        value={newVendorName}
                        onChange={(e) => setNewVendorName(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            handleAddVendor();
                          }
                        }}
                        className="form-input"
                        placeholder="Type vendor name (e.g. Suresh, Naresh, Globex Corp)..."
                        style={{ flex: 1 }}
                      />
                      <button
                        onClick={handleAddVendor}
                        className="btn-primary"
                        style={{ padding: "0 18px", fontSize: "13px" }}
                      >
                        + Add Vendor
                      </button>
                    </div>

                    {/* Chips list */}
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                      {selectedVendors.map((v) => (
                        <div
                          key={v}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            backgroundColor: "rgba(0, 242, 254, 0.08)",
                            border: "1px solid var(--accent-cyan)",
                            padding: "6px 12px",
                            borderRadius: "6px",
                            fontSize: "12.5px",
                            color: "#fff"
                          }}
                        >
                          <span style={{ fontWeight: "600" }}>{v}</span>
                          <button
                            onClick={() => handleRemoveVendor(v)}
                            style={{
                              background: "none",
                              border: "none",
                              color: "var(--text-secondary)",
                              cursor: "pointer",
                              fontSize: "13px",
                              padding: "0 2px",
                              display: "flex",
                              alignItems: "center"
                            }}
                            title="Remove vendor"
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="input-group">
                    <label className="input-label">Category</label>
                    <select
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      className="form-input"
                    >
                      <option value="">Select Category...</option>
                      <option>Software</option>
                      <option>Hardware</option>
                      <option>Consulting</option>
                      <option>Equipment</option>
                    </select>
                  </div>

                  <div className="input-group">
                    <label className="input-label">Target Priority</label>
                    <div className="priority-container">
                      {["Cost", "Delivery", "Quality"].map((p) => (
                        <button
                          key={p}
                          onClick={() => setPriority(p)}
                          className={`priority-btn ${priority === p ? "active" : ""}`}
                        >
                          {p}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="input-group">
                    <label className="input-label">Department</label>
                    <select
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                      className="form-input"
                    >
                      <option value="">Select Department...</option>
                      <option>IT</option>
                      <option>HR</option>
                      <option>Finance</option>
                      <option>Operations</option>
                    </select>
                  </div>

                  <div className="input-group" style={{ gridColumn: "span 3" }}>
                    <label className="input-label">Estimated Project Budget ($)</label>
                    <input
                      type="number"
                      value={budget}
                      onChange={(e) => setBudget(e.target.value)}
                      className="form-input"
                    />
                  </div>
                </div>

                {/* Custom Requirements Glow Card */}
                <div className="glow-card" style={{ marginTop: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
                  <h3 style={{ fontSize: "14px", margin: 0, fontWeight: "700", display: "flex", alignItems: "center", gap: "8px" }}>
                    <Sparkles style={{ width: "16px", height: "16px", color: "var(--accent-cyan)" }} />
                    Custom Procurement Requirements & Rules
                  </h3>
                  <textarea
                    value={customRules}
                    onChange={(e) => setCustomRules(e.target.value)}
                    className="form-input"
                    style={{ height: "70px", resize: "vertical", width: "100%", boxSizing: "border-box", fontSize: "12.5px" }}
                    placeholder="E.g., Vendor must have SOC 2 or ISO 27001 certification. Delivery timeline must be under 14 days..."
                  />
                </div>

                {/* Upload File Deck */}
                <div style={{ marginTop: "24px" }}>
                  <h3 style={{ fontSize: "16px", marginBottom: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
                    <Upload style={{ width: "18px", height: "18px", color: "var(--accent-cyan)" }} />
                    Upload Deal Documentation for Selected Vendors
                  </h3>
                  
                  {/* Tabs Selector */}
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "20px", borderBottom: "1px solid var(--border-color)", paddingBottom: "12px" }}>
                    {selectedVendors.map(v => (
                      <button
                        key={v}
                        onClick={() => setActiveUploadVendor(v)}
                        className={`nav-item ${activeUploadVendor === v ? "active" : ""}`}
                        style={{
                          padding: "6px 14px",
                          fontSize: "13px",
                          borderRadius: "6px",
                          border: activeUploadVendor === v ? "1px solid var(--accent-cyan)" : "1px solid transparent",
                          backgroundColor: activeUploadVendor === v ? "rgba(0, 242, 254, 0.05)" : "transparent"
                        }}
                      >
                        {v}
                        <span style={{
                          marginLeft: "8px",
                          fontSize: "10px",
                          backgroundColor: "rgba(255,255,255,0.08)",
                          padding: "2px 6px",
                          borderRadius: "10px",
                          color: "var(--text-secondary)"
                        }}>
                          {Object.values(vendorUploadedFiles[v] || {}).filter(Boolean).length}
                        </span>
                      </button>
                    ))}
                  </div>

                  {activeUploadVendor && selectedVendors.includes(activeUploadVendor) && (
                    <div>
                      <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginBottom: "16px" }}>
                        Currently uploading files for <strong>{activeUploadVendor}</strong>. If no files are uploaded, default catalog specifications will be simulated.
                      </div>
                      
                      <div className="upload-grid">
                        
                        {/* File Upload Slot 1: Email */}
                        <div className={`upload-card ${vendorUploadedFiles[activeUploadVendor]?.email ? 'success' : ''}`} style={{ position: "relative" }}>
                          {vendorUploadedFiles[activeUploadVendor]?.email && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                e.preventDefault();
                                handleRemoveFile("email");
                              }}
                              style={{
                                position: "absolute",
                                top: "8px",
                                right: "8px",
                                background: "rgba(255, 255, 255, 0.1)",
                                border: "none",
                                color: "#ff4d4d",
                                borderRadius: "50%",
                                width: "22px",
                                height: "22px",
                                cursor: "pointer",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                fontWeight: "bold",
                                zIndex: 10
                              }}
                            >
                              ×
                            </button>
                          )}
                          <input
                            type="file"
                            id="upload-email"
                            style={{ display: "none" }}
                            onChange={(e) => handleFileChange("email", e)}
                          />
                          <label htmlFor="upload-email" style={{ cursor: "pointer", display: "flex", flexDirection: "column", alignItems: "center", gap: "10px" }}>
                            {vendorUploadedFiles[activeUploadVendor]?.email ? (
                              <>
                                <CheckCircle style={{ width: "32px", height: "32px", color: "var(--status-completed)" }} />
                                <span style={{ fontSize: "13px", fontWeight: "600", color: "#fff" }}>Email Uploaded</span>
                                <span style={{ fontSize: "10px", color: "var(--text-muted)", maxWidth: "160px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{vendorUploadedFiles[activeUploadVendor].email.name}</span>
                              </>
                            ) : (
                              <>
                                <Upload style={{ width: "24px", height: "24px", color: "var(--text-secondary)" }} />
                                <span style={{ fontSize: "13.5px", fontWeight: "600", color: "#fff" }}>Vendor Email</span>
                                <span style={{ fontSize: "11px", color: "var(--text-secondary)" }}>Attach negotiations/promises</span>
                              </>
                            )}
                          </label>
                        </div>

                        {/* File Upload Slot 2: Quote */}
                        <div className={`upload-card ${vendorUploadedFiles[activeUploadVendor]?.quotation ? 'success' : ''}`} style={{ position: "relative" }}>
                          {vendorUploadedFiles[activeUploadVendor]?.quotation && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                e.preventDefault();
                                handleRemoveFile("quotation");
                              }}
                              style={{
                                position: "absolute",
                                top: "8px",
                                right: "8px",
                                background: "rgba(255, 255, 255, 0.1)",
                                border: "none",
                                color: "#ff4d4d",
                                borderRadius: "50%",
                                width: "22px",
                                height: "22px",
                                cursor: "pointer",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                fontWeight: "bold",
                                zIndex: 10
                              }}
                            >
                              ×
                            </button>
                          )}
                          <input
                            type="file"
                            id="upload-quote"
                            style={{ display: "none" }}
                            onChange={(e) => handleFileChange("quotation", e)}
                          />
                          <label htmlFor="upload-quote" style={{ cursor: "pointer", display: "flex", flexDirection: "column", alignItems: "center", gap: "10px" }}>
                            {vendorUploadedFiles[activeUploadVendor]?.quotation ? (
                              <>
                                <CheckCircle style={{ width: "32px", height: "32px", color: "var(--status-completed)" }} />
                                <span style={{ fontSize: "13px", fontWeight: "600", color: "#fff" }}>Quote Uploaded</span>
                                <span style={{ fontSize: "10px", color: "var(--text-muted)", maxWidth: "160px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{vendorUploadedFiles[activeUploadVendor].quotation.name}</span>
                              </>
                            ) : (
                              <>
                                <Upload style={{ width: "24px", height: "24px", color: "var(--text-secondary)" }} />
                                <span style={{ fontSize: "13.5px", fontWeight: "600", color: "#fff" }}>Quotation PDF</span>
                                <span style={{ fontSize: "11px", color: "var(--text-secondary)" }}>Mandatory for pricing review</span>
                              </>
                            )}
                          </label>
                        </div>

                        {/* File Upload Slot 3: Contract */}
                        <div className={`upload-card ${vendorUploadedFiles[activeUploadVendor]?.contract ? 'success' : ''}`} style={{ position: "relative" }}>
                          {vendorUploadedFiles[activeUploadVendor]?.contract && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                e.preventDefault();
                                handleRemoveFile("contract");
                              }}
                              style={{
                                position: "absolute",
                                top: "8px",
                                right: "8px",
                                background: "rgba(255, 255, 255, 0.1)",
                                border: "none",
                                color: "#ff4d4d",
                                borderRadius: "50%",
                                width: "22px",
                                height: "22px",
                                cursor: "pointer",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                fontWeight: "bold",
                                zIndex: 10
                              }}
                            >
                              ×
                            </button>
                          )}
                          <input
                            type="file"
                            id="upload-contract"
                            style={{ display: "none" }}
                            onChange={(e) => handleFileChange("contract", e)}
                          />
                          <label htmlFor="upload-contract" style={{ cursor: "pointer", display: "flex", flexDirection: "column", alignItems: "center", gap: "10px" }}>
                            {vendorUploadedFiles[activeUploadVendor]?.contract ? (
                              <>
                                <CheckCircle style={{ width: "32px", height: "32px", color: "var(--status-completed)" }} />
                                <span style={{ fontSize: "13px", fontWeight: "600", color: "#fff" }}>Contract Uploaded</span>
                                <span style={{ fontSize: "10px", color: "var(--text-muted)", maxWidth: "160px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{vendorUploadedFiles[activeUploadVendor].contract.name}</span>
                              </>
                            ) : (
                              <>
                                <Upload style={{ width: "24px", height: "24px", color: "var(--text-secondary)" }} />
                                <span style={{ fontSize: "13.5px", fontWeight: "600", color: "#fff" }}>Contract Agreement</span>
                                <span style={{ fontSize: "11px", color: "var(--text-secondary)" }}>SLA limits and penalties</span>
                              </>
                            )}
                          </label>
                        </div>

                        {/* File Upload Slot 4: Meeting Notes */}
                        <div className={`upload-card ${vendorUploadedFiles[activeUploadVendor]?.meeting_notes ? 'success' : ''}`} style={{ position: "relative" }}>
                          {vendorUploadedFiles[activeUploadVendor]?.meeting_notes && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                e.preventDefault();
                                handleRemoveFile("meeting_notes");
                              }}
                              style={{
                                position: "absolute",
                                top: "8px",
                                right: "8px",
                                background: "rgba(255, 255, 255, 0.1)",
                                border: "none",
                                color: "#ff4d4d",
                                borderRadius: "50%",
                                width: "22px",
                                height: "22px",
                                cursor: "pointer",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                fontWeight: "bold",
                                zIndex: 10
                              }}
                            >
                              ×
                            </button>
                          )}
                          <input
                            type="file"
                            id="upload-meeting"
                            style={{ display: "none" }}
                            onChange={(e) => handleFileChange("meeting_notes", e)}
                          />
                          <label htmlFor="upload-meeting" style={{ cursor: "pointer", display: "flex", flexDirection: "column", alignItems: "center", gap: "10px" }}>
                            {vendorUploadedFiles[activeUploadVendor]?.meeting_notes ? (
                              <>
                                <CheckCircle style={{ width: "32px", height: "32px", color: "var(--status-completed)" }} />
                                <span style={{ fontSize: "13px", fontWeight: "600", color: "#fff" }}>Notes Uploaded</span>
                                <span style={{ fontSize: "10px", color: "var(--text-muted)", maxWidth: "160px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{vendorUploadedFiles[activeUploadVendor].meeting_notes.name}</span>
                              </>
                            ) : (
                              <>
                                <Upload style={{ width: "24px", height: "24px", color: "var(--text-secondary)" }} />
                                <span style={{ fontSize: "13.5px", fontWeight: "600", color: "#fff" }}>Meeting Transcript</span>
                                <span style={{ fontSize: "11px", color: "var(--text-secondary)" }}>Verbal agreements tracker</span>
                              </>
                            )}
                          </label>
                        </div>

                      </div>
                    </div>
                  )}
                </div>

                {/* Submit Trigger */}
                <div style={{ display: "flex", justifyContent: "center", marginTop: "32px" }}>
                  <button onClick={startAnalysis} className="btn-primary">
                    <Play style={{ width: "16px", height: "16px", color: "#000" }} fill="black" />
                    Initiate AI Procurement Analysis
                  </button>
                </div>
              </>
            )}

            {/* ========================================== */}
            {/* TAB 2: AGENT TIMELINE PROGRESS */}
            {/* ========================================== */}
            {activeTab === "execution" && decisionState && (
              <div className="glow-card">
                <h3 style={{ fontSize: "16px", marginBottom: "24px", display: "flex", alignItems: "center", gap: "8px" }}>
                  <RefreshCw style={{ width: "16px", height: "16px", color: "var(--accent-cyan)" }} className="animate-spin-slow" />
                  Planner Orchestration Sequence
                </h3>

                <div className="timeline-container">
                  {decisionState.agent_timeline?.map((agent, index) => (
                    <div key={index} className="timeline-row">
                      {/* Left Dot */}
                      <span 
                        className="timeline-dot" 
                        style={{ backgroundColor: getStatusDotColor(agent.status) }} 
                      />

                      <div>
                        <h4 style={{ fontSize: "14px", fontWeight: "600", color: "#fff" }}>{agent.agent_name}</h4>
                        <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                          Execution node tracking
                        </span>
                      </div>
                      
                      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                        {agent.duration_ms !== null && agent.duration_ms !== undefined && (
                          <span style={{ fontSize: "12px", fontFamily: "monospace", color: "var(--text-muted)" }}>
                            {agent.duration_ms}ms
                          </span>
                        )}
                        <span className={`badge-status ${agent.status}`}>
                          {agent.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                {!loading && (
                  <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "32px" }}>
                    <button onClick={() => setActiveTab("risk")} className="btn-primary">
                      Verify Risk & Compliance Matrix
                      <ArrowRight style={{ width: "14px", height: "14px", color: "#000" }} />
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* ========================================== */}
            {/* TAB 3: RISK & COMPLIANCE MATRIX */}
            {/* ========================================== */}
            {activeTab === "risk" && decisionState && (() => {
              const targetRiskVendor = activeRiskVendor || decisionState.recommended_vendor_name || selectedVendors[0];
              const vendorData = decisionState.evaluated_vendors?.[targetRiskVendor] || decisionState;
              const policyChecks = vendorData.policy_checks;
              const riskAssessment = vendorData.risk_assessment;
              
              return (
                <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%" }}>
                  
                  {/* Vendor selector tabs */}
                  {selectedVendors.length > 1 && (
                    <div className="glow-card" style={{ display: "flex", alignItems: "center", gap: "10px", padding: "12px 20px" }}>
                      <span style={{ fontSize: "12.5px", color: "var(--text-secondary)", fontWeight: "600", marginRight: "10px" }}>Inspect Vendor Profile:</span>
                      <div style={{ display: "flex", gap: "8px" }}>
                        {selectedVendors.map((name) => {
                          const isActive = name === targetRiskVendor;
                          const isRecommended = name === decisionState.recommended_vendor_name;
                          return (
                            <button
                              key={name}
                              onClick={() => setActiveRiskVendor(name)}
                              className={`priority-btn ${isActive ? "active" : ""}`}
                              style={{
                                padding: "6px 14px",
                                fontSize: "12.5px",
                                borderRadius: "6px",
                                display: "flex",
                                alignItems: "center",
                                gap: "6px"
                              }}
                            >
                              {name}
                              {isRecommended && (
                                <span style={{
                                  fontSize: "9px",
                                  backgroundColor: isActive ? "rgba(0,0,0,0.2)" : "rgba(0, 242, 254, 0.15)",
                                  color: isActive ? "#fff" : "var(--accent-cyan)",
                                  padding: "2px 6px",
                                  borderRadius: "4px",
                                  fontWeight: "700"
                                }}>
                                  REC
                                </span>
                              )}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  <div className="grid-2col">
                    
                    {/* RAG Checks */}
                    <div className="glow-card" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                      <h3 style={{ fontSize: "16px", borderBottom: "1px solid var(--border-color)", paddingBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
                        <UserCheck style={{ width: "18px", height: "18px", color: "var(--accent-cyan)" }} />
                        Policy Compliance Verification
                      </h3>

                      {policyChecks ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", backgroundColor: "rgba(255,255,255,0.01)", padding: "12px", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
                            <span style={{ fontSize: "13.5px", color: "var(--text-secondary)" }}>Compliance State</span>
                            <span className={`badge-status ${
                              policyChecks.compliance_status?.toLowerCase().includes("compliant") && !policyChecks.compliance_status?.toLowerCase().includes("conditional") && !policyChecks.compliance_status?.toLowerCase().includes("non")
                                ? "completed"
                                : policyChecks.compliance_status?.toLowerCase().includes("conditional")
                                  ? "pending"
                                  : "failed"
                            }`}>
                              {policyChecks.compliance_status}
                            </span>
                          </div>

                          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                            <span className="input-label">Target Rules Triggered</span>
                            <ul style={{ listStyleType: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "8px" }}>
                              {policyChecks.relevant_policies?.map((pol, idx) => (
                                <li key={idx} style={{ fontSize: "13px", backgroundColor: "rgba(255,255,255,0.02)", border: "1px solid var(--border-color)", padding: "10px", borderRadius: "6px", color: "var(--text-secondary)" }}>
                                  {pol}
                                </li>
                              ))}
                            </ul>
                          </div>

                          <div style={{ display: "flex", justifyContent: "space-between", borderTop: "1px solid var(--border-color)", paddingTop: "16px", fontSize: "13.5px" }}>
                            <span style={{ color: "var(--text-secondary)" }}>Purchase Limit Exceeded?</span>
                            <span style={{ fontWeight: "600", color: policyChecks.purchase_limit_exceeded ? "var(--status-failed)" : "var(--status-completed)" }}>
                              {policyChecks.purchase_limit_exceeded ? "YES ($100k cap exceeded)" : "NO"}
                            </span>
                          </div>

                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13.5px" }}>
                            <span style={{ color: "var(--text-secondary)" }}>Vendor Blacklist Status</span>
                            <span style={{ fontWeight: "600", color: policyChecks.vendor_blacklisted ? "var(--status-failed)" : "var(--status-completed)" }}>
                              {policyChecks.vendor_blacklisted ? "WARNING" : "CLEARED"}
                            </span>
                          </div>
                        </div>
                      ) : (
                        <div style={{ textAlign: "center", color: "var(--text-muted)" }}>Not run yet.</div>
                      )}
                    </div>

                    {/* Risk Assess */}
                    <div className="glow-card" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                      <h3 style={{ fontSize: "16px", borderBottom: "1px solid var(--border-color)", paddingBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
                        <ShieldAlert style={{ width: "18px", height: "18px", color: "var(--accent-cyan)" }} />
                        Multi-Factor Risk Assessment
                      </h3>

                      {riskAssessment ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", backgroundColor: "rgba(255,255,255,0.01)", padding: "12px", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
                            <div>
                              <span className="input-label">Overall Risk Score</span>
                              <h4 style={{ fontSize: "20px", fontWeight: "700", marginTop: "4px" }}>{riskAssessment.overall_risk}%</h4>
                            </div>
                            <span className={`badge-status ${riskAssessment.risk_level === "Low" ? "completed" : riskAssessment.risk_level === "Medium" ? "pending" : "failed"}`}>
                              {riskAssessment.risk_level} RISK
                            </span>
                          </div>

                          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                            <div>
                              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px", color: "var(--text-secondary)" }}>
                                <span>Delivery delay risk</span>
                                <span>{riskAssessment.delivery_risk}%</span>
                              </div>
                              <div style={{ height: "6px", background: "rgba(255,255,255,0.05)", borderRadius: "3px", overflow: "hidden" }}>
                                <div style={{ height: "100%", background: "var(--accent-cyan)", width: `${riskAssessment.delivery_risk}%` }} />
                              </div>
                            </div>

                            <div>
                              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px", color: "var(--text-secondary)" }}>
                                <span>Financial anomaly risk</span>
                                <span>{riskAssessment.financial_risk}%</span>
                              </div>
                              <div style={{ height: "6px", background: "rgba(255,255,255,0.05)", borderRadius: "3px", overflow: "hidden" }}>
                                <div style={{ height: "100%", background: "var(--accent-blue)", width: `${riskAssessment.financial_risk}%` }} />
                              </div>
                            </div>

                            <div>
                              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px", color: "var(--text-secondary)" }}>
                                <span>Legal & Contractual risk</span>
                                <span>{riskAssessment.legal_risk}%</span>
                              </div>
                              <div style={{ height: "6px", background: "rgba(255,255,255,0.05)", borderRadius: "3px", overflow: "hidden" }}>
                                <div style={{ height: "100%", background: "var(--accent-purple)", width: `${riskAssessment.legal_risk}%` }} />
                              </div>
                            </div>
                          </div>

                          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                            <span className="input-label">Risk Factors Identified</span>
                            <ul style={{ listStyleType: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "8px" }}>
                              {riskAssessment.risk_factors?.map((fact, idx) => (
                                <li key={idx} style={{ fontSize: "13px", color: "var(--text-secondary)", display: "flex", gap: "6px", alignItems: "flex-start" }}>
                                  <span style={{ color: "var(--accent-cyan)", marginTop: "2px" }}>•</span>
                                  <span>{fact}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      ) : (
                        <div style={{ textAlign: "center", color: "var(--text-muted)" }}>Not run yet.</div>
                      )}
                    </div>
                  </div>

                  <div style={{ display: "flex", justifyContent: "flex-end" }}>
                    <button onClick={() => setActiveTab("recommendations")} className="btn-primary">
                      Generate Recommendation & Explainability
                      <ArrowRight style={{ width: "14px", height: "14px", color: "#000" }} />
                    </button>
                  </div>
                </div>
              );
            })()}

            {/* ========================================== */}
            {/* TAB 4: RECOMMENDED ACTION & SIGN-OFF */}
            {/* ========================================== */}
            {activeTab === "recommendations" && decisionState && (
              <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                
                {/* comparison matrix */}
                {decisionState.comparison_matrix && decisionState.comparison_matrix.length > 0 && (
                  <div className="glow-card">
                    <h3 style={{ fontSize: "15px", marginBottom: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
                      <Award style={{ width: "18px", height: "18px", color: "var(--accent-cyan)" }} />
                      Multi-Vendor Comparison Matrix
                    </h3>
                    <div style={{ overflowX: "auto" }}>
                      <table className="audit-table">
                        <thead>
                          <tr>
                            <th>Vendor</th>
                            <th>Offered Price ($)</th>
                            <th>Compliance</th>
                            <th>Lead Time</th>
                            <th>Risk Factor Score</th>
                            <th>History Score</th>
                            <th>Recommendation Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {decisionState.comparison_matrix.map((row, idx) => (
                            <tr key={idx} style={{
                              backgroundColor: row.status === "Recommended" ? "rgba(0, 242, 254, 0.03)" : "transparent",
                              borderLeft: row.status === "Recommended" ? "3px solid var(--accent-cyan)" : "3px solid transparent"
                            }}>
                              <td style={{ fontWeight: "700", color: "#fff" }}>{row.vendor}</td>
                              <td style={{ fontFamily: "monospace", color: row.price > budget ? "var(--status-failed)" : "#fff" }}>
                                ${row.price?.toLocaleString()}
                              </td>
                              <td>
                                <span className={`badge-status ${
                                  row.compliance?.toLowerCase().includes("compliant") && !row.compliance?.toLowerCase().includes("conditional") && !row.compliance?.toLowerCase().includes("non")
                                    ? "completed"
                                    : row.compliance?.toLowerCase().includes("conditional")
                                      ? "pending"
                                      : "failed"
                                }`}>
                                  {row.compliance}
                                </span>
                              </td>
                              <td>{row.lead_time}</td>
                              <td>
                                <span className={`badge-status ${row.risk === "Low" ? "completed" : row.risk === "Medium" ? "pending" : "failed"}`}>
                                  {row.risk_score}% ({row.risk})
                                </span>
                              </td>
                              <td style={{ color: "var(--accent-cyan)", fontWeight: "700" }}>{row.performance} / 5.0</td>
                              <td>
                                <span className={`badge-status ${row.status === "Recommended" ? "completed" : row.status === "Rejected" ? "failed" : "skipped"}`}>
                                  {row.status}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Side-by-Side Vendor Feature Comparison */}
                {decisionState.comparison_matrix && decisionState.comparison_matrix.length > 0 && (
                  <div className="glow-card" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                    <h3 style={{ fontSize: "15px", display: "flex", alignItems: "center", gap: "8px", margin: 0 }}>
                      <Activity style={{ width: "18px", height: "18px", color: "var(--accent-cyan)" }} />
                      Side-by-Side Vendor Feature comparison
                    </h3>
                    <div style={{ display: "grid", gridTemplateColumns: `repeat(${decisionState.comparison_matrix.length}, 1fr)`, gap: "20px", marginTop: "8px" }}>
                      {decisionState.comparison_matrix.map((row, idx) => {
                        const isRecommended = row.status === "Recommended";
                        return (
                          <div key={idx} style={{
                            background: isRecommended ? "rgba(0, 242, 254, 0.02)" : "rgba(255, 255, 255, 0.01)",
                            border: isRecommended ? "1px solid var(--accent-cyan)" : "1px solid var(--border-color)",
                            borderRadius: "12px",
                            padding: "20px",
                            display: "flex",
                            flexDirection: "column",
                            gap: "16px",
                            boxShadow: isRecommended ? "0 0 15px rgba(0, 242, 254, 0.1)" : "none",
                            position: "relative"
                          }}>
                            {isRecommended && (
                              <span style={{
                                position: "absolute",
                                top: "-10px",
                                right: "20px",
                                background: "var(--accent-cyan)",
                                color: "#000",
                                fontSize: "10px",
                                fontWeight: "800",
                                padding: "2px 8px",
                                borderRadius: "10px",
                                textTransform: "uppercase"
                              }}>
                                Recommended
                              </span>
                            )}
                            <h4 style={{ margin: 0, fontSize: "16px", fontWeight: "700", color: "#fff" }}>
                              {row.vendor}
                            </h4>
                            
                            <div style={{ display: "flex", flexDirection: "column", gap: "12px", fontSize: "13px" }}>
                              <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: "8px" }}>
                                <span style={{ color: "var(--text-muted)" }}>Price</span>
                                <strong style={{ color: isRecommended ? "var(--accent-cyan)" : "#fff", fontFamily: "monospace" }}>
                                  ${row.price?.toLocaleString()}
                                </strong>
                              </div>
                              
                              <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: "8px" }}>
                                <span style={{ color: "var(--text-muted)" }}>Delivery Speed</span>
                                <strong style={{ color: "#fff" }}>{row.lead_time}</strong>
                              </div>
                              
                              <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: "8px" }}>
                                <span style={{ color: "var(--text-muted)" }}>Compliance</span>
                                <span className={`badge-status ${
                                  row.compliance?.toLowerCase().includes("compliant") && !row.compliance?.toLowerCase().includes("conditional") && !row.compliance?.toLowerCase().includes("non") 
                                    ? "completed" 
                                    : row.compliance?.toLowerCase().includes("conditional") 
                                    ? "pending" 
                                    : "failed"
                                }`} style={{ fontSize: "11px", padding: "2px 6px" }}>
                                  {row.compliance}
                                </span>
                              </div>
                              
                              <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: "8px" }}>
                                <span style={{ color: "var(--text-muted)" }}>Overall Risk</span>
                                <span className={`badge-status ${row.risk === "Low" ? "completed" : row.risk === "Medium" ? "pending" : "failed"}`} style={{ fontSize: "11px", padding: "2px 6px" }}>
                                  {row.risk_score}% ({row.risk})
                                </span>
                              </div>
                              
                              <div style={{ display: "flex", justifyContent: "space-between", paddingBottom: "4px" }}>
                                <span style={{ color: "var(--text-muted)" }}>History Rating</span>
                                <strong style={{ color: "var(--accent-cyan)" }}>{row.performance} / 5.0</strong>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {decisionState.comparison_matrix && decisionState.comparison_matrix.length > 0 && (() => {
                  const maxPrice = Math.max(
                    ...decisionState.comparison_matrix.map(r => r.price || 0),
                    parseFloat(budget) || 100000
                  ) * 1.2 || 100000;

                  return (
                    <div className="grid-2col">
                      
                      {/* Price Chart */}
                      <div className="glow-card" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                        <h4 className="input-label" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span>💰 Price vs Budget Analysis</span>
                          <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Target Budget: ${parseFloat(budget)?.toLocaleString()}</span>
                        </h4>
                        
                        <div style={{ height: "220px", display: "flex", alignItems: "flex-end", padding: "10px 20px 20px 20px", borderBottom: "1px solid var(--border-color)", position: "relative" }}>
                          {/* Budget limit line */}
                          {(() => {
                            const budgetY = 220 - ((parseFloat(budget) || 0) / maxPrice) * 180 - 20;
                            return (
                              <div style={{
                                position: "absolute",
                                left: 0,
                                right: 0,
                                top: `${budgetY}px`,
                                borderTop: "2px dashed var(--status-failed)",
                                zIndex: 1,
                                display: "flex",
                                justifyContent: "flex-end"
                              }}>
                                <span style={{ fontSize: "9px", color: "var(--status-failed)", background: "#0a0d14", padding: "2px 6px", borderRadius: "4px", marginTop: "-10px", fontWeight: "700" }}>
                                  BUDGET CEILING
                                </span>
                              </div>
                            );
                          })()}

                          {/* Columns mapping */}
                          <div style={{ display: "flex", width: "100%", justifyContent: "space-around", zIndex: 2, height: "180px", alignItems: "flex-end" }}>
                            {decisionState.comparison_matrix.map((row, idx) => {
                              const barHeight = ((row.price || 0) / maxPrice) * 180;
                              const isOverBudget = row.price > (parseFloat(budget) || Infinity);
                              return (
                                <div key={idx} style={{ display: "flex", flexDirection: "column", alignItems: "center", width: "30%", gap: "8px" }}>
                                  <span style={{ fontSize: "11.5px", fontFamily: "monospace", fontWeight: "600", color: isOverBudget ? "var(--status-failed)" : "var(--accent-cyan)" }}>
                                    ${row.price?.toLocaleString()}
                                  </span>
                                  <div style={{
                                    width: "100%",
                                    height: `${barHeight}px`,
                                    background: isOverBudget 
                                      ? "linear-gradient(180deg, var(--status-failed), rgba(255, 75, 75, 0.2))"
                                      : row.status === "Recommended"
                                        ? "linear-gradient(180deg, var(--accent-cyan), rgba(0, 242, 254, 0.2))"
                                        : "linear-gradient(180deg, var(--accent-blue), rgba(0, 102, 255, 0.2))",
                                    borderRadius: "4px 4px 0 0",
                                    transition: "height 0.5s ease",
                                    boxShadow: row.status === "Recommended" ? "0 0 12px rgba(0, 242, 254, 0.3)" : "none"
                                  }} />
                                  <span style={{ fontSize: "12px", fontWeight: "700", color: "#fff", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap", maxWidth: "90px" }}>
                                    {row.vendor}
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>

                      {/* Risk & Performance Chart */}
                      <div className="glow-card" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                        <h4 className="input-label">🛡️ Risk vs Past Performance comparison</h4>
                        
                        <div style={{ display: "flex", flexDirection: "column", gap: "24px", padding: "10px 0" }}>
                          {decisionState.comparison_matrix.map((row, idx) => (
                            <div key={idx} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                              <span style={{ fontSize: "13px", fontWeight: "700", color: "#fff" }}>
                                {row.vendor} {row.status === "Recommended" && <span style={{ color: "var(--accent-cyan)", fontSize: "10px" }}>(Recommended)</span>}
                              </span>
                              
                              <div style={{ display: "grid", gridTemplateColumns: "100px 1fr", alignItems: "center", gap: "12px" }}>
                                {/* Risk Bar */}
                                <span style={{ fontSize: "11px", color: "var(--text-secondary)" }}>Audit Risk: {row.risk_score}%</span>
                                <div style={{ height: "10px", background: "rgba(255,255,255,0.03)", borderRadius: "5px", overflow: "hidden" }}>
                                  <div style={{
                                    height: "100%",
                                    width: `${row.risk_score}%`,
                                    background: row.risk === "High" ? "var(--status-failed)" : row.risk === "Medium" ? "var(--status-pending)" : "var(--status-completed)"
                                  }} />
                                </div>

                                {/* Performance Bar */}
                                <span style={{ fontSize: "11px", color: "var(--text-secondary)" }}>Performance: {row.performance}/5</span>
                                <div style={{ height: "10px", background: "rgba(255,255,255,0.03)", borderRadius: "5px", overflow: "hidden" }}>
                                  <div style={{
                                    height: "100%",
                                    width: `${(row.performance / 5.0) * 100}%`,
                                    background: "var(--accent-cyan)",
                                    boxShadow: "0 0 8px rgba(0, 242, 254, 0.3)"
                                  }} />
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                    </div>
                  );
                })()}

                <div className="grid-3col">
                  
                  {/* Recommendation Detail */}
                  <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                    {decisionState.next_best_action ? (
                      <>
                        <div className="glow-card" style={{ borderLeft: "4px solid var(--accent-cyan)", background: "linear-gradient(90deg, rgba(0, 242, 254, 0.02), transparent)" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                            <span style={{ fontSize: "11px", fontWeight: "700", color: "var(--accent-cyan)", tracking: "0.1em", textTransform: "uppercase", display: "flex", alignItems: "center", gap: "6px" }}>
                              <Sparkles style={{ width: "14px", height: "14px" }} />
                              Recommended Active Vendor: {decisionState.recommended_vendor_name || decisionState.quote_data?.vendor_name || "Primary Option"}
                            </span>
                            <span style={{ fontSize: "13px", fontWeight: "700", color: "#fff" }}>
                              Confidence: {decisionState.next_best_action.recommendations[0]?.confidence || 90}%
                            </span>
                          </div>
                          
                          <h3 style={{ fontSize: "17px", marginBottom: "12px", color: "#fff", lineHeight: "1.4" }}>
                            {decisionState.next_best_action.recommendations[0]?.action}
                          </h3>
                          
                          <p style={{ fontSize: "13.5px", color: "var(--text-secondary)", margin: 0, lineHeight: "1.5" }}>
                            <strong>Reason: </strong> {decisionState.next_best_action.recommendations[0]?.reason}
                          </p>
                          </div>

                        {/* ====== POLICY VERDICT CARD ====== */}
                        {(() => {
                          // Collect policy verdict data from evaluated_vendors or fallback to direct policy_checks
                          const vendorsToShow = decisionState.evaluated_vendors
                            ? Object.entries(decisionState.evaluated_vendors)
                            : decisionState.policy_checks
                              ? [[decisionState.recommended_vendor_name || "Vendor", { policy_checks: decisionState.policy_checks }]]
                              : [];

                          if (vendorsToShow.length === 0) return null;

                          return (
                            <div className="glow-card" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: "1px solid var(--border-color)", paddingBottom: "12px" }}>
                                <h4 style={{ margin: 0, fontSize: "14px", fontWeight: "700", color: "#fff", display: "flex", alignItems: "center", gap: "8px" }}>
                                  <ShieldAlert style={{ width: "16px", height: "16px", color: "var(--accent-cyan)" }} />
                                  Policy Compliance Verdict
                                </h4>
                                <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Why recommended or rejected</span>
                              </div>

                              {vendorsToShow.map(([vName, vData]) => {
                                const pc = vData.policy_checks;
                                if (!pc) return null;
                                const verdict = pc.policy_verdict || [];
                                const decisionReason = pc.decision_reason || "";
                                const isRecommended = vName === decisionState.recommended_vendor_name;
                                const isRejected = decisionState.rejected_vendors?.includes(vName);
                                const passCount = verdict.filter(v => v.status === "PASS").length;
                                const failCount = verdict.filter(v => v.status === "FAIL").length;

                                return (
                                  <div key={vName} style={{
                                    border: `1px solid ${isRecommended ? "var(--accent-cyan)" : isRejected ? "var(--status-failed)" : "var(--border-color)"}`,
                                    borderRadius: "10px",
                                    overflow: "hidden"
                                  }}>
                                    {/* Vendor header */}
                                    <div style={{
                                      display: "flex",
                                      alignItems: "center",
                                      justifyContent: "space-between",
                                      padding: "12px 16px",
                                      background: isRecommended
                                        ? "linear-gradient(90deg, rgba(0,242,254,0.06), transparent)"
                                        : isRejected
                                          ? "rgba(255,75,75,0.04)"
                                          : "rgba(255,255,255,0.01)"
                                    }}>
                                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                                        <span style={{ fontSize: "14px", fontWeight: "700", color: "#fff" }}>{vName}</span>
                                        <span className={`badge-status ${isRecommended ? "completed" : isRejected ? "failed" : "skipped"}`} style={{ fontSize: "10px" }}>
                                          {isRecommended ? "✓ Recommended" : isRejected ? "✗ Rejected" : "Alternative"}
                                        </span>
                                      </div>
                                      <div style={{ display: "flex", gap: "8px" }}>
                                        <span style={{ fontSize: "11px", background: "rgba(0,200,100,0.12)", color: "#00c864", border: "1px solid rgba(0,200,100,0.25)", padding: "3px 10px", borderRadius: "12px", fontWeight: "700" }}>
                                          ✓ {passCount} Passed
                                        </span>
                                        <span style={{ fontSize: "11px", background: "rgba(255,75,75,0.1)", color: "var(--status-failed)", border: "1px solid rgba(255,75,75,0.25)", padding: "3px 10px", borderRadius: "12px", fontWeight: "700" }}>
                                          ✗ {failCount} Failed
                                        </span>
                                      </div>
                                    </div>

                                    {/* Decision reason summary */}
                                    {decisionReason && (
                                      <div style={{
                                        padding: "10px 16px",
                                        background: isRecommended ? "rgba(0,242,254,0.03)" : "rgba(255,75,75,0.03)",
                                        borderBottom: "1px solid var(--border-color)",
                                        fontSize: "12.5px",
                                        color: isRecommended ? "var(--accent-cyan)" : "var(--text-secondary)",
                                        lineHeight: "1.5"
                                      }}>
                                        {decisionReason}
                                      </div>
                                    )}

                                    {/* Per-policy breakdown */}
                                    {verdict.length > 0 && (
                                      <div style={{ padding: "12px 16px", display: "flex", flexDirection: "column", gap: "8px", maxHeight: "320px", overflowY: "auto" }}>
                                        {verdict.map((item, idx) => (
                                          <div key={idx} style={{
                                            display: "grid",
                                            gridTemplateColumns: "80px 1fr auto",
                                            alignItems: "center",
                                            gap: "12px",
                                            padding: "8px 10px",
                                            borderRadius: "6px",
                                            background: item.status === "PASS"
                                              ? "rgba(0,200,100,0.04)"
                                              : "rgba(255,75,75,0.04)",
                                            border: `1px solid ${item.status === "PASS" ? "rgba(0,200,100,0.12)" : "rgba(255,75,75,0.12)"}`
                                          }}>
                                            <span style={{ fontSize: "10px", fontFamily: "monospace", fontWeight: "700", color: "var(--text-muted)" }}>{item.code}</span>
                                            <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                                              <span style={{ fontSize: "11.5px", color: "#fff", lineHeight: "1.3" }}>{item.text}</span>
                                              <span style={{ fontSize: "10.5px", color: "var(--text-muted)", fontStyle: "italic" }}>{item.reason}</span>
                                            </div>
                                            <span style={{
                                              fontSize: "10px",
                                              fontWeight: "800",
                                              padding: "3px 8px",
                                              borderRadius: "10px",
                                              whiteSpace: "nowrap",
                                              background: item.status === "PASS" ? "rgba(0,200,100,0.15)" : "rgba(255,75,75,0.15)",
                                              color: item.status === "PASS" ? "#00c864" : "var(--status-failed)"
                                            }}>
                                              {item.status === "PASS" ? "✓ PASS" : "✗ FAIL"}
                                            </span>
                                          </div>
                                        ))}
                                      </div>
                                    )}

                                    {verdict.length === 0 && (
                                      <div style={{ padding: "16px", fontSize: "12px", color: "var(--text-muted)", textAlign: "center" }}>
                                        Upload vendor documents to see detailed policy verdict.
                                      </div>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          );
                        })()}

                        <div className="glow-card">
                          <h4 className="input-label" style={{ marginBottom: "10px" }}>AI Alternative Directions Considered</h4>
                          <p style={{ fontSize: "13px", color: "var(--text-secondary)", margin: 0, fontStyle: "italic", lineHeight: "1.5" }}>
                            {decisionState.next_best_action.recommendations[0]?.alternative}
                          </p>

                          {/* Switch suggestion */}
                          {decisionState.next_best_action.alternative_vendors && decisionState.next_best_action.alternative_vendors.length > 0 && (
                            <div style={{ marginTop: "24px", display: "flex", flexDirection: "column", gap: "12px" }}>
                              <h4 className="input-label" style={{ borderTop: "1px solid var(--border-color)", paddingTop: "16px", marginBottom: "4px" }}>
                                Other Available Options
                              </h4>
                              <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "16px" }}>
                                {decisionState.next_best_action.alternative_vendors.map((alt, idx) => (
                                  <div key={idx} className="glow-card" style={{
                                    border: "1px solid var(--border-color)",
                                    padding: "16px",
                                    borderRadius: "8px",
                                    background: "rgba(255, 255, 255, 0.01)",
                                    display: "flex",
                                    flexDirection: "column",
                                    gap: "12px"
                                  }}>
                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                      <span style={{ fontWeight: "700", color: "#fff", fontSize: "14px" }}>{alt.name}</span>
                                      <span className={`badge-status ${alt.risk_level === "Low" ? "completed" : alt.risk_level === "Medium" ? "pending" : "failed"}`} style={{ fontSize: "11px" }}>
                                        {alt.risk_level} Risk
                                      </span>
                                    </div>
                                    
                                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px", fontSize: "12px", color: "var(--text-secondary)" }}>
                                      <div>
                                        <span style={{ display: "block", color: "var(--text-muted)", fontSize: "10px", textTransform: "uppercase" }}>Price</span>
                                        <strong style={{ color: "#fff" }}>${alt.unit_price?.toLocaleString()}/unit</strong>
                                      </div>
                                      <div>
                                        <span style={{ display: "block", color: "var(--text-muted)", fontSize: "10px", textTransform: "uppercase" }}>Performance</span>
                                        <strong style={{ color: "var(--accent-cyan)" }}>{alt.performance_score} / 5.0</strong>
                                      </div>
                                      <div>
                                        <span style={{ display: "block", color: "var(--text-muted)", fontSize: "10px", textTransform: "uppercase" }}>Lead Time</span>
                                        <strong style={{ color: "#fff" }}>{alt.typical_lead_time_days || 14} days</strong>
                                      </div>
                                    </div>
                                    
                                    <button
                                      onClick={() => {
                                        // Dynamic switch in UI triggers rejection of recommended to bring next
                                        submitDecision("Rejected");
                                      }}
                                      className="btn-secondary"
                                      style={{
                                        fontSize: "11.5px",
                                        padding: "6px 12px",
                                        alignSelf: "flex-end",
                                        marginTop: "4px",
                                        borderColor: "var(--accent-cyan)",
                                        color: "var(--accent-cyan)",
                                        background: "rgba(0, 242, 254, 0.05)"
                                      }}
                                    >
                                      Reject Top and Try Alternative
                                    </button>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>

                        {decisionState.reasoning && (
                          <div className="glow-card" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                            <h4 className="input-label" style={{ borderBottom: "1px solid var(--border-color)", paddingBottom: "8px" }}>Evidence Traceability ("Why?")</h4>
                            
                            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                              {decisionState.reasoning.cognitive_findings?.map((find, idx) => (
                                <div key={idx} style={{ backgroundColor: "rgba(255,255,255,0.01)", border: "1px solid var(--border-color)", padding: "12px", borderRadius: "6px", display: "flex", flexDirection: "column", gap: "6px" }}>
                                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px" }}>
                                    <span style={{ fontWeight: "700", color: "var(--accent-cyan)" }}>{find.source}</span>
                                    <span style={{ color: "var(--text-muted)" }}>Fact verified</span>
                                  </div>
                                  <p style={{ fontSize: "13.5px", color: "#fff", margin: 0 }}>"{find.fact}"</p>
                                  <p style={{ fontSize: "11px", color: "var(--text-muted)", margin: 0 }}>
                                    <strong>Impact:</strong> {find.reasoning_step}
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    ) : (
                      <div style={{ textAlign: "center", color: "var(--text-muted)" }}>No recommendations available.</div>
                    )}
                  </div>

                  {/* Human sign off right sidebar */}
                  <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                    <div className="glow-card" style={{ backgroundColor: "rgba(255,255,255,0.01)", display: "flex", flexDirection: "column", gap: "20px" }}>
                      <h3 style={{ fontSize: "15px", borderBottom: "1px solid var(--border-color)", paddingBottom: "10px", display: "flex", alignItems: "center", gap: "8px" }}>
                        <Lock style={{ width: "16px", height: "16px", color: "var(--accent-cyan)" }} />
                        Procurement Sign-off Lock
                      </h3>

                      {decisionState.next_best_action && (
                        <div style={{ backgroundColor: "rgba(255,255,255,0.02)", border: "1px solid var(--border-color)", padding: "12px", borderRadius: "6px", fontSize: "13px" }}>
                          <span style={{ fontSize: "11px", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>Approval Tier Matrix Target:</span>
                          <span style={{ fontWeight: "700", color: "#fff" }}>{decisionState.next_best_action.final_decision_tier}</span>
                        </div>
                      )}

                      {decisionOutcome ? (
                        <div style={{ textAlign: "center", padding: "24px 0", display: "flex", flexDirection: "column", gap: "12px", alignItems: "center" }}>
                          <CheckCircle style={{ width: "48px", height: "48px", color: "var(--status-completed)" }} />
                          <h4 style={{ fontSize: "18px", color: "var(--status-completed)", fontWeight: "700" }}>Decision {decisionOutcome}</h4>
                          <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Audit log permanently stored.</span>
                          <button
                            onClick={handleDownloadPDFReport}
                            className="btn-primary"
                            style={{ display: "flex", alignItems: "center", gap: "8px", width: "100%", justifyContent: "center", marginTop: "16px", padding: "10px" }}
                          >
                            <FileText style={{ width: "14px", height: "14px" }} />
                            Download PDF Audit Report
                          </button>
                        </div>
                      ) : (
                        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                          <div className="input-group">
                            <label className="input-label">Approval Comments / Audit Notes</label>
                            <textarea
                              value={approvalNotes}
                              onChange={(e) => setApprovalNotes(e.target.value)}
                              rows={3}
                              className="form-input"
                              style={{ height: "80px", resize: "none", fontSize: "12px" }}
                              placeholder="Enter override comments..."
                            />
                          </div>

                          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                            <button onClick={() => submitDecision("Approved")} className="btn-primary" style={{ fontSize: "12px", padding: "10px" }}>
                              Approve Deal
                            </button>
                            
                            <button onClick={() => submitDecision("Rejected")} className="btn-secondary" style={{ fontSize: "12px", padding: "10px", borderColor: "var(--status-failed)", color: "var(--status-failed)" }}>
                              Reject Deal
                            </button>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Missing Info Warning */}
                    {decisionState.missing_info && (
                      <div className="glow-card">
                        <h4 style={{ fontSize: "13.5px", color: "var(--status-pending)", marginBottom: "12px", display: "flex", alignItems: "center", gap: "6px" }}>
                          <AlertTriangle style={{ width: "16px", height: "16px" }} />
                          Missing Info warnings
                        </h4>
                        <ul style={{ listStyleType: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "8px", fontSize: "12px", color: "var(--text-secondary)" }}>
                          {decisionState.missing_info.missing_fields?.map((f, idx) => (
                            <li key={idx}>• {f}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                </div>
              </div>
            )}

            {/* ========================================== */}
            {/* TAB 5: AUDIT LOGS HISTORY */}
            {/* ========================================== */}
            {activeTab === "history" && (
              <div className="glow-card">
                <h3 style={{ fontSize: "16px", borderBottom: "1px solid var(--border-color)", paddingBottom: "12px", marginBottom: "24px", display: "flex", alignItems: "center", gap: "8px" }}>
                  <History style={{ width: "18px", height: "18px", color: "var(--accent-cyan)" }} />
                  Procurement Audit Records (Memory Store)
                </h3>

                <div style={{ overflowX: "auto" }}>
                  <table className="audit-table">
                    <thead>
                      <tr>
                        <th>Session ID</th>
                        <th>Vendor</th>
                        <th>Category</th>
                        <th>Budget ($)</th>
                        <th>Final Action Recommended</th>
                        <th>Decision</th>
                        <th>Timestamp</th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditLogs.map((log, idx) => (
                        <tr key={idx}>
                          <td style={{ fontFamily: "monospace", color: "var(--text-muted)" }}>{log.session_id}</td>
                          <td style={{ fontWeight: "700", color: "#fff" }}>{log.vendor}</td>
                          <td>{log.category}</td>
                          <td style={{ fontFamily: "monospace" }}>${log.budget}</td>
                          <td style={{ fontSize: "12px", maxWidth: "250px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{log.recommendation}</td>
                          <td>
                            <span className={`badge-status ${log.status === "Approved" ? "completed" : "failed"}`}>
                              {log.status}
                            </span>
                          </td>
                          <td style={{ fontSize: "11px", fontFamily: "monospace", color: "var(--text-muted)" }}>{log.timestamp}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* ========================================== */}
            {/* TAB 6: COMPLIANCE POLICIES ADMIN */}
            {/* ========================================== */}
            {activeTab === "policies_admin" && (
              <div className="grid-2col">
                {/* Active policies list */}
                <div className="glow-card" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                  <h3 style={{ fontSize: "16px", borderBottom: "1px solid var(--border-color)", paddingBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
                    <Lock style={{ width: "18px", height: "18px", color: "var(--accent-cyan)" }} />
                    Active Corporate Compliance Rules
                  </h3>
                  
                  <div style={{ display: "flex", flexDirection: "column", gap: "16px", maxHeight: "600px", overflowY: "auto", paddingRight: "4px" }}>
                    {policies.length === 0 ? (
                      <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "20px 0" }}>No compliance policies configured in the system.</div>
                    ) : (
                      policies.map((pol) => (
                        <div key={pol.id} className="glow-card" style={{
                          border: "1px solid var(--border-color)",
                          padding: "16px",
                          borderRadius: "8px",
                          background: "rgba(255, 255, 255, 0.01)",
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "flex-start",
                          gap: "16px"
                        }}>
                          <div style={{ display: "flex", flexDirection: "column", gap: "8px", flex: 1 }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                              <span style={{ fontWeight: "700", color: "var(--accent-cyan)", fontSize: "14px", fontFamily: "monospace" }}>
                                {pol.code}
                              </span>
                              <span className="badge-status pending" style={{ fontSize: "10px", padding: "2px 8px" }}>
                                {pol.category}
                              </span>
                            </div>
                            <p style={{ fontSize: "13px", color: "var(--text-secondary)", margin: 0, lineHeight: "1.5" }}>
                              {pol.text}
                            </p>
                          </div>
                          
                          <button
                            onClick={() => handleDeletePolicy(pol.id)}
                            style={{
                              background: "rgba(255, 75, 75, 0.1)",
                              border: "1px solid rgba(255, 75, 75, 0.2)",
                              color: "var(--status-failed)",
                              cursor: "pointer",
                              padding: "6px 10px",
                              borderRadius: "4px",
                              fontSize: "12px",
                              fontWeight: "600",
                              transition: "all 0.2s ease"
                            }}
                            title="Delete Policy Rule"
                          >
                            Delete
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Add new policy form */}
                <div className="glow-card" style={{ display: "flex", flexDirection: "column", gap: "20px", height: "fit-content" }}>
                  <h3 style={{ fontSize: "16px", borderBottom: "1px solid var(--border-color)", paddingBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
                    <PlusCircle style={{ width: "18px", height: "18px", color: "var(--accent-cyan)" }} />
                    Register New Compliance Guideline
                  </h3>
                  
                  <form onSubmit={handleAddPolicy} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                    {policyError && (
                      <div style={{
                        backgroundColor: "rgba(255, 75, 75, 0.1)",
                        border: "1px solid var(--status-failed)",
                        color: "var(--status-failed)",
                        padding: "10px 14px",
                        borderRadius: "6px",
                        fontSize: "12.5px"
                      }}>
                        {policyError}
                      </div>
                    )}
                    
                    <div className="input-group">
                      <label className="input-label">Policy Reference Code</label>
                      <input
                        type="text"
                        value={newPolicyCode}
                        onChange={(e) => setNewPolicyCode(e.target.value)}
                        placeholder="e.g. PROC-POL-15"
                        className="form-input"
                        required
                      />
                    </div>
                    
                    <div className="input-group">
                      <label className="input-label">Policy Category</label>
                      <select
                        value={newPolicyCategory}
                        onChange={(e) => setNewPolicyCategory(e.target.value)}
                        className="form-input"
                        required
                      >
                        <option value="limits">Spending Limits (limits)</option>
                        <option value="payment_terms">Payment Terms (payment_terms)</option>
                        <option value="security">InfoSec & Compliance (security)</option>
                        <option value="escrow">SLA & Escrow (escrow)</option>
                        <option value="approval">Approval Tiers (approval)</option>
                      </select>
                    </div>
                    
                    <div className="input-group">
                      <label className="input-label">Compliance Rule Statement (AI Context)</label>
                      <textarea
                        value={newPolicyText}
                        onChange={(e) => setNewPolicyText(e.target.value)}
                        placeholder="e.g. Any third-party software transaction exceeding $50,000 requires full architecture review and legal compliance clearance."
                        className="form-input"
                        style={{ height: "120px", resize: "none", fontSize: "12.5px", lineHeight: "1.4" }}
                        required
                      />
                    </div>
                    
                    <button type="submit" className="btn-primary" style={{ width: "100%", justifyContent: "center", padding: "12px" }}>
                      Register Policy & Generate Embeddings
                    </button>
                  </form>
                </div>
              </div>
            )}

            {/* ========================================== */}
            {/* TAB 7: VENDOR DIRECTORY */}
            {/* ========================================== */}
            {activeTab === "vendors" && (
              <div className="vendor-dir-layout">
                {/* Left side list of vendors */}
                <div className="vendor-sidebar glow-card">
                  <h3 style={{ fontSize: "15px", borderBottom: "1px solid var(--border-color)", paddingBottom: "12px", display: "flex", alignItems: "center", gap: "8px", margin: 0 }}>
                    <Users style={{ width: "18px", height: "18px", color: "var(--accent-cyan)" }} />
                    Registered Vendors
                  </h3>
                  <div className="vendor-list-container" style={{ marginTop: "12px" }}>
                    {vendorsList.length === 0 ? (
                      <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "20px 0" }}>No vendors found in the database.</div>
                    ) : (
                      vendorsList.map((vendor) => (
                        <button
                          key={vendor.id}
                          onClick={() => setSelectedDirVendor(vendor.name)}
                          className={`vendor-list-card ${selectedDirVendor === vendor.name ? "active" : ""}`}
                        >
                          <div className="vendor-list-card-header">
                            <span className="vendor-list-card-name">{vendor.name}</span>
                            <span className={`badge-status ${vendor.status === "Active" ? "completed" : "failed"}`} style={{ fontSize: "9px", padding: "1px 6px" }}>
                              {vendor.status}
                            </span>
                          </div>
                          <div className="vendor-list-card-meta">
                            <span>Score: {vendor.performance_score.toFixed(1)}</span>
                            <span>•</span>
                            <span className={`badge-risk ${vendor.risk_level.toLowerCase()}`}>{vendor.risk_level} Risk</span>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </div>

                {/* Right side detailed view */}
                <div className="vendor-detail-pane">
                  {!selectedDirVendor ? (
                    <div className="glow-card" style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "200px", color: "var(--text-muted)" }}>
                      Select a vendor from the list to view profile details.
                    </div>
                  ) : !vendorDetails ? (
                    <div className="glow-card" style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "200px" }}>
                      <RefreshCw className="animate-spin-slow" style={{ width: "24px", height: "24px", color: "var(--accent-cyan)", marginRight: "8px" }} />
                      Loading profile details...
                    </div>
                  ) : (
                    <>
                      {/* Vendor Profile Info Card */}
                      <div className="glow-card">
                        <div className="vendor-details-header">
                          <div>
                            <h2 style={{ fontSize: "20px", fontWeight: "700", margin: "0 0 4px 0", color: "#fff" }}>
                              {vendorDetails.profile.name}
                            </h2>
                            <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
                              Category: <strong>{vendorDetails.profile.category}</strong>
                            </span>
                          </div>
                          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                            {vendorDetails.profile.is_blacklisted === 1 && (
                              <span className="badge-status failed" style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                                <ShieldAlert style={{ width: "12px", height: "12px" }} />
                                Blacklisted
                              </span>
                            )}
                            <span className={`badge-status ${vendorDetails.profile.status === "Active" ? "completed" : "failed"}`}>
                              Status: {vendorDetails.profile.status}
                            </span>
                          </div>
                        </div>

                        <div className="vendor-detail-metrics" style={{ marginTop: "16px" }}>
                          <div className="vendor-metric-box">
                            <span className="vendor-metric-label">Performance score</span>
                            <span className="vendor-metric-value" style={{ color: "var(--accent-cyan)", display: "flex", alignItems: "center", gap: "6px" }}>
                              <Award style={{ width: "18px", height: "18px", color: "var(--accent-cyan)" }} />
                              {vendorDetails.profile.performance_score.toFixed(1)} / 5.0
                            </span>
                          </div>
                          <div className="vendor-metric-box">
                            <span className="vendor-metric-label">Risk Profile</span>
                            <span className={`vendor-metric-value badge-risk ${vendorDetails.profile.risk_level.toLowerCase()}`} style={{ width: "fit-content", padding: "4px 8px", fontSize: "12px", borderRadius: "4px" }}>
                              {vendorDetails.profile.risk_level} Risk
                            </span>
                          </div>
                          <div className="vendor-metric-box">
                            <span className="vendor-metric-label">Purchase Orders</span>
                            <span className="vendor-metric-value">
                              {vendorDetails.purchase_history.length} Total
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Session Documents Preview Card */}
                      <div className="glow-card" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                        <h3 style={{ fontSize: "15px", borderBottom: "1px solid var(--border-color)", paddingBottom: "12px", display: "flex", alignItems: "center", gap: "8px", margin: 0 }}>
                          <FileText style={{ width: "18px", height: "18px", color: "var(--accent-cyan)" }} />
                          Current Session Deal Documents
                        </h3>
                        {!sessionId ? (
                          <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                            No active procurement session. Open the <strong>Upload & Setup</strong> workspace to upload files and preview content.
                          </div>
                        ) : !vendorDetails.session_documents || vendorDetails.session_documents.uploaded_files?.length === 0 ? (
                          <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                            No documents have been uploaded for <strong>{vendorDetails.profile.name}</strong> in the current session.
                          </div>
                        ) : (
                          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
                              {vendorDetails.session_documents.has_email && (
                                <button
                                  onClick={() => fetchDocumentPreview(vendorDetails.profile.name, "email")}
                                  className={`btn-secondary ${previewDocType === "email" ? "active" : ""}`}
                                  style={{ padding: "6px 12px", fontSize: "12px", border: previewDocType === "email" ? "1px solid var(--accent-cyan)" : "" }}
                                >
                                  Preview Email
                                </button>
                              )}
                              {vendorDetails.session_documents.has_quote && (
                                <button
                                  onClick={() => fetchDocumentPreview(vendorDetails.profile.name, "quotation")}
                                  className={`btn-secondary ${previewDocType === "quotation" ? "active" : ""}`}
                                  style={{ padding: "6px 12px", fontSize: "12px", border: previewDocType === "quotation" ? "1px solid var(--accent-cyan)" : "" }}
                                >
                                  Preview Quotation
                                </button>
                              )}
                              {vendorDetails.session_documents.has_contract && (
                                <button
                                  onClick={() => fetchDocumentPreview(vendorDetails.profile.name, "contract")}
                                  className={`btn-secondary ${previewDocType === "contract" ? "active" : ""}`}
                                  style={{ padding: "6px 12px", fontSize: "12px", border: previewDocType === "contract" ? "1px solid var(--accent-cyan)" : "" }}
                                >
                                  Preview Contract
                                </button>
                              )}
                              {vendorDetails.session_documents.has_meeting && (
                                <button
                                  onClick={() => fetchDocumentPreview(vendorDetails.profile.name, "meeting_notes")}
                                  className={`btn-secondary ${previewDocType === "meeting_notes" ? "active" : ""}`}
                                  style={{ padding: "6px 12px", fontSize: "12px", border: previewDocType === "meeting_notes" ? "1px solid var(--accent-cyan)" : "" }}
                                >
                                  Preview Transcript
                                </button>
                              )}
                            </div>

                            {previewDocType && (
                              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                  <span style={{ fontSize: "12px", fontWeight: "600", textTransform: "uppercase", color: "var(--accent-cyan)" }}>
                                    Document Preview: {previewDocType.replace("_", " ")}
                                  </span>
                                  <button
                                    onClick={() => { setPreviewDocType(null); setPreviewDocContent(""); }}
                                    style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "12px" }}
                                  >
                                    Collapse
                                  </button>
                                </div>
                                {previewLoading ? (
                                  <div className="doc-preview-area" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                                    <RefreshCw className="animate-spin-slow" style={{ width: "16px", height: "16px", marginRight: "8px" }} />
                                    Fetching document text...
                                  </div>
                                ) : previewError ? (
                                  <div className="doc-preview-area" style={{ color: "var(--status-failed)" }}>
                                    {previewError}
                                  </div>
                                ) : (
                                  <pre className="doc-preview-area">{previewDocContent}</pre>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Catalog Grid */}
                      <div className="glow-card">
                        <h3 style={{ fontSize: "15px", borderBottom: "1px solid var(--border-color)", paddingBottom: "12px", display: "flex", alignItems: "center", gap: "8px", margin: "0 0 16px 0" }}>
                          <Activity style={{ width: "18px", height: "18px", color: "var(--accent-cyan)" }} />
                          Catalog Offerings
                        </h3>
                        {vendorDetails.catalog.length === 0 ? (
                          <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                            No catalog items registered for this vendor.
                          </div>
                        ) : (
                          <div className="catalog-grid">
                            {vendorDetails.catalog.map((item) => (
                              <div key={item.id} className="catalog-card">
                                <span className="catalog-item-name">{item.item_description}</span>
                                <span className="catalog-item-price">${item.standard_unit_price.toLocaleString()}</span>
                                <span className="catalog-item-lead">Typical Lead Time: <strong>{item.typical_lead_time_days} days</strong></span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Purchase History Card */}
                      <div className="glow-card">
                        <h3 style={{ fontSize: "15px", borderBottom: "1px solid var(--border-color)", paddingBottom: "12px", display: "flex", alignItems: "center", gap: "8px", margin: "0 0 16px 0" }}>
                          <History style={{ width: "18px", height: "18px", color: "var(--accent-cyan)" }} />
                          Purchase History Records
                        </h3>
                        {vendorDetails.purchase_history.length === 0 ? (
                          <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                            No past transactions found for this vendor.
                          </div>
                        ) : (
                          <div style={{ overflowX: "auto" }}>
                            <table className="audit-table">
                              <thead>
                                <tr>
                                  <th>Order ID</th>
                                  <th>Order Date</th>
                                  <th>Price</th>
                                  <th>Qty</th>
                                  <th>Total Amount</th>
                                  <th>Status</th>
                                  <th>Rating</th>
                                </tr>
                              </thead>
                              <tbody>
                                {vendorDetails.purchase_history.map((record) => (
                                  <tr key={record.purchase_id}>
                                    <td style={{ fontFamily: "monospace", color: "var(--text-muted)" }}>{record.purchase_id}</td>
                                    <td>{record.date}</td>
                                    <td>${record.unit_price.toLocaleString()}</td>
                                    <td>{record.qty}</td>
                                    <td style={{ fontWeight: "700" }}>${record.amount.toLocaleString()}</td>
                                    <td>
                                      <span className={`badge-status ${record.status === "Completed" ? "completed" : "pending"}`}>
                                        {record.status}
                                      </span>
                                    </td>
                                    <td>★ {record.rating.toFixed(1)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}


          </div>
        </div>
      </main>
    </div>
  );
}
