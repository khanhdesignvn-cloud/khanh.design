(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.SlideConfig = api;
})(typeof window === "undefined" ? globalThis : window, function () {
  "use strict";

  const TEXT_LIMITS = { eyebrow: 120, title: 240, body: 2000, note: 300 };
  const ID_PATTERN = /^[a-z0-9][a-z0-9-]{1,79}$/;
  const IMAGE_PATTERN = /^assets\/admin\/[a-f0-9-]+\.(?:jpe?g|png|webp)$/i;
  const MARKUP_PATTERN = /[<>]/;

  function fail(message) {
    throw new TypeError(message);
  }

  function validText(value, field, required) {
    if (value == null && !required) return;
    if (typeof value !== "string" || (required && !value.trim())) fail(`invalid_${field}`);
    if (value.length > TEXT_LIMITS[field] || MARKUP_PATTERN.test(value)) fail(`invalid_${field}`);
  }

  function validateConfig(config, knownIds) {
    if (!config || typeof config !== "object" || Array.isArray(config)) fail("invalid_config");
    if (config.schema_version !== 1) fail("invalid_schema_version");
    if (typeof config.revision !== "string" || !config.revision || config.revision.length > 120) fail("invalid_revision");
    if (!Array.isArray(knownIds) || new Set(knownIds).size !== knownIds.length) fail("invalid_known_ids");
    if (!Array.isArray(config.custom_slides)) fail("invalid_custom_slides");

    const customIds = [];
    for (const slide of config.custom_slides) {
      if (!slide || typeof slide !== "object" || !ID_PATTERN.test(slide.id || "")) fail("invalid_custom_id");
      customIds.push(slide.id);
      validText(slide.eyebrow || "", "eyebrow", false);
      validText(slide.title, "title", true);
      if (!Array.isArray(slide.body) || slide.body.length > 12) fail("invalid_body");
      slide.body.forEach(value => validText(value, "body", true));
      validText(slide.note || "", "note", false);
      if (slide.image && (typeof slide.image !== "string" || !IMAGE_PATTERN.test(slide.image))) fail("invalid_image");
    }

    const allIds = knownIds.concat(customIds);
    if (new Set(allIds).size !== allIds.length) fail("duplicate_id");
    if (!Array.isArray(config.order) || config.order.length !== allIds.length) fail("missing_id");
    if (new Set(config.order).size !== config.order.length) fail("duplicate_order_id");
    if (config.order.some(id => !allIds.includes(id))) fail("unknown_id");
    if (allIds.some(id => !config.order.includes(id))) fail("missing_id");
    if (!Array.isArray(config.hidden) || new Set(config.hidden).size !== config.hidden.length) fail("invalid_hidden");
    if (config.hidden.some(id => !allIds.includes(id))) fail("unknown_hidden_id");
    if (!config.overrides || typeof config.overrides !== "object" || Array.isArray(config.overrides)) fail("invalid_overrides");
    for (const [id, override] of Object.entries(config.overrides)) {
      if (!knownIds.includes(id) || !override || typeof override !== "object") fail("invalid_override");
      if (Object.keys(override).some(key => key !== "title")) fail("invalid_override_field");
      validText(override.title, "title", true);
    }
    return config;
  }

  function makeCustomSlide(slide) {
    const section = document.createElement("section");
    section.className = "s light admin-custom-slide";
    section.dataset.slideId = slide.id;
    section.dataset.t = slide.title;

    const chapter = document.createElement("div");
    chapter.className = "chap";
    const number = document.createElement("span");
    number.className = "num";
    const title = document.createElement("span");
    title.className = "ttl";
    title.textContent = slide.title;
    const rule = document.createElement("span");
    rule.className = "rule";
    chapter.append(number, title, rule);

    const layout = document.createElement("div");
    layout.className = "user-page-layout";
    if (slide.image) {
      const figure = document.createElement("figure");
      figure.className = "user-board";
      const image = document.createElement("img");
      image.src = slide.image;
      image.alt = slide.title;
      figure.append(image);
      layout.append(figure);
    }
    const notes = document.createElement("aside");
    notes.className = "user-notes";
    if (slide.eyebrow) {
      const eyebrow = document.createElement("div");
      eyebrow.className = "eyebrow";
      eyebrow.textContent = slide.eyebrow;
      notes.append(eyebrow);
    }
    const heading = document.createElement("h2");
    heading.textContent = slide.title;
    notes.append(heading);
    const list = document.createElement("ul");
    slide.body.forEach(text => {
      const item = document.createElement("li");
      item.textContent = text;
      list.append(item);
    });
    notes.append(list);
    if (slide.note) {
      const note = document.createElement("div");
      note.className = "note-foot";
      note.textContent = slide.note;
      notes.append(note);
    }
    layout.append(notes);
    section.append(chapter, layout);
    return section;
  }

  function applyConfig(config) {
    const base = Array.from(document.querySelectorAll("section.s[data-slide-id]"));
    const knownIds = base.map(slide => slide.dataset.slideId);
    validateConfig(config, knownIds);
    const nodes = new Map(base.map(slide => [slide.dataset.slideId, slide]));
    config.custom_slides.forEach(slide => nodes.set(slide.id, makeCustomSlide(slide)));
    Object.entries(config.overrides).forEach(([id, override]) => {
      const slide = nodes.get(id);
      slide.dataset.t = override.title;
      const label = slide.querySelector(".chap .ttl");
      if (label) label.textContent = override.title;
    });
    const stage = document.getElementById("stage");
    config.order.forEach(id => {
      if (!config.hidden.includes(id)) stage.append(nodes.get(id));
    });
    config.hidden.forEach(id => nodes.get(id).remove());
    stage.dataset.slideRevision = config.revision;
    return config;
  }

  async function loadAndApply(url) {
    try {
      if (typeof location !== "undefined" && location.protocol === "file:") {
        console.warn("Không thể áp dụng cấu hình slide; đang dùng thứ tự mặc định.");
        return null;
      }
      const response = await fetch(url || "slide-config.json", { credentials: "same-origin", cache: "no-store" });
      if (!response.ok) throw new Error("config_request_failed");
      return applyConfig(await response.json());
    } catch (error) {
      console.warn("Không thể áp dụng cấu hình slide; đang dùng thứ tự mặc định.");
      return null;
    }
  }

  return { validateConfig, applyConfig, loadAndApply };
});
