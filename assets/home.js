(function () {
  "use strict";
  const KEY = "horus-workspace-v1";
  const statuses = {
    todo: "Chưa bắt đầu",
    designing: "Đang thiết kế",
    review: "Chờ duyệt",
    revision: "Cần chỉnh sửa",
    done: "Hoàn thành",
  };
  const seed = () => ({
    version: 1,
    activeProjectId: "ks100",
    projects: [
      {
        id: "ks100",
        code: "KS100",
        name: "100 năm cà phê Khe Sanh",
        description: "Bộ nhận diện · Cà phê Khe Sanh, Hương vị hòa bình",
        groups: [
          {
            id: "core",
            name: "Nhận diện cốt lõi",
            items: [
              item("Logo & biểu tượng"),
              item("Màu sắc & typography"),
              item("Pattern & brand guidelines"),
            ],
          },
          {
            id: "media",
            name: "Truyền thông sự kiện",
            items: [
              item("Key visual & poster"),
              item("Banner & bài đăng mạng xã hội"),
              item("Video giới thiệu"),
            ],
          },
          {
            id: "space",
            name: "Không gian sự kiện",
            items: [
              item("Cổng chào & sân khấu"),
              item("Gian hàng & bảng chỉ dẫn"),
              item("Photobooth & check-in"),
            ],
          },
          {
            id: "gift",
            name: "Ấn phẩm & quà tặng",
            items: [
              item("Thư mời & vé tham dự"),
              item("Túi quà & bao bì cà phê"),
              item("Áo, mũ & quà lưu niệm"),
              item("Ví dụ"),
            ],
          },
        ],
      },
    ],
  });
  function item(name) {
    return { id: uid(), name, status: "todo", notes: "" };
  }
  function uid() {
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  }
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function button(label, action, className) {
    const node = el("button", className, label);
    node.type = "button";
    node.dataset.action = action;
    node.setAttribute("aria-label", label);
    return node;
  }
  let state = load(),
    view = "map",
    query = "",
    filter = "all",
    transform = matchMedia("(max-width: 700px)").matches
      ? { x: 0, y: 0, scale: 0.45 }
      : { x: 0, y: 0, scale: 1 },
    urls = [],
    editorUrls = [],
    reviewFiles = [],
    reviewIndex = 0,
    reviewUrl = "",
    reviewZoom = 1;
  const host = document.querySelector("[data-view-host]");
  function load() {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed.version === 1 && Array.isArray(parsed.projects))
          return parsed;
      }
    } catch (error) {
      setTimeout(
        () => notify("Không thể đọc dữ liệu đã lưu. Đang dùng dữ liệu mẫu."),
        0,
      );
    }
    const initial = seed();
    try {
      localStorage.setItem(KEY, JSON.stringify(initial));
    } catch (error) {
      // The workspace still works for this visit when browser storage is blocked.
    }
    return initial;
  }
  function persist(next) {
    try {
      localStorage.setItem(KEY, JSON.stringify(next));
      state = next;
      render();
      return true;
    } catch (error) {
      notify("Không thể lưu thay đổi. Dữ liệu trước đó vẫn được giữ nguyên.");
      return false;
    }
  }
  function active() {
    return (
      state.projects.find((project) => project.id === state.activeProjectId) ||
      state.projects[0]
    );
  }
  function notify(message) {
    const toast = document.querySelector(".toast");
    toast.textContent = message;
    toast.hidden = false;
    clearTimeout(notify.timer);
    notify.timer = setTimeout(() => {
      toast.hidden = true;
    }, 5000);
  }
  function allItems(project = active()) {
    return project ? project.groups.flatMap((group) => group.items) : [];
  }
  function filtered(items) {
    const needle = query.trim().toLocaleLowerCase("vi");
    return items.filter(
      (entry) =>
        (filter === "all" || entry.status === filter) &&
        (!needle || entry.name.toLocaleLowerCase("vi").includes(needle)),
    );
  }
  function render() {
    renderProjects();
    const project = active();
    if (!project) {
      renderEmpty();
      return;
    }
    document.querySelector("[data-project-code]").textContent =
      `DỰ ÁN / ${project.code}`;
    document.querySelector("[data-project-title]").textContent = project.name;
    document.querySelector("[data-project-description]").textContent =
      project.description;
    const items = allItems(project),
      done = items.filter((entry) => entry.status === "done").length;
    document.querySelector("[data-progress]").textContent =
      `${done} / ${items.length}`;
    document.querySelector("[data-progress-bar]").style.width =
      `${items.length ? (done / items.length) * 100 : 0}%`;
    document.querySelector(".board").hidden = false;
    renderLegend();
    renderView();
  }
  function renderProjects() {
    const tabs = document.querySelector("[data-project-tabs]");
    tabs.replaceChildren();
    state.projects.forEach((project) => {
      const tab = el("button");
      tab.type = "button";
      tab.role = "tab";
      tab.dataset.projectId = project.id;
      tab.setAttribute(
        "aria-selected",
        String(project.id === state.activeProjectId),
      );
      tab.append(el("b", null, project.name));
      tabs.append(tab);
    });
  }
  function renderEmpty() {
    document.querySelector(".project-summary").hidden = true;
    document.querySelector(".board").hidden = true;
    host.replaceChildren(
      el("div", "no-project", "Tạo dự án đầu tiên để bắt đầu."),
    );
  }
  function renderLegend() {
    const legend = document.querySelector(".legend");
    legend.replaceChildren();
    Object.entries(statuses).forEach(([key, label]) =>
      legend.append(el("i", `status-${key}`, label)),
    );
  }
  function renderView() {
    document
      .querySelectorAll("[data-view]")
      .forEach((tab) =>
        tab.setAttribute("aria-selected", String(tab.dataset.view === view)),
      );
    document.querySelector(".board-footer").hidden = view !== "map";
    urls.forEach(URL.revokeObjectURL);
    urls = [];
    if (view === "map") renderMap();
    if (view === "table") renderTable();
    if (view === "showcase") renderShowcase();
  }
  function renderMap() {
    const project = active(),
      viewport = el("div", "map-viewport");
    viewport.dataset.mapViewport = "";
    viewport.dataset.scale = String(transform.scale);
    viewport.dataset.x = String(transform.x);
    viewport.dataset.transform = JSON.stringify(transform);
    const stage = el("div", "map-stage");
    const layout = [];
    let cursorY = 32;
    project.groups.forEach((group) => {
      const visibleItems = filtered(group.items);
      const itemHeight = visibleItems.length ? visibleItems.length * 78 - 9 : 69;
      const groupTop = cursorY + Math.max(0, (itemHeight - 76) / 2);
      layout.push({ group, visibleItems, itemTop: cursorY, groupTop });
      cursorY += Math.max(itemHeight, 76) + 58;
    });
    const stageHeight = Math.max(660, cursorY + 18);
    const rootTop = Math.max(28, (stageHeight - 190) / 2);
    stage.style.height = `${stageHeight}px`;
    stage.style.transform = `translate(${transform.x}px,${transform.y}px) scale(${transform.scale})`;
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("map-lines");
    svg.setAttribute("viewBox", `0 0 1290 ${stageHeight}`);
    layout.forEach(({ visibleItems, itemTop, groupTop }) => {
      const groupCenter = groupTop + 38;
      line(svg, 306, rootTop + 95, 405, groupCenter);
      visibleItems.forEach((entry, itemIndex) =>
        line(svg, 665, groupCenter, 720, itemTop + itemIndex * 78 + 34),
      );
    });
    stage.append(svg);
    const root = el("article", "root-card");
    root.style.top = `${rootTop}px`;
    root.append(
      el(
        "small",
        null,
        `DỰ ÁN THIẾT KẾ · ${allItems(project).length} HẠNG MỤC`,
      ),
      el("h3", null, project.name),
      el("p", null, "Đang triển khai"),
    );
    const rootAdd = button("Thêm nhóm từ sơ đồ", "new-group", "root-add");
    rootAdd.textContent = "＋";
    root.append(rootAdd);
    stage.append(root);
    layout.forEach(({ group, visibleItems, itemTop, groupTop }, index) => {
      const groupCard = el("article", "group-card");
      groupCard.dataset.groupCard = "";
      groupCard.dataset.groupId = group.id;
      groupCard.style.top = `${groupTop}px`;
      groupCard.append(
        el("span", "number", String(index + 1).padStart(2, "0")),
        el("h3", null, group.name),
        el("small", null, `${group.items.length} hạng mục`),
      );
      const actions = el("div", "group-actions");
      const add = button("Thêm hạng mục", "new-item");
      add.textContent = "＋";
      add.dataset.groupId = group.id;
      const edit = button("Sửa nhóm", "edit-group");
      edit.textContent = "✎";
      edit.dataset.groupId = group.id;
      const remove = button("Xóa nhóm", "delete-group");
      remove.textContent = "×";
      remove.dataset.groupId = group.id;
      actions.append(edit, remove, add);
      groupCard.append(actions);
      stage.append(groupCard);
      visibleItems.forEach((entry, itemIndex) => {
        const card = el("article", `item-card status-${entry.status}`);
        card.dataset.itemCard = "";
        card.dataset.itemId = entry.id;
        card.dataset.groupId = group.id;
        card.style.top = `${itemTop + itemIndex * 78}px`;
        card.append(
          el("span", "cube", "◇"),
          el("h4", null, entry.name),
          el("small", null, statuses[entry.status]),
        );
        const itemEdit = button(
          `Sửa hạng mục ${entry.name}`,
          "edit-item",
          "item-edit-button",
        );
        itemEdit.textContent = "✎";
        itemEdit.dataset.itemId = entry.id;
        itemEdit.dataset.groupId = group.id;
        card.append(itemEdit);
        stage.append(card);
      });
    });
    viewport.append(stage);
    host.replaceChildren(viewport);
    enablePan(viewport, stage);
  }
  function line(svg, x1, y1, x2, y2) {
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute(
      "d",
      `M${x1} ${y1} C${(x1 + x2) / 2} ${y1},${(x1 + x2) / 2} ${y2},${x2} ${y2}`,
    );
    svg.append(path);
  }
  function enablePan(viewport, stage) {
    let start = null;
    const update = () => {
      stage.style.transform = `translate(${transform.x}px,${transform.y}px) scale(${transform.scale})`;
      viewport.dataset.x = String(transform.x);
      viewport.dataset.scale = String(transform.scale);
      viewport.dataset.transform = JSON.stringify(transform);
      document.querySelector("[data-zoom]").textContent =
        `${Math.round(transform.scale * 100)}%`;
    };
    viewport.addEventListener("pointerdown", (event) => {
      if (event.target.closest("button,.item-card")) return;
      start = {
        x: event.clientX,
        y: event.clientY,
        tx: transform.x,
        ty: transform.y,
      };
      viewport.setPointerCapture(event.pointerId);
    });
    viewport.addEventListener("pointermove", (event) => {
      if (!start) return;
      transform.x = start.tx + event.clientX - start.x;
      transform.y = start.ty + event.clientY - start.y;
      update();
    });
    viewport.addEventListener("pointerup", () => {
      start = null;
    });
    viewport.addEventListener(
      "wheel",
      (event) => {
        event.preventDefault();
        transform.scale = Math.min(
          1.6,
          Math.max(0.5, transform.scale + (event.deltaY < 0 ? 0.1 : -0.1)),
        );
        update();
      },
      { passive: false },
    );
    update();
  }
  function renderTable() {
    const wrap = el("div", "table-wrap"),
      table = el("table", "data-table");
    table.setAttribute("aria-label", "Danh sách hạng mục");
    const head = el("thead"),
      tr = el("tr");
    ["Hạng mục", "Nhóm", "Trạng thái"].forEach((label) =>
      tr.append(el("th", null, label)),
    );
    head.append(tr);
    const body = el("tbody");
    active().groups.forEach((group) =>
      filtered(group.items).forEach((entry) => {
        const row = el("tr");
        row.dataset.itemId = entry.id;
        row.dataset.groupId = group.id;
        const status = el(
          "button",
          `status-pill status-${entry.status}`,
          statuses[entry.status],
        );
        status.type = "button";
        status.dataset.action = "edit-item";
        status.dataset.itemId = entry.id;
        status.dataset.groupId = group.id;
        const statusCell = el("td");
        statusCell.append(status);
        row.append(
          el("td", null, entry.name),
          el("td", null, group.name),
          statusCell,
        );
        body.append(row);
      }),
    );
    table.append(head, body);
    wrap.append(table);
    host.replaceChildren(wrap);
  }
  async function renderShowcase() {
    const showcase = el("div", "showcase"),
      head = el("div", "showcase-head");
    head.append(el("h3", null, "Showcase dự án"));
    const upload = el("label", "button primary upload-button", "＋ Thêm ảnh");
    const input = el("input");
    input.type = "file";
    input.accept = "image/*";
    input.multiple = true;
    input.setAttribute("aria-label", "Thêm ảnh showcase");
    upload.append(input);
    head.append(upload);
    const gallery = el("div", "gallery");
    showcase.append(head, gallery);
    host.replaceChildren(showcase);
    input.addEventListener("change", uploadImages);
    try {
      const rows = await window.HorusDB.list(active().id);
      const images = rows.filter((row) =>
        (row.mimeType || row.blob.type).startsWith("image/"),
      );
      if (!images.length)
        gallery.append(
          el("p", "empty", "Chưa có hình ảnh. Hãy thêm thiết kế đầu tiên."),
        );
      images.forEach((row) => {
        const figure = el("figure"),
          img = el("img");
        const url = URL.createObjectURL(row.blob);
        urls.push(url);
        img.src = url;
        img.alt = row.name;
        figure.append(img, el("figcaption", null, row.name));
        gallery.append(figure);
      });
    } catch (error) {
      notify("Không thể đọc thư viện ảnh trên thiết bị này.");
    }
  }
  async function uploadImages(event) {
    for (const file of event.target.files) {
      if (!file.type.startsWith("image/") || file.size > 8 * 1024 * 1024) {
        notify("Chỉ chấp nhận ảnh nhỏ hơn 8 MB.");
        continue;
      }
      try {
        await window.HorusDB.put({
          id: uid(),
          projectId: active().id,
          name: file.name,
          mimeType: file.type,
          size: file.size,
          createdAt: Date.now(),
          blob: file,
        });
      } catch (error) {
        notify("Không thể lưu ảnh trên thiết bị này.");
        return;
      }
    }
    renderShowcase();
  }
  function field(label, name, value, type = "text") {
    const wrap = el("label");
    wrap.append(document.createTextNode(label));
    const control = type === "textarea" ? el("textarea") : el("input");
    control.name = name;
    control.value = value || "";
    control.required = name !== "notes";
    wrap.append(control);
    return wrap;
  }
  function statusField(value) {
    const wrap = el("label");
    wrap.append(document.createTextNode("Trạng thái"));
    const select = el("select");
    select.name = "status";
    select.setAttribute("aria-label", "Trạng thái");
    Object.entries(statuses).forEach(([key, label]) => {
      const option = el("option", null, label);
      option.value = key;
      option.selected = key === value;
      select.append(option);
    });
    wrap.append(select);
    return wrap;
  }
  function formatBytes(size) {
    if (!size) return "0 KB";
    if (size < 1024 * 1024)
      return `${Math.max(1, Math.round(size / 1024))} KB`;
    return `${(size / 1024 / 1024).toFixed(1)} MB`;
  }
  function clearEditorUrls() {
    editorUrls.forEach(URL.revokeObjectURL);
    editorUrls = [];
  }
  async function renderItemMedia(itemId, panel) {
    clearEditorUrls();
    const grid = panel.querySelector("[data-item-media-grid]");
    grid.replaceChildren(el("p", "item-media-empty", "Đang tải tệp…"));
    try {
      const rows = await window.HorusDB.listItem(itemId);
      grid.replaceChildren();
      if (!rows.length) {
        grid.append(el("p", "item-media-empty", "Chưa có ảnh hoặc PDF."));
        return;
      }
      rows.forEach((row, index) => {
        const tile = el("article", "item-media-tile");
        const preview = button(`Xem ${row.name}`, null, "item-media-preview");
        preview.type = "button";
        preview.textContent = "";
        if ((row.mimeType || row.blob.type).startsWith("image/")) {
          const image = el("img");
          const url = URL.createObjectURL(row.blob);
          editorUrls.push(url);
          image.src = url;
          image.alt = "";
          preview.append(image);
        } else {
          preview.append(el("span", "pdf-badge", "PDF"));
        }
        preview.append(el("span", "item-media-name", row.name));
        preview.addEventListener("click", () => openMediaReview(rows, index));
        const meta = el(
          "small",
          null,
          formatBytes(row.size || row.blob.size),
        );
        const remove = button(`Xóa ${row.name}`, null, "item-media-remove");
        remove.type = "button";
        remove.textContent = "×";
        remove.addEventListener("click", async () => {
          await window.HorusDB.remove(row.id);
          await renderItemMedia(itemId, panel);
        });
        tile.append(preview, meta, remove);
        grid.append(tile);
      });
    } catch (error) {
      grid.replaceChildren(
        el("p", "item-media-empty", "Không thể đọc tệp trên thiết bị này."),
      );
    }
  }
  function itemMediaPanel(itemId) {
    const panel = el("section", "item-media-panel");
    panel.append(el("h4", null, "Ảnh & tài liệu sản phẩm"));
    if (!itemId) {
      panel.append(
        el(
          "p",
          "item-media-empty",
          "Lưu hạng mục trước, sau đó mở lại để tải tệp.",
        ),
      );
      return panel;
    }
    const upload = el("label", "item-upload-zone");
    upload.append(
      el("strong", null, "Kéo thả hoặc chọn nhiều tệp"),
      el("span", null, "Ảnh JPG, PNG, WebP… hoặc PDF · tối đa 25 MB/tệp"),
    );
    const input = el("input");
    input.type = "file";
    input.multiple = true;
    input.accept = "image/*,application/pdf";
    input.setAttribute("aria-label", "Tải ảnh hoặc PDF cho hạng mục");
    upload.append(input);
    const grid = el("div", "item-media-grid");
    grid.dataset.itemMediaGrid = "";
    panel.append(upload, grid);
    input.addEventListener("change", async () => {
      for (const file of input.files) {
        const accepted =
          file.type.startsWith("image/") || file.type === "application/pdf";
        if (!accepted || file.size > 25 * 1024 * 1024) {
          notify(`${file.name}: chỉ nhận ảnh/PDF tối đa 25 MB.`);
          continue;
        }
        try {
          await window.HorusDB.put({
            id: uid(),
            projectId: active().id,
            itemId,
            name: file.name,
            mimeType: file.type,
            size: file.size,
            createdAt: Date.now(),
            blob: file,
          });
        } catch (error) {
          notify("Không thể lưu tệp trên thiết bị này.");
          break;
        }
      }
      input.value = "";
      await renderItemMedia(itemId, panel);
    });
    renderItemMedia(itemId, panel);
    return panel;
  }
  function openMediaReview(rows, index) {
    reviewFiles = rows;
    reviewIndex = index;
    reviewZoom = 1;
    renderMediaReview();
    document.querySelector("#media-review-dialog").showModal();
  }
  function renderMediaReview() {
    const dialog = document.querySelector("#media-review-dialog"),
      stage = dialog.querySelector("[data-review-stage]"),
      row = reviewFiles[reviewIndex];
    if (!row) return;
    if (reviewUrl) URL.revokeObjectURL(reviewUrl);
    reviewUrl = URL.createObjectURL(row.blob);
    stage.replaceChildren();
    const isImage = (row.mimeType || row.blob.type).startsWith("image/");
    if (isImage) {
      const image = el("img");
      image.src = reviewUrl;
      image.alt = row.name;
      image.dataset.reviewImage = "";
      image.dataset.zoom = String(reviewZoom);
      image.style.transform = `scale(${reviewZoom})`;
      stage.append(image);
    } else {
      const frame = el("iframe");
      frame.src = reviewUrl;
      frame.title = row.name;
      stage.append(frame);
    }
    dialog.querySelector("[data-review-count]").textContent =
      `${reviewIndex + 1} / ${reviewFiles.length}`;
    dialog.querySelector("[data-review-caption]").textContent =
      `${row.name} · ${formatBytes(row.size || row.blob.size)}`;
    const download = dialog.querySelector("[data-review-download]");
    download.href = reviewUrl;
    download.download = row.name;
    dialog.querySelector("[data-review-zoom-in]").disabled = !isImage;
    dialog.querySelector("[data-review-zoom-out]").disabled = !isImage;
  }
  function openEditor(kind, data = {}) {
    const dialog = document.querySelector("#editor-dialog"),
      fields = dialog.querySelector("[data-form-fields]");
    fields.replaceChildren();
    dialog.dataset.kind = kind;
    dialog.dataset.id = data.id || "";
    dialog.dataset.groupId = data.groupId || "";
    const titles = {
      project: data.id ? "Sửa dự án" : "Dự án mới",
      group: data.id ? "Sửa nhóm" : "Nhóm mới",
      item: data.id ? "Sửa hạng mục" : "Hạng mục mới",
    };
    document.querySelector("#editor-title").textContent = titles[kind];
    if (kind === "project")
      fields.append(
        field("Tên dự án", "name", data.name),
        field("Mã dự án", "code", data.code),
        field("Mô tả", "description", data.description, "textarea"),
      );
    if (kind === "group") fields.append(field("Tên nhóm", "name", data.name));
    if (kind === "item")
      fields.append(
        field("Tên hạng mục", "name", data.name),
        statusField(data.status || "todo"),
        field("Ghi chú", "notes", data.notes, "textarea"),
        itemMediaPanel(data.id),
      );
    dialog.showModal();
  }
  function saveEditor(dialog) {
    const values = Object.fromEntries(
      new FormData(dialog.querySelector("form")),
    );
    if (!String(values.name || "").trim()) return;
    const next = structuredClone(state),
      project = next.projects.find(
        (entry) => entry.id === next.activeProjectId,
      );
    if (dialog.dataset.kind === "project") {
      if (dialog.dataset.id) {
        Object.assign(project, values);
      } else {
        const created = {
          id: uid(),
          name: values.name,
          code: values.code,
          description: values.description,
          groups: [],
        };
        next.projects.push(created);
        next.activeProjectId = created.id;
      }
    }
    if (dialog.dataset.kind === "group") {
      if (dialog.dataset.id)
        project.groups.find((entry) => entry.id === dialog.dataset.id).name =
          values.name;
      else project.groups.push({ id: uid(), name: values.name, items: [] });
    }
    if (dialog.dataset.kind === "item") {
      const group = project.groups.find(
        (entry) => entry.id === dialog.dataset.groupId,
      );
      if (dialog.dataset.id)
        Object.assign(
          group.items.find((entry) => entry.id === dialog.dataset.id),
          values,
        );
      else
        group.items.push({
          id: uid(),
          name: values.name,
          status: values.status,
          notes: values.notes,
        });
    }
    persist(next);
  }
  function confirmAction(title, copy, label, callback) {
    const dialog = document.querySelector("#confirm-dialog");
    document.querySelector("#confirm-title").textContent = title;
    dialog.querySelector("[data-confirm-copy]").textContent = copy;
    const confirm = dialog.querySelector("[data-confirm-button]");
    confirm.textContent = label;
    dialog._callback = callback;
    dialog.showModal();
  }
  function findGroup(id) {
    return active().groups.find((group) => group.id === id);
  }
  function handleAction(target) {
    const action = target.dataset.action;
    if (action === "new-project") openEditor("project");
    if (action === "edit-project") openEditor("project", active());
    if (action === "delete-project")
      confirmAction(
        "Xóa dự án?",
        "Dự án và mọi hạng mục sẽ bị xóa khỏi thiết bị này.",
        "Xác nhận xóa",
        () => {
          const next = structuredClone(state);
          next.projects = next.projects.filter(
            (entry) => entry.id !== active().id,
          );
          next.activeProjectId = next.projects[0]?.id || "";
          persist(next);
        },
      );
    if (action === "new-group") openEditor("group");
    if (action === "edit-group")
      openEditor("group", findGroup(target.dataset.groupId));
    if (action === "delete-group")
      confirmAction(
        "Xóa nhóm?",
        "Mọi hạng mục trong nhóm cũng sẽ bị xóa.",
        "Xác nhận xóa",
        () => {
          const next = structuredClone(state),
            project = next.projects.find(
              (entry) => entry.id === next.activeProjectId,
            );
          project.groups = project.groups.filter(
            (entry) => entry.id !== target.dataset.groupId,
          );
          persist(next);
        },
      );
    if (action === "new-item")
      openEditor("item", { groupId: target.dataset.groupId });
    if (action === "edit-item") {
      const group = findGroup(target.dataset.groupId),
        entry = group.items.find((row) => row.id === target.dataset.itemId);
      openEditor("item", { ...entry, groupId: group.id });
    }
    if (action === "zoom-in" || action === "zoom-out") {
      transform.scale = Math.min(
        1.6,
        Math.max(0.5, transform.scale + (action === "zoom-in" ? 0.1 : -0.1)),
      );
      renderMap();
    }
    if (action === "fit-map") {
      transform = { x: 0, y: 0, scale: 1 };
      renderMap();
    }
    if (action === "reset")
      confirmAction(
        "Khôi phục dữ liệu mẫu?",
        "Mọi thay đổi hiện tại và ảnh showcase sẽ bị xóa.",
        "Xác nhận khôi phục",
        async () => {
          try {
            localStorage.removeItem(KEY);
            await window.HorusDB.clear();
          } catch (error) {
            notify("Không thể xóa toàn bộ dữ liệu đã lưu.");
            return;
          }
          state = seed();
          view = "map";
          render();
        },
      );
  }
  document.addEventListener("click", (event) => {
    const projectTab = event.target.closest("[data-project-id]");
    if (projectTab) {
      state.activeProjectId = projectTab.dataset.projectId;
      persist(state);
      return;
    }
    const viewTab = event.target.closest("[data-view]");
    if (viewTab) {
      view = viewTab.dataset.view;
      renderView();
      return;
    }
    const itemCard = event.target.closest("[data-item-card]");
    if (itemCard) {
      handleAction({
        dataset: {
          action: "edit-item",
          groupId: itemCard.dataset.groupId,
          itemId: itemCard.dataset.itemId,
        },
      });
      return;
    }
    const action = event.target.closest("[data-action]");
    if (action) handleAction(action);
  });
  document
    .querySelector("#editor-dialog")
    .addEventListener("close", (event) => {
      if (event.target.returnValue === "save") saveEditor(event.target);
      clearEditorUrls();
    });
  const reviewDialog = document.querySelector("#media-review-dialog");
  reviewDialog
    .querySelector("[data-review-close]")
    .addEventListener("click", () => reviewDialog.close());
  reviewDialog
    .querySelector("[data-review-prev]")
    .addEventListener("click", () => {
      reviewIndex = (reviewIndex - 1 + reviewFiles.length) % reviewFiles.length;
      reviewZoom = 1;
      renderMediaReview();
    });
  reviewDialog
    .querySelector("[data-review-next]")
    .addEventListener("click", () => {
      reviewIndex = (reviewIndex + 1) % reviewFiles.length;
      reviewZoom = 1;
      renderMediaReview();
    });
  reviewDialog
    .querySelector("[data-review-zoom-in]")
    .addEventListener("click", () => {
      reviewZoom = Math.min(3, reviewZoom + 0.25);
      renderMediaReview();
    });
  reviewDialog
    .querySelector("[data-review-zoom-out]")
    .addEventListener("click", () => {
      reviewZoom = Math.max(0.5, reviewZoom - 0.25);
      renderMediaReview();
    });
  reviewDialog.addEventListener("close", () => {
    if (reviewUrl) URL.revokeObjectURL(reviewUrl);
    reviewUrl = "";
  });
  document
    .querySelector("#confirm-dialog")
    .addEventListener("close", (event) => {
      if (event.target.returnValue === "confirm") event.target._callback();
    });
  document
    .querySelector("[aria-label='Tìm hạng mục']")
    .addEventListener("input", (event) => {
      query = event.target.value;
      renderView();
    });
  document
    .querySelector("[aria-label='Lọc trạng thái']")
    .addEventListener("change", (event) => {
      filter = event.target.value;
      renderView();
    });
  render();
})();
