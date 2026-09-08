'use client';
import './hkm.css';
import {useState, useEffect, useRef} from 'react';
import {Plus, Trash2, ImagePlus, Printer, Loader2, X, FolderPlus} from 'lucide-react';
import {
  HkmData, HkmQuote, HkmLine, HkmSection, emptyHkmData, fmtMoney, fmtDate,
  parseQty, lineTotal, numToWordsVn, newQuote, newSection, newLine, HKM, todayIso,
} from './hkm-model';

const standardTerms = (q: HkmQuote) => [
  'Toàn bộ sản phẩm dùng ván MDF, Plywood được dán chỉ 4 cạnh, đảm bảo chống ẩm cho sản phẩm.',
  'Tạm ứng công trình đợt 1 là 50% theo báo giá; đợt 2 quyết toán theo khối lượng thực tế.',
  'Tiến độ thi công theo thỏa thuận, kể từ ngày nhận mặt bằng và nhận tạm ứng đợt 1.',
  q.vatPct > 0 ? `Đơn giá trên đã bao gồm thuế VAT ${q.vatPct}%.` : 'Đơn giá trên chưa bao gồm thuế VAT.',
  'Đơn giá trên đã bao gồm chi phí lắp đặt nội thất hoàn thiện tại công trình.',
  'Cam kết sử dụng đúng vật liệu và chất lượng như đã báo.',
];

