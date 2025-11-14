# cognitolink.py
import streamlit as st
import datetime
import random
import pandas as pd
import plotly.express as px
from typing import List, Dict, Any, Optional
import json # Import for JSON parsing from DB

# Importa a classe SynapseForgeBackend corretamente
from synapse_forge_backend import SynapseForgeBackend

# --- Inicializa o backend (Singleton) ---
backend = SynapseForgeBackend()

# --- Configuração da Página ---
st.set_page_config(
    page_title="CognitoLink - Synapse Forge",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Inicializa o estado da aplicação (session_state) ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = "dashboard"
if 'last_chat_message_time' not in st.session_state:
    st.session_state.last_chat_message_time = datetime.datetime.now()


# --- Funções para Renderizar as Páginas ---

def navigate_to(page_name: str):
    st.session_state.current_page = page_name
    st.rerun() # Force rerun to navigate

def dashboard_page():
    st.header("✨ Dashboard Executivo")
    st.markdown("""
    Visão de alto nível de projetos, KPIs, e o status geral da Synapse Forge,
    tudo atualizado em tempo real pelo MOAI.
    """)

    st.subheader("Visão Geral de Operações:")
    summary = backend.get_dashboard_summary()

    total_proposals = summary.get('total_proposals', 0)
    pending_proposals = summary.get('pending_proposals', 0)
    approved_proposals = summary.get('approved_proposals', 0)
    rejected_proposals = summary.get('rejected_proposals', 0)
    total_projects = summary.get('total_projects', 0)
    active_projects = summary.get('active_projects', 0)
    completed_projects = summary.get('completed_projects', 0)
    total_estimated_value_approved_proposals = summary.get('total_estimated_value_approved_proposals', 0.0)

    # Agentes em Atividade
    agents_in_activity_list = backend.get_agents_in_activity()
    num_agents_in_activity = len(agents_in_activity_list) # Conta o número de agentes

    # Saúde da Infraestrutura
    saude_infraestrutura_data = backend.get_infrastructure_health()
    overall_health_status = saude_infraestrutura_data.get("overall_status", "Desconhecido")
    health_score = 0
    if overall_health_status == "Operacional":
        health_score = 3
    elif overall_health_status == "Atenção":
        health_score = 2
    elif overall_health_status == "Crítico":
        health_score = 1
    
    # Eventos de Log do MOAI
    moai_log_events_counts = backend.get_moai_log_events_count()
    total_moai_log_events = sum(moai_log_events_counts.values()) if moai_log_events_counts else 0

    # AMS Summary
    ams_summary = backend.get_monitoring_summary()
    overall_system_status_ams = ams_summary.get("overall_system_status", "N/A")
    total_recent_alerts_ams = ams_summary.get("total_recent_alerts", 0)

    # Exibindo as métricas
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(label="Total Propostas", value=f"{total_proposals}")
    with col2:
        st.metric(label="Propostas Pendentes", value=f"{pending_proposals}")
    with col3:
        st.metric(label="Propostas Aprovadas", value=f"{approved_proposals}")
    with col4:
        st.metric(label="Total Projetos", value=f"{total_projects}")
    with col5:
        st.metric(label="Projetos Ativos", value=f"{active_projects}")
    
    col6, col7, col8, col9, col10 = st.columns(5)
    with col6:
        st.metric(label="Projetos Concluídos", value=f"{completed_projects}")
    with col7:
        st.metric(label="Agentes em Atividade", value=f"{num_agents_in_activity}")
    with col8:
        st.metric(label=f"Saúde da Infraestrutura: {overall_health_status}", value=health_score, delta="0.1%")
    with col9:
        st.metric(label="Eventos MOAI Log", value=f"{total_moai_log_events}")
    with col10:
        estimated_value_str = f"R$ {total_estimated_value_approved_proposals:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        st.metric(label="Valor Estimado Aprovado", value=estimated_value_str)

    # Métricas do AMS
    st.markdown("---")
    col_ams1, col_ams2, col_ams3 = st.columns(3)
    with col_ams1:
        st.metric(label=f"Status Geral do Sistema (AMS)", value=overall_system_status_ams)
    with col_ams2:
        st.metric(label="Total Alertas Recentes", value=f"{total_recent_alerts_ams}")
    with col_ams3:
        critical_incidents_24h_val = ams_summary.get("critical_incidents_24h", 0) 
        st.metric(label="Incidentes Críticos (24h)", value=f"{critical_incidents_24h_val}")

    # Exibição detalhada para Saúde da Infraestrutura (em expander)
    with st.expander("Detalhes da Saúde da Infraestrutura"):
        components = saude_infraestrutura_data.get("components", {})
        if components:
            for component_name, details in components.items():
                st.write(f"**{component_name.capitalize()}**: {details['status']} - {details['message']} (Último log: {details['last_log_time']})")
        else:
            st.write("Nenhum detalhe de componente de infraestrutura disponível.")

    # Exibição detalhada para Agentes em Atividade (em expander)
    with st.expander("Detalhes de Agentes em Atividade"):
        if agents_in_activity_list:
            df_agents = pd.DataFrame(agents_in_activity_list)
            st.table(df_agents)
        else:
            st.write("Nenhum agente em atividade registrado.")

    # Exibição detalhada para Contagem de Eventos MOAI por Tipo (em expander)
    with st.expander("Contagem de Eventos MOAI por Tipo"):
        if moai_log_events_counts:
            df_log_events = pd.DataFrame(list(moai_log_events_counts.items()), columns=['Tipo de Evento', 'Contagem'])
            st.table(df_log_events)
        else:
            st.write("Nenhum evento MOAI log registrado.")

    # Expander do AMS
    with st.expander("Detalhes de Monitoramento e Suporte (AMS)"):
        st.write(f"**Status Geral do Sistema:** {ams_summary.get('overall_system_status', 'N/A')}")
        st.write(f"**Total de Monitores Ativos:** {ams_summary.get('total_active_monitors', 'N/A')}")
        st.write(f"**Total de Alertas Recentes:** {ams_summary.get('total_recent_alerts', 0)}")
        st.write(f"**Incidentes Críticos (24h):** {ams_summary.get('critical_incidents_24h', 0)}")
        st.write(f"**Último Resumo Geral:** {ams_summary.get('last_overall_summary', 'N/A')}")
        
        st.markdown("---")
        st.subheader("Visualização por Projeto (Exemplo):")
        all_projects = backend.get_projects()
        if all_projects:
            project_options_display = {f"{p.project_id[:8]}... - {p.name}": p.project_id for p in all_projects}
            selected_project_display_ams = st.selectbox(
                "Selecione um Projeto para detalhes de monitoramento:", 
                list(project_options_display.keys()), 
                key="ams_proj_select"
            )
            selected_project_id_ams = project_options_display.get(selected_project_display_ams)

            if selected_project_id_ams:
                project_monitoring_report = backend.get_monitoring_summary(project_id=selected_project_id_ams)
                st.write(f"**Status Geral:** {project_monitoring_report['overall_status']}")
                st.write(f"**Disponibilidade (24h):** {project_monitoring_report['uptime_percentage_24h']}%")
                st.write(f"**Tempo de Resposta Médio:** {project_monitoring_report['response_time_ms']} ms")
                st.write(f"**Usuários Ativos (Simulado):** {project_monitoring_report['active_users']}")
                st.write(f"**Alertas Recentes:**")
                if project_monitoring_report['recent_alerts']:
                    for alert in project_monitoring_report['recent_alerts']:
                        st.warning(f"- {alert}")
                else:
                    st.info("- Nenhum alerta recente.")
                st.write(f"**Última Verificação:** {project_monitoring_report['last_checked']}")
        else:
            st.info("Nenhum projeto encontrado para detalhes de monitoramento.")

    st.subheader("Alertas e Notificações:")
    if pending_proposals > 0:
        st.warning(f"Você tem {pending_proposals} proposta(s) pendente(s) de aprovação na Central de Aprovações.")
    else:
        st.info("Nenhum alerta crítico ou aprovação pendente no momento.")

    st.markdown("---")

    st.subheader("Visualização Detalhada")

    # Exemplo de gráfico de propostas por status
    proposal_status_data = {
        'Status': ['Pendentes', 'Aprovadas', 'Rejeitadas'],
        'Contagem': [pending_proposals, approved_proposals, rejected_proposals]
    }
    df_proposal_status = pd.DataFrame(proposal_status_data)
    if not df_proposal_status.empty:
        fig_proposals = px.pie(df_proposal_status, values='Contagem', names='Status', 
                               title='Distribuição de Propostas por Status',
                               color_discrete_map={'Pendentes': 'orange', 'Aprovadas': 'green', 'Rejeitadas': 'red'})
        st.plotly_chart(fig_proposals, use_container_width=True)
    else:
        st.info("Não há dados de propostas para exibir.")

    # Exemplo de gráfico de projetos por status
    project_status_data = {
        'Status': ['Ativos', 'Concluídos'],
        'Contagem': [active_projects, completed_projects]
    }
    df_project_status = pd.DataFrame(project_status_data)
    if not df_project_status.empty:
        fig_projects = px.bar(df_project_status, x='Status', y='Contagem', 
                            title='Distribuição de Projetos por Status',
                            color='Status',
                            color_discrete_map={'Ativos': 'blue', 'Concluídos': 'green'})
        st.plotly_chart(fig_projects, use_container_width=True)
    else:
        st.info("Não há dados de projetos para exibir.")

    st.markdown("--- \n _As cores desta interface estão sendo aplicadas conforme o seu `config.toml` (Primary Color: `#1081BA`, Background: `#16171C`, Text: `#AFB1B0`)._")

def requirements_entry_page():
    st.header("📝 Módulo de Entrada de Requisitos")
    st.markdown("""
    Utilize este formulário para traduzir as necessidades do cliente em requisitos claros.
    O MOAI processará essas informações para iniciar o ciclo de vida do projeto.
    """)

    with st.form("form_requisitos_projeto", clear_on_submit=True):
        st.subheader("Detalhes do Novo Projeto")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            nome_projeto = st.text_input("Nome do Projeto", placeholder="Ex: Sistema de Gestão de Clientes v2")
        with col_r2:
            nome_cliente = st.text_input("Nome do Cliente", placeholder="Ex: Empresa XYZ")

        problema_negocio = st.text_area(
            "Qual o problema ou desafio de negócio que o cliente busca resolver?",
            height=100,
            placeholder="Descreva o cenário atual do cliente e o que ele precisa superar."
        )
        objetivos_projeto = st.text_area(
            "Quais são os principais objetivos da solução?",
            height=70,
            placeholder="Ex: Reduzir custos operacionais em X%, aumentar a satisfação do cliente em Y%."
        )
        funcionalidades_esperadas = st.text_area(
            "Liste as funcionalidades esperadas da solução (se houver detalhes prévios)",
            height=100,
            placeholder="Ex: Módulo de cadastro de usuários, integração com API A, dashboard de vendas."
        )
        restricoes = st.text_area(
            "Existem restrições importantes (orçamento, prazo, tecnologias, compliance)?",
            height=70,
            placeholder=r"Ex: Orçamento de R$X, prazo de 3 meses, deve ser em Python/Django."
        )
        publico_alvo = st.text_input("Público-alvo / Usuários Finais", placeholder="Ex: Equipe de vendas, clientes finais.")

        submitted = st.form_submit_button("Enviar Requisitos para MOAI")
        if submitted:
            if nome_projeto and nome_cliente and problema_negocio and objetivos_projeto:
                req_data = {
                    "nome_projeto": nome_projeto,
                    "nome_cliente": nome_cliente,
                    "problema_negocio": problema_negocio,
                    "objetivos_projeto": objetivos_projeto,
                    "funcionalidades_esperadas": funcionalidades_esperadas,
                    "restricoes": restricoes,
                    "publico_alvo": publico_alvo
                }
                # PONTO DE INTEGRAÇÃO REAL: Envio ao MOAI (backend)
                new_proposal = backend.create_proposal(req_data)

                st.success(f"Requisitos do projeto '{nome_projeto}' para '{nome_cliente}' enviados com sucesso para o MOAI para análise!")
                st.info(f"Uma proposta comercial (rascunho: {new_proposal.id[:8]}...) foi gerada e está aguardando sua aprovação na 'Central de Aprovações'.")
                navigate_to("aprovacoes") # Use navigate_to
            else:
                st.error("Por favor, preencha os campos obrigatórios (Nome do Projeto, Cliente, Problema e Objetivos) para que o MOAI possa analisar.")
    st.markdown("--- \n _O MOAI garantirá a resiliência e a evolução contínua da Synapse Forge._")

def approvals_center_page():
    st.header("✅ Central de Aprovações")
    st.markdown("""
    Sua área para revisar e fornecer a aprovação final para propostas, arquiteturas,
    roadmaps, estratégias de infraestrutura e backup geradas pelo MOAI e Agentes.
    """)

    pending_proposals = backend.get_proposals(status="pending")
    approved_proposals = backend.get_proposals(status="approved")
    rejected_proposals = backend.get_proposals(status="rejected")

    st.subheader(f"Propostas Pendentes de Aprovação ({len(pending_proposals)})")
    if not pending_proposals:
        st.warning("Nenhuma proposta ou item pendente de aprovação no momento. Tudo sob controle!")
    else:
        for proposal in pending_proposals:
            edit_mode_key = f"edit_mode_proposal_{proposal.id}"
            if edit_mode_key not in st.session_state:
                st.session_state[edit_mode_key] = False

            with st.expander(f"🔔 PROPOSTA PENDENTE: ID {proposal.id[:8]}... - {proposal.title}"):
                st.write(f"**Gerado em:** {proposal.submitted_at.strftime('%d/%m/%Y %H:%M:%S')}")
                st.write(f"**Cliente:** {proposal.requirements.get('nome_cliente', 'Não informado')}")
                st.markdown(f"**Resumo:** {proposal.description}")
                st.markdown("---")

                if st.session_state[edit_mode_key]:
                    st.subheader("Modo de Edição da Proposta")
                    with st.form(key=f"edit_form_{proposal.id}"):
                        edited_title = st.text_input("Título da Proposta", value=proposal.title, key=f"edit_title_{proposal.id}")
                        edited_description = st.text_area("Resumo da Proposta", value=proposal.description, height=70, key=f"edit_desc_{proposal.id}")
                        edited_problem_understanding = st.text_area("1. Análise de Requisitos (ARA)", value=proposal.problem_understanding_moai, height=150, key=f"edit_ara_{proposal.id}")
                        edited_solution_proposal = st.text_area("2. Design de Solução (AAD)", value=proposal.solution_proposal_moai, height=150, key=f"edit_aad_{proposal.id}")
                        edited_scope = st.text_area("3. Escopo Detalhado (AAD)", value=proposal.scope_moai, height=150, key=f"edit_scope_{proposal.id}")
                        edited_technologies = st.text_area("4. Tecnologias Sugeridas (AAD/MOAI)", value=proposal.technologies_suggested_moai, height=100, key=f"edit_tech_{proposal.id}")
                        edited_estimated_value = st.text_input("5. Valor Estimado", value=proposal.estimated_value_moai, key=f"edit_value_{proposal.id}")
                        edited_estimated_time = st.text_input("5. Prazo Estimado", value=proposal.estimated_time_moai, key=f"edit_time_{proposal.id}")
                        edited_terms_conditions = st.text_area("6. Termos e Condições (MOAI)", value=proposal.terms_conditions_moai, height=150, key=f"edit_terms_{proposal.id}")

                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 Salvar Alterações", key=f"save_edit_{proposal.id}"):
                                updated_fields = {
                                    "title": edited_title,
                                    "description": edited_description,
                                    "problem_understanding_moai": edited_problem_understanding,
                                    "solution_proposal_moai": edited_solution_proposal,
                                    "scope_moai": edited_scope,
                                    "technologies_suggested_moai": edited_technologies,
                                    "estimated_value_moai": edited_estimated_value,
                                    "estimated_time_moai": edited_estimated_time,
                                    "terms_conditions_moai": edited_terms_conditions
                                }
                                backend.update_proposal_content(proposal.id, updated_fields)
                                st.session_state[edit_mode_key] = False
                                st.success(f"Proposta {proposal.id[:8]}... atualizada com sucesso!")
                                st.rerun()
                        with col_cancel:
                            if st.form_submit_button("❌ Cancelar Edição", key=f"cancel_edit_{proposal.id}"):
                                st.session_state[edit_mode_key] = False
                                st.info("Edição cancelada.")
                                st.rerun()
                else: # Modo de visualização
                    st.subheader("1. Análise de Requisitos (ARA):")
                    st.write(proposal.problem_understanding_moai)
                    
                    st.subheader("2. Design de Solução (AAD):")
                    st.write(proposal.solution_proposal_moai)

                    st.subheader("3. Escopo Detalhado (AAD):")
                    st.markdown(proposal.scope_moai)

                    st.subheader("4. Tecnologias Sugeridas (AAD/MOAI):")
                    st.markdown(proposal.technologies_suggested_moai)

                    st.subheader("5. Estimativas e Recursos (AGP):")
                    st.write(f"**Valor Estimado:** {proposal.estimated_value_moai}")
                    st.write(f"**Prazo Estimado:** {proposal.estimated_time_moai}")
                    
                    st.subheader("6. Termos e Condições (MOAI):\n")
                    st.markdown(proposal.terms_conditions_moai)

                    st.markdown("---")
                    st.subheader("Requisitos Base do Cliente (Originais):")
                    st.json(proposal.requirements)

                    st.subheader("Análise do MOAI (Sugestão de Ação):")
                    st.info("O MOAI recomenda a aprovação desta proposta, pois alinha-se com os objetivos do cliente e as capacidades da Synapse Forge, com margem de lucro saudável e riscos gerenciados.")

                    # Padronização de botões usando st.columns
                    col_aprv1, col_aprv2, col_edit, col_delete = st.columns(4)
                    with col_aprv1:
                        if st.button("👍 Aprovar", key=f"aprv_{proposal.id}", use_container_width=True): # Botão padronizado
                            backend.update_proposal_status(proposal.id, "approved")
                            st.success(f"Proposta '{proposal.id[:8]}...' aprovada! MOAI iniciará o provisionamento do ambiente e a distribuição de tarefas.")
                            st.rerun()
                    with col_aprv2:
                        if st.button("🚫 Rejeitar", key=f"rej_{proposal.id}", use_container_width=True): # Botão padronizado
                            backend.update_proposal_status(proposal.id, "rejected")
                            st.warning(f"Proposta '{proposal.id[:8]}...' rejeitada. Favor fornecer feedback ao MOAI para ajustes e reavaliação.")
                            st.rerun()
                    with col_edit:
                        if st.button("✏️ Editar", key=f"edit_btn_{proposal.id}", use_container_width=True): # Botão padronizado
                            st.session_state[edit_mode_key] = True
                            st.rerun()
                    with col_delete: # Botão de exclusão adicionado
                        if st.button("🗑️ Excluir", key=f"delete_btn_{proposal.id}", help="Excluirá a proposta e todos os dados relacionados (IRREVERSÍVEL).", use_container_width=True): # Botão padronizado
                            # Usar uma confirmação em uma nova coluna ou pop-up
                            st.warning(f"Tem certeza que deseja excluir a Proposta {proposal.id[:8]}... e *todos* os seus dados relacionados (projeto, código, relatórios, documentação)? Esta ação é irreversível e permanente.")
                            if st.button(f"Confirmar Exclusão de {proposal.id[:8]}...", key=f"confirm_delete_{proposal.id}", type="danger", use_container_width=True): # Botão padronizado
                                with st.spinner(f"Excluindo proposta {proposal.id[:8]}... e dados relacionados..."):
                                    if backend.db_manager.delete_proposal_and_related_data(proposal.id):
                                        st.success(f"Proposta {proposal.id[:8]}... e todos os dados relacionados excluídos com sucesso.")
                                        st.rerun()
                                    else:
                                        st.error(f"Falha ao excluir a proposta {proposal.id[:8]}.... Verifique os logs.")

    # Histórico de propostas aprovadas e rejeitadas
    if approved_proposals:
        st.subheader("Histórico de Propostas Aprovadas")
        for proposal in approved_proposals:
            st.success(f"**ID {proposal.id[:8]}... - {proposal.title}** (Aprovada em {proposal.submitted_at.strftime('%d/%m/%Y %H:%M:%S')})")

    if rejected_proposals:
        st.subheader("Histórico de Propostas Rejeitadas")
        for proposal in rejected_proposals:
            st.error(f"**ID {proposal.id[:8]}... - {proposal.title}** (Rejeitada em {proposal.submitted_at.strftime('%d/%m/%Y %H:%M:%S')})")
    st.markdown("--- \n _Sua validação e aprovação são essenciais para a execução do plano._")

def project_timeline_page():
    st.header("⏳ Linha do Tempo Dinâmica do Projeto")
    st.markdown("""
    Visualização do progresso dos projetos, marcos importantes e desvios.
    Permite acompanhar o status em tempo real, orquestrado pelo AGP e MOAI.
    """)

    all_projects = backend.get_projects()
    active_projects = [p for p in all_projects if p.status == "active"]

    if not active_projects:
        st.info("Nenhum projeto ativo para exibir na linha do tempo. Aprove um projeto na Central de Aprovações!")
    else:
        st.subheader("Projetos Ativos:")
        for project in active_projects:
            st.markdown(f"### Projeto: {project.name} - {project.client_name} ({project.project_id[:8]}...)")
            st.progress(project.progress / 100, text=f"Progresso Geral: {project.progress}%")
            
            phases_data = backend.get_project_phases_status(project.project_id)
            if phases_data.get("error"):
                st.error(f"Erro ao obter fases do projeto: {phases_data['error']}")
            else:
                st.write("**Fases Atuais:**")
                
                next_milestone = "N/A"
                for phase in phases_data["phases"]:
                    if phase["status"] == "Em Andamento":
                        next_milestone = f"{phase['name']}"
                        break
                    elif phase["status"] == "Pendente":
                        next_milestone = f"{phase['name']}"
                        break
                st.info(f"**Próximo Marco:** {next_milestone} (Data Estimada: {datetime.date.today() + datetime.timedelta(days=random.randint(5,15))})")

                num_cols = 3
                cols = st.columns(num_cols)
                for i, phase in enumerate(phases_data["phases"]):
                    with cols[i % num_cols]:
                        st.write(f"{phase['name']}: {phase['icon']} {phase['status']}")

            st.markdown("--- \n _Detalhes do progresso e interdependências são monitorados pelo AGP._")

def detailed_reports_page():
    st.header("📊 Relatórios Detalhados")
    st.markdown("""
    Acesso a relatórios completos sobre desempenho de agentes, uso de recursos,
    qualidade, segurança, comerciais, e status de infraestrutura/backups.
    """)

    st.subheader("Selecione o Tipo de Relatório:")
    report_type = st.selectbox(
        "",
        ["Desempenho de Agentes", "Uso de Recursos", "Qualidade e Testes", "Segurança e Auditoria", "Relatórios Comerciais", "Status de Backup e Infraestrutura", "Logs de Orquestração MOAI"]
    )

    if report_type == "Desempenho de Agentes":
        st.info("Relatório do MOAI: Visão detalhada da eficiência e produtividade de cada Agente de IA.")
        st.write("**Exemplo:**")
        st.table(backend.get_agents_in_activity())
    elif report_type == "Uso de Recursos":
        st.info("Relatório do MOAI: Monitoramento de recursos de computação, armazenamento e licenças.")
        st.write("**Exemplo:**")
        data_res = pd.DataFrame({
            "Mês": ["Jan", "Fev", "Mar"],
            "Uso CPU (%)": [random.randint(60,90), random.randint(60,90), random.randint(60,90)],
            "Uso RAM (%)": [random.randint(70,95), random.randint(70,95), random.randint(70,95)]
        })
        st.line_chart(data_res.set_index("Mês"))
    elif report_type == "Qualidade e Testes":
        st.info("Relatório do AQT: Métricas de cobertura de testes, bugs encontrados e tempo de resolução.")
        quality_report = backend.get_quality_tests_report()

        st.write(f"**Status Geral:** {quality_report['status_geral']}")
        st.write(f"**Bugs Abertos (Total):** {quality_report['bugs_abertos_total']}")
        st.write(f"**Cobertura Média de Código:** {quality_report['cobertura_media_codigo']}")
        st.write(f"**Risco de Qualidade:** {quality_report['risco_qualidade']}")
        st.write(f"**Última Atualização:** {quality_report['last_update']}")

        st.markdown("---")
        st.subheader("Visualização por Projeto (Exemplo):")
        
        all_projects = backend.get_projects()
        if all_projects:
            project_options_display = {f"{p.project_id[:8]}... - {p.name}": p.project_id for p in all_projects}
            selected_project_display_aqt = st.selectbox(
                "Selecione um Projeto para relatório detalhado:", 
                list(project_options_display.keys()), 
                key="aqt_proj_select"
            )
            selected_project_id_aqt = project_options_display.get(selected_project_display_aqt)

            if selected_project_id_aqt:
                project_quality_report = backend.get_quality_tests_report(project_id=selected_project_id_aqt)
                st.write(f"**Status do Relatório:** {project_quality_report['status']}")
                st.write(f"**Total de Testes:** {project_quality_report['total_tests']}")
                st.write(f"**Testes Aprovados:** {project_quality_report['passed_tests']}")
                st.write(f"**Testes Falhos:** {project_quality_report['failed_tests']}")
                st.write(f"**Cobertura de Código:** {project_quality_report['code_coverage']}")
                st.write(f"**Estabilidade:** {project_quality_report['stability']}")
                st.write(f"**Tempo Médio de Execução:** {project_quality_report['average_test_execution_time_seconds']} segundos")
                st.write("**Recomendações:**")
                for rec in project_quality_report['recommendations']:
                    st.markdown(f"- {rec}")
                st.write(f"**Última Atualização:** {project_quality_report['last_update']}")
                if 'details_llm' in project_quality_report:
                    with st.expander("Ver Detalhes Gerados pelo LLM"):
                        st.markdown(project_quality_report['details_llm'])
        else:
            st.info("Nenhum projeto encontrado para gerar relatório detalhado de qualidade.")
    elif report_type == "Segurança e Auditoria":
        st.info("Relatório do ASE: Avaliação de vulnerabilidades, auditorias de conformidade e incidentes de segurança.")
        security_report = backend.get_security_audit_report()

        st.write(f"**Status Geral:** {security_report['status_geral']}")
        st.write(f"**Vulnerabilidades Críticas (Total):** {security_report['vulnerabilidades_criticas_total']}")
        st.write(f"**Incidentes Recentes:** {security_report['incidentes_recentes']}")
        st.write(f"**Status de Conformidade:** {security_report['conformidade']}")
        st.write(f"**Última Atualização:** {security_report['last_update']}")

        st.markdown("---")
        st.subheader("Visualização por Projeto (Exemplo):")

        all_projects = backend.get_projects()
        if all_projects:
            project_options_display = {f"{p.project_id[:8]}... - {p.name}": p.project_id for p in all_projects}
            selected_project_display_ase = st.selectbox(
                "Selecione um Projeto para relatório detalhado:", 
                list(project_options_display.keys()), 
                key="ase_proj_select"
            )
            selected_project_id_ase = project_options_display.get(selected_project_display_ase)

            if selected_project_id_ase:
                project_security_report = backend.get_security_audit_report(project_id=selected_project_id_ase)
                st.write(f"**Status da Auditoria:** {project_security_report['status']}")
                st.write(f"**Risco Geral:** {project_security_report['overall_risk']}")
                st.write(f"**Vulnerabilidades Encontradas:**")
                st.write(f"  - Críticas: {project_security_report['vulnerabilities']['critical']}")
                st.write(f"  - Altas: {project_security_report['vulnerabilities']['high']}")
                st.write(f"  - Médias: {project_security_report['vulnerabilities']['medium']}")
                st.write(f"  - Baixas: {project_security_report['vulnerabilities']['low']}")
                st.write(f"**Status de Conformidade:** {project_security_report['compliance_status']}")
                st.write(f"**Última Varredura:** {project_security_report['last_scan']}")
                st.write("**Recomendações:**")
                for rec in project_security_report['recommendations']:
                    st.markdown(f"- {rec}")
                if 'details_llm' in project_security_report:
                    with st.expander("Ver Detalhes Gerados pelo LLM"):
                        st.markdown(project_security_report['details_llm'])
        else:
            st.info("Nenhum projeto encontrado para gerar relatório detalhado de segurança.")
    elif report_type == "Relatórios Comerciais":
        st.info("Relatório do ANP: Análise de propostas geradas, taxas de conversão e receita projetada.")
        commercial_data = backend.get_commercial_report()

        st.write(f"**Propostas Geradas:** {commercial_data.get('propostas_geradas', 0)}")
        st.write(f"**Propostas Aprovadas:** {commercial_data.get('propostas_aprovadas', 0)}")
        st.write(f"**Propostas Rejeitadas:** {commercial_data.get('propostas_rejeitadas', 0)}")
        st.write(f"**Taxa de Aprovação:** {commercial_data.get('taxa_aprovacao', 0):.2f}%")
        estimated_total_value_str = f"R$ {commercial_data.get('valor_total_gerado', 0.0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        estimated_approved_value_str = f"R$ {commercial_data.get('valor_total_aprovado', 0.0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        st.write(f"**Valor Total Estimado Gerado:** {estimated_total_value_str}")
        st.write(f"**Valor Total Estimado Aprovado:** {estimated_approved_value_str}")
        st.write(f"**Última Atualização:** {commercial_data.get('last_update', 'N/A')}")
    elif report_type == "Status de Backup e Infraestrutura":
        st.info("Relatório do MOAI/AID: Saúde dos sistemas, logs de infraestrutura e verificação de backups.")
        
        infra_health = backend.get_infrastructure_health()
        st.subheader("Saúde da Infraestrutura Geral:")
        st.json(infra_health)

        st.subheader("Status do Último Backup (Simulado):")
        backup_infra_status = {
            'status_backup_recente': random.choice(["Sucesso", "Sucesso com Avisos", "Falha"]),
            'timestamp_backup': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'politicas': ["Diário, 7 dias retenção", "Semanal, 4 semanas retenção"]
        }
        if backup_infra_status.get('status_backup_recente') == "Sucesso":
            st.success(f"Último backup completo em {backup_infra_status.get('timestamp_backup')} - Status: Sucesso ✅")
        elif backup_infra_status.get('status_backup_recente') == "Sucesso com Avisos":
            st.warning(f"Último backup completo em {backup_infra_status.get('timestamp_backup')} - Status: Sucesso com Avisos ⚠️")
        else:
            st.error(f"Último backup completo em {backup_infra_status.get('timestamp_backup')} - Status: Falha ❌")
        
        st.subheader("Políticas de Backup:")
        for policy in backup_infra_status.get('politicas', []):
            st.markdown(policy)
    elif report_type == "Logs de Orquestração MOAI":
        st.info("Este relatório detalha todas as ações e decisões tomadas pelo MOAI, incluindo a orquestração de agentes e interação com o sistema.")
        moai_logs = backend.db_manager.get_all_moai_logs()
        if not moai_logs:
            st.info("Nenhum log de orquestração do MOAI encontrado ainda.")
        else:
            st.subheader("Histórico de Logs do MOAI:")
            for log_entry in moai_logs:
                with st.expander(f"[{log_entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] **{log_entry.event_type.replace('_', ' ').title()}**"):
                    try:
                        details_json = json.loads(log_entry.details)
                        st.json(details_json)
                    except (json.JSONDecodeError, TypeError):
                        st.write(log_entry.details if log_entry.details else "Nenhum detalhe adicional.")
    st.markdown("--- \n _Relatórios acionáveis para guiar suas decisões estratégicas._")

def moai_communication_page():
    st.header("💬 Comunicação Bidirecional com MOAI")
    st.markdown("""
    Interface de chat/comando para perguntas diretas, atualizações, alertas de decisões cruciais
    ou insights do MOAI. Seu canal direto com o cérebro da Synapse Forge.
    """)

    chat_history = backend.get_chat_history()
    for message_obj in chat_history:
        with st.chat_message(message_obj.sender):
            st.markdown(message_obj.message)

    if prompt := st.chat_input("Fale com o MOAI..."):
        backend.add_chat_message("user", prompt)
        
        with st.spinner("MOAI está processando sua solicitação..."):
            moai_raw_response = backend.process_moai_chat(prompt)
            backend.add_chat_message("ai", moai_raw_response)
        
        st.rerun()
    st.markdown("--- \n _O MOAI sempre pronto para responder e auxiliar._")

def code_viewer_page():
    st.header("💻 Visualizador de Código Gerado")
    st.markdown("""
    Inspecione o código-fonte gerado pelos Agentes de Desenvolvimento (ADE-X).
    Garanta a qualidade e a conformidade com os padrões internos.
    """)

    all_projects = backend.get_projects()
    if not all_projects:
        st.info("Nenhum projeto aprovado para visualizar o código. Aprovando uma proposta na Central de Aprovações, o ADE-X começará a gerar o código.")
    else:
        project_options_display = {f"{p.project_id[:8]}... - {p.name}": p.project_id for p in all_projects}
        
        selected_project_display = st.selectbox(
            "Selecione um Projeto para Visualizar o Código:", 
            list(project_options_display.keys()), 
            key="code_viewer_select"
        )
        
        selected_project_id = project_options_display.get(selected_project_display)

        if selected_project_id:
            generated_codes = backend.get_generated_code_for_project(selected_project_id)
            
            if not generated_codes:
                # Botão para gerar código se não houver nenhum
                if st.button(f"Gerar Código Exemplo para o Projeto {selected_project_id[:8]}...", key=f"generate_code_btn_{selected_project_id}", use_container_width=True): # Botão padronizado
                    with st.spinner("Gerando código exemplo..."):
                        # Simula a geração de um arquivo Python básico
                        backend.generate_code_for_project(selected_project_id, "main.py", "Python", "Código inicial do projeto.")
                        st.success("Código exemplo gerado! Recarregando...")
                        st.rerun()
                st.info("Nenhum código gerado para este projeto ainda.")
            else:
                project_name_display = next((p.name for p in all_projects if p.project_id == selected_project_id), "Nome Desconhecido")
                st.subheader(f"Código Gerado para {project_name_display} ({selected_project_id[:8]}...)")
                st.info("Conteúdo do código gerado pelos ADE-X. Permite revisão e auditoria.")

                code_files = {gc.filename: gc for gc in generated_codes}
                selected_filename = st.selectbox("Selecione o arquivo de código:", list(code_files.keys()))

                if selected_filename:
                    selected_code = code_files[selected_filename]
                    st.code(selected_code.content, language=selected_code.language)
                    st.download_button(label=f"Baixar {selected_filename}", data=selected_code.content.encode('utf-8'), file_name=selected_filename, use_container_width=True) # Botão padronizado
    st.markdown("--- \n _A qualidade do código é garantida pelos padrões da Synapse Forge._")

def infra_backup_management_page():
    st.header("⚙️ Gestão de Infraestrutura e Backup")
    st.markdown("""
    Gerencie o layout do ambiente (pastas, arquivos), visualize o status dos backups,
    programe restaurações (para testes) e revise as políticas de retenção,
    tudo orquestrado pelo MOAI e AID.
    """)

    all_projects = backend.get_projects()
    if not all_projects:
        st.info("Nenhum ambiente de projeto para gerenciar. Aprovando uma proposta, o AID provisionará o ambiente.")
    else:
        project_options_display = {f"{p.project_id[:8]}... - {p.name}": p.project_id for p in all_projects}
        selected_project_display_infra = st.selectbox(
            "Selecione um Projeto para Gestão:", 
            list(project_options_display.keys()), 
            key="infra_proj_select"
        )
        
        selected_project_id_infra = project_options_display.get(selected_project_display_infra)

        if selected_project_id_infra:
            project_name_display = next((p.name for p in all_projects if p.project_id == selected_project_id_infra), "Nome Desconhecido")
            st.write(f"### Ambiente do Projeto: {project_name_display} ({selected_project_id_infra[:8]}...)")
            
            infra_status = backend.get_infra_status(selected_project_id_infra)
            if infra_status.get("error"):
                st.error(infra_status["error"])
            else:
                st.json(infra_status)

            st.subheader("Status do Último Backup (Simulado):")
            backup_infra_status = {
                'status_backup_recente': random.choice(["Sucesso", "Sucesso com Avisos", "Falha"]),
                'timestamp_backup': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'politicas': ["Diário, 7 dias retenção", "Semanal, 4 semanas retenção"]
            }
            if backup_infra_status.get('status_backup_recente') == "Sucesso":
                st.success(f"Último backup completo em {backup_infra_status.get('timestamp_backup')} - Status: Sucesso ✅")
            elif backup_infra_status.get('status_backup_recente') == "Sucesso com Avisos":
                st.warning(f"Último backup completo em {backup_infra_status.get('timestamp_backup')} - Status: Sucesso com Avisos ⚠️")
            else:
                st.error(f"Último backup completo em {backup_infra_status.get('timestamp_backup')} - Status: Falha ❌")
            
            st.subheader("Políticas de Backup:")
            for policy in backup_infra_status.get('politicas', []):
                st.markdown(policy)

            st.subheader("Ações:")
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("Executar Backup Manual (AID)", key="manual_backup", use_container_width=True): # Botão padronizado
                    response = backend.trigger_manual_backup(selected_project_id_infra)
                    if response["success"]:
                        st.success(response["message"])
                    else:
                        st.error(response["message"])
            with col_b2:
                if st.button("Programar Restauração para Testes (AID)", key="test_restore", use_container_width=True): # Botão padronizado
                    response = backend.schedule_test_restore(selected_project_id_infra)
                    if response["success"]:
                        st.info(response["message"])
                    else:
                        st.error(response["message"])
    st.markdown("--- \n _O AID, o braço executor do MOAI, garante a automação e segurança._")

def documentation_page():
    st.header("📚 Módulo de Documentação do Projeto")
    st.markdown("""
    Visualize a documentação técnica e de usuário gerada pelo Agente de Documentação (ADO).
    Aqui você pode inspecionar e baixar os manuais e guias do projeto.
    """)

    all_projects = backend.get_projects()
    if not all_projects:
        st.info("Nenhum projeto disponível para gerar documentação. Aprovando uma proposta, o ADO poderá começar a trabalhar.")
    else:
        project_options_display = {f"{p.project_id[:8]}... - {p.name}": p.project_id for p in all_projects}
        
        selected_project_display_doc = st.selectbox(
            "Selecione um Projeto para gerar/visualizar a documentação:", 
            list(project_options_display.keys()), 
            key="doc_proj_select"
        )
        
        selected_project_id_doc = project_options_display.get(selected_project_display_doc)

        if selected_project_id_doc:
            project_name_display = next((p.name for p in all_projects if p.project_id == selected_project_id_doc), "Nome Desconhecido")
            st.subheader(f"Documentação para {project_name_display} ({selected_project_id_doc[:8]}...)")

            existing_docs = backend.get_documentation_for_project(selected_project_id_doc)
            
            if st.button(f"Gerar/Atualizar Documentação (ADO) para {project_name_display}", key=f"generate_doc_{selected_project_id_doc}", use_container_width=True): # Botão padronizado
                with st.spinner("Gerando documentação..."):
                    doc_result = backend.generate_project_documentation(selected_project_id_doc)
                
                if doc_result["error"]:
                    st.error(f"Erro ao gerar documentação: {doc_result['error']}")
                else:
                    st.success("Nova documentação gerada com sucesso!")
                    st.rerun() # To show the new doc immediately
            
            if existing_docs:
                st.markdown("---")
                st.subheader("Documentações Existentes:")
                doc_files = {doc.filename: doc for doc in existing_docs}
                selected_doc_filename = st.selectbox("Selecione um documento:", list(doc_files.keys()), key=f"select_existing_doc_{selected_project_id_doc}")

                if selected_doc_filename:
                    selected_doc = doc_files[selected_doc_filename]
                    st.markdown(selected_doc.content)
                    st.download_button(
                        label=f"Baixar {selected_doc.filename}",
                        data=selected_doc.content.encode('utf-8'),
                        file_name=selected_doc.filename,
                        mime="text/markdown",
                        key=f"download_doc_{selected_doc.id}",
                        use_container_width=True # Botão padronizado
                    )
            else:
                st.info("Nenhuma documentação para este projeto ainda. Clique no botão acima para gerar.")

    st.markdown("--- \n _A documentação é a base do conhecimento da sua solução._")

def project_management_page():
    st.header("🚧 Gestão e Revisão de Projetos")
    st.markdown("""
    Visualize os detalhes dos projetos ativos, monitore seu progresso e, se necessário,
    revise e atualize as especificações da proposta original associada.
    """)

    all_projects = backend.get_projects()
    if not all_projects:
        st.info("Nenhum projeto encontrado. Aprove uma proposta na Central de Aprovações para iniciar um projeto.")
        return

    project_options_display = {f"{p.project_id[:8]}... - {p.name}": p.project_id for p in all_projects}
    selected_project_display = st.selectbox(
        "Selecione um Projeto para Gerenciar:",
        list(project_options_display.keys()),
        key="project_mgmt_select"
    )
    selected_project_id = project_options_display.get(selected_project_display)

    if selected_project_id:
        project = backend.get_project_by_id(selected_project_id)
        if not project:
            st.error("Projeto não encontrado.")
            return

        st.subheader(f"Detalhes do Projeto: {project.name} ({project.project_id[:8]}...)")
        st.write(f"**Cliente:** {project.client_name}")
        st.write(f"**Status:** {project.status.capitalize()}")
        st.write(f"**Progresso:** {project.progress}%")

        # --- Modo de Edição para Detalhes Básicos do Projeto ---
        st.markdown("---")
        st.subheader("Editar Detalhes Básicos do Projeto")
        edit_project_key = f"edit_project_details_{project.project_id}"
        if edit_project_key not in st.session_state:
            st.session_state[edit_project_key] = False

        if st.session_state[edit_project_key]:
            with st.form(key=f"form_edit_project_basic_{project.project_id}"):
                new_name = st.text_input("Nome do Projeto", value=project.name)
                new_client_name = st.text_input("Nome do Cliente", value=project.client_name)
                new_status = st.selectbox("Status", options=["active", "completed", "on hold", "cancelled"], index=["active", "completed", "on hold", "cancelled"].index(project.status), key=f"edit_proj_status_{project.project_id}")
                new_progress = st.slider("Progresso (%)", min_value=0, max_value=100, value=project.progress)

                col_save_proj, col_cancel_proj = st.columns(2)
                with col_save_proj:
                    if st.form_submit_button("💾 Salvar Detalhes do Projeto", key=f"save_proj_basic_{project.project_id}", use_container_width=True): # Botão padronizado
                        updated_fields = {
                            "name": new_name,
                            "client_name": new_client_name,
                            "status": new_status,
                            "progress": new_progress
                        }
                        backend.update_project_details(project.project_id, updated_fields)
                        st.session_state[edit_project_key] = False
                        st.success(f"Detalhes do projeto {project.project_id[:8]}... atualizados com sucesso!")
                        st.rerun()
                with col_cancel_proj:
                    if st.form_submit_button("❌ Cancelar Edição", key=f"cancel_proj_basic_{project.project_id}", use_container_width=True): # Botão padronizado
                        st.session_state[edit_project_key] = False
                        st.info("Edição de detalhes do projeto cancelada.")
                        st.rerun()
        else:
            if st.button("✏️ Editar Detalhes Básicos do Projeto", key=f"btn_edit_proj_basic_{project.project_id}", use_container_width=True): # Botão padronizado
                st.session_state[edit_project_key] = True
                st.rerun()

        # --- Modo de Edição para Especificações da Proposta Associada ---
        st.markdown("---")
        st.subheader("Revisar/Editar Especificações Detalhadas (da Proposta Original)")

        if project.proposal_id:
            proposal = backend.get_proposal_by_id(project.proposal_id)
            if proposal:
                edit_proposal_spec_key = f"edit_proposal_spec_{proposal.id}"
                if edit_proposal_spec_key not in st.session_state:
                    st.session_state[edit_proposal_spec_key] = False

                if st.session_state[edit_proposal_spec_key]:
                    with st.form(key=f"form_edit_proposal_spec_{proposal.id}"):
                        edited_problem_understanding = st.text_area("1. Análise de Requisitos (ARA)", value=proposal.problem_understanding_moai, height=150, key=f"edit_proj_ara_{proposal.id}")
                        edited_solution_proposal = st.text_area("2. Design de Solução (AAD)", value=proposal.solution_proposal_moai, height=150, key=f"edit_proj_aad_{proposal.id}")
                        edited_scope = st.text_area("3. Escopo Detalhado (AAD)", value=proposal.scope_moai, height=150, key=f"edit_proj_scope_{proposal.id}")
                        edited_technologies = st.text_area("4. Tecnologias Sugeridas (AAD/MOAI)", value=proposal.technologies_suggested_moai, height=100, key=f"edit_proj_tech_{proposal.id}")
                        edited_estimated_value = st.text_input("5. Valor Estimado", value=proposal.estimated_value_moai, key=f"edit_proj_value_{proposal.id}")
                        edited_estimated_time = st.text_input("5. Prazo Estimado", value=proposal.estimated_time_moai, key=f"edit_proj_time_{proposal.id}")
                        edited_terms_conditions = st.text_area("6. Termos e Condições (MOAI)", value=proposal.terms_conditions_moai, height=150, key=f"edit_proj_terms_{proposal.id}")
                        
                        col_save_prop, col_cancel_prop = st.columns(2)
                        with col_save_prop:
                            if st.form_submit_button("💾 Salvar Especificações da Proposta", key=f"save_prop_spec_{proposal.id}", use_container_width=True): # Botão padronizado
                                updated_proposal_fields = {
                                    "problem_understanding_moai": edited_problem_understanding,
                                    "solution_proposal_moai": edited_solution_proposal,
                                    "scope_moai": edited_scope,
                                    "technologies_suggested_moai": edited_technologies,
                                    "estimated_value_moai": edited_estimated_value,
                                    "estimated_time_moai": edited_estimated_time,
                                    "terms_conditions_moai": edited_terms_conditions
                                }
                                backend.update_proposal_content(proposal.id, updated_proposal_fields)
                                st.session_state[edit_proposal_spec_key] = False
                                st.success(f"Especificações da proposta {proposal.id[:8]}... (projeto {project.project_id[:8]}...) atualizadas com sucesso!")
                                st.rerun()
                        with col_cancel_prop:
                            if st.form_submit_button("❌ Cancelar Edição", key=f"cancel_prop_spec_{proposal.id}", use_container_width=True): # Botão padronizado
                                st.session_state[edit_proposal_spec_key] = False
                                st.info("Edição de especificações da proposta cancelada.")
                                st.rerun()
                else: # Modo de visualização das especificações da proposta
                    st.markdown(f"**Proposta ID Associada:** {proposal.id[:8]}...")
                    st.write(f"**Título da Proposta:** {proposal.title}")
                    st.write(f"**Resumo da Proposta:** {proposal.description}")
                    st.subheader("1. Análise de Requisitos (ARA):")
                    st.write(proposal.problem_understanding_moai)
                    st.subheader("2. Solução Proposta (AAD):")
                    st.write(proposal.solution_proposal_moai)
                    st.subheader("3. Escopo Detalhado (AAD):")
                    st.markdown(proposal.scope_moai)
                    st.subheader("4. Tecnologias Sugeridas (AAD/MOAI):")
                    st.markdown(proposal.technologies_suggested_moai)
                    st.subheader("5. Estimativas e Recursos (AGP):")
                    st.write(f"**Valor Estimado:** {proposal.estimated_value_moai}")
                    st.write(f"**Prazo Estimado:** {proposal.estimated_time_moai}")
                    st.subheader("6. Termos e Condições (MOAI):")
                    st.markdown(proposal.terms_conditions_moai)

                    if st.button("✏️ Revisar Especificações da Proposta", key=f"btn_edit_prop_spec_{proposal.id}", use_container_width=True): # Botão padronizado
                        st.session_state[edit_proposal_spec_key] = True
                        st.rerun()
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
    # Padronização de botões do sidebar com use_container_width=True
    
    if st.button("🏠 Dashboard Executivo", key="btn_dashboard", use_container_width=True):
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