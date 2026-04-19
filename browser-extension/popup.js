chrome.storage.sync.get(["apiUrl", "token"], (s) => {
  document.getElementById("apiUrl").value = s.apiUrl || "";
  document.getElementById("token").value = s.token || "";
});
document.getElementById("save").onclick = () => {
  chrome.storage.sync.set({
    apiUrl: document.getElementById("apiUrl").value.trim().replace(/\/$/, ""),
    token: document.getElementById("token").value.trim(),
  }, () => window.close());
};
