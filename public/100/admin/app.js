"use strict";

const API_BASE = window.SLIDE_ADMIN_API || "https://slide-admin.103-142-26-14.sslip.io";
const LOCAL_KEY = "khanh-slide-admin-draft-v1";
const state = { config: null, published: null, selected: null, csrf: "", dirty: false };

const byId = id => document.getElementById(id);
const loginView = byId("login-view");
const workspace = byId("workspace");
const list = byId("slide-list");
const message = byId("message");

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (state.csrf) headers.set("X-CSRF-Token", state.csrf);
  const response = await fetch(`${API_BASE}${path}`, { credentials: "include", ...options, headers });
  const payload = response.status === 204 ? null : await response.json();
  if (!response.ok) throw new Error(payload?.error || "request_failed");
  return payload;
}

function safeLocalRead() {
  try { return JSON.parse(localStorage.getItem(LOCAL_KEY)); } catch (_) { return null; }
}
function safeLocalWrite(value) {
  try { localStorage.setItem(LOCAL_KEY, JSON.stringify(value)); } catch (_) { /* server draft remains canonical */ }
}

function customById(id) {
  return state.config.custom_slides.find(slide => slide.id === id);
}
function isCustom(id) { return Boolean(customById(id)); }
function displayTitle(id) {
  const custom = customById(id);
  if (custom) return custom.title;
  return state.config.overrides[id]?.title || id.split("-").map(word => word[0]?.toUpperCase() + word.slice(1)).join(" ");
}

function markDirty() {
  state.dirty = true;
  state.config.revision = `draft-${Date.now()}`;
  byId("draft-status").textContent = "Chưa lưu · có thay đổi";
  safeLocalWrite(state.config);
}

function selectSlide(id) {
  state.selected = id;
  renderList();
  renderProperties();
  renderPreview();
}

function moveSlide(id, delta) {
  const current = state.config.order.indexOf(id);
  const target = current + delta;
  if (current < 0 || target < 0 || target >= state.config.order.length) return;
  [state.config.order[current], state.config.order[target]] = [state.config.order[target], state.config.order[current]];
  markDirty();
  renderList();
}

function toggleSlide(id) {
  const index = state.config.hidden.indexOf(id);
  if (index >= 0) state.config.hidden.splice(index, 1);
  else state.config.hidden.push(id);
  markDirty();
  renderList();
  renderPreview();
}

function renderList() {
  list.replaceChildren();
  state.config.order.forEach((id, index) => {
    const item = element("li", `slide-item ${id}${isCustom(id) ? " custom" : ""}${state.config.hidden.includes(id) ? " hidden-slide" : ""}${state.selected === id ? " selected" : ""}`);
    item.dataset.slideId = id;
    item.draggable = true;
    item.tabIndex = 0;
    item.append(element("span", "slide-number", String(index + 1).padStart(2, "0")));
    item.append(element("span", "slide-name", displayTitle(id)));
    const actions = element("span", "item-actions");
    [["up", "↑", "Đưa lên"], ["down", "↓", "Đưa xuống"], ["toggle", state.config.hidden.includes(id) ? "Hiện" : "Ẩn", "Ẩn hoặc hiện"]].forEach(([action, label, title]) => {
      const button = element("button", "", label);
      button.type = "button";
      button.dataset.action = action;
      button.title = title;
      button.addEventListener("click", event => {
        event.stopPropagation();
        if (action === "up") moveSlide(id, -1);
        if (action === "down") moveSlide(id, 1);
        if (action === "toggle") toggleSlide(id);
      });
      actions.append(button);
    });
    item.append(actions);
    item.addEventListener("click", () => selectSlide(id));
    item.addEventListener("keydown", event => { if (event.key === "Enter") selectSlide(id); });
    item.addEventListener("dragstart", event => event.dataTransfer.setData("text/plain", id));
    item.addEventListener("dragover", event => event.preventDefault());
    item.addEventListener("drop", event => {
      event.preventDefault();
      const source = event.dataTransfer.getData("text/plain");
      const from = state.config.order.indexOf(source);
      const to = state.config.order.indexOf(id);
      if (from < 0 || to < 0 || from === to) return;
      state.config.order.splice(from, 1);
      state.config.order.splice(to, 0, source);
      markDirty();
      renderList();
    });
    list.append(item);
  });
}

const fields = {
  eyebrow: byId("field-eyebrow"), title: byId("field-title"),
  body: byId("field-body"), note: byId("field-note")
};

function renderProperties() {
  const id = state.selected;
  const custom = customById(id);
  fields.eyebrow.value = custom?.eyebrow || "";
  fields.title.value = custom?.title || state.config.overrides[id]?.title || displayTitle(id);
  fields.body.value = custom?.body.join("\n") || "";
  fields.note.value = custom?.note || "";
  fields.eyebrow.disabled = !custom;
  fields.body.disabled = !custom;
  fields.note.disabled = !custom;
  byId("field-image").disabled = !custom;
  byId("delete-slide").hidden = !custom;
}

