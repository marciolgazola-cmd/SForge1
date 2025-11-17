# database_manager.py
import sqlite3
import json
import datetime
from typing import List, Dict, Any, Optional
import logging

# Importa os modelos do novo arquivo models.py
from models import Proposal, Project, GeneratedCode, QualityReport, SecurityReport, Documentation, MonitoringSummary, ChatMessage, MOAILog

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        logging.info(f"DatabaseManager inicializado. Banco de dados: {self.db_path}")
        self.initialize_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.row_factory = sqlite3.Row # Permite acessar colunas por nome
        return conn

    def initialize_db(self):
        conn = self._connect()
        cursor = conn.cursor()

        # Tabela de Propostas (estimated_value_moai agora é REAL para float)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proposals (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                requirements TEXT,
                problem_understanding_moai TEXT,
                solution_proposal_moai TEXT,
                scope_moai TEXT,
                technologies_suggested_moai TEXT,
                estimated_value_moai REAL,
                estimated_time_moai TEXT,
                terms_conditions_moai TEXT,
                status TEXT NOT NULL,
                submitted_at TIMESTAMP,
                approved_at TIMESTAMP
            )
        """)

        # Tabela de Projetos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                proposal_id TEXT,
                name TEXT NOT NULL,
                client_name TEXT,
                status TEXT NOT NULL,
                progress INTEGER,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (proposal_id) REFERENCES proposals (id)
            )
        """)

        # Tabela de Código Gerado
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generated_code (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                filename TEXT NOT NULL,
                language TEXT,
                content TEXT,
                description TEXT,
                generated_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)

        # Tabela de Relatórios de Qualidade
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_reports (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                report_data TEXT, -- Armazenar como JSON
                generated_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)

        # Tabela de Relatórios de Segurança
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_reports (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                report_data TEXT, -- Armazenar como JSON
                generated_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)

        # Tabela de Documentação
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documentation (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                filename TEXT NOT NULL,
                content TEXT,
                document_type TEXT,
                version TEXT,
                last_updated TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)

        # Tabela de Resumos de Monitoramento
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitoring_summaries (
                id TEXT PRIMARY KEY,
                project_id TEXT, -- NULL para resumos globais
                summary_data TEXT, -- Armazenar como JSON
                generated_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        
        # Tabela de Histórico de Chat do MOAI
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id TEXT PRIMARY KEY,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP
            )
        """)

        # Tabela de Logs do MOAI
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS moai_logs (
                id TEXT PRIMARY KEY,
                timestamp TIMESTAMP,
                event_type TEXT,
                details TEXT,
                project_id TEXT,
                agent_id TEXT,
                status TEXT
            )
        """)


        conn.commit()
        conn.close()
        logging.info("Banco de dados inicializado/verificado com sucesso.")

    def add_proposal(self, proposal_data: Dict[str, Any]):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO proposals (id, title, description, requirements, problem_understanding_moai,
                                       solution_proposal_moai, scope_moai, technologies_suggested_moai,
                                       estimated_value_moai, estimated_time_moai, terms_conditions_moai,
                                       status, submitted_at, approved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal_data["id"], proposal_data["title"], proposal_data["description"],
                json.dumps(proposal_data["requirements"]), proposal_data["problem_understanding_moai"],
                proposal_data["solution_proposal_moai"], proposal_data["scope_moai"],
                proposal_data["technologies_suggested_moai"], proposal_data["estimated_value_moai"], # Agora é float
                proposal_data["estimated_time_moai"], proposal_data["terms_conditions_moai"],
                proposal_data["status"], proposal_data["submitted_at"], proposal_data["approved_at"]
            ))
            conn.commit()
            logging.info(f"Proposta {proposal_data['id'][:8]}... adicionada com sucesso.")
        except sqlite3.Error as e:
            logging.error(f"Erro ao adicionar proposta: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_all_proposals(self) -> List[Proposal]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM proposals")
        rows = cursor.fetchall()
        conn.close()
        proposals = []
        for row in rows:
            proposal_dict = dict(row)
            proposal_dict["requirements"] = json.loads(proposal_dict["requirements"])
            proposals.append(Proposal(**proposal_dict))
        return proposals

    def get_proposals(self, status: Optional[str] = None) -> List[Proposal]:
        conn = self._connect()
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM proposals WHERE status = ?", (status,))
        else:
            cursor.execute("SELECT * FROM proposals")
        rows = cursor.fetchall()
        conn.close()
        proposals = []
        for row in rows:
            proposal_dict = dict(row)
            proposal_dict["requirements"] = json.loads(proposal_dict["requirements"])
            proposals.append(Proposal(**proposal_dict))
        return proposals

    def get_proposal_by_id(self, proposal_id: str) -> Optional[Proposal]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            proposal_dict = dict(row)
            proposal_dict["requirements"] = json.loads(proposal_dict["requirements"])
            return Proposal(**proposal_dict)
        return None

    def update_proposal(self, proposal_id: str, **kwargs):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            set_clauses = []
            values = []
            for key, value in kwargs.items():
                if key == "requirements": # Handle JSON field
                    set_clauses.append(f"{key} = ?")
                    values.append(json.dumps(value))
                elif isinstance(value, datetime.datetime): # Handle datetime objects
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
                else:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            if set_clauses:
                query = f"UPDATE proposals SET {', '.join(set_clauses)} WHERE id = ?"
                values.append(proposal_id)
                cursor.execute(query, tuple(values))
                conn.commit()
                logging.info(f"Proposta {proposal_id[:8]}... atualizada com sucesso.")
            else:
                logging.warning(f"Nenhum campo para atualizar para proposta {proposal_id[:8]}...")
        except sqlite3.Error as e:
            logging.error(f"Erro ao atualizar proposta {proposal_id[:8]}...: {e}")
            conn.rollback()
        finally:
            conn.close()

    def update_proposal_status(self, proposal_id: str, new_status: str):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            approved_at = datetime.datetime.now() if new_status == "approved" else None
            cursor.execute("UPDATE proposals SET status = ?, approved_at = ? WHERE id = ?",
                           (new_status, approved_at, proposal_id))
            conn.commit()
            logging.info(f"Status da proposta {proposal_id[:8]}... atualizado para {new_status}.")
        except sqlite3.Error as e:
            logging.error(f"Erro ao atualizar status da proposta {proposal_id[:8]}...: {e}")
            conn.rollback()
        finally:
            conn.close()

    def delete_proposal(self, proposal_id: str) -> bool:
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM proposals WHERE id = ?", (proposal_id,))
            conn.commit()
            logging.info(f"Proposta {proposal_id[:8]}... excluída com sucesso.")
            return True
        except sqlite3.Error as e:
            logging.error(f"Erro ao excluir proposta {proposal_id[:8]}...: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def add_project(self, project_data: Dict[str, Any]):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO projects (id, proposal_id, name, client_name, status, progress, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_data["id"], project_data["proposal_id"], project_data["name"],
                project_data["client_name"], project_data["status"], project_data["progress"],
                project_data["started_at"], project_data["completed_at"]
            ))
            conn.commit()
            logging.info(f"Projeto {project_data['id'][:8]}... adicionado com sucesso.")
        except sqlite3.Error as e:
            logging.error(f"Erro ao adicionar projeto: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_all_projects(self) -> List[Project]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects")
        rows = cursor.fetchall()
        conn.close()
        return [Project(**dict(row)) for row in rows]

    def get_project_by_id(self, project_id: str) -> Optional[Project]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        conn.close()
        return Project(**dict(row)) if row else None
    
    def get_project_by_proposal_id(self, proposal_id: str) -> Optional[Project]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE proposal_id = ?", (proposal_id,))
        row = cursor.fetchone()
        conn.close()
        return Project(**dict(row)) if row else None

    def update_project(self, project_id: str, **kwargs):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            set_clauses = []
            values = []
            for key, value in kwargs.items():
                if isinstance(value, datetime.datetime):
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
                else:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            if set_clauses:
                query = f"UPDATE projects SET {', '.join(set_clauses)} WHERE id = ?"
                values.append(project_id)
                cursor.execute(query, tuple(values))
                conn.commit()
                logging.info(f"Projeto {project_id[:8]}... atualizado com sucesso.")
            else:
                logging.warning(f"Nenhum campo para atualizar para projeto {project_id[:8]}...")
        except sqlite3.Error as e:
            logging.error(f"Erro ao atualizar projeto {project_id[:8]}...: {e}")
            conn.rollback()
        finally:
            conn.close()
            
    def update_project_progress(self, project_id: str, new_progress: int):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE projects SET progress = ? WHERE id = ?",
                           (new_progress, project_id))
            conn.commit()
            logging.info(f"Progresso do projeto {project_id[:8]}... atualizado para {new_progress}%.")
        except sqlite3.Error as e:
            logging.error(f"Erro ao atualizar progresso do projeto {project_id[:8]}...: {e}")
            conn.rollback()
        finally:
            conn.close()
            
    def update_project_status(self, project_id: str, new_status: str):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE projects SET status = ? WHERE id = ?",
                           (new_status, project_id))
            conn.commit()
            logging.info(f"Status do projeto {project_id[:8]}... atualizado para {new_status}.")
        except sqlite3.Error as e:
            logging.error(f"Erro ao atualizar status do projeto {project_id[:8]}...: {e}")
            conn.rollback()
        finally:
            conn.close()

    def delete_project(self, project_id: str) -> bool:
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
            logging.info(f"Projeto {project_id[:8]}... excluído com sucesso.")
            return True
        except sqlite3.Error as e:
            logging.error(f"Erro ao excluir projeto {project_id[:8]}...: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def add_generated_code(self, code_data: Dict[str, Any]):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO generated_code (id, project_id, filename, language, content, description, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                code_data["id"], code_data["project_id"], code_data["filename"],
                code_data["language"], code_data["content"], code_data["description"],
                code_data["generated_at"]
            ))
            conn.commit()
            logging.info(f"Código {code_data['id'][:8]}... adicionado para o projeto {code_data['project_id'][:8]}...")
        except sqlite3.Error as e:
            logging.error(f"Erro ao adicionar código gerado: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_generated_code_for_project(self, project_id: str) -> List[GeneratedCode]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM generated_code WHERE project_id = ?", (project_id,))
        rows = cursor.fetchall()
        conn.close()
        return [GeneratedCode(**dict(row)) for row in rows]

    def delete_generated_code_by_project(self, project_id: str) -> bool:
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM generated_code WHERE project_id = ?", (project_id,))
            conn.commit()
            logging.info(f"Código gerado para projeto {project_id[:8]}... excluído.")
            return True
        except sqlite3.Error as e:
            logging.error(f"Erro ao excluir código gerado para projeto {project_id[:8]}...: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def add_quality_report(self, report_data: Dict[str, Any]):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO quality_reports (id, project_id, report_data, generated_at)
                VALUES (?, ?, ?, ?)
            """, (
                report_data["id"], report_data["project_id"], json.dumps(report_data["report_data"]),
                report_data["generated_at"]
            ))
            conn.commit()
            logging.info(f"Relatório de qualidade {report_data['id'][:8]}... adicionado para o projeto {report_data['project_id'][:8]}...")
        except sqlite3.Error as e:
            logging.error(f"Erro ao adicionar relatório de qualidade: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_quality_report_for_project(self, project_id: str) -> Optional[QualityReport]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quality_reports WHERE project_id = ? ORDER BY generated_at DESC LIMIT 1", (project_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            report_dict = dict(row)
            report_dict["report_data"] = json.loads(report_dict["report_data"])
            return QualityReport(**report_dict)
        return None

    def delete_quality_report_by_project(self, project_id: str) -> bool:
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM quality_reports WHERE project_id = ?", (project_id,))
            conn.commit()
            logging.info(f"Relatórios de qualidade para projeto {project_id[:8]}... excluídos.")
            return True
        except sqlite3.Error as e:
            logging.error(f"Erro ao excluir relatórios de qualidade para projeto {project_id[:8]}...: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
            
    def add_security_report(self, report_data: Dict[str, Any]):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO security_reports (id, project_id, report_data, generated_at)
                VALUES (?, ?, ?, ?)
            """, (
                report_data["id"], report_data["project_id"], json.dumps(report_data["report_data"]),
                report_data["generated_at"]
            ))
            conn.commit()
            logging.info(f"Relatório de segurança {report_data['id'][:8]}... adicionado para o projeto {report_data['project_id'][:8]}...")
        except sqlite3.Error as e:
            logging.error(f"Erro ao adicionar relatório de segurança: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_security_report_for_project(self, project_id: str) -> Optional[SecurityReport]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM security_reports WHERE project_id = ? ORDER BY generated_at DESC LIMIT 1", (project_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            report_dict = dict(row)
            report_dict["report_data"] = json.loads(report_dict["report_data"])
            return SecurityReport(**report_dict)
        return None

    def delete_security_report_by_project(self, project_id: str) -> bool:
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM security_reports WHERE project_id = ?", (project_id,))
            conn.commit()
            logging.info(f"Relatórios de segurança para projeto {project_id[:8]}... excluídos.")
            return True
        except sqlite3.Error as e:
            logging.error(f"Erro ao excluir relatórios de segurança para projeto {project_id[:8]}...: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
            
    def add_documentation(self, doc_data: Dict[str, Any]):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO documentation (id, project_id, filename, content, document_type, version, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_data["id"], doc_data["project_id"], doc_data["filename"],
                doc_data["content"], doc_data["document_type"], doc_data["version"],
                doc_data["last_updated"]
            ))
            conn.commit()
            logging.info(f"Documentação {doc_data['id'][:8]}... adicionada para o projeto {doc_data['project_id'][:8]}...")
        except sqlite3.Error as e:
            logging.error(f"Erro ao adicionar documentação: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_documentation_by_project(self, project_id: str) -> List[Documentation]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documentation WHERE project_id = ? ORDER BY last_updated DESC", (project_id,))
        rows = cursor.fetchall()
        conn.close()
        return [Documentation(**dict(row)) for row in rows]
    
    def delete_documentation_by_project(self, project_id: str) -> bool:
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM documentation WHERE project_id = ?", (project_id,))
            conn.commit()
            logging.info(f"Documentação para projeto {project_id[:8]}... excluída.")
            return True
        except sqlite3.Error as e:
            logging.error(f"Erro ao excluir documentação para projeto {project_id[:8]}...: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def add_monitoring_summary(self, summary_data: Dict[str, Any]):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            project_id = summary_data.get("project_id")
            # Verifica se já existe um resumo global (project_id is NULL) e atualiza, senão insere
            if project_id is None:
                existing_summary = self.get_monitoring_summary(project_id=None)
                if existing_summary and existing_summary.id: # Garante que o ID existe antes de tentar atualizar
                    # Se for uma atualização de um resumo global existente, atualiza
                    self.update_monitoring_summary(existing_summary.id, **summary_data["summary_data"])
                    return # Já foi atualizado, sai da função
            
            # Se não existe, ou se é um resumo de projeto, insere
            cursor.execute("""
                INSERT INTO monitoring_summaries (id, project_id, summary_data, generated_at)
                VALUES (?, ?, ?, ?)
            """, (
                summary_data["id"], summary_data["project_id"], json.dumps(summary_data["summary_data"]),
                summary_data["generated_at"]
            ))
            conn.commit()
            logging.info(f"Resumo de monitoramento {summary_data['id'][:8]}... adicionado para o projeto {summary_data.get('project_id', 'Global')[:8]}...")
        except sqlite3.Error as e:
            logging.error(f"Erro ao adicionar resumo de monitoramento: {e}")
            conn.rollback()
        finally:
            conn.close()
            
    def get_monitoring_summary(self, project_id: Optional[str] = None) -> Optional[MonitoringSummary]:
        conn = self._connect()
        cursor = conn.cursor()
        if project_id:
            cursor.execute("SELECT * FROM monitoring_summaries WHERE project_id = ? ORDER BY generated_at DESC LIMIT 1", (project_id,))
        else: # Global summary
            cursor.execute("SELECT * FROM monitoring_summaries WHERE project_id IS NULL ORDER BY generated_at DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            summary_dict = dict(row)
            summary_dict["summary_data"] = json.loads(summary_dict["summary_data"])
            return MonitoringSummary(**summary_dict)
        return None

    def update_monitoring_summary(self, summary_id: str, **kwargs):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            set_clauses = []
            values = []
            for key, value in kwargs.items():
                if key == "summary_data": # Handle JSON field
                    set_clauses.append(f"summary_data = ?")
                    values.append(json.dumps(value))
                elif isinstance(value, datetime.datetime): # Handle datetime objects
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
                else:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            if set_clauses:
                query = f"UPDATE monitoring_summaries SET {', '.join(set_clauses)} WHERE id = ?"
                values.append(summary_id)
                cursor.execute(query, tuple(values))
                conn.commit()
                logging.info(f"Resumo de monitoramento {summary_id[:8]}... atualizado com sucesso.")
            else:
                logging.warning(f"Nenhum campo para atualizar para resumo de monitoramento {summary_id[:8]}...")
        except sqlite3.Error as e:
            logging.error(f"Erro ao atualizar resumo de monitoramento {summary_id[:8]}...: {e}")
            conn.rollback()
        finally:
            conn.close()

    def delete_monitoring_summary_by_project(self, project_id: str) -> bool:
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM monitoring_summaries WHERE project_id = ?", (project_id,))
            conn.commit()
            logging.info(f"Resumos de monitoramento para projeto {project_id[:8]}... excluídos.")
            return True
        except sqlite3.Error as e:
            logging.error(f"Erro ao excluir resumos de monitoramento para projeto {project_id[:8]}...: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def add_chat_message(self, message_data: Dict[str, Any]):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO chat_history (id, sender, message, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                message_data["id"], message_data["sender"], message_data["message"],
                message_data["timestamp"]
            ))
            conn.commit()
            logging.info(f"Mensagem de chat {message_data['id'][:8]}... adicionada.")
        except sqlite3.Error as e:
            logging.error(f"Erro ao adicionar mensagem de chat: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_chat_history(self) -> List[ChatMessage]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chat_history ORDER BY timestamp ASC")
        rows = cursor.fetchall()
        conn.close()
        return [ChatMessage(**dict(row)) for row in rows]
    
    def add_moai_log(self, log_data: Dict[str, Any]):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO moai_logs (id, timestamp, event_type, details, project_id, agent_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                log_data["id"], log_data["timestamp"], log_data["event_type"],
                log_data["details"], log_data["project_id"], log_data["agent_id"], log_data["status"]
            ))
            conn.commit()
            logging.debug(f"Log MOAI {log_data['id'][:8]}... adicionado: {log_data['event_type']}")
        except sqlite3.Error as e:
            logging.error(f"Erro ao adicionar log MOAI: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_all_moai_logs(self) -> List[MOAILog]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM moai_logs ORDER BY timestamp ASC")
        rows = cursor.fetchall()
        conn.close()
        return [MOAILog(**dict(row)) for row in rows]

    def delete_moai_logs_by_project(self, project_id: str) -> bool:
        conn = self._connect()
        cursor = conn.cursor()
        try:
            # Exclui logs cujo project_id corresponda ao fornecido
            cursor.execute("DELETE FROM moai_logs WHERE project_id = ?", (project_id,))
            # Exclui logs cujo ID do log seja igual ao project_id (para o caso de logs de proposta)
            cursor.execute("DELETE FROM moai_logs WHERE id = ?", (project_id,)) # Assume que proposal_id pode ser usado como id do log também em alguns casos
            conn.commit()
            logging.info(f"Logs MOAI relacionados ao ID {project_id[:8]}... excluídos.")
            return True
        except sqlite3.Error as e:
            logging.error(f"Erro ao excluir logs MOAI para ID {project_id[:8]}...: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()