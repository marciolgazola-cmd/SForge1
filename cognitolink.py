import streamlit as st
import datetime
import random
import json # Para exibir detalhes dos logs
from typing import List
from synapse_forge_backend import SynapseForgeBackend
from data_models import Requirement, GeneratedCode, MoaiLog, Proposal # Importamos MoaiLog e Proposal

# --- Inicializa o backend (Singleton) ---
backend = SynapseForgeBackend()

# --- Configuração da Página ---
st.set_page_config(
    page_title="CognitoLink - Synapse Forge",
    page_icon="🧠", # Corrigi o emoji para algo mais comum
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Inicializa o estado da aplicação (session_state) ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = "dashboard"
if 'last_chat_message_time' not in st.session_state:
    st.session_state.last_chat_message_time = datetime.datetime.now()


# --- Funções para Renderizar as Páginas ---

def dashboard_page():
    st.header("✨ Dashboard Executivo")
    st.markdown("""
    Visão de alto nível de projetos, KPIs, e o status geral da Synapse Forge,
    tudo atualizado em tempo real pelo MOAI.
    """)

    st.subheader("Visão Geral de Operações:")
    summary = backend.get_dashboard_summary()
    col1, col2, col3, col4, col5 = st.columns(5) # Adicionada uma coluna para logs do MOAI
    with col1:
        st.metric(label="Projetos Ativos", value=f"{summary['projetos_ativos']}")
    with col2:
        st.metric(label="Propostas Pendentes", value=f"{summary['pending_proposals']}")
    with col3:
        st.metric(label="Agentes em Atividade", value=f"{summary['agentes_em_atividade']}")
    with col4:
        st.metric(label="Saúde da Infraestrutura", value=summary['saude_infraestrutura'], delta="0.1%")
    with col5: # Nova métrica para eventos do MOAI
        st.metric(label="Eventos MOAI Log", value=f"{summary['eventos_moai_log']}")


    st.subheader("Alertas e Notificações:")
    # === CORREÇÃO: Utilizando 'pending_proposals' consistentemente ===
    if summary['pending_proposals'] > 0:
        st.warning(f"Você tem {summary['pending_proposals']} proposta(s) pendente(s) de aprovação na Central de Aprovações.")
    else:
        st.info("Nenhum alerta crítico ou aprovação pendente no momento.")

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
            # CORREÇÃO: Uso de raw string para evitar SyntaxWarning
            placeholder=r"Ex: Orçamento de R\$X, prazo de 3 meses, deve ser em Python/Django."
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
                # --- PONTO DE INTEGRAÇÃO REAL: Envio ao MOAI (backend) ---
                new_proposal = backend.submit_requirements_to_moai(req_data)

                st.success(f"Requisitos do projeto '{nome_projeto}' para '{nome_cliente}' enviados com sucesso para o MOAI para análise!")
                st.info(f"Uma proposta comercial (rascunho: {new_proposal.id}) foi gerada e está aguardando sua aprovação na 'Central de Aprovações'.")
                st.session_state.current_page = "aprovacoes"
                st.rerun()
            else:
                st.error("Por favor, preencha os campos obrigatórios (Nome do Projeto, Cliente, Problema e Objetivos) para que o MOAI possa analisar.")
    st.markdown("--- \n _O MOAI garantirá a resiliência e a evolução contínua da Synapse Forge._")

def approvals_center_page():
    st.header("✅ Central de Aprovações")
    st.markdown("""
    Sua área para revisar e fornecer a aprovação final para propostas, arquiteturas,
    roadmaps, estratégias de infraestrutura e backup geradas pelo MOAI e Agentes.
    """)

    # Certifique-se de que o backend tem os métodos para obter as listas
    pending_proposals = backend.get_pending_proposals_list()
    approved_proposals = backend.get_approved_proposals()
    rejected_proposals = backend.get_rejected_proposals()

    st.subheader(f"Propostas Pendentes de Aprovação ({len(pending_proposals)})")
    if not pending_proposals:
        st.warning("Nenhuma proposta ou item pendente de aprovação no momento. Tudo sob controle!")
    else:
        for i, proposal in enumerate(pending_proposals):
            with st.expander(f"🔔 PROPOSTA PENDENTE: ID {proposal.id} - {proposal.title}"):
                # --- Corrigido: Usando atributos reais da classe Proposal ---
                st.write(f"**Gerado em:** {proposal.submitted_at.strftime('%d/%m/%Y %H:%M:%S') if isinstance(proposal.submitted_at, datetime.datetime) else proposal.submitted_at}")
                st.write(f"**Cliente:** {proposal.requirements.get('nome_cliente', 'Não informado')}")
                st.markdown(f"**Resumo:** {proposal.description}")
                st.markdown("---")

                st.subheader("1. Entendimento do Problema:")
                # Corrigido: Acessando a chave 'problema_negocio' do dicionário 'requirements'
                st.write(proposal.requirements.get('problema_negocio', 'Entendimento do problema não especificado.'))

                st.subheader("2. Solução Proposta:")
                # Corrigido: Acessando a chave 'funcionalidades_esperadas' como a "solução proposta"
                st.write(proposal.requirements.get('funcionalidades_esperadas', 'Solução proposta não especificada.'))

                st.subheader("3. Escopo do Projeto:")
                # Corrigido: O escopo virá das funcionalidades esperadas, talvez separadas por linha
                funcionalidades = proposal.requirements.get('funcionalidades_esperadas', '')
                if funcionalidades:
                    for item in funcionalidades.split('\n'):
                        if item.strip():
                            st.markdown(f"- {item.strip()}")
                else:
                    st.markdown("Nenhum escopo detalhado disponível nos requisitos base.")
                
                st.subheader("4. Tecnologias Sugeridas:")
                # Corrigido: Este é um campo que o MOAI geraria. Para os requisitos base, usaremos placeholder.
                st.write("Não disponível nos requisitos base. O MOAI sugeriria aqui as tecnologias.")

                st.subheader("5. Estimativas:")
                # Corrigido: Campos que o MOAI geraria. Placeholder para os requisitos base.
                st.write(f"**Valor Estimado:** A ser estimado pelo MOAI.")
                st.write(f"**Prazo Estimado:** A ser estimado pelo MOAI.")

                st.subheader("6. Termos e Condições:")
                # Corrigido: Campos que o MOAI geraria. Placeholder para os requisitos base.
                st.write("Termos e condições padrão serão aplicados após a geração da proposta completa pelo MOAI.")

                st.markdown("---")
                st.subheader("Requisitos Base do Cliente (Originais):")
                # Corrigido: proposal.requirements JÁ É o dicionário
                st.json(proposal.requirements)

                st.subheader("Análise do MOAI (Sugestão de Ação):")
                st.info("O MOAI recomenda a aprovação desta proposta, pois alinha-se com os objetivos do cliente e as capacidades da Synapse Forge, com margem de lucro saudável e riscos gerenciados.")

                col_aprv1, col_aprv2 = st.columns(2)
                with col_aprv1:
                    # Corrigido: Usando proposal.id e chamando update_proposal_status
                    if st.button(f"👍 Aprovar Proposta {proposal.id}", key=f"aprv_{proposal.id}"):
                        backend.update_proposal_status(proposal.id, "approved")
                        st.success(f"Proposta '{proposal.id}' aprovada! MOAI iniciará o provisionamento do ambiente e a distribuição de tarefas.")
                        st.rerun()
                with col_aprv2:
                    # Corrigido: Usando proposal.id e chamando update_proposal_status
                    if st.button(f"🚫 Rejeitar Proposta {proposal.id}", key=f"rej_{proposal.id}"):
                        backend.update_proposal_status(proposal.id, "rejected")
                        st.warning(f"Proposta '{proposal.id}' rejeitada. Favor fornecer feedback ao MOAI para ajustes e reavaliação.")
                        st.rerun()

    # --- Corrigido: Histórico de propostas aprovadas e rejeitadas ---
    if approved_proposals:
        st.subheader("Histórico de Propostas Aprovadas")
        for proposal in approved_proposals:
            st.success(f"**ID {proposal.id} - {proposal.title}** (Aprovada em {proposal.submitted_at.strftime('%d/%m/%Y %H:%M:%S') if isinstance(proposal.submitted_at, datetime.datetime) else proposal.submitted_at})")

    if rejected_proposals:
        st.subheader("Histórico de Propostas Rejeitadas")
        for proposal in rejected_proposals:
            st.error(f"**ID {proposal.id} - {proposal.title}** (Rejeitada em {proposal.submitted_at.strftime('%d/%m/%Y %H:%M:%S') if isinstance(proposal.submitted_at, datetime.datetime) else proposal.submitted_at})")
    st.markdown("--- \n _Sua validação e aprovação são essenciais para a execução do plano._")

def project_timeline_page():
    st.header("⏳ Linha do Tempo Dinâmica do Projeto")
    st.markdown("""
    Visualização do progresso dos projetos, marcos importantes e desvios.
    Permite acompanhar o status em tempo real, orquestrado pelo AGP e MOAI.
    """)

    all_projects = backend.get_all_projects() # Presumindo que este método retorne uma lista de objetos com 'status', 'name', 'client_name', 'project_id', 'progress'
    active_projects = [p for p in all_projects if getattr(p, 'status', 'Unknown') == "approved"] # Alterado para "approved"

    if not active_projects:
        st.info("Nenhum projeto ativo para exibir na linha do tempo. Aprove um projeto na Central de Aprovações!")
    else:
        st.subheader("Projetos Ativos:")
        for project in active_projects:
            # Corrigido: Assumindo que project_id é um atributo direto
            st.markdown(f"### Projeto: {getattr(project, 'name', 'Nome Desconhecido')} - {getattr(project, 'client_name', 'Cliente Desconhecido')} ({getattr(project, 'project_id', 'ID Desconhecido')})")
            st.progress(getattr(project, 'progress', 0), text=f"Progresso Geral: {getattr(project, 'progress', 0)}%")
            st.info(f"**Próximo Marco:** Revisão de Arquitetura (Data Estimada: {datetime.date.today() + datetime.timedelta(days=random.randint(5,15))})")
            st.write("**Fases Atuais:**")
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1: st.write("ARA: Completo ✅")
            with col_t2: st.write(f"AAD: {random.choice(['Em Andamento ⚙️', 'Completo ✅'])}")
            with col_t3: st.write(f"ADE-X: {random.choice(['Iniciado 🚀', 'Em Desenvolvimento ��'])}")
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
        # backend.get_agent_performance_report() deve retornar um dicionário ou lista de dicionários
        # com chaves que possam ser usadas em st.table. Exemplo: [{"Agente": "Agente X", "Tarefas Concluídas": 10, "Eficiência": "95%"}]
        st.table(backend.get_agent_performance_report())
    elif report_type == "Uso de Recursos":
        st.info("Relatório do MOAI: Monitoramento de recursos de computação, armazenamento e licenças.")
        st.write("**Exemplo:**")
        # backend.get_resource_usage_report() deve retornar um DataFrame ou dicionário compatível com st.line_chart
        # Exemplo: {"Mês": ["Jan", "Fev"], "Uso CPU": [80, 85], "Uso RAM": [70, 75]}
        data = backend.get_resource_usage_report()
        st.line_chart(data, x="Mês")
    elif report_type == "Qualidade e Testes":
        st.info("Relatório do AQT: Métricas de cobertura de testes, bugs encontrados e tempo de resolução.")
        st.write("**Exemplo:**")
        # backend.get_quality_tests_report() deve retornar um DataFrame ou dicionário compatível com st.bar_chart
        # Exemplo: {"Mês": ["Jan", "Fev"], "Bugs": [5, 3], "Cobertura": [90, 92]}
        data = backend.get_quality_tests_report()
        st.bar_chart(data, x="Mês")
    elif report_type == "Segurança e Auditoria":
        st.info("Relatório do ASE: Avaliação de vulnerabilidades, auditorias de conformidade e incidentes de segurança.")
        # backend.get_security_audit_report() deve retornar uma string ou outro tipo de dado que st.warning possa exibir
        st.warning(backend.get_security_audit_report())
    elif report_type == "Relatórios Comerciais":
        st.info("Relatório do ANP: Análise de propostas geradas, taxas de conversão e receita projetada.")
        commercial_data = backend.get_commercial_report() # Este deve retornar um dicionário com chaves como 'propostas_geradas', 'propostas_aprovadas', 'taxa_aprovacao'
        st.write(f"**Propostas Geradas:** {commercial_data.get('propostas_geradas', 0)}")
        st.write(f"**Propostas Aprovadas:** {commercial_data.get('propostas_aprovadas', 0)}")
        st.write(f"**Taxa de Aprovação:** {commercial_data.get('taxa_aprovacao', 0):.2f}%")
    elif report_type == "Status de Backup e Infraestrutura":
        st.info("Relatório do MOAI/AID: Saúde dos sistemas, logs de infraestrutura e verificação de backups.")
        backup_infra_status = backend.get_backup_infra_status_report() # Este deve retornar um dicionário
        if backup_infra_status.get('status_backup_recente') == "Sucesso":
            st.success(f"Último backup completo em {backup_infra_status.get('timestamp_backup')} - Status: Sucesso ✅")
        elif backup_infra_status.get('status_backup_recente') == "Sucesso com Avisos":
            st.warning(f"Último backup completo em {backup_infra_status.get('timestamp_backup')} - Status: Sucesso com Avisos ⚠️")
        else:
            st.error(f"Último backup completo em {backup_infra_status.get('timestamp_backup')} - Status: Falha ❌")
        
        st.subheader("Políticas de Backup:")
        for policy in backup_infra_status.get('politicas', []):
            st.markdown(policy)
    elif report_type == "Logs de Orquestração MOAI": # Nova página de logs
        st.info("Este relatório detalha todas as ações e decisões tomadas pelo MOAI, incluindo a orquestração de agentes e interação com o sistema.")
        moai_logs: List[MoaiLog] = backend.get_moai_logs()
        if not moai_logs:
            st.info("Nenhum log de orquestração do MOAI encontrado ainda.")
        else:
            st.subheader("Histórico de Logs do MOAI:")
            for log_entry in moai_logs:
                # Corrigido: Usando atributos da classe MoaiLog
                with st.expander(f"[{log_entry.timestamp}] **{log_entry.action.replace('_', ' ').title()}**"):
                    st.json(log_entry.details) # Exibe os detalhes como JSON
    st.markdown("--- \n _Relatórios acionáveis para guiar suas decisões estratégicas._")

def moai_communication_page():
    st.header("💬 Comunicação Bidirecional com MOAI")
    st.markdown("""
    Interface de chat/comando para perguntas diretas, atualizações, alertas de decisões cruciais
    ou insights do MOAI. Seu canal direto com o cérebro da Synapse Forge.
    """)

    chat_history = backend.get_chat_history() # Este deve retornar uma lista de objetos com 'role' e 'content'
    for message in chat_history:
        with st.chat_message(message.role):
            st.markdown(message.content)

    if prompt := st.chat_input("Fale com o MOAI..."):
        # --- PONTO DE INTEGRAÇÃO REAL: Enviar mensagem ao MOAI (backend) ---
        backend.send_message_to_moai(prompt)
        st.rerun()
    st.markdown("--- \n _O MOAI sempre pronto para responder e auxiliar._")

def code_viewer_page():
    st.header("💻 Visualizador de Código Gerado")
    st.markdown("""
    Inspecione o código-fonte gerado pelos Agentes de Desenvolvimento (ADE-X).
    Garanta a qualidade e a conformidade com os padrões internos.
    """)

    all_projects = backend.get_all_projects() # Este deve retornar uma lista de objetos de projeto com 'db_id', 'name', 'project_id'
    if not all_projects:
        st.info("Nenhum projeto aprovado para visualizar o código. Aprovando uma proposta na Central de Aprovações, o ADE-X começará a gerar o código.")
    else:
        project_options = {p.db_id: p.name for p in all_projects} # Usar db_id como key
        selected_project_db_id = st.selectbox("Selecione um Projeto para Visualizar o Código:", list(project_options.keys()), format_func=lambda x: project_options[x], key="code_viewer_select")

        if selected_project_db_id:
            generated_codes: List[GeneratedCode] = backend.get_project_generated_code(selected_project_db_id)
            
            if not generated_codes:
                st.info("Nenhum código gerado para este projeto ainda.")
            else:
                project_name_display = project_options[selected_project_db_id]
                project_id_display = next((p.project_id for p in all_projects if p.db_id == selected_project_db_id), "")
                st.subheader(f"Código Gerado para {project_name_display} ({project_id_display})")
                st.info("Conteúdo do código gerado pelos ADE-X. Permite revisão e auditoria.")

                code_files = {gc.filename: gc for gc in generated_codes}
                selected_filename = st.selectbox("Selecione o arquivo de código:", list(code_files.keys()))

                if selected_filename:
                    selected_code = code_files[selected_filename]
                    # Corrigido: Usando atributos da classe GeneratedCode
                    st.code(selected_code.content, language=selected_code.language)
                    st.download_button(label=f"Baixar {selected_filename}", data=selected_code.content.encode('utf-8'), file_name=selected_filename)
    st.markdown("--- \n _A qualidade do código é garantida pelos padrões da Synapse Forge._")

def infra_backup_management_page():
    st.header("⚙️ Gestão de Infraestrutura e Backup")
    st.markdown("""
    Gerencie o layout do ambiente (pastas, arquivos), visualize o status dos backups,
    programe restaurações (para testes) e revise as políticas de retenção,
    tudo orquestrado pelo MOAI e AID.
    """)

    all_projects = backend.get_all_projects() # Este deve retornar uma lista de objetos de projeto com 'db_id', 'name', 'project_id'
    if not all_projects:
        st.info("Nenhum ambiente de projeto para gerenciar. Aprovando uma proposta, o AID provisionará o ambiente.")
    else:
        project_options = {p.db_id: p.name for p in all_projects} # Usar db_id como key
        selected_project_db_id_infra = st.selectbox("Selecione um Projeto para Gestão:", list(project_options.keys()), format_func=lambda x: project_options[x], key="infra_proj_select")

        if selected_project_db_id_infra:
            project_name_display = project_options[selected_project_db_id_infra]
            project_id_display = next((p.project_id for p in all_projects if p.db_id == selected_project_db_id_infra), "")
            st.write(f"### Ambiente do Projeto: {project_name_display} ({project_id_display})")
            # --- PONTO DE INTEGRAÇÃO REAL: Recuperar status da Infra (backend) ---
            infra_status = backend.get_infra_status(selected_project_db_id_infra)
            if "error" in infra_status:
                st.error(infra_status["error"])
            else:
                st.json(infra_status)

            st.subheader("Status do Último Backup:")
            backup_infra_status = backend.get_backup_infra_status_report() # Relatório geral, mas poderíamos ter um por projeto
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
                if st.button("Executar Backup Manual (AID)", key="manual_backup"):
                    # --- PONTO DE INTEGRAÇÃO REAL: Acionar Backup no AID (backend) ---
                    st.info(backend.trigger_manual_backup(selected_project_db_id_infra))
            with col_b2:
                if st.button("Programar Restauração para Testes (AID)", key="test_restore"):
                    # --- PONTO DE INTEGRAÇÃO REAL: Agendar Restauração no AID (backend) ---
                    st.warning(backend.schedule_test_restore(selected_project_db_id_infra))
    st.markdown("--- \n _O AID, o braço executor do MOAI, garante a automação e segurança._")

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
    st.title("🧠 CognitoLink")
    st.markdown("--- ✨ Visionary Command Center ✨ ---")

    st.subheader("Navegação Principal")
    if st.button("🏠 Dashboard Executivo", key="btn_dashboard"):
        st.session_state.current_page = "dashboard"
    if st.button("�� Entrada de Requisitos", key="btn_requisitos"):
        st.session_state.current_page = "requisitos"
    pending_proposals_count = backend.get_pending_proposals() # Este é o método que retorna APENAS a contagem
    if st.button(f"✅ Central de Aprovações ({pending_proposals_count})", key="btn_aprovacoes"):
        st.session_state.current_page = "aprovacoes"
    if st.button("⏳ Linha do Tempo do Projeto", key="btn_timeline"):
        st.session_state.current_page = "timeline"
    if st.button("📊 Relatórios Detalhados", key="btn_relatorios"):
        st.session_state.current_page = "relatorios"
    if st.button("💬 Comunicação com MOAI", key="btn_chat_moai"):
        st.session_state.current_page = "chat_moai"
    if st.button("💻 Visualizador de Código", key="btn_code_viewer"):
        st.session_state.current_page = "code_viewer"
    if st.button("⚙️ Gestão de Infraestrutura e Backup", key="btn_infra_backup"):
        st.session_state.current_page = "infra_backup"
    st.markdown("---")
    if st.button("ℹ️ Sobre o CognitoLink", key="btn_sobre"):
        st.session_state.current_page = "sobre"

# --- Roteamento de Páginas (Conteúdo Principal) ---
if st.session_state.current_page == "dashboard":
    dashboard_page()
elif st.session_state.current_page == "requisitos":
    requirements_entry_page()
elif st.session_state.current_page == "aprovacoes":
    approvals_center_page()
elif st.session_state.current_page == "timeline":
    project_timeline_page()
elif st.session_state.current_page == "relatorios":
    detailed_reports_page()
elif st.session_state.current_page == "chat_moai":
    moai_communication_page()
elif st.session_state.current_page == "code_viewer":
    code_viewer_page()
elif st.session_state.current_page == "infra_backup":
    infra_backup_management_page()
elif st.session_state.current_page == "sobre":
    about_page()
