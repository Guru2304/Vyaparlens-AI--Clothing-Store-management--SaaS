(function () {
  const list = document.getElementById("inventoryList");
  if (!list) return;

  const search = document.getElementById("inventorySearch");
  const category = document.getElementById("categoryFilter");
  const brand = document.getElementById("brandFilter");
  const stock = document.getElementById("stockFilter");
  const sort = document.getElementById("sortInventory");

  function applyFilters() {
    const term = search.value.trim().toLowerCase();
    const categoryValue = category.value;
    const brandValue = brand.value;
    const lowOnly = stock.value === "low";
    Array.from(list.children).forEach((card) => {
      const matchesTerm = !term || card.textContent.toLowerCase().includes(term);
      const matchesCategory = !categoryValue || card.dataset.category === categoryValue;
      const matchesBrand = !brandValue || card.dataset.brand === brandValue;
      const matchesLow = !lowOnly || card.dataset.low === "1";
      card.classList.toggle("hidden", !(matchesTerm && matchesCategory && matchesBrand && matchesLow));
    });
  }

  function applySort() {
    const cards = Array.from(list.children);
    if (sort.value === "stock") {
      cards.sort((a, b) => Number(b.dataset.stock) - Number(a.dataset.stock));
    } else if (sort.value === "profit") {
      cards.sort((a, b) => Number(b.dataset.profit) - Number(a.dataset.profit));
    }
    cards.forEach((card) => list.appendChild(card));
  }

  [search, category, brand, stock].forEach((input) => input.addEventListener("input", applyFilters));
  sort.addEventListener("change", () => {
    applySort();
    applyFilters();
  });
})();
