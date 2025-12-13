# data_models.py
import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator

class Proposal(BaseModel):
    id: str
    title: str
    description: str
    requirements: Dict[str, Any]
    problem_understanding_moai: str
    solution_proposal_moai: str
    scope_moai: str
    technologies_suggested_moai: Union[str, List[str]]
    estimated_value_moai: Optional[float] = Field(default=None)
    estimated_time_moai: str
    terms_conditions_moai: str
    status: str
    submitted_at: datetime.datetime
    approved_at: Optional[datetime.datetime] = None
    
    @field_validator('technologies_suggested_moai', mode='before')
    @classmethod
    def convert_tech_list_to_string(cls, v):
        """Converte listas de tecnologias em string formatada"""
        if v is None:
            return ""
        if isinstance(v, list):
            return ", ".join([str(tech).strip() for tech in v if tech])
        return str(v).strip() if v else ""

class Project(BaseModel):
    id: str
    proposal_id: str
    name: str
    client_name: str
    status: str
    progress: int
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None

class GeneratedCode(BaseModel):
    id: str
    project_id: str
    filename: str
    language: str
    content: str
    description: str
    generated_at: datetime.datetime

class QualityReport(BaseModel):
    id: str
    project_id: str
    report_data: Dict[str, Any]
    generated_at: datetime.datetime

class SecurityReport(BaseModel):
    id: str
    project_id: str
    report_data: Dict[str, Any]
    generated_at: datetime.datetime

class Documentation(BaseModel):
    id: str
    project_id: str
    filename: str
    content: str
    document_type: str
    version: Optional[str] = None
    last_updated: Optional[datetime.datetime] = None

class MonitoringSummary(BaseModel):
    id: str
    project_id: Optional[str]
    summary_data: Dict[str, Any]
    generated_at: datetime.datetime

class ChatMessage(BaseModel):
    id: str
    sender: str
    message: str
    timestamp: datetime.datetime

class MOAILog(BaseModel):
    id: str
    timestamp: datetime.datetime
    event_type: str
    details: str
    project_id: Optional[str] = None
    agent_id: Optional[str] = None
    status: str