# database_manager.py
import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

from data_models import (
    Proposal, Project, GeneratedCode, QualityReportEntry,
    SecurityReportEntry, Documentation, MonitoringSummary, MOAILog, ChatMessage
)

class DatabaseManager:
    def __init__(self, db_path="synapse_forge.db"):
        self.db_path = db_path
        print(f"DEBUG: DatabaseManager inicializado. Caminho do DB: {self.db_path}")
        self._create_tables()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;") # Ensure foreign key constraints are enforced
        return conn

    def _create_tables(self):
        print(f"DEBUG: Tentando criar/verificar tabelas em {self.db_path}...")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Table for Chat Messages
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id TEXT PRIMARY KEY,
                        sender TEXT NOT NULL,
                        message TEXT NOT NULL,
                        timestamp TEXT NOT NULL
                    )
                """)
                print("DEBUG: Tabela 'chat_messages' processada.")
                # Table for Proposals
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS proposals (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        status TEXT NOT NULL,
                        submitted_at TEXT NOT NULL,
                        requirements TEXT,
                        problem_understanding_moai TEXT,
                        solution_proposal_moai TEXT,
                        scope_moai TEXT,
                        technologies_suggested_moai TEXT,
                        estimated_value_moai TEXT,
                        estimated_time_moai TEXT,
                        terms_conditions_moai TEXT,
                        project_id TEXT UNIQUE
                    )
                """)
                print("DEBUG: Tabela 'proposals' processada.")
                # Table for Projects
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        project_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        client_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        progress INTEGER,
                        proposal_id TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (proposal_id) REFERENCES proposals(id) ON DELETE CASCADE
                    )
                """)
                print("DEBUG: Tabela 'projects' processada.")
                # Table for Generated Code
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS generated_code (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        content TEXT NOT NULL,
                        language TEXT,
                        description TEXT,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
                    )
                """)
                print("DEBUG: Tabela 'generated_code' processada.")
                # Table for Quality Reports
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS quality_reports (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        summary TEXT,
                        details TEXT,
                        score REAL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
                    )
                """)
                print("DEBUG: Tabela 'quality_reports' processada.")
                # Table for Security Reports
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS security_reports (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        summary TEXT,
                        details TEXT,
                        vulnerabilities_found INTEGER,
                        severity_level TEXT,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
                    )
                """)
                print("DEBUG: Tabela 'security_reports' processada.")
                # Table for Documentation
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS documentation (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        content TEXT NOT NULL,
                        format TEXT,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
                    )
                """)
                print("DEBUG: Tabela 'documentation' processada.")
                # Table for Monitoring Summaries
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS monitoring_summaries (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        summary TEXT,
                        status TEXT,
                        metrics_snapshot TEXT,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
                    )
                """)
                print("DEBUG: Tabela 'monitoring_summaries' processada.")
                # Table for MOAI Logs
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS moai_logs (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        details TEXT
                    )
                """)
                print("DEBUG: Tabela 'moai_logs' processada.")
                conn.commit()
                print("DEBUG: Criação/verificação de tabelas concluída e commitada.")
        except sqlite3.Error as e:
            print(f"ERRO CRÍTICO DB: Falha ao criar tabelas da base de dados: {e}")
            raise # Re-lança a exceção para que ela não seja engolida silenciosamente

    # --- Chat Messages ---
    def add_chat_message(self, message: ChatMessage):
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO chat_messages (id, sender, message, timestamp)
                VALUES (?, ?, ?, ?)
            """, (str(uuid.uuid4()), message.sender, message.message, message.timestamp.isoformat()))
            conn.commit()

    def get_chat_history(self) -> List[ChatMessage]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM chat_messages ORDER BY timestamp ASC")
            return [ChatMessage(id=row['id'], sender=row['sender'], message=row['message'], timestamp=datetime.fromisoformat(row['timestamp'])) for row in cursor.fetchall()]

    # --- Proposals ---
    def add_proposal(self, proposal: Proposal):
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO proposals (id, title, description, status, submitted_at, requirements,
                                       problem_understanding_moai, solution_proposal_moai, scope_moai,
                                       technologies_suggested_moai, estimated_value_moai, estimated_time_moai,
                                       terms_conditions_moai, project_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal.id, proposal.title, proposal.description, proposal.status, proposal.submitted_at.isoformat(),
                json.dumps(proposal.requirements), proposal.problem_understanding_moai,
                proposal.solution_proposal_moai, proposal.scope_moai, proposal.technologies_suggested_moai,
                proposal.estimated_value_moai, proposal.estimated_time_moai, proposal.terms_conditions_moai,
                proposal.project_id
            ))
            conn.commit()

    def get_proposal_by_id(self, proposal_id: str) -> Optional[Proposal]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,))
            row = cursor.fetchone()
            if row:
                return Proposal(
                    id=row['id'],
                    title=row['title'],
                    description=row['description'],
                    status=row['status'],
                    submitted_at=datetime.fromisoformat(row['submitted_at']),
                    requirements=json.loads(row['requirements']) if row['requirements'] else {},
                    problem_understanding_moai=row['problem_understanding_moai'],
                    solution_proposal_moai=row['solution_proposal_moai'],
                    scope_moai=row['scope_moai'],
                    technologies_suggested_moai=row['technologies_suggested_moai'],
                    estimated_value_moai=row['estimated_value_moai'],
                    estimated_time_moai=row['estimated_time_moai'],
                    terms_conditions_moai=row['terms_conditions_moai'],
                    project_id=row['project_id']
                )
            return None
    
    def get_proposals(self, status: Optional[str] = None) -> List[Proposal]:
        with self._get_connection() as conn:
            query = "SELECT * FROM proposals"
            params = []
            if status:
                query += " WHERE status = ?"
                params.append(status)
            cursor = conn.execute(query, params)
            return [
                Proposal(
                    id=row['id'],
                    title=row['title'],
                    description=row['description'],
                    status=row['status'],
                    submitted_at=datetime.fromisoformat(row['submitted_at']),
                    requirements=json.loads(row['requirements']) if row['requirements'] else {},
                    problem_understanding_moai=row['problem_understanding_moai'],
                    solution_proposal_moai=row['solution_proposal_moai'],
                    scope_moai=row['scope_moai'],
                    technologies_suggested_moai=row['technologies_suggested_moai'],
                    estimated_value_moai=row['estimated_value_moai'],
                    estimated_time_moai=row['estimated_time_moai'],
                    terms_conditions_moai=row['terms_conditions_moai'],
                    project_id=row['project_id']
                )
                for row in cursor.fetchall()
            ]

    def update_proposal_status(self, proposal_id: str, new_status: str):
        with self._get_connection() as conn:
            conn.execute("UPDATE proposals SET status = ? WHERE id = ?", (new_status, proposal_id))
            conn.commit()

    def update_proposal_content(self, proposal_id: str, updated_fields: Dict[str, Any]):
        with self._get_connection() as conn:
            set_clauses = []
            params = []
            for key, value in updated_fields.items():
                if key == 'requirements': # Store as JSON string
                    set_clauses.append(f"{key} = ?")
                    params.append(json.dumps(value))
                else:
                    set_clauses.append(f"{key} = ?")
                    params.append(value)
            
            if set_clauses:
                query = f"UPDATE proposals SET {', '.join(set_clauses)} WHERE id = ?"
                params.append(proposal_id)
                conn.execute(query, params)
                conn.commit()

    def update_proposal_project_id(self, proposal_id: str, project_id: str):
        with self._get_connection() as conn:
            conn.execute("UPDATE proposals SET project_id = ? WHERE id = ?", (project_id, proposal_id))
            conn.commit()
    
    # --- Projects ---
    def add_project(self, project: Project):
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO projects (project_id, name, client_name, status, progress, proposal_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project.project_id, project.name, project.client_name, project.status, project.progress,
                project.proposal_id, project.created_at.isoformat(), project.updated_at.isoformat()
            ))
            conn.commit()

    def get_project_by_id(self, project_id: str) -> Optional[Project]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,))
            row = cursor.fetchone()
            if row:
                return Project(
                    project_id=row['project_id'],
                    name=row['name'],
                    client_name=row['client_name'],
                    status=row['status'],
                    progress=row['progress'],
                    proposal_id=row['proposal_id'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
            return None

    def get_all_projects(self) -> List[Project]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM projects")
            return [
                Project(
                    project_id=row['project_id'],
                    name=row['name'],
                    client_name=row['client_name'],
                    status=row['status'],
                    progress=row['progress'],
                    proposal_id=row['proposal_id'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
                for row in cursor.fetchall()
            ]

    def update_project_details(self, project_id: str, updated_fields: Dict[str, Any]):
        with self._get_connection() as conn:
            set_clauses = []
            params = []
            for key, value in updated_fields.items():
                set_clauses.append(f"{key} = ?")
                params.append(value)
            
            if set_clauses:
                query = f"UPDATE projects SET {', '.join(set_clauses)}, updated_at = ? WHERE project_id = ?"
                params.append(datetime.now().isoformat())
                params.append(project_id)
                conn.execute(query, params)
                conn.commit()

    # --- Generated Code ---
    def add_generated_code(self, code: GeneratedCode):
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO generated_code (id, project_id, filename, content, language, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (code.id, code.project_id, code.filename, code.content, code.language, code.description, code.created_at.isoformat()))
            conn.commit()

    def get_generated_code_for_project(self, project_id: str) -> List[GeneratedCode]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM generated_code WHERE project_id = ?", (project_id,))
            return [
                GeneratedCode(
                    id=row['id'],
                    project_id=row['project_id'],
                    filename=row['filename'],
                    content=row['content'],
                    language=row['language'],
                    description=row['description'],
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                for row in cursor.fetchall()
            ]

    # --- Quality Reports ---
    def add_quality_report(self, report: QualityReportEntry):
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO quality_reports (id, project_id, summary, details, score, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (report.id, report.project_id, report.summary, report.details, report.score, report.created_at.isoformat()))
            conn.commit()

    def get_quality_reports_for_project(self, project_id: str) -> List[QualityReportEntry]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM quality_reports WHERE project_id = ?", (project_id,))
            return [
                QualityReportEntry(
                    id=row['id'],
                    project_id=row['project_id'],
                    summary=row['summary'],
                    details=row['details'],
                    score=row['score'],
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                for row in cursor.fetchall()
            ]

    # --- Security Reports ---
    def add_security_report(self, report: SecurityReportEntry):
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO security_reports (id, project_id, summary, details, vulnerabilities_found, severity_level, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (report.id, report.project_id, report.summary, report.details, report.vulnerabilities_found, report.severity_level, report.created_at.isoformat()))
            conn.commit()

    def get_security_reports_for_project(self, project_id: str) -> List[SecurityReportEntry]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM security_reports WHERE project_id = ?", (project_id,))
            return [
                SecurityReportEntry(
                    id=row['id'],
                    project_id=row['project_id'],
                    summary=row['summary'],
                    details=row['details'],
                    vulnerabilities_found=row['vulnerabilities_found'],
                    severity_level=row['severity_level'],
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                for row in cursor.fetchall()
            ]

    # --- Documentation ---
    def add_documentation(self, doc: Documentation):
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO documentation (id, project_id, filename, content, format, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (doc.id, doc.project_id, doc.filename, doc.content, doc.format, doc.created_at.isoformat()))
            conn.commit()

    def get_documentation_by_project(self, project_id: str) -> List[Documentation]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM documentation WHERE project_id = ?", (project_id,))
            return [
                Documentation(
                    id=row['id'],
                    project_id=row['project_id'],
                    filename=row['filename'],
                    content=row['content'],
                    format=row['format'],
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                for row in cursor.fetchall()
            ]
            
    # --- Monitoring Summaries ---
    def add_monitoring_summary(self, summary: MonitoringSummary):
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO monitoring_summaries (id, project_id, summary, status, metrics_snapshot, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (summary.id, summary.project_id, summary.summary, summary.status, summary.metrics_snapshot, summary.created_at.isoformat()))
            conn.commit()

    def get_monitoring_summary_by_project(self, project_id: str) -> Optional[MonitoringSummary]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM monitoring_summaries WHERE project_id = ? ORDER BY created_at DESC LIMIT 1", (project_id,))
            row = cursor.fetchone()
            if row:
                return MonitoringSummary(
                    id=row['id'],
                    project_id=row['project_id'],
                    summary=row['summary'],
                    status=row['status'],
                    metrics_snapshot=row['metrics_snapshot'],
                    created_at=datetime.fromisoformat(row['created_at'])
                )
            return None

    # --- MOAI Logs ---
    def add_moai_log(self, log: MOAILog):
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO moai_logs (id, timestamp, event_type, description, details)
                VALUES (?, ?, ?, ?, ?)
            """, (log.id, log.timestamp.isoformat(), log.event_type, log.description, log.details))
            conn.commit()

    def get_all_moai_logs(self) -> List[MOAILog]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM moai_logs ORDER BY timestamp DESC")
            return [
                MOAILog(
                    id=row['id'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    event_type=row['event_type'],
                    description=row['description'],
                    details=row['details']
                )
                for row in cursor.fetchall()
            ]
            
    # --- EXCLUSÃO EM CASCATA ---
    def delete_proposal_and_related_data(self, proposal_id: str) -> bool:
        """
        Deletes a proposal and all related data (projects, generated code, reports, docs, monitoring)
        due to ON DELETE CASCADE constraints.
        Returns True if successful, False otherwise.
        """
        try:
            with self._get_connection() as conn:
                # The ON DELETE CASCADE will handle projects and their children.
                # Just delete the proposal.
                conn.execute("DELETE FROM proposals WHERE id = ?", (proposal_id,))
                conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting proposal {proposal_id} and related data: {e}")
            return False

    def close(self):
        # In a typical Streamlit app, connections are managed by context,
        # but this method is here for completeness if explicit closing is needed.
        pass