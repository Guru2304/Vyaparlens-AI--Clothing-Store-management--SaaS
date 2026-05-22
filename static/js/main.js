(function () {
  const sidebar = document.getElementById("sidebar");
  const sidebarToggle = document.querySelector("[data-sidebar-toggle]");
  const sidebarOverlay = document.querySelector("[data-sidebar-close]");

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", () => {
      sidebar.classList.toggle("open");
      document.body.classList.toggle("sidebar-open", sidebar.classList.contains("open"));
    });
  }

  if (sidebarOverlay && sidebar) {
    sidebarOverlay.addEventListener("click", () => {
      sidebar.classList.remove("open");
      document.body.classList.remove("sidebar-open");
    });
  }

  document.querySelectorAll(".side-nav a, .logout-link").forEach((link) => {
    link.addEventListener("click", () => {
      sidebar?.classList.remove("open");
      document.body.classList.remove("sidebar-open");
    });
  });

  document.querySelectorAll("[data-toggle-target]").forEach((button) => {
    button.addEventListener("click", () => {
      const target = document.getElementById(button.dataset.toggleTarget);
      if (target) target.classList.toggle("hidden");
    });
  });

  document.addEventListener("click", (event) => {
    const stockButton = event.target.closest("[data-open-stock]");
    if (stockButton) {
      const modal = document.getElementById(`stockModal-${stockButton.dataset.openStock}`);
      if (modal) modal.classList.add("open");
    }

    const collectButton = event.target.closest("[data-open-collect]");
    if (collectButton) {
      const modal = document.getElementById(`collectModal-${collectButton.dataset.openCollect}`);
      if (modal) modal.classList.add("open");
    }

    if (event.target.matches("[data-close-modal]")) {
      event.target.closest(".modal")?.classList.remove("open");
    }

    if (event.target.classList.contains("modal")) {
      event.target.classList.remove("open");
    }
  });

  const toasts = document.querySelectorAll(".toast");
  toasts.forEach((toast) => {
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(8px)";
      setTimeout(() => toast.remove(), 220);
    }, 3400);
  });
})();
