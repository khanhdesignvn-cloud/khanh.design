'use client';
import {Data,Item,searchWorkspace,normalizeStatus,attachments} from './model';

type Result=ReturnType<typeof searchWorkspace>[number];
export default function WorkspaceInsights({data,results,onOpen}:{data:Data;results:Result[];onOpen:(projectId:string,groupId:string,item:Item)=>void}){
 return <div className="workspace-insights">
  <h2>Tổng quan tiến độ</h2>
  <p className="hint">Tiến độ toàn bộ dự án được phép xem · Tìm theo tên, đường dẫn, ghi chú hoặc mã vị trí.</p>
  <div className="insight-projects">{data.projects.map(project=>{
   const items=project.groups.flatMap(g=>g.items),done=items.filter(i=>normalizeStatus(i.status)==='Hoàn thành').length;
   const missing=items.filter(i=>!attachments(i).length&&!i.driveUrl).length;
   return <section className="insight-project" key={project.id} aria-label={'Tiến độ '+project.name}>
    <h3>{project.name}</h3><strong>{done} / {items.length} hoàn thành</strong>
    <progress max={items.length||1} value={done} aria-label={'Tiến độ '+project.name}/>
    <p>{items.length-done} đang triển khai · {missing} chưa có tệp</p>
   </section>;
  })}</div>
  <h3>Kết quả tìm kiếm <span>({results.length})</span></h3>
  <p className="hint">Bộ lọc áp dụng cho kết quả bên dưới; tiến độ phía trên luôn tính toàn bộ dự án.</p>
  {!results.length&&<p role="status">Không có sản phẩm phù hợp. Thử xóa từ khóa hoặc đổi bộ lọc.</p>}
  <div className="insight-results">{results.map(result=><button className="insight-result" key={result.projectId+':'+result.groupId+':'+result.item.id} onClick={()=>onOpen(result.projectId,result.groupId,result.item)}>
   <small>{result.breadcrumb}</small><strong>{result.code} · {result.item.name}</strong><span>{normalizeStatus(result.item.status)}{!attachments(result.item).length&&!result.item.driveUrl?' · Chưa có tệp':''}</span>
  </button>)}</div>
 </div>;
}
