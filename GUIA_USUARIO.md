# 📚 GUIA DE USO - CognitoLink v2.0 (Interface Melhorada)

## 🎯 Visão Geral

CognitoLink é o centro de comando visual da SForge, permitindo gerenciar toda a orquestração de propostas e projetos de forma intuitiva através da interface web com Streamlit.

---

## 🚀 INICIALIZAÇÃO

### Pré-requisitos
- Python 3.12+
- Ollama rodando localmente com modelos: llama3, mistral, codellama
- Banco de dados: synapse_forge.db (criado automaticamente)

### Iniciar a Aplicação
```bash
cd /home/marcio-gazola/SForge1
streamlit run cognitolink.py
```

A aplicação abrirá em `http://localhost:8501`

### Tela Inicial
- **Título**: CognitoLink com ✨
- **Sidebar**: Menu de navegação com todas as opções
- **Tema**: Azul escuro moderno com ícones visuais

---

## 📝 SEÇÃO 1: ENTRADA DE REQUISITOS

### Localização
Sidebar → 📝 Entrada de Requisitos

### Propósito
Coletar informações do cliente para gerar proposta via MOAI

### Como Usar

#### 1️⃣ Preencha os Campos Obrigatórios
- **🏢 Nome do Projeto** *: Ex: "Sistema de Gestão de Clientes"
- **👤 Nome do Cliente** *: Ex: "Acme Corporation"
- **❓ Problema de Negócio** *: Descrição detalhada do problema

> *Campos marcados com asterisco são obrigatórios

#### 2️⃣ Preencha os Campos Opcionais
- **🎯 Público-alvo**: Quem são os usuários?
- **📍 Objetivos do Projeto**: O que a solução deve alcançar?
- **✨ Funcionalidades Esperadas**: Lista de features principais
- **⚠️ Restrições e Requisitos**: Orçamento, prazo, limites técnicos

#### 3️⃣ Gere a Proposta
Clique em **🚀 Gerar Proposta via MOAI**

### Validações
- ❌ Se campos obrigatórios vazios: "Por favor, preencha: Nome do Projeto, Cliente e Problema de Negócio"
- ✅ Se tudo OK: MOAI orquestra agentes e gera proposta
- ✅ Proposta criada com sucesso: Redirecionado para Central de Aprovações

### Tempo Esperado
- Geração de proposta: 30-60 segundos (depende dos LLMs)

---

## ✅ SEÇÃO 2: CENTRAL DE APROVAÇÕES

### Localização
Sidebar → ✅ Central de Aprovações (X pendentes)

### Propósito
Revisar, editar e aprovar/rejeitar propostas geradas

### Interface

#### 🔹 Abas de Status
1. **⏳ Pendentes**: Propostas aguardando revisão
2. **✅ Aprovadas**: Propostas já aprovadas
3. **❌ Rejeitadas**: Propostas rejeitadas

### Como Usar

#### 1️⃣ Revisar Proposta Pendente

Clique no expander da proposta para expandir:
```
📄 Título da Proposta (ID: abc123...)
```

Será exibido:
- **🔍 Entendimento do Problema**: Análise feita pelo MOAI
- **💡 Solução Proposta**: Solução gerada
- **📊 Escopo**: O que será desenvolvido
- **🛠️ Tecnologias**: Stack recomendado
- **💰 Estimativas**: Valor e prazo
- **📋 Termos e Condições**: Condições comerciais

#### 2️⃣ Editar Proposta (Opcional)

Clique em **✏️ Editar**:

O formulário de edição aparece com:
- Seção de informações básicas
- Seção de análise e solução
- Seção de detalhes técnicos

**Editar e Salvar**:
1. Modifique os campos desejados
2. Clique em **💾 Salvar Alterações**
3. Proposta atualizada com sucesso

#### 3️⃣ Aprovar Proposta

Clique em **✅ Aprovar**:
1. Sistema exibe: "⏳ Aprovando proposta..."
2. Sucesso: "✅ Proposta aprovada! Projeto iniciado."
3. Proposta move para aba "✅ Aprovadas"
4. Projeto criado automaticamente

#### 4️⃣ Rejeitar Proposta

