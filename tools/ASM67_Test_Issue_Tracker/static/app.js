let opts = {}, issues = [], quick = 'open', editIssue = null;
const $ = id => document.getElementById(id);

function fill(sel, values, blank=null){
  const el=$(sel); const prior=el.value; el.innerHTML='';
  if(blank!==null){const o=document.createElement('option');o.value='';o.textContent=blank;el.append(o)}
  values.forEach(v=>{const o=document.createElement('option');o.value=v;o.textContent=v;el.append(o)});
  if([...el.options].some(o=>o.value===prior)) el.value=prior;
}
function qp(){
  const p=new URLSearchParams(); if(quick)p.set('quick',quick);
  [['mode','fMode'],['type','fType'],['area','fArea'],['status','fStatus']].forEach(([k,id])=>{if($(id).value)p.set(k,$(id).value)});
  if($('search').value.trim())p.set('q',$('search').value.trim()); return p;
}
function safeJson(obj){
  return JSON.stringify(obj).replace(/[^\x00-\x7F]/g,c=>'\\u'+c.charCodeAt(0).toString(16).padStart(4,'0'));
}
async function load(){
  const r=await fetch('/api/issues?'+qp());
  if(!r.ok){const msg=await responseError(r);toast('Could not load issues: '+msg);return}
  const data=await r.json(); issues=Array.isArray(data)?data:(data?[data]:[]); render();
}
function td(label, html){ return `<td data-label="${label}">${html}</td>`; }
function render(){
  $('summary').textContent=`${issues.length} issue${issues.length===1?'':'s'} shown`;
  $('issues').innerHTML='';
  issues.forEach(i=>{
    const tr=document.createElement('tr');
    tr.innerHTML=
      td('ID',`#${i.id}`)+
      td('Mode',esc(i.mode))+
      td('Type / Area',`<span class="pill">${esc(i.issue_type)}</span><br><small>${esc(i.area)}</small>`)+
      td('Priority',`<span class="pill priority-${css(i.priority)}">${esc(i.priority)}</span>`)+
      td('Issue',`<div class="issue-title">${esc(i.title)}</div><div class="notes-preview">${esc(i.notes||'')}</div>`)+
      td('Status',`<select class="status-select">${opts.statuses.map(s=>`<option${s===i.status?' selected':''}>${esc(s)}</option>`).join('')}</select>`)+
      td('Updated',`<small>${fmt(i.updated_at)}</small>`)+
      td('',`<button class="edit-btn">Edit</button>`);
    tr.querySelector('.status-select').addEventListener('change', async e=>{
      try{await update(i.id,{status:e.target.value});toast(`Issue #${i.id} → ${e.target.value}`);await load()}
      catch(err){toast('Could not save status: '+err.message);await load()}
    });
    tr.querySelector('.edit-btn').addEventListener('click',()=>openEdit(i)); $('issues').append(tr);
  });
}
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const css=s=>String(s).replace(/[^a-z0-9_-]/gi,'');
function fmt(s){try{return new Date(s).toLocaleString()}catch{return s}}
async function responseError(r){
  try{const data=await r.json();return data.detail||data.error||(`HTTP ${r.status}`)}catch{try{return (await r.text())||(`HTTP ${r.status}`)}catch{return `HTTP ${r.status}`}}
}
async function update(id, body){
  const r=await fetch('/api/issues/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:safeJson(body)});
  if(!r.ok) throw new Error(await responseError(r));
  return r;
}
function toast(t){const el=$('toast');el.textContent=t;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),1800)}

