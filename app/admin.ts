import {headers} from 'next/headers';
import {validSession} from './password-auth';

export async function adminSession(){
  const isAdmin=await validSession((await headers()).get('cookie'));
  return {isAdmin};
}

export async function authorizeWrite(req:Request){
  const {isAdmin}=await adminSession();
  if(!isAdmin)return Response.json({error:'Chỉ quản trị viên đã đăng nhập mới được chỉnh sửa.'},{status:403});
  const origin=req.headers.get('origin');
  if(req.headers.get('sec-fetch-site')==='cross-site'||(origin&&origin!==new URL(req.url).origin))return Response.json({error:'Yêu cầu không hợp lệ.'},{status:403});
  return null;
}
