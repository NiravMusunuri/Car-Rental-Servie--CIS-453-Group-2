(() => {
  const button = document.getElementById("theme-toggle");
  if (!button) return;
  const system = window.matchMedia("(prefers-color-scheme: dark)");
  const updateLabel = () => {
    const dark = document.documentElement.dataset.theme === "dark";
    button.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
    button.querySelector(".theme-label").textContent = dark ? "Light mode" : "Dark mode";
  };
  button.hidden = false;
  updateLabel();
  button.addEventListener("click", () => {
    const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("nhs-theme", theme); } catch (_) {}
    updateLabel();
  });
  system.addEventListener("change", (event) => {
    let saved;
    try { saved = localStorage.getItem("nhs-theme"); } catch (_) {}
    if (saved !== "light" && saved !== "dark") {
      document.documentElement.dataset.theme = event.matches ? "dark" : "light";
      updateLabel();
    }
  });
})();