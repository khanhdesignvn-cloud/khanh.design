"use strict";

const DRAFT_KEY = "khanh-design-ai-course-draft-v1";
const APPLICATION_API_URL = "https://undefined-seeks-mall-disclose.trycloudflare.com/course/apply";
const DRAFT_FIELDS = [
  "full_name",
  "phone",
  "industry",
  "expectation",
  "data_consent",
];

function canPersistDraft(hasConsent) {
  return hasConsent === true;
}

function getCountdownParts(deadline, now = new Date()) {
  const remaining = new Date(deadline).getTime() - new Date(now).getTime();
  if (!Number.isFinite(remaining) || remaining <= 0) {
    return { days: 0, hours: 0, minutes: 0, seconds: 0, expired: true };
  }
  const totalSeconds = Math.floor(remaining / 1000);
  return {
    days: Math.floor(totalSeconds / 86400),
    hours: Math.floor((totalSeconds % 86400) / 3600),
    minutes: Math.floor((totalSeconds % 3600) / 60),
    seconds: totalSeconds % 60,
    expired: false,
  };
}

function initialiseCountdown() {
  const countdown = document.querySelector(".registration-countdown");
  if (!countdown) return;
  const deadline = countdown.dataset.deadline;
  const fields = {
    days: document.getElementById("countdown-days"),
    hours: document.getElementById("countdown-hours"),
    minutes: document.getElementById("countdown-minutes"),
    seconds: document.getElementById("countdown-seconds"),
  };
  const status = document.getElementById("countdown-status");
  const cta = countdown.querySelector(".countdown-cta");
  let timer;
  const render = () => {
    const parts = getCountdownParts(deadline);
    Object.entries(fields).forEach(([key, element]) => {
      if (element) element.textContent = String(parts[key]).padStart(2, "0");
    });
    if (parts.expired) {
      if (status) status.textContent = "Đăng ký cohort này đã kết thúc.";
      if (cta) {
        cta.textContent = "Đã đóng đăng ký";
        cta.removeAttribute("href");
        cta.setAttribute("aria-disabled", "true");
      }
      if (timer) window.clearInterval(timer);
    }
    return parts.expired;
  };
  if (!render()) timer = window.setInterval(render, 1000);
}

function encodeLine(label, value) {
  return `${label}: ${String(value || "").trim()}`;
}

function buildMailto(data) {
  const subject = "Đăng ký quan tâm — AI Vận Hành Doanh Nghiệp";
  const body = [
    "Chào Khánh,",
    "",
    "Tôi muốn đăng ký quan tâm cohort sáng lập AI Vận Hành Doanh Nghiệp.",
    "",
    encodeLine("Họ và tên", data.full_name),
    encodeLine("Số điện thoại", data.phone),
    encodeLine("Ngành nghề", data.industry),
    encodeLine("Mong muốn khi tham gia khóa học", data.expectation),
    "",
    "Tôi đã đọc thông báo sử dụng dữ liệu và chủ động xác nhận gửi email này.",
  ].join("\r\n");

  return `mailto:hi@nguyenquockhanh.vn?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

async function submitApplication(data, fetchImpl = fetch) {
  const response = await fetchImpl(APPLICATION_API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  let result = {};
  try {
    result = await response.json();
  } catch (_) {
    result = {};
  }
  if (response.status === 201) {
    return { ok: true, application_id: result.id };
  }
  return { ok: false, error: result.error || "submission_failed" };
}

function formValues(form) {
  const values = {};
  DRAFT_FIELDS.forEach((name) => {
    const field = form.elements.namedItem(name);
    values[name] = field.type === "checkbox" ? field.checked : field.value;
  });
  return values;
}

function writeStatus(status, message) {
  status.textContent = message;
}

function saveDraft(form, status) {
  const values = formValues(form);
  if (!canPersistDraft(values.data_consent)) {
    try {
      localStorage.removeItem(DRAFT_KEY);
    } catch (_) {
      // Storage can be unavailable; the form still works without a draft.
    }
    return;
  }

  try {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(values));
    writeStatus(status, "Đã lưu nháp riêng trên thiết bị này.");
  } catch (_) {
    writeStatus(status, "Không thể lưu nháp trên thiết bị. Bạn vẫn có thể tiếp tục đăng ký.");
  }
}

function restoreDraft(form, status) {
  let stored;
  try {
    stored = localStorage.getItem(DRAFT_KEY);
  } catch (_) {
    return;
  }
  if (!stored) return;

  try {
    const values = JSON.parse(stored);
    if (!canPersistDraft(values.data_consent)) return;
    DRAFT_FIELDS.forEach((name) => {
      const field = form.elements.namedItem(name);
      if (!field || !(name in values)) return;
      if (field.type === "checkbox") field.checked = Boolean(values[name]);
      else field.value = String(values[name]);
    });
    writeStatus(status, "Đã khôi phục nháp từ thiết bị này.");
  } catch (_) {
    try {
      localStorage.removeItem(DRAFT_KEY);
    } catch (_) {
      // Ignore unavailable storage and leave the blank form usable.
    }
  }
}

function initialiseForm() {
  const form = document.getElementById("course-application");
  const status = document.getElementById("form-status");
  const clearButton = document.getElementById("clear-draft");
  if (!form || !status || !clearButton) return;

  restoreDraft(form, status);

  form.addEventListener("input", () => saveDraft(form, status));
  form.addEventListener("change", () => saveDraft(form, status));

  clearButton.addEventListener("click", () => {
    try {
      localStorage.removeItem(DRAFT_KEY);
    } catch (_) {
      // A clear action is already satisfied when storage is unavailable.
    }
    form.reset();
    writeStatus(status, "Đã xóa nháp trên thiết bị.");
    form.elements.namedItem("full_name").focus();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.checkValidity()) {
      writeStatus(status, "Hãy hoàn thành các trường bắt buộc trước khi tiếp tục.");
      form.reportValidity();
      return;
    }

    const values = formValues(form);
    if (!canPersistDraft(values.data_consent)) {
      writeStatus(status, "Bạn cần đồng ý cách xử lý dữ liệu trước khi tiếp tục.");
      return;
    }

    saveDraft(form, status);
    writeStatus(status, "Đang gửi đăng ký an toàn…");
    try {
      const result = await submitApplication(values);
      if (result.ok) {
        try {
          localStorage.removeItem(DRAFT_KEY);
        } catch (_) {
          // The application is already received even when local storage is unavailable.
        }
        form.reset();
        writeStatus(status, `Đã nhận đăng ký. Mã hồ sơ: ${result.application_id}`);
        return;
      }
      if (result.error === "duplicate_application") {
        writeStatus(status, "Thông tin này đã được đăng ký. Khánh sẽ liên hệ theo hồ sơ đã nhận.");
        return;
      }
      if (result.error === "rate_limited") {
        writeStatus(status, "Bạn đã gửi quá nhanh. Vui lòng thử lại sau ít phút.");
        return;
      }
      throw new Error("submission_failed");
    } catch (_) {
      writeStatus(status, "Máy chủ tạm thời chưa nhận được. Email dự phòng đã được chuẩn bị để bạn kiểm tra và tự xác nhận gửi.");
      window.location.href = buildMailto(values);
    }
  });
}

if (typeof document !== "undefined") {
  initialiseCountdown();
  initialiseForm();
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { buildMailto, canPersistDraft, getCountdownParts, submitApplication };
}
