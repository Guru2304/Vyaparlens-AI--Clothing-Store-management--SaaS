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

  function syncModalScrollLock() {
    document.body.classList.toggle("modal-open", Boolean(document.querySelector(".modal.open")));
  }

  function openModal(modal) {
    if (!modal) return;
    if (modal.parentElement !== document.body) {
      document.body.appendChild(modal);
    }
    modal.classList.add("open");
    syncModalScrollLock();
  }

  function closeModal(modal) {
    if (!modal) return;
    modal.classList.remove("open");
    syncModalScrollLock();
  }

  document.querySelectorAll(".modal.open").forEach(openModal);

  document.addEventListener("click", (event) => {
    const stockButton = event.target.closest("[data-open-stock]");
    if (stockButton) {
      const modal = document.getElementById(`stockModal-${stockButton.dataset.openStock}`);
      openModal(modal);
    }

    const collectButton = event.target.closest("[data-open-collect]");
    if (collectButton) {
      const modal = document.getElementById(`collectModal-${collectButton.dataset.openCollect}`);
      openModal(modal);
    }

    if (event.target.matches("[data-close-modal]")) {
      closeModal(event.target.closest(".modal"));
    }

    if (event.target.classList.contains("modal")) {
      closeModal(event.target);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    closeModal(document.querySelector(".modal.open"));
  });

  const seenToastMessages = new Set();
  document.querySelectorAll(".toast").forEach((toast) => {
    const key = `${toast.className}:${toast.textContent.trim()}`;
    if (seenToastMessages.has(key)) {
      toast.remove();
      return;
    }
    seenToastMessages.add(key);
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
