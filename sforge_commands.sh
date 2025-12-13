#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# QUICK REFERENCE - Comandos de Otimização Synapse Forge
# ═══════════════════════════════════════════════════════════════════════

# 📌 VERIFICAÇÃO RÁPIDA

## Status Geral
alias sforge-status='echo "📊 Status Synapse Forge:" && echo "Ollama:" && pgrep -f "ollama serve" && echo "  ✓ Rodando" || echo "  ✗ Parado" && echo "Streamlit:" && pgrep -f "streamlit" && echo "  ✓ Rodando" || echo "  ✗ Parado" && nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader'

## Verificar GPU
alias gpu-check='nvidia-smi --query-gpu=index,name,driver_version,compute_cap,memory.total,memory.used --format=csv,noheader'

## Verificar Modelos Disponíveis
alias models-list='ollama list'

## Verificar CPU Threads
alias cpu-threads='cat /proc/cpuinfo | grep processor | wc -l'

# ───────────────────────────────────────────────────────────────────────
# 🚀 INICIAR SERVIÇOS

## Start Ollama (background)
alias ollama-start='nohup ollama serve > ~/.ollama/ollama.log 2>&1 &'

## Stop Ollama
alias ollama-stop='pkill -f "ollama serve"'

## Start Streamlit
alias streamlit-start='streamlit run cognitolink.py --server.port 8501 --logger.level=error &'

## Stop Streamlit
alias streamlit-stop='pkill -f streamlit'

## Start All Services
function start-sforge() {
    echo "🚀 Iniciando Synapse Forge..."
    
    # Limpar pids antigos
    pkill -f "ollama serve" 2>/dev/null || true
    pkill -f streamlit 2>/dev/null || true
    sleep 1
    
    # Iniciar Ollama
    echo "  1/3 Ollama..."
    nohup ollama serve > ~/.ollama/ollama.log 2>&1 &
    sleep 3
    
    # Verificar
    if pgrep -f "ollama serve" > /dev/null; then
        echo "  ✓ Ollama iniciado"
    else
        echo "  ✗ Ollama falhou"
        tail ~/.ollama/ollama.log
        return 1
    fi
    
    # Iniciar Streamlit
    echo "  2/3 Streamlit..."
    nohup streamlit run cognitolink.py --server.port 8501 > ~/.streamlit/streamlit.log 2>&1 &
    sleep 2
    
    if pgrep -f streamlit > /dev/null; then
        echo "  ✓ Streamlit iniciado"
    else
        echo "  ✗ Streamlit falhou"
        tail ~/.streamlit/streamlit.log
        return 1
    fi
    
    echo "  3/3 Verificando conectividade..."
    sleep 2
    
    # Verificar GPU
    GPU_CHECK=$(nvidia-smi 2>/dev/null | grep -o "NVIDIA" || echo "GPU NOT FOUND")
    if [ "$GPU_CHECK" = "NVIDIA" ]; then
        echo "  ✓ GPU detectada"
    fi
    
    # Teste Ollama
    TEST=$(curl -s http://localhost:11434/api/status | grep -o '"status"' || echo "FAIL")
    if [ "$TEST" = '"status"' ]; then
        echo "  ✓ Ollama respondendo"
    else
        echo "  ✗ Ollama não respondendo"
    fi
    
    echo ""
    echo "✅ Serviços iniciados!"
    echo ""
    echo "🌐 Acesso:"
    echo "   • Streamlit: http://192.168.15.20:8501"
    echo "   • Ollama API: http://localhost:11434"
    echo ""
}

## Stop All Services
function stop-sforge() {
    echo "🛑 Parando Synapse Forge..."
    pkill -f "ollama serve" 2>/dev/null && echo "  ✓ Ollama parado" || echo "  • Ollama já parado"
    pkill -f streamlit 2>/dev/null && echo "  ✓ Streamlit parado" || echo "  • Streamlit já parado"
    echo "✅ Tudo parado"
}

# ───────────────────────────────────────────────────────────────────────
# 🧪 TESTES

## Teste Ollama
function test-ollama() {
    echo "🧪 Testando Ollama..."
    
    MODEL=${1:-mixtral}
    
    echo "  Modelo: $MODEL"
    echo "  Enviando teste..."
    
    RESPONSE=$(curl -s -X POST http://localhost:11434/api/chat \
      -H "Content-Type: application/json" \
      -d "{
        \"model\": \"$MODEL\",
        \"messages\": [{\"role\": \"user\", \"content\": \"Diga 'Oi!' em uma palavra\"}],
        \"stream\": false
      }")
    
    if echo "$RESPONSE" | grep -q "message"; then
        echo "  ✓ Resposta recebida"
        CONTENT=$(echo "$RESPONSE" | grep -o '"content":"[^"]*' | head -1 | cut -d'"' -f4)
        echo "  📝 Resposta: $CONTENT"
        return 0
    else
        echo "  ✗ Falha na resposta"
        echo "     $RESPONSE"
        return 1
    fi
}

## Teste Performance
function test-performance() {
    echo "📊 Testando Performance..."
    
    MODEL=${1:-mixtral}
    ITERATIONS=${2:-3}
    
    echo "  Modelo: $MODEL"
    echo "  Iterações: $ITERATIONS"
    echo ""
    
    TOTAL_TIME=0
    
    for i in $(seq 1 $ITERATIONS); do
        echo "  Teste $i/$ITERATIONS..."
        START=$(date +%s%N)
        
        curl -s -X POST http://localhost:11434/api/chat \
          -H "Content-Type: application/json" \
          -d "{
            \"model\": \"$MODEL\",
            \"messages\": [{\"role\": \"user\", \"content\": \"Teste de latência $i\"}],
            \"stream\": false
          }" > /dev/null
        
        END=$(date +%s%N)
        ELAPSED=$(( (END - START) / 1000000 ))  # Converter ns → ms
        ELAPSED_SEC=$(echo "scale=2; $ELAPSED / 1000" | bc)
        
        echo "    Tempo: ${ELAPSED_SEC}s"
        TOTAL_TIME=$(echo "$TOTAL_TIME + $ELAPSED_SEC" | bc)
    done
    
    AVG_TIME=$(echo "scale=2; $TOTAL_TIME / $ITERATIONS" | bc)
    echo ""
    echo "  📈 Tempo médio: ${AVG_TIME}s"
}

