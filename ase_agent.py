# ase_agent.py
import uuid
import datetime
import random
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
from agent_model_mapping import get_agent_model
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Modelo Pydantic para a resposta do ASE ---
class ASEReport(BaseModel):
    status: Optional[str] = Field(None, description="Status geral da auditoria de segurança (ex: 'Seguro', 'Vulnerabilidades Encontradas').")
    overall_risk: Optional[str] = Field(None, description="Avaliação do risco geral (ex: 'Baixo', 'Médio', 'Alto').")
    vulnerabilities: Dict[str, int] = Field(default_factory=dict, description="Contagem de vulnerabilidades por nível (crítico, alto, médio, baixo).")
    compliance_status: Optional[str] = Field(None, description="Status de conformidade com padrões de segurança (ex: 'Em conformidade', 'Não conforme').")
    last_scan: Optional[str] = Field(None, description="Data e hora da última varredura de segurança.")
    recommendations: List[str] = Field(default_factory=list, description="Lista de recomendações de segurança.")
    details_llm: Optional[str] = Field(None, description="Detalhes adicionais e insights gerados pelo LLM.")

class ASEAgent:
    def __init__(self, llm_simulator: LLMSimulator):
        self.llm_simulator = llm_simulator
        self.model = get_agent_model('ASE')  # llama3 para análise minuciosa de segurança
        logging.info(f"ASEAgent inicializado com modelo {self.model} e pronto para auditar segurança.")

    def generate_security_report(self, project_id: str, project_name: str, code_snippets: List[Dict[str, str]]) -> Dict[str, Any]:
        logging.info(f"ASEAgent: Gerando relatório de segurança para o projeto '{project_name}' ({project_id})...")

        # Simula algumas vulnerabilidades
        critical_v = random.randint(0, 1)
        high_v = random.randint(0, 3)
        medium_v = random.randint(0, 5)
        low_v = random.randint(0, 10)

        # Converte snippets de código em uma string para o prompt do LLM
        code_str = "\n\n".join([f"### {snippet['filename']} ({snippet['language']})\n```\n{snippet['content']}\n```" for snippet in code_snippets])
        if not code_str:
            code_str = "Nenhum snippet de código fornecido. Gerando relatório baseado apenas na descrição."

        prompt = f"""
        Gere um relatório de segurança e auditoria para o projeto de software '{project_name}' (ID: {project_id}).
        Considere os seguintes dados de vulnerabilidades e snippets de código (se disponíveis).
        Forneça uma análise detalhada, incluindo status, risco geral, vulnerabilidades encontradas,
        status de conformidade e recomendações.

        Dados de Vulnerabilidades Sintéticas:
        - Críticas: {critical_v}
        - Altas: {high_v}
        - Médias: {medium_v}
        - Baixas: {low_v}

        Snippets de Código para Análise (se houver):
        {code_str}

        Sua resposta deve ser um JSON estritamente conforme o modelo ASEReport Pydantic.
        """

        system_message = "Você é o Agente de Segurança (ASE) da Synapse Forge. Sua função é analisar o código e a infraestrutura, identificar vulnerabilidades de segurança, garantir conformidade com padrões e fornecer recomendações para proteger os sistemas."
        
        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': prompt}
        ]

        try:
            response_obj = self.llm_simulator.chat(messages, response_model=ASEReport, model_override=self.model)
            logging.info(f"ASEAgent: Relatório de segurança gerado para o projeto '{project_name}' ({project_id}).")
            return response_obj.dict()
        except (LLMConnectionError, LLMGenerationError) as e:
            logging.error(f"ASEAgent: Falha ao gerar relatório de segurança para '{project_name}' ({project_id}). Erro: {e}")
            error_message = f"Erro ao gerar relatório de segurança com o LLM: {e}. Gerando relatório padrão."
            logging.warning(error_message)
            # Fallback para um relatório com dados padrão
            return {
                "status": "Erro na Geração",
                "overall_risk": "Desconhecido",
                "vulnerabilities": {"critical": critical_v, "high": high_v, "medium": medium_v, "low": low_v},
                "compliance_status": "N/A (Erro LLM)",
                "last_scan": datetime.datetime.now().isoformat(),
                "recommendations": [f"Não foi possível gerar recomendações detalhadas devido a um erro no LLM. {error_message}"],
                "details_llm": f"O LLM falhou ao gerar o relatório de segurança detalhado. Motivo: {e}."
            }
        except Exception as e:
            logging.error(f"ASEAgent: Erro inesperado ao gerar relatório de segurança: {e}")
            return {
                "status": "Erro Interno",
                "overall_risk": "Desconhecido",
                "vulnerabilities": {"critical": critical_v, "high": high_v, "medium": medium_v, "low": low_v},
                "compliance_status": "N/A (Erro Interno)",
                "last_scan": datetime.datetime.now().isoformat(),
                "recommendations": [f"Não foi possível gerar recomendações detalhadas devido a um erro interno: {e}"],
                "details_llm": f"Um erro inesperado ocorreu: {e}."
            }