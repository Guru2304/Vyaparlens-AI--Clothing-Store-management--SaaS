(function () {
  const printButton = document.getElementById("printReceipt");
  const downloadButton = document.getElementById("downloadReceipt");
  const paper = document.getElementById("receiptPaper");

  printButton?.addEventListener("click", () => window.print());

  downloadButton?.addEventListener("click", () => {
    const text = paper.innerText.trim();
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "receipt.txt";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  });
})();
