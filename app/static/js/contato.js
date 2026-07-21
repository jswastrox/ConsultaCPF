(function () {
  "use strict";

  var CONTATO_MOTIVOS = ["Reclamação", "Suporte", "Sugestão"];
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function onlyDigits(value) {
    return String(value || "").replace(/\D/g, "");
  }

  function formatPhone(value) {
    var digits = onlyDigits(value).slice(0, 11);
    if (!digits) return "";
    var ddd = digits.slice(0, 2);
    var numero = digits.slice(2);
    if (digits.length <= 2) return "(" + ddd;
    if (numero.length <= 5) return "(" + ddd + ") " + numero;
    return "(" + ddd + ") " + numero.slice(0, 5) + "-" + numero.slice(5);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var form = document.getElementById("contato-form");
    if (!form) return;

    var telefoneInput = document.getElementById("contatoTelefone");
    var submitBtn = document.getElementById("contato-submit-btn");
    var successEl = document.getElementById("contato-feedback-success");
    var warningEl = document.getElementById("contato-feedback-warning");
    var errorEl = document.getElementById("contato-feedback-error");

    telefoneInput.addEventListener("input", function () {
      telefoneInput.value = formatPhone(telefoneInput.value);
    });

    function hideFeedback() {
      successEl.hidden = true;
      warningEl.hidden = true;
      errorEl.hidden = true;
    }

    function showError(message) {
      hideFeedback();
      errorEl.textContent = message;
      errorEl.hidden = false;
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      hideFeedback();

      var motivo = form.motivo.value;
      var nome = String(form.nome.value || "").trim();
      var email = String(form.email.value || "").trim();
      var telefoneDigits = onlyDigits(form.telefone.value);
      var mensagem = String(form.mensagem.value || "").trim();

      if (CONTATO_MOTIVOS.indexOf(motivo) === -1) {
        showError("Selecione o motivo do contato.");
        return;
      }
      if (nome.length < 2) {
        showError("Informe seu nome.");
        return;
      }
      if (!email || !EMAIL_RE.test(email)) {
        showError("Informe um e-mail válido.");
        return;
      }
      if (telefoneDigits.length < 10) {
        showError("Informe telefone ou celular com DDD (mínimo 10 dígitos).");
        return;
      }
      if (mensagem.length < 5) {
        showError("Escreva sua mensagem (mínimo 5 caracteres).");
        return;
      }

      var originalBtnHtml = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.textContent = "Enviando...";

      fetch("/api/contato", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ motivo: motivo, nome: nome, email: email, telefone: telefoneDigits, mensagem: mensagem })
      })
        .then(function (response) {
          return response.json().then(function (data) {
            return { ok: response.ok, data: data };
          });
        })
        .then(function (result) {
          if (!result.ok) {
            throw new Error(result.data.message || "Não foi possível enviar sua mensagem.");
          }
          hideFeedback();
          var message = String(result.data.message || "Mensagem recebida.");
          if (result.data.emailSent) {
            successEl.textContent = message;
            successEl.hidden = false;
          } else {
            warningEl.textContent = message;
            warningEl.hidden = false;
          }
          form.reset();
        })
        .catch(function (error) {
          showError(error.message || "Não foi possível enviar sua mensagem.");
        })
        .finally(function () {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalBtnHtml;
        });
    });
  });
})();
