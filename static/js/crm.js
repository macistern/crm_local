document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("whatsapp-modal");
  if (modal && !modal.open && modal.dataset.open === "true") modal.showModal();
  if (modal && modal.hasAttribute("open") && typeof modal.showModal === "function") {
    modal.removeAttribute("open");
    modal.showModal();
  }

  document.querySelectorAll("[data-open-whatsapp]").forEach((button) => {
    button.addEventListener("click", () => modal?.showModal());
  });
  document.querySelectorAll("[data-close-whatsapp]").forEach((button) => {
    button.addEventListener("click", () => modal?.close());
  });
  document.querySelectorAll("[data-quick-message]").forEach((button) => {
    button.addEventListener("click", () => {
      const textarea = modal?.querySelector('textarea[name="texto"]');
      const plantilla = modal?.querySelector('input[name="plantilla"]');
      if (!textarea || !plantilla) return;
      textarea.value = button.dataset.quickMessage
        .replaceAll("{nombre}", modal.dataset.nombre || "")
        .replaceAll("{empresa}", modal.dataset.empresa || "nuestro equipo");
      plantilla.value = button.dataset.plantillaId || "";
      textarea.focus();
    });
  });
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });
});
