'use client';
import {useState,useLayoutEffect,useRef} from 'react';
import type {AttachmentFilter} from './model';
export type ViewState={view:string;search:string;filter:string;fileFilter:AttachmentFilter;group:string;collapsed:string[]};
const defaults:ViewState={view:'map',search:'',filter:'Tất cả trạng thái',fileFilter:'all',group:'all',collapsed:[]};
export function readView(key:string):ViewState{
 try{const v=JSON.parse(localStorage.getItem(key)||'null');if(!v)return {...defaults};return {
 view:['map','table','showcase','report','overview'].includes(v.view)?v.view:'map',
 search:typeof v.search==='string'?v.search.slice(0,500):'',filter:['Tất cả trạng thái','Đang triển khai','Hoàn thành'].includes(v.filter)?v.filter:defaults.filter,
 fileFilter:['all','missing','attached'].includes(v.fileFilter)?v.fileFilter:'all',group:typeof v.group==='string'?v.group:'all',
 collapsed:Array.isArray(v.collapsed)?v.collapsed.filter((x:unknown)=>typeof x==='string').slice(0,1000):[]};}catch{return {...defaults};}
}
export function useContentScroll(key:string,view:string,ready:boolean){
 const ref=useRef<HTMLElement>(null);
 useLayoutEffect(()=>{
  const el=ref.current?.querySelector<HTMLElement>(':scope > .table-wrap,:scope > .showcase,:scope > .report-area,:scope > .workspace-insights');if(!ready||!el)return;
  const storageKey=key+':scroll:'+view;
  try{const saved=JSON.parse(localStorage.getItem(storageKey)||'null');if(saved){el.scrollTop=Number(saved.top)||0;el.scrollLeft=Number(saved.left)||0}}catch{}
  const remember=()=>{try{localStorage.setItem(storageKey,JSON.stringify({top:el.scrollTop,left:el.scrollLeft}))}catch{}};
  el.addEventListener('scroll',remember,{passive:true});window.addEventListener('pagehide',remember);
  return()=>{el.removeEventListener('scroll',remember);window.removeEventListener('pagehide',remember)};
 },[key,view,ready]);return ref;
}
export function useProjectView(key:string){
 const [state,setState]=useState<{key:string;value:ViewState}|null>(null);
 const value=state?.key===key?state.value:readView(key);
 function update<K extends keyof ViewState>(field:K,next:ViewState[K]|((prev:ViewState[K])=>ViewState[K])){
  setState(prev=>{const old=prev?.key===key?prev.value:readView(key);const value={...old,[field]:typeof next==='function'?next(old[field]):next};try{localStorage.setItem(key,JSON.stringify(value))}catch{}return {key,value};});
 }
 return {...value,setView:(v:string)=>update('view',v),setSearch:(v:string)=>update('search',v),setFilter:(v:string)=>update('filter',v),setFileFilter:(v:AttachmentFilter)=>update('fileFilter',v),setGroup:(v:string)=>update('group',v),setCollapsed:(v:string[]|((p:string[])=>string[]))=>update('collapsed',v)};
}
