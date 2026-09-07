const ALLOWED_TYPES = new Set([
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/gif",
  "application/pdf",
]);

function startsWith(bytes: Uint8Array, signature: number[]) {
  return signature.every((value, index) => bytes[index] === value);
}

export function validateUpload(type: string, bytes: Uint8Array): string | null {
  if (!ALLOWED_TYPES.has(type)) {
    return "Chọn ảnh JPG, PNG, WebP, GIF hoặc PDF.";
  }

  const valid =
    (type === "image/jpeg" && startsWith(bytes, [0xff, 0xd8, 0xff])) ||
    (type === "image/png" &&
      startsWith(bytes, [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])) ||
    (type === "image/gif" &&
      (startsWith(bytes, [0x47, 0x49, 0x46, 0x38, 0x37, 0x61]) ||
        startsWith(bytes, [0x47, 0x49, 0x46, 0x38, 0x39, 0x61]))) ||
    (type === "image/webp" &&
      startsWith(bytes, [0x52, 0x49, 0x46, 0x46]) &&
      bytes[8] === 0x57 &&
      bytes[9] === 0x45 &&
      bytes[10] === 0x42 &&
      bytes[11] === 0x50) ||
    (type === "application/pdf" &&
      startsWith(bytes, [0x25, 0x50, 0x44, 0x46, 0x2d]));

  return valid ? null : "Định dạng khai báo không khớp nội dung tệp.";
}
