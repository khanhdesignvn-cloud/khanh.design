import {env} from 'cloudflare:workers';
import {normalizeData,publicProject} from '../../../model';
function db(){if(!env.DB)throw new Error('Database unavailable');return env.DB;}
const TOKEN_RE=/^[A-Za-z0-9_-]{8,64}$/;
const headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'};
export async function GET(_req:Request,{params}:{params:Promise<{token:string}>}){
 try {
  const {token}=await params;
  if(!TOKEN_RE.test(token))return Response.json({error:'Liên kết không hợp lệ.'},{status:404,headers});
  const row=await db().prepare('SELECT payload,revision FROM workspace WHERE id=?').bind('main').first<{payload:string;revision:number}>();
  const missing=()=>Response.json({error:'Liên kết không tồn tại hoặc đã ngừng chia sẻ.'},{status:404,headers});
  if(!row)return missing();
  const data=normalizeData(JSON.parse(row.payload));
  const project=data.projects.find(p=>p.shareToken===token);
  if(!project)return missing();
  return Response.json({data:publicProject(project),revision:row.revision||0},{headers});
 }catch(e){
  console.error(e);
  return Response.json({error:'Không tải được dự án. Vui lòng thử lại.'},{status:503,headers});
 }
}
