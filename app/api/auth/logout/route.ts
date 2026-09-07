import {sessionCookie} from '../../../password-auth';
export async function POST(req:Request){if(req.headers.get('origin')!==new URL(req.url).origin)return Response.json({error:'Yêu cầu không hợp lệ.'},{status:403});return Response.json({ok:true},{headers:{'Set-Cookie':sessionCookie('',0),'Cache-Control':'no-store'}});}
