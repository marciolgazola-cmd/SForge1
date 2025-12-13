# aqt_agent.py
import uuid
import datetime
import random
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
from agent_model_mapping import get_agent_model
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Modelo Pydantic para a resposta do AQT ---
class AQTReport(BaseModel):
    status: Optional[str] = Field(None, description="Status geral do relatório de qualidade (ex: 'Aprovado', 'Com Falhas').")
    total_tests: Optional[int] = Field(0, description="Número total de testes executados.")
    passed_tests: Optional[int] = Field(0, description="Número de testes aprovados.")
    failed_tests: Optional[int] = Field(0, description="Número de testes falhos.")
    code_coverage: Optional[str] = Field(None, description="Porcentagem de cobertura de código (ex: '85%').")
    stability: Optional[str] = Field(None, description="Avaliação da estabilidade do software (ex: 'Alta', 'Média', 'Baixa').")
    average_test_execution_time_seconds: float = Field(0.0, description="Tempo médio de execução dos testes em segundos.")
    recommendations: List[str] = Field(default_factory=list, description="Lista de recomendações para melhoria da qualidade.")
    details_llm: Optional[str] = Field(None, description="Detalhes adicionais e insights gerados pelo LLM.")
    last_update: Optional[str] = Field(None, description="Data e hora da última atualização do relatório.")

class AQTAgent:
    def __init__(self, llm_simulator: LLMSimulator):
        self.llm_simulator = llm_simulator
        self.model = get_agent_model('AQT')  # llama3 para análise detalhada de testes
        logging.info(f"AQTAgent inicializado com modelo {self.model} e pronto para auditar qualidade.")

    def generate_quality_report(self, project_id: str, project_name: str, code_snippets: List[Dict[str, str]]) -> Dict[str, Any]:
        logging.info(f"AQTAgent: Gerando relatório de qualidade para o projeto '{project_name}' ({project_id})...")

        # Simula alguns dados básicos de teste
        total_tests = random.randint(50, 200)
        failed_tests = random.randint(0, int(total_tests * 0.1)) # Até 10% de falhas
        passed_tests = total_tests - failed_tests
        
        # Converte snippets de código em uma string para o prompt do LLM
        code_str = "\n\n".join([f"### {snippet['filename']} ({snippet['language']})\n```\n{snippet['content']}\n```" for snippet in code_snippets])
        if not code_str:
            code_str = "Nenhum snippet de código fornecido. Gerando relatório baseado apenas na descrição."

        prompt = f"""
        Gere um relatório de qualidade e testes para o projeto de software '{project_name}' (ID: {project_id}).
        Considere os seguintes dados de teste e snippets de código (se disponíveis).
        Forneça uma análise detalhada, incluindo status, métricas e recomendações.

        Dados de Teste Sintéticos:
        - Total de testes executados: {total_tests}
        - Testes aprovados: {passed_tests}
        - Testes falhos: {failed_tests}
        - Cobertura de código (simulada): {random.randint(60, 95)}%

        Snippets de Código para Análise (se houver):
        {code_str}

        Sua resposta deve ser um JSON estritamente conforme o modelo AQTReport Pydantic.
        """

        system_message = "Você é o Agente de Qualidade e Testes (AQT) da Synapse Forge. Sua função é analisar o código e o comportamento do software, gerar relatórios de qualidade detalhados, identificar bugs e vulnerabilidades, e fornecer recomendações para garantir a excelência do produto."
        
        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': prompt}
        ]

        try:
            response_obj = self.llm_simulator.chat(messages, response_model=AQTReport, model_override=self.model)
            logging.info(f"AQTAgent: Relatório de qualidade gerado para o projeto '{project_name}' ({project_id}).")
            return response_obj.dict()
        except (LLMConnectionError, LLMGenerationError) as e:
            logging.error(f"AQTAgent: Falha ao gerar relatório de qualidade para '{project_name}' ({project_id}). Erro: {e}")
            error_message = f"Erro ao gerar relatório de qualidade com o LLM: {e}. Gerando relatório padrão."
            logging.warning(error_message)
            # Fallback para um relatório com dados padrão
            return {
                "status": "Erro na Geração",
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "code_coverage": "N/A (Erro LLM)",
                "stability": "Desconhecida (Erro LLM)",
                "average_test_execution_time_seconds": 0.0,
                "recommendations": [f"Não foi possível gerar recomendações detalhadas devido a um erro no LLM. {error_message}"],
                "details_llm": f"O LLM falhou ao gerar o relatório de qualidade detalhado. Motivo: {e}.",
                "last_update": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"AQTAgent: Erro inesperado ao gerar relatório de qualidade: {e}")
            return {
                "status": "Erro Interno",
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "code_coverage": "N/A (Erro Interno)",
                "stability": "Desconhecida (Erro Interno)",
                "average_test_execution_time_seconds": 0.0,
                "recommendations": [f"Não foi possível gerar recomendações detalhadas devido a um erro interno: {e}"],
                "details_llm": f"Um erro inesperado ocorreu: {e}.",
                "last_update": datetime.datetime.now().isoformat()
            }
