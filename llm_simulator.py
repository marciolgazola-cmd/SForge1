# llm_simulator.py
import time
import random
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from data_models import (
    Proposal, Project, GeneratedCode, QualityReportEntry,
    SecurityReportEntry, Documentation, MonitoringSummary, MOAILog, ChatMessage
)

class LLMSimulator:
    def __init__(self):
        # No Ollama connection for now, just simulate output
        pass

    # --- Simulações para Geração de Propostas (ANP) ---
    def generate_proposal_content(self, requirements: Dict[str, Any]) -> Dict[str, str]:
        # Small delay to simulate LLM processing
        time.sleep(random.uniform(0.5, 1.5))
        
        project_name = requirements.get('nome_projeto', 'Projeto Genérico')
        client_name = requirements.get('nome_cliente', 'Cliente Desconhecido')
        objetivos = requirements.get('objetivos_projeto', 'Melhorar eficiência e inovação.')
        problema = requirements.get('problema_negocio', 'Problemas de sistema legados.')

        problem_understanding = f"""
        **Análise Aprofundada (ARA):**

        O cliente **{client_name}** busca resolver o desafio de:
        *   **{problema}**
        *   Observa-se a necessidade de modernização e otimização de processos, atualmente impactados por [mencionar dores específicas, ex: ineficiências operacionais, falta de escalabilidade].

        A compreensão do problema aponta para uma lacuna em [áreas específicas, ex: automatização de tarefas, integração de sistemas], que impede o alcance dos objetivos de [citar objetivos, ex: redução de custos, melhoria na experiência do usuário].
        """

        solution_proposal = f"""
        **Proposta de Solução (AAD):**

        Propomos a implementação de um sistema [tipo de sistema, ex: web-based, mobile-first] com arquitetura de microsserviços, utilizando [tecnologia primária, ex: Python/FastAPI, Node.js/React].

        A solução focará em:
        1.  Desenvolvimento de um módulo de [funcionalidade chave, ex: gestão de inventário] com interface intuitiva.
        2.  Integração com [sistemas existentes, ex: ERP, CRM] para garantir fluxo de dados contínuo.
        3.  Implementação de funcionalidades de [funcionalidade secundária, ex: relatórios analíticos em tempo real] para suporte à decisão.
        """

        scope = f"""
        **Escopo Detalhado (AAD):**

        O escopo inclui:
        *   **Fase 1: Levantamento e Planejamento (2 semanas)**
            *   Workshops com stakeholders, detalhamento de requisitos.
        *   **Fase 2: Desenvolvimento do Backend (6 semanas)**
            *   APIs RESTful, banco de dados (PostgreSQL/MongoDB).
        *   **Fase 3: Desenvolvimento do Frontend (5 semanas)**
            *   Interface responsiva, componentes reutilizáveis.
        *   **Fase 4: Testes e Homologação (3 semanas)**
            *   Testes de unidade, integração, aceitação do usuário.
        *   **Fase 5: Implantação e Treinamento (1 semana)**
            *   Go-live, suporte inicial.

        **Não Inclui:** [Excluir funcionalidades específicas se necessário, ex: manutenção de hardware existente, integrações não especificadas].
        """

        technologies_suggested = f"""
        **Tecnologias Sugeridas (AAD/MOAI):**

        *   **Backend:** Python 3.10+, FastAPI, SQLAlchemy, PostgreSQL.
        *   **Frontend:** React 18+, TypeScript, Material-UI.
        *   **Infraestrutura:** Docker, Kubernetes (opcional, para escalabilidade), AWS/Azure (EC2, RDS).
        *   **CI/CD:** GitHub Actions / GitLab CI.
        *   **Controle de Versão:** Git.
        """

        estimated_value = f"R$ {random.randint(50000, 200000):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') # Format as Brazilian currency
        estimated_time = f"{random.randint(12, 20)} semanas" # in weeks

        terms_conditions = f"""
        **Termos e Condições (MOAI):**

        *   **Validade da Proposta:** 30 dias a partir da data de emissão.
        *   **Condições de Pagamento:** 30% na aprovação, 40% na entrega do MVP, 30% na homologação final.
        *   **Suporte Pós-Implantação:** 30 dias de garantia contra defeitos de código. Suporte estendido via contrato SLA separado.
        *   **Propriedade Intelectual:** Todo o código-fonte desenvolvido será de propriedade do cliente após a quitação total do projeto.
        *   **Reajuste:** Valores e prazos podem ser reavaliados em caso de mudança de escopo.
        """

        return {
            "title": f"Proposta para {project_name} - {client_name}",
            "description": f"Desenvolvimento de uma solução para {problema} com foco em {objetivos}.",
            "problem_understanding_moai": problem_understanding,
            "solution_proposal_moai": solution_proposal,
            "scope_moai": scope,
            "technologies_suggested_moai": technologies_suggested,
            "estimated_value_moai": estimated_value,
            "estimated_time_moai": estimated_time,
            "terms_conditions_moai": terms_conditions
        }
    
    # --- Simulações para Geração de Código (ADE-X) ---
    def generate_code(self, project_description: str, filename: str, language: str) -> str:
        time.sleep(random.uniform(0.5, 1.0))
        
        # Helper to create a valid JavaScript component name (PascalCase, no hyphens)
        def get_js_component_name(file_name):
            name_without_ext = file_name.replace('.js', '').replace('.jsx', '')
            return ''.join(word.capitalize() for word in name_without_ext.split('-')).replace('_', '') # Also remove underscores

        if language == "Python":
            if "flask" in project_description.lower():
                return f"""# {filename}
# Simulando código Python (Flask) para: {project_description}

from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({{"message": "Dados do projeto {project_description} via Flask!"}})

@app.route('/api/data', methods=['POST'])
def post_data():
    data = request.json
    return jsonify({{"message": f"Dados recebidos para {project_description}: {{data}}", "status": "success"}})

if __name__ == '__main__':
    app.run(debug=True)
"""
            elif "react" in project_description.lower():
                component_name = get_js_component_name(filename)
                return f"""// {filename}
// Simulando código JavaScript (React Component) para: {project_description}

import React from 'react';

function {component_name}() {{
  return (
    <div>
      <h1>Componente React para {project_description}</h1>
      <p>Este é um componente simulado para demonstração.</p>
      <button onClick={{() => alert('Botão clicado!')}}>Clique-me</button>
    </div>
  );
}}

export default {component_name};
"""
            else:
                return f"""# {filename}
# Simulando código Python genérico para: {project_description}

def hello_{project_description.replace(' ', '_').lower()}():
    return f"Olá do {filename}! Seu projeto é sobre: {project_description}"

if __name__ == "__main__":
    print(hello_{project_description.replace(' ', '_').lower()}())
"""
        elif language == "JavaScript":
            return f"""// {filename}
// Simulando código JavaScript para: {project_description}

function runProjectLogic() {{
    console.log("Executando lógica JavaScript para: {project_description}");
    // Exemplo de lógica simples
    let data = {{"status": "online", "version": "1.0"}};
    return data;
}}

runProjectLogic();
"""
        elif language == "SQL":
            return f"""-- {filename}
-- Simulando SQL para: {project_description}

CREATE TABLE IF NOT EXISTS {project_description.replace(' ', '_').lower()}_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    value TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO {project_description.replace(' ', '_').lower()}_data (name, value) VALUES ('Exemplo 1', 'Valor para {project_description}');
SELECT * FROM {project_description.replace(' ', '_').lower()}_data;
"""
        else:
            return f"""# {filename}
# Código genérico para: {project_description} em {language}
# Nenhuma simulação específica disponível para esta linguagem.
"""

    # --- Simulações para Geração de Relatórios de Qualidade (AQT) ---
    def generate_quality_report(self, project_description: str) -> Dict[str, Any]:
        time.sleep(random.uniform(0.5, 1.0))
        return {
            "status": random.choice(["Concluído", "Em Análise", "Falha nos Testes"]),
            "total_tests": random.randint(100, 500),
            "passed_tests": random.randint(70, 95), # Percentage
            "failed_tests": random.randint(5, 30), # Percentage
            "code_coverage": f"{random.randint(70, 99)}%",
            "stability": random.choice(["Alta", "Média", "Baixa"]),
            "average_test_execution_time_seconds": round(random.uniform(0.5, 5.0), 2),
            "recommendations": [
                "Aumentar cobertura de testes para módulos críticos.",
                "Otimizar tempo de execução de testes de integração.",
                "Revisar falhas recorrentes no módulo X."
            ],
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "details_llm": f"""
                O relatório de qualidade para o projeto "{project_description}" indica uma cobertura de testes sólida e boa estabilidade geral. No entanto, foram identificadas falhas em [módulo ou área específica] que merecem atenção para manter a alta qualidade do produto. A otimização contínua dos testes pode reduzir ainda mais o tempo de feedback do ciclo de desenvolvimento.
            """
        }

    # --- Simulações para Geração de Relatórios de Segurança (ASE) ---
    def generate_security_report(self, project_description: str) -> Dict[str, Any]:
        time.sleep(random.uniform(0.5, 1.0))
        return {
            "status": random.choice(["Seguro", "Com Avisos", "Vulnerabilidades Críticas"]),
            "overall_risk": random.choice(["Baixo", "Médio", "Alto"]),
            "vulnerabilities": {
                "critical": random.randint(0, 2),
                "high": random.randint(0, 5),
                "medium": random.randint(0, 10),
                "low": random.randint(5, 20)
            },
            "compliance_status": random.choice(["Conforme GDPR/LGPD", "Requer Ajustes", "Não Conforme"]),
            "last_scan": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "recommendations": [
                "Aplicar patches de segurança críticos imediatamente.",
                "Revisar configurações de firewall e grupos de segurança.",
                "Implementar MFA para acesso administrativo."
            ],
            "details_llm": f"""
                A análise de segurança para o projeto "{project_description}" revelou um risco geral {random.choice(["Baixo", "Médio"])}. Embora algumas vulnerabilidades {random.choice(["menores", "médias"])} tenham sido identificadas, não há ameaças críticas imediatas. Recomenda-se a revisão periódica e a aplicação de boas práticas de segurança, especialmente em [áreas específicas, ex: tratamento de dados sensíveis].
            """
        }

    # --- Simulações para Geração de Documentação (ADO) ---
    def generate_documentation(self, project_description: str, project_requirements: Dict[str, Any]) -> Dict[str, str]:
        time.sleep(random.uniform(0.5, 1.5))
        
        doc_content = f"""# Documentação do Projeto: {project_description}

## Visão Geral

Este documento detalha a arquitetura, funcionalidades e diretrizes de uso do projeto. O objetivo principal é **{project_requirements.get('objetivos_projeto', 'N/A')}**, abordando o problema de **{project_requirements.get('problema_negocio', 'N/A')}** para o cliente **{project_requirements.get('nome_cliente', 'N/A')}**.

## Requisitos Iniciais do Cliente

### Problema de Negócio
{project_requirements.get('problema_negocio', 'N/A')}

### Objetivos do Projeto
{project_requirements.get('objetivos_projeto', 'N/A')}

### Funcionalidades Esperadas
{project_requirements.get('funcionalidades_esperadas', 'Nenhuma detalhada.')}

### Restrições
{project_requirements.get('restricoes', 'Nenhuma.')}

## Arquitetura da Solução

[Diagrama ou descrição da arquitetura. Ex: Microsserviços, componentes, fluxos de dados.]

## Tecnologias Utilizadas

*   **Backend:** Python, FastAPI, PostgreSQL
*   **Frontend:** React, TypeScript
*   **Infraestrutura:** Docker, AWS EC2

## Guia de Implantação

1.  Clone o repositório: `git clone [URL_DO_REPO]`
2.  Configure variáveis de ambiente.
3.  Execute o script de deploy: `./deploy.sh`

## Guia de Uso

[Instruções detalhadas para usuários finais ou desenvolvedores.]

## Changelog

*   **Versão 1.0.0 (Data):** Lançamento inicial.
*   **Versão 1.0.1 (Data):** Correções de bugs e melhorias de performance.
"""
        return {
            "filename": f"documentacao_{project_description.replace(' ', '_').lower()}.md",
            "content": doc_content,
            "format": "Markdown"
        }

    # --- Simulações para Chat com MOAI ---
    def process_chat_message(self, user_message: str) -> str:
        time.sleep(random.uniform(0.5, 1.0))
        user_message_lower = user_message.lower()

        if "olá" in user_message_lower or "oi" in user_message_lower:
            return "Olá! Como posso ajudar você hoje?"
        elif "status do projeto" in user_message_lower:
            return "Simulando consulta ao status... O Projeto X está 75% concluído, em fase de testes."
        elif "criar proposta" in user_message_lower:
            return "Para criar uma nova proposta, por favor, utilize o 'Módulo de Entrada de Requisitos'."
        elif "agentes" in user_message_lower:
            return "No momento, os agentes ADE-X e AQT estão ativos em projetos. O AID está monitorando a infraestrutura."
        elif "excluir" in user_message_lower and "proposta" in user_message_lower:
            return "A função de exclusão de proposta está disponível na 'Central de Aprovações'. Tenha cuidado, pois a ação é irreversível."
        elif "obrigado" in user_message_lower or "valeu" in user_message_lower:
            return "De nada! Estou à disposição."
        else:
            return "Entendi. Sua solicitação foi registrada e o MOAI está analisando para as próximas ações."