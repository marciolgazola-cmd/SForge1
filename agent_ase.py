# agent_ase.py
import logging
import json
import random
from typing import Dict, Any, List, cast # Adicionado 'cast'
from pydantic import BaseModel, Field
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
from agent_models import get_agent_model

logger = logging.getLogger(__name__)

# Exemplo de modelo de saída para o ASE
class SecurityReportOutput(BaseModel):
    overall_security_status: str = Field(description="Status geral de segurança (Secure, Vulnerable, Warning).")
    vulnerabilities_found: int = Field(description="Número de vulnerabilidades identificadas.")
    risk_level: str = Field(description="Nível de risco geral (Low, Medium, High, Critical).")
    vulnerabilities: List[Dict[str, str]] = Field(description="Detalhes das vulnerabilidades (nome, severidade, descrição, recomendação).")
    security_score: int = Field(description="Pontuação de segurança (0-100).")
    recommendations: List[str] = Field(description="Recomendações para melhorar a segurança.")

class AgentASE:
    def __init__(self, llm_simulator: LLMSimulator):
        self.llm_simulator = llm_simulator
        self.model_name = get_agent_model('ASE') # Obtém o modelo para ASE
        logger.info(f"AgentASE inicializado com modelo {self.model_name} e pronto para auditar segurança.")

    def generate_security_report(self, project_id: str, project_name: str, code_snippets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Gera um relatório de segurança para um projeto, simulando uma auditoria.
        """
        # Simula uma análise de segurança básica
        simulated_security_scan = {
            "critical_vulnerabilities": random.randint(0, 1),
            "high_vulnerabilities": random.randint(0, 2),
            "medium_vulnerabilities": random.randint(0, 5),
            "low_vulnerabilities": random.randint(0, 10),
            "compliance_score": random.randint(60, 99),
        }

        prompt = f"""
        Gere um relatório de segurança abrangente para o projeto '{project_name}' (ID: {project_id}).
        Considere a seguinte análise de segurança simulada e snippets de código fornecidos.
        Identifique o status geral, vulnerabilidades, nível de risco e recomendações.

        Análise de Segurança Simulada:
        {json.dumps(simulated_security_scan, indent=2, ensure_ascii=False)}

        Snippets de Código (visão geral):
        {[c.get('filename', 'N/A') for c in code_snippets]}

        Sua resposta deve ser um objeto JSON.
        """

        messages = [
            {"role": "system", "content": "Você é um Agente de Segurança (ASE). Sua tarefa é identificar vulnerabilidades e garantir a integridade e conformidade dos sistemas."
                                                "Sua saída deve ser um JSON estritamente no formato do esquema Pydantic para SecurityReportOutput."},
            {"role": "user", "content": prompt}
        ]

        try:
            # Passa o nome do modelo explicitamente e força json_mode
            response_raw = self.llm_simulator.chat(
                messages=messages,
                model=self.model_name,
                response_model=SecurityReportOutput,
                json_mode=True
            )
            response: SecurityReportOutput = cast(SecurityReportOutput, response_raw) # Cast para informar o Pylance
            logger.info(f"AgentASE: Relatório de segurança gerado com sucesso usando {self.model_name} para '{project_name}'.")
            return response.model_dump() # Converte o modelo Pydantic para dicionário
        except (LLMConnectionError, LLMGenerationError) as e:
            logger.error(f"AgentASE: Falha ao gerar relatório de segurança com o LLM {self.model_name}. Erro: {e}")
            logger.warning(f"Erro ao gerar relatório de segurança com o LLM: {e}. Gerando relatório padrão.")
            # Retorno de fallback consistente com a estrutura esperada
            return {
                "overall_security_status": "Vulnerable",
                "vulnerabilities_found": 1,
                "risk_level": "High",
                "vulnerabilities": [{"name": "LLM Report Generation Failed", "severity": "Critical", "description": f"Falha na comunicação com o LLM para gerar o relatório de segurança: {e}", "recommendation": "Verificar LLM"}],
                "security_score": 0,
                "recommendations": ["Verificar a conexão com o LLM e se o modelo está disponível."]
            }
        except Exception as e:
            logger.error(f"AgentASE: Erro inesperado ao gerar relatório de segurança: {e}")
            return {
                "overall_security_status": "Error",
                "vulnerabilities_found": 0,
                "risk_level": "Critical",
                "vulnerabilities": [{"name": "Internal Error", "severity": "Critical", "description": f"Erro inesperado ao gerar relatório de segurança: {e}", "recommendation": "Contatar suporte"}],
                "security_score": 0,
                "recommendations": ["Contatar o administrador do sistema para investigação."]
            }
