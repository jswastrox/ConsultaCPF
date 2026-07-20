(function () {
  function onlyDigits(value) {
    return (value || "").replace(/\D/g, "");
  }

  function maskCpf(value) {
    var d = onlyDigits(value).slice(0, 11);
    return d
      .replace(/(\d{3})(\d)/, "$1.$2")
      .replace(/(\d{3})(\d)/, "$1.$2")
      .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
  }

  function maskCnpj(value) {
    var d = onlyDigits(value).slice(0, 14);
    return d
      .replace(/^(\d{2})(\d)/, "$1.$2")
      .replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/\.(\d{3})(\d)/, ".$1/$2")
      .replace(/(\d{4})(\d)/, "$1-$2");
  }

  function maskTelefone(value) {
    var d = onlyDigits(value).slice(0, 11);
    if (d.length <= 10) {
      return d
        .replace(/^(\d{2})(\d)/, "($1) $2")
        .replace(/(\d{4})(\d)/, "$1-$2");
    }
    return d
      .replace(/^(\d{2})(\d)/, "($1) $2")
      .replace(/(\d{5})(\d)/, "$1-$2");
  }

  function maskCep(value) {
    var d = onlyDigits(value).slice(0, 8);
    return d.replace(/^(\d{5})(\d)/, "$1-$2");
  }

  var masks = {
    cpf: maskCpf,
    cnpj: maskCnpj,
    telefone: maskTelefone,
    cep: maskCep,
  };

  document.querySelectorAll("input[data-mask]").forEach(function (input) {
    var kind = input.getAttribute("data-mask");
    var fn = masks[kind];
    if (!fn) return;
    input.addEventListener("input", function () {
      var start = input.selectionStart;
      var before = input.value.length;
      input.value = fn(input.value);
      var after = input.value.length;
      if (typeof start === "number") {
        input.setSelectionRange(start + (after - before), start + (after - before));
      }
    });
  });

  var panel = document.getElementById("formulario-consulta");
  if (panel) {
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
  }
})();
