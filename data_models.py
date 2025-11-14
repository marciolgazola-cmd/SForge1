# data_models.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

@dataclass
class ChatMessage:
    sender: str # "user" or "ai"
    message: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Proposal:
    id: str
    title: str
    description: str
    status: str # "pending", "approved", "rejected"
    submitted_at: datetime = field(default_factory=datetime.now)
    # The 'requirements' dict from the form submission
    requirements: Dict[str, Any] = field(default_factory=dict)
    # MOAI generated content fields
    problem_understanding_moai: str = ""
    solution_proposal_moai: str = ""
    scope_moai: str = ""
    technologies_suggested_moai: str = ""
    estimated_value_moai: str = "R$ 0,00"
    estimated_time_moai: str = "A definir"
    terms_conditions_moai: str = ""
    project_id: Optional[str] = None # ID do projeto se a proposta for aprovada

@dataclass
class Project:
    project_id: str # Renamed from 'id' to match user's cognitolink and be explicit
    name: str
    client_name: str
    status: str # "active", "completed", "on hold", "cancelled"
    progress: int = 0 # Percentage
    proposal_id: Optional[str] = None # Link back to the proposal that created it
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class GeneratedCode:
    id: str
    project_id: str
    filename: str # New field for filename for better viewing
    content: str  # Renamed from code_content for consistency
    language: str # Ex: "Python", "JavaScript", "SQL"
    description: str
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class QualityReportEntry: # Renamed from QualityReport to avoid confusion with the backend report object
    id: str
    project_id: str
    summary: str
    details: str
    score: float # Ex: 0.0 a 1.0
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class SecurityReportEntry: # Renamed from SecurityReport
    id: str
    project_id: str
    summary: str
    details: str
    vulnerabilities_found: int
    severity_level: str # Ex: "Low", "Medium", "High", "Critical"
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Documentation:
    id: str
    project_id: str
    filename: str
    content: str
    format: str # Ex: "Markdown", "PDF"
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class MonitoringSummary:
    id: str
    project_id: str
    summary: str # Textual summary of monitoring status
    status: str # "Operational", "Warning", "Critical"
    metrics_snapshot: str # JSON string of key metrics (CPU, RAM, etc.)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class MOAILog:
    id: str
    timestamp: datetime
    event_type: str # Ex: "PROPOSAL_CREATED", "PROJECT_APPROVED", "AGENT_TASK_ASSIGNED"
    description: str
    details: Optional[str] = None # JSON string of additional relevant data