async function add(){
  const body={mode:$('mode').value,issue_type:$('type').value,area:$('area').value,priority:$('priority').value,title:$('title').value.trim(),notes:$('notes').value.trim()};
  if(!body.title){$('title').focus();return}
  const r=await fetch('/api/issues',{method:'POST',headers:{'Content-Type':'application/json'},body:safeJson(body)});
  if(!r.ok){toast('Could not save issue: '+await responseError(r));return}
  $('title').value='';$('notes').value='';toast('Issue added');$('title').focus();await load();
}
function openEdit(i){editIssue=i;$('editId').textContent='#'+i.id;$('eMode').value=i.mode;$('eType').value=i.issue_type;$('eArea').value=i.area;$('ePriority').value=i.priority;$('eStatus').value=i.status;$('eTitle').value=i.title;$('eNotes').value=i.notes||'';$('editDialog').showModal()}
async function saveEdit(){
  if(!editIssue)return;
  const body={mode:$('eMode').value,issue_type:$('eType').value,area:$('eArea').value,priority:$('ePriority').value,status:$('eStatus').value,title:$('eTitle').value.trim(),notes:$('eNotes').value.trim()};
  try{await update(editIssue.id,body);$('editDialog').close();toast('Issue saved');await load()}catch(e){toast('Could not save issue: '+e.message)}
}
async function del(){
  if(!editIssue||!confirm(`Delete issue #${editIssue.id}?`))return;
  const r=await fetch('/api/issues/'+editIssue.id,{method:'DELETE'});
  if(!r.ok){toast('Could not delete issue: '+await responseError(r));return}
  $('editDialog').close();toast('Issue deleted');await load();
}
async function copyText(text){
  try{ if(navigator.clipboard && window.isSecureContext){ await navigator.clipboard.writeText(text); return true; } }catch{}
  const ta=document.createElement('textarea');ta.value=text;ta.style.position='fixed';ta.style.opacity='0';document.body.append(ta);ta.focus();ta.select();
  let ok=false;try{ok=document.execCommand('copy')}catch{} ta.remove(); return ok;
}
async function copyChat(){const t=await (await fetch('/api/copy?'+qp())).text();const ok=await copyText(t);if(ok)toast('Copied current list for ChatGPT');else{prompt('Copy this text:',t)}}
function download(kind){window.location='/api/export/'+kind+'?'+qp()}

function drawQr(url){
  const host=$('qr');host.innerHTML='';
  if(!window.ASM67QRCode || !url)return;
  try{
    const QRCode=window.ASM67QRCode.QRCode, E=window.ASM67QRCode.QRErrorCorrectLevel;
    const q=new QRCode(-1,E.L);q.addData(url);q.make();
    const n=q.getModuleCount(), quiet=4, cell=Math.max(4,Math.floor(220/(n+quiet*2))), size=(n+quiet*2)*cell;
    const canvas=document.createElement('canvas');canvas.width=size;canvas.height=size;canvas.className='qr-canvas';
    const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,size,size);ctx.fillStyle='#000';
    for(let r=0;r<n;r++)for(let c=0;c<n;c++)if(q.isDark(r,c))ctx.fillRect((c+quiet)*cell,(r+quiet)*cell,cell,cell);
    host.append(canvas);
  }catch(e){host.textContent='QR unavailable';console.error(e)}
}
async function loadServerInfo(){
  try{
    const info=await (await fetch('/api/serverinfo')).json();
    const url=info.primary_url || location.href;
    $('phoneUrl').textContent=url;$('phoneUrl').href=url;drawQr(url);
  }catch{$('phoneUrl').textContent='LAN address unavailable';}
}

async function init(){
  opts=await (await fetch('/api/options')).json();
  fill('mode',opts.modes);fill('type',opts.types);fill('area',opts.areas);fill('priority',opts.priorities);$('priority').value='Normal';
  fill('fMode',opts.modes,'All modes');fill('fType',opts.types,'All types');fill('fArea',opts.areas,'All areas');fill('fStatus',opts.statuses,'All statuses');
  fill('eMode',opts.modes);fill('eType',opts.types);fill('eArea',opts.areas);fill('ePriority',opts.priorities);fill('eStatus',opts.statuses);
  $('addBtn').onclick=add;$('saveEditBtn').onclick=saveEdit;$('deleteBtn').onclick=del;$('copyBtn').onclick=copyChat;$('mdBtn').onclick=()=>download('markdown');$('csvBtn').onclick=()=>download('csv');
  document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));b.classList.add('active');quick=b.dataset.quick;load()});
  ['fMode','fType','fArea','fStatus'].forEach(id=>$(id).onchange=load);let timer;$('search').oninput=()=>{clearTimeout(timer);timer=setTimeout(load,200)};
  $('title').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();add()}});
  await loadServerInfo(); load();
}
init();
