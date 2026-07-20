(function () {
  const btnPagar = document.getElementById("btn-pagar");
  const modal = document.getElementById("modal-pix");
  const conteudo = document.getElementById("modal-pix-conteudo");
  const fecharBtn = document.getElementById("modal-fechar");

  if (!btnPagar || !modal) return;

  const cpf = btnPagar.getAttribute("data-cpf");
  let pollTimer = null;

  function abrirModal() {
    modal.hidden = false;
    conteudo.innerHTML = '<p class="modal-carregando">Gerando cobrança...</p>';
    criarPedido();
  }

  function fecharModal() {
    modal.hidden = true;
    if (pollTimer) clearInterval(pollTimer);
  }

  function mostrarErro(msg) {
    conteudo.innerHTML = `<p class="modal-erro">${msg}</p>`;
  }

  async function criarPedido() {
    try {
      const resp = await fetch("/api/pedidos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cpf: cpf }),
      });
      if (!resp.ok) {
        const erro = await resp.json().catch(() => ({}));
        throw new Error(erro.detail || "Não foi possível gerar a cobrança.");
      }
      const pedido = await resp.json();

      conteudo.innerHTML = `
        <img class="modal-qrcode" src="${pedido.qrcode_image}" alt="QR Code Pix">
        <label class="modal-brcode-label">Pix copia e cola</label>
        <div class="modal-brcode-row">
          <input type="text" id="modal-brcode-input" readonly value="${pedido.brcode}">
          <button type="button" id="modal-copiar-btn" class="btn-secundario">Copiar</button>
        </div>
        <p id="modal-status" class="modal-status">Aguardando pagamento…</p>
      `;

      document.getElementById("modal-copiar-btn").addEventListener("click", () => {
        const input = document.getElementById("modal-brcode-input");
        input.select();
        navigator.clipboard.writeText(input.value).then(() => {
          const btn = document.getElementById("modal-copiar-btn");
          btn.textContent = "Copiado!";
          setTimeout(() => (btn.textContent = "Copiar"), 1500);
        });
      });

      pollTimer = setInterval(() => verificarStatus(pedido.correlation_id), 3000);
    } catch (err) {
      mostrarErro(err.message || "Erro ao gerar cobrança Pix.");
    }
  }

  async function verificarStatus(correlationId) {
    try {
      const resp = await fetch(`/api/pedidos/${correlationId}/status`);
      if (!resp.ok) return;
      const data = await resp.json();
      if (data.status === "paid") {
        clearInterval(pollTimer);
        const statusEl = document.getElementById("modal-status");
        if (statusEl) statusEl.textContent = "Pagamento confirmado! Atualizando página…";
        setTimeout(() => window.location.reload(), 1200);
      }
    } catch (err) {
      // silencioso: tenta de novo no próximo ciclo
    }
  }

  btnPagar.addEventListener("click", abrirModal);
  if (fecharBtn) fecharBtn.addEventListener("click", fecharModal);
  modal.addEventListener("click", (e) => {
    if (e.target === modal) fecharModal();
  });
})();
