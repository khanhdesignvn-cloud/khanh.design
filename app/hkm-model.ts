export type HkmLine={id:string;image?:string;name:string;desc:string;unit:string;qty:number;price:number};
export type HkmQuote={id:string;name:string;number:string;date:string;customer:{name:string;address:string;phone:string;email:string};items:HkmLine[];discountPct:number;vatPct:number;notes:string};
export type HkmData={quotes:HkmQuote[]};
export const emptyHkmData:HkmData={quotes:[]};
export const fmtMoney=(n:number)=>Number(n||0).toLocaleString('vi-VN');
export const lineTotal=(l:HkmLine)=>(Number(l.qty)||0)*(Number(l.price)||0);

const SO=['không','một','hai','ba','bốn','năm','sáu','bảy','tám','chín'];
const DONVI=['','nghìn','triệu','tỷ','nghìn tỷ'];
function read3(n:number){const a=Math.floor(n/100),b=Math.floor(n/10)%10,c=n%10;let s='';if(a)s+=SO[a]+' trăm ';if(b===0&&a&&c)s+='lẻ ';if(b===1)s+='mười ';else if(b)s+=SO[b]+' mươi ';if(c===1&&b>1)s+='mốt';else if(c===5&&b>0)s+='lăm';else if(c)s+=SO[c];return s.trim();}
export function numToWordsVn(n:number){n=Math.round(Math.abs(n));if(n===0)return 'không đồng';let s='';let i=0;while(n>0){const g=n%1000;if(g)s=(read3(g)+(DONVI[i]?' '+DONVI[i]:''))+(s?' '+s:'');n=Math.floor(n/1000);i++;}return s.trim()+' đồng';}
