const header=document.querySelector('[data-header]');
const toggle=document.querySelector('[data-menu-toggle]');
const drawer=document.querySelector('[data-mobile-menu]');
const backdrop=document.querySelector('[data-menu-backdrop]');
const navLinks=[...document.querySelectorAll('[data-nav-link]')];
const sections=[...document.querySelectorAll('[data-section]')];

function setMenu(open){
  toggle.setAttribute('aria-expanded',String(open));
  toggle.setAttribute('aria-label',open?'Đóng menu':'Mở menu');
  drawer.setAttribute('aria-hidden',String(!open));
  drawer.classList.toggle('open',open);
  backdrop.classList.toggle('open',open);
  header.classList.toggle('menu-open',open);
}
toggle.addEventListener('click',()=>setMenu(toggle.getAttribute('aria-expanded')!=='true'));
backdrop.addEventListener('click',()=>setMenu(false));
window.addEventListener('keydown',event=>{if(event.key==='Escape')setMenu(false)});
navLinks.forEach(link=>link.addEventListener('click',()=>setMenu(false)));

function updateNavigation(){
  const marker=window.scrollY+Math.max(144,window.innerHeight*.28);
  let active='';
  sections.forEach(section=>{if(section.offsetTop<=marker)active=section.dataset.section});
  navLinks.forEach(link=>link.classList.toggle('active',link.dataset.navLink===active));
  header.classList.toggle('scrolled',window.scrollY>18);
}
window.addEventListener('scroll',updateNavigation,{passive:true});
updateNavigation();

const revealObserver=new IntersectionObserver(entries=>{
  entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('in-view');revealObserver.unobserve(entry.target)}});
},{threshold:.12});
document.querySelectorAll('.reveal').forEach(node=>revealObserver.observe(node));

const form=document.getElementById('project-form');
const status=document.getElementById('form-success');
const draftKey='khanh-design-project-brief';
const fields=['name','phone','email','brand','service','budget','story'];

function formValues(){
  const data=new FormData(form);
  const values={};
  fields.forEach(field=>{values[field]=String(data.get(field)||'').trim()});
  return values;
}
function saveDraft(){
  localStorage.setItem(draftKey,JSON.stringify(formValues()));
}
function restoreDraft(){
  try{
    const values=JSON.parse(localStorage.getItem(draftKey)||'{}');
    fields.forEach(field=>{if(values[field]&&form.elements[field])form.elements[field].value=values[field]});
  }catch(error){localStorage.removeItem(draftKey)}
}
form.addEventListener('input',saveDraft);
restoreDraft();

form.addEventListener('submit',event=>{
  event.preventDefault();
  status.className='form-note';
  const values=formValues();
  const missing=[];
  if(!values.name)missing.push('họ và tên');
  if(!values.phone)missing.push('số điện thoại');
  if(!values.service)missing.push('dịch vụ quan tâm');
  if(!values.story)missing.push('câu chuyện dự án');
  if(missing.length){
    status.className='form-note error';
    status.textContent='Vui lòng bổ sung: '+missing.join(', ')+'.';
    const first=form.querySelector(':invalid');
    if(first)first.focus();
    return;
  }
  saveDraft();
  const subject='Brief dự án từ '+(values.brand||values.name);
  const body=[
    'Họ và tên: '+values.name,
    'Số điện thoại: '+values.phone,
    'Email: '+(values.email||'Chưa cung cấp'),
    'Tên thương hiệu: '+(values.brand||'Chưa xác định'),
    'Dịch vụ quan tâm: '+values.service,
    'Ngân sách dự kiến: '+(values.budget||'Chưa xác định'),
    '',
    'Câu chuyện và mục tiêu:',
    values.story
  ].join('\n');
  status.textContent='Thông tin đã được chuẩn bị. Ứng dụng email sẽ mở để bạn xác nhận gửi.';
  window.location.href='mailto:hi@nguyenquockhanh.vn?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(body);
});
