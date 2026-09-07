import {authorizeWrite} from '../../admin';
import {env} from 'cloudflare:workers';
import {BodyTooLargeError,requestWithLimitedBody} from '../../request-limits';
import {validateUpload} from '../../upload-validation';

const MAX_FILE_BYTES=25*1024*1024;
const MAX_MULTIPART_BYTES=MAX_FILE_BYTES+64*1024;

export async function POST(req:Request){
 try{
  const denied=await authorizeWrite(req);if(denied)return denied;
  const limited=await requestWithLimitedBody(req,MAX_MULTIPART_BYTES);
  const form=await limited.formData();const file=form.get('file');
  if(!(file instanceof File))return Response.json({error:'Chọn ảnh JPG, PNG, WebP, GIF hoặc PDF.'},{status:400});
  if(file.size>MAX_FILE_BYTES)return Response.json({error:'Tệp tối đa 25 MB.'},{status:413});
  const bytes=await file.arrayBuffer();const invalid=validateUpload(file.type,new Uint8Array(bytes));
  if(invalid)return Response.json({error:invalid},{status:400});
  const id=crypto.randomUUID();await env.BUCKET.put(id,bytes,{httpMetadata:{contentType:file.type},customMetadata:{name:file.name.slice(0,200)}});
  return Response.json({id,name:file.name.slice(0,200),url:'/api/image/'+id,type:file.type==='application/pdf'?'pdf':'image'});
 }catch(error){
  if(error instanceof BodyTooLargeError)return Response.json({error:'Tệp tối đa 25 MB.'},{status:413});
  console.error(error);return Response.json({error:'Chưa tải được tệp. Vui lòng thử lại.'},{status:503});
 }
}
