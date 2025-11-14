# synapse_forge_backend.py
import uuid
from datetime import datetime
import time
import random
from typing import List, Optional, Dict, Any
import json

from data_models import (
    Proposal, Project, GeneratedCode, QualityReportEntry,
    SecurityReportEntry, Documentation, MonitoringSummary, MOAILog, ChatMessage
)
from database_manager import DatabaseManager
from llm_simulator import LLMSimulator

class SynapseForgeBackend:
    _instance = None # Singleton pattern

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SynapseForgeBackend, cls).__new__(cls)
            cls._instance._initialized = False # Use a flag to avoid re-initialization
        return cls._instance

    def __init__(self):
        if self._initialized:
            print("DEBUG: SynapseForgeBackend já inicializado, pulando setup.") # Adicionado para debug
            return
        
        print("DEBUG: Inicializando SynapseForgeBackend pela primeira vez...") # Adicionado para debug
        self.db_manager = DatabaseManager()
        self.llm_simulator = LLMSimulator()
        self._initialized = True # Set the flag to True after initialisation

        # Garante que a estrutura do DB está pronta ao inicializar o backend
        # self.db_manager._create_tables() # Isso já é chamado no __init__ do DatabaseManager
        print("DEBUG: Inicialização do SynapseForgeBackend completa.") # Adicionado para debug

    # --- Métodos de Simulação de Agentes (MOAI Orchestration) ---
    def _create_project_from_proposal(self, proposal: Proposal) -> Project:
        project_id = str(uuid.uuid4())
        project_name = proposal.requirements.get('nome_projeto', proposal.title)
        client_name = proposal.requirements.get('nome_cliente', 'Cliente Desconhecido')
        
        project = Project(
            project_id=project_id,
            name=project_name,
            client_name=client_name,
            status="active",
            progress=0,
            proposal_id=proposal.id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.db_manager.add_project(project)
        self.db_manager.update_proposal_project_id(proposal.id, project_id) # Link project to proposal
        
        self.db_manager.add_moai_log(MOAILog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type="PROJECT_CREATED",
            description=f"Projeto '{project.name}' criado a partir da proposta {proposal.id}",
            details=json.dumps({"project_id": project.project_id, "proposal_id": proposal.id})
        ))
        
        # Simula o provisionamento do ambiente inicial pelo AID
        self._simulate_aid_provisioning(project.project_id, project.name)
        # Simula a criação de um resumo de monitoramento inicial
        self._simulate_initial_monitoring_summary(project.project_id)

        return project

    def _simulate_aid_provisioning(self, project_id: str, project_name: str):
        # Simula a criação de pastas, arquivos e repositórios
        self.db_manager.add_moai_log(MOAILog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type="INFRA_PROVISIONING",
            description=f"AID: Ambiente inicial provisionado para o projeto '{project_name}'",
            details=json.dumps({
                "project_id": project_id,
                "environment_layout": {
                    "root": ["src/", "docs/", "tests/", "infra/"],
                    "src": ["main.py", "requirements.txt"],
                    "infra": ["terraform/", "ansible/"]
                },
                "repo_url": f"https://github.com/synapseforge/{project_name.lower().replace(' ', '-')}"
            })
        ))

    def _simulate_initial_monitoring_summary(self, project_id: str):
        monitoring_entry = MonitoringSummary(
            id=str(uuid.uuid4()), project_id=project_id, summary="Resumo de monitoramento inicial do ambiente de dev.",
            status="Operational", metrics_snapshot=json.dumps({"cpu": f"{random.randint(10,30)}%", "mem": f"{random.randint(30,60)}%", "disk_io": "normal"}), # Formato JSON string
            created_at=datetime.now()
        )
        self.db_manager.add_monitoring_summary(monitoring_entry)
        self.db_manager.add_moai_log(MOAILog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type="MONITORING_INITIATED",
            description=f"AMS: Monitoramento inicial ativado para o projeto {project_id}",
            details=json.dumps({"project_id": project_id, "status": "Operational"})
        ))

    # --- Métodos de Criação e Gestão de Propostas ---
    def create_proposal(self, req_data: Dict[str, Any]) -> Proposal:
        proposal_id = str(uuid.uuid4())
        
        # Simula a geração de conteúdo da proposta pelo ANP (via LLMSimulator)
        llm_generated_content = self.llm_simulator.generate_proposal_content(req_data)
        
        new_proposal = Proposal(
            id=proposal_id,
            title=llm_generated_content.get('title', req_data.get('nome_projeto', 'Nova Proposta')),
            description=llm_generated_content.get('description', 'Descrição gerada automaticamente.'),
            status="pending",
            submitted_at=datetime.now(),
            requirements=req_data,
            problem_understanding_moai=llm_generated_content.get('problem_understanding_moai', ''),
            solution_proposal_moai=llm_generated_content.get('solution_proposal_moai', ''),
            scope_moai=llm_generated_content.get('scope_moai', ''),
            technologies_suggested_moai=llm_generated_content.get('technologies_suggested_moai', ''),
            estimated_value_moai=llm_generated_content.get('estimated_value_moai', 'R$ 0,00'),
            estimated_time_moai=llm_generated_content.get('estimated_time_moai', 'A definir'),
            terms_conditions_moai=llm_generated_content.get('terms_conditions_moai', '')
        )
        self.db_manager.add_proposal(new_proposal)
        self.db_manager.add_moai_log(MOAILog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type="PROPOSAL_CREATED",
            description=f"Proposta '{new_proposal.title}' criada e aguardando aprovação.",
            details=json.dumps({"proposal_id": new_proposal.id, "status": new_proposal.status})
        ))
        return new_proposal

    def get_proposal_by_id(self, proposal_id: str) -> Optional[Proposal]:
        return self.db_manager.get_proposal_by_id(proposal_id)

    def get_proposals(self, status: Optional[str] = None) -> List[Proposal]:
        return self.db_manager.get_proposals(status)
    
    def get_pending_proposals(self) -> int:
        return len(self.db_manager.get_proposals(status="pending"))

    def update_proposal_status(self, proposal_id: str, new_status: str):
        self.db_manager.update_proposal_status(proposal_id, new_status)
        self.db_manager.add_moai_log(MOAILog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type="PROPOSAL_STATUS_UPDATED",
            description=f"Proposta {proposal_id} teve status atualizado para {new_status}.",
            details=json.dumps({"proposal_id": proposal_id, "new_status": new_status})
        ))
        if new_status == "approved":
            proposal = self.db_manager.get_proposal_by_id(proposal_id)
            if proposal:
                self._create_project_from_proposal(proposal)

    def update_proposal_content(self, proposal_id: str, updated_fields: Dict[str, Any]):
        self.db_manager.update_proposal_content(proposal_id, updated_fields)
        self.db_manager.add_moai_log(MOAILog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type="PROPOSAL_CONTENT_UPDATED",
            description=f"Conteúdo da proposta {proposal_id} foi atualizado.",
            details=json.dumps({"proposal_id": proposal_id, "updated_fields": list(updated_fields.keys())})
        ))

    # --- Métodos de Gestão de Projetos ---
    def get_projects(self) -> List[Project]:
        return self.db_manager.get_all_projects()
    
    def get_project_by_id(self, project_id: str) -> Optional[Project]:
        return self.db_manager.get_project_by_id(project_id)

    def update_project_details(self, project_id: str, updated_fields: Dict[str, Any]):
        self.db_manager.update_project_details(project_id, updated_fields)
        self.db_manager.add_moai_log(MOAILog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type="PROJECT_DETAILS_UPDATED",
            description=f"Detalhes do projeto {project_id} atualizados.",
            details=json.dumps({"project_id": project_id, "updated_fields": list(updated_fields.keys())})
        ))

    # --- Métodos de Geração de Código ---
    def generate_code_for_project(self, project_id: str, filename: str, language: str, description: str) -> GeneratedCode:
        project = self.db_manager.get_project_by_id(project_id)
        if not project:
            raise ValueError("Project not found.")
        
        code_content = self.llm_simulator.generate_code(project.name, filename, language)
        new_code = GeneratedCode(
            id=str(uuid.uuid4()),
            project_id=project_id,
            filename=filename,
            content=code_content,
            language=language,
            description=description,
            created_at=datetime.now()
        )
        self.db_manager.add_generated_code(new_code)
        self.db_manager.add_moai_log(MOAILog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type="CODE_GENERATED",
            description=f"ADE-X: Código '{filename}' gerado para o projeto {project.name}.",
            details=json.dumps({"project_id": project_id, "filename": filename, "language": language})
        ))
        return new_code

    def get_generated_code_for_project(self, project_id: str) -> List[GeneratedCode]:
        return self.db_manager.get_generated_code_for_project(project_id)

    # --- Métodos de Geração de Relatórios ---
    def generate_quality_report_for_project(self, project_id: str) -> QualityReportEntry:
        project = self.db_manager.get_project_by_id(project_id)
        if not project:
            raise ValueError("Project not found.")
        
        report_data = self.llm_simulator.generate_quality_report(project.name)
        new_report = QualityReportEntry(
            id=str(uuid.uuid4()),
            project_id=project_id,
            summary=report_data.get('details_llm', 'Resumo padrão de qualidade.'),
            details=json.dumps(report_data), # Store full report as JSON string
            score=random.uniform(0.7, 0.99),
            created_at=datetime.now()
        )
        self.db_manager.add_quality_report(new_report)
        self.db_manager.add_moai_log(MOAILog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type="QUALITY_REPORT_GENERATED",
            description=f"AQT: Relatório de qualidade gerado para o projeto {project.name}.",
            details=json.dumps({"project_id": project_id, "status": report_data.get('status')})
        ))
        return new_report

    def get_quality_reports_for_project(self, project_id: str) -> List[QualityReportEntry]:
        return self.db_manager.get_quality_reports_for_project(project_id)

    def generate_security_report_for_project(self, project_id: str) -> SecurityReportEntry:
        project = self.db_manager.get_project_by_id(project_id)
        if not project:
            raise ValueError("Project not found.")
        
        report_data = self.llm_simulator.generate_security_report(project.name)
        new_report = SecurityReportEntry(
            id=str(uuid.uuid4()),
            project_id=project_id,
            summary=report_data.get('details_llm', 'Resumo padrão de segurança.'),
            details=json.dumps(report_data), # Store full report as JSON string
            vulnerabilities_found=report_data['vulnerabilities']['critical'] + report_data['vulnerabilities']['high'],
            severity_level=report_data['overall_risk'],
            created_at=datetime.now()
        )
        self.db_manager.add_security_report(new_report)
        self.db_manager.add_moai_log(MOAILog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type="SECURITY_REPORT_GENERATED",
            description=f"ASE: Relatório de segurança gerado para o projeto {project.name}.",
            details=json.dumps({"project_id": project_id, "risk": report_data.get('overall_risk')})
        ))
        return new_report

    def get_security_reports_for_project(self, project_id: str) -> List[SecurityReportEntry]:
        return self.db_manager.get_security_reports_for_project(project_id)

    def generate_project_documentation(self, project_id: str) -> Dict[str, str]:
        project = self.db_manager.get_project_by_id(project_id)
        if not project:
            return {"error": "Projeto não encontrado."}
        
        proposal = self.db_manager.get_proposal_by_id(project.proposal_id)
        if not proposal:
            return {"error": "Proposta associada ao projeto não encontrada."}

        # CORREÇÃO: Passar o dicionário de requisitos da proposta para o LLM Simulator
        doc_data = self.llm_simulator.generate_documentation(project.name, proposal.requirements)
        
        new_doc = Documentation(
            id=str(uuid.uuid4()),
            project_id=project_id,
            filename=doc_data.get('filename', f"documentacao_{project.name.replace(' ', '_').lower()}.md"),
            content=doc_data.get('content', "Conteúdo da documentação não gerado."),
            format=doc_data.get('format', "Markdown"),
            created_at=datetime.now()
        )
        self.db_manager.add_documentation(new_doc)
        self.db_manager.add_moai_log(MOAILog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type="DOCUMENTATION_GENERATED",
            description=f"ADO: Documentação gerada para o projeto {project.name}.",
            details=json.dumps({"project_id": project_id, "filename": new_doc.filename})
        ))
        return {"success": True, "filename": new_doc.filename, "content": new_doc.content, "error": None}

    def get_documentation_for_project(self, project_id: str) -> List[Documentation]:
        return self.db_manager.get_documentation_by_project(project_id)

    # --- Métodos de Monitoramento e Infraestrutura ---
    def get_monitoring_summary(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        if project_id:
            summary_obj = self.db_manager.get_monitoring_summary_by_project(project_id)
            if summary_obj:
                metrics = json.loads(summary_obj.metrics_snapshot)
                return {
                    "overall_status": summary_obj.status,
                    "summary": summary_obj.summary,
                    "uptime_percentage_24h": random.randint(95, 100),
                    "response_time_ms": random.randint(50, 300),
                    "active_users": random.randint(10, 500),
                    "recent_alerts": random.sample(["CPU Alta", "Memória Cheia", "Serviço Offline", "Nenhum"], k=random.randint(0,2)),
                    "last_checked": summary_obj.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    "metrics": metrics
                }
            return {
                "overall_status": "N/A", "summary": "Nenhum monitoramento encontrado para este projeto.",
                "uptime_percentage_24h": 0, "response_time_ms": 0, "active_users": 0,
                "recent_alerts": [], "last_checked": "N/A", "metrics": {}
            }
        
        # Global summary for dashboard
        return {
            "overall_system_status": random.choice(["Operacional", "Atenção", "Crítico"]),
            "total_active_monitors": random.randint(10, 50),
            "total_recent_alerts": random.randint(0, 5),
            "critical_incidents_24h": random.randint(0, 1),
            "last_overall_summary": "Todos os sistemas operando dentro dos parâmetros esperados, com pequenas anomalias monitoradas.",
        }

    def get_infrastructure_health(self) -> Dict[str, Any]:
        # Simula o status de diferentes componentes da infraestrutura
        return {
            "overall_status": random.choice(["Operacional", "Atenção", "Crítico"]),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "components": {
                "servidores": {"status": random.choice(["Operacional", "Atenção"]), "message": "CPU e RAM ok.", "last_log_time": "2 min atrás"},
                "bancos_de_dados": {"status": random.choice(["Operacional", "Atenção"]), "message": "Conexões estáveis.", "last_log_time": "5 min atrás"},
                "redes": {"status": "Operacional", "message": "Latência normal.", "last_log_time": "1 min atrás"},
                "backups": {"status": random.choice(["Operacional", "Crítico"]), "message": "Último backup completo com sucesso.", "last_log_time": "12 horas atrás"}
            }
        }
    
    def get_infra_status(self, project_id: str) -> Dict[str, Any]:
        # Simula o layout do ambiente de um projeto específico
        # Isso pode vir de um registro no DB que o AID manteria
        project = self.db_manager.get_project_by_id(project_id)
        if not project:
            return {"error": "Projeto não encontrado para status de infraestrutura."}

        return {
            "project_id": project_id,
            "project_name": project.name,
            "ambiente_dev": {
                "status": "Ativo",
                "recursos_alocados": {"CPU": "2 vCPU", "RAM": "4 GB", "Armazenamento": "50 GB"},
                "estrutura_pastas": ["/app", "/app/src", "/app/tests", "/app/config"],
                "repositorios": [f"git@github.com:synapseforge/{project.name.lower().replace(' ', '-')}.git"]
            },
            "ambiente_prod": {
                "status": "Não provisionado" if project.status != "completed" else "Ativo",
                "recursos_alocados": {"CPU": "4 vCPU", "RAM": "8 GB", "Armazenamento": "100 GB"},
                "estrutura_pastas": ["/var/www/app"],
                "servidores": ["web-01", "db-01"]
            },
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def trigger_manual_backup(self, project_id: str) -> Dict[str, Any]:
        time.sleep(random.uniform(0.5, 1.5))
        status = random.choice([True, False])
        if status:
            self.db_manager.add_moai_log(MOAILog(
                id=str(uuid.uuid4()), timestamp=datetime.now(),
                event_type="BACKUP_MANUAL", description=f"AID: Backup manual do projeto {project_id} executado com sucesso.",
                details=json.dumps({"project_id": project_id, "status": "Success"})
            ))
            return {"success": True, "message": f"Backup manual para {project_id[:8]}... solicitado e concluído com sucesso."}
        else:
            self.db_manager.add_moai_log(MOAILog(
                id=str(uuid.uuid4()), timestamp=datetime.now(),
                event_type="BACKUP_MANUAL_FAILED", description=f"AID: Falha na execução do backup manual para o projeto {project_id}.",
                details=json.dumps({"project_id": project_id, "status": "Failed"})
            ))
            return {"success": False, "message": f"Falha ao executar backup manual para {project_id[:8]}..."}

    def schedule_test_restore(self, project_id: str) -> Dict[str, Any]:
        time.sleep(random.uniform(0.5, 1.5))
        status = random.choice([True, False])
        if status:
            self.db_manager.add_moai_log(MOAILog(
                id=str(uuid.uuid4()), timestamp=datetime.now(),
                event_type="TEST_RESTORE_SCHEDULED", description=f"AID: Restauração de teste para o projeto {project_id} agendada.",
                details=json.dumps({"project_id": project_id, "status": "Scheduled"})
            ))
            return {"success": True, "message": f"Restauração de teste para {project_id[:8]}... agendada com sucesso. Notificação será enviada ao concluir."}
        else:
            self.db_manager.add_moai_log(MOAILog(
                id=str(uuid.uuid4()), timestamp=datetime.now(),
                event_type="TEST_RESTORE_FAILED", description=f"AID: Falha ao agendar restauração de teste para o projeto {project_id}.",
                details=json.dumps({"project_id": project_id, "status": "Failed"})
            ))
            return {"success": False, "message": f"Falha ao agendar restauração de teste para {project_id[:8]}..."}

    # --- Métodos de Logs do MOAI ---
    def get_moai_logs(self) -> List[MOAILog]:
        return self.db_manager.get_all_moai_logs()

    def get_moai_log_events_count(self) -> Dict[str, int]:
        logs = self.db_manager.get_all_moai_logs()
        counts = {}
        for log in logs:
            counts[log.event_type] = counts.get(log.event_type, 0) + 1
        return counts

    # --- Métodos de Chat com MOAI ---
    def get_chat_history(self) -> List[ChatMessage]:
        return self.db_manager.get_chat_history()

    def add_chat_message(self, sender: str, message: str):
        self.db_manager.add_chat_message(ChatMessage(sender=sender, message=message))

    def process_moai_chat(self, user_message: str) -> str:
        # Aqui, o MOAI (simulado) processa a mensagem e retorna uma resposta
        response = self.llm_simulator.process_chat_message(user_message)
        self.db_manager.add_moai_log(MOAILog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type="MOAI_CHAT_INTERACTION",
            description=f"Interação de chat: Usuário -> MOAI: '{user_message[:50]}...'",
            details=json.dumps({"user_message": user_message, "moai_response": response})
        ))
        return response

    # --- Métodos de Relatórios Detalhados (AQT, ASE, ANP) ---
    def get_project_phases_status(self, project_id: str) -> Dict[str, Any]:
        project = self.db_manager.get_project_by_id(project_id)
        if not project:
            return {"error": "Projeto não encontrado."}
        
        progress = project.progress
        
        phases = [
            {"name": "Levantamento", "icon": "📋", "status": "Concluído" if progress >= 10 else "Pendente"},
            {"name": "Arquitetura", "icon": "🏗️", "status": "Concluído" if progress >= 20 else ("Em Andamento" if progress >= 10 else "Pendente")},
            {"name": "Desenvolvimento Backend", "icon": "🐍", "status": "Concluído" if progress >= 50 else ("Em Andamento" if progress >= 20 else "Pendente")},
            {"name": "Desenvolvimento Frontend", "icon": "💻", "status": "Concluído" if progress >= 70 else ("Em Andamento" if progress >= 50 else "Pendente")},
            {"name": "Testes e QA", "icon": "🧪", "status": "Concluído" if progress >= 85 else ("Em Andamento" if progress >= 70 else "Pendente")},
            {"name": "Homologação", "icon": "✅", "status": "Concluído" if progress >= 95 else ("Em Andamento" if progress >= 85 else "Pendente")},
            {"name": "Implantação", "icon": "🚀", "status": "Concluído" if progress == 100 else ("Em Andamento" if progress >= 95 else "Pendente")}
        ]
        return {"phases": phases}

    def get_quality_tests_report(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        if project_id:
            reports = self.db_manager.get_quality_reports_for_project(project_id)
            if reports:
                latest_report = json.loads(reports[-1].details) # Get latest and parse its details
                return latest_report
            
            # If no report for project, generate a simulated one
            project = self.db_manager.get_project_by_id(project_id)
            if project:
                return self.llm_simulator.generate_quality_report(project.name)
            
            return {"status": "N/A", "total_tests": 0, "passed_tests": 0, "failed_tests": 0, "code_coverage": "0%", "stability": "N/A", "average_test_execution_time_seconds": 0, "recommendations": ["Nenhum relatório encontrado."], "last_update": "N/A", "details_llm": "Nenhum relatório de qualidade disponível para este projeto."}
        
        # Overall summary
        return {
            "status_geral": random.choice(["Excelente", "Bom", "Atenção"]),
            "bugs_abertos_total": random.randint(0, 10),
            "cobertura_media_codigo": f"{random.randint(75, 95)}%",
            "risco_qualidade": random.choice(["Baixo", "Médio"]),
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def get_security_audit_report(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        if project_id:
            reports = self.db_manager.get_security_reports_for_project(project_id)
            if reports:
                latest_report = json.loads(reports[-1].details)
                return latest_report
            
            # If no report for project, generate a simulated one
            project = self.db_manager.get_project_by_id(project_id)
            if project:
                return self.llm_simulator.generate_security_report(project.name)

            return {"status": "N/A", "overall_risk": "N/A", "vulnerabilities": {"critical":0, "high":0, "medium":0, "low":0}, "compliance_status": "N/A", "last_scan": "N/A", "recommendations": ["Nenhum relatório encontrado."], "details_llm": "Nenhum relatório de segurança disponível para este projeto."}

        # Overall summary
        return {
            "status_geral": random.choice(["Seguro", "Com Avisos", "Vulnerabilidades Críticas"]),
            "vulnerabilidades_criticas_total": random.randint(0, 3),
            "incidentes_recentes": random.randint(0, 1),
            "conformidade": random.choice(["Conforme", "Requer Ajustes"]),
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def get_commercial_report(self) -> Dict[str, Any]:
        all_proposals = self.db_manager.get_proposals()
        approved_proposals = [p for p in all_proposals if p.status == "approved"]
        rejected_proposals = [p for p in all_proposals if p.status == "rejected"]

        total_estimated_value_generated = sum(float(p.estimated_value_moai.replace('R$', '').replace('.', '').replace(',', '.').strip()) for p in all_proposals if p.estimated_value_moai)
        total_estimated_value_approved = sum(float(p.estimated_value_moai.replace('R$', '').replace('.', '').replace(',', '.').strip()) for p in approved_proposals if p.estimated_value_moai)

        return {
            "propostas_geradas": len(all_proposals),
            "propostas_aprovadas": len(approved_proposals),
            "propostas_rejeitadas": len(rejected_proposals),
            "taxa_aprovacao": (len(approved_proposals) / len(all_proposals) * 100) if all_proposals else 0,
            "valor_total_gerado": total_estimated_value_generated,
            "valor_total_aprovado": total_estimated_value_approved,
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    # --- Dashboard Summary ---
    def get_dashboard_summary(self) -> Dict[str, Any]:
        all_proposals = self.db_manager.get_proposals()
        pending = [p for p in all_proposals if p.status == "pending"]
        approved = [p for p in all_proposals if p.status == "approved"]
        rejected = [p for p in all_proposals if p.status == "rejected"]

        all_projects = self.db_manager.get_all_projects()
        active_projects = [p for p in all_projects if p.status == "active"]
        completed_projects = [p for p in all_projects if p.status == "completed"]

        total_estimated_value_approved = sum(float(p.estimated_value_moai.replace('R$', '').replace('.', '').replace(',', '.').strip()) for p in approved if p.estimated_value_moai)

        return {
            "total_proposals": len(all_proposals),
            "pending_proposals": len(pending),
            "approved_proposals": len(approved),
            "rejected_proposals": len(rejected),
            "total_projects": len(all_projects),
            "active_projects": len(active_projects),
            "completed_projects": len(completed_projects),
            "total_estimated_value_approved_proposals": total_estimated_value_approved,
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_agents_in_activity(self) -> List[Dict[str, Any]]:
        # Simula a lista de agentes em atividade
        return [
            {"Agente": "ARA (Análise de Requisitos)", "Status": "Ativo", "Tarefas Atuais": 2},
            {"Agente": "AAD (Arquitetura e Design)", "Status": "Ativo", "Tarefas Atuais": 1},
            {"Agente": "AGP (Gerenciamento de Projetos)", "Status": "Monitorando", "Tarefas Atuais": 3},
            {"Agente": "AID (Infraestrutura e DevOps)", "Status": "Monitorando", "Tarefas Atuais": 5},
            {"Agente": "ANP (Negócios e Propostas)", "Status": "Ocioso", "Tarefas Atuais": 0},
            {"Agente": "ADE-X (Desenvolvimento)", "Status": "Ativo", "Tarefas Atuais": 4},
            {"Agente": "AQT (Qualidade e Testes)", "Status": "Ativo", "Tarefas Atuais": 2},
            {"Agente": "ASE (Segurança)", "Status": "Ativo", "Tarefas Atuais": 1},
            {"Agente": "ADO (Documentação)", "Status": "Ocioso", "Tarefas Atuais": 0},
            {"Agente": "AMS (Monitoramento e Suporte)", "Status": "Ativo", "Tarefas Atuais": 6}
        ]