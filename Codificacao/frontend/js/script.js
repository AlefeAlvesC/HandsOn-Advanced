// script.js

// Importação do SDK já ocorre via <script> no HTML
//Configuaçao do Firebase
const firebaseConfig = {
    apiKey: "SUA_API_KEY",
    authDomain: "DOMINIO_DO_SEU_FIREBASE",
    databaseURL: "URL_DO_SEU_FIREBASE",
    projectId: "ID_DO_SEU_PROJETO_NO_FIREBASE",
    storageBucket: "STORA_DO_FIREBASE",
    messagingSenderId: "MESSAGING_DO_FIREBASE",
    appId: "ID_DO_APP_DO_FIREBASE"
};

// Inicializar o Firebase
firebase.initializeApp(firebaseConfig);

// Referência ao Realtime Database
const database = firebase.database();

// Arquivo reservado para funcionalidades futuras.
//console.log("Página carregada com sucesso.");

// Quando o DOM estiver carregado
document.addEventListener("DOMContentLoaded", () => {
    const homeIcon = document.getElementById("home-icon");
    const exitIcon = document.getElementById("exit-icon");
    const undoIcon = document.getElementById("undo-icon")
    const tabela_pendentes = document.getElementById("tabela-pendentes");
    const tabela_entregas = document.getElementById("tabela-entregas");
    
    const btnPendentes = document.getElementById("btn-pendentes");
    const btnConcluidas = document.getElementById("btn-concluidas");
    const secaoPendentes = document.getElementById("secao-pendentes");
    const secaoConcluidas = document.getElementById("secao-concluidas");

    const statusDiv = document.getElementById("blockchain-status");
    
    //Verifica integridade da blockchain
    fetch("SUA_CONEXÃO_LOCAL:5000/validar_blockchain")
    .then(res => res.json())
    .then(data => {
        
        if (data.valido) {
            statusDiv.textContent = "Blockchain íntegra ✅";
            statusDiv.style.color = "green";
        } else {
            statusDiv.textContent = "Blockchain corrompida ❌";
            statusDiv.style.color = "red";
        }
    })
    .catch(error => {
        console.error("Erro ao verificar integridade da blockchain:", error);
        statusDiv.textContent = "Erro ao validar blockchain ⚠️";
        statusDiv.style.color = "orange";
    });



    // Redireciona para a página inicial (index.html)
    if (homeIcon) {
      homeIcon.addEventListener("click", () => {
            window.location.href = "index.html";
      });
    }

    if (exitIcon) {
        exitIcon.addEventListener("click", () => {
            window.location.href = "index.html";
        });
    }
    
    // Se estiver na nova-entrega.html, o botão exit volta para index.html
    //if (undoIcon && window.location.pathname.includes("nova-entrega.html")) {
    if (undoIcon){
        undoIcon.addEventListener("click", () => {
            window.location.href = "index.html";
      });
    }

    //Botões para tabela concluida e pendente
    if (btnPendentes && btnConcluidas && secaoPendentes && secaoConcluidas) {
        btnPendentes.addEventListener("click", () => {
            secaoPendentes.style.display = "block";
            secaoConcluidas.style.display = "none";
            btnPendentes.classList.add("ativo");
            btnConcluidas.classList.remove("ativo");
        });
    
        btnConcluidas.addEventListener("click", () => {
            secaoPendentes.style.display = "none";
            secaoConcluidas.style.display = "block";
            btnPendentes.classList.remove("ativo");
            btnConcluidas.classList.add("ativo");
        });
    }    

    const confirmarBtn = document.querySelector(".btn-programar");
    //const btnConfirmar = document.getElementById("btnConfirmar");
    
    // Se estiver na página nova-entrega.html
    if (confirmarBtn && window.location.pathname.includes("nova-entrega.html")) {
        
    
        confirmarBtn.addEventListener("click", () => {
            const sala = document.getElementById("sala").value;
            const nome = document.getElementById("nome").value;
            const medicamento = document.getElementById("medicamento").value;
            const medico = document.getElementById("medico").value;
            const horario = document.getElementById("horario").value;


        if (sala && nome && medicamento && medico && horario) {
            const novaEntregaRef = database.ref("entregas").push(); // Cria ID único
            novaEntregaRef.set({
                sala,
                nome,
                medicamento,
                medico,
                horario,
                status: "pendente"
            }).then(() => {
                // Envia os dados para o backend registrar na blockchain
                
                fetch('SUA_CONEXAO_LOCAL:5000/registrar', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        sala: sala,
                        medicamento: medicamento,
                        nome_medico: medico,
                        nome_paciente: nome,
                        horario: horario
                    })
                })

                .then(response => response.json())
                .then(data => {

                    console.log("Registro blockchain:", data);
                    alert("Entrega registrada com sucesso!");
                    window.location.href = "index.html"; // Redireciona para página principal

                }).catch((error) => {
                    console.error("Erro ao registrar na blockchain:", error);
                    alert("Erro ao registrar na blockchain. Verifique o servidor.");
                    window.location.href = "index.html";
                });
            });
        } else {
            alert("Por favor, preencha todos os campos.");
        }
        });
    }

    if (tabela_pendentes) {
        const entregasRef = firebase.database().ref("entregas").orderByChild("status").equalTo("pendente");
    
        entregasRef.on("value", (snapshot) => {
          tabela_pendentes.innerHTML = ""; // Limpa a tabela antes de inserir os dados
    
          snapshot.forEach((childSnapshot) => {
            const entrega = childSnapshot.val();
    
            const row = document.createElement("tr");
            row.innerHTML = `
              <td>${entrega.sala}</td>
              <td>${entrega.nome}</td>
              <td>${entrega.medicamento}</td>
              <td>${entrega.horario}</td>
            `;
            tabela_pendentes.appendChild(row);
          });
        });
    }

    if (tabela_entregas) {
        const entregasRef = firebase.database().ref("entregas").orderByChild("status").equalTo("entregue");
    
        entregasRef.on("value", (snapshot) => {
          tabela_entregas.innerHTML = ""; // Limpa a tabela antes de inserir os dados
    
          snapshot.forEach((childSnapshot) => {
            const entrega = childSnapshot.val();
    
            const row = document.createElement("tr");
            row.innerHTML = `
              <td>${entrega.sala}</td>
              <td>${entrega.nome}</td>
              <td>${entrega.medicamento}</td>
              <td>${entrega.horario}</td>
            `;
            tabela_entregas.appendChild(row);
          });
        });
    }
  
});
  
