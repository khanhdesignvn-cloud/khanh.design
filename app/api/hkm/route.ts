import {authorizeWrite, adminSession} from '../../admin';
import {env} from 'cloudflare:workers';
import {emptyHkmData} from '../../hkm-model';
function db(){if(!env.DB)throw new Error('Database unavailable');return env.DB;}
const IMG=/^\/api\/image\/[a-f0-9-]+$/;
const num=(v:unknown,min:number,max:number)=>{const n=Number(v);return Number.isFinite(n)&&n>=min&&n<=max};
const str=(v:unknown,max:number)=>typeof v==='string'&&v.length<=max;

function valid(data:any){
  if(!data||!Array.isArray(data.quotes)||data.quotes.length>100)throw Error('Invalid data');
  for(const q of data.quotes){
    if(!str(q.id,64)||!str(q.name,200)||!str(q.number,60)||!str(q.date,40))throw Error('Invalid quote');
    if(!str(q.title,200)||!str(q.hangMuc,120)||!str(q.seller,120)||!str(q.sellerRole,60)||!str(q.notes,4000))throw Error('Invalid quote meta');
    const c=q.customer||{};
    if(!str(c.name,200)||!str(c.address,300)||!str(c.phone,60)||!str(c.email,120))throw Error('Invalid customer');
    if(!num(q.discountPct,0,100)||!num(q.vatPct,0,100))throw Error('Invalid quote meta');
    if(!Array.isArray(q.sections)||q.sections.length>50)throw Error('Invalid sections');
    for(const sec of q.sections){
      if(!str(sec.id,64)||!str(sec.name,120))throw Error('Invalid section');
      if(!Array.isArray(sec.items)||sec.items.length>200)throw Error('Invalid items');
      for(const it of sec.items){
        if(!str(it.id,64)||!str(it.name,300)||!str(it.desc,2000)||!str(it.unit,20))throw Error('Invalid item');
        if(!str(it.dimensions,120)||!str(it.warranty,80)||!str(it.qty,40))throw Error('Invalid item dims');
        if(it.image!==undefined&&it.image!==''&&!IMG.test(it.image))throw Error('Invalid image');
        if(!num(it.price,0,1e12))throw Error('Invalid price');
      }
    }
  }
}

export async function GET(){try{const {isAdmin}=await adminSession();if(!isAdmin)return Response.json({data:emptyHkmData,revision:0});const row=await db().prepare('SELECT payload,revision FROM workspace WHERE id=?').bind('hkm').first<{payload:string;revision:number}>();return Response.json({data:row?JSON.parse(row.payload):emptyHkmData,revision:row?.revision||0});}catch(e){console.error(e);return Response.json({error:'Không tải được báo giá.'},{status:503});}}
export async function PUT(req:Request){try{const denied=await authorizeWrite(req);if(denied)return denied;await db().prepare('INSERT OR IGNORE INTO workspace (id,payload,revision) VALUES (?,?,0)').bind('hkm','{"quotes":[]}').run();const {data,revision}=await req.json();valid(data);const payload=JSON.stringify(data);if(payload.length>2000000)return Response.json({error:'Báo giá quá lớn.'},{status:413});const r=await db().prepare('UPDATE workspace SET payload=?,revision=revision+1 WHERE id=? AND revision=?').bind(payload,'hkm',revision).run();if(!r.meta.changes)return Response.json({error:'Dữ liệu đã thay đổi ở nơi khác. Hãy tải lại trang.'},{status:409});return Response.json({revision:revision+1});}catch(e){console.error(e);return Response.json({error:'Không lưu được báo giá.'},{status:400});}}
