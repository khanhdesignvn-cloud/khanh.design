import {revokeSession,sessionCookie} from '../../../password-auth';

export async function POST(req:Request){
 if(req.headers.get('origin')!==new URL(req.url).origin)return Response.json({error:'Yêu cầu không hợp lệ.'},{status:403});
 try{await revokeSession(req.headers.get('cookie'));}catch{return Response.json({error:'Chưa đăng xuất được. Vui lòng thử lại.'},{status:503,headers:{'Cache-Control':'no-store'}});}
 return Response.json({ok:true},{headers:{'Set-Cookie':sessionCookie('',0),'Cache-Control':'no-store'}});
}
