/* RO extension background — context menu + API calls. */
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "ro-rate",
    title: 'Rate "%s" in RO',
    contexts: ["selection"],
  });
  chrome.contextMenus.create({
    id: "ro-add",
    title: 'Add "%s" to My List',
    contexts: ["selection"],
  });
});

async function apiBase() {
  const { apiUrl } = await chrome.storage.sync.get("apiUrl");
  return apiUrl || "http://localhost:8000";
}

async function token() {
  const { token } = await chrome.storage.sync.get("token");
  return token;
}

async function searchByTitle(title) {
  const base = await apiBase();
  const tok = await token();
  const r = await fetch(`${base}/search/suggest?q=${encodeURIComponent(title)}&limit=1`, {
    headers: tok ? { Authorization: `Bearer ${tok}` } : {},
  });
  if (!r.ok) return null;
  const data = await r.json();
  return data.items?.[0] || null;
}

chrome.contextMenus.onClicked.addListener(async (info) => {
  const title = (info.selectionText || "").trim();
  if (!title) return;
  const match = await searchByTitle(title);
  if (!match) {
    chrome.notifications?.create?.({
      type: "basic", iconUrl: "icon-48.png", title: "RO", message: `No match for "${title}"`,
    });
    return;
  }
  const base = await apiBase();
  const tok = await token();
  if (info.menuItemId === "ro-add") {
    await fetch(`${base}/users/me/watchlist/${match.id}`, {
      method: "POST", headers: tok ? { Authorization: `Bearer ${tok}` } : {},
    });
  } else if (info.menuItemId === "ro-rate") {
    // Send to content page to open rating popup
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]?.id) chrome.tabs.sendMessage(tabs[0].id, { type: "ro-rate", match });
    });
  }
});