## Monitorar GPU em tempo real
function monitor-gpu() {
    echo "📡 Monitorando GPU (Ctrl+C para sair)..."
    watch -n 1 'nvidia-smi --query-gpu=index,name,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv,noheader'
}

## Monitorar CPU/GPU
function monitor-system() {
    echo "📡 Monitorando Sistema (Ctrl+C para sair)..."
    watch -n 1 'echo "=== GPU ===" && nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader && echo "=== CPU ===" && top -bn1 | head -3'
}

# ───────────────────────────────────────────────────────────────────────
# 🔧 MAINTENANCE

## Limpar cache Ollama
function clean-ollama-cache() {
    echo "🧹 Limpando cache Ollama..."
    pkill -f "ollama serve" 2>/dev/null || true
    sleep 1
    rm -rf ~/.ollama/cache
    mkdir -p ~/.ollama/cache
    echo "✓ Cache limpo"
}

## Download modelo
function download-model() {
    MODEL=$1
    if [ -z "$MODEL" ]; then
        echo "❌ Uso: download-model <model_name>"
        echo "   Exemplos: mixtral, llama2, neural-chat"
        return 1
    fi
    
    echo "📥 Baixando $MODEL..."
    ollama pull "$MODEL"
    echo "✓ Download concluído"
}

## Remover modelo
function remove-model() {
    MODEL=$1
    if [ -z "$MODEL" ]; then
        echo "❌ Uso: remove-model <model_name>"
        return 1
    fi
    
    echo "🗑️  Removendo $MODEL..."
    ollama rm "$MODEL"
    echo "✓ Modelo removido"
}

## Espaço em disco
function disk-space() {
    echo "💾 Uso de Espaço:"
    du -sh ~/.ollama
    du -sh ~/.streamlit
    du -sh ~/.cache
    echo ""
    echo "📊 Espaço disponível:"
    df -h ~/.ollama | tail -1
}

# ───────────────────────────────────────────────────────────────────────
# 📖 DOCUMENTAÇÃO

## Mostrar ajuda
function sforge-help() {
    cat << 'HELPEOF'
╔══════════════════════════════════════════════════════════════════════════╗
║          🚀 SYNAPSE FORGE - QUICK REFERENCE v3.0                       ║
╚══════════════════════════════════════════════════════════════════════════╝

📍 INICIAR/PARAR:
  start-sforge          - Iniciar todos os serviços
  stop-sforge           - Parar todos os serviços
  ollama-start/stop     - Controlar Ollama
  streamlit-start/stop  - Controlar Streamlit

🧪 TESTES:
  test-ollama [model]          - Testar resposta Ollama
  test-performance [model] [n] - Testar latência (n iterações)
  monitor-gpu                  - Monitorar GPU em tempo real
  monitor-system               - Monitorar CPU + GPU

⚙️  MANUTENÇÃO:
  download-model <name>   - Baixar novo modelo
  remove-model <name>     - Remover modelo
  clean-ollama-cache      - Limpar cache
  disk-space              - Ver uso de disco

✅ STATUS:
  sforge-status    - Verificar status geral
  gpu-check        - Verificar GPU
  models-list      - Listar modelos disponíveis
  cpu-threads      - Ver cores CPU

📚 DOCUMENTAÇÃO:
  cat OTIMIZACOES_v3_MIXTRAL.md  - Guia completo
  sforge-help                     - Esta ajuda

HELPEOF
}

# ═══════════════════════════════════════════════════════════════════════

# Mostrar ajuda ao carregar
echo "✅ Synapse Forge Quick Commands Loaded!"
echo "   Execute: sforge-help"
