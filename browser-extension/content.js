/* RO content-script — injects a minimal rate-in-place popup. */
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type !== "ro-rate" || !msg.match) return;
  const m = msg.match;
  const existing = document.getElementById("ro-rate-popup");
  if (existing) existing.remove();
  const el = document.createElement("div");
  el.id = "ro-rate-popup";
  el.style.cssText = "position:fixed;bottom:20px;right:20px;z-index:2147483647;background:#1f1f1f;color:#fff;padding:16px;border-radius:12px;box-shadow:0 10px 40px rgba(0,0,0,.5);font-family:system-ui;min-width:260px;max-width:320px;";
  el.innerHTML = `
    <div style="font-weight:700;font-size:14px;margin-bottom:4px">Rate "${m.title}"</div>
    <div style="font-size:12px;color:#888;margin-bottom:10px">${m.release_year || ""}</div>
    <div id="ro-stars" style="font-size:20px;color:#444;cursor:pointer">★★★★★</div>
    <button id="ro-close" style="margin-top:10px;font-size:11px;color:#888;background:none;border:0;cursor:pointer">dismiss</button>
  `;
  document.body.appendChild(el);
  el.querySelector("#ro-close").onclick = () => el.remove();
  const stars = el.querySelectorAll("#ro-stars");
  el.querySelector("#ro-stars").onclick = async (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    const rating = Math.max(1, Math.min(5, Math.ceil(pct * 5)));
    const { apiUrl, token } = await chrome.storage.sync.get(["apiUrl", "token"]);
    await fetch((apiUrl || "http://localhost:8000") + `/users/me/ratings/${m.id}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ rating }),
    });
    el.innerHTML = `<div style="font-size:13px">✓ Rated "${m.title}" ${rating}★</div>`;
    setTimeout(() => el.remove(), 1500);
  };
});
