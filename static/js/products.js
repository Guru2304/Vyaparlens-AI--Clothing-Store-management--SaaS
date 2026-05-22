(function () {
  const form = document.getElementById("productForm");
  if (!form) return;

  const sizeChips = document.getElementById("sizeChips");
  const colourChips = document.getElementById("colourChips");
  const sizesInput = document.getElementById("sizesInput");
  const coloursInput = document.getElementById("coloursInput");
  const variantDistribution = document.getElementById("variantDistribution");
  const customSize = document.getElementById("customSize");
  const customColour = document.getElementById("customColour");
  const categorySelect = document.getElementById("categorySelect");
  const manualWrap = document.getElementById("manualGridWrap");
  const manualGrid = document.getElementById("manualGrid");
  const totalQuantity = document.getElementById("totalQuantity");
  const buyingPrice = document.getElementById("buyingPrice");
  const sellingPrice = document.getElementById("sellingPrice");
  const enteredQty = document.getElementById("enteredQty");
  const remainingQty = document.getElementById("remainingQty");
  const distributionStatus = document.getElementById("distributionStatus");
  const summaryTotalQty = document.getElementById("summaryTotalQty");
  const summaryEnteredQty = document.getElementById("summaryEnteredQty");
  const summaryRemainingQty = document.getElementById("summaryRemainingQty");
  const summaryRevenue = document.getElementById("summaryRevenue");
  const summaryProfit = document.getElementById("summaryProfit");

  function money(value) {
    return `Rs. ${Number(value || 0).toFixed(2)}`;
  }

  function getSelectedSizes() {
    return Array.from(sizeChips.querySelectorAll(".chip.active")).map((chip) => chip.dataset.token);
  }

  function getSelectedColours() {
    return Array.from(colourChips.querySelectorAll(".chip.active")).map((chip) => chip.dataset.token);
  }

  function getDistributionMode() {
    return form.querySelector("input[name='distribution_mode']:checked")?.value || "equal";
  }

  function syncSelectedInputs() {
    sizesInput.value = getSelectedSizes().join(",");
    coloursInput.value = getSelectedColours().join(",");
  }

  function currentGridValues() {
    const values = {};
    manualGrid.querySelectorAll(".manual-qty").forEach((input) => {
      values[`${input.dataset.colour}||${input.dataset.size}`] = input.value;
    });
    return values;
  }

  function createChip(token) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "chip active";
    button.dataset.token = token;
    button.textContent = token;
    return button;
  }

  function renderChips(container, tokens) {
    container.innerHTML = "";
    tokens.forEach((token) => container.appendChild(createChip(token)));
    syncSelectedInputs();
    buildManualDistributionGrid();
  }

  function addToken(type) {
    const input = type === "size" ? customSize : customColour;
    const container = type === "size" ? sizeChips : colourChips;
    const value = input.value.trim();
    if (!value) return;

    const exists = Array.from(container.querySelectorAll(".chip")).some(
      (chip) => chip.dataset.token.toLowerCase() === value.toLowerCase()
    );
    if (!exists) container.appendChild(createChip(value));
    input.value = "";
    syncSelectedInputs();
    buildManualDistributionGrid();
  }

  function buildManualDistributionGrid() {
    syncSelectedInputs();
    const mode = getDistributionMode();
    const sizes = getSelectedSizes();
    const colours = getSelectedColours();
    const previous = currentGridValues();

    manualWrap.classList.toggle("hidden", mode !== "manual");
    if (mode !== "manual") {
      variantDistribution.value = "[]";
      updateSummaryTotals();
      return;
    }

    const table = document.createElement("table");
    table.className = "manual-distribution-table";
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    ["Colour", ...sizes, "Total"].forEach((label) => {
      const th = document.createElement("th");
      th.textContent = label;
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    colours.forEach((colour) => {
      const tr = document.createElement("tr");
      const colourCell = document.createElement("td");
      colourCell.textContent = colour;
      tr.appendChild(colourCell);

      sizes.forEach((size) => {
        const td = document.createElement("td");
        const input = document.createElement("input");
        input.className = "manual-qty";
        input.type = "number";
        input.min = "0";
        input.step = "1";
        input.value = previous[`${colour}||${size}`] || "0";
        input.dataset.colour = colour;
        input.dataset.size = size;
        td.appendChild(input);
        tr.appendChild(td);
      });

      const totalCell = document.createElement("td");
      totalCell.className = "row-total";
      totalCell.textContent = "0";
      tr.appendChild(totalCell);
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    manualGrid.innerHTML = "";
    manualGrid.appendChild(table);
    updateDistributionTotals();
  }

  function updateSummaryTotals(manualTotal) {
    const target = Math.max(0, parseInt(totalQuantity.value || "0", 10));
    const entered = getDistributionMode() === "manual" ? Number(manualTotal || 0) : target;
    const remaining = target - entered;
    const sell = Number(sellingPrice?.value || 0);
    const buy = Number(buyingPrice?.value || 0);

    if (summaryTotalQty) summaryTotalQty.textContent = target;
    if (summaryEnteredQty) summaryEnteredQty.textContent = entered;
    if (summaryRemainingQty) {
      summaryRemainingQty.textContent = remaining;
      summaryRemainingQty.classList.toggle("success-text", remaining === 0 && target > 0);
      summaryRemainingQty.classList.toggle("danger-text", remaining < 0);
      summaryRemainingQty.classList.toggle("warning-text", remaining > 0);
    }
    if (summaryRevenue) summaryRevenue.textContent = money(sell * target);
    if (summaryProfit) summaryProfit.textContent = money((sell - buy) * target);
  }

  function serializeManualDistribution() {
    const rows = [];
    manualGrid.querySelectorAll(".manual-qty").forEach((input) => {
      const quantity = Math.max(0, parseInt(input.value || "0", 10));
      rows.push({
        colour: input.dataset.colour,
        size: input.dataset.size,
        quantity,
      });
    });
    variantDistribution.value = JSON.stringify(rows);
    return rows;
  }

  function updateDistributionTotals() {
    const rows = serializeManualDistribution();
    const target = Math.max(0, parseInt(totalQuantity.value || "0", 10));
    const total = rows.reduce((sum, row) => sum + row.quantity, 0);

    manualGrid.querySelectorAll("tbody tr").forEach((tr) => {
      let rowTotal = 0;
      tr.querySelectorAll(".manual-qty").forEach((input) => {
        const value = Math.max(0, parseInt(input.value || "0", 10));
        if (String(value) !== input.value && input.value !== "") input.value = value;
        rowTotal += value;
      });
      tr.querySelector(".row-total").textContent = rowTotal;
    });

    enteredQty.textContent = total;
    remainingQty.textContent = target - total;
    remainingQty.classList.toggle("danger-text", total > target);
    distributionStatus.classList.remove("success", "error");

    if (!target) {
      distributionStatus.textContent = "Enter total quantity to validate distribution.";
    } else if (total < target) {
      distributionStatus.textContent = "Please distribute all quantity before saving.";
      distributionStatus.classList.add("error");
    } else if (total > target) {
      distributionStatus.textContent = "Distributed quantity exceeds total quantity.";
      distributionStatus.classList.add("error");
    } else {
      distributionStatus.textContent = "Distribution complete. You can save this product.";
      distributionStatus.classList.add("success");
    }
    updateSummaryTotals(total);
  }

  function validateManualDistributionBeforeSubmit() {
    if (getDistributionMode() !== "manual") return true;
    updateDistributionTotals();
    const target = parseInt(totalQuantity.value || "0", 10);
    const entered = parseInt(enteredQty.textContent || "0", 10);
    if (entered < target) {
      alert("Please distribute all quantity before saving.");
      return false;
    }
    if (entered > target) {
      alert("Distributed quantity exceeds total quantity.");
      return false;
    }
    return true;
  }

  [sizeChips, colourChips].forEach((container) => {
    container.addEventListener("click", (event) => {
      const chip = event.target.closest(".chip");
      if (!chip) return;
      chip.classList.toggle("active");
      syncSelectedInputs();
      buildManualDistributionGrid();
    });
  });

  document.querySelectorAll("[data-add-token]").forEach((button) => {
    button.addEventListener("click", () => addToken(button.dataset.addToken));
  });

  categorySelect.addEventListener("change", () => {
    const pantCategories = ["Pant", "Jeans", "Track Pant"];
    renderChips(sizeChips, pantCategories.includes(categorySelect.value) ? window.defaultPantSizes || [] : window.defaultShirtSizes || []);
  });

  form.querySelectorAll("input[name='distribution_mode']").forEach((radio) => {
    radio.addEventListener("change", buildManualDistributionGrid);
  });

  manualGrid.addEventListener("input", (event) => {
    if (event.target.classList.contains("manual-qty")) updateDistributionTotals();
  });
  totalQuantity.addEventListener("input", () => {
    if (getDistributionMode() === "manual") updateDistributionTotals();
    else updateSummaryTotals();
  });
  buyingPrice?.addEventListener("input", () => updateSummaryTotals(Number(enteredQty.textContent || 0)));
  sellingPrice?.addEventListener("input", () => updateSummaryTotals(Number(enteredQty.textContent || 0)));

  form.addEventListener("submit", (event) => {
    syncSelectedInputs();
    if (!sizesInput.value || !coloursInput.value) {
      event.preventDefault();
      alert("Select at least one size and one colour.");
      return;
    }
    if (!validateManualDistributionBeforeSubmit()) {
      event.preventDefault();
    }
  });

  buildManualDistributionGrid();
  updateSummaryTotals();
})();
