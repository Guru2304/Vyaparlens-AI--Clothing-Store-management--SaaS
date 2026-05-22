(function () {
  const tabButtons = document.querySelectorAll("[data-auth-tab]");
  const loginForm = document.getElementById("loginForm");
  const signupForm = document.getElementById("signupForm");

  tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      tabButtons.forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      const isLogin = button.dataset.authTab === "login";
      loginForm.classList.toggle("active", isLogin);
      signupForm.classList.toggle("active", !isLogin);
    });
  });

  signupForm?.addEventListener("submit", (event) => {
    const email = signupForm.email.value.trim();
    const password = signupForm.password.value;
    const mobile = signupForm.mobile.value.trim();
    if (!email.includes("@") || !email.includes(".")) {
      event.preventDefault();
      alert("Enter a valid email address.");
    } else if (password.length < 6) {
      event.preventDefault();
      alert("Password must be at least 6 characters.");
    } else if (!mobile) {
      event.preventDefault();
      alert("Mobile number is required.");
    }
  });
})();
