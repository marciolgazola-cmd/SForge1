"""
Mapeamento de Agentes → Modelos LLM Recomendados

Este arquivo define qual modelo LLM cada agente da Synapse Forge deve usar,
baseado no propósito, complexidade e tipo de tarefa de cada agente.

Modelos Disponíveis:
- mistral: Versátil, bom balanço entre qualidade e velocidade (padrão)
- llama3: Análise profunda, raciocínio lógico detalhado
- codellama: Especializado em geração de código
"""

from typing import Dict, Any

# Mapeamento central: agente -> configuração
AGENT_MODEL_MAP: Dict[str, Dict[str, Any]] = {
    # ============================================================
    # AGENTES DE ANÁLISE E DESIGN
    # ============================================================
    
    'ARA': {
        'name': 'Agente de Análise de Requisitos',
        'model': 'llama3',
        'reason': 'Análise profunda de requisitos requer raciocínio lógico estruturado',
        'key_tasks': ['analyze_requirements'],
        'priority': 'HIGH',
    },
    
    'AAD': {
        'name': 'Agente de Arquitetura e Design',
        'model': 'mistral',
        'reason': 'Design de soluções necessita versátil e decisões coerentes',
        'key_tasks': ['design_solution'],
        'priority': 'HIGH',
    },
    
    # ============================================================
    # AGENTES DE DESENVOLVIMENTO
    # ============================================================
    
    'ADEX': {
        'name': 'Agente de Desenvolvimento (Código)',
        'model': 'codellama',
        'reason': 'Especializado em geração de código com melhor qualidade e sintaxe',
        'key_tasks': ['generate_code'],
        'priority': 'CRITICAL',
    },
    
    # ============================================================
    # AGENTES DE QUALIDADE E SEGURANÇA
    # ============================================================
    
    'AQT': {
        'name': 'Agente de Qualidade e Testes',
        'model': 'llama3',
        'reason': 'Análise de testes e cobertura requer raciocínio detalhado',
        'key_tasks': ['generate_quality_report'],
        'priority': 'HIGH',
    },
    
    'ASE': {
        'name': 'Agente de Segurança',
        'model': 'llama3',
        'reason': 'Auditoria de segurança requer análise profunda e minuciosa',
        'key_tasks': ['generate_security_report'],
        'priority': 'CRITICAL',
    },
    
    # ============================================================
    # AGENTES DE GESTÃO E DOCUMENTAÇÃO
    # ============================================================
    
    'AGP': {
        'name': 'Agente de Gerenciamento de Projetos',
        'model': 'mistral',
        'reason': 'Estimativas e planejamento beneficiam de versátil e velocidade',
        'key_tasks': ['estimate_project'],
        'priority': 'HIGH',
    },
    
    'ADO': {
        'name': 'Agente de Documentação',
        'model': 'mistral',
        'reason': 'Documentação em português requer clareza e estrutura',
        'key_tasks': ['generate_documentation'],
        'priority': 'MEDIUM',
    },
    
    'ANP': {
        'name': 'Agente de Negócios e Propostas',
        'model': 'mistral',
        'reason': 'Propostas comerciais precisam ser persuasivas e estruturadas',
        'key_tasks': ['generate_proposal'],
        'priority': 'MEDIUM',
    },
    
    # ============================================================
    # AGENTES DE MONITORAMENTO E INFRAESTRUTURA
    # ============================================================
    
    'AMS': {
        'name': 'Agente de Monitoramento de Sistemas',
        'model': 'mistral',
        'reason': 'Análise de métricas simples, velocidade importante',
        'key_tasks': ['monitor_system'],
        'priority': 'LOW',
    },
    
    'AID': {
        'name': 'Agente de Infraestrutura',
        'model': 'mistral',
        'reason': 'Gerenciamento de infraestrutura não requer raciocínio profundo',
        'key_tasks': ['provision_environment', 'configure_backups', 'get_infrastructure_status'],
        'priority': 'LOW',
    },
}


def get_agent_model(agent_name: str) -> str:
    """
    Retorna o modelo recomendado para um agente.
    
    :param agent_name: Nome do agente (ex: 'ARA', 'ADEX', 'AGP')
    :return: Nome do modelo ('mistral', 'llama3', 'codellama')
    :raises KeyError: Se o agente não estiver no mapeamento
    """
    if agent_name not in AGENT_MODEL_MAP:
        raise KeyError(f"Agente '{agent_name}' não encontrado no mapeamento. Agentes disponíveis: {list(AGENT_MODEL_MAP.keys())}")
    return AGENT_MODEL_MAP[agent_name]['model']


def get_agent_info(agent_name: str) -> Dict[str, Any]:
    """
    Retorna informações completas sobre um agente e seu modelo.
    
    :param agent_name: Nome do agente
    :return: Dicionário com 'model', 'reason', 'key_tasks', 'priority'
    """
    if agent_name not in AGENT_MODEL_MAP:
        raise KeyError(f"Agente '{agent_name}' não encontrado")
    return AGENT_MODEL_MAP[agent_name]


def list_all_agents() -> Dict[str, str]:
    """
    Lista todos os agentes e seus modelos recomendados.
    
    :return: Dict {agent_name: model_name}
    """
    return {agent: config['model'] for agent, config in AGENT_MODEL_MAP.items()}


def list_agents_by_model(model: str) -> list:
    """
    Lista todos os agentes que usam um modelo específico.
    
    :param model: Nome do modelo ('mistral', 'llama3', 'codellama')
    :return: Lista de agentes
    """
    return [agent for agent, config in AGENT_MODEL_MAP.items() if config['model'].lower() == model.lower()]


if __name__ == '__main__':
    # Exemplo de uso e testes
    print("="*80)
    print("MAPEAMENTO DE AGENTES → MODELOS LLM")
    print("="*80)
    
    # Listar todos os agentes
    print("\n📊 TODOS OS AGENTES:\n")
    for agent, config in sorted(AGENT_MODEL_MAP.items()):
        print(f"  {agent:6} → {config['model']:10} | {config['name']}")
        print(f"          Razão: {config['reason']}")
        print(f"          Prioridade: {config['priority']}\n")
    
    # Agrupar por modelo
    print("\n📋 AGRUPADO POR MODELO:\n")
    for model in ['mistral', 'llama3', 'codellama']:
        agents = list_agents_by_model(model)
        print(f"  {model.upper()}: {', '.join(agents)}")
    
    print("\n" + "="*80)
    print("Para usar o mapeamento nos agentes:")
    print("  from agent_model_mapping import get_agent_model")
    print("  model = get_agent_model('ADEX')  # Retorna 'codellama'")
    print("="*80)
