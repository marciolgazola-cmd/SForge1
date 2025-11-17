import streamlit as st
import datetime
import random
import pandas as pd
import plotly.express as px
from typing import List, Dict, Any, Optional
import json

# Importa a classe SynapseForgeBackend corretamente, agora do arquivo MOAI
from MOAI import SynapseForgeBackend
# Importa as exceções personalizadas para tratamento específico
from llm_simulator import LLMConnectionError, LLMGenerationError
# Importa os modelos de dados
from data_models import Proposal, Project, Documentation, ChatMessage, MOAILog

# --- Inicializa o backend (Singleton) ---
backend = SynapseForgeBackend()

# --- Configuração da Página ---
st.set_page_config(
    page_title="CognitoLink - Synapse Forge",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Funções Auxiliares ---
def format_currency(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    return f"R\$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- Inicializa o estado da aplicação (session_state) ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = "dashboard"
if 'last_chat_message_time' not in st.session_state:
    st.session_state.last_chat_message_time = datetime.datetime.now()

# --- Funções para Navegação ---
def navigate_to(page_name: str):
    st.session_state.current_page = page_name
    st.rerun() # Force rerun to navigate

# --- Funções para Renderizar as Páginas ---

def dashboard_page():
    st.header("✨ Dashboard Executivo")
    st.markdown("""
    Visão de alto nível de projetos, KPIs, e o status geral da Synapse Forge,
    tudo atualizado em tempo real pelo MOAI.
    """)

    summary = backend.get_dashboard_summary()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Propostas", summary.get('total_proposals', 0))
        st.metric("Propostas Pendentes", summary.get('pending_proposals', 0))
    with col2:
        st.metric("Propostas Aprovadas", summary.get('approved_proposals', 0))
        st.metric("Propostas Rejeitadas", summary.get('rejected_proposals', 0))
    with col3:
        st.metric("Valor Total Aprovado", format_currency(summary.get('total_estimated_value_approved_proposals', 0.0)))

    st.markdown("---")

    col4, col5 = st.columns(2)
    with col4:
        st.subheader("Status dos Projetos:")
        st.metric("Total de Projetos", summary.get('total_projects', 0))
        st.metric("Projetos Ativos", summary.get('active_projects', 0))
        st.metric("Projetos Concluídos", summary.get('completed_projects', 0))
    with col5:
        st.subheader("Atividade dos Agentes de IA:")
        agents_data = summary.get('agents_in_activity', [])
        for agent in agents_data:
            st.markdown(f"- **{agent['name']}**: {agent['status']} - *{agent['last_task']}*")

    st.markdown("---")
    st.subheader("Infraestrutura Global (Simulada):")
    infra_health = backend.get_infrastructure_health()
    st.markdown(f"**Status Geral:** {infra_health['overall_status']}")
    for component, details in infra_health['components'].items():
        st.markdown(f"- **{component}**: {details['status']} - {details['message']}")

    st.markdown("---")
    st.subheader("Logs Recentes do MOAI:")
    all_logs = backend.db_manager.get_all_moai_logs() # Acessa diretamente o db_manager
    if all_logs:
        latest_logs = sorted(all_logs, key=lambda x: x.timestamp, reverse=True)[:5]
        for log in latest_logs:
            status_emoji = "✅" if log.status == "SUCCESS" else ("⚠️" if log.status == "WARNING" else ("❌" if log.status == "ERROR" or log.status == "CRITICAL" else "ℹ️"))
            project_info = f" (Projeto: {log.project_id[:8]}...)" if log.project_id else ""
            agent_info = f" (Agente: {log.agent_id})" if log.agent_id else ""
            st.write(f"{status_emoji} {log.timestamp.strftime('%H:%M:%S')} - **{log.event_type}**{project_info}{agent_info}: {log.details}")
    else:
        st.info("Nenhum log recente do MOAI para exibir.")


def requirements_entry_page():
    st.header("📝 Entrada de Requisitos")
    st.markdown("""
    Insira as necessidades do cliente para que o MOAI possa iniciar a orquestração e gerar uma proposta.
    """)

    with st.form("requirements_form"):
        project_name = st.text_input("Nome do Projeto", "Sistema de Gestão de Clientes v2")
        client_name = st.text_input("Nome do Cliente", "Acme Corporation")
        business_problem = st.text_area("Problema de Negócio (Desafio do Cliente)",
                                        "A Acme Corporation enfrenta dificuldades em gerenciar seu crescente número de clientes. O sistema atual é obsoleto, manual e não permite uma visão 360 do cliente, impactando a retenção e o cross-selling.")
        objectives = st.text_area("Objetivos do Projeto",
                                  "Desenvolver um CRM moderno que centralize informações de clientes, automatize interações, gere relatórios de vendas e integre com plataformas de e-mail marketing existentes.")
        expected_features = st.text_area("Funcionalidades Esperadas",
                                         "Cadastro de clientes, histórico de interações, gestão de leads, automação de e-mails, relatórios customizáveis, painel de controle para gerentes de vendas.")
        restrictions = st.text_area("Restrições e Requisitos Não Funcionais (Orçamento, Prazo, Segurança, etc.)",
                                      "Orçamento máximo de R\$ 80.000,00. Prazo de entrega de 5 meses para MVP. Alta disponibilidade (99.9%), escalabilidade para 10.000 usuários ativos simultâneos. Deve ser hospedado em ambiente de nuvem AWS.")
        target_audience = st.text_area("Público-alvo",
                                        "Equipes de vendas, marketing e suporte ao cliente da Acme Corporation.")

        submitted = st.form_submit_button("Gerar Proposta via MOAI")

        if submitted:
            req_data = {
                "nome_projeto": project_name,
                "nome_cliente": client_name,
                "problema_negocio": business_problem,
                "objetivos_projeto": objectives,
                "funcionalidades_esperadas": expected_features,
                "restricoes": restrictions,
                "publico_alvo": target_audience
            }
            try:
                with st.spinner("MOAI e Agentes trabalhando na sua proposta..."):
                    # MOAI agora espera um dicionário do ANP e o converte internamente
                    proposal_content_dict = backend.anp_agent.generate_proposal_content(req_data)
                    new_proposal = backend.create_proposal(req_data, initial_content=proposal_content_dict)
                st.success(f"Proposta '{new_proposal.title}' gerada com sucesso! ID: {new_proposal.id[:8]}... Enviada para Central de Aprovações.")
                navigate_to("aprovacoes")
            except (LLMConnectionError, LLMGenerationError) as e:
                st.error(f"Erro ao gerar proposta: {e}. Verifique a conexão com o LLM (Ollama) e se o modelo está baixado.")
            except Exception as e:
                st.error(f"Ocorreu um erro inesperado ao gerar a proposta: {e}")


def approvals_center_page():
    st.header("✅ Central de Aprovações")
    st.markdown("""
    Revise e aprove as propostas geradas pelo MOAI. Sua aprovação transforma a proposta em um projeto ativo.
    """)

    all_proposals = backend.get_all_proposals()
    
    pending_proposals = [p for p in all_proposals if p.status == "pending"]
    approved_proposals = [p for p in all_proposals if p.status == "approved"]
    rejected_proposals = [p for p in all_proposals if p.status == "rejected"]

    st.subheader(f"Propostas Pendentes ({len(pending_proposals)})")
    if pending_proposals:
        for proposal in pending_proposals:
            with st.expander(f"Proposta: {proposal.title} (ID: {proposal.id[:8]}...)"):
                st.subheader("1. Entendimento do Problema (MOAI):")
                st.write(proposal.problem_understanding_moai)
                st.subheader("2. Proposta de Solução (MOAI):")
                st.write(proposal.solution_proposal_moai)
                st.subheader("3. Escopo (MOAI):")
                st.write(proposal.scope_moai)
                st.subheader("4. Tecnologias Sugeridas (MOAI):")
                st.write(proposal.technologies_suggested_moai)
                st.subheader("5. Estimativas (MOAI):")
                st.write(f"**Valor Estimado:** {format_currency(proposal.estimated_value_moai)}")
                st.write(f"**Prazo Estimado:** {proposal.estimated_time_moai}")
                st.subheader("6. Termos e Condições (MOAI):")
                st.write(proposal.terms_conditions_moai)
                
                edit_key = f"edit_proposal_content_{proposal.id}"
                if edit_key not in st.session_state:
                    st.session_state[edit_key] = False

                col_actions = st.columns(3)
                with col_actions[0]:
                    if st.button(f"Aprovar Proposta {proposal.id[:4]}...", key=f"approve_{proposal.id}"):
                        with st.spinner(f"Aprovando proposta {proposal.id[:8]}... e iniciando orquestração do projeto..."):
                            project_id = backend.update_proposal_status(proposal.id, "approved")
                            if project_id:
                                st.success(f"Proposta {proposal.id[:8]}... aprovada! Projeto {project_id[:8]}... criado e orquestração iniciada.")
                            else:
                                st.error(f"Erro ao criar projeto para proposta {proposal.id[:8]}.... Verifique os logs do MOAI.")
                            st.rerun()
                with col_actions[1]:
                    if st.button(f"Rejeitar Proposta {proposal.id[:4]}...", key=f"reject_{proposal.id}"):
                        with st.spinner(f"Rejeitando proposta {proposal.id[:8]}..."):
                            backend.update_proposal_status(proposal.id, "rejected")
                        st.warning(f"Proposta {proposal.id[:8]}... rejeitada.")
                        st.rerun()
                with col_actions[2]:
                     if st.button(f"✏️ Editar Conteúdo {proposal.id[:4]}...", key=f"edit_{proposal.id}"):
                         st.session_state[edit_key] = not st.session_state[edit_key]
                         st.rerun() # Force rerun to show/hide edit form
                
                if st.session_state[edit_key]:
                    st.subheader(f"Editar Conteúdo da Proposta {proposal.id[:8]}...")
                    with st.form(key=f"form_edit_proposal_{proposal.id}"):
                        edited_title = st.text_input("Título", value=proposal.title)
                        edited_desc = st.text_area("Descrição", value=proposal.description)
                        edited_problem_understanding = st.text_area("Entendimento do Problema", value=proposal.problem_understanding_moai)
                        edited_solution_proposal = st.text_area("Solução Proposta", value=proposal.solution_proposal_moai)
                        edited_scope = st.text_area("Escopo", value=proposal.scope_moai)
                        edited_technologies = st.text_area("Tecnologias Sugeridas", value=proposal.technologies_suggested_moai)
                        
                        # Exibe o valor formatado para edição, e tenta converter de volta
                        edited_estimated_value_str = st.text_input("Valor Estimado (R\$)", value=format_currency(proposal.estimated_value_moai))
                        edited_estimated_time = st.text_input("Prazo Estimado", value=proposal.estimated_time_moai)
                        edited_terms_conditions = st.text_area("Termos e Condições", value=proposal.terms_conditions_moai)

                        save_changes = st.form_submit_button("Salvar Alterações")
                        if save_changes:
                            try:
                                # A função update_proposal_content já faz a conversão de string para float
                                updated_fields = {
                                    "title": edited_title,
                                    "description": edited_desc,
                                    "problem_understanding_moai": edited_problem_understanding,
                                    "solution_proposal_moai": edited_solution_proposal,
                                    "scope_moai": edited_scope,
                                    "technologies_suggested_moai": edited_technologies,
                                    "estimated_value_moai": edited_estimated_value_str, # Passa string, backend converterá
                                    "estimated_time_moai": edited_estimated_time,
                                    "terms_conditions_moai": edited_terms_conditions
                                }
                                backend.update_proposal_content(proposal.id, updated_fields)
                                st.success("Proposta atualizada com sucesso!")
                                st.session_state[edit_key] = False # Fecha o formulário após salvar
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao salvar alterações: {e}. Certifique-se de que o valor estimado é um número válido.")

    else:
        st.info("Nenhuma proposta pendente no momento. 🎉")

    st.subheader(f"Propostas Aprovadas ({len(approved_proposals)})")
    if approved_proposals:
        for proposal in approved_proposals:
            with st.expander(f"Proposta: {proposal.title} (ID: {proposal.id[:8]}...)"):
                st.write(f"**Aprovada em:** {proposal.approved_at.strftime('%Y-%m-%d %H:%M:%S')}")
                st.subheader("Entendimento do Problema:")
                st.write(proposal.problem_understanding_moai)
                st.subheader("Proposta de Solução:")
                st.write(proposal.solution_proposal_moai)
                st.subheader("Escopo:")
                st.write(proposal.scope_moai)
                st.subheader("Tecnologias Sugeridas:")
                st.write(proposal.technologies_suggested_moai)
                st.subheader("Estimativas:")
                st.write(f"**Valor Estimado:** {format_currency(proposal.estimated_value_moai)}")
                st.write(f"**Prazo Estimado:** {proposal.estimated_time_moai}")
                st.subheader("Termos e Condições:")
                st.write(proposal.terms_conditions_moai)
                if st.button(f"Excluir Proposta e Projeto Associado {proposal.id[:4]}...", key=f"delete_approved_{proposal.id}", type="secondary"):
                    if backend.delete_proposal(proposal.id):
                        st.success(f"Proposta {proposal.id[:8]}... e projeto associado excluídos com sucesso.")
                    else:
                        st.error(f"Erro ao excluir proposta {proposal.id[:8]}... e projeto associado.")
                    st.rerun()
    else:
        st.info("Nenhuma proposta aprovada ainda.")

    st.subheader(f"Propostas Rejeitadas ({len(rejected_proposals)})")
    if rejected_proposals:
        for proposal in rejected_proposals:
            with st.expander(f"Proposta: {proposal.title} (ID: {proposal.id[:8]}...)"):
                st.subheader("Entendimento do Problema:")
                st.write(proposal.problem_understanding_moai)
                st.subheader("Estimativas:")
                st.write(f"**Valor Estimado:** {format_currency(proposal.estimated_value_moai)}")
                st.write(f"**Status:** {proposal.status}")
                if st.button(f"Excluir Proposta Rejeitada {proposal.id[:4]}...", key=f"delete_rejected_{proposal.id}", type="secondary"):
                    if backend.delete_proposal(proposal.id):
                        st.success(f"Proposta {proposal.id[:8]}... excluída com sucesso.")
                    else:
                        st.error(f"Erro ao excluir proposta {proposal.id[:8]}....")
                    st.rerun()
    else:
        st.info("Nenhuma proposta rejeitada.")


def project_timeline_page():
    st.header("⏳ Linha do Tempo do Projeto")
    st.markdown("""
    Visualize o progresso dos projetos em andamento e as fases concluídas ou futuras.
    """)

    all_projects = backend.get_all_projects() # CORRIGIDO: get_all_projects()
    if not all_projects:
        st.info("Nenhum projeto ativo para exibir a linha do tempo.")
        return

    # Mapeia ID do projeto para o nome formatado para o selectbox
    project_options_display = {f"{p.id[:8]}... - {p.name}": p.id for p in all_projects} # CORRIGIDO: p.id
    selected_project_key = st.selectbox(
        "Selecione um Projeto",
        options=list(project_options_display.keys()),
        format_func=lambda x: x # Mantém o formato no selectbox
    )

    if selected_project_key:
        selected_project_id = project_options_display[selected_project_key]
        project = backend.get_project_by_id(selected_project_id)

        if project:
            st.markdown(f"### Projeto: {project.name} - {project.client_name} (ID: {project.id[:8]}...)") # CORRIGIDO: project.id
            st.progress(project.progress / 100.0, text=f"Progresso Geral: {project.progress}%")
            st.write(f"**Status:** {project.status}")
            st.write(f"**Iniciado em:** {project.started_at.strftime('%Y-%m-%d')}")
            if project.completed_at:
                st.write(f"**Concluído em:** {project.completed_at.strftime('%Y-%m-%d')}")

            st.subheader("Fases do Projeto:")
            phases_data = backend.get_project_phases_status(project.id) # CORRIGIDO: project.id
            
            # Criar um DataFrame para exibição (opcional, mas pode ser útil para gráficos futuros)
            phases_df = pd.DataFrame(phases_data)
            
            # Exibir como tabela ou lista
            for phase in phases_data:
                status_emoji = "✅" if phase["status"] == "Concluído" else ("⏳" if phase["status"] == "Em Andamento" else "⚪")
                st.markdown(f"- {status_emoji} **{phase['name']}**: {phase['status']}")
            
            st.subheader("Logs do Projeto:")
            project_logs = [log for log in backend.db_manager.get_all_moai_logs() if log.project_id == project.id]
            if project_logs:
                latest_project_logs = sorted(project_logs, key=lambda x: x.timestamp, reverse=True)[:10]
                for log in latest_project_logs:
                    status_emoji = "✅" if log.status == "SUCCESS" else ("⚠️" if log.status == "WARNING" else ("❌" if log.status == "ERROR" or log.status == "CRITICAL" else "ℹ️"))
                    agent_info = f" (Agente: {log.agent_id})" if log.agent_id else ""
                    st.write(f"{status_emoji} {log.timestamp.strftime('%H:%M:%S')} - **{log.event_type}**{agent_info}: {log.details}")
            else:
                st.info("Nenhum log para este projeto ainda.")

        else:
            st.error("Projeto selecionado não encontrado.")
    else:
        st.info("Selecione um projeto para ver a linha do tempo.")


def detailed_reports_page():
    st.header("📊 Relatórios Detalhados")
    st.markdown("""
    Acesse relatórios completos de desempenho, qualidade, segurança e aspectos comerciais da Synapse Forge.
    """)

    report_type = st.radio(
        "Selecione o Tipo de Relatório",
        ("Comercial", "Qualidade e Testes", "Segurança e Auditoria", "Monitoramento Geral"),
        key="report_type_radio"
    )

    if report_type == "Comercial":
        st.subheader("Relatório Comercial")
        commercial_report = backend.get_commercial_report()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Propostas Geradas", commercial_report['propostas_geradas'])
            st.metric("Propostas Aprovadas", commercial_report['propostas_aprovadas'])
            st.metric("Propostas Rejeitadas", commercial_report['propostas_rejeitadas'])
        with col2:
            st.metric("Taxa de Aprovação", f"{commercial_report['taxa_aprovacao']:.2f}%")
            st.metric("Valor Total Gerado", format_currency(commercial_report['valor_total_gerado']))
            st.metric("Valor Total Aprovado", format_currency(commercial_report['valor_total_aprovado']))
        
        st.caption(f"Última atualização: {commercial_report['last_update']}")

        # Gerar gráfico de propostas por status
        df_proposals_status = pd.DataFrame({
            'Status': ['Aprovadas', 'Rejeitadas', 'Pendentes'],
            'Quantidade': [commercial_report['propostas_aprovadas'], commercial_report['propostas_rejeitadas'], commercial_report['propostas_geradas'] - commercial_report['propostas_aprovadas'] - commercial_report['propostas_rejeitadas']]
        })
        fig = px.pie(df_proposals_status, values='Quantidade', names='Status', title='Propostas por Status')
        st.plotly_chart(fig, use_container_width=True)


    elif report_type == "Qualidade e Testes":
        st.subheader("Relatório de Qualidade e Testes (AQT)")
        all_projects = backend.get_all_projects() # CORRIGIDO: get_all_projects()
        if not all_projects:
            st.info("Nenhum projeto ativo para gerar relatórios de qualidade.")
            return

        project_options_display = {f"{p.id[:8]}... - {p.name}": p.id for p in all_projects} # CORRIGIDO: p.id
        selected_project_key = st.selectbox(
            "Selecione um Projeto para Relatório de Qualidade",
            options=list(project_options_display.keys()),
            key="select_quality_project"
        )

        if selected_project_key:
            selected_project_id = project_options_display[selected_project_key]
            quality_report_data = backend.get_quality_tests_report(selected_project_id)

            if quality_report_data and not quality_report_data.get("error"):
                st.markdown(f"**Relatório para:** {selected_project_key}")
                st.write(f"**Status Geral:** {quality_report_data.get('overall_status', 'N/A')}")
                st.write(f"**Total de Testes:** {quality_report_data.get('total_tests', 'N/A')}")
                st.write(f"**Testes Aprovados:** {quality_report_data.get('passed_tests', 'N/A')}")
                st.write(f"**Testes Falhos:** {quality_report_data.get('failed_tests', 'N/A')}")
                
                st.markdown("---")
                st.subheader("Detalhamento dos Testes:")
                test_results = quality_report_data.get('test_results', [])
                if test_results:
                    for test in test_results:
                        status_emoji = "✅" if test['status'] == 'Passed' else "❌"
                        st.markdown(f"- {status_emoji} **{test['name']}**: {test['status']} - {test['message']}")
                else:
                    st.info("Nenhum detalhe de teste disponível.")
            else:
                st.warning(f"Nenhum relatório de qualidade encontrado para o projeto selecionado ou {quality_report_data.get('error', 'Erro desconhecido')}.")
        else:
            st.info("Selecione um projeto.")

    elif report_type == "Segurança e Auditoria":
        st.subheader("Relatório de Segurança e Auditoria (ASE)")
        all_projects = backend.get_all_projects() # CORRIGIDO: get_all_projects()
        if not all_projects:
            st.info("Nenhum projeto ativo para gerar relatórios de segurança.")
            return
        
        project_options_display = {f"{p.id[:8]}... - {p.name}": p.id for p in all_projects} # CORRIGIDO: p.id
        selected_project_key = st.selectbox(
            "Selecione um Projeto para Relatório de Segurança",
            options=list(project_options_display.keys()),
            key="select_security_project"
        )

        if selected_project_key:
            selected_project_id = project_options_display[selected_project_key]
            security_report_data = backend.get_security_audit_report(selected_project_id)

            if security_report_data and not security_report_data.get("error"):
                st.markdown(f"**Relatório para:** {selected_project_key}")
                st.write(f"**Status Geral de Segurança:** {security_report_data.get('overall_security_status', 'N/A')}")
                st.write(f"**Vulnerabilidades Encontradas:** {security_report_data.get('vulnerabilities_found', 'N/A')}")
                st.write(f"**Nível de Risco:** {security_report_data.get('risk_level', 'N/A')}")
                
                st.markdown("---")
                st.subheader("Vulnerabilidades Detalhadas:")
                vulnerabilities = security_report_data.get('vulnerabilities', [])
                if vulnerabilities:
                    for vuln in vulnerabilities:
                        st.markdown(f"- **{vuln['name']}**: {vuln['severity']} - {vuln['description']}")
                else:
                    st.info("Nenhuma vulnerabilidade detalhada disponível.")
            else:
                st.warning(f"Nenhum relatório de segurança encontrado para o projeto selecionado ou {security_report_data.get('error', 'Erro desconhecido')}.")
        else:
            st.info("Selecione um projeto.")

    elif report_type == "Monitoramento Geral":
        st.subheader("Relatório de Monitoramento Geral (AMS)")
        monitoring_summary = backend.get_monitoring_summary() # Resumo global
        if monitoring_summary and not monitoring_summary.get("error"):
            st.write(f"**Status Geral dos Sistemas:** {monitoring_summary.get('system_health', {}).get('status', 'N/A')}")
            st.write(f"**Uptime Médio:** {monitoring_summary.get('system_health', {}).get('average_uptime', 'N/A')}")
            
            st.markdown("---")
            st.subheader("Uso de Recursos (Global):")
            resources = monitoring_summary.get('resource_usage', {})
            st.write(f"**CPU:** {resources.get('cpu_usage', 'N/A')}")
            st.write(f"**Memória:** {resources.get('memory_usage', 'N/A')}")
            st.write(f"**Rede:** {resources.get('network_traffic', 'N/A')}")
            
            st.markdown("---")
            st.subheader("Alertas Recentes:")
            alerts = monitoring_summary.get('recent_alerts', [])
            if alerts:
                for alert in alerts:
                    st.warning(f"- **{alert['severity']}**: {alert['message']} ({alert['timestamp']})")
            else:
                st.info("Nenhum alerta recente.")
        else:
            st.warning(f"Nenhum resumo de monitoramento global disponível ou {monitoring_summary.get('error', 'Erro desconhecido')}.")


def code_viewer_page():
    st.header("💻 Visualizador de Código Gerado")
    st.markdown("""
    Inspecione o código-fonte gerado pelos Agentes de Desenvolvimento (ADE-X).
    """)

    all_projects = backend.get_all_projects() # CORRIGIDO: get_all_projects()
    if not all_projects:
        st.info("Nenhum projeto ativo com código gerado para exibir.")
        return

    project_options_display = {f"{p.id[:8]}... - {p.name}": p.id for p in all_projects} # CORRIGIDO: p.id
    selected_project_key = st.selectbox(
        "Selecione um Projeto",
        options=list(project_options_display.keys()),
        key="select_code_project"
    )

    if selected_project_key:
        selected_project_id = project_options_display[selected_project_key]
        project_name_display = selected_project_key.split(' - ')[1] # Extrai o nome do projeto

        st.subheader(f"Código Gerado para {project_name_display} (ID: {selected_project_id[:8]}...)") # CORRIGIDO: selected_project_id

        # Formulário para gerar novo código (exemplo)
        with st.expander("Gerar Novo Código (via ADE-X)"):
            with st.form(key=f"form_generate_code_{selected_project_id}"):
                code_filename = st.text_input("Nome do Arquivo", value="new_module.py")
                code_language = st.text_input("Linguagem", value="Python")
                code_description = st.text_area("Descrição do Código a ser Gerado", value="Um módulo Python para manipulação de dados.")
                submit_code_gen = st.form_submit_button("Gerar Código")

                if submit_code_gen:
                    with st.spinner("ADE-X está gerando o código..."):
                        result = backend.generate_code_for_project(selected_project_id, code_filename, code_language, code_description)
                        if result["success"]:
                            st.success(result["message"])
                            st.rerun()
                        else:
                            st.error(f"Falha ao gerar código: {result['message']}")


        generated_code_list = backend.get_generated_code_for_project(selected_project_id)
        if generated_code_list:
            # Dropdown para selecionar o arquivo de código
            code_files_map = {c.filename: c for c in generated_code_list}
            selected_code_file_name = st.selectbox("Selecione um arquivo de código:", list(code_files_map.keys()))

            if selected_code_file_name:
                selected_code = code_files_map[selected_code_file_name]
                st.code(selected_code.content, language=selected_code.language)
                st.markdown(f"**Descrição:** {selected_code.description}")
                st.markdown(f"**Gerado em:** {selected_code.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.info("Nenhum código gerado para este projeto ainda.")
    else:
        st.info("Selecione um projeto para visualizar o código.")


def infra_backup_management_page():
    st.header("⚙️ Gestão de Infraestrutura e Backup")
    st.markdown("""
    Gerencie e monitore a infraestrutura dos projetos e as estratégias de backup.
    """)

    all_projects = backend.get_all_projects() # CORRIGIDO: get_all_projects()
    if not all_projects:
        st.info("Nenhum projeto ativo para gerenciar infraestrutura e backup.")
        return

    project_options_display = {f"{p.id[:8]}... - {p.name}": p.id for p in all_projects} # CORRIGIDO: p.id
    selected_project_key = st.selectbox(
        "Selecione um Projeto",
        options=list(project_options_display.keys()),
        key="select_infra_project"
    )

    if selected_project_key:
        selected_project_id = project_options_display[selected_project_key]
        project_name_display = selected_project_key.split(' - ')[1]

        st.subheader(f"Ambiente do Projeto: {project_name_display} (ID: {selected_project_id[:8]}...)") # CORRIGIDO: selected_project_id

        st.markdown("---")
        st.subheader("Status da Infraestrutura (AID):")
        infra_status = backend.get_project_infra_status(selected_project_id)
        if infra_status:
            st.write(f"**Status Geral:** {infra_status.get('overall_status', 'N/A')}")
            for item, detail in infra_status.get('resources', {}).items():
                st.markdown(f"- **{item}**: {detail['status']} - {detail['message']}")
        else:
            st.info("Status da infraestrutura não disponível.")

        st.markdown("---")
        st.subheader("Gestão de Backups (AID):")
        backup_info = backend.aid_agent.get_backup_status(selected_project_id) # Usando AID diretamente
        if backup_info:
            st.write(f"**Último Backup:** {backup_info.get('last_backup', 'N/A')}")
            st.write(f"**Frequência:** {backup_info.get('frequency', 'N/A')}")
            st.write(f"**Retenção:** {backup_info.get('retention_policy', 'N/A')}")
            st.write(f"**Status:** {backup_info.get('status', 'N/A')}")

            col_backup_buttons = st.columns(2)
            with col_backup_buttons[0]:
                if st.button("Manual Backup", key=f"manual_backup_{selected_project_id}", use_container_width=True):
                    with st.spinner("Executando backup manual..."):
                        result = backend.trigger_manual_backup(selected_project_id)
                        if result["success"]:
                            st.success(result["message"])
                        else:
                            st.error(f"Erro no backup manual: {result['message']}")
                    st.rerun()
            with col_backup_buttons[1]:
                if st.button("Schedule Test Restore", key=f"schedule_test_restore_{selected_project_id}", use_container_width=True):
                    with st.spinner("Agendando teste de restauração..."):
                        result = backend.schedule_test_restore(selected_project_id)
                        if result["success"]:
                            st.success(result["message"])
                        else:
                            st.error(f"Erro ao agendar teste de restauração: {result['message']}")
                    st.rerun()
        else:
            st.info("Informações de backup não disponíveis.")
    else:
        st.info("Selecione um projeto para gerenciar a infraestrutura e backup.")


def documentation_page():
    st.header("📚 Módulo de Documentação")
    st.markdown("""
    Acesse e gere a documentação completa dos projetos, mantendo tudo atualizado pelo ADO.
    """)

    all_projects = backend.get_all_projects() # CORRIGIDO: get_all_projects()
    if not all_projects:
        st.info("Nenhum projeto ativo com documentação para exibir.")
        return

    project_options_display = {f"{p.id[:8]}... - {p.name}": p.id for p in all_projects} # CORRIGIDO: p.id
    selected_project_key = st.selectbox(
        "Selecione um Projeto",
        options=list(project_options_display.keys()),
        key="select_doc_project"
    )

    if selected_project_key:
        selected_project_id = project_options_display[selected_project_key]
        project_name_display = selected_project_key.split(' - ')[1]

        st.subheader(f"Documentação para {project_name_display} (ID: {selected_project_id[:8]}...)") # CORRIGIDO: selected_project_id

        if st.button(f"Gerar/Atualizar Documentação (ADO) para {project_name_display}", key=f"generate_doc_{selected_project_id}", use_container_width=True): # CORRIGIDO: selected_project_id
            with st.spinner("ADO está gerando/atualizando a documentação..."):
                result = backend.generate_project_documentation(selected_project_id)
                if result["success"]:
                    st.success(result["message"])
                else:
                    st.error(f"Falha ao gerar documentação: {result['message']}")
            st.rerun()

        documentation_list = backend.get_documentation_for_project(selected_project_id)
        if documentation_list:
            doc_files_map = {d.filename: d for d in documentation_list}
            selected_doc_file_name = st.selectbox("Selecione um documento:", list(doc_files_map.keys()))

            if selected_doc_file_name:
                selected_doc = doc_files_map[selected_doc_file_name]
                st.markdown(f"**Tipo:** {selected_doc.document_type}")
                st.markdown(f"**Versão:** {selected_doc.version}")
                st.markdown(f"**Última Atualização:** {selected_doc.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
                st.markdown("---")
                st.markdown(selected_doc.content) # Renderiza o markdown
        else:
            st.info("Nenhum documento gerado para este projeto ainda.")
    else:
        st.info("Selecione um projeto para visualizar a documentação.")


def moai_communication_page():
    st.header("💬 Comunicação com MOAI")
    st.markdown("""
    Converse diretamente com o MOAI para obter insights, status ou emitir comandos.
    """)

    st.subheader("Histórico de Conversa:")
    chat_history = backend.get_chat_history() # CORRIGIDO: usa o método do MOAI que já chama db_manager
    for chat_message in chat_history:
        with st.chat_message(chat_message.sender):
            st.markdown(chat_message.message)

    user_input = st.chat_input("Fale com o MOAI...")

    if user_input:
        backend.add_chat_message("user", user_input)
        with st.chat_message("user"):
            st.markdown(user_input)
        
        with st.spinner("MOAI está pensando..."):
            moai_response = backend.process_moai_chat(user_input)
        
        backend.add_chat_message("assistant", moai_response)
        with st.chat_message("assistant"):
            st.markdown(moai_response)
        
        # st.session_state.last_chat_message_time = datetime.datetime.now() # Não precisa de rerun imediato se a resposta já foi exibida
        st.rerun() # Force rerun to clear input box and update history fully


def project_management_page():
    st.header("🚧 Gestão de Projetos")
    st.markdown("""
    Gerencie os detalhes dos projetos, acompanhe o progresso e faça ajustes.
    """)

    all_projects = backend.get_all_projects() # CORRIGIDO: get_all_projects()
    if not all_projects:
        st.info("Nenhum projeto ativo para gerenciar.")
        return
    
    project_options_display = {f"{p.id[:8]}... - {p.name}": p.id for p in all_projects} # CORRIGIDO: p.id
    selected_project_key = st.selectbox(
        "Selecione um Projeto para Gerenciar",
        options=list(project_options_display.keys()),
        key="select_manage_project"
    )

    if selected_project_key:
        selected_project_id = project_options_display[selected_project_key]
        project = backend.get_project_by_id(selected_project_id)

        if project:
            st.subheader(f"Detalhes do Projeto: {project.name} (ID: {project.id[:8]}...)") # CORRIGIDO: project.id

            col_info_1, col_info_2 = st.columns(2)
            with col_info_1:
                st.write(f"**Cliente:** {project.client_name}")
                st.write(f"**Status:** {project.status}")
                st.write(f"**Iniciado em:** {project.started_at.strftime('%Y-%m-%d')}")
            with col_info_2:
                st.write(f"**Progresso:** {project.progress}%")
                if project.completed_at:
                    st.write(f"**Concluído em:** {project.completed_at.strftime('%Y-%m-%d')}")
                else:
                    st.write("**Concluído em:** N/A")

            # Editar detalhes básicos do projeto
            edit_project_basic_key = f"edit_project_basic_{project.id}"
            if edit_project_basic_key not in st.session_state:
                st.session_state[edit_project_basic_key] = False

            if st.button("✏️ Editar Detalhes Básicos do Projeto", key=f"btn_edit_proj_basic_{project.id}", use_container_width=True): # CORRIGIDO: project.id
                st.session_state[edit_project_basic_key] = not st.session_state[edit_project_basic_key]
                st.rerun()

            if st.session_state[edit_project_basic_key]:
                st.subheader(f"Editar Dados Básicos do Projeto {project.id[:8]}...")
                with st.form(key=f"form_edit_project_basic_{project.id}"):
                    edited_project_name = st.text_input("Nome do Projeto", value=project.name)
                    edited_client_name = st.text_input("Nome do Cliente", value=project.client_name)
                    edited_status = st.selectbox("Status", options=["active", "on hold", "completed", "cancelled"], index=["active", "on hold", "completed", "cancelled"].index(project.status))
                    edited_progress = st.slider("Progresso (%)", min_value=0, max_value=100, value=project.progress)
                    
                    save_basic_changes = st.form_submit_button("Salvar Detalhes Básicos")
                    if save_basic_changes:
                        try:
                            updated_fields = {
                                "name": edited_project_name,
                                "client_name": edited_client_name,
                                "status": edited_status,
                                "progress": edited_progress
                            }
                            if edited_status == "completed" and not project.completed_at:
                                updated_fields["completed_at"] = datetime.datetime.now()
                            elif edited_status != "completed" and project.completed_at:
                                updated_fields["completed_at"] = None # Remove data de conclusão se não estiver mais completo

                            backend.update_project_details(project.id, updated_fields)
                            st.success(f"Detalhes do projeto {project.id[:8]}... atualizados com sucesso!") # CORRIGIDO: project.id
                            st.session_state[edit_project_basic_key] = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar detalhes básicos: {e}")
            
            st.markdown("---")
            st.subheader("Especificações da Proposta Original:")
            proposal = backend.get_proposal_by_id(project.proposal_id)
            if proposal:
                st.write(f"**Título:** {proposal.title}")
                st.write(f"**Descrição:** {proposal.description}")
                st.write(f"**Status da Proposta:** {proposal.status}")
                st.write(f"**Valor Estimado:** {format_currency(proposal.estimated_value_moai)}")
                st.write(f"**Prazo Estimado:** {proposal.estimated_time_moai}")
                
                edit_proposal_spec_key = f"edit_proposal_spec_{proposal.id}"
                if edit_proposal_spec_key not in st.session_state:
                    st.session_state[edit_proposal_spec_key] = False

                if st.button("✏️ Revisar Especificações da Proposta", key=f"btn_edit_prop_spec_{proposal.id}", use_container_width=True):
                    st.session_state[edit_proposal_spec_key] = not st.session_state[edit_proposal_spec_key]
                    st.rerun()
                
                if st.session_state[edit_proposal_spec_key]:
                    st.subheader(f"Editar Especificações da Proposta {proposal.id[:8]}...")
                    with st.form(key=f"form_edit_proposal_spec_{proposal.id}"):
                        edited_proposal_title = st.text_input("Título da Proposta", value=proposal.title)
                        edited_problem_understanding = st.text_area("Entendimento do Problema (MOAI)", value=proposal.problem_understanding_moai)
                        edited_solution_proposal = st.text_area("Proposta de Solução (MOAI)", value=proposal.solution_proposal_moai)
                        edited_scope = st.text_area("Escopo (MOAI)", value=proposal.scope_moai)
                        edited_technologies = st.text_area("Tecnologias Sugeridas (MOAI)", value=proposal.technologies_suggested_moai)
                        edited_estimated_value_str = st.text_input("Valor Estimado (R\$)", value=format_currency(proposal.estimated_value_moai))
                        edited_estimated_time = st.text_input("Prazo Estimado", value=proposal.estimated_time_moai)
                        edited_terms_conditions = st.text_area("Termos e Condições (MOAI)", value=proposal.terms_conditions_moai)
                        
                        save_spec_changes = st.form_submit_button("Salvar Especificações da Proposta")
                        if save_spec_changes:
                            try:
                                updated_proposal_fields = {
                                    "title": edited_proposal_title,
                                    "problem_understanding_moai": edited_problem_understanding,
                                    "solution_proposal_moai": edited_solution_proposal,
                                    "scope_moai": edited_scope,
                                    "technologies_suggested_moai": edited_technologies,
                                    "estimated_value_moai": edited_estimated_value_str, # Passa string, backend converterá
                                    "estimated_time_moai": edited_estimated_time,
                                    "terms_conditions_moai": edited_terms_conditions
                                }
                                backend.update_proposal_content(proposal.id, updated_proposal_fields)
                                st.success(f"Especificações da proposta {proposal.id[:8]}... (projeto {project.id[:8]}...) atualizadas com sucesso!") # CORRIGIDO: project.id
                                st.session_state[edit_proposal_spec_key] = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao salvar especificações da proposta: {e}. Certifique-se de que o valor estimado é um número válido.")
                else:
                    st.subheader("1. Entendimento do Problema (MOAI):")
                    st.markdown(proposal.problem_understanding_moai)
                    st.subheader("2. Proposta de Solução (MOAI):")
                    st.markdown(proposal.solution_proposal_moai)
                    st.subheader("3. Escopo (MOAI):")
                    st.markdown(proposal.scope_moai)
                    st.subheader("4. Tecnologias Sugeridas (MOAI):")
                    st.markdown(proposal.technologies_suggested_moai)
                    st.subheader("5. Estimativas (MOAI):")
                    st.write(f"**Valor Estimado:** {format_currency(proposal.estimated_value_moai)}")
                    st.write(f"**Prazo Estimado:** {proposal.estimated_time_moai}")
                    st.subheader("6. Termos e Condições (MOAI):")
                    st.markdown(proposal.terms_conditions_moai)
            else:
                st.warning("Proposta associada não encontrada ou acessível.")
        else:
            st.info("Nenhuma proposta associada a este projeto.")
    st.markdown("--- \n _O MOAI garante que todas as revisões sejam documentadas e orquestradas._")


def about_page():
    st.header("ℹ️ Sobre o CognitoLink e a Synapse Forge")
    st.markdown("""
    O CognitoLink é a sua central de inteligência e controle na Synapse Forge,
    a empresa do futuro impulsionada por IA. Ele serve como a interface principal
    entre você, o CVO (Chief Visionary Officer), o MOAI (Modular Orchestrating AI)
    e o universo de Agentes de IA.
    """)
    st.write("""
    **Nossa Missão:** Transformar desafios complexos em soluções tecnológicas robustas e confiáveis,
    garantindo a evolução contínua da empresa com segurança e autonomia.
    """)
    st.markdown("--- \n _Impulsionando o futuro da tecnologia com inteligência artificial._")


# --- Sidebar de Navegação ---
with st.sidebar:
    # st.image("logo_sforge.jpg", use_column_width=True) # Certifique-se de que 'logo_sforge.jpg' está na pasta
    st.title("✨ CognitoLink")
    st.markdown("--- ✨ Visionary Command Center ✨ ---")

    st.subheader("Navegação Principal")
    
    if st.button("🌟 Dashboard Executivo", key="btn_dashboard", use_container_width=True):
        navigate_to("dashboard")
    
    if st.button("📝 Entrada de Requisitos", key="btn_requisitos", use_container_width=True):
        navigate_to("requisitos")
    
    pending_proposals_count = backend.get_pending_proposals()
    if st.button(f"✅ Central de Aprovações ({pending_proposals_count})", key="btn_aprovacoes", use_container_width=True):
        navigate_to("aprovacoes")
    
    if st.button("⏳ Linha do Tempo do Projeto", key="btn_timeline", use_container_width=True):
        navigate_to("timeline")
    
    if st.button("🚧 Gestão de Projetos", key="btn_project_management", use_container_width=True):
        navigate_to("project_management")
    
    if st.button("📊 Relatórios Detalhados", key="btn_relatorios", use_container_width=True):
        navigate_to("relatorios")
    
    if st.button("💬 Comunicação com MOAI", key="btn_chat_moai", use_container_width=True):
        navigate_to("chat_moai")
    
    if st.button("📚 Módulo de Documentação", key="btn_documentation", use_container_width=True):
        navigate_to("documentation")
    
    if st.button("💻 Visualizador de Código", key="btn_code_viewer", use_container_width=True):
        navigate_to("code_viewer")
    
    if st.button("⚙️ Gestão de Infraestrutura e Backup", key="btn_infra_backup", use_container_width=True):
        navigate_to("infra_backup")
    
    st.markdown("---")
    
    if st.button("ℹ️ Sobre o CognitoLink", key="btn_sobre", use_container_width=True):
        navigate_to("sobre")

# --- Roteamento de Páginas (Conteúdo Principal) ---
if st.session_state.current_page == "dashboard":
    dashboard_page()
elif st.session_state.current_page == "requisitos":
    requirements_entry_page()
elif st.session_state.current_page == "aprovacoes":
    approvals_center_page()
elif st.session_state.current_page == "timeline":
    project_timeline_page()
elif st.session_state.current_page == "project_management":
    project_management_page()
elif st.session_state.current_page == "relatorios":
    detailed_reports_page()
elif st.session_state.current_page == "chat_moai":
    moai_communication_page()
elif st.session_state.current_page == "code_viewer":
    code_viewer_page()
elif st.session_state.current_page == "infra_backup":
    infra_backup_management_page()
elif st.session_state.current_page == "documentation":
    documentation_page()
elif st.session_state.current_page == "sobre":
    about_page()