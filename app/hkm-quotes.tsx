'use client';
import './hkm.css';
import {useState,useEffect,useRef} from 'react';
import {Plus,Trash2,ImagePlus,Printer,Loader2,Upload,ExternalLink} from 'lucide-react';
import {HkmData,HkmQuote,HkmLine,emptyHkmData,fmtMoney,lineTotal,numToWordsVn} from './hkm-model';

const today=()=>new Date().toISOString().slice(0,10);
function newQuote():HkmQuote{return {id:crypto.randomUUID(),name:'Khách hàng mới',number:'BG-'+today().replace(/-/g,''),date:today(),customer:{name:'',address:'',phone:'',email:''},items:[],discountPct:0,vatPct:0,notes:''};}
function newLine():HkmLine{return {id:crypto.randomUUID(),name:'',desc:'',unit:'cái',qty:1,price:0};}

export default function HkmQuotes(){
 const [data,setData]=useState<HkmData>(emptyHkmData),[revision,setRevision]=useState(0),[loaded,setLoaded]=useState(false),[saving,setSaving]=useState(false),[error,setError]=useState(''),[uploading,setUploading]=useState(''),[active,setActive]=useState('');
 const lock=useRef(false),timer=useRef<number|null>(null),dataRef=useRef(data);dataRef.current=data;
 const quote=data.quotes.find(q=>q.id===active)||data.quotes[0];

 async function load(){setError('');try{const r=await fetch('/api/hkm');const j=await r.json();if(!r.ok)throw Error(j.error);setData(j.data);setRevision(j.revision||0);setActive(j.data.quotes[0]?.id||'');setLoaded(true);}catch(e){setError((e as Error).message);setLoaded(true)}}
 useEffect(()=>{load()},[]);

 function mutate(next:HkmData){setData(next);if(timer.current)window.clearTimeout(timer.current);setSaving(true);timer.current=window.setTimeout(flushSave,700);}
 async function flushSave(){if(lock.current)return;lock.current=true;setError('');try{const r=await fetch('/api/hkm',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({data:dataRef.current,revision})});const j=await r.json();if(!r.ok){if(r.status===409){await load();return}throw Error(j.error)}setRevision(j.revision);}catch(e){setError((e as Error).message)}finally{lock.current=false;setSaving(false)}}

 const up=(fn:(d:HkmData)=>HkmData)=>mutate(fn(structuredClone(data)));
 function patchQuote(p:Partial<HkmQuote>){up(d=>d.quotes.map(q=>q.id===quote.id?{...q,...p}:q))}
 function patchCustomer(p:Partial<HkmQuote['customer']>){up(d=>d.quotes.map(q=>q.id===quote.id?{...q,customer:{...q.customer,...p}}:q))}
 function patchItem(id:string,p:Partial<HkmLine>){up(d=>d.quotes.map(q=>q.id===quote.id?{...q,items:q.items.map(l=>l.id===id?{...l,...p}:l)}:q))}
 function addQuote(){const q=newQuote();up(d=>d.quotes.concat(q));setActive(q.id)}
 function removeQuote(){if(!quote||data.quotes.length<=1)return;up(d=>{const n=d.quotes.filter(q=>q.id!==quote.id);return {quotes:n}});setActive(data.quotes.find(q=>q.id!==quote.id)?.id||'')}
 function addItem(){patchQuote({items:[...quote.items,newLine()]})}
 function removeItem(id:string){patchQuote({items:quote.items.filter(l=>l.id!==id)})}

 async function uploadItemImage(id:string,files:FileList|null){const f=files?.[0];if(!f)return;setUploading(id);setError('');try{const body=new FormData();body.append('file',f);const r=await fetch('/api/upload',{method:'POST',body});const j=await r.json();if(!r.ok)throw Error(j.error||'Không tải được ảnh.');patchItem(id,{image:j.url});}catch(e){setError((e as Error).message)}finally{setUploading('')}}

 const subtotal=quote?quote.items.reduce((s,l)=>s+lineTotal(l),0):0;
 const discount=subtotal*(quote?.discountPct||0)/100,afterDiscount=subtotal-discount;
 const vat=afterDiscount*(quote?.vatPct||0)/100,total=afterDiscount+vat;

 if(!loaded)return <main className="hkm hkm-loading"><Loader2 className="spin"/><span>Đang mở báo giá…</span></main>;
 return <main className="hkm">
  <header className="hkm-topbar">
   <div className="hkm-brand">HOÀNG KIM MINH <span>FURNITURE</span></div>
   <div className="hkm-tabs">{data.quotes.map(q=><button key={q.id} className={'hkm-tab '+(q.id===(quote?.id)?'active':'')} onClick={()=>setActive(q.id)} title={q.customer.name||q.name}>{q.customer.name||q.name}</button>)}<button className="hkm-tab hkm-tab-add" onClick={addQuote} title="Thêm báo giá mới"><Plus size={16}/></button></div>
   <div className="hkm-actions"><button className="hkm-print-btn" onClick={()=>window.print()}><Printer size={16}/> Xuất PDF</button><span className={'hkm-saved '+(error?'err':'')}>{saving?'Đang lưu…':error||'Đã lưu'}</span></div>
  </header>
  {quote&&<div className="hkm-editor">
   <div className="hkm-quote-head">
    <input className="hkm-customer-name" value={quote.customer.name} placeholder="Tên khách hàng" onChange={e=>patchCustomer({name:e.target.value})}/>
    <label>Số BG<input value={quote.number} onChange={e=>patchQuote({number:e.target.value})}/></label>
    <label>Ngày<input type="date" value={quote.date} onChange={e=>patchQuote({date:e.target.value})}/></label>
   </div>
   <div className="hkm-customer">
    <label>Địa chỉ<input value={quote.customer.address} onChange={e=>patchCustomer({address:e.target.value})}/></label>
    <label>Điện thoại<input value={quote.customer.phone} onChange={e=>patchCustomer({phone:e.target.value})}/></label>
    <label>Email<input value={quote.customer.email} onChange={e=>patchCustomer({email:e.target.value})}/></label>
    <label>Tên thẻ (nội bộ)<input value={quote.name} onChange={e=>patchQuote({name:e.target.value})}/></label>
   </div>
   <div className="hkm-table-wrap"><table className="hkm-table">
    <thead><tr><th className="hkm-col-img">Ảnh</th><th>Tên sản phẩm / dịch vụ</th><th>Mô tả</th><th className="hkm-col-unit">ĐVT</th><th className="hkm-col-num">SL</th><th className="hkm-col-num">Đơn giá (đ)</th><th className="hkm-col-num">Thành tiền</th><th></th></tr></thead>
    <tbody>{quote.items.map(l=><tr key={l.id}>
      <td className="hkm-img-cell">{l.image?<div className="hkm-thumb"><img src={l.image} alt=""/><button className="hkm-img-x" onClick={()=>patchItem(l.id,{image:''})} title="Bỏ ảnh"><Trash2 size={12}/></button></div>:<label className="hkm-img-add">{uploading===l.id?<Loader2 className="spin" size={18}/>:<ImagePlus size={18}/>}<input type="file" accept="image/jpeg,image/png,image/webp,image/gif" hidden onChange={e=>{uploadItemImage(l.id,e.target.files);e.target.value=''}}/></label>}</td>
      <td><input value={l.name} placeholder="Tên sản phẩm" onChange={e=>patchItem(l.id,{name:e.target.value})}/></td>
      <td><textarea rows={2} value={l.desc} placeholder="Quy cách, chất liệu…" onChange={e=>patchItem(l.id,{desc:e.target.value})}/></td>
      <td><input className="hkm-center" value={l.unit} onChange={e=>patchItem(l.id,{unit:e.target.value})}/></td>
      <td><input className="hkm-center" type="number" min={0} value={l.qty} onChange={e=>patchItem(l.id,{qty:Number(e.target.value)})}/></td>
      <td><input className="hkm-right" type="number" min={0} value={l.price} onChange={e=>patchItem(l.id,{price:Number(e.target.value)})}/></td>
      <td className="hkm-right hkm-line-total">{fmtMoney(lineTotal(l))}</td>
      <td><button className="hkm-del" onClick={()=>removeItem(l.id)} title="Xóa dòng"><Trash2 size={15}/></button></td>
     </tr>)}</tbody>
   </table></div>
   <button className="hkm-add-row" onClick={addItem}><Plus size={15}/> Thêm dòng sản phẩm</button>
   <div className="hkm-totals">
    <div className="hkm-total-labels">
     <label>Tên khách (hiển thị trên báo giá)<input value={quote.customer.name} onChange={e=>patchCustomer({name:e.target.value})}/></label>
     <label>Ghi chú / điều khoản<textarea rows={3} value={quote.notes} onChange={e=>patchQuote({notes:e.target.value})} placeholder="Bảo hành, thời gian giao hàng, hiệu lực báo giá…"/></label>
    </div>
    <div className="hkm-total-box">
     <div className="hkm-total-row"><span>Tiền hàng</span><b>{fmtMoney(subtotal)}</b></div>
     <div className="hkm-total-row"><label>Chiết khấu %<input type="number" min={0} max={100} value={quote.discountPct} onChange={e=>patchQuote({discountPct:Number(e.target.value)})}/></label><b>-{fmtMoney(discount)}</b></div>
     <div className="hkm-total-row"><label>VAT %<input type="number" min={0} max={100} value={quote.vatPct} onChange={e=>patchQuote({vatPct:Number(e.target.value)})}/></label><b>{fmtMoney(vat)}</b></div>
     <div className="hkm-total-row hkm-grand"><span>TỔNG CỘNG</span><b>{fmtMoney(total)} đ</b></div>
     <p className="hkm-words">{numToWordsVn(total)}</p>
    </div>
   </div>
   <div className="hkm-footer-row"><button className="hkm-del-quote" onClick={removeQuote} disabled={data.quotes.length<=1}><Trash2 size={15}/> Xóa thẻ báo giá này</button><a className="hkm-site" href="https://www.hoangkimminh.vn" target="_blank" rel="noreferrer">www.hoangkimminh.vn <ExternalLink size={13}/></a></div>
  </div>}
  {quote&&<div className="hkm-print">
   <div className="hkm-print-head"><div className="hkm-print-logo">HOÀNG KIM MINH<br/><span>FURNITURE</span></div><div className="hkm-print-title"><h1>BÁO GIÁ</h1><p>Số: {quote.number} · Ngày: {quote.date}</p></div><div className="hkm-print-contact">www.hoangkimminh.vn<br/>0982 506 079</div></div>
   <div className="hkm-print-customer"><span><b>Khách hàng:</b> {quote.customer.name}</span><span><b>Địa chỉ:</b> {quote.customer.address}</span><span><b>ĐT:</b> {quote.customer.phone}</span>{quote.customer.email&&<span><b>Email:</b> {quote.customer.email}</span>}</div>
   <table className="hkm-print-table"><thead><tr><th>STT</th><th>Hình ảnh</th><th>Tên sản phẩm / dịch vụ</th><th>Mô tả</th><th>ĐVT</th><th>SL</th><th>Đơn giá</th><th>Thành tiền</th></tr></thead><tbody>{quote.items.map((l,i)=><tr key={l.id}><td>{i+1}</td><td>{l.image?<img src={l.image} alt=""/>:''}</td><td>{l.name}</td><td>{l.desc}</td><td>{l.unit}</td><td>{l.qty}</td><td>{fmtMoney(l.price)}</td><td>{fmtMoney(lineTotal(l))}</td></tr>)}</tbody></table>
   <div className="hkm-print-totals"><div>Tiền hàng: {fmtMoney(subtotal)} · Chiết khấu {quote.discountPct}%: -{fmtMoney(discount)} · VAT {quote.vatPct}%: {fmtMoney(vat)}</div><div className="hkm-print-grand">TỔNG CỘNG: {fmtMoney(total)} đ</div><div>Bằng chữ: {numToWordsVn(total)}</div></div>
   {quote.notes&&<div className="hkm-print-notes"><b>Ghi chú:</b> {quote.notes}</div>}
   <div className="hkm-print-foot">HOÀNG KIM MINH FURNITURE · www.hoangkimminh.vn · Hotline 0982 506 079</div>
  </div>}
 </main>;
}