Clique em **❌ Rejeitar**:
1. Sistema exibe: "⏳ Rejeitando proposta..."
2. Aviso: "⚠️ Proposta rejeitada."
3. Proposta move para aba "❌ Rejeitadas"

### Dicas
- 💡 Sempre revise o entendimento do problema
- 💡 Edite se necessário ajustar escopo ou estimativas
- 💡 Tecnologias sugeridas vêm do agente especializado
- 💡 Termos e condições são gerados pelo MOAI

---

## 🚧 SEÇÃO 3: GESTÃO DE PROJETOS

### Localização
Sidebar → 🚧 Gestão de Projetos

### Propósito
Gerenciar projetos ativos após aprovação

### Interface

#### 1️⃣ Seleção de Projeto
- Dropdown: "Selecione um Projeto para Gerenciar"
- Escolha o projeto pela lista

#### 2️⃣ Métricas do Projeto

Quando projeto selecionado, 4 cards aparecem:
- **📊 Progresso**: X% (0-100%)
- **Status**: 🟢 Ativo / 🟡 Em Pausa / ✅ Concluído / ⛔ Cancelado
- **👤 Cliente**: Nome do cliente
- **📅 Iniciado**: Data de início

#### 3️⃣ Abas de Gestão

**Aba 📋 Detalhes**:
- Identificação completa do projeto
- Cronograma (início, conclusão se houver)
- Barra de progresso visual

**Aba 📄 Proposta Original**:
- Título e descrição
- Análise completa do problema
- Solução, escopo, tecnologias
- Estimativas e termos

**Aba ✏️ Editar**:
- Editar dados básicos do projeto (nome, cliente, status, progresso)
- Editar especificações da proposta
- Salvar tudo de uma vez ou cancelar

### Como Editar Projeto

1. Selecione o projeto
2. Vá para aba **✏️ Editar**
3. Modifique:
   - **📝 Nome do Projeto**
   - **👤 Nome do Cliente**
   - **Status**: active / on hold / completed / cancelled
   - **Progresso**: 0-100% (slider)

4. Modifique a proposta (opcional):
   - Título, escopo, tecnologias
   - Problema e solução
   - Estimativas

5. Clique **💾 Salvar Todas as Alterações**

### Dicas
- 💡 Atualize progresso regularmente
- 💡 Marque como "on hold" se necessário pausa
- 💡 Sistema marca data de conclusão automaticamente
- 💡 Mudanças em proposta afetam referência do projeto

---

## 📊 SEÇÃO 4: DASHBOARD EXECUTIVO

### Localização
Sidebar → 🌟 Dashboard Executivo

### Exibições
- **KPIs**: Total de propostas, taxa de aprovação, tempo médio
- **Gráficos**: Distribuição de status, timeline
- **Atividades**: Log de operações recentes

### Uso
- Visão geral do estado da SForge
- Métricas de desempenho
- Identificar gargalos

---

## ⏳ SEÇÃO 5: LINHA DO TEMPO DO PROJETO

### Localização
Sidebar → ⏳ Linha do Tempo do Projeto

### Exibições
- Timeline visual de eventos
- Milestones completados
- Próximos passos

---

## 📊 SEÇÃO 6: RELATÓRIOS DETALHADOS

### Localização
Sidebar → 📊 Relatórios Detalhados

### Relatórios Disponíveis
- **Por Status**: Propostas/Projetos agrupados
- **Por Cliente**: Histórico de trabalhos
- **Financeiro**: Valores gerados, aprovados, realizados
- **Temporal**: Distribuição por período

### Exportar
Dados podem ser copiados ou exportados para análise

---

## 💬 SEÇÃO 7: COMUNICAÇÃO COM MOAI

### Localização
Sidebar → 💬 Comunicação com MOAI

### Uso
- Chat interativo com MOAI
- Fazer perguntas sobre propostas/projetos
- Obter análises rápidas
- Gerar conteúdo adicional

### Exemplos de Perguntas
- "Qual é o escopo do projeto XYZ?"
- "Qual tecnologia você recomenda para o cliente ABC?"
- "Qual é a taxa de aprovação este mês?"

---

## 📚 SEÇÃO 8: DOCUMENTAÇÃO

### Localização
Sidebar → 📚 Módulo de Documentação

### Conteúdo
- Guias de referência
- Documentação técnica
- Padrões de desenvolvimento
- Melhores práticas

