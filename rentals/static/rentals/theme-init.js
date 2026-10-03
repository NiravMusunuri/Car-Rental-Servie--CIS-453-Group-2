(() => {
  let saved = null;
  try { saved = localStorage.getItem("nhs-theme"); } catch (_) {}
  const preference = saved === "light" || saved === "dark" ? saved : null;
  document.documentElement.dataset.theme = preference || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
})();