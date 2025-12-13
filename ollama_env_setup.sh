#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════
# OTIMIZAÇÕES PARA OLLAMA - Ryzen 7800X3D + RTX 4070 Ti Super
# ═══════════════════════════════════════════════════════════════════════

echo "🔧 Configurando ambiente Ollama para Ryzen 7800X3D + RTX 4070 Ti Super..."

# ───────────────────────────────────────────────────────────────────────
# 1. VARIÁVEIS DE AMBIENTE - GPU & THREADING
# ───────────────────────────────────────────────────────────────────────

export OLLAMA_NUM_GPU=1                    # Use 1 GPU (a que você tem)
export OLLAMA_NUM_THREAD=8                 # 8 cores físicos (máximo do Ryzen 7800X3D X3D)
export OLLAMA_KEEP_ALIVE=3600              # Manter modelo 1h em memória
export OLLAMA_MAX_LOADED_MODELS=2          # Até 2 modelos em VRAM simultaneamente
export OLLAMA_GPU_TOTALLY_FREE=false       # Não liberar GPU entre requisições
export OLLAMA_DEBUG=0                      # Desabilitar debug (overhead)

# ───────────────────────────────────────────────────────────────────────
# 2. VERIFICAR CONFIGURAÇÃO
# ───────────────────────────────────────────────────────────────────────

echo ""
echo "📊 Configurações Aplicadas:"
echo "├─ GPU: ${OLLAMA_NUM_GPU}"
echo "├─ CPU Threads: ${OLLAMA_NUM_THREAD}"
echo "├─ Keep Alive: ${OLLAMA_KEEP_ALIVE}s"
echo "├─ Max Loaded Models: ${OLLAMA_MAX_LOADED_MODELS}"
echo "└─ GPU Lock: ${OLLAMA_GPU_TOTALLY_FREE}"

# ───────────────────────────────────────────────────────────────────────
# 3. CRIAR ARQUIVO DE CONFIGURAÇÃO PERSISTENTE
# ───────────────────────────────────────────────────────────────────────

OLLAMA_CONFIG_DIR="/etc/ollama"
OLLAMA_ENV_FILE="$OLLAMA_CONFIG_DIR/ollama.env"

if [ ! -d "$OLLAMA_CONFIG_DIR" ]; then
    sudo mkdir -p "$OLLAMA_CONFIG_DIR"
    echo "✓ Diretório de config criado: $OLLAMA_CONFIG_DIR"
fi

sudo tee "$OLLAMA_ENV_FILE" > /dev/null << 'CONFIGEOF'
# ═══════════════════════════════════════════════════════════════════════
# OLLAMA Configuration - Ryzen 7800X3D + RTX 4070 Ti Super
# ═══════════════════════════════════════════════════════════════════════

# GPU Configuration
OLLAMA_NUM_GPU=1
OLLAMA_NUM_THREAD=8

# Memory & Cache Management
OLLAMA_KEEP_ALIVE=3600
OLLAMA_MAX_LOADED_MODELS=2
OLLAMA_GPU_TOTALLY_FREE=false

# Performance Tuning
OLLAMA_DEBUG=0

# Model Server
OLLAMA_HOST=0.0.0.0:11434

CONFIGEOF

echo "✓ Arquivo de config criado: $OLLAMA_ENV_FILE"

# ───────────────────────────────────────────────────────────────────────
# 4. VERIFICAR GPU
# ───────────────────────────────────────────────────────────────────────

echo ""
echo "🎮 Verificando GPU..."
nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv,noheader || \
echo "⚠ NVIDIA GPU não detectado. Verificar drivers."

echo ""
echo "✅ Setup concluído!"
echo ""
echo "Para aplicar as configurações:"
echo "  1. Reinicie Ollama: systemctl restart ollama"
echo "  2. Ou rode em terminal: ollama serve"
echo ""
