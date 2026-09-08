'use client';
import './showcase.css';
import {useState} from 'react';
import ShowcaseSlideshow,{type ShowcaseSlide} from './showcase-slideshow';
import {ArrowUpRight, Images} from 'lucide-react';
import {attachments, driveValid, type Group, type Item} from './model';

export default function Showcase({groups,onItem,onEmpty}:{groups:Group[];onItem:(group:string,item:Item)=>void;onEmpty:()=>void}) {
  const [presentation,setPresentation]=useState<{slides:ShowcaseSlide[];start:number;trigger:HTMLElement}|null>(null);
  const cards=groups.flatMap(group=>group.items.map(item=>({group,item,files:attachments(item).map(file=>{
    if(file.type!=='image'||!item.images.includes(file.url))return file;
    // Legacy images have only a URL, not the original uploaded filename.
    try{return {...file,name:decodeURIComponent(new URL(file.url,'https://khanh.design').pathname.split('/').pop()||file.name)}}catch{return file}
  })})))
    .filter(({item,files})=>files.length||(item.driveUrl&&driveValid(item.driveUrl)));
  const slides=cards.flatMap(({item,files})=>files.filter(file=>file.type==='image').map((file,imageIndex)=>({file,title:item.name,itemId:item.id,imageIndex})));
  return <div className="showcase showcase-gallery">
    {cards.map(({group,item,files})=><article key={item.id} className="showcase-card">
      <button className="showcase-description" onClick={()=>onItem(group.id,item)}>
        <small>{group.name} · {files.filter(f=>f.type==='image').length} ảnh</small>
        <h3>{item.name}</h3><span className="status">{item.status}</span>
      </button>
      <div className="showcase-images">{files.filter(f=>f.type==='image').map((file,index)=><button key={`${file.id}-${index}`} className="showcase-image" onClick={event=>{setPresentation({slides,trigger:event.currentTarget,start:slides.findIndex(s=>s.itemId===item.id&&s.imageIndex===index)})}} aria-label={`Xem ${file.name} · ${item.name}`}>
        <img src={file.url} alt={file.name} loading="lazy"/><span>{file.name}</span>
      </button>)}</div>
      <div className="showcase-links">{files.filter(f=>f.type!=='image').filter(f=>f.type!=='drive'||driveValid(f.url)).map((file,index)=><a key={`${file.id}-${index}`} href={file.url} target="_blank" rel="noopener noreferrer">{file.name}<small>{file.type==='pdf'?'PDF':'Google Drive'}</small><ArrowUpRight size={16}/></a>)}
        {item.driveUrl&&driveValid(item.driveUrl)&&<a href={item.driveUrl} target="_blank" rel="noopener noreferrer">Thư mục Google Drive<ArrowUpRight size={16}/></a>}
      </div>
    </article>)}
    {!cards.length&&<div className="empty"><Images size={38}/><h3>Showcase của dự án</h3><p>Thêm ảnh, PDF hoặc liên kết Google Drive vào từng hạng mục để trưng bày thiết kế.</p><button className="outline" onClick={onEmpty}>Chọn hạng mục <ArrowUpRight size={16}/></button></div>}
    {presentation&&<ShowcaseSlideshow {...presentation} onClose={()=>setPresentation(null)}/>}
  </div>;
}
