// InvenShop · interacciones del frontend
(function () {
  "use strict";

  // Cierra automáticamente los mensajes después de 6 segundos.
  document.querySelectorAll("[data-auto-dismiss]").forEach(function (alert) {
    window.setTimeout(function () {
      if (!alert.isConnected) return;
      alert.style.transition = "opacity .3s ease, transform .3s ease";
      alert.style.opacity = "0";
      alert.style.transform = "translateY(-6px)";
      window.setTimeout(function () { alert.remove(); }, 320);
    }, 6000);
  });

  // Botones +/- de cantidad.
  document.querySelectorAll("[data-qty]").forEach(function (group) {
    var input = group.querySelector("input[type='number']");
    if (!input) return;
    group.querySelectorAll("button[data-step]").forEach(function (button) {
      button.addEventListener("click", function () {
        var paso = parseInt(button.getAttribute("data-step"), 10) || 0;
        var min = parseInt(input.getAttribute("min") || "1", 10);
        var max = parseInt(input.getAttribute("max") || "999999", 10);
        var actual = parseInt(input.value || "1", 10);
        var nuevo = Math.min(max, Math.max(min, actual + paso));
        input.value = nuevo;
        input.dispatchEvent(new Event("change", { bubbles: true }));
      });
    });
  });

  // Vista previa de la imagen al editar un producto.
  var inputImagen = document.querySelector("[data-preview-input]");
  var preview = document.querySelector("[data-preview-image]");
  if (inputImagen && preview) {
    inputImagen.addEventListener("change", function () {
      var archivo = inputImagen.files && inputImagen.files[0];
      if (!archivo) return;
      if (archivo.size > 2 * 1024 * 1024) {
        alert("La imagen supera los 2 MB permitidos.");
        inputImagen.value = "";
        return;
      }
      preview.src = URL.createObjectURL(archivo);
      preview.classList.remove("d-none");
    });
  }

  // Confirma acciones destructivas con un mensaje claro.
  document.querySelectorAll("[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (!window.confirm(form.getAttribute("data-confirm"))) {
        event.preventDefault();
      }
    });
  });

  // Enfoca el buscador con la tecla "/".
  document.addEventListener("keydown", function (event) {
    if (event.key === "/" && !/input|textarea|select/i.test(document.activeElement.tagName)) {
      var buscador = document.querySelector("[data-buscador]");
      if (buscador) {
        event.preventDefault();
        buscador.focus();
      }
    }
  });
})();
