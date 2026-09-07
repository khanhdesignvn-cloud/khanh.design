import {env} from 'cloudflare:workers';
import {createSession,sessionCookie,verifyPassword} from '../../../password-auth';
import {BodyTooLargeError,readBodyLimited} from '../../../request-limits';

export async function POST(req:Request){
 try{
  if(req.headers.get('origin')!==new URL(req.url).origin||req.headers.get('sec-fetch-site')==='cross-site')return Response.json({error:'Yêu cầu không hợp lệ.'},{status:403});
  if(!(req.headers.get('content-type')||'').toLowerCase().startsWith('application/json'))return Response.json({error:'Yêu cầu không hợp lệ.'},{status:415});
  const raw=await readBodyLimited(req,2048);
  const ip=req.headers.get('cf-connecting-ip')||'unknown';
  const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(ip));
  const key=Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');
  const now=Math.floor(Date.now()/1000);
  await env.DB.prepare('DELETE FROM login_limits WHERE started_at < ? OR id IN (SELECT id FROM login_limits ORDER BY started_at DESC LIMIT -1 OFFSET 10000)').bind(now-900).run();
  const limit=await env.DB.prepare('INSERT INTO login_limits (id,attempts,started_at) VALUES (?,1,?) ON CONFLICT(id) DO UPDATE SET attempts=CASE WHEN started_at < ? THEN 1 ELSE attempts+1 END, started_at=CASE WHEN started_at < ? THEN ? ELSE started_at END RETURNING attempts').bind(key,now,now-900,now-900,now).first<{attempts:number}>();
  if(!limit||limit.attempts>8)return Response.json({error:'Đã thử quá nhiều lần. Vui lòng thử lại sau 15 phút.'},{status:429,headers:{'Retry-After':'900','Cache-Control':'no-store'}});
  let payload:unknown;try{payload=JSON.parse(new TextDecoder().decode(raw));}catch{return Response.json({error:'Yêu cầu không hợp lệ.'},{status:400});}
  const {username,password}=payload as {username?:unknown;password?:unknown};
  if(typeof username!=='string'||typeof password!=='string'||password.length>256)return Response.json({error:'Tên đăng nhập hoặc mật khẩu không đúng.'},{status:401,headers:{'Cache-Control':'no-store'}});
  const correct=await verifyPassword(password);
  if(username!=='admin'||!correct)return Response.json({error:'Tên đăng nhập hoặc mật khẩu không đúng.'},{status:401,headers:{'Cache-Control':'no-store'}});
  const token=await createSession();await env.DB.prepare('DELETE FROM login_limits WHERE id=?').bind(key).run();
  return Response.json({ok:true},{headers:{'Set-Cookie':sessionCookie(token),'Cache-Control':'no-store'}});
 }catch(error){
  if(error instanceof BodyTooLargeError)return Response.json({error:'Yêu cầu quá lớn.'},{status:413,headers:{'Cache-Control':'no-store'}});
  console.error(error);return Response.json({error:'Chưa đăng nhập được. Vui lòng thử lại.'},{status:503,headers:{'Cache-Control':'no-store'}});
 }
}
