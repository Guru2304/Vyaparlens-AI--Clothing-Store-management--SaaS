(function () {
  const productData = JSON.parse(document.getElementById("productData")?.textContent || "[]");
  const productSearch = document.getElementById("productSearch");
  const productSelect = document.getElementById("productSelect");
  const colourSelect = document.getElementById("colourSelect");
  const sizeSelect = document.getElementById("sizeSelect");
  const availableStock = document.getElementById("availableStock");
  const itemPrice = document.getElementById("itemPrice");
  const itemQty = document.getElementById("itemQty");
  const itemDiscountType = document.getElementById("itemDiscountType");
  const itemDiscountValue = document.getElementById("itemDiscountValue");
  const itemDiscountValueWrap = document.getElementById("itemDiscountValueWrap");
  const customFinalPrice = document.getElementById("customFinalPrice");
  const customFinalPriceWrap = document.getElementById("customFinalPriceWrap");
  const previewDefaultUnit = document.getElementById("previewDefaultUnit");
  const previewFinalUnit = document.getElementById("previewFinalUnit");
  const previewDiscountUnit = document.getElementById("previewDiscountUnit");
  const previewDiscountPercent = document.getElementById("previewDiscountPercent");
  const previewLineTotal = document.getElementById("previewLineTotal");
  const itemPricingError = document.getElementById("itemPricingError");
  const itemPricingWarning = document.getElementById("itemPricingWarning");
  const addCartItem = document.getElementById("addCartItem");
  const cartBody = document.getElementById("cartBody");
  const clearCart = document.getElementById("clearCart");
  const clearCartBtn = document.getElementById("clearCartBtn");
  const billForm = document.getElementById("billingForm") || document.getElementById("billForm");
  const cartData = document.getElementById("cartData");
  const subtotalAmount = document.getElementById("subtotalAmount");
  const discountAmount = document.getElementById("discountAmount");
  const settlementDiscountRow = document.getElementById("settlementDiscountRow");
  const settlementDiscountAmount = document.getElementById("settlementDiscountAmount");
  const billTotal = document.getElementById("billTotal");
  const paymentMode = document.getElementById("paymentMode");
  const paidAmount = document.getElementById("paidAmount");
  const paidSummary = document.getElementById("paidSummary");
  const pendingAmount = document.getElementById("pendingAmount");
  const customerBox = document.getElementById("customerBox");
  const mixedFields = document.getElementById("mixedFields");
  const generateBillBtn = document.getElementById("generateBillBtn");
  const previewItems = document.getElementById("previewItems");
  const previewSubtotal = document.getElementById("previewSubtotal");
  const previewDiscount = document.getElementById("previewDiscount");
  const previewSettlementRow = document.getElementById("previewSettlementRow");
  const previewSettlementDiscount = document.getElementById("previewSettlementDiscount");
  const previewTotal = document.getElementById("previewTotal");
  const previewPaid = document.getElementById("previewPaid");
  const previewPending = document.getElementById("previewPending");
  const cart = [];
  let paidAuto = true;
  let syncingFinalPrice = false;

  function money(value) {
    return `₹${Number(value || 0).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  function round2(value) {
    return Math.round((Number(value || 0) + Number.EPSILON) * 100) / 100;
  }

  function showToast(message, type = "error") {
    const toastWrap = document.getElementById("toastWrap");
    if (!toastWrap) {
      alert(message);
      return;
    }

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toastWrap.appendChild(toast);
    setTimeout(() => toast.remove(), 3600);
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    }[char]));
  }

  function productLabel(product) {
    if (product.display_name) return product.display_name;
    const brand = String(product.brand_name || "").trim();
    const name = String(product.product_name || "").trim();
    if (!brand) return name;
    if (!name) return brand;
    return name.toLowerCase().startsWith(brand.toLowerCase()) ? name : `${brand} ${name}`;
  }

  function filteredProducts() {
    const term = productSearch.value.trim().toLowerCase();
    if (!term) return productData;
    return productData.filter((product) => {
      const haystack = [
        product.display_name,
        product.brand_name,
        product.product_name,
        product.category,
        ...product.variants.map((variant) => `${variant.colour} ${variant.size} ${variant.sku}`),
      ].join(" ").toLowerCase();
      return haystack.includes(term);
    });
  }

  function selectedProduct() {
    return productData.find((product) => String(product.id) === productSelect.value);
  }

  function selectedVariant() {
    const product = selectedProduct();
    if (!product) return null;
    return product.variants.find((variant) => variant.colour === colourSelect.value && variant.size === sizeSelect.value);
  }

  function quantityInCart(variantId, exceptIndex = -1) {
    return cart.reduce((sum, item, index) => {
      if (item.variantId !== variantId || index === exceptIndex) return sum;
      return sum + item.quantity;
    }, 0);
  }

  function calculateItemPricing(defaultPrice, quantity, discountType, discountValue, customFinalPrice) {
    defaultPrice = Number(defaultPrice || 0);
    quantity = Number(quantity || 1);

    let finalUnitPrice = defaultPrice;
    let discountPerUnit = 0;
    let error = "";

    if (discountType === "flat") {
      discountPerUnit = Number(discountValue || 0);
      if (discountPerUnit < 0) error = "Flat discount cannot be negative.";
      if (discountPerUnit > defaultPrice) error = "Flat discount cannot exceed default price.";
      finalUnitPrice = defaultPrice - discountPerUnit;
    }

    if (discountType === "percent") {
      const percent = Number(discountValue || 0);
      if (percent < 0) error = "Percentage discount cannot be negative.";
      if (percent > 100) error = "Percentage discount cannot exceed 100.";
      discountPerUnit = defaultPrice * percent / 100;
      finalUnitPrice = defaultPrice - discountPerUnit;
    }

    if (discountType === "custom_price") {
      finalUnitPrice = Number(customFinalPrice === "" || customFinalPrice === null || customFinalPrice === undefined ? defaultPrice : customFinalPrice);
      if (finalUnitPrice < 0) error = "Custom final price cannot be negative.";
      discountPerUnit = defaultPrice - finalUnitPrice;
    }

    if (discountType === "none") {
      finalUnitPrice = defaultPrice;
      discountPerUnit = 0;
    }

    if (discountPerUnit < 0) discountPerUnit = 0;
    if (finalUnitPrice < 0) finalUnitPrice = 0;

    const lineSubtotal = round2(defaultPrice * quantity);
    const lineTotal = round2(finalUnitPrice * quantity);
    const discountAmount = round2(lineSubtotal - lineTotal);
    const discountPercent = defaultPrice > 0 ? round2((Math.max(defaultPrice - finalUnitPrice, 0) / defaultPrice) * 100) : 0;

    return {
      defaultPrice: round2(defaultPrice),
      quantity,
      finalUnitPrice: round2(finalUnitPrice),
      discountPerUnit: round2(discountPerUnit),
      lineSubtotal,
      lineTotal,
      discountAmount: Math.max(discountAmount, 0),
      discountPercent,
      error,
    };
  }

  function currentItemPricing() {
    const product = selectedProduct();
    const defaultPrice = Number(product?.selling_price || itemPrice.value || 0);
    const quantity = Math.max(1, Number(itemQty.value || 1));
    return calculateItemPricing(
      defaultPrice,
      quantity,
      itemDiscountType.value,
      itemDiscountValue.value,
      customFinalPrice.value
    );
  }

  function updateDiscountControls() {
    const type = itemDiscountType.value;
    itemDiscountValueWrap.classList.toggle("hidden", !["flat", "percent"].includes(type));
    customFinalPriceWrap.classList.remove("hidden");
    if (type === "flat") itemDiscountValueWrap.firstChild.textContent = "Discount per item";
    if (type === "percent") itemDiscountValueWrap.firstChild.textContent = "Discount %";
    if (type === "custom_price" && !customFinalPrice.value) customFinalPrice.value = itemPrice.value || "0.00";
  }

  function syncFinalPriceFromDiscount() {
    if (itemDiscountType.value === "custom_price") return;
    const product = selectedProduct();
    const defaultPrice = Number(product?.selling_price || itemPrice.value || 0);
    const quantity = Math.max(1, Number(itemQty.value || 1));
    const pricing = calculateItemPricing(defaultPrice, quantity, itemDiscountType.value, itemDiscountValue.value, customFinalPrice.value);
    syncingFinalPrice = true;
    customFinalPrice.value = pricing.finalUnitPrice.toFixed(2);
    syncingFinalPrice = false;
  }

  function useReverseFinalPrice() {
    if (syncingFinalPrice) return;
    itemDiscountType.value = "custom_price";
    itemDiscountValue.value = "0";
    updateItemPricingPreview();
  }

  function updateItemPricingPreview() {
    updateDiscountControls();
    const product = selectedProduct();
    const pricing = currentItemPricing();
    const warnings = [];

    if (product?.minimum_selling_price && pricing.finalUnitPrice < Number(product.minimum_selling_price)) {
      warnings.push("This price is below minimum selling price.");
    }
    if (product?.buying_price && pricing.finalUnitPrice < Number(product.buying_price)) {
      warnings.push("This sale may create loss.");
    }

    previewDefaultUnit.textContent = money(pricing.defaultPrice);
    previewFinalUnit.textContent = money(pricing.finalUnitPrice);
    previewDiscountUnit.textContent = money(pricing.discountPerUnit);
    previewDiscountPercent.textContent = `${pricing.discountPercent.toFixed(2)}%`;
    previewLineTotal.textContent = money(pricing.lineTotal);
    itemPricingError.textContent = pricing.error;
    itemPricingError.classList.toggle("hidden", !pricing.error);
    itemPricingWarning.textContent = warnings.join(" ");
    itemPricingWarning.classList.toggle("hidden", !warnings.length);
    return pricing;
  }

  function populateProducts() {
    const products = filteredProducts();
    productSelect.innerHTML = products.map((product) => `<option value="${product.id}">${escapeHtml(productLabel(product))}</option>`).join("");
    populateColours();
  }

  function populateColours() {
    const product = selectedProduct();
    const colours = product ? [...new Set(product.variants.map((variant) => variant.colour))] : [];
    colourSelect.innerHTML = colours.map((colour) => `<option>${escapeHtml(colour)}</option>`).join("");
    if (product) {
      itemPrice.value = Number(product.selling_price).toFixed(2);
      customFinalPrice.value = Number(product.selling_price).toFixed(2);
    }
    populateSizes();
    syncFinalPriceFromDiscount();
    updateItemPricingPreview();
  }

  function populateSizes() {
    const product = selectedProduct();
    const sizes = product ? product.variants.filter((variant) => variant.colour === colourSelect.value).map((variant) => variant.size) : [];
    sizeSelect.innerHTML = sizes.map((size) => `<option>${escapeHtml(size)}</option>`).join("");
    updateVariantInfo();
  }

  function updateVariantInfo() {
    const variant = selectedVariant();
    if (!variant) {
      availableStock.value = "0 pcs";
      updateItemPricingPreview();
      return;
    }
    const remaining = Math.max(variant.quantity - quantityInCart(variant.id), 0);
    availableStock.value = `${remaining} pcs`;
    updateItemPricingPreview();
  }

  function calculateCartSubtotal() {
    return round2(cart.reduce((sum, item) => sum + item.lineSubtotal, 0));
  }

  function calculateDiscountAmount() {
    return round2(cart.reduce((sum, item) => sum + item.discountAmount, 0));
  }

  function calculateTotalAmount() {
    return round2(cart.reduce((sum, item) => sum + item.lineTotal, 0));
  }

  function isSettlementPaymentMode() {
    return ["Cash", "UPI", "Card"].includes(paymentMode.value);
  }

  function calculateAcceptedDiscount(baseTotal) {
    const paid = Number(paidAmount.value || 0);
    if (!isSettlementPaymentMode() || paidAuto || paid <= 0 || paid >= baseTotal) return 0;
    return round2(baseTotal - paid);
  }

  function calculatePayableTotal(baseTotal = calculateTotalAmount()) {
    return round2(baseTotal - calculateAcceptedDiscount(baseTotal));
  }

  function updateGenerateButtonState() {
    if (!generateBillBtn) return;

    if (!cart.length) {
      generateBillBtn.disabled = true;
      generateBillBtn.textContent = "Add items to generate bill";
      return;
    }

    generateBillBtn.disabled = false;
    generateBillBtn.textContent = "Generate Bill";
  }

  function updatePaymentSummary() {
    const subtotal = calculateCartSubtotal();
    const itemDiscount = calculateDiscountAmount();
    const itemTotal = calculateTotalAmount();

    subtotalAmount.textContent = money(subtotal);
    discountAmount.textContent = money(itemDiscount);

    if (paymentMode.value === "Udhar") {
      paidAmount.value = "0.00";
      paidAuto = true;
    } else if (isSettlementPaymentMode() && paidAuto) {
      paidAmount.value = itemTotal.toFixed(2);
    }

    const acceptedDiscount = calculateAcceptedDiscount(itemTotal);
    const total = round2(itemTotal - acceptedDiscount);
    const paid = Number(paidAmount.value || 0);
    const pending = isSettlementPaymentMode() ? 0 : Math.max(round2(total - paid), 0);

    if (settlementDiscountRow && settlementDiscountAmount) {
      settlementDiscountRow.classList.toggle("hidden", acceptedDiscount <= 0);
      settlementDiscountAmount.textContent = money(acceptedDiscount);
    }

    billTotal.textContent = money(total);
    paidSummary.textContent = money(paid);
    pendingAmount.textContent = money(pending);
    customerBox.classList.toggle("hidden", !(pending > 0 || paymentMode.value === "Udhar"));
    mixedFields.classList.toggle("hidden", paymentMode.value !== "Mixed");

    updateReceiptPreview(subtotal, itemDiscount, total, paid, pending, acceptedDiscount);
    updateVariantInfo();
    updateGenerateButtonState();
  }

  function updateReceiptPreview(subtotal, discount, total, paid, pending, acceptedDiscount = 0) {
    if (!cart.length) {
      previewItems.innerHTML = `<p class="muted center-text">Cart items will appear here.</p>`;
    } else {
      previewItems.innerHTML = cart.map((item) => `
        <div class="receipt-item">
          <strong>${escapeHtml(item.name)}</strong>
          <div><span>${escapeHtml(item.colour)} / ${escapeHtml(item.size)} x${item.quantity}</span><span>${money(item.lineSubtotal)}</span></div>
          ${item.discountAmount > 0 ? `<div class="receipt-discount"><span>Discount</span><span>-${money(item.discountAmount)}</span></div><div><span>Item Total</span><span>${money(item.lineTotal)}</span></div>` : ""}
        </div>
      `).join("");
    }
    previewSubtotal.textContent = money(subtotal);
    previewDiscount.textContent = money(discount);
    if (previewSettlementRow && previewSettlementDiscount) {
      previewSettlementRow.classList.toggle("hidden", acceptedDiscount <= 0);
      previewSettlementDiscount.textContent = `-${money(acceptedDiscount)}`;
    }
    previewTotal.textContent = money(total);
    previewPaid.textContent = money(paid);
    previewPending.textContent = money(pending);
  }

  function renderCart() {
    if (!cart.length) {
      cartBody.innerHTML = `<tr><td colspan="7" class="empty-table">No items added.</td></tr>`;
      updatePaymentSummary();
      return;
    }

    cartBody.innerHTML = cart.map((item, index) => {
      const effectivePercent = item.defaultSellingPrice > 0
        ? round2((item.discountPerUnit / item.defaultSellingPrice) * 100)
        : 0;
      const discountLabel = item.discountAmount > 0
        ? `${effectivePercent.toFixed(2)}% / ${money(item.discountAmount)}`
        : "No discount";
      return `
        <tr>
          <td><strong>${escapeHtml(item.name)}</strong><br><span class="muted">${escapeHtml(item.colour)} / ${escapeHtml(item.size)}</span></td>
          <td><input class="cart-qty" type="number" min="1" value="${item.quantity}" data-cart-index="${index}"></td>
          <td class="table-currency">${money(item.defaultSellingPrice)}</td>
          <td class="table-currency">${discountLabel}</td>
          <td class="table-currency">${money(item.finalUnitPrice)}</td>
          <td class="table-currency">${money(item.lineTotal)}</td>
          <td><button class="btn btn-secondary compact" type="button" data-remove-cart="${index}">Remove</button></td>
        </tr>
      `;
    }).join("");
    updatePaymentSummary();
  }

  function addToCart() {
    const product = selectedProduct();
    const variant = selectedVariant();
    if (!product || !variant) {
      showToast("Select a product variant.", "error");
      return;
    }

    const quantity = Number(itemQty.value || 0);
    const alreadyAdded = quantityInCart(variant.id);
    const pricing = updateItemPricingPreview();

    if (quantity <= 0) {
      showToast("Quantity must be positive.", "error");
      return;
    }
    if (quantity + alreadyAdded > variant.quantity) {
      showToast(`Only ${variant.quantity} pieces available for this variant.`, "error");
      return;
    }
    if (pricing.error) {
      showToast(pricing.error, "error");
      return;
    }

    const discountType = itemDiscountType.value;
    const discountValue = Number(itemDiscountValue.value || 0);
    const customPrice = discountType === "custom_price"
      ? Number(customFinalPrice.value === "" ? pricing.finalUnitPrice : customFinalPrice.value)
      : "";
    const existingIndex = cart.findIndex((item) => (
      item.variantId === variant.id &&
      item.discountType === discountType &&
      round2(item.discountValue) === round2(discountValue) &&
      round2(item.finalUnitPrice) === round2(pricing.finalUnitPrice)
    ));

    if (existingIndex >= 0) {
      cart[existingIndex].quantity += quantity;
      refreshCartItemPricing(cart[existingIndex]);
    } else {
      cart.push({
        productId: product.id,
        variantId: variant.id,
        name: productLabel(product),
        brandName: product.brand_name,
        productName: product.product_name,
        colour: variant.colour,
        size: variant.size,
        quantity,
        defaultSellingPrice: pricing.defaultPrice,
        finalUnitPrice: pricing.finalUnitPrice,
        discountType,
        discountValue,
        customFinalPrice: customPrice,
        discountPerUnit: pricing.discountPerUnit,
        discountAmount: pricing.discountAmount,
        lineSubtotal: pricing.lineSubtotal,
        lineTotal: pricing.lineTotal,
        availableStock: variant.quantity,
      });
    }

    itemQty.value = 1;
    renderCart();
  }

  function refreshCartItemPricing(item) {
    const pricing = calculateItemPricing(
      item.defaultSellingPrice,
      item.quantity,
      item.discountType,
      item.discountValue,
      item.customFinalPrice
    );
    item.finalUnitPrice = pricing.finalUnitPrice;
    item.discountPerUnit = pricing.discountPerUnit;
    item.discountAmount = pricing.discountAmount;
    item.lineSubtotal = pricing.lineSubtotal;
    item.lineTotal = pricing.lineTotal;
  }

  function serializeCartForSubmit() {
    cartData.value = JSON.stringify(cart.map((item) => ({
      productId: item.productId,
      variantId: item.variantId,
      quantity: item.quantity,
      sellingPrice: item.finalUnitPrice,
      discountType: item.discountType,
      discountValue: item.discountValue,
      customFinalPrice: item.customFinalPrice,
    })));
  }

  function clearCartItems() {
    cart.length = 0;
    paidAuto = true;
    renderCart();
  }

  addCartItem?.addEventListener("click", addToCart);

  cartBody.addEventListener("input", (event) => {
    const input = event.target.closest(".cart-qty");
    if (!input) return;
    const index = Number(input.dataset.cartIndex);
    const item = cart[index];
    const nextQuantity = Math.max(1, Number(input.value || 1));
    const otherQuantity = quantityInCart(item.variantId, index);
    if (nextQuantity + otherQuantity > item.availableStock) {
      showToast(`Only ${item.availableStock} pieces available for this variant.`, "error");
      input.value = item.quantity;
      return;
    }
    item.quantity = nextQuantity;
    refreshCartItemPricing(item);
    renderCart();
  });

  cartBody.addEventListener("click", (event) => {
    const button = event.target.closest("[data-remove-cart]");
    if (!button) return;
    cart.splice(Number(button.dataset.removeCart), 1);
    renderCart();
  });

  clearCart?.addEventListener("click", clearCartItems);
  clearCartBtn?.addEventListener("click", clearCartItems);

  productSearch.addEventListener("input", populateProducts);
  productSelect.addEventListener("change", populateColours);
  colourSelect.addEventListener("change", populateSizes);
  sizeSelect.addEventListener("change", updateVariantInfo);
  itemQty.addEventListener("input", updateItemPricingPreview);
  itemDiscountType.addEventListener("change", () => {
    syncFinalPriceFromDiscount();
    updateItemPricingPreview();
  });
  itemDiscountValue.addEventListener("input", () => {
    syncFinalPriceFromDiscount();
    updateItemPricingPreview();
  });
  customFinalPrice.addEventListener("input", useReverseFinalPrice);
  paymentMode.addEventListener("change", () => {
    paidAuto = ["Cash", "UPI", "Card", "Udhar"].includes(paymentMode.value);
    if (!paidAuto && !paidAmount.value) paidAmount.value = "0.00";
    updatePaymentSummary();
  });
  paidAmount.addEventListener("input", () => {
    paidAuto = false;
    updatePaymentSummary();
  });
  mixedFields.addEventListener("input", updatePaymentSummary);

  billForm?.addEventListener("submit", (event) => {
    if (!cart.length) {
      event.preventDefault();
      showToast("Please add at least one item to cart", "error");
      return;
    }

    const baseTotal = calculateTotalAmount();
    const total = calculatePayableTotal(baseTotal);
    const paid = Number(paidAmount.value || 0);
    if (paid > total) {
      event.preventDefault();
      showToast("Paid amount cannot exceed total amount.", "error");
      return;
    }

    if (paymentMode.value === "Mixed") {
      const cash = Number(billForm.mixed_cash_amount.value || 0);
      const upi = Number(billForm.mixed_upi_amount.value || 0);
      const card = Number(billForm.mixed_card_amount.value || 0);
      if (round2(cash + upi + card) !== round2(paid)) {
        event.preventDefault();
        showToast("Mixed amounts must equal paid amount.", "error");
        return;
      }
    }

    const pending = isSettlementPaymentMode() ? 0 : round2(total - paid);
    if (pending > 0 || paymentMode.value === "Udhar") {
      const existing = billForm.customer_id.value;
      const name = billForm.customer_name.value.trim();
      const mobile = billForm.customer_mobile.value.trim();
      if (!existing && (!name || !mobile)) {
        event.preventDefault();
        showToast("Customer name and mobile are required for udhar.", "error");
        return;
      }
    }

    serializeCartForSubmit();
    generateBillBtn.disabled = true;
    generateBillBtn.textContent = "Generating...";
  });

  populateProducts();
  renderCart();
})();
