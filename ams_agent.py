# ams_agent.py
import uuid
import datetime
import random
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Modelos Pydantic para a resposta do AMS ---
class AMSProjectSummary(BaseModel):
    overall_status: str = Field(..., description="Status geral do projeto (ex: 'Operacional', 'Degradado', 'Fora do Ar').")
    uptime_percentage_24h: float = Field(..., description="Porcentagem de uptime nas últimas 24 horas.")
    response_time_ms: float = Field(..., description="Tempo médio de resposta em milissegundos.")
    active_users: int = Field(..., description="Número de usuários ativos (simulado).")
    recent_alerts: List[str] = Field(..., description="Lista de alertas recentes.")
    last_checked: str = Field(..., description="Data e hora da última verificação.")

class AMSGlobalSummary(BaseModel):
    overall_system_status: str = Field(..., description="Status geral de todo o sistema Synapse Forge.")
    total_active_monitors: int = Field(..., description="Número total de monitores ativos.")
    total_recent_alerts: int = Field(..., description="Total de alertas recentes em todos os projetos.")
    critical_incidents_24h: int = Field(..., description="Número de incidentes críticos nas últimas 24 horas.")
    last_overall_summary: str = Field(..., description="Resumo geral das últimas verificações.")

class AMSAgent:
    def __init__(self, llm_simulator: LLMSimulator):
        self.llm_simulator = llm_simulator
        logging.info("AMSAgent inicializado e pronto para monitorar sistemas.")

    def generate_monitoring_summary(self, project_id: Optional[str] = None, project_name: Optional[str] = None) -> Dict[str, Any]:
        logging.info(f"AMSAgent: Gerando resumo de monitoramento para {'global' if project_id is None else project_name}...")

        if project_id is None: # Resumo Global
            total_active_monitors = random.randint(50, 150)
            total_recent_alerts = random.randint(0, 10)
            critical_incidents_24h = random.randint(0, 2)
            
            prompt = f"""
            Gere um resumo de monitoramento global para o ambiente da Synapse Forge.
            Considere as seguintes métricas simuladas:
            - Monitores ativos: {total_active_monitors}
            - Alertas recentes: {total_recent_alerts}
            - Incidentes críticos (últimas 24h): {critical_incidents_24h}

            Sua resposta deve ser um JSON estritamente conforme o modelo AMSGlobalSummary Pydantic.
            """
            system_message = "Você é o Agente de Monitoramento e Suporte (AMS) da Synapse Forge. Sua função é fornecer resumos de status de monitoramento global e por projeto, alertar sobre incidentes e garantir a saúde contínua dos sistemas."
            response_model_type = AMSGlobalSummary
        else: # Resumo por Projeto
            uptime = round(random.uniform(99.0, 100.0), 2)
            response_time = round(random.uniform(50.0, 300.0), 2)
            active_users = random.randint(10, 500)
            
            alerts = []
            if uptime < 99.5: alerts.append("Disponibilidade abaixo do esperado nas últimas 24h.")
            if response_time > 200: alerts.append("Tempo de resposta elevado detectado.")
            if random.random() < 0.1: alerts.append("Pico inesperado de uso de CPU/Memória.")

            prompt = f"""
            Gere um resumo de monitoramento para o projeto '{project_name}' (ID: {project_id}).
            Considere as seguintes métricas simuladas:
            - Uptime (24h): {uptime}%
            - Tempo de resposta médio: {response_time} ms
            - Usuários ativos (simulado): {active_users}
            - Alertas: {', '.join(alerts) if alerts else 'Nenhum'}

            Sua resposta deve ser um JSON estritamente conforme o modelo AMSProjectSummary Pydantic.
            """
            system_message = "Você é o Agente de Monitoramento e Suporte (AMS) da Synapse Forge. Sua função é fornecer resumos de status de monitoramento para projetos específicos, alertar sobre incidentes e garantir a saúde contínua dos sistemas."
            response_model_type = AMSProjectSummary
        
        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': prompt}
        ]

        try:
            response_obj = self.llm_simulator.chat(messages, response_model=response_model_type)
            logging.info(f"AMSAgent: Resumo de monitoramento gerado para {'global' if project_id is None else project_name}.")
            return response_obj.dict()
        except (LLMConnectionError, LLMGenerationError) as e:
            logging.error(f"AMSAgent: Falha ao gerar resumo de monitoramento para {'global' if project_id is None else project_name}. Erro: {e}")
            error_message = f"Erro ao gerar resumo de monitoramento com o LLM: {e}. Gerando dados padrão."
            logging.warning(error_message)
            
            # Fallback para dados padrão
            if project_id is None:
                return {
                    "overall_system_status": f"Degradado (Erro LLM: {e})",
                    "total_active_monitors": total_active_monitors,
                    "total_recent_alerts": total_recent_alerts,
                    "critical_incidents_24h": critical_incidents_24h,
                    "last_overall_summary": f"Falha na geração de resumo global: {error_message}"
                }
            else:
                return {
                    "overall_status": f"Degradado (Erro LLM: {e})",
                    "uptime_percentage_24h": uptime,
                    "response_time_ms": response_time,
                    "active_users": active_users,
                    "recent_alerts": [f"Falha na geração de resumo: {error_message}"],
                    "last_checked": datetime.datetime.now().isoformat()
                }
        except Exception as e:
            logging.error(f"AMSAgent: Erro inesperado ao gerar resumo de monitoramento: {e}")
            if project_id is None:
                return {
                    "overall_system_status": f"Indisponível (Erro Interno: {e})",
                    "total_active_monitors": total_active_monitors,
                    "total_recent_alerts": total_recent_alerts,
                    "critical_incidents_24h": critical_incidents_24h,
                    "last_overall_summary": f"Erro interno na geração de resumo global: {e}"
                }
            else:
                return {
                    "overall_status": f"Indisponível (Erro Interno: {e})",
                    "uptime_percentage_24h": uptime,
                    "response_time_ms": response_time,
                    "active_users": active_users,
                    "recent_alerts": [f"Erro interno na geração de resumo: {e}"],
                    "last_checked": datetime.datetime.now().isoformat()
                }
