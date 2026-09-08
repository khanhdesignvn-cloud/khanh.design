'use client';
import {useState} from 'react';
export default function LoginScreen(){
 const [username,setUsername]=useState('admin'),[password,setPassword]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function submit(e:React.FormEvent){e.preventDefault();setBusy(true);setError('');try{const r=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})});const j=await r.json();if(!r.ok)throw Error(j.error);window.location.assign('/admin');}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 return <main className="login-screen"><form className="login-card" onSubmit={submit}><div className="login-brand">khanh.design</div><h1>Đăng nhập quản trị</h1><p>Đăng nhập để quản lý dự án và chia sẻ cho khách.</p><label>Tên đăng nhập<input autoComplete="username" value={username} onChange={e=>setUsername(e.target.value)} required autoFocus/></label><label>Mật khẩu<input type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} required/></label>{error&&<p className="error" role="alert">{error}</p>}<button className="primary" disabled={busy}>{busy?'Đang đăng nhập…':'Đăng nhập'}</button></form></main>;
}
