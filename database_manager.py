# database_manager.py

import sqlite3
import datetime
import json
from data_models import MoaiLog, ChatMessage, Proposal, Project, GeneratedCode

class DatabaseManager:
    _instance = None

    def __new__(cls, db_name="synapse_forge.db"):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.db_name = db_name
            cls._instance.conn = None
            cls._instance.cursor = None
            cls._instance.connect()
            cls._instance.create_tables()
        return cls._instance

    def connect(self):
        if self.conn is None:
            # check_same_thread=False allows multiple threads to access the DB, necessary for Streamlit reruns
            self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row # Allows accessing columns by name
            self.cursor = self.conn.cursor()

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def create_tables(self):
        self.connect()
        # Tabela moai_logs
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS moai_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT NOT NULL
            )
        """)
        # Tabela chat_history
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        # Tabela proposals (ATUALIZADA)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                requirements TEXT NOT NULL,
                status TEXT NOT NULL,
                submitted_at TEXT NOT NULL,
                problem_understanding_moai TEXT,
                solution_proposal_moai TEXT,
                scope_moai TEXT,
                technologies_suggested_moai TEXT,
                estimated_value_moai TEXT,
                estimated_time_moai TEXT,
                terms_conditions_moai TEXT
            )
        """)
        # Tabela projects
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                db_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                client_name TEXT NOT NULL,
                status TEXT NOT NULL,
                progress INTEGER NOT NULL,
                proposal_id INTEGER,
                FOREIGN KEY(proposal_id) REFERENCES proposals(id)
            )
        """)
        # Tabela generated_code (NOVA)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS generated_code (
                db_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                proposal_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                content TEXT NOT NULL,
                language TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(project_id),
                FOREIGN KEY(proposal_id) REFERENCES proposals(id)
            )
        """)
        self.conn.commit()

    def insert_moai_log(self, action: str, details: dict):
        self.connect()
        timestamp = datetime.datetime.now().isoformat()
        self.cursor.execute(
            "INSERT INTO moai_logs (timestamp, action, details) VALUES (?, ?, ?)",
            (timestamp, action, json.dumps(details))
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_moai_logs(self):
        self.connect()
        self.cursor.execute("SELECT id, timestamp, action, details FROM moai_logs ORDER BY timestamp DESC")
        rows = self.cursor.fetchall()
        logs = []
        for row in rows:
            logs.append(MoaiLog(row["id"], datetime.datetime.fromisoformat(row["timestamp"]), row["action"], json.loads(row["details"])))
        return logs

    def insert_chat_message(self, role: str, content: str):
        self.connect()
        timestamp = datetime.datetime.now().isoformat()
        self.cursor.execute(
            "INSERT INTO chat_history (role, content, timestamp) VALUES (?, ?, ?)",
            (timestamp, role, content) # Corrected order for placeholder values
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_chat_history(self):
        self.connect()
        self.cursor.execute("SELECT id, role, content, timestamp FROM chat_history ORDER BY timestamp ASC")
        rows = self.cursor.fetchall()
        messages = []
        for row in rows:
            messages.append(ChatMessage(row["id"], row["role"], row["content"], datetime.datetime.fromisoformat(row["timestamp"])))
        return messages

    # ATUALIZADO: insert_proposal com novos campos
    def insert_proposal(self, proposal: Proposal):
        self.connect()
        self.cursor.execute(
            """INSERT INTO proposals (
                title, description, requirements, status, submitted_at,
                problem_understanding_moai, solution_proposal_moai, scope_moai,
                technologies_suggested_moai, estimated_value_moai, estimated_time_moai,
                terms_conditions_moai
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                proposal.title,
                proposal.description,
                json.dumps(proposal.requirements),
                proposal.status,
                proposal.submitted_at.isoformat(),
                proposal.problem_understanding_moai,
                proposal.solution_proposal_moai,
                proposal.scope_moai,
                proposal.technologies_suggested_moai,
                proposal.estimated_value_moai,
                proposal.estimated_time_moai,
                proposal.terms_conditions_moai
            )
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def update_proposal_status(self, proposal_id: int, status: str):
        self.connect()
        self.cursor.execute(
            "UPDATE proposals SET status = ? WHERE id = ?",
            (status, proposal_id)
        )
        self.conn.commit()

    def get_proposal_by_id(self, proposal_id: int):
        self.connect()
        self.cursor.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,))
        row = self.cursor.fetchone()
        if row:
            return self.proposal_from_row(row)
        return None

    def get_proposals_by_status(self, status: str):
        self.connect()
        self.cursor.execute("SELECT * FROM proposals WHERE status = ? ORDER BY submitted_at DESC", (status,))
        rows = self.cursor.fetchall()
        return [self.proposal_from_row(row) for row in rows]

    def get_all_proposals(self):
        self.connect()
        self.cursor.execute("SELECT * FROM proposals ORDER BY submitted_at DESC")
        rows = self.cursor.fetchall()
        return [self.proposal_from_row(row) for row in rows]
    
    def get_pending_proposals_count(self):
        self.connect()
        self.cursor.execute("SELECT COUNT(*) FROM proposals WHERE status = 'pending'")
        count = self.cursor.fetchone()[0]
        return count

    # ATUALIZADO: proposal_from_row para incluir novos campos (usa row_factory)
    def proposal_from_row(self, row):
        return Proposal(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            requirements=json.loads(row["requirements"]),
            status=row["status"],
            submitted_at=datetime.datetime.fromisoformat(row["submitted_at"]),
            problem_understanding_moai=row["problem_understanding_moai"],
            solution_proposal_moai=row["solution_proposal_moai"],
            scope_moai=row["scope_moai"],
            technologies_suggested_moai=row["technologies_suggested_moai"],
            estimated_value_moai=row["estimated_value_moai"],
            estimated_time_moai=row["estimated_time_moai"],
            terms_conditions_moai=row["terms_conditions_moai"]
        )

    # --- Métodos para Projects ---
    def insert_project(self, project: Project):
        self.connect()
        self.cursor.execute(
            "INSERT INTO projects (project_id, name, client_name, status, progress, proposal_id) VALUES (?, ?, ?, ?, ?, ?)",
            (project.project_id, project.name, project.client_name, project.status, project.progress, project.proposal_id)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_project_by_id(self, project_db_id: int):
        self.connect()
        self.cursor.execute("SELECT db_id, project_id, name, client_name, status, progress, proposal_id FROM projects WHERE db_id = ?", (project_db_id,))
        row = self.cursor.fetchone()
        if row:
            return Project(row["db_id"], row["project_id"], row["name"], row["client_name"], row["status"], row["progress"], row["proposal_id"])
        return None
        
    def get_project_by_proposal_id(self, proposal_id: int):
        self.connect()
        self.cursor.execute("SELECT db_id, project_id, name, client_name, status, progress, proposal_id FROM projects WHERE proposal_id = ?", (proposal_id,))
        row = self.cursor.fetchone()
        if row:
            return Project(row["db_id"], row["project_id"], row["name"], row["client_name"], row["status"], row["progress"], row["proposal_id"])
        return None

    def get_all_projects(self):
        self.connect()
        self.cursor.execute("SELECT db_id, project_id, name, client_name, status, progress, proposal_id FROM projects")
        rows = self.cursor.fetchall()
        return [Project(row["db_id"], row["project_id"], row["name"], row["client_name"], row["status"], row["progress"], row["proposal_id"]) for row in rows]
    
    def update_project_status(self, project_db_id: int, status: str):
        self.connect()
        self.cursor.execute(
            "UPDATE projects SET status = ? WHERE db_id = ?",
            (status, project_db_id)
        )
        self.conn.commit()

    # --- Métodos para GeneratedCode ---
    def insert_generated_code(self, generated_code: GeneratedCode):
        self.connect()
        self.cursor.execute(
            """INSERT INTO generated_code (project_id, proposal_id, filename, content, language, generated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                generated_code.project_id,
                generated_code.proposal_id,
                generated_code.filename,
                generated_code.content,
                generated_code.language,
                generated_code.generated_at.isoformat()
            )
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_generated_code_for_project(self, project_db_id: int):
        self.connect()
        # Precisamos do project_id STRING, não do db_id INTEGER
        self.cursor.execute("SELECT project_id FROM projects WHERE db_id = ?", (project_db_id,))
        project_id_str_row = self.cursor.fetchone()
        if not project_id_str_row:
            return [] # Projeto não encontrado

        project_id_str = project_id_str_row["project_id"] # Access by name

        self.cursor.execute(
            "SELECT db_id, project_id, proposal_id, filename, content, language, generated_at FROM generated_code WHERE project_id = ?",
            (project_id_str,)
        )
        rows = self.cursor.fetchall()
        code_files = []
        for row in rows:
            code_files.append(
                GeneratedCode(
                    db_id=row["db_id"],
                    project_id=row["project_id"],
                    proposal_id=row["proposal_id"],
                    filename=row["filename"],
                    content=row["content"],
                    language=row["language"],
                    generated_at=datetime.datetime.fromisoformat(row["generated_at"])
                )
            )
        return code_files