import streamlit as st
import streamlit.components.v1 as components
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
# Importa o módulo de tema customizado
from streamlit_theme import apply_custom_theme, format_status, create_card

# --- Aplicar Tema Customizado ---
apply_custom_theme()

# Forçar idioma pt-BR e habilitar spellcheck nos inputs/textarea do Streamlit
components.html("""
<script>
    document.documentElement.lang = 'pt-BR';
    function setPtBRSpell() {
        document.querySelectorAll('input, textarea').forEach(function(el){
            el.lang = 'pt-BR';
            el.setAttribute('spellcheck', 'true');
            el.setAttribute('autocapitalize', 'sentences');
        });
    }
    setPtBRSpell();
    const observer = new MutationObserver(function(){ setPtBRSpell(); });
    observer.observe(document.body, { childList: true, subtree: true });
</script>
""", height=0)

# --- Inicializa o backend (Singleton) ---
backend = SynapseForgeBackend()

# --- Funções Auxiliares ---
def format_currency(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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
        st.markdown("### 📋 Informações Básicas")
        col1, col2, col3 = st.columns(3)
        with col1:
            project_name = st.text_input("🏢 Nome do Projeto *", value="", help="Ex: Sistema de Gestão de Clientes")
        with col2:
            client_name = st.text_input("👤 Nome do Cliente *", value="", help="Ex: Acme Corporation")
        with col3:
            target_audience = st.text_input("🎯 Público-alvo", value="", help="Usuários principais da solução")
        
        st.markdown("### 🔍 Análise do Problema")
        business_problem = st.text_area("❓ Problema de Negócio (Desafio do Cliente) *", value="", height=120, help="Descreva o principal problema que precisa ser resolvido")
        
        st.markdown("### 💡 Solução Proposta")
        col4, col5 = st.columns(2)
        with col4:
            objectives = st.text_area("📍 Objetivos do Projeto", value="", height=100, help="Objetivos principais que a solução deve alcançar")
        with col5:
            expected_features = st.text_area("✨ Funcionalidades Esperadas", value="", height=100, help="Lista de funcionalidades principais")
        
        st.markdown("### 📊 Escopo e Restrições")
        restrictions = st.text_area("⚠️ Restrições e Requisitos (Orçamento, Prazo, Segurança, etc.)", value="", height=100, help="Limites técnicos, financeiros e temporais")

        submitted = st.form_submit_button("🚀 Gerar Proposta via MOAI", use_container_width=True)

        if submitted:
            # Validar campos obrigatórios
            if not project_name or not client_name or not business_problem:
                st.error("❌ Por favor, preencha pelo menos: Nome do Projeto, Cliente e Problema de Negócio")
            else:
                req_data = {
                    "nome_projeto": project_name.strip(),
                    "nome_cliente": client_name.strip(),
                    "problema_negocio": business_problem.strip(),
                    "objetivos_projeto": objectives.strip(),
                    "funcionalidades_esperadas": expected_features.strip(),
                    "restricoes": restrictions.strip(),
                    "publico_alvo": target_audience.strip()
                }
                try:
                    with st.spinner("⏳ MOAI e Agentes trabalhando na sua proposta..."):
                        # MOAI agora espera um dicionário do ANP e o converte internamente
                        proposal_content_dict = backend.anp_agent.generate_proposal_content(req_data)
                        new_proposal = backend.create_proposal(req_data, initial_content=proposal_content_dict)
                    st.success(f"✅ Proposta '{new_proposal.title}' gerada com sucesso! ID: {new_proposal.id[:8]}... Enviada para Central de Aprovações.")
                    navigate_to("aprovacoes")
                except (LLMConnectionError, LLMGenerationError) as e:
                    st.error(f"❌ Erro ao gerar proposta: {e}. Verifique a conexão com o LLM (Ollama) e se o modelo está baixado.")
                except Exception as e:
                    st.error(f"❌ Ocorreu um erro inesperado ao gerar a proposta: {e}")
                    st.info(f"Detalhes técnicos: {type(e).__name__}")


def approvals_center_page():
    st.header("✅ Central de Aprovações")
    st.markdown("""
    Revise e aprove as propostas geradas pelo MOAI. Sua aprovação transforma a proposta em um projeto ativo.
    """)

    all_proposals = backend.get_all_proposals()
    
    pending_proposals = [p for p in all_proposals if p.status == "pending"]
    approved_proposals = [p for p in all_proposals if p.status == "approved"]
    rejected_proposals = [p for p in all_proposals if p.status == "rejected"]

    # Abas para organizar as propostas
    tab1, tab2, tab3 = st.tabs([
        f"⏳ Pendentes ({len(pending_proposals)})", 
        f"✅ Aprovadas ({len(approved_proposals)})", 
        f"❌ Rejeitadas ({len(rejected_proposals)})"
    ])
    
    with tab1:
        if pending_proposals:
            for proposal in pending_proposals:
                with st.expander(f"📄 {proposal.title} (ID: {proposal.id[:8]}...)", expanded=False):
                    col_info = st.columns([2, 1])
                    
                    with col_info[0]:
                        st.markdown("#### 🔍 Entendimento do Problema")
                        st.write(proposal.problem_understanding_moai)
                        
                        st.markdown("#### 💡 Solução Proposta")
                        st.write(proposal.solution_proposal_moai)
                        
                        st.markdown("#### 📊 Escopo")
                        st.write(proposal.scope_moai)
                    
                    with col_info[1]:
                        st.markdown("#### 🛠️ Tecnologias")
                        st.write(proposal.technologies_suggested_moai)
                        
                        st.markdown("#### 💰 Estimativas")
                        # Exibir Valor e Prazo com fonte/tamanho consistentes aos campos do formulário
                        st.markdown(f"**Valor:** <span style='font-size:16px'>{format_currency(proposal.estimated_value_moai)}</span>", unsafe_allow_html=True)
                        st.markdown(f"**Prazo:** <span style='font-size:16px'>{proposal.estimated_time_moai}</span>", unsafe_allow_html=True)
                    
                    st.divider()
                    
                    st.markdown("#### 📋 Termos e Condições")
                    st.write(proposal.terms_conditions_moai)
                    
                    st.divider()
                    
                    edit_key = f"edit_proposal_content_{proposal.id}"
                    if edit_key not in st.session_state:
                        st.session_state[edit_key] = False

                    col_actions = st.columns(4)
                    with col_actions[0]:
                        if st.button("✅ Aprovar", key=f"approve_{proposal.id}", use_container_width=True):
                            with st.spinner(f"Aprovando proposta..."):
                                project_id = backend.update_proposal_status(proposal.id, "approved")
                                if project_id:
                                    st.success(f"✅ Proposta aprovada! Projeto iniciado.")
                                else:
                                    st.error(f"❌ Erro ao criar projeto.")
                                st.rerun()
                    
                    with col_actions[1]:
                        if st.button("❌ Rejeitar", key=f"reject_{proposal.id}", use_container_width=True):
                            with st.spinner(f"Rejeitando proposta..."):
                                backend.update_proposal_status(proposal.id, "rejected")
                            st.warning(f"⚠️ Proposta rejeitada.")
                            st.rerun()
                    
                    with col_actions[2]:
                        if st.button("✏️ Editar", key=f"edit_{proposal.id}", use_container_width=True):
                            st.session_state[edit_key] = not st.session_state[edit_key]
                            st.rerun()
                    
                    with col_actions[3]:
                        if st.button("📋 Visualizar Completo", key=f"full_{proposal.id}", use_container_width=True):
                            st.session_state[f"view_full_{proposal.id}"] = not st.session_state.get(f"view_full_{proposal.id}", False)
                            st.rerun()
                    
                    if st.session_state[edit_key]:
                        st.markdown("---")
                        st.subheader(f"✏️ Editar Conteúdo")
                        with st.form(key=f"form_edit_proposal_{proposal.id}"):
                            st.markdown("**Informações Básicas**")
                            col_basic = st.columns(2)
                            with col_basic[0]:
                                edited_title = st.text_input("Título", value=proposal.title)
                            with col_basic[1]:
                                edited_estimated_time = st.text_input("Prazo Estimado", value=proposal.estimated_time_moai)
                            
                            edited_desc = st.text_area("Descrição", value=proposal.description, height=80)
                            
                            st.markdown("**Análise e Proposta**")
                            col_analysis = st.columns(2)
                            with col_analysis[0]:
                                edited_problem_understanding = st.text_area("Entendimento do Problema", value=proposal.problem_understanding_moai, height=100)
                            with col_analysis[1]:
                                edited_solution_proposal = st.text_area("Solução Proposta", value=proposal.solution_proposal_moai, height=100)
                            
                            st.markdown("**Detalhes Técnicos**")
                            col_tech = st.columns(2)
                            with col_tech[0]:
                                edited_scope = st.text_area("Escopo", value=proposal.scope_moai, height=80)
                                edited_technologies = st.text_area("Tecnologias Sugeridas", value=proposal.technologies_suggested_moai, height=80)
                            with col_tech[1]:
                                edited_estimated_value_str = st.text_input("💰 Valor Estimado (R$)", value=format_currency(proposal.estimated_value_moai))
                                edited_terms_conditions = st.text_area("Termos e Condições", value=proposal.terms_conditions_moai, height=80)

                            col_submit = st.columns(2)
                            with col_submit[0]:
                                save_changes = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)
                            with col_submit[1]:
                                cancel_edit = st.form_submit_button("❌ Cancelar", use_container_width=True)
                            
                            if save_changes:
                                try:
                                    updated_fields = {
                                        "title": edited_title,
                                        "description": edited_desc,
                                        "problem_understanding_moai": edited_problem_understanding,
                                        "solution_proposal_moai": edited_solution_proposal,
                                        "scope_moai": edited_scope,
                                        "technologies_suggested_moai": edited_technologies,
                                        "estimated_value_moai": edited_estimated_value_str,
                                        "estimated_time_moai": edited_estimated_time,
                                        "terms_conditions_moai": edited_terms_conditions
                                    }
                                    backend.update_proposal_content(proposal.id, updated_fields)
                                    st.success("✅ Proposta atualizada com sucesso!")
                                    st.session_state[edit_key] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro ao salvar alterações: {e}")
        else:
            st.info("🎉 Nenhuma proposta pendente. Todas as propostas foram revisadas!")
    
    with tab2:
        if approved_proposals:
            for proposal in approved_proposals:
                with st.expander(f"✅ {proposal.title} (ID: {proposal.id[:8]}...)", expanded=False):
                    st.success(f"Aprovado em: {proposal.approved_at.strftime('%d/%m/%Y %H:%M') if proposal.approved_at else 'N/A'}")
                    st.write(proposal.description)
                    # Mostrar Valor e Prazo com mesmo estilo dos formulários
                    st.markdown(f"**Valor:** <span style='font-size:16px'>{format_currency(proposal.estimated_value_moai)}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Prazo:** <span style='font-size:16px'>{proposal.estimated_time_moai}</span>", unsafe_allow_html=True)
                    if st.button("📄 Ver Detalhes", key=f"view_approved_{proposal.id}"):
                        st.write(proposal.solution_proposal_moai)
        else:
            st.info("📭 Nenhuma proposta aprovada ainda.")
    
    with tab3:
        if rejected_proposals:
            for proposal in rejected_proposals:
                with st.expander(f"❌ {proposal.title} (ID: {proposal.id[:8]}...)", expanded=False):
                    st.error(f"Rejeitado em: {proposal.submitted_at.strftime('%d/%m/%Y %H:%M')}")
                    st.write(proposal.description)
        else:
            st.info("📭 Nenhuma proposta rejeitada.")


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
        backup_info = backend.aid_agent.configure_backups(selected_project_id, "Projeto Backup") # Obtém informações de backup
        if backup_info and backup_info.get('success'):
            details = backup_info.get('details', {})
            st.write(f"**Política de Backup:** {details.get('policy_data', 'N/A')}")
            st.write(f"**Último Status:** {details.get('last_backup_status', 'N/A')}")
            st.write(f"**Próximo Backup Agendado:** {details.get('next_scheduled_backup', 'N/A')}")
            st.write(f"**Mensagem:** {backup_info.get('message', 'N/A')}")

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
    Gerencie os detalhes dos projetos, acompanhe o progresso e faça ajustes em tempo real.
    """)

    all_projects = backend.get_all_projects()
    if not all_projects:
        st.info("🎉 Nenhum projeto ativo para gerenciar no momento.")
        return
    
    project_options_display = {f"{p.id[:8]}... - {p.name}": p.id for p in all_projects}
    selected_project_key = st.selectbox(
        "Selecione um Projeto para Gerenciar",
        options=list(project_options_display.keys()),
        key="select_manage_project"
    )

    if selected_project_key:
        selected_project_id = project_options_display[selected_project_key]
        project = backend.get_project_by_id(selected_project_id)

        if project:
            # Header com informações principais
            col_header1, col_header2, col_header3, col_header4 = st.columns(4)
            with col_header1:
                st.metric("📊 Progresso", f"{project.progress}%")
            with col_header2:
                status_emoji = {"active": "🟢", "on hold": "🟡", "completed": "✅", "cancelled": "⛔"}.get(project.status, "❓")
                st.metric("Status", f"{status_emoji} {project.status.title()}")
            with col_header3:
                st.metric("👤 Cliente", project.client_name[:20] + ("..." if len(project.client_name) > 20 else ""))
            with col_header4:
                st.metric("📅 Iniciado", project.started_at.strftime('%d/%m/%Y'))

            st.divider()

            # Abas para diferentes seções
            tab_details, tab_proposal, tab_edit = st.tabs(["📋 Detalhes", "📄 Proposta Original", "✏️ Editar"])
            
            with tab_details:
                st.subheader(f"Informações do Projeto: {project.name}")
                
                col_detail1, col_detail2 = st.columns(2)
                with col_detail1:
                    st.markdown("**Identificação**")
                    st.write(f"ID: `{project.id}`")
                    st.write(f"Nome: {project.name}")
                    st.write(f"Cliente: {project.client_name}")
                
                with col_detail2:
                    st.markdown("**Cronograma**")
                    st.write(f"Iniciado em: {project.started_at.strftime('%d/%m/%Y %H:%M')}")
                    if project.completed_at:
                        st.write(f"Concluído em: {project.completed_at.strftime('%d/%m/%Y %H:%M')}")
                    else:
                        st.write("Status: Em Andamento")
                
                st.markdown("**Progresso**")
                st.progress(project.progress / 100, text=f"{project.progress}%")
            
            with tab_proposal:
                st.subheader("📄 Especificações da Proposta Original")
                proposal = backend.get_proposal_by_id(project.proposal_id)

                if proposal:
                    col_prop1, col_prop2 = st.columns(2)
                    with col_prop1:
                        st.write(f"**Título:** {proposal.title}")
                        st.write(f"**Status:** {proposal.status}")
                    with col_prop2:
                        st.write(f"**Valor Estimado:** {format_currency(proposal.estimated_value_moai)}")
                        st.write(f"**Prazo Estimado:** {proposal.estimated_time_moai}")
                    
                    st.write(f"**Descrição:** {proposal.description}")
                    
                    st.markdown("### 🔍 Entendimento do Problema")
                    st.write(proposal.problem_understanding_moai)
                    
                    st.markdown("### 💡 Solução Proposta")
                    st.write(proposal.solution_proposal_moai)
                    
                    col_tech1, col_tech2 = st.columns(2)
                    with col_tech1:
                        st.markdown("### 📊 Escopo")
                        st.write(proposal.scope_moai)
                    with col_tech2:
                        st.markdown("### 🛠️ Tecnologias")
                        st.write(proposal.technologies_suggested_moai)
                    
                    st.markdown("### 📋 Termos e Condições")
                    st.write(proposal.terms_conditions_moai)
                else:
                    st.warning("⚠️ Proposta associada não encontrada ou não está acessível.")
            
            with tab_edit:
                st.subheader(f"✏️ Editar Projeto: {project.name}")
                
                st.markdown("### 📝 Dados Básicos do Projeto")
                with st.form(key=f"form_edit_project_{project.id}"):
                    col_edit1, col_edit2 = st.columns(2)
                    with col_edit1:
                        edited_project_name = st.text_input("Nome do Projeto", value=project.name)
                        edited_client_name = st.text_input("Nome do Cliente", value=project.client_name)
                    with col_edit2:
                        edited_status = st.selectbox("Status do Projeto", 
                            options=["active", "on hold", "completed", "cancelled"], 
                            index=["active", "on hold", "completed", "cancelled"].index(project.status))
                        edited_progress = st.slider("Progresso (%)", min_value=0, max_value=100, value=project.progress)
                    
                    st.divider()
                    st.markdown("### 🔧 Editar Especificações da Proposta")
                    
                    proposal = backend.get_proposal_by_id(project.proposal_id)
                    if proposal:
                        col_edit_title = st.columns(1)
                        edited_proposal_title = st.text_input("Título da Proposta", value=proposal.title)
                        
                        edited_problem_understanding = st.text_area("🔍 Entendimento do Problema", value=proposal.problem_understanding_moai, height=100)
                        edited_solution_proposal = st.text_area("💡 Solução Proposta", value=proposal.solution_proposal_moai, height=100)
                        
                        col_edit_scope = st.columns(2)
                        with col_edit_scope[0]:
                            edited_scope = st.text_area("📊 Escopo", value=proposal.scope_moai, height=80)
                        with col_edit_scope[1]:
                            edited_technologies = st.text_area("🛠️ Tecnologias", value=proposal.technologies_suggested_moai, height=80)
                        
                        col_edit_est = st.columns(2)
                        with col_edit_est[0]:
                            edited_estimated_value_str = st.text_input("💰 Valor Estimado (R$)", value=format_currency(proposal.estimated_value_moai))
                        with col_edit_est[1]:
                            edited_estimated_time = st.text_input("⏱️ Prazo Estimado", value=proposal.estimated_time_moai)
                        
                        edited_terms_conditions = st.text_area("📋 Termos e Condições", value=proposal.terms_conditions_moai, height=80)
                    
                    col_buttons = st.columns(2)
                    with col_buttons[0]:
                        save_changes = st.form_submit_button("💾 Salvar Todas as Alterações", use_container_width=True)
                    with col_buttons[1]:
                        cancel_edit = st.form_submit_button("❌ Cancelar", use_container_width=True)
                    
                    if save_changes:
                        try:
                            # Atualizar projeto
                            updated_project_fields = {
                                "name": edited_project_name,
                                "client_name": edited_client_name,
                                "status": edited_status,
                                "progress": edited_progress
                            }
                            if edited_status == "completed" and not project.completed_at:
                                updated_project_fields["completed_at"] = datetime.datetime.now()
                            elif edited_status != "completed" and project.completed_at:
                                updated_project_fields["completed_at"] = None

                            backend.update_project_details(project.id, updated_project_fields)
                            
                            # Atualizar proposta se houver
                            if proposal:
                                updated_proposal_fields = {
                                    "title": edited_proposal_title,
                                    "problem_understanding_moai": edited_problem_understanding,
                                    "solution_proposal_moai": edited_solution_proposal,
                                    "scope_moai": edited_scope,
                                    "technologies_suggested_moai": edited_technologies,
                                    "estimated_value_moai": edited_estimated_value_str,
                                    "estimated_time_moai": edited_estimated_time,
                                    "terms_conditions_moai": edited_terms_conditions
                                }
                                backend.update_proposal_content(proposal.id, updated_proposal_fields)
                            
                            st.success("✅ Projeto e proposta atualizados com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao salvar alterações: {e}")
            
            if proposal:
                st.markdown("--- \n _O MOAI garante que todas as revisões sejam documentadas e orquestradas._")
        else:
            st.info("🎉 Nenhum projeto encontrado.")
    st.markdown("---")


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