console.log("Script.js carregado com sucesso!");
//alert("Bem-vindo ao SForge1!");

const meuBotao = document.getElementById("meuBotao");
const resetBotao = document.getElementById("resetBotao");
const mensagemParagrafo = document.getElementById("mensagem");

let contador = 0;

function atualizarMensagemContador() {
    if (contador === 0) {
        mensagemParagrafo.textContent = "Clique no botão para começar a contar! ��";
    } else {
        mensagemParagrafo.textContent = `Você clicou ${contador} vezes! ��`;
    }
}

atualizarMensagemContador();

meuBotao.addEventListener("click", () => {
    contador++;
    atualizarMensagemContador();
});

resetBotao.addEventListener("click", () => {
    contador = 0;
    atualizarMensagemContador();
});

const campoEntrada = document.getElementById("campoEntrada");
const exibirEntrada = document.getElementById("exibirEntrada");

campoEntrada.addEventListener("input", (event) => {
    exibirEntrada.textContent = `Você está digitando: ${event.target.value}`;
});

// Lógica para a lista de tarefas
const campoTarefa = document.getElementById("campoTarefa");
const adicionarTarefaBotao = document.getElementById("adicionarTarefa");
const listaDeTarefas = document.getElementById("listaDeTarefas");
const contadorTotalTarefas = document.getElementById("contadorTotalTarefas"); // NOVO
const contadorPendentes = document.getElementById("contadorPendentes");       // NOVO

// --- Funções para Local Storage e Contadores ---
function salvarTarefas() {
    const tarefas = [];
    listaDeTarefas.querySelectorAll("li").forEach(item => {
        tarefas.push({
            text: item.querySelector("span").textContent,
            concluida: item.classList.contains("concluida")
        });
    });
    localStorage.setItem("tarefasSForge1", JSON.stringify(tarefas));
}

function atualizarContadores() { // NOVA FUNÇÃO
    const total = listaDeTarefas.children.length;
    const concluidas = listaDeTarefas.querySelectorAll(".concluida").length;
    const pendentes = total - concluidas;

    contadorTotalTarefas.textContent = total;
    contadorPendentes.textContent = pendentes;
}

function carregarTarefas() {
    const tarefasSalvas = localStorage.getItem("tarefasSForge1");
    if (tarefasSalvas) {
        const tarefas = JSON.parse(tarefasSalvas);
        tarefas.forEach(tarefa => {
            const novoItemLista = document.createElement("li");
            
            const spanTexto = document.createElement("span");
            spanTexto.textContent = tarefa.text;
            if (tarefa.concluida) {
                novoItemLista.classList.add("concluida");
            }
            spanTexto.addEventListener("click", () => {
                novoItemLista.classList.toggle("concluida");
                salvarTarefas();
                atualizarContadores(); // Chamada para atualizar contadores
            });

            const botaoExcluir = document.createElement("button");
            botaoExcluir.textContent = "❌";
            botaoExcluir.classList.add("btn-excluir");
            botaoExcluir.addEventListener("click", () => {
                listaDeTarefas.removeChild(novoItemLista);
                salvarTarefas();
                atualizarContadores(); // Chamada para atualizar contadores
            });

            novoItemLista.appendChild(spanTexto);
            novoItemLista.appendChild(botaoExcluir);
            listaDeTarefas.appendChild(novoItemLista);
        });
    }
    atualizarContadores(); // Chamada inicial para atualizar contadores após carregar
}

function adicionarNovaTarefa() {
    const textoTarefa = campoTarefa.value.trim();

    if (textoTarefa !== "") {
        const novoItemLista = document.createElement("li");
        
        const spanTexto = document.createElement("span");
        spanTexto.textContent = textoTarefa;
        spanTexto.addEventListener("click", () => {
            novoItemLista.classList.toggle("concluida");
            salvarTarefas();
            atualizarContadores(); // Chamada para atualizar contadores
        });

        const botaoExcluir = document.createElement("button");
        botaoExcluir.textContent = "❌";
        botaoExcluir.classList.add("btn-excluir");
        botaoExcluir.addEventListener("click", () => {
            listaDeTarefas.removeChild(novoItemLista);
            salvarTarefas();
            atualizarContadores(); // Chamada para atualizar contadores
        });

        novoItemLista.appendChild(spanTexto);
        novoItemLista.appendChild(botaoExcluir);
        listaDeTarefas.appendChild(novoItemLista);
        campoTarefa.value = "";
        salvarTarefas();
        atualizarContadores(); // Chamada para atualizar contadores
    } else {
        alert("Por favor, digite uma tarefa!");
    }
}

adicionarTarefaBotao.addEventListener("click", adicionarNovaTarefa);

campoTarefa.addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
        adicionarNovaTarefa();
    }
});

carregarTarefas(); // Garante que as tarefas sejam carregadas (e os contadores atualizados) no início