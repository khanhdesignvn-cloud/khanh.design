'use client';
import {useEffect,useRef,useState} from 'react';
import {ChevronLeft,ChevronRight,Maximize,Minimize,X} from 'lucide-react';
import {Dialog,DialogContent,DialogTitle,DialogDescription} from '@/components/ui/dialog';
import type {Attachment} from './model';

export type ShowcaseSlide={file:Attachment;title:string;itemId:string;imageIndex:number};
export default function ShowcaseSlideshow({slides,start,onClose,trigger}:{slides:ShowcaseSlide[];start:number;onClose:()=>void;trigger:HTMLElement|null}) {
  const [index,setIndex]=useState(start);
  const [fullscreen,setFullscreen]=useState(false);
  const [notice,setNotice]=useState('');
  const container=useRef<HTMLDivElement>(null);
  const touch=useRef<{x:number;y:number}|null>(null);
  const slide=slides[index];
  const advance=(delta:number)=>setIndex(current=>(current+delta+slides.length)%slides.length);
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
    <DialogContent ref={container} className="showcase-slideshow" style={{translate:'none',transform:'none'}} showCloseButton={false}
      onCloseAutoFocus={event=>{event.preventDefault();trigger?.focus()}}
      onKeyDown={event=>{if(event.key==='ArrowRight'||event.key==='ArrowLeft'){event.preventDefault();advance(event.key==='ArrowRight'?1:-1)}}}>
      <header className="showcase-slide-header"><div><DialogTitle>{slide.file.name}</DialogTitle><DialogDescription>{slide.title}</DialogDescription></div>
        <button aria-label={fullscreen?'Thoát toàn màn hình':'Toàn màn hình'} onClick={()=>void toggleFullscreen()}>{fullscreen?<Minimize/>:<Maximize/>}</button>
        <button aria-label="Đóng trình chiếu" onClick={()=>void close()}><X/></button>
      </header>
      <div className="showcase-slide-stage"
        onTouchStart={event=>{touch.current=event.touches.length===1?{x:event.touches[0].clientX,y:event.touches[0].clientY}:null}}
        onTouchCancel={()=>{touch.current=null}}
        onTouchEnd={event=>{const start=touch.current;touch.current=null;if(!start||!event.changedTouches.length)return;const dx=event.changedTouches[0].clientX-start.x,dy=event.changedTouches[0].clientY-start.y;if(Math.abs(dx)>=50&&Math.abs(dx)>Math.abs(dy)*1.5)advance(dx<0?1:-1)}}><img key={slide.file.url} src={slide.file.url} alt={slide.file.name} draggable={false}/></div>
      <footer className="showcase-slide-controls"><button aria-label="Ảnh trước" disabled={slides.length<2} onClick={()=>advance(-1)}><ChevronLeft/></button><span aria-live="polite" aria-atomic="true">{index+1} / {slides.length}</span><button aria-label="Ảnh tiếp" disabled={slides.length<2} onClick={()=>advance(1)}><ChevronRight/></button></footer>
      {notice&&<p className="showcase-slide-notice" role="status">{notice}</p>}
    </DialogContent>
  </Dialog>;
}
