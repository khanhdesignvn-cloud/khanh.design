import khesanhProject from './data/khesanh-project.json';

export const statuses=['Chưa giao việc','Đang triển khai','Đợi duyệt','Hoàn thành'];
export const legacyStatuses=['Chưa bắt đầu','Đang thiết kế','Chờ duyệt','Cần chỉnh sửa'];
export const normalizeStatus=(s:string)=>s==='Chưa bắt đầu'?'Chưa giao việc':s==='Chờ duyệt'?'Đợi duyệt':['Đang thiết kế','Cần chỉnh sửa'].includes(s)?'Đang triển khai':s;
export function normalizeData(data:Data):Data{return {...data,projects:data.projects.map(p=>({...p,groups:p.groups.map(g=>({...g,items:g.items.map(i=>({...i,status:normalizeStatus(i.status)}))}))}))};}
export type Attachment={id:string;name:string;url:string;type:'image'|'pdf'|'drive'};
export type Item={id:string;name:string;status:string;note:string;images:string[];files?:Attachment[];driveUrl?:string};
export type Group={id:string;name:string;items:Item[]};
export type Project={id:string;name:string;subtitle:string;groups:Group[];driveFolder?:string;cover?:string};
export type Data={projects:Project[]};
export const driveValid=(value:string)=>{if(!value)return true;try{const u=new URL(value);return u.protocol==='https:'&&['drive.google.com','docs.google.com'].includes(u.hostname)&&!u.username&&!u.password}catch{return false}};
export const groupCode=(i:number)=>String(i+1).padStart(2,'0');
export const itemCode=(gi:number,ii:number)=>`${groupCode(gi)}.${String(ii+1).padStart(2,'0')}`;
export const attachments=(item:Item):Attachment[]=>[...item.images.map(url=>({id:url,name:'Ảnh thiết kế',url,type:'image' as const})),...(item.files||[])];
export type DragNode={kind:'group'|'item';id:string;group?:string};
export function moveNode(data:Data,projectId:string,from:DragNode,to:DragNode):Data {const next=structuredClone(data);const p=next.projects.find(p=>p.id===projectId);if(!p||from.id===to.id)return data;if(from.kind==='group'){const target=to.kind==='group'?to.id:to.group;const a=p.groups.findIndex(g=>g.id===from.id),b=p.groups.findIndex(g=>g.id===target);if(a<0||b<0||a===b)return data;const [g]=p.groups.splice(a,1);p.groups.splice(b,0,g);}else{const src=p.groups.find(g=>g.id===from.group),dest=p.groups.find(g=>g.id===(to.kind==='group'?to.id:to.group));if(!src||!dest)return data;const a=src.items.findIndex(i=>i.id===from.id);if(a<0)return data;const [item]=src.items.splice(a,1);const b=to.kind==='item'?dest.items.findIndex(i=>i.id===to.id):-1;dest.items.splice(b<0?dest.items.length:b,0,item);}return next;}
export const initial:Data={projects:[khesanhProject as unknown as Project]};
