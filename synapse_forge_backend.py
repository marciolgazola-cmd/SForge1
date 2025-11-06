import datetime
import random
import uuid
from typing import Dict, Any, List
from data_models import MoaiLog, ChatMessage, Proposal, Project, GeneratedCode
from database_manager import DatabaseManager

class SynapseForgeBackend:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SynapseForgeBackend, cls).__new__(cls)
            cls._instance.db_manager = DatabaseManager()
            # Initialize with default data if DB is empty (first run)
            if not cls._instance.db_manager.get_all_proposals() and \
               not cls._instance.db_manager.get_all_projects():
                cls._instance._initialize_sample_data()
        return cls._instance

    def _initialize_sample_data(self):
        print("Initializing sample data...")
        # Sample MOAI Logs
        self.db_manager.insert_moai_log("system_boot", {"message": "MOAI core systems online."})
        self.db_manager.insert_moai_log("agent_orchestration", {"agent": "ADE-X", "status": "idle"})

        # Sample Chat Messages
        self.db_manager.insert_chat_message("ai", "Bem-vindo ao CognitoLink! Como posso ajudar hoje?")
        self.db_manager.insert_chat_message("user", "Preciso de uma visão geral dos projetos.")
        self.db_manager.insert_chat_message("ai", "Claro! Acesse o 'Dashboard Executivo' para uma visão rápida.")

        # Sample Proposals (for testing new fields)
        # Pending proposal
        req1 = {
            "nome_projeto": "Plataforma E-commerce",
            "nome_cliente": "Loja Online X",
            "problema_negocio": "Aumentar vendas e alcance de mercado.",
            "objetivos_projeto": "Expandir para novos mercados, melhorar experiência do usuário.",
            "funcionalidades_esperadas": "Carrinho de compras, gestão de produtos, processamento de pagamentos.",
            "restricoes": "Orçamento de R\$50k, prazo de 4 meses.",
            "publico_alvo": "Consumidores finais."
        }
        prop1 = self._moai_process_requirements(req1, 0) # Use 0 as temp id
        prop1.id = self.db_manager.insert_proposal(prop1) # Get real id
        
        # Approved proposal
        req2 = {
            "nome_projeto": "Sistema de Gestão Interna",
            "nome_cliente": "Tech Solutions LTDA",
            "problema_negocio": "Otimizar processos internos de RH.",
            "objetivos_projeto": "Reduzir tempo de onboarding em 30%, automatizar folha de pagamento.",
            "funcionalidades_esperadas": "Gestão de funcionários, controle de ponto, portal do colaborador.",
            "restricoes": "Uso de tecnologias open-source, integração com ERP existente.",
            "publico_alvo": "Colaboradores da empresa."
        }
        prop2 = self._moai_process_requirements(req2, 0) # Use 0 as temp id
        prop2.status = "approved"
        prop2.id = self.db_manager.insert_proposal(prop2) # Get real id
        
        # Rejected proposal
        req3 = {
            "nome_projeto": "Aplicativo de Delivery",
            "nome_cliente": "Fast Food Y",
            "problema_negocio": "Entregar pedidos mais rapidamente e aumentar a base de clientes.",
            "objetivos_projeto": "Lançar em 2 meses, suporte para 100k usuários.",
            "funcionalidades_esperadas": "Rastreamento em tempo real, pedidos online, avaliações.",
            "restricoes": "Orçamento limitado, equipe de desenvolvimento pequena.",
            "publico_alvo": "Usuários de smartphone."
        }
        prop3 = self._moai_process_requirements(req3, 0) # Use 0 as temp id
        prop3.status = "rejected"
        prop3.id = self.db_manager.insert_proposal(prop3) # Get real id

        # Simulate creation of a project for the approved proposal (prop2)
        project_id_str = f"PROJ-{uuid.uuid4().hex[:6].upper()}"
        project = Project(
            db_id=0, # temp
            project_id=project_id_str,
            name=prop2.title,
            client_name=prop2.requirements.get('nome_cliente', 'N/A'),
            status="active",
            progress=random.randint(10, 60),
            proposal_id=prop2.id
        )
        self.db_manager.insert_project(project)
        self._generate_code_for_project(prop2.id, project_id_str, prop2.title)

        print("Sample data initialized.")

    def _moai_process_requirements(self, req_data: Dict[str, Any], temp_proposal_id: int) -> Proposal:
        """
        Simula o processamento dos requisitos pelo MOAI para gerar uma proposta detalhada.
        """
        now = datetime.datetime.now()
        
        # Gerar título e descrição baseados nos requisitos
        title = f"Proposta para {req_data.get('nome_projeto', 'Novo Projeto')}"
        description = f"Proposta inicial para a {req_data.get('nome_projeto', 'solução desconhecida')} para o cliente {req_data.get('nome_cliente', 'desconhecido')}. Foco em {req_data.get('problema_negocio', 'resolver um desafio de negócio')}."

        # Gerar detalhes simulados pelo MOAI
        problem_understanding = (
            f"O MOAI analisou que o principal desafio do cliente {req_data.get('nome_cliente', 'N/A')} "
            f"com o projeto '{req_data.get('nome_projeto', 'N/A')}' é: "{req_data.get('problema_negocio', 'Problema não detalhado.')}". "
            "A solução deve endereçar esta questão para atingir os seguintes objetivos: "
            f""{req_data.get('objetivos_projeto', 'Objetivos não definidos.')}"."
        )

        solution_proposal = (
            f"A solução proposta pelo MOAI para o projeto '{req_data.get('nome_projeto', 'N/A')}' "
            f"incluirá funcionalidades como: {req_data.get('funcionalidades_esperadas', 'Funcionalidades básicas de gestão.')}. "
            "Será uma plataforma robusta e escalável, pensada para o público-alvo: "
            f"'{req_data.get('publico_alvo', 'usuários genéricos')}'."
        )

        scope_items = [
            f"- Desenvolvimento de módulo de {item.strip()}" for item in req_data.get('funcionalidades_esperadas', 'funcionalidades padrão').split(',')
        ]
        scope_moai = "Escopo detalhado:\n" + "\n".join(scope_items) + "\n- Integração contínua e deploy automatizado.\n- Testes unitários e de integração."

        technologies_suggested = (
            "Para esta solução, o MOAI sugere as seguintes tecnologias:\n"
            "- Backend: Python (Django/Flask) ou Node.js (Express)\n"
            "- Frontend: React.js ou Vue.js\n"
            "- Banco de Dados: PostgreSQL ou MongoDB\n"
            "- Infraestrutura: Docker, Kubernetes, AWS/Azure/GCP (dependendo da escalabilidade e custo)\n"
            "- Versionamento: Git (GitHub/GitLab)"
        )
        
        # Gerar valores e prazos mais realistas
        estimated_value = f"R\${random.randint(20000, 150000):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") # Formato pt-BR
        estimated_time = f"{random.randint(2, 6)} meses"

        terms_conditions = (
            "Termos e Condições Padrão da Synapse Forge:\n"
            "- Pagamento em parcelas mensais, com 30% de adiantamento.\n"
            "- Manutenção e suporte por 6 meses inclusos.\n"
            "- Alterações de escopo serão tratadas como aditivos contratuais.\n"
            "- Garantia de conformidade com as restrições fornecidas: "
            f"'{req_data.get('restricoes', 'Nenhuma restrição específica mencionada.')}'."
        )

        return Proposal(
            id=temp_proposal_id, # Será atualizado pelo DB
            title=title,
            description=description,
            requirements=req_data,
            status="pending",
            submitted_at=now,
            problem_understanding_moai=problem_understanding,
            solution_proposal_moai=solution_proposal,
            scope_moai=scope_moai,
            technologies_suggested_moai=technologies_suggested,
            estimated_value_moai=estimated_value,
            estimated_time_moai=estimated_time,
            terms_conditions_moai=terms_conditions
        )

    def _generate_code_for_project(self, proposal_id: int, project_id_str: str, project_name: str):
        """
        Simula a geração de código pelo ADE-X.
        """
        now = datetime.datetime.now()
        
        # Exemplo de arquivos gerados
        code_files_data = [
            {
                "filename": f"backend/{project_name.replace(' ', '_').lower()}/models.py",
                "content": f"""
# {project_name} - Backend Models
from django.db import models

class {project_name.replace(' ', '')}Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
                """,
                "language": "python"
            },
            {
                "filename": f"frontend/{project_name.replace(' ', '_').lower()}/App.js",
                "content": f"""
// {project_name} - Frontend App
import React from 'react';

function App() {{
  return (
    <div className="App">
      <header className="App-header">
        <h1>Welcome to {project_name}!</h1>
        <p>This is a basic frontend application.</p>
      </header>
    </div>
  );
  }}
export default App;
                """,
                "language": "javascript"
            },
            {
                "filename": f"README.md",
                "content": f"""
# {project_name} - Documentação do Projeto

Este é o repositório para a solução do projeto "{project_name}" gerado automaticamente pelo ADE-X da Synapse Forge.

## Visão Geral

A solução consiste em um backend (Python/Django) e um frontend (React.js) para {project_name}.

## Instalação

Siga os passos abaixo para configurar o ambiente de desenvolvimento.

### Backend

```bash
cd backend/{project_name.replace(' ', '_').lower()}
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver