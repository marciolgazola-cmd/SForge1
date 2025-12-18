# MOAI.py
import logging
import uuid
import datetime
import random
import json # Certifique-se que está importado
import time
from typing import Dict, Any, List, Optional, Union, cast # Adicionado 'cast'

# Importa os modelos do novo arquivo data_models.py
from data_models import Proposal, Project, GeneratedCode, QualityReport, SecurityReport, Documentation, MonitoringSummary, ChatMessage, MOAILog

# Importa DatabaseManager
from database_manager import DatabaseManager

# Importações de exceções e do LLMSimulator
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError

# Importa o mapeamento de modelos para agentes
from agent_model_mapping import get_agent_model

# Importações dos agentes e seus modelos de saída (para type hinting e conversão)
from ara_agent import ARAAgent, ARAOutput
from aad_agent import AADAgent, AADSolutionOutput
from agp_agent import AGPAgent, AGPEstimateOutput
from anp_agent import ANPAgent, ProposalContentOutput
from adex_agent import ADEXAgent, GeneratedCodeOutput
from aqt_agent import AQTAgent, QualityReportOutput
from ase_agent import ASEAgent, SecurityReportOutput
from ado_agent import ADOAgent, DocumentationOutput
from ams_agent import AMSAgent, MonitoringSummaryOutput
from aid_agent import AIDAgent, InfraStatusOutput


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SynapseForgeBackend:
    _instance = None # Singleton pattern

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SynapseForgeBackend, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'): # Garante que __init__ só roda uma vez para o Singleton
            self.db_manager = DatabaseManager('synapse_forge.db')
            self.llm_simulator = LLMSimulator() # Inicializa o LLM Simulator

            # Inicializa os Agentes
            # Agentes base que não dependem de outros para inicialização
            self.ara_agent = ARAAgent(self.llm_simulator)
            self.aad_agent = AADAgent(self.llm_simulator)
            self.agp_agent = AGPAgent(self.llm_simulator)
            self.adex_agent = ADEXAgent(self.llm_simulator)
            self.aqt_agent = AQTAgent(self.llm_simulator)
            self.ase_agent = ASEAgent(self.llm_simulator)
            self.ado_agent = ADOAgent(self.llm_simulator)
            self.ams_agent = AMSAgent(self.llm_simulator)
            self.aid_agent = AIDAgent(self.llm_simulator)

            # ANPAgent que depende de outros agentes
            self.anp_agent = ANPAgent(self.llm_simulator, self.ara_agent, self.aad_agent, self.agp_agent)
            
            self._initialized = True
            logger.info("SynapseForgeBackend (MOAI) inicializado com sucesso e orquestrando agentes.")
            self._initialize_data() # Inicializa com dados de exemplo se o DB estiver vazio

    def _add_moai_log(self, event_type: str, details: str, project_id: Optional[str] = None, agent_id: Optional[str] = None, status: str = "INFO"):
        log_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now()
        log_entry = MOAILog(id=log_id, timestamp=timestamp, event_type=event_type, details=details, project_id=project_id, agent_id=agent_id, status=status)
        self.db_manager.add_moai_log(log_entry.dict())

    def _update_agent_status(self, agent_name: str, status: str, project_id: Optional[str] = None, message: str = ""):
        self._add_moai_log(f"AGENT_STATUS_{agent_name.upper()}", f"Status: {status}. Mensagem: {message}", project_id=project_id, agent_id=agent_name, status=status)

    def _convert_estimated_value_to_float(self, value: Any) -> Optional[float]:
        """Converte um valor estimado (string R$, etc.) para float ou None."""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                numeric_string = value.replace(r'R$', '').replace('.', '').replace(',', '.').strip()
                return float(numeric_string) if numeric_string else None
            except ValueError:
                logger.warning(f"Não foi possível converter o valor '{value}' para float. Retornando None.")
                return None
        return None

    def _build_code_generation_brief(self, project: Project, base_description: str) -> str:
        """
        Constrói um briefing detalhado para o ADE-X usando contexto do projeto/proposta.
        """
        base_description = base_description.strip() if base_description else "Implementação solicitada pelo CVO."
        lines = [
            "=== CONTEXTO DO PROJETO ===",
            f"Projeto: {project.name}",
            f"Cliente: {project.client_name}",
            "=== REQUISITOS ESPECÍFICOS ===",
            base_description,
        ]

        proposal = self.db_manager.get_proposal_by_id(project.proposal_id) if project.proposal_id else None
        if proposal:
            requirements = proposal.requirements or {}
            def normalize_value(value: Any) -> str:
                if value is None:
                    return ""
                if isinstance(value, list):
                    return ", ".join(str(item).strip() for item in value if str(item).strip())
                return str(value).strip()

            def add_line(label: str, value: Any):
                value_str = normalize_value(value)
                if value_str:
                    lines.append(f"{label}: {value_str}")

            add_line("Problema de negócio", requirements.get('problema_negocio'))
            add_line("Objetivos do projeto", requirements.get('objetivos_projeto'))
            add_line("Funcionalidades esperadas", requirements.get('funcionalidades_esperadas'))
            add_line("Restrições", requirements.get('restricoes'))
            add_line("Solução proposta pelo MOAI", proposal.solution_proposal_moai)
            add_line("Escopo aprovado", proposal.scope_moai)
            add_line("Tecnologias sugeridas", proposal.technologies_suggested_moai)
            add_line("Público-alvo", requirements.get('publico_alvo'))
        else:
            lines.append("Contexto adicional: Proposta associada não encontrada no momento.")

        lines.extend([
            "=== ORIENTAÇÕES DE IMPLEMENTAÇÃO ===",
            "- Cubra todas as funcionalidades listadas acima. Não devolva exemplos genéricos.",
            "- Estruture o código em funções ou classes reutilizáveis e inclua tratamento de erros.",
            "- Se o escopo citar integrações (e-mail, APIs, bancos), implemente stubs ou camadas reais.",
            "- Inclua comentários essenciais e, se fizer sentido, um bloco `if __name__ == '__main__':` demonstrando uso.",
            "- Utilize as tecnologias recomendadas quando possível. Caso não seja viável, justifique via comentários.",
            "- Entregue o código pronto para execução, evitando trechos placeholders."
        ])
        return "\n".join(lines)

    def _initialize_data(self):
        logger.info("Inicializando dados de exemplo...")
        if not self.db_manager.get_all_proposals():
            logger.info("Nenhuma proposta encontrada. Criando dados de exemplo...")
            sample_reqs = {
                "nome_projeto": "Sistema de Gestão de Eventos",
                "nome_cliente": "OrganizaEventos Ltda.",
                "problema_negocio": "A OrganizaEventos precisa de uma plataforma para gerenciar inscrições, agenda e comunicação com participantes de múltiplos eventos simultaneamente, pois o processo atual é manual e ineficaz.",
                "objetivos_projeto": "Automatizar o processo de inscrição, centralizar a gestão de eventos, melhorar a comunicação com os participantes e gerar relatórios de desempenho dos eventos.",
                "funcionalidades_esperadas": "Cadastro de eventos, gestão de inscrições (com diferentes tipos de ingresso), agenda de palestras, envio de notificações, chat para participantes, área de expositores, relatórios financeiros e de presença.",
                "restricoes": r"Orçamento de até R\$ 50.000,00. Prazo de 4 meses para MVP. Deve ser escalável para 10.000 participantes por evento. Utilizar tecnologias open-source quando possível.",
                "publico_alvo": "Organizadores de eventos (administradores), palestrantes, participantes e expositores."
            }
            try:
                # Assumimos que ANPAgent.generate_proposal_content retorna um Dict[str, Any]
                proposal_content_dict = self.anp_agent.generate_proposal_content(sample_reqs)
                
                # Garante que estimated_value_moai seja float ou None
                proposal_content_dict['estimated_value_moai'] = self._convert_estimated_value_to_float(
                    proposal_content_dict.get('estimated_value_moai')
                )
                
                self.create_proposal(sample_reqs, initial_content=proposal_content_dict)
                logger.info("Dados de exemplo de proposta gerados com sucesso.")
            except Exception as e:
                logger.error(f"ERRO: Falha ao gerar conteúdo da proposta inicial via ANP. Erro: {e}. Criando proposta com dados padrão.")
                self.create_proposal(sample_reqs, initial_content={
                    "title": f"Proposta para {sample_reqs['nome_projeto']} (Rascunho de Fallback)",
                    "description": f"Proposta inicial gerada automaticamente. Necessita de revisão manual devido a um erro na geração do conteúdo pelo LLM: {e}.",
                    "problem_understanding_moai": "Análise de problema padrão.",
                    "solution_proposal_moai": "Solução padrão.",
                    "scope_moai": "Escopo padrão.",
                    "technologies_suggested_moai": "Tecnologias padrão.",
                    "estimated_value_moai": 0.0,
                    "estimated_time_moai": "Indefinido",
                    "terms_conditions_moai": "Termos e condições padrão."
                })

            # Criar uma proposta aprovada de exemplo para já ter um projeto
            sample_reqs_approved = {
                "nome_projeto": "Plataforma de E-commerce B2B",
                "nome_cliente": "Distribuidores Integrados S.A.",
                "problema_negocio": "A Distributedora Integrada precisa modernizar seu canal de vendas B2B, substituindo pedidos manuais por uma plataforma online que integre com seu ERP, otimize o processo de pedidos e acompanhamento.",
                "objetivos_projeto": "Digitalizar o processo de vendas B2B, reduzir erros, melhorar a experiência do cliente e fornecer dados de vendas em tempo real.",
                "funcionalidades_esperadas": "Catálogo de produtos, gestão de preços personalizados por cliente, histórico de pedidos, integração com ERP (SAP), gestão de usuários, dashboard de analytics.",
                "restricoes": r"Orçamento de até R\$ 120.000,00. Prazo de 6 meses para lançamento. Alta segurança. Multi-idioma.",
                "publico_alvo": "Clientes B2B da Distribuidores Integrados (empresas, revendedores)."
            }
            try:
                # Geração do conteúdo da proposta inicial
                # Assumimos que ANPAgent.generate_proposal_content retorna um Dict[str, Any]
                proposal_content_approved_dict = self.anp_agent.generate_proposal_content(sample_reqs_approved)
                proposal_content_approved_dict['estimated_value_moai'] = self._convert_estimated_value_to_float(
                    proposal_content_approved_dict.get('estimated_value_moai')
                )

                # Cria a proposta como "pending" primeiro, pois o estado "approved" é definido na atualização
                approved_proposal_obj = self.create_proposal(sample_reqs_approved, status="pending", initial_content=proposal_content_approved_dict)
                
                # Gerar a versão final (aprovada) da proposta, que pode ter mais detalhes ou formatação final
                # Assumimos que ANPAgent.generate_approved_proposal_content retorna um Dict[str, Any]
                final_proposal_details_dict = self.anp_agent.generate_approved_proposal_content(approved_proposal_obj.dict())
                final_proposal_details_dict['estimated_value_moai'] = self._convert_estimated_value_to_float(
                    final_proposal_details_dict.get('estimated_value_moai')
                )

                # Atualiza a proposta existente com os detalhes finais e o status de "approved"
                self.db_manager.update_proposal(
                    approved_proposal_obj.id,
                    **final_proposal_details_dict, # Usa os detalhes do conteúdo final
                    status="approved", # Define o status como aprovado
                    approved_at=datetime.datetime.now() # Registra a data de aprovação
                )
                
                # Recupera a proposta atualizada para ter os dados completos (incluindo approved_at)
                approved_proposal_obj_final = self.db_manager.get_proposal_by_id(approved_proposal_obj.id)
                if not approved_proposal_obj_final:
                    raise Exception(f"Proposta {approved_proposal_obj.id} não encontrada após atualização.")

                project_id = str(uuid.uuid4())
                project = Project(
                    id=project_id,
                    proposal_id=approved_proposal_obj_final.id,
                    name=sample_reqs_approved['nome_projeto'],
                    client_name=sample_reqs_approved['nome_cliente'],
                    status="active",
                    progress=20,
                    started_at=datetime.datetime.now()
                )
                self.db_manager.add_project(project.dict())
                self._add_moai_log("PROJECT_CREATED", f"Projeto '{project.name}' criado a partir da proposta {approved_proposal_obj_final.id[:8]}...", project_id=project.id)

                logger.info(f"Iniciando orquestração de agentes para o projeto {project.name}...")
                self._orchestrate_after_approval(approved_proposal_obj_final.id, project.id)

                # Assumimos que ADEXAgent.generate_code retorna um Dict[str, Any]
                initial_brief = self._build_code_generation_brief(project, "Configuração inicial do projeto (estrutura base, scripts de setup e README).")
                code_result = self.adex_agent.generate_code(project.name, project.client_name, initial_brief)
                if code_result.get("filename"):
                    self.db_manager.add_generated_code(GeneratedCode(
                        id=str(uuid.uuid4()),
                        project_id=project_id,
                        filename=code_result.get('filename', 'initial_config.py'),
                        language=code_result.get('language', 'Python'),
                        content=code_result.get('content', '# Initial configuration code'),
                        description=code_result.get('description', 'Código de configuração inicial gerado pelo ADE-X'),
                        generated_at=datetime.datetime.now()
                    ).dict())
                    self._add_moai_log("CODE_GENERATED", f"Código inicial gerado pelo ADE-X para {project.name}.", project_id=project.id, agent_id="ADE-X")
                else:
                    logger.error(f"Falha na geração de código: {code_result.get('message', 'Erro desconhecido')}")
                    self._add_moai_log("CODE_GEN_FAILED", f"Falha na geração de código inicial para {project.name}. Erro: {code_result.get('message', 'Erro desconhecido')}", project_id=project.id, agent_id="ADE-X", status="ERROR")

            except Exception as e:
                logger.error(f"ERRO: Falha ao gerar conteúdo da proposta aprovada via ANP. Erro: {e}. Criando proposta com dados padrão.")
                approved_proposal_obj = self.create_proposal(sample_reqs_approved, status="approved", initial_content={
                    "title": f"Proposta Aprovada para {sample_reqs_approved['nome_projeto']} (Rascunho de Fallback)",
                    "description": f"Proposta aprovada, mas com conteúdo padrão devido a erro do LLM: {e}.",
                    "problem_understanding_moai": "Análise de problema padrão (aprovada).",
                    "solution_proposal_moai": "Solução padrão (aprovada).",
                    "scope_moai": "Escopo padrão (aprovado).",
                    "technologies_suggested_moai": "Tecnologias padrão (aprovada).",
                    "estimated_value_moai": 0.0,
                    "estimated_time_moai": "Indefinido",
                    "terms_conditions_moai": "Termos e condições padrão (aprovados)."
                })
                project_id = str(uuid.uuid4())
                project = Project(
                    id=project_id,
                    proposal_id=approved_proposal_obj.id,
                    name=sample_reqs_approved['nome_projeto'],
                    client_name=sample_reqs_approved['nome_cliente'],
                    status="active",
                    progress=20,
                    started_at=datetime.datetime.now()
                )
                self.db_manager.add_project(project.dict())
                self._add_moai_log("PROJECT_CREATED_FALLBACK", f"Projeto '{project.name}' criado com dados de fallback devido a erro LLM.", project_id=project.id)
        else:
            logger.info("Dados de exemplo carregados ou já existentes.")

        projects = self.db_manager.get_all_projects()
        for project in projects:
            if project.status == "active":
                try:
                    generated_code_snippets = self.db_manager.get_generated_code_for_project(project.id)
                    # Assumimos que AQTAgent.generate_quality_report retorna um Dict[str, Any]
                    quality_report_dict = self.aqt_agent.generate_quality_report(project.id, project.name, [c.dict() for c in generated_code_snippets])
                    self.db_manager.add_quality_report(QualityReport(
                        id=str(uuid.uuid4()), project_id=project.id, report_data=quality_report_dict, generated_at=datetime.datetime.now()
                    ).dict())
                    self._add_moai_log("QUALITY_REPORT_GENERATED", f"Relatório de qualidade gerado para {project.name}.", project_id=project.id, agent_id="AQT")
                except Exception as e:
                    logger.error(f"Falha ao gerar relatório de qualidade para {project.name}: {e}")
                    self._add_moai_log("QUALITY_REPORT_FAILED", f"Falha ao gerar relatório de qualidade para {project.name}. Erro: {e}", project_id=project.id, agent_id="AQT", status="ERROR")

                try:
                    generated_code_snippets = self.db_manager.get_generated_code_for_project(project.id)
                    # Assumimos que ASEAgent.generate_security_report retorna um Dict[str, Any]
                    security_report_dict = self.ase_agent.generate_security_report(project.id, project.name, [c.dict() for c in generated_code_snippets])
                    self.db_manager.add_security_report(SecurityReport(
                        id=str(uuid.uuid4()), project_id=project.id, report_data=security_report_dict, generated_at=datetime.datetime.now()
                    ).dict())
                    self._add_moai_log("SECURITY_REPORT_GENERATED", f"Relatório de segurança gerado para {project.name}.", project_id=project.id, agent_id="ASE")
                except Exception as e:
                    logger.error(f"Falha ao gerar relatório de segurança para {project.name}: {e}")
                    self._add_moai_log("SECURITY_REPORT_FAILED", f"Falha ao gerar relatório de segurança para {project.name}. Erro: {e}", project_id=project.id, agent_id="ASE", status="ERROR")

                try:
                    # Define chosen_doc_type uma vez antes de chamar o agente
                    chosen_doc_type = random.choice(["Documentação Técnica", "Manual do Usuário"]) 
                    relevant_info = f"Detalhes do projeto {project.name}, funcionalidades principais, e tecnologias usadas."
                    # Assumimos que ADOAgent.generate_documentation retorna um Dict[str, Any]
                    doc_content_dict = self.ado_agent.generate_documentation(project.id, project.name, chosen_doc_type, relevant_info)
                    
                    if doc_content_dict.get('content'):
                        # Usa o document_type do dicionário retornado pelo ADO, ou volta para chosen_doc_type
                        final_doc_type = doc_content_dict.get('document_type', chosen_doc_type)

                        self.db_manager.add_documentation(Documentation(
                            id=str(uuid.uuid4()),
                            project_id=project.id,
                            filename=doc_content_dict.get('filename', f'doc_{uuid.uuid4().hex[:8]}.md'),
                            content=doc_content_dict['content'],
                            document_type=final_doc_type, # Usa o final_doc_type determinado
                            version=doc_content_dict.get('version', 'N/A'),
                            last_updated=datetime.datetime.now()
                        ).dict())
                        self._add_moai_log("DOCUMENTATION_GENERATED", f"Documentação '{final_doc_type}' gerada para {project.name}.", project_id=project.id, agent_id="ADO")
                except Exception as e:
                    logger.error(f"Falha ao gerar documentação para {project.name}: {e}")
                    self._add_moai_log("DOCUMENTATION_FAILED", f"Falha ao gerar documentação para {project.name}. Erro: {e}", project_id=project.id, agent_id="ADO", status="ERROR")
                
                try:
                    # Assumimos que AMSAgent.generate_monitoring_summary retorna um Dict[str, Any]
                    monitoring_summary_dict = self.ams_agent.generate_monitoring_summary(project_id=project.id, project_name=project.name)
                    self.db_manager.add_monitoring_summary(MonitoringSummary(
                        id=str(uuid.uuid4()), project_id=project.id, summary_data=monitoring_summary_dict, generated_at=datetime.datetime.now()
                    ).dict())
                    self._add_moai_log("PROJECT_MONITORING_SUMMARY", f"Resumo de monitoramento gerado para {project.name}.", project_id=project.id, agent_id="AMS")
                except Exception as e:
                    logger.error(f"Falha ao gerar resumo de monitoramento para {project.name}: {e}")
                    self._add_moai_log("PROJECT_MONITORING_FAILED", f"Falha ao gerar resumo de monitoramento para {project.name}. Erro: {e}", project_id=project.id, agent_id="AMS", status="ERROR")

        try:
            # Assumimos que AMSAgent.generate_monitoring_summary retorna um Dict[str, Any]
            global_monitoring_summary_dict = self.ams_agent.generate_monitoring_summary(project_id=None)
            existing_global_summary = self.db_manager.get_monitoring_summary(project_id=None)
            if existing_global_summary and existing_global_summary.id:
                self.db_manager.update_monitoring_summary(existing_global_summary.id, summary_data=global_monitoring_summary_dict)
            else:
                self.db_manager.add_monitoring_summary(MonitoringSummary(
                    id=str(uuid.uuid4()), project_id=None, summary_data=global_monitoring_summary_dict, generated_at=datetime.datetime.now()
                ).dict())
            self._add_moai_log("GLOBAL_MONITORING_SUMMARY", "Resumo de monitoramento global gerado/atualizado.", agent_id="AMS")
        except Exception as e:
            logger.error(f"Falha ao gerar resumo de monitoramento global: {e}")
            self._add_moai_log("GLOBAL_MONITORING_FAILED", f"Falha ao gerar resumo de monitoramento global. Erro: {e}", agent_id="AMS", status="ERROR")

    def create_proposal(self, req_data: Dict[str, Any], status: str = "pending", initial_content: Optional[Dict[str, Any]] = None) -> Proposal:
        proposal_id = str(uuid.uuid4())
        submitted_at = datetime.datetime.now()
        approved_at = submitted_at if status == "approved" else None

        if initial_content is None:
            logger.warning("create_proposal chamado sem initial_content. Gerando conteúdo básico.")
            initial_content = {
                "title": f"Proposta para {req_data.get('nome_projeto', 'Novo Projeto')} (Padrão)",
                "description": f"Proposta inicial para {req_data.get('problema_negocio', 'um problema de negócio')}.",
                "problem_understanding_moai": "Análise de problema padrão.",
                "solution_proposal_moai": "Solução proposta padrão.",
                "scope_moai": "Escopo padrão.",
                "technologies_suggested_moai": "Tecnologias padrão.",
                "estimated_value_moai": None, # Valor padrão como None, para Optional[float]
                "estimated_time_moai": "Indefinido",
                "terms_conditions_moai": "Termos e condições padrão."
            }
        
        # Converte o valor estimado para float se ele vier como string formatada
        estimated_value = self._convert_estimated_value_to_float(initial_content.get('estimated_value_moai'))

        proposal = Proposal(
            id=proposal_id,
            title=initial_content.get('title', f"Proposta para {req_data.get('nome_projeto', 'Novo Projeto')}") or f"Proposta para {req_data.get('nome_projeto', 'Novo Projeto')}",
            description=initial_content.get('description', f"Proposta gerada para {req_data.get('nome_cliente', 'o cliente')}") or f"Proposta gerada para {req_data.get('nome_cliente', 'o cliente')}",
            requirements=req_data,
            problem_understanding_moai=initial_content.get('problem_understanding_moai', "") or "",
            solution_proposal_moai=initial_content.get('solution_proposal_moai', "") or "",
            scope_moai=initial_content.get('scope_moai', "") or "",
            technologies_suggested_moai=initial_content.get('technologies_suggested_moai', "") or "",
            estimated_value_moai=estimated_value,
            estimated_time_moai=initial_content.get('estimated_time_moai', "") or "",
            terms_conditions_moai=initial_content.get('terms_conditions_moai', "") or "",
            status=status,
            submitted_at=submitted_at,
            approved_at=approved_at
        )
        self.db_manager.add_proposal(proposal.dict())
        self._add_moai_log("PROPOSAL_CREATED", f"Proposta '{proposal.title}' criada com status '{status}'.", project_id=proposal_id)
        return proposal

    def update_proposal_content(self, proposal_id: str, updated_fields: Dict[str, Any]):
        # Converte o valor estimado para float se ele vier como string formatada no update
        if 'estimated_value_moai' in updated_fields:
            updated_fields['estimated_value_moai'] = self._convert_estimated_value_to_float(
                updated_fields['estimated_value_moai']
            )
        
        self.db_manager.update_proposal(proposal_id, **updated_fields)
        self._add_moai_log("PROPOSAL_UPDATED", f"Proposta {proposal_id[:8]}... atualizada.", project_id=proposal_id)

    def update_proposal_status(self, proposal_id: str, new_status: str):
        self.db_manager.update_proposal_status(proposal_id, new_status)
        self._add_moai_log("PROPOSAL_STATUS_CHANGED", f"Status da proposta {proposal_id[:8]}... alterado para '{new_status}'.", project_id=proposal_id, status=new_status.upper())
        
        if new_status == "approved":
            proposal = self.db_manager.get_proposal_by_id(proposal_id)
            if proposal:
                project_id = str(uuid.uuid4())
                project = Project(
                    id=project_id,
                    proposal_id=proposal.id,
                    name=proposal.title,
                    client_name=proposal.requirements.get('nome_cliente', 'Cliente Desconhecido'),
                    status="active",
                    progress=0,
                    started_at=datetime.datetime.now()
                )
                self.db_manager.add_project(project.dict())
                self._add_moai_log("PROJECT_CREATED", f"Projeto '{project.name}' criado a partir da proposta {proposal_id[:8]}...", project_id=project_id, status="SUCCESS")
                
                self._orchestrate_after_approval(proposal_id, project_id)
                
                return project_id
            else:
                logger.error(f"MOAI: Proposta com ID {proposal_id} não encontrada para criar projeto.")
                self._add_moai_log("PROJECT_CREATION_FAILED", f"Falha ao criar projeto: Proposta {proposal_id[:8]}... não encontrada.", project_id=proposal_id, status="ERROR")
                return None
        return None

    def _orchestrate_after_approval(self, proposal_id: str, project_id: str):
        logger.info(f"MOAI: Iniciando orquestração pós-aprovação para proposta {proposal_id[:8]}... e projeto {project_id[:8]}...")
        self._add_moai_log("ORCHESTRATION_START", "Iniciando orquestração pós-aprovação.", project_id=project_id)

        try:
            # 1. AID: Provisionar o ambiente do projeto
            self._update_agent_status("AID", "IN_PROGRESS", project_id, "Provisionando ambiente.")
            project_obj_for_aid = self.db_manager.get_project_by_id(project_id)
            if not project_obj_for_aid:
                raise Exception(f"Projeto {project_id} não encontrado durante orquestração para AID.")
            # Assumimos que AIDAgent.provision_environment retorna um Dict[str, Any]
            aid_response = self.aid_agent.provision_environment(project_id, project_obj_for_aid.name)
            if aid_response["success"]:
                self._update_agent_status("AID", "COMPLETED", project_id, aid_response["message"])
                self._add_moai_log("ENV_PROVISIONED", aid_response["message"], project_id=project_id, agent_id="AID")
            else:
                self._update_agent_status("AID", "FAILED", project_id, aid_response["message"])
                self._add_moai_log("ENV_PROVISION_FAILED", aid_response["message"], project_id=project_id, agent_id="AID", status="ERROR")
                raise Exception(aid_response["message"])

            # 2. AID: Configurar as rotinas de backup
            self._update_agent_status("AID", "IN_PROGRESS", project_id, "Configurando backups.")
            # Assumimos que AIDAgent.configure_backups retorna um Dict[str, Any]
            aid_backup_response = self.aid_agent.configure_backups(project_id, project_obj_for_aid.name)
            if aid_backup_response["success"]:
                self._update_agent_status("AID", "COMPLETED", project_id, aid_backup_response["message"])
                self._add_moai_log("BACKUPS_CONFIGURED", aid_backup_response["message"], project_id=project_id, agent_id="AID")
            else:
                self._update_agent_status("AID", "FAILED", project_id, aid_backup_response["message"])
                self._add_moai_log("BACKUP_CONFIG_FAILED", aid_backup_response["message"], project_id=project_id, agent_id="AID", status="ERROR")
                raise Exception(aid_backup_response["message"])

            # 3. Gerar código inicial do projeto (usando ADE-X)
            if not self.db_manager.get_generated_code_for_project(project_id):
                self._update_agent_status("ADE-X", "IN_PROGRESS", project_id, "Gerando código inicial.")
                project_obj = self.db_manager.get_project_by_id(project_id) # Recupera novamente para garantir o estado mais recente
                
                if project_obj:
                    # Assumimos que ADEXAgent.generate_code retorna um Dict[str, Any]
                    code_brief = self._build_code_generation_brief(project_obj, "Configuração inicial do projeto (setup de ambiente, estrutura de diretórios e ponto de entrada).")
                    code_result = self.adex_agent.generate_code(project_obj.name, project_obj.client_name, code_brief)
                    if code_result.get("filename"):
                        self.db_manager.add_generated_code(GeneratedCode(
                            id=str(uuid.uuid4()),
                            project_id=project_id,
                            filename=code_result.get('filename', 'initial_config.py'),
                            language=code_result.get('language', 'Python'),
                            content=code_result.get('content', '# Initial configuration code'),
                            description=code_result.get('description', 'Código de configuração inicial gerado pelo ADE-X'),
                            generated_at=datetime.datetime.now()
                        ).dict())
                        self._update_agent_status("ADE-X", "COMPLETED", project_id, f"Código inicial '{code_result['filename']}' gerado.")
                        self._add_moai_log("CODE_GENERATED", f"Código inicial '{code_result['filename']}' gerado pelo ADE-X.", project_id=project_id, agent_id="ADE-X")
                    else:
                        self._update_agent_status("ADE-X", "FAILED", project_id, f"Falha na geração de código inicial: {code_result.get('message', 'Erro desconhecido')}")
                        self._add_moai_log("CODE_GEN_FAILED", f"Falha na geração de código inicial. Erro: {code_result.get('message', 'Erro desconhecido')}", project_id=project_id, agent_id="ADE-X", status="ERROR")
                else:
                    logger.error(f"Projeto {project_id} não encontrado para gerar código inicial.")
                    self._add_moai_log("CODE_GEN_FAILED", f"Projeto {project_id} não encontrado para gerar código inicial.", project_id=project_id, agent_id="ADE-X", status="ERROR")
            
            self.db_manager.update_project_progress(project_id, 10)
            self._add_moai_log("PROJECT_PROGRESS_UPDATED", "Progresso do projeto atualizado para 10% (ambiente e código inicial).", project_id=project_id)

            self._add_moai_log("ORCHESTRATION_COMPLETED", "Orquestração pós-aprovação concluída com sucesso.", project_id=project_id)

        except Exception as e:
            logger.error(f"ERRO CRÍTICO: Falha na orquestração de agentes para o projeto {project_id[:8]}.... Erro: {e}")
            self._add_moai_log("ORCHESTRATION_FAILED", f"Falha crítica na orquestração: {e}", project_id=project_id, status="CRITICAL")
            self.db_manager.update_project_status(project_id, "on hold")
            self._add_moai_log("PROJECT_STATUS_CHANGED", "Projeto colocado 'em espera' devido a falha na orquestração.", project_id=project_id, status="ON_HOLD")


    def get_dashboard_summary(self) -> Dict[str, Any]:
        proposals = self.db_manager.get_all_proposals()
        projects = self.db_manager.get_all_projects()
        
        total_proposals = len(proposals)
        pending_proposals = len([p for p in proposals if p.status == "pending"])
        approved_proposals = len([p for p in proposals if p.status == "approved"])
        rejected_proposals = len([p for p in proposals if p.status == "rejected"])

        total_projects = len(projects)
        active_projects = len([p for p in projects if p.status == "active"])
        completed_projects = len([p for p in projects if p.status == "completed"])

        total_estimated_value_approved_proposals = 0.0
        for p in proposals:
            if p.status == "approved" and p.estimated_value_moai is not None:
                total_estimated_value_approved_proposals += p.estimated_value_moai

        # Mock de agentes em atividade - para simulação no dashboard
        agents_in_activity = self.get_agents_in_activity() # Usa o método atualizado
        
        return {
            "total_proposals": total_proposals,
            "pending_proposals": pending_proposals,
            "approved_proposals": approved_proposals,
            "rejected_proposals": rejected_proposals,
            "total_projects": total_projects,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "total_estimated_value_approved_proposals": total_estimated_value_approved_proposals,
            "agents_in_activity": agents_in_activity
        }

    def get_agents_in_activity(self) -> List[Dict[str, Any]]:
        active_agents = []
        
        llm_available = self.llm_simulator.is_available() # Usa o método is_available do LLMSimulator
        
        if llm_available:
            # Lista de todos os agentes e seus modelos
            all_agent_codes = [
                'ARA', 'AAD', 'AGP', 'ANP', 'ADE-X', 'AQT', 'ASE', 'ADO', 'AMS', 'AID'
            ]
            
            for agent_code in all_agent_codes:
                model_name = get_agent_model(agent_code) # Obtém o modelo configurado
                active_agents.append({"name": agent_code, "status": "Pronto", "last_task": f"Aguardando tarefa ({model_name})"})
        else:
            active_agents.extend([
                {"name": "LLM_Service", "status": "OFFLINE", "last_task": "Verificar Ollama"},
                {"name": "MOAI_Core", "status": "DEGRADADO", "last_task": "Dependências ausentes"},
            ])
        
        # Marca aleatoriamente alguns agentes como 'Em Atividade' para simulação no dashboard
        num_busy_agents = min(random.randint(0, len(active_agents)), len(active_agents)) # No máximo todos, no mínimo 0
        busy_sample = random.sample(active_agents, k=num_busy_agents)
        for agent in busy_sample:
            agent["status"] = "Em Atividade"
            agent["last_task"] = f"Processando... ({agent['name']})" # Atualiza a mensagem para refletir a atividade
        return active_agents

    def get_infrastructure_health(self) -> Dict[str, Any]:
        overall_status = random.choice(["Operacional", "Atenção", "Crítico"])
        return {
            "overall_status": overall_status,
            "components": {
                "Servidores App": {"status": "Operacional", "message": "Todos OK", "last_log_time": datetime.datetime.now().isoformat()},
                "Banco de Dados": {"status": "Operacional", "message": "Latência normal", "last_log_time": datetime.datetime.now().isoformat()},
                "Rede": {"status": "Operacional", "message": "Tráfego estável", "last_log_time": datetime.datetime.now().isoformat()}
            }
        }
    
    # Assumimos que AIDAgent.get_infrastructure_status retorna um Dict[str, Any]
    def get_project_infra_status(self, project_id: str) -> Dict[str, Any]:
        return self.aid_agent.get_infrastructure_status(project_id)

    # Assumimos que AIDAgent.trigger_manual_backup retorna um Dict[str, Any]
    def trigger_manual_backup(self, project_id: str) -> Dict[str, Any]:
        return self.aid_agent.trigger_manual_backup(project_id)

    # Assumimos que AIDAgent.schedule_test_restore retorna um Dict[str, Any]
    def schedule_test_restore(self, project_id: str) -> Dict[str, Any]:
        return self.aid_agent.schedule_test_restore(project_id)

    def get_moai_log_events_count(self) -> Dict[str, int]:
        all_logs = self.db_manager.get_all_moai_logs()
        event_counts = {}
        for log in all_logs:
            event_counts[log.event_type] = event_counts.get(log.event_type, 0) + 1
        return event_counts

    def get_all_proposals(self) -> List[Proposal]:
        return self.db_manager.get_all_proposals()

    def get_pending_proposals(self) -> int:
        return len(self.db_manager.get_proposals(status="pending"))

    def get_proposals(self, status: Optional[str] = None) -> List[Proposal]:
        return self.db_manager.get_proposals(status)

    def get_proposal_by_id(self, proposal_id: str) -> Optional[Proposal]:
        return self.db_manager.get_proposal_by_id(proposal_id)

    def delete_proposal(self, proposal_id: str) -> bool:
        project = self.db_manager.get_project_by_proposal_id(proposal_id)
        if project:
            self.db_manager.delete_generated_code_by_project(project.id)
            self.db_manager.delete_quality_report_by_project(project.id)
            self.db_manager.delete_security_report_by_project(project.id)
            self.db_manager.delete_documentation_by_project(project.id)
            self.db_manager.delete_monitoring_summary_by_project(project.id)
            self.db_manager.delete_moai_logs_by_project(project.id)
            self.db_manager.delete_project(project.id)
            self._add_moai_log("PROJECT_DELETED", f"Projeto {project.id[:8]}... associado à proposta {proposal_id[:8]}... excluído.", project_id=project.id)
        
        self.db_manager.delete_moai_logs_by_project(proposal_id)
        
        success = self.db_manager.delete_proposal(proposal_id)
        if success:
            self._add_moai_log("PROPOSAL_DELETED", f"Proposta {proposal_id[:8]}... excluída com sucesso.", project_id=proposal_id, status="SUCCESS")
        else:
            self. _add_moai_log("PROPOSAL_DELETE_FAILED", f"Falha ao excluir proposta {proposal_id[:8]}....", project_id=proposal_id, status="ERROR")
        return success

    def get_all_projects(self) -> List[Project]:
        return self.db_manager.get_all_projects()

    def get_project_by_id(self, project_id: str) -> Optional[Project]:
        return self.db_manager.get_project_by_id(project_id)

    def update_project_details(self, project_id: str, updated_fields: Dict[str, Any]):
        self.db_manager.update_project(project_id, **updated_fields)
        self._add_moai_log("PROJECT_UPDATED", f"Detalhes do projeto {project_id[:8]}... atualizados.", project_id=project_id)

    def get_project_phases_status(self, project_id: str) -> List[Dict[str, Any]]:
        project = self.db_manager.get_project_by_id(project_id)
        if not project:
            return [{"phase": "Erro", "status": "Projeto não encontrado."}]

        progress = project.progress
        phases = [
            {"name": "Iniciação", "status": "Concluído", "progress_threshold": 5},
            {"name": "Análise e Design", "status": "Concluído", "progress_threshold": 20},
            {"name": "Desenvolvimento", "status": "Em Andamento", "progress_threshold": 60},
            {"name": "Testes", "status": "Não Iniciado", "progress_threshold": 80},
            {"name": "Implantação", "status": "Não Iniciado", "progress_threshold": 95},
            {"name": "Monitoramento", "status": "Não Iniciado", "progress_threshold": 100}
        ]

        for phase in phases:
            if progress < phase["progress_threshold"]:
                if phase["status"] == "Concluído":
                    phase["status"] = "Em Andamento"
                elif phase["status"] == "Não Iniciado" and progress >= (phase["progress_threshold"] / 2):
                     phase["status"] = "Em Andamento"
            else:
                phase["status"] = "Concluido"
        
        if project.status == "active" and progress > 5 and progress < 100:
            for phase in phases:
                if phase["name"] == "Desenvolvimento" and phase["status"] == "Não Iniciado":
                    phase["status"] = "Em Andamento"
                    break
        
        return phases

    def get_generated_code_for_project(self, project_id: str) -> List[GeneratedCode]:
        return self.db_manager.get_generated_code_for_project(project_id)

    def generate_code_for_project(self, project_id: str, filename: str, language: str, description: str) -> Dict[str, Any]:
        project = self.db_manager.get_project_by_id(project_id)
        if not project:
            return {"success": False, "message": "Projeto não encontrado."}
        
        try:
            contextual_description = self._build_code_generation_brief(project, description)
            # Assumimos que ADEXAgent.generate_code retorna um Dict[str, Any]
            code_result_dict = self.adex_agent.generate_code(project.name, project.client_name, contextual_description)
            
            if code_result_dict.get('content'):
                generated_code_obj = GeneratedCode(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    filename=code_result_dict.get('filename', filename),
                    language=code_result_dict.get('language', language),
                    content=code_result_dict['content'],
                    description=code_result_dict.get('description', description),
                    generated_at=datetime.datetime.now()
                )
                self.db_manager.add_generated_code(generated_code_obj.dict())
                self._add_moai_log("CODE_GENERATED_ON_DEMAND", f"Código '{generated_code_obj.filename}' gerado para {project.name}.", project_id=project_id, agent_id="ADE-X")
                return {"success": True, "message": f"Código gerado e salvo: {generated_code_obj.filename}"}
            else:
                return {"success": False, "message": f"ADE-X não gerou conteúdo de código. Erro: {code_result_dict.get('description', 'Conteúdo vazio.')}"}
        except Exception as e:
            logger.error(f"MOAI: Falha ao gerar código para projeto {project_id}: {e}")
            self._add_moai_log("CODE_GEN_FAILED_ON_DEMAND", f"Falha ao gerar código para {project_id}. Erro: {e}", project_id=project_id, agent_id="ADE-X", status="ERROR")
            return {"success": False, "message": f"Erro ao gerar código: {e}"}

    def get_quality_tests_report(self, project_id: str) -> Dict[str, Any]:
        report = self.db_manager.get_quality_report_for_project(project_id)
        if report:
            return report.report_data
        
        project = self.db_manager.get_project_by_id(project_id)
        if project:
            try:
                logger.info(f"MOAI: Gerando relatório de qualidade on-demand para o projeto {project_id}...")
                generated_code_snippets = self.db_manager.get_generated_code_for_project(project.id)
                # Assumimos que AQTAgent.generate_quality_report retorna um Dict[str, Any]
                quality_report_dict = self.aqt_agent.generate_quality_report(project.id, project.name, [c.dict() for c in generated_code_snippets])
                new_report = QualityReport(
                    id=str(uuid.uuid4()), project_id=project.id, report_data=quality_report_dict, generated_at=datetime.datetime.now()
                )
                self.db_manager.add_quality_report(new_report.dict())
                self._add_moai_log("QUALITY_REPORT_GENERATED_ON_DEMAND", f"Relatório de qualidade gerado on-demand para {project.name}..", project_id=project.id, agent_id="AQT")
                return new_report.report_data
            except Exception as e:
                logger.error(f"MOAI: Falha ao gerar relatório de qualidade on-demand para {project_id}: {e}")
                self._add_moai_log("QUALITY_REPORT_FAILED_ON_DEMAND", f"Falha ao gerar relatório de qualidade on-demand. Erro: {e}", project_id=project.id, agent_id="AQT", status="ERROR")
                return {"error": f"Falha ao gerar relatório de qualidade: {e}"}
        return {"error": "Relatório de qualidade não encontrado e projeto não existe para gerar um novo."}

    def get_security_audit_report(self, project_id: str) -> Dict[str, Any]:
        report = self.db_manager.get_security_report_for_project(project_id)
        if report:
            return report.report_data
        
        project = self.db_manager.get_project_by_id(project_id)
        if project:
            try:
                logger.info(f"MOAI: Gerando relatório de segurança on-demand para o projeto {project_id}...")
                generated_code_snippets = self.db_manager.get_generated_code_for_project(project.id)
                # Assumimos que ASEAgent.generate_security_report retorna um Dict[str, Any]
                security_report_dict = self.ase_agent.generate_security_report(project.id, project.name, [c.dict() for c in generated_code_snippets])
                new_report = SecurityReport(
                    id=str(uuid.uuid4()), project_id=project.id, report_data=security_report_dict, generated_at=datetime.datetime.now()
                )
                self.db_manager.add_security_report(new_report.dict())
                self._add_moai_log("SECURITY_REPORT_GENERATED_ON_DEMAND", f"Relatório de segurança gerado on-demand para {project.name}.", project_id=project.id, agent_id="ASE")
                return new_report.report_data
            except Exception as e:
                logger.error(f"MOAI: Falha ao gerar relatório de segurança on-demand para {project_id}: {e}")
                self._add_moai_log("SECURITY_REPORT_FAILED_ON_DEMAND", f"Falha ao gerar relatório de segurança on-demand. Erro: {e}", project_id=project.id, agent_id="ASE", status="ERROR")
                return {"error": f"Falha ao gerar relatório de segurança: {e}"}
        return {"error": "Relatório de segurança não encontrado e projeto não existe para gerar um novo."}

    def get_documentation_for_project(self, project_id: str) -> List[Documentation]:
        return self.db_manager.get_documentation_by_project(project_id)

    def generate_project_documentation(self, project_id: str) -> Dict[str, Any]:
        project = self.db_manager.get_project_by_id(project_id)
        if not project:
            return {"success": False, "message": "Projeto não encontrado."}
        
        try:
            proposal = self.db_manager.get_proposal_by_id(project.proposal_id)
            proposal_objectives = proposal.requirements.get('objetivos_projeto', 'N/A') if proposal else 'N/A'
            proposal_solution = proposal.solution_proposal_moai if proposal else 'N/A'
            proposal_technologies = proposal.technologies_suggested_moai if proposal else 'N/A'

            relevant_info = f"""
            Projeto: {project.name}
            Cliente: {project.client_name}
            Status: {project.status}
            Progresso: {project.progress}%
            Objetivos: {proposal_objectives}
            Solução Proposta: {proposal_solution}
            Tecnologias: {proposal_technologies}
            """
            
            # Define chosen_doc_type uma vez antes de chamar o agente
            chosen_doc_type = random.choice(["Documentação Técnica", "Manual do Usuário"])

            # Assumimos que ADOAgent.generate_documentation retorna um Dict[str, Any]
            doc_content_dict = self.ado_agent.generate_documentation(project.id, project.name, chosen_doc_type, relevant_info)
            
            if doc_content_dict.get('content'):
                # Usa o document_type do dicionário retornado pelo ADO, ou volta para chosen_doc_type
                final_doc_type = doc_content_dict.get('document_type', chosen_doc_type)

                new_doc_obj = Documentation(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    filename=doc_content_dict.get('filename', f'doc_{uuid.uuid4().hex[:8]}.md'),
                    content=doc_content_dict['content'],
                    document_type=final_doc_type, # Usa o final_doc_type determinado
                    version=doc_content_dict.get('version', '1.0'),
                    last_updated=datetime.datetime.now()
                )
                self.db_manager.add_documentation(new_doc_obj.dict())
                self._add_moai_log("DOCUMENTATION_GENERATED_ON_DEMAND", f"Documentação '{final_doc_type}' gerada on-demand para {project.name}.", project_id=project_id, agent_id="ADO")
                return {"success": True, "message": f"Documentação gerada e salva: {new_doc_obj.filename}"}
            else:
                return {"success": False, "message": f"ADO não gerou conteúdo de documentação. Erro: {doc_content_dict.get('description', 'Conteúdo vazio.')}"}
        except Exception as e:
            logger.error(f"MOAI: Falha ao gerar documentação para projeto {project_id}: {e}")
            self._add_moai_log("DOCUMENTATION_FAILED_ON_DEMAND", f"Falha ao gerar documentação para {project_id}. Erro: {e}", project_id=project_id, agent_id="ADO", status="ERROR")
            return {"success": False, "message": f"Erro ao gerar documentação: {e}"}

    def get_commercial_report(self) -> Dict[str, Any]:
        proposals = self.db_manager.get_all_proposals()
        total_geradas = len(proposals)
        aprovadas = len([p for p in proposals if p.status == "approved"])
        rejeitadas = len([p for p in proposals if p.status == "rejected"])
        
        taxa_aprovacao = (aprovadas / total_geradas * 100) if total_geradas > 0 else 0
        
        valor_total_gerado = 0.0
        valor_total_aprovado = 0.0
        for p in proposals:
            if p.estimated_value_moai is not None:
                valor_total_gerado += p.estimated_value_moai
                if p.status == "approved":
                    valor_total_aprovado += p.estimated_value_moai

        return {
            "propostas_geradas": total_geradas,
            "propostas_aprovadas": aprovadas,
            "propostas_rejeitadas": rejeitadas,
            "taxa_aprovacao": taxa_aprovacao,
            "valor_total_gerado": valor_total_gerado,
            "valor_total_aprovado": valor_total_aprovado,
            "last_update": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def get_monitoring_summary(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        summary_db = self.db_manager.get_monitoring_summary(project_id=project_id)
        if summary_db:
            return summary_db.summary_data
        
        project_name = None
        if project_id:
            project = self.db_manager.get_project_by_id(project_id)
            if project:
                project_name = project.name
        
        try:
            logger.info(f"MOAI: Gerando resumo de monitoramento on-demand para {'global' if project_id is None else project_name}...")
            # Assumimos que AMSAgent.generate_monitoring_summary retorna um Dict[str, Any]
            summary_data_dict = self.ams_agent.generate_monitoring_summary(project_id=project_id, project_name=project_name)
            
            new_summary = MonitoringSummary(
                id=str(uuid.uuid4()), project_id=project_id, summary_data=summary_data_dict, generated_at=datetime.datetime.now()
            )
            self.db_manager.add_monitoring_summary(new_summary.dict())
            self._add_moai_log("MONITORING_SUMMARY_GENERATED_ON_DEMAND", f"Resumo de monitoramento gerado on-demand para {'global' if project_id is None else project_name}.", project_id=project_id, agent_id="AMS")
            return new_summary.summary_data
        except Exception as e:
            logger.error(f"MOAI: Falha ao gerar resumo de monitoramento on-demand para {'global' if project_id is None else project_name}: {e}")
            self._add_moai_log("MONITORING_SUMMARY_FAILED_ON_DEMAND", f"Falha ao gerar resumo de monitoramento on-demand. Erro: {e}", project_id=project_id, agent_id="AMS", status="ERROR")
            return {"error": f"Falha ao gerar resumo de monitoramento: {e}"}

    def add_chat_message(self, sender: str, message: str):
        message_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now()
        chat_message = ChatMessage(id=message_id, sender=sender, message=message, timestamp=timestamp)
        self.db_manager.add_chat_message(chat_message.dict())

    def get_chat_history(self) -> List[ChatMessage]:
        return self.db_manager.get_chat_history()

    def process_moai_chat(self, user_message: str) -> str:
        messages_history = self.db_manager.get_chat_history()
        llm_messages = []
        for msg in messages_history:
            llm_messages.append({'role': msg.sender, 'content': msg.message})
        
        llm_messages.append({'role': 'user', 'content': user_message})

        # Sistema melhorado com instruções mais claras e precisas
        system_message = """Você é o MOAI, o Orquestrador Modular de IA da Synapse Forge. 

INSTRUÇÕES CRÍTICAS:
1. Sempre responda em português claro, correto e profissional
2. Use frases bem estruturadas, sem erros gramaticais ou de ortografia
3. Seja conciso mas informativo
4. Mantenha um tom profissional, visionário e amigável
5. Estruture suas respostas com clareza lógica

CONTEXTO:
- Você interage com o CVO (Chief Visionary Officer) da organização
- Forneça insights estratégicos baseados nos dados dos projetos e propostas
- Ofereça recomendações práticas e executáveis
- Responda com confiança sobre as capacidades do sistema

FORMATO:
- Respostas diretas e bem articuladas
- Se aplicável, use tópicos com marcadores
- Sempre mantenha coerência e clareza máxima
- Evite respostas fragmentadas ou truncadas"""
        
        llm_messages.insert(0, {'role': 'system', 'content': system_message})

        try:
            moai_model_name = get_agent_model('MOAI_Chat') # O MOAI Chat também usa um modelo
            # self.llm_simulator.chat sem response_model retorna Dict[str, Any] com a chave 'content'
            response_from_llm = self.llm_simulator.chat(llm_messages, model=moai_model_name)
            
            # Garante que response_from_llm é um dicionário e extrai o conteúdo.
            # Se não for um dicionário (o que não deveria ocorrer dado o design de LLMSimulator.chat),
            # ou se 'content' não estiver presente, fornece um fallback.
            if isinstance(response_from_llm, dict):
                content = response_from_llm.get('content')
                if content is not None:
                    return content
                else:
                    logger.warning("MOAI Chat: O dicionário de resposta do LLM não continha a chave 'content'. Retornando mensagem de fallback.")
                    return "Desculpe, a resposta do LLM não continha o conteúdo esperado."
            else:
                logger.error(f"MOAI Chat: O simulador LLM retornou um tipo inesperado: {type(response_from_llm)}. Esperava um dicionário.")
                return "Desculpe, não consegui obter uma resposta válida do LLM devido a um formato inesperado."

        except (LLMConnectionError, LLMGenerationError, json.JSONDecodeError) as e:
            logger.error(f"MOAI Chat: Falha ao processar mensagem do usuário '{user_message}'. Erro: {type(e).__name__}: {e}")
            return f"Desculpe, CVO, mas enfrentei um problema técnico ao processar sua solicitação ({type(e).__name__}). Por favor, tente novamente ou verifique a conexão com o LLM."
        except Exception as e:
            logger.error(f"MOAI Chat: Erro inesperado ao processar mensagem do usuário '{user_message}'. Erro: {type(e).__name__}: {e}")
            return f"Ocorreu um erro inesperado ao tentar responder, CVO. ({type(e).__name__}: {e})"