export default function HkmQuotes() {
  const [data, setData] = useState<HkmData>(emptyHkmData);
  const [revision, setRevision] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState('');
  const [active, setActive] = useState('');
  const lock = useRef(false), timer = useRef<number | null>(null), dataRef = useRef(data);
  dataRef.current = data;
  const quote = data.quotes.find(q => q.id === active) || data.quotes[0];

  async function load() {
    setError('');
    try {
      const r = await fetch('/api/hkm');
      const j = await r.json();
      if (!r.ok) throw Error(j.error);
      const d: HkmData = (j.data && j.data.quotes && j.data.quotes.length) ? j.data : {quotes: [newQuote()]};
      setData(d); setRevision(j.revision || 0); setActive(d.quotes[0].id); setLoaded(true);
    } catch (e) { setError((e as Error).message); setLoaded(true); }
  }
  useEffect(() => { load(); }, []);

  function mutate(next: HkmData) {
    setData(next);
    if (timer.current) window.clearTimeout(timer.current);
    setSaving(true);
    timer.current = window.setTimeout(flushSave, 700);
  }
  async function flushSave() {
    if (lock.current) return; lock.current = true; setError('');
    try {
      const r = await fetch('/api/hkm', {method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({data: dataRef.current, revision})});
      const j = await r.json();
      if (!r.ok) { if (r.status === 409) { await load(); return; } throw Error(j.error); }
      setRevision(j.revision);
    } catch (e) { setError((e as Error).message); }
    finally { lock.current = false; setSaving(false); }
  }

  const up = (fn: (d: HkmData) => HkmQuote[]) => mutate({quotes: fn(structuredClone(data))});
  function patchQuote(p: Partial<HkmQuote>) { up(d => d.quotes.map(q => q.id === quote.id ? {...q, ...p} : q)); }
  function patchCustomer(p: Partial<HkmQuote['customer']>) { up(d => d.quotes.map(q => q.id === quote.id ? {...q, customer: {...q.customer, ...p}} : q)); }
  function patchSection(sid: string, p: Partial<HkmSection>) { up(d => d.quotes.map(q => q.id === quote.id ? {...q, sections: q.sections.map(s => s.id === sid ? {...s, ...p} : s)} : q)); }
  function patchItem(sid: string, iid: string, p: Partial<HkmLine>) { up(d => d.quotes.map(q => q.id === quote.id ? {...q, sections: q.sections.map(s => s.id === sid ? {...s, items: s.items.map(l => l.id === iid ? {...l, ...p} : l)} : s)} : q)); }

  function addQuote() { const q = newQuote(); up(d => d.quotes.concat(q)); setActive(q.id); }
  function removeQuote() { if (!quote || data.quotes.length <= 1) return; up(d => d.quotes.filter(q => q.id !== quote.id)); setActive(data.quotes.find(q => q.id !== quote.id)?.id || ''); }
  function addSection() { patchQuote({sections: [...quote.sections, newSection()]}); }
  function removeSection(sid: string) { if (quote.sections.length <= 1) return; patchQuote({sections: quote.sections.filter(s => s.id !== sid)}); }
  function addItem(sid: string) { patchQuote({sections: quote.sections.map(s => s.id === sid ? {...s, items: [...s.items, newLine()]} : s)}); }
  function removeItem(sid: string, iid: string) { patchQuote({sections: quote.sections.map(s => s.id === sid ? {...s, items: s.items.filter(l => l.id !== iid)} : s)}); }

  async function uploadItemImage(sid: string, iid: string, files: FileList | null) {
    const f = files?.[0]; if (!f) return; setUploading(iid); setError('');
    try {
      const body = new FormData(); body.append('file', f);
      const r = await fetch('/api/upload', {method: 'POST', body});
      const j = await r.json();
      if (!r.ok) throw Error(j.error || 'Không tải được ảnh.');
      patchItem(sid, iid, {image: j.url});
    } catch (e) { setError((e as Error).message); } finally { setUploading(''); }
  }

  const allItems = quote ? quote.sections.flatMap(s => s.items) : [];
  const subtotal = allItems.reduce((s, l) => s + lineTotal(l), 0);
  const discount = subtotal * (quote?.discountPct || 0) / 100, afterDiscount = subtotal - discount;
  const vat = afterDiscount * (quote?.vatPct || 0) / 100, total = afterDiscount + vat;

  if (!loaded) return <main className="hkm hkm-loading"><Loader2 className="spin" /> <span>Đang mở báo giá…</span></main>;

  return <main className="hkm">
    <header className="hkm-topbar">
      <div className="hkm-brand">HOÀNG KIM MINH <span>FURNITURE</span></div>
      <div className="hkm-tabs">
        {data.quotes.map(q => (
          <button key={q.id} className={'hkm-tab ' + (q.id === quote?.id ? 'active' : '')} onClick={() => setActive(q.id)} title={q.customer.name || q.name}>
            {q.customer.name || q.name}
          </button>
        ))}
        <button className="hkm-tab hkm-tab-add" onClick={addQuote} title="Thêm khách hàng mới"><Plus size={16} /></button>
      </div>
      <div className="hkm-actions">
        <button className="hkm-print-btn" onClick={() => window.print()}><Printer size={16} /> Xuất PDF</button>
        <span className={'hkm-saved ' + (error ? 'err' : '')}>{saving ? 'Đang lưu…' : error || 'Đã lưu'}</span>
      </div>
    </header>

    {quote && <div className="hkm-editor">
      <div className="hkm-card">
        <div className="hkm-quote-head">
          <label className="grow">Tiêu đề công trình<input value={quote.title} placeholder="VD: Thi công nội thất bếp trọn gói" onChange={e => patchQuote({title: e.target.value})} /></label>
          <label>Số BG<input value={quote.number} onChange={e => patchQuote({number: e.target.value})} /></label>
          <label>Ngày<input type="date" value={quote.date} onChange={e => patchQuote({date: e.target.value})} /></label>
        </div>
        <div className="hkm-customer">
          <label>Tên khách hàng<input value={quote.customer.name} placeholder="VD: Chị Hằng" onChange={e => patchCustomer({name: e.target.value})} /></label>
          <label>Địa chỉ công trình<input value={quote.customer.address} placeholder="VD: Nghĩa Hà" onChange={e => patchCustomer({address: e.target.value})} /></label>
          <label>Điện thoại<input value={quote.customer.phone} onChange={e => patchCustomer({phone: e.target.value})} /></label>
          <label>Email<input value={quote.customer.email} onChange={e => patchCustomer({email: e.target.value})} /></label>
          <label>Hạng mục<input value={quote.hangMuc} placeholder="VD: Khu vực bếp" onChange={e => patchQuote({hangMuc: e.target.value})} /></label>
          <label>Người ký<input value={quote.seller} onChange={e => patchQuote({seller: e.target.value})} /></label>
          <label>Chức danh<input value={quote.sellerRole} onChange={e => patchQuote({sellerRole: e.target.value})} /></label>
        </div>
      </div>

      {quote.sections.map((sec, si) => (
        <div className="hkm-card" key={sec.id}>
          <div className="hkm-section-head">
            <label className="hkm-section-name">Nhóm / hạng mục<input value={sec.name} placeholder="VD: Bếp" onChange={e => patchSection(sec.id, {name: e.target.value})} /></label>
            <span className="hkm-section-count">{sec.items.length} dòng</span>
            <button className="hkm-del-quote" onClick={() => removeSection(sec.id)} disabled={quote.sections.length <= 1} title="Xóa nhóm"><Trash2 size={15} /></button>
          </div>
          <div className="hkm-table-wrap">
            <table className="hkm-table">
              <thead><tr>
                <th className="hkm-col-img">Ảnh</th>
                <th>Tên sản phẩm</th>
                <th>Thông số kỹ thuật</th>
                <th>Kích thước</th>
                <th>Bảo hành</th>
                <th className="hkm-col-unit">ĐVT</th>
                <th className="hkm-col-qty">SL</th>
                <th className="hkm-col-num">Đơn giá (đ)</th>
                <th className="hkm-col-num">Thành tiền</th>
                <th></th>
              </tr></thead>
              <tbody>
                {sec.items.map(l => (
                  <tr key={l.id}>
                    <td className="hkm-img-cell">
                      {l.image
                        ? <div className="hkm-thumb"><img src={l.image} alt="" /><button className="hkm-img-x" onClick={() => patchItem(sec.id, l.id, {image: ''})} title="Bỏ ảnh"><X size={12} /></button></div>
                        : <label className="hkm-img-add">{uploading === l.id ? <Loader2 className="spin" size={18} /> : <ImagePlus size={18} />}<input type="file" accept="image/jpeg,image/png,image/webp,image/gif" hidden onChange={e => { uploadItemImage(sec.id, l.id, e.target.files); e.target.value = ''; }} /></label>}
                    </td>
                    <td><input value={l.name} placeholder="Tên sản phẩm" onChange={e => patchItem(sec.id, l.id, {name: e.target.value})} /></td>
                    <td><textarea rows={2} value={l.desc} placeholder="Vật liệu, quy cách…" onChange={e => patchItem(sec.id, l.id, {desc: e.target.value})} /></td>
                    <td><input value={l.dimensions} placeholder="D x × R y × C z mm" onChange={e => patchItem(sec.id, l.id, {dimensions: e.target.value})} /></td>
                    <td><input value={l.warranty} placeholder="2 năm" onChange={e => patchItem(sec.id, l.id, {warranty: e.target.value})} /></td>
                    <td><input className="hkm-center" value={l.unit} onChange={e => patchItem(sec.id, l.id, {unit: e.target.value})} /></td>
                    <td><input className="hkm-center" value={l.qty} onChange={e => patchItem(sec.id, l.id, {qty: e.target.value})} /></td>
                    <td><input className="hkm-right" type="number" min={0} value={l.price} onChange={e => patchItem(sec.id, l.id, {price: Number(e.target.value)})} /></td>
                    <td className="hkm-right hkm-line-total">{fmtMoney(lineTotal(l))}</td>
                    <td><button className="hkm-del" onClick={() => removeItem(sec.id, l.id)} title="Xóa dòng"><Trash2 size={15} /></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button className="hkm-add-row" onClick={() => addItem(sec.id)}><Plus size={15} /> Thêm dòng</button>
        </div>
      ))}

      <button className="hkm-add-section" onClick={addSection}><FolderPlus size={16} /> Thêm nhóm / hạng mục</button>

      <div className="hkm-totals">
        <div className="hkm-total-labels">
          <label>Điều khoản bổ sung / ghi chú<textarea rows={6} value={quote.notes} onChange={e => patchQuote({notes: e.target.value})} placeholder="Ghi chú thêm ngoài điều khoản mặc định…" /></label>
        </div>
        <div className="hkm-total-box">
          <div className="hkm-total-row"><span>Tiền hàng</span><b>{fmtMoney(subtotal)}</b></div>
          <div className="hkm-total-row"><label>Chiết khấu %<input type="number" min={0} max={100} value={quote.discountPct} onChange={e => patchQuote({discountPct: Number(e.target.value)})} /></label><b>-{fmtMoney(discount)}</b></div>
          <div className="hkm-total-row"><label>VAT %<input type="number" min={0} max={100} value={quote.vatPct} onChange={e => patchQuote({vatPct: Number(e.target.value)})} /></label><b>{fmtMoney(vat)}</b></div>
          <div className="hkm-total-row hkm-grand"><span>TỔNG CỘNG</span><b>{fmtMoney(total)} đ</b></div>
          <p className="hkm-words">{numToWordsVn(total)}</p>
        </div>
      </div>

      <div className="hkm-footer-row">
        <button className="hkm-del-quote" onClick={removeQuote} disabled={data.quotes.length <= 1}><Trash2 size={15} /> Xóa thẻ khách này</button>
        <a className="hkm-site" href="https://www.hoangkimminh.vn" target="_blank" rel="noreferrer">{HKM.website}</a>
      </div>
    </div>}

    {quote && <div className="hkm-print">
      <div className="hkm-print-header">
        <div className="hkm-print-logo">
          <span className="hkm-print-mark" />
          <div className="hkm-print-brand">HOÀNG KIM MINH<br /><b>FURNITURE</b></div>
        </div>
        <div className="hkm-print-header-info">
          <div>{HKM.showroom}</div>
          <div>{HKM.contact}</div>
        </div>
      </div>

      <div className="hkm-print-title">
        <h1>Bảng báo giá</h1>
        <p>{quote.title}{quote.title && quote.date ? ' · ' : ''}Ngày {fmtDate(quote.date)}</p>
      </div>

      <div className="hkm-print-meta">
        <div className="hkm-print-meta-col"><span>Khách hàng</span><b>{quote.customer.name || '—'}</b></div>
        <div className="hkm-print-meta-col"><span>Địa chỉ công trình</span><b>{quote.customer.address || '—'}</b></div>
        <div className="hkm-print-meta-col"><span>Hạng mục</span><b>{quote.hangMuc || '—'}</b></div>
      </div>

      {quote.sections.map(sec => (
        <div className="hkm-print-section" key={sec.id}>
          <div className="hkm-print-sec-head">
            <span className="hkm-print-sec-name">{sec.name || 'Hạng mục'}</span>
            <span className="hkm-print-sec-count">{sec.items.length} hạng mục</span>
          </div>
          {sec.items.map((l, i) => (
            <div className="hkm-print-item" key={l.id}>
              <div className="hkm-print-item-top">
                <div className="hkm-print-item-num">{String(i + 1).padStart(2, '0')}</div>
                <div className="hkm-print-item-title">{l.name}</div>
                <div className="hkm-print-item-qty">{l.qty} {l.unit}</div>
              </div>
              <div className="hkm-print-item-body">
                <div className="hkm-print-item-specs">
                  {l.desc.split('\n').map((ln, k) => <div key={k}>{ln}</div>)}
                </div>
                <div className="hkm-print-item-prices">
                  <div className="hkm-print-item-total">{fmtMoney(lineTotal(l))}</div>
                  <div className="hkm-print-item-unit">{fmtMoney(l.price)} / {l.unit}</div>
                </div>
              </div>
              {(l.dimensions || l.warranty) && <div className="hkm-print-item-tags">
                {l.dimensions && <span className="hkm-print-pill">{l.dimensions}</span>}
                {l.warranty && <span className="hkm-print-pill hkm-print-warranty">{l.warranty ? 'Bảo hành ' + l.warranty : ''}</span>}
              </div>}
            </div>
          ))}
        </div>
      ))}

      <div className="hkm-print-total">
        <div className="hkm-print-total-note">Đơn giá {quote.vatPct > 0 ? `đã bao gồm thuế VAT ${quote.vatPct}%` : 'chưa bao gồm thuế VAT'}, đã bao gồm chi phí lắp đặt hoàn thiện tại công trình.</div>
        {quote.discountPct > 0 && <div className="hkm-print-total-line"><span>Chiết khấu {quote.discountPct}%</span><b>-{fmtMoney(discount)}</b></div>}
        <div className="hkm-print-total-row">
          <span className="hkm-print-total-label">TỔNG CỘNG</span>
          <span className="hkm-print-total-value">{fmtMoney(total)} <small>VNĐ</small></span>
        </div>
        <div className="hkm-print-total-words">Bằng chữ: {numToWordsVn(total)}</div>
      </div>

      <div className="hkm-print-terms">
        <div className="hkm-print-terms-title">Điều khoản &amp; cam kết</div>
        <ul>
          {standardTerms(quote).map((t, k) => <li key={k}>{t}</li>)}
          {quote.notes.split('\n').filter(Boolean).map((n, k) => <li key={'n' + k}>{n}</li>)}
        </ul>
      </div>

      <div className="hkm-print-sign">
        <div className="hkm-print-sign-role">{quote.sellerRole}</div>
        <div className="hkm-print-sign-name">{quote.seller}</div>
      </div>

      <div className="hkm-print-footer">
        <div className="hkm-print-footer-left">{HKM.company}</div>
        <div className="hkm-print-footer-right">{HKM.footer}</div>
      </div>
    </div>}
  </main>;
}
