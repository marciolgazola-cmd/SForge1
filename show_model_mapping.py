#!/usr/bin/env python3
"""
📊 VISUALIZADOR DE MAPEAMENTO AGENTES → MODELOS LLM
====================================================

Este script mostra visualmente qual LLM cada agente usa
e organiza por prioridade e tipo de tarefa.

Uso: python3 show_model_mapping.py
"""

from agent_model_mapping import AGENT_MODEL_MAP
from typing import List, Dict, Any # Adicionado para anotações de tipo

def print_header(text: str):
    """Imprimir cabeçalho"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)

def print_agent_card(agent_name: str, config: Dict[str, Any]):
    """Imprimir card de agente"""
    model_name = config['model'] # Nome exato do modelo (ex: 'llama3:8b')
    priority = config['priority']
    
    # Cores para modelos (usando código ANSI) - Atualizado para os nomes específicos
    color_map = {
        'MISTRAL': '\033[94m',    # Azul
        'LLAMA3:8B': '\033[92m',      # Verde
        'CODELLAMA:13B': '\033[93m',   # Amarelo
        'MIXTRAL:8X7B-INSTRUCT': '\033[95m' # Magenta para Mixtral
    }
    # Usar o nome do modelo em maiúsculas para o lookup
    color = color_map.get(model_name.upper(), '')
    reset = '\033[0m'
    
    # Ícone de prioridade
    priority_icon = {
        'CRITICAL': '🔴',
        'HIGH': '🟠',
        'MEDIUM': '🟡',
        'LOW': '🟢'
    }
    icon = priority_icon.get(priority, '⚪')
    
    print(f"\n  {icon} {agent_name}")
    print(f"     └─ Nome: {config['name']}")
    print(f"     └─ Modelo: {color}{model_name.upper()}{reset}") # Exibe o nome completo do modelo
    print(f"     └─ Razão: {config['reason']}")
    print(f"     └─ Tarefas: {', '.join(config['key_tasks'])}")
    print(f"     └─ Prioridade: {priority}")

def show_by_model():
    """Mostrar agentes agrupados por modelo"""
    print_header("AGENTES AGRUPADOS POR MODELO LLM")
    
    models: Dict[str, List[str]] = {}
    for agent, config in AGENT_MODEL_MAP.items():
        model = config['model']
        if model not in models:
            models[model] = []
        models[model].append(agent)
    
    # Adicionado 'mixtral:8x7b-instruct' para garantir que apareça
    for model in sorted(models.keys()):
        agents = models[model]
        print(f"\n  📌 {model.upper()} ({len(agents)} agentes)")
        print(f"     Agentes: {', '.join(sorted(agents))}")
        
        # Características - Atualizado para os novos nomes exatos
        if model == 'mistral':
            print(f"     ✨ Características:")
            print(f"        • Temperatura: 0.5 (equilibrado)")
            print(f"        • Top P: 0.85 (diversidade moderada)")
            print(f"        • Contexto: 8192 tokens")
            print(f"        • Melhor para: Versatilidade e velocidade")
        elif model == 'llama3:8b': # Nome exato
            print(f"     ✨ Características:")
            print(f"        • Temperatura: 0.3 (determinístico)")
            print(f"        • Top P: 0.9 (seleção rigorosa)")
            print(f"        • Contexto: 8192 tokens (para 8B)")
            print(f"        • Melhor para: Análise profunda, raciocínio lógico e instruções")
        elif model == 'codellama:13b': # Nome exato
            print(f"     ✨ Características:")
            print(f"        • Temperatura: 0.1 (muito preciso)")
            print(f"        • Top P: 0.95 (extremamente rigoroso)")
            print(f"        • Contexto: 16384 tokens (contexto amplo)")
            print(f"        • Melhor para: Geração e compreensão de código com alta qualidade")
        elif model == 'mixtral:8x7b-instruct': # Novo modelo
            print(f"     ✨ Características:")
            print(f"        • Temperatura: 0.7 (criativo/equilibrado)")
            print(f"        • Top P: 0.8 (diversidade moderada)")
            print(f"        • Contexto: 32768 tokens (muito amplo)")
            print(f"        • Melhor para: Raciocínio complexo, tarefas multi-passos e instruções detalhadas")


def show_by_priority():
    """Mostrar agentes agrupados por prioridade"""
    print_header("AGENTES AGRUPADOS POR PRIORIDADE")
    
    priorities: Dict[str, List[tuple[str, str]]] = {}
    for agent, config in AGENT_MODEL_MAP.items():
        priority = config['priority']
        if priority not in priorities:
            priorities[priority] = []
        priorities[priority].append((agent, config['model']))
    
    priority_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
    priority_colors = {
        'CRITICAL': '🔴 CRÍTICO',
        'HIGH': '🟠 ALTO',
        'MEDIUM': '🟡 MÉDIO',
        'LOW': '🟢 BAIXO'
    }
    
    for priority in priority_order:
        if priority in priorities:
            agents = priorities[priority]
            print(f"\n  {priority_colors[priority]} ({len(agents)} agentes)")
            for agent, model in sorted(agents):
                print(f"     • {agent:6} → {model}")

def show_detailed():
    """Mostrar detalhes de cada agente"""
    print_header("DETALHES DE TODOS OS AGENTES")
    
    for agent in sorted(AGENT_MODEL_MAP.keys()):
        config = AGENT_MODEL_MAP[agent]
        print_agent_card(agent, config)

def show_table():
    """Mostrar tabela comparativa"""
    print_header("TABELA COMPARATIVA")
    
    print(f"\n  {'Agent':<8} {'Modelo':<22} {'Prioridade':<10} {'Tarefas':<40}") # Ajustado largura do 'Modelo'
    print(f"  {'-'*8} {'-'*22} {'-'*10} {'-'*40}")
    
    for agent in sorted(AGENT_MODEL_MAP.keys()):
        config = AGENT_MODEL_MAP[agent]
        tasks = ', '.join(config['key_tasks'][:2])
        if len(config['key_tasks']) > 2:
            tasks += f" (+{len(config['key_tasks'])-2} mais)"
        
        print(f"  {agent:<8} {config['model']:<22} {config['priority']:<10} {tasks:<40}") # Ajustado largura do 'Modelo'

def show_statistics():
    """Mostrar estatísticas"""
    print_header("ESTATÍSTICAS")
    
    total_agents = len(AGENT_MODEL_MAP)
    
    models: Dict[str, int] = {}
    priorities: Dict[str, int] = {}
    for agent, config in AGENT_MODEL_MAP.items():
        model = config['model']
        priority = config['priority']
        models[model] = models.get(model, 0) + 1
        priorities[priority] = priorities.get(priority, 0) + 1
    
    print(f"\n  📊 Total de Agentes: {total_agents}")
    print(f"\n  📌 Por Modelo:")
    for model in sorted(models.keys()):
        count = models[model]
        percentage = (count / total_agents) * 100
        print(f"     • {model:<22}: {count:2} agentes ({percentage:5.1f}%)") # Ajustado largura do 'Modelo'
    
    print(f"\n  🎯 Por Prioridade:")
    priority_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
    for priority in priority_order:
        if priority in priorities:
            count = priorities[priority]
            percentage = (count / total_agents) * 100
            print(f"     • {priority:10}: {count:2} agentes ({percentage:5.1f}%)")

def main():
    """Menu principal"""
    print("\n" + "="*80)
    print("  📊 VISUALIZADOR: MAPEAMENTO AGENTES → MODELOS LLM")
    print("="*80)
    print("\n  Escolha uma opção:\n")
    print("    1. Ver agentes por MODELO")
    print("    2. Ver agentes por PRIORIDADE")
    print("    3. Ver DETALHES de cada agente")
    print("    4. Ver TABELA comparativa")
    print("    5. Ver ESTATÍSTICAS")
    print("    6. Ver TUDO")
    print("    0. SAIR\n")
    
    choice = input("  Opção (0-6): ").strip()
    
    if choice == '1':
        show_by_model()
    elif choice == '2':
        show_by_priority()
    elif choice == '3':
        show_detailed()
    elif choice == '4':
        show_table()
    elif choice == '5':
        show_statistics()
    elif choice == '6':
        show_by_model()
        show_by_priority()
        show_detailed()
        show_table()
        show_statistics()
    elif choice == '0':
        print("\n  Até logo! 👋\n")
        return
    else:
        print("\n  ❌ Opção inválida!\n")
        return
    
    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    import sys
    
    # Se tiver argumento na linha de comando, executar automaticamente
    if len(sys.argv) > 1:
        if sys.argv[1] == 'by-model':
            show_by_model()
        elif sys.argv[1] == 'by-priority':
            show_by_priority()
        elif sys.argv[1] == 'details':
            show_detailed()
        elif sys.argv[1] == 'table':
            show_table()
        elif sys.argv[1] == 'stats':
            show_statistics()
        elif sys.argv[1] == 'all':
            show_by_model()
            show_by_priority()
            show_detailed()
            show_table()
            show_statistics()
        print()
    else:
        # Menu interativo
        while True:
            main()