function renderPreview() {
  const id = state.selected;
  const custom = customById(id);
  byId("preview-eyebrow").textContent = custom?.eyebrow || "Slide thiết kế gốc";
  byId("preview-title").textContent = displayTitle(id);
  const body = byId("preview-body");
  body.replaceChildren();
  (custom?.body || ["Nội dung thiết kế gốc được giữ nguyên trên trang công khai."]).forEach(line => body.append(element("p", "", line)));
  byId("preview-note").textContent = custom?.note || "";
  const image = byId("preview-image");
  if (custom?.image) {
    image.src = `../${custom.image}`;
    image.hidden = false;
  } else {
    image.removeAttribute("src");
    image.hidden = true;
  }
}

Object.entries(fields).forEach(([name, field]) => field.addEventListener("input", () => {
  const custom = customById(state.selected);
  if (custom) {
    custom[name] = name === "body" ? field.value.split("\n").map(line => line.trim()).filter(Boolean) : field.value;
  } else if (name === "title") {
    state.config.overrides[state.selected] = { title: field.value };
  }
  markDirty();
  renderPreview();
}));

byId("add-slide").addEventListener("click", () => {
  const id = `custom-${crypto.randomUUID()}`;
  state.config.custom_slides.push({ id, eyebrow: "Dấu mốc mới", title: "Slide mới", body: ["Nhập nội dung tại đây"], note: "", image: "" });
  state.config.order.push(id);
  markDirty();
  selectSlide(id);
});

byId("delete-slide").addEventListener("click", () => {
  if (!isCustom(state.selected)) return;
  state.config.custom_slides = state.config.custom_slides.filter(slide => slide.id !== state.selected);
  state.config.order = state.config.order.filter(id => id !== state.selected);
  state.config.hidden = state.config.hidden.filter(id => id !== state.selected);
  state.selected = state.config.order[0];
  markDirty();
  renderList(); renderProperties(); renderPreview();
});

byId("field-image").addEventListener("change", async event => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    const uploaded = await api("/images", { method: "POST", headers: { "Content-Type": file.type }, body: file });
    customById(state.selected).image = uploaded.path;
    markDirty(); renderPreview();
  } catch (_) { message.textContent = "Ảnh không hợp lệ hoặc vượt giới hạn."; }
});

async function saveDraft() {
  const saved = await api("/draft", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(state.config) });
  state.config = saved.draft;
  state.dirty = false;
  safeLocalWrite(state.config);
  byId("draft-status").textContent = "Đã lưu bản nháp";
  message.textContent = "Đã lưu bản nháp";
}
byId("save-draft").addEventListener("click", () => saveDraft().catch(() => { message.textContent = "Không thể lưu. Bản sửa vẫn còn trên máy này."; }));
byId("publish").addEventListener("click", async () => {
  try { await saveDraft(); const result = await api("/publish", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" }); message.textContent = `Đang triển khai · ${result.state}`; }
  catch (_) { message.textContent = "Xuất bản thất bại. Trang công khai chưa được xác nhận."; }
});
byId("rollback").addEventListener("click", async () => {
  if (!window.confirm("Hoàn tác lần xuất bản gần nhất?")) return;
  try { const result = await api("/rollback", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" }); message.textContent = `Đang hoàn tác · ${result.state}`; }
  catch (_) { message.textContent = "Không thể hoàn tác lúc này."; }
});

async function enterWorkspace(authenticated) {
  state.csrf = authenticated.csrf_token;
  const slides = await api("/slides");
  state.published = slides.published;
  state.config = safeLocalRead() || slides.draft || slides.published;
  state.selected = state.config.order[0];
  loginView.hidden = true;
  workspace.hidden = false;
  renderList(); renderProperties(); renderPreview();
}

byId("login-form").addEventListener("submit", async event => {
  event.preventDefault();
  byId("login-error").textContent = "";
  try {
    const result = await api("/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ password: byId("password").value }) });
    byId("password").value = "";
    await enterWorkspace(result);
  } catch (_) { byId("login-error").textContent = "Đăng nhập không thành công. Kiểm tra mật khẩu và thử lại."; }
});

byId("setup-form").addEventListener("submit", async event => {
  event.preventDefault();
  const password = byId("new-password");
  const confirmation = byId("confirm-password");
  byId("login-error").textContent = "";
  if (password.value !== confirmation.value) {
    byId("login-error").textContent = "Hai mật khẩu chưa khớp.";
    return;
  }
  try {
    const result = await api("/setup", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ password: password.value }) });
    password.value = "";
    confirmation.value = "";
    await enterWorkspace(result);
  } catch (_) {
    password.value = "";
    confirmation.value = "";
    byId("login-error").textContent = "Không thể tạo mật khẩu. Tải lại trang và thử lại.";
  }
});

api("/setup-status").then(status => {
  if (!status.setup_required) return;
  byId("login-title").textContent = "Tạo mật khẩu quản trị";
  byId("login-description").textContent = "Đây là lần thiết lập đầu tiên. Mật khẩu chỉ được gửi trực tiếp tới dịch vụ bảo mật và không lưu trong trình duyệt.";
  byId("login-form").hidden = true;
  byId("setup-form").hidden = false;
}).catch(() => {
  byId("login-error").textContent = "Không thể kiểm tra trạng thái dịch vụ. Vui lòng thử lại.";
});
