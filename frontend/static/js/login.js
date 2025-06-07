document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  const loginError = document.getElementById("loginError");

  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    loginError.textContent = "";

    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value.trim();

    if (!email || !password) {
      loginError.textContent = "Please enter both email and password.";
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        // Save token/session as needed (example using sessionStorage)
        sessionStorage.setItem("idToken", data.idToken || "");
        // Redirect user after successful login
        window.location.href = "/"; // or your dashboard/home page route
      } else {
        loginError.textContent = data.detail || "Login failed. Please try again.";
      }
    } catch (error) {
      loginError.textContent = "Server error. Please try again later.";
      console.error("Login error:", error);
    }
  });

  // TODO: Implement signup form handling similarly if needed
});
