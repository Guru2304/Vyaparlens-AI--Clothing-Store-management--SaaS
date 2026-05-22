(function () {
  document.querySelectorAll("form").forEach((form) => {
    if (!form.action.includes("/udhar/collect")) return;
    form.addEventListener("submit", (event) => {
      const amount = Number(form.amount.value || 0);
      if (amount <= 0) {
        event.preventDefault();
        alert("Received amount must be positive.");
      }
    });
  });
})();
