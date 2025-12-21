# agent_aqt.py
import logging
import json
import random
from typing import Dict, Any, List, cast # Adicionado 'cast'
from pydantic import BaseModel, Field
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
from agent_models import get_agent_model

logger = logging.getLogger(__name__)

# Exemplo de modelo de saída para o AQT
class QualityReportOutput(BaseModel):
    overall_status: str = Field(description="Status geral da qualidade (Passed, Failed, Warning).")
    total_tests: int = Field(description="Número total de testes executados.")
    passed_tests: int = Field(description="Número de testes que passaram.")
    failed_tests: int = Field(description="Número de testes que falharam.")
    test_results: List[Dict[str, str]] = Field(description="Detalhes de cada teste (nome, status, mensagem).")
    recommendations: List[str] = Field(description="Recomendações para melhoria da qualidade.")

class AgentAQT:
    def __init__(self, llm_simulator: LLMSimulator):
        self.llm_simulator = llm_simulator
        self.model_name = get_agent_model('AQT') # Obtém o modelo para AQT
        logger.info(f"AgentAQT inicializado com modelo {self.model_name} e pronto para auditar qualidade.")

    def generate_quality_report(self, project_id: str, project_name: str, code_snippets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Gera um relatório de qualidade e testes para um projeto.
        """
        # Simula a análise de código para gerar um relatório
        simulated_analysis = {
            "total_lines": sum(len(c.get('content', '').split('\n')) for c in code_snippets),
            "total_files": len(code_snippets),
            "potential_bugs": random.randint(0, 5),
            "test_coverage": random.randint(70, 95),
            "static_analysis_issues": random.randint(0, 10),
        }

        prompt = f"""
        Gere um relatório detalhado de qualidade e testes para o projeto '{project_name}' (ID: {project_id}).
        Considere a seguinte análise simulada e snippets de código fornecidos.
        Identifique o status geral, a quantidade de testes passados/falhos e recomendações.

        Análise Simulada:
        {json.dumps(simulated_analysis, indent=2, ensure_ascii=False)}

        Snippets de Código (visão geral):
        {[c.get('filename', 'N/A') for c in code_snippets]}

        Sua resposta deve ser um objeto JSON.
        """

        messages = [
            {"role": "system", "content": "Você é um Agente de Qualidade e Testes (AQT). Sua tarefa é auditar o código e processos para garantir a qualidade do projeto."
                                                "Sua saída deve ser um JSON estritamente no formato do esquema Pydantic para QualityReportOutput."},
            {"role": "user", "content": prompt}
        ]

        try:
            # Passa o nome do modelo explicitamente e força json_mode
            response_raw = self.llm_simulator.chat(
                messages=messages,
                model=self.model_name,
                response_model=QualityReportOutput,
                json_mode=True
            )
            response: QualityReportOutput = cast(QualityReportOutput, response_raw) # Cast para informar o Pylance
            logger.info(f"AgentAQT: Relatório de qualidade gerado com sucesso usando {self.model_name} para '{project_name}'.")
            return response.model_dump() # Converte o modelo Pydantic para dicionário
        except (LLMConnectionError, LLMGenerationError) as e:
            logger.error(f"AgentAQT: Falha ao gerar relatório de qualidade com o LLM {self.model_name}. Erro: {e}")
            # Retorno de fallback consistente com a estrutura esperada
            return {
                "overall_status": "Failed",
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "test_results": [{"name": "LLM Interaction", "status": "Failed", "message": f"Erro na geração do relatório: {e}"}],
                "recommendations": ["Verificar conexão LLM e modelo." if isinstance(e, LLMConnectionError) else "Analisar falha na geração do LLM."]
            }
        except Exception as e:
            logger.error(f"AgentAQT: Erro inesperado ao gerar relatório de qualidade: {e}")
            return {
                "overall_status": "Error",
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "test_results": [{"name": "Internal Error", "status": "Error", "message": f"Erro inesperado: {e}"}],
                "recommendations": ["Contatar suporte técnico."]
            }
