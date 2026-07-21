(function () {
  const checkboxes = document.querySelectorAll(".pacote-checkbox");
  const btnPagar = document.getElementById("btn-pagar");
  const precoEl = document.getElementById("preco-selecionado");
  if (!checkboxes.length || !btnPagar) return;

  const precos = window.PRECOS_PACOTE || {};

  function formatarPreco(valor) {
    return "R$ " + Number(valor).toFixed(2).replace(".", ",");
  }

  function atualizar() {
    const marcado = Array.from(checkboxes).find((cb) => cb.checked);
    const pacote = marcado ? marcado.value : "basico";
    btnPagar.setAttribute("data-pacote", pacote);
    if (precoEl && precos[pacote] !== undefined) {
      precoEl.textContent = formatarPreco(precos[pacote]);
    }
  }

  checkboxes.forEach((cb) => {
    cb.addEventListener("change", () => {
      if (cb.checked) {
        checkboxes.forEach((outro) => {
          if (outro !== cb) outro.checked = false;
        });
      }
      atualizar();
    });
  });

  atualizar();
})();
