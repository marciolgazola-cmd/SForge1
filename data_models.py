# data_models.py

import json
import datetime
from typing import Dict, Any, Optional

class MoaiLog:
    def __init__(self, id: int, timestamp: datetime.datetime, action: str, details: Dict):
        self.id = id
        self.timestamp = timestamp
        self.action = action
        self.details = details

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "details": self.details
        }

class ChatMessage:
    def __init__(self, id: int, role: str, content: str, timestamp: datetime.datetime):
        self.id = id
        self.role = role
        self.content = content
        self.timestamp = timestamp

    def to_dict(self):
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }

class Project:
    def __init__(self, db_id: int, project_id: str, name: str, client_name: str, status: str, progress: int, proposal_id: int):
        self.db_id = db_id
        self.project_id = project_id
        self.name = name
        self.client_name = client_name
        self.status = status
        self.progress = progress
        self.proposal_id = proposal_id # Link para a proposta que gerou o projeto

    def to_dict(self):
        return {
            "db_id": self.db_id,
            "project_id": self.project_id,
            "name": self.name,
            "client_name": self.client_name,
            "status": self.status,
            "progress": self.progress,
            "proposal_id": self.proposal_id
        }

class GeneratedCode:
    def __init__(self, db_id: int, project_id: str, proposal_id: int, filename: str, content: str, language: str, generated_at: datetime.datetime):
        self.db_id = db_id
        self.project_id = project_id
        self.proposal_id = proposal_id
        self.filename = filename
        self.content = content
        self.language = language
        self.generated_at = generated_at

    def to_dict(self):
        return {
            "db_id": self.db_id,
            "project_id": self.project_id,
            "proposal_id": self.proposal_id,
            "filename": self.filename,
            "content": self.content,
            "language": self.language,
            "generated_at": self.generated_at.isoformat()
        }

class Proposal:
    def __init__(
        self,
        id: int,
        title: str,
        description: str,
        requirements: Dict[str, Any],
        status: str,
        submitted_at: datetime.datetime,
        # Novos campos para detalhes gerados pelo MOAI
        problem_understanding_moai: Optional[str] = None,
        solution_proposal_moai: Optional[str] = None,
        scope_moai: Optional[str] = None,
        technologies_suggested_moai: Optional[str] = None,
        estimated_value_moai: Optional[str] = None,
        estimated_time_moai: Optional[str] = None,
        terms_conditions_moai: Optional[str] = None
    ):
        self.id = id
        self.title = title
        self.description = description
        self.requirements = requirements
        self.status = status
        self.submitted_at = submitted_at
        self.problem_understanding_moai = problem_understanding_moai
        self.solution_proposal_moai = solution_proposal_moai
        self.scope_moai = scope_moai
        self.technologies_suggested_moai = technologies_suggested_moai
        self.estimated_value_moai = estimated_value_moai
        self.estimated_time_moai = estimated_time_moai
        self.terms_conditions_moai = terms_conditions_moai

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "requirements": self.requirements,
            "status": self.status,
            "submitted_at": self.submitted_at.isoformat(),
            "problem_understanding_moai": self.problem_understanding_moai,
            "solution_proposal_moai": self.solution_proposal_moai,
            "scope_moai": self.scope_moai,
            "technologies_suggested_moai": self.technologies_suggested_moai,
            "estimated_value_moai": self.estimated_value_moai,
            "estimated_time_moai": self.estimated_time_moai,
            "terms_conditions_moai": self.terms_conditions_moai
        }

# Mantém a classe Requirement se ainda for usada em algum lugar,
# mas para as propostas, estamos usando um dicionário de requisitos.
class Requirement:
    def __init__(self, nome_projeto: str, nome_cliente: str, problema_negocio: str, objetivos_projeto: str, funcionalidades_esperadas: str, restricoes: str, publico_alvo: str):
        self.nome_projeto = nome_projeto
        self.nome_cliente = nome_cliente
        self.problema_negocio = problema_negocio
        self.objetivos_projeto = objetivos_projeto
        self.funcionalidades_esperadas = funcionalidades_esperadas
        self.restricoes = restricoes
        self.publico_alvo = publico_alvo

    def to_dict(self):
        return {
            "nome_projeto": self.nome_projeto,
            "nome_cliente": self.nome_cliente,
            "problema_negocio": self.problema_negocio,
            "objetivos_projeto": self.objetivos_projeto,
            "funcionalidades_esperadas": self.funcionalidades_esperadas,
            "restricoes": self.restricoes,
            "publico_alvo": self.publico_alvo
        }