---

## 🎨 PERSONALIZAÇÃO E CONFIGURAÇÕES

### Tema
- Automático: Tema azul escuro aplicado
- Cores: Azul (#1081BA), Cinza, Branco
- Emojis: Visuais em todos os elementos

### Responsividade
- **Desktop**: Layout completo com múltiplas colunas
- **Tablet**: Layout adaptado com 2 colunas
- **Mobile**: Layout com 1 coluna, elementos reordenados

### Acessibilidade
- Cores contrastantes
- Textos descritivos
- Suporte a emojis para ícones rápidos

---

## ⚠️ MENSAGENS E ALERTAS

### ✅ Verde - Sucesso
```
✅ Proposta 'XXX' gerada com sucesso!
✅ Proposta aprovada! Projeto iniciado.
✅ Projeto e proposta atualizados com sucesso!
```

### ❌ Vermelho - Erro
```
❌ Por favor, preencha os campos obrigatórios
❌ Ocorreu um erro ao gerar a proposta
❌ Erro ao salvar alterações
```

### 🟡 Amarelo - Aviso
```
⚠️ Proposta rejeitada.
⚠️ Verifique os logs do MOAI.
⚠️ Proposta associada não encontrada.
```

### ℹ️ Azul - Informação
```
ℹ️ Nenhuma proposta pendente. Todas foram revisadas!
ℹ️ Nenhum projeto ativo para gerenciar.
```

---

## 🔄 FLUXO COMPLETO

```
1. ENTRADA DE REQUISITOS
   ↓
   Preencher formulário
   Gerar proposta via MOAI
   ↓
2. CENTRAL DE APROVAÇÕES
   ↓
   Revisar proposta
   Editar (se necessário)
   Aprovar ou Rejeitar
   ↓
3. GESTÃO DE PROJETOS (se aprovado)
   ↓
   Acompanhar progresso
   Editar dados do projeto
   Marcar como concluído
   ↓
4. RELATÓRIOS
   ↓
   Analisar métricas
   Exportar dados
```

---

## 🐛 TROUBLESHOOTING

### Problema: Formulário de Requisitos vem preenchido
**Solução**: Atualizar página (F5) - bug foi corrigido

### Problema: Erro "string_type" ao gerar proposta
**Solução**: Verificar se todos os campos obrigatórios foram preenchidos - validação foi implementada

### Problema: Proposta não salva ao editar
**Solução**:
1. Verificar se há espaço em disco
2. Verificar conexão com banco de dados
3. Tentar salvar novamente
4. Contatar administrador se persistir

### Problema: Ollama não conecta
**Solução**:
1. Verificar se Ollama está rodando: `ollama serve`
2. Verificar se modelos estão baixados: `ollama list`
3. Verificar porta (padrão 11434)

### Problema: Interface demora a carregar
**Solução**:
1. Limpar cache do navegador
2. Atualizar página
3. Verificar conexão de internet
4. Fechar outras abas abertas

---

## 💡 DICAS E BOAS PRÁTICAS

### Melhor UX
- 💡 Preencha sempre os 3 campos obrigatórios primeiro
- 💡 Revise a proposta antes de aprovar
- 💡 Edite escopo/estimativas se necessário
- 💡 Atualize progresso do projeto regularmente
- 💡 Use relatórios para acompanhar métricas

### Performance
- 💡 Não deixe muitas abas abertas
- 💡 Feche expanders após revisar
- 💡 Navegue entre seções com sidebar (não F5)
- 💡 Limite a 10+ projetos ativos para melhor performance

### Segurança
- 💡 Propostas são armazenadas em banco SQLite local
- 💡 Não compartilhe a pasta /SForge1 publicamente
- 💡 Backup regular do synapse_forge.db
- 💡 Senhas e dados sensíveis não são exibidos

---

## 📞 SUPORTE

Para problemas ou sugestões:
1. Consulte o arquivo `MELHORIAS_INTERFACE_V1.md` (documentação técnica)
2. Verifique o `CHECKLIST_TESTES.md` (testes implementados)
3. Contate o administrador do sistema

---

**Versão**: 2.0 (Interface Melhorada)
**Última Atualização**: 2024
**Status**: ✅ Pronto para uso

Aproveite a SForge! 🚀✨

