'use client';
import {useEffect,useRef,useState} from 'react';
import {ChevronLeft,ChevronRight,Maximize,Minimize,X,ZoomIn,ZoomOut,Download} from 'lucide-react';
import {Dialog,DialogContent,DialogTitle,DialogDescription} from '@/components/ui/dialog';
import type {Attachment} from './model';

export type ShowcaseSlide={file:Attachment;title:string;itemId:string;imageIndex:number};
export default function ShowcaseSlideshow({slides,start,onClose,trigger,enhanced=false}:{slides:ShowcaseSlide[];start:number;onClose:()=>void;trigger:HTMLElement|null;enhanced?:boolean}) {
  const [index,setIndex]=useState(start);
  const [scale,setScale]=useState(1);
  const [downloading,setDownloading]=useState(false);
  const stage=useRef<HTMLDivElement>(null);
  const [fullscreen,setFullscreen]=useState(false);
  const [notice,setNotice]=useState('');
  const container=useRef<HTMLDivElement>(null);
  const touch=useRef<{x:number;y:number}|null>(null);
  const slide=slides[index];
  const select=(next:number)=>{setIndex(next);setScale(1);setNotice('');stage.current?.scrollTo(0,0)};
  const advance=(delta:number)=>select((index+delta+slides.length)%slides.length);
  async function downloadImage(){
    setDownloading(true);setNotice('');
    try{
      const response=await fetch(slide.file.url);
      if(!response.ok)throw Error('download');
      const url=URL.createObjectURL(await response.blob());
      const link=document.createElement('a');link.href=url;link.download=slide.file.name;
      document.body.appendChild(link);link.click();link.remove();
      window.setTimeout(()=>URL.revokeObjectURL(url),60000);
    }catch{setNotice('Chưa tải được ảnh. Vui lòng thử lại hoặc mở file gốc trên Google Drive.')}
    finally{setDownloading(false)}
  }
  useEffect(()=>{
    const change=()=>setFullscreen(document.fullscreenElement===container.current);
    document.addEventListener('fullscreenchange',change);
    return()=>document.removeEventListener('fullscreenchange',change);
  },[]);
  async function close(){
    if(document.fullscreenElement===container.current)try{await document.exitFullscreen()}catch{}
    onClose();
  }
  async function toggleFullscreen(){
    setNotice('');
    try{
      if(document.fullscreenElement===container.current)await document.exitFullscreen();
      else if(container.current?.requestFullscreen)await container.current.requestFullscreen();
      else setNotice('Trình duyệt chưa hỗ trợ toàn màn hình. Bạn vẫn có thể xem ảnh trong trình chiếu.');
    }catch{setNotice('Chưa bật được toàn màn hình. Bạn vẫn có thể xem ảnh trong trình chiếu.')}
  }
  return <Dialog open onOpenChange={open=>{if(!open)void close()}}>
    <DialogContent ref={container} className={'showcase-slideshow'+(enhanced?' item-slideshow':'')} style={{translate:'none',transform:'none'}} showCloseButton={false}
      onCloseAutoFocus={event=>{event.preventDefault();trigger?.focus()}}
      onKeyDown={event=>{if(event.key==='ArrowRight'||event.key==='ArrowLeft'){event.preventDefault();advance(event.key==='ArrowRight'?1:-1)}}}>
      <header className="showcase-slide-header"><div><DialogTitle>{slide.title}</DialogTitle><DialogDescription>Ảnh {slide.imageIndex+1}</DialogDescription></div>
        <button aria-label={fullscreen?'Thoát toàn màn hình':'Toàn màn hình'} onClick={()=>void toggleFullscreen()}>{fullscreen?<Minimize/>:<Maximize/>}</button>
        <button aria-label="Đóng trình chiếu" onClick={()=>void close()}><X/></button>
      </header>
      <div ref={stage} className="showcase-slide-stage"
        onTouchStart={event=>{touch.current=event.touches.length===1?{x:event.touches[0].clientX,y:event.touches[0].clientY}:null}}
        onTouchCancel={()=>{touch.current=null}}
        onTouchEnd={event=>{const start=touch.current;touch.current=null;if(!start||scale!==1||!event.changedTouches.length)return;const dx=event.changedTouches[0].clientX-start.x,dy=event.changedTouches[0].clientY-start.y;if(Math.abs(dx)>=50&&Math.abs(dx)>Math.abs(dy)*1.5)advance(dx<0?1:-1)}}>{enhanced?<div className="item-slide-canvas" style={{width:`${scale*100}%`,height:`${scale*100}%`}}><img key={slide.file.url} src={slide.file.url} alt={`${slide.title} · Ảnh ${slide.imageIndex+1}`} draggable={false}/></div>:<img key={slide.file.url} src={slide.file.url} alt={`${slide.title} · Ảnh ${slide.imageIndex+1}`} draggable={false}/>}</div>
      {enhanced&&<div className="item-slide-tools"><button aria-label="Thu nhỏ ảnh" disabled={scale<=1} onClick={()=>setScale(s=>Math.max(1,s-.25))}><ZoomOut/></button><button aria-label="Đặt lại thu phóng" onClick={()=>{setScale(1);stage.current?.scrollTo(0,0)}}>{Math.round(scale*100)}%</button><button aria-label="Phóng to ảnh" disabled={scale>=4} onClick={()=>setScale(s=>Math.min(4,s+.25))}><ZoomIn/></button><button aria-label="Tải ảnh hiện tại" disabled={downloading} onClick={()=>void downloadImage()}><Download/></button></div>}
      {enhanced&&<nav className="item-slide-thumbnails" aria-label="Ảnh trong hạng mục">{slides.map((s,i)=><button key={`${s.file.id}-${i}`} aria-label={`Xem ảnh ${i+1}`} aria-current={i===index?'true':undefined} onClick={()=>select(i)}><img src={s.file.url} alt="" loading="lazy"/></button>)}</nav>}
      <footer className="showcase-slide-controls"><button aria-label="Ảnh trước" disabled={slides.length<2} onClick={()=>advance(-1)}><ChevronLeft/></button><span aria-live="polite" aria-atomic="true">{index+1} / {slides.length}</span><button aria-label="Ảnh tiếp" disabled={slides.length<2} onClick={()=>advance(1)}><ChevronRight/></button></footer>
      {notice&&<p className="showcase-slide-notice" role="status">{notice}</p>}
    </DialogContent>
  </Dialog>;
}
