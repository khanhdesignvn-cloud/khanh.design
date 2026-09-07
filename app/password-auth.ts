import {env} from 'cloudflare:workers';
import {parsePasswordHash} from './password-hash';

export const COOKIE='__Host-design-admin';
export const SESSION_SECONDS=8*60*60;
const enc=new TextEncoder();
const config=()=>env as unknown as {ADMIN_PASSWORD_HASH?:string;ADMIN_SESSION_SECRET?:string;DB:D1Database};
const hex=(bytes:ArrayBuffer)=>Array.from(new Uint8Array(bytes),b=>b.toString(16).padStart(2,'0')).join('');
function bytes(s:string){if(!/^[a-f0-9]+$/.test(s)||s.length%2)throw Error('Invalid hex');return new Uint8Array(s.match(/../g)!.map(x=>parseInt(x,16)));}

export async function verifyPassword(password:string){
 const parsed=parsePasswordHash(config().ADMIN_PASSWORD_HASH);if(!parsed)return false;
 const key=await crypto.subtle.importKey('raw',enc.encode(password),'PBKDF2',false,['deriveBits']);
 const salt=parsed.salt.buffer.slice(parsed.salt.byteOffset,parsed.salt.byteOffset+parsed.salt.byteLength) as ArrayBuffer;
 const hash=hex(await crypto.subtle.deriveBits({name:'PBKDF2',hash:'SHA-256',salt,iterations:parsed.rounds},key,256));
 let diff=hash.length^parsed.expectedHex.length;for(let i=0;i<hash.length;i++)diff|=hash.charCodeAt(i)^(parsed.expectedHex.charCodeAt(i)||0);return diff===0;
}
async function signingKey(){const secret=config().ADMIN_SESSION_SECRET;if(!secret||secret.length<32)throw Error('Login is not configured');return crypto.subtle.importKey('raw',enc.encode(secret),{name:'HMAC',hash:'SHA-256'},false,['sign','verify']);}
type Claims={sub:'admin';exp:number;nonce:string};
function tokenFromCookie(cookieHeader:string|null){return (cookieHeader||'').split(';').map(s=>s.trim()).find(s=>s.startsWith(COOKIE+'='))?.slice(COOKIE.length+1);}
async function verifiedClaims(cookieHeader:string|null):Promise<Claims|null>{try{const token=tokenFromCookie(cookieHeader);if(!token||token.length>1024)return null;const parts=token.split('.');if(parts.length!==2)return null;const [payload,sig]=parts;if(!await crypto.subtle.verify('HMAC',await signingKey(),bytes(sig),enc.encode(payload)))return null;const claims=JSON.parse(atob(payload.replace(/-/g,'+').replace(/_/g,'/'))) as Claims;const now=Math.floor(Date.now()/1000);return claims.sub==='admin'&&Number.isInteger(claims.exp)&&claims.exp>now&&claims.exp<=now+SESSION_SECONDS&&typeof claims.nonce==='string'&&/^[0-9a-f-]{36}$/.test(claims.nonce)?claims:null;}catch{return null;}}
export async function createSession(){const exp=Math.floor(Date.now()/1000)+SESSION_SECONDS,nonce=crypto.randomUUID();const payload=btoa(JSON.stringify({sub:'admin',exp,nonce})).replace(/=/g,'').replace(/\+/g,'-').replace(/\//g,'_');const token=payload+'.'+hex(await crypto.subtle.sign('HMAC',await signingKey(),enc.encode(payload)));await config().DB.prepare('DELETE FROM admin_sessions WHERE expires_at <= ?').bind(Math.floor(Date.now()/1000)).run();await config().DB.prepare('INSERT INTO admin_sessions (id,expires_at) VALUES (?,?)').bind(nonce,exp).run();return token;}
export async function validSession(cookieHeader:string|null){const claims=await verifiedClaims(cookieHeader);if(!claims)return false;try{return !!await config().DB.prepare('SELECT id FROM admin_sessions WHERE id=? AND expires_at>?').bind(claims.nonce,Math.floor(Date.now()/1000)).first();}catch{return false;}}
export async function revokeSession(cookieHeader:string|null){const claims=await verifiedClaims(cookieHeader);if(!claims)return;await config().DB.prepare('DELETE FROM admin_sessions WHERE id=?').bind(claims.nonce).run();}
export function sessionCookie(value:string,age=SESSION_SECONDS){return `${COOKIE}=${value}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${age}`;}
