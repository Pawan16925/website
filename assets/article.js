document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-stx-year]").forEach((element) => {
    element.textContent = String(new Date().getFullYear());
  });

  document.querySelectorAll("a[href]").forEach((link) => {
    if (link.hostname && link.hostname !== window.location.hostname) {
      link.target = "_blank";
      link.rel = "noopener noreferrer";
    }
  });
});
