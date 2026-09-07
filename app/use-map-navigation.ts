'use client';
import {useEffect,useLayoutEffect,useRef,useState} from 'react';
export const clampZoom=(z:number)=>Math.max(.25,Math.min(2.5,z));
export function zoomPosition(old:number,next:number,left:number,top:number,x:number,y:number){return {left:(left+x)*next/old-x,top:(top+y)*next/old-y};}
export function useMapNavigation(enabled:boolean){
 const viewport=useRef<HTMLDivElement>(null),[zoom,setZoom]=useState(1),scale=useRef(1),pending=useRef<{left:number;top:number}|null>(null);
 const apply=(z:number,x?:number,y?:number)=>{const v=viewport.current;if(!v)return;const next=clampZoom(z);const position=pending.current||{left:v.scrollLeft,top:v.scrollTop};pending.current=zoomPosition(scale.current,next,position.left,position.top,x??v.clientWidth/2,y??v.clientHeight/2);scale.current=next;setZoom(next)};
 const fit=()=>{const v=viewport.current;if(v){const next=clampZoom(Math.min((v.clientWidth-24)/1260,(v.clientHeight-24)/(v.firstElementChild?.firstElementChild?.clientHeight||600),1));pending.current={left:0,top:0};if(next===scale.current){v.scrollTo(0,0);pending.current=null}else{scale.current=next;setZoom(next)}}};
 useLayoutEffect(()=>{if(viewport.current&&pending.current){viewport.current.scrollLeft=pending.current.left;viewport.current.scrollTop=pending.current.top;pending.current=null}},[zoom]);
 useEffect(()=>{const v=viewport.current;if(!enabled||!v)return;const points=new Map<number,{x:number;y:number}>();let moved=false,blockUntil=0,travel=0;
 const autoFitTimer=v.clientWidth<=640?window.setTimeout(fit,0):0;
 const down=(e:PointerEvent)=>{if(e.button!==0|| (e.target as Element).closest('.grip'))return;if(e.pointerType==='mouse'&&(e.target as Element).closest('button,a,input'))return;points.set(e.pointerId,{x:e.clientX,y:e.clientY});moved=false;travel=0;};
 const move=(e:PointerEvent)=>{const previous=points.get(e.pointerId);if(!previous)return;const oldPoints=[...points.values()];const oldMid=oldPoints.length>1?{x:(oldPoints[0].x+oldPoints[1].x)/2,y:(oldPoints[0].y+oldPoints[1].y)/2}:previous;points.set(e.pointerId,{x:e.clientX,y:e.clientY});const current=[...points.values()];const dx=e.clientX-previous.x,dy=e.clientY-previous.y;travel+=Math.abs(dx)+Math.abs(dy);if(travel<4&&!moved&&current.length<2)return;moved=true;blockUntil=Date.now()+350;v.setPointerCapture(e.pointerId);e.preventDefault();e.stopPropagation();
 if(current.length>=2&&oldPoints.length>=2){const before=Math.hypot(oldPoints[0].x-oldPoints[1].x,oldPoints[0].y-oldPoints[1].y);const after=Math.hypot(current[0].x-current[1].x,current[0].y-current[1].y);const mid={x:(current[0].x+current[1].x)/2,y:(current[0].y+current[1].y)/2};const rect=v.getBoundingClientRect();if(before>2){const next=clampZoom(scale.current*after/before);const pos=pending.current||{left:v.scrollLeft,top:v.scrollTop};const target=zoomPosition(scale.current,next,pos.left,pos.top,oldMid.x-rect.left,oldMid.y-rect.top);target.left-=mid.x-oldMid.x;target.top-=mid.y-oldMid.y;pending.current=target;if(next===scale.current){v.scrollLeft=target.left;v.scrollTop=target.top;pending.current=null}else{scale.current=next;setZoom(next)}}
 }else{v.scrollLeft-=dx;v.scrollTop-=dy;}};
 const up=(e:PointerEvent)=>{points.delete(e.pointerId);if(v.hasPointerCapture(e.pointerId))v.releasePointerCapture(e.pointerId);if(!points.size)moved=false;travel=0;};
 const wheel=(e:WheelEvent)=>{if((e.target as Element).closest('input,textarea'))return;e.preventDefault();const rect=v.getBoundingClientRect();const delta=e.deltaY*(e.deltaMode===1?16:e.deltaMode===2?v.clientHeight:1);apply(scale.current*Math.exp(-delta*.002),e.clientX-rect.left,e.clientY-rect.top)};
 const click=(e:MouseEvent)=>{if(Date.now()<blockUntil){e.preventDefault();e.stopPropagation()}};
 v.addEventListener('pointerdown',down,true);v.addEventListener('pointermove',move,{capture:true,passive:false});v.addEventListener('pointerup',up,true);v.addEventListener('pointercancel',up,true);v.addEventListener('wheel',wheel,{passive:false});v.addEventListener('click',click,true);
 return()=>{if(autoFitTimer)window.clearTimeout(autoFitTimer);v.removeEventListener('pointerdown',down,true);v.removeEventListener('pointermove',move,true);v.removeEventListener('pointerup',up,true);v.removeEventListener('pointercancel',up,true);v.removeEventListener('wheel',wheel);v.removeEventListener('click',click,true)};
 },[enabled]);
 return {viewport,zoom,zoomIn:()=>apply(scale.current*1.2),zoomOut:()=>apply(scale.current/1.2),fit};
}
