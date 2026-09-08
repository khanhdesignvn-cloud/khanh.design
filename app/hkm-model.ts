export type HkmLine = {
  id: string;
  name: string;        // "Bếp trên"
  desc: string;        // thông số kỹ thuật (nhiều dòng, phân cách bằng \n)
  dimensions: string;  // "D 4.865 × R 350 × C 700 mm"
  warranty: string;    // "Bảo hành 2 năm" (có thể để trống)
  unit: string;        // "md", "m²", "cái", "bộ"
  qty: string;         // "4,865" (dấu phẩy thập phân)
  price: number;       // đơn giá (VNĐ)
  image?: string;      // ảnh dòng (tùy chọn)
};

export type HkmSection = {
  id: string;
  name: string;        // "Bếp", "Phòng khách", ...
  items: HkmLine[];
};

export type HkmQuote = {
  id: string;
  name: string;        // tên thẻ (nội bộ)
  number: string;      // "BG-20260907"
  date: string;        // ISO "2026-09-07"
  title: string;       // "Thi công nội thất bếp trọn gói"
  hangMuc: string;     // "Khu vực bếp"
  customer: { name: string; address: string; phone: string; email: string };
  seller: string;      // "Phan Mạnh Đạt"
  sellerRole: string;  // "GIÁM ĐỐC"
  sections: HkmSection[];
  discountPct: number;
  vatPct: number;
  notes: string;       // điều khoản bổ sung (nhiều dòng)
};

export type HkmData = { quotes: HkmQuote[] };
export const emptyHkmData: HkmData = { quotes: [] };

export const HKM = {
  brand: 'HOÀNG KIM MINH',
  brandSub: 'FURNITURE',
  showroom: 'Showroom Nội thất – Phụ kiện bếp · 100 Quang Trung, TP. Quảng Ngãi',
  contact: 'Liên hệ · 0982 50 60 79 – Mr. Đạt',
  website: 'www.hoangkimminh.vn',
  hotline: '0982 506 079',
  company: 'Công ty TNHH Nội thất Hoàng Kim Minh',
  footer: '100 Quang Trung, TP. Quảng Ngãi · 0982 50 60 79',
};

export const fmtMoney = (n: number) => Number(n || 0).toLocaleString('vi-VN');
export const fmtDate = (iso: string) => {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || '');
  return m ? `${m[3]}.${m[2]}.${m[1]}` : iso || '';
};
export const parseQty = (s: string) => parseFloat(String(s || '0').replace(',', '.')) || 0;
export const lineTotal = (l: HkmLine) => parseQty(l.qty) * (Number(l.price) || 0);
export const todayIso = () => new Date().toISOString().slice(0, 10);

const SO = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín'];
const DONVI = ['', 'nghìn', 'triệu', 'tỷ', 'nghìn tỷ'];
function read3(n: number) {
  const a = Math.floor(n / 100), b = Math.floor(n / 10) % 10, c = n % 10;
  let s = '';
  if (a) s += SO[a] + ' trăm ';
  if (b === 0 && a && c) s += 'lẻ ';
  if (b === 1) s += 'mười ';
  else if (b) s += SO[b] + ' mươi ';
  if (c === 1 && b > 1) s += 'mốt';
  else if (c === 5 && b > 0) s += 'lăm';
  else if (c) s += SO[c];
  return s.trim();
}
export function numToWordsVn(n: number) {
  n = Math.round(Math.abs(n));
  if (n === 0) return 'không đồng';
  let s = '';
  let i = 0;
  while (n > 0) {
    const g = n % 1000;
    if (g) s = (read3(g) + (DONVI[i] ? ' ' + DONVI[i] : '')) + (s ? ' ' + s : '');
    n = Math.floor(n / 1000);
    i++;
  }
  return s.trim() + ' đồng';
}

export function newQuote(): HkmQuote {
  return {
    id: crypto.randomUUID(),
    name: 'Khách hàng mới',
    number: 'BG-' + todayIso().replace(/-/g, ''),
    date: todayIso(),
    title: '',
    hangMuc: '',
    customer: { name: '', address: '', phone: '', email: '' },
    seller: 'Phan Mạnh Đạt',
    sellerRole: 'GIÁM ĐỐC',
    sections: [newSection()],
    discountPct: 0,
    vatPct: 0,
    notes: '',
  };
}

export function newSection(): HkmSection {
  return { id: crypto.randomUUID(), name: '', items: [newLine()] };
}

export function newLine(): HkmLine {
  return { id: crypto.randomUUID(), name: '', desc: '', dimensions: '', warranty: '', unit: 'md', qty: '1', price: 0 };
}
