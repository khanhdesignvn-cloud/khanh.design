import {redirect} from 'next/navigation';
import {headers} from 'next/headers';
export const dynamic='force-dynamic';
export default async function Page(){
  const h=await headers();
  const host=(h.get('x-forwarded-host')||h.get('host')||'khanh.design').split(',')[0].trim();
  redirect(`https://${host}/admin`);
}
