(function () {
  const toggle = document.getElementById("toggle-diferencas");
  if (!toggle) return;

  function aplicar() {
    const somenteDiferencas = toggle.checked;

    document.querySelectorAll(".comparativo-linha").forEach((linha) => {
      const igual = linha.getAttribute("data-igual") === "true";
      linha.style.display = somenteDiferencas && igual ? "none" : "";
    });

    document.querySelectorAll(".comparativo-categoria").forEach((categoria) => {
      let el = categoria.nextElementSibling;
      let temLinhaVisivel = false;
      while (el && !el.classList.contains("comparativo-categoria")) {
        if (el.style.display !== "none") {
          temLinhaVisivel = true;
          break;
        }
        el = el.nextElementSibling;
      }
      categoria.style.display = somenteDiferencas && !temLinhaVisivel ? "none" : "";
    });
  }

  toggle.addEventListener("change", aplicar);
})();
