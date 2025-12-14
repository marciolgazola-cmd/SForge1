# ams_agent.py
import logging
import json
import random
import datetime
from typing import Dict, Any, List, Optional, cast # Adicionado 'cast'
from pydantic import BaseModel, Field
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
from agent_model_mapping import get_agent_model

logger = logging.getLogger(__name__)

# Exemplo de modelo de saída para o AMS
class MonitoringSummaryOutput(BaseModel):
    system_health: Dict[str, Any] = Field(description="Status geral de saúde dos sistemas (ex: 'OK', 'Warning', 'Critical').")
    resource_usage: Dict[str, str] = Field(description="Uso de recursos (CPU, memória, rede) (ex: '75%').")
    recent_alerts: List[Dict[str, str]] = Field(description="Lista de alertas recentes (severidade, mensagem, timestamp).")
    recommendations: List[str] = Field(description="Recomendações para otimização ou resolução de problemas.")
    last_updated: str = Field(description="Timestamp da última atualização do resumo.")

class AMSAgent:
    def __init__(self, llm_simulator: LLMSimulator):
        self.llm_simulator = llm_simulator
        self.model_name = get_agent_model('AMS') # Obtém o modelo para AMS
        logger.info(f"AMSAgent inicializado com modelo {self.model_name} e pronto para monitorar sistemas.")

    def generate_monitoring_summary(self, project_id: Optional[str] = None, project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Gera um resumo de monitoramento, seja global ou para um projeto específico.
        """
        scope = "global"
        if project_id and project_name:
            scope = f"para o projeto '{project_name}' (ID: {project_id})"

        # Simula dados de monitoramento
        simulated_data = {
            "uptime": f"{random.randint(90, 100)}%",
            "cpu_usage": f"{random.randint(10, 80)}%",
            "memory_usage": f"{random.randint(20, 90)}%",
            "network_traffic": f"{random.randint(10, 100)} Mbps",
            "db_connections": random.randint(5, 50),
            "errors_per_sec": round(random.uniform(0.0, 1.5), 2),
            "alerts_count": random.randint(0, 3)
        }
        
        alerts = []
        if simulated_data["alerts_count"] > 0:
            alerts.append({"severity": "Warning", "message": f"Alto uso de CPU ({simulated_data['cpu_usage']}) detectado.", "timestamp": datetime.datetime.now().isoformat()})

        prompt = f"""
        Gere um resumo de monitoramento para o escopo {scope}.
        Analise os dados simulados e forneça o status geral de saúde, uso de recursos, alertas recentes e recomendações.

        Dados Simulados de Monitoramento:
        {json.dumps(simulated_data, indent=2, ensure_ascii=False)}

        Sua resposta deve ser um objeto JSON.
        """

        messages = [
            {"role": "system", "content": "Você é um Agente de Monitoramento e Suporte (AMS). Sua tarefa é fornecer resumos claros e acionáveis sobre o estado dos sistemas."
                                                "Sua saída deve ser um JSON estritamente no formato do esquema Pydantic para MonitoringSummaryOutput."},
            {"role": "user", "content": prompt}
        ]

        try:
            # Passa o nome do modelo explicitamente e força json_mode
            response_raw = self.llm_simulator.chat(
                messages=messages,
                model=self.model_name,
                response_model=MonitoringSummaryOutput,
                json_mode=True
            )
            response: MonitoringSummaryOutput = cast(MonitoringSummaryOutput, response_raw) # Cast para informar o Pylance
            logger.info(f"AMSAgent: Resumo de monitoramento gerado com sucesso usando {self.model_name} para {scope}.")
            return response.model_dump() # Converte o modelo Pydantic para dicionário
        except (LLMConnectionError, LLMGenerationError) as e:
            logger.error(f"AMSAgent: Falha ao gerar resumo de monitoramento com o LLM {self.model_name}. Erro: {e}")
            logger.warning(f"Erro ao gerar resumo de monitoramento com o LLM: {e}. Gerando dados padrão.")
            # Retorno de fallback consistente com a estrutura esperada
            return {
                "system_health": {"status": "Degraded", "message": f"Falha na comunicação LLM: {e}", "average_uptime": "N/A"},
                "resource_usage": {"cpu_usage": "N/A", "memory_usage": "N/A", "network_traffic": "N/A"},
                "recent_alerts": [{"severity": "Critical", "message": f"Falha na geração do resumo de monitoramento via LLM: {e}", "timestamp": datetime.datetime.now().isoformat()}],
                "recommendations": ["Verificar conexão com o LLM e logs do AMS."],
                "last_updated": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"AMSAgent: Erro inesperado ao gerar resumo de monitoramento: {e}")
            return {
                "system_health": {"status": "Error", "message": f"Erro inesperado: {e}", "average_uptime": "N/A"},
                "resource_usage": {"cpu_usage": "N/A", "memory_usage": "N/A", "network_traffic": "N/A"},
                "recent_alerts": [{"severity": "Critical", "message": f"Erro inesperado ao gerar resumo: {e}", "timestamp": datetime.datetime.now().isoformat()}],
                "recommendations": ["Contatar o administrador do sistema."],
                "last_updated": datetime.datetime.now().isoformat()
            }
