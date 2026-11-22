'use strict';
const $ = id => document.getElementById(id);
const state = { tickets: [], selectedId: null, selected: null, busy: false };
let toastTimer;
function h(value) { return String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch])); }
function showToast(message, error=false) { const node=$('toast'); node.textContent=message; node.className='toast visible'+(error?' error':''); clearTimeout(toastTimer); toastTimer=setTimeout(()=>node.className='toast',5200); }
async function api(path, options={}) {
  let response;
  try { response=await fetch(path,{...options,headers:{'Content-Type':'application/json',...(options.headers||{})}}); }
  catch(e) { throw new Error('Server offline. Run: python -m uvicorn backend.main:app --port 8002'); }
  const body=await response.json().catch(()=>({detail:'Unexpected server response'}));
  if(!response.ok) throw new Error(typeof body.detail==='string'?body.detail:`Request failed (${response.status})`);
  return body;
}
function renderTickets() {
  $('tickets-count').textContent=state.tickets.length+' ticket'+(state.tickets.length===1?'':'s');
  const list=$('ticket-list');
  if(!state.tickets.length){list.innerHTML='<p class="empty">No tickets yet. Create one above to start the workflow.</p>';return;}
  list.innerHTML=state.tickets.map(t=>`<button class="ticket-row ${state.selectedId===t.id?'selected':''}" data-id="${t.id}" type="button"><div class="ticket-title">#${t.id} · ${h(t.subject)}</div><div class="ticket-excerpt">${h(t.message)}</div><div class="ticket-meta"><span class="tag ${h(t.category)}">${h(t.category)}</span><span>${h(t.status)}</span></div></button>`).join('');
  list.querySelectorAll('[data-id]').forEach(button=>button.addEventListener('click',()=>selectTicket(Number(button.dataset.id))));
}
async function selectTicket(id) {
  state.selectedId=id;
  renderTickets();
  try{state.selected=await api(`/api/tickets/${id}`);renderDetail();}
  catch(e){showToast(e.message,true);}
}
function renderDetail(){
  const node=$('ticket-detail'); const selected=state.selected;
  if(!selected){node.innerHTML='<p class="empty">Choose a ticket from the queue.</p>';return;}
  const {ticket,drafts}=selected;
  const latest=drafts[0];
  node.innerHTML=`<div class="detail-card-head"><span class="tag ${h(ticket.category)}">${h(ticket.category)}</span><span class="tag">#${ticket.id} · ${h(ticket.status)}</span></div>
    <div class="detail-title">${h(ticket.subject)}</div><div class="detail-message" dir="auto">${h(ticket.message)}</div>
    ${ticket.ml_intent?`<p class="draft-provider">Optional BANKING77 ML intent: <strong>${h(ticket.ml_intent)}</strong> · confidence ${Math.round((ticket.ml_confidence||0)*100)}%</p>`:''}
    <div class="detail-actions"><button id="generate-btn" class="btn primary" type="button">✳ Generate AI draft</button></div>
    ${latest?`<div class="draft-header"><h3>Suggested reply</h3><span class="tag ${h(latest.status)}">${h(latest.status.replaceAll('_',' '))}</span></div>
      <textarea id="draft-text" class="draft-editor" rows="7" aria-label="Edit draft reply" ${latest.status==='pending_approval'?'':'disabled'} dir="auto">${h(latest.edited_body||latest.body)}</textarea>
      <div class="draft-provider">Source: <strong>${h(latest.provider.replaceAll('_',' '))}</strong>${latest.warning?`<span class="warning"> · ${h(latest.warning)}</span>`:''}</div>
      ${latest.status==='pending_approval'?`<div class="draft-buttons"><button id="approve-btn" class="btn approve" type="button">✓ Approve edited draft</button><button id="reject-btn" class="btn reject" type="button">✕ Reject</button></div>`:'<p class="draft-provider">Reviewed. This draft has not been sent to a customer.</p>'}
      <div class="source-list">Knowledge sources: ${latest.knowledge_sources.length?latest.knowledge_sources.map(id=>`<span class="source-pill">${h(id)}</span>`).join(''):'No relevant knowledge matched'}</div>`:'<p class="draft-provider">No AI drafts yet. Generate one to start human review.</p>'}`;
  $('generate-btn').addEventListener('click',()=>generateDraft(ticket.id));
  if(latest?.status==='pending_approval'){
    $('approve-btn').addEventListener('click',()=>reviewDraft(latest.id,'approve'));
    $('reject-btn').addEventListener('click',()=>reviewDraft(latest.id,'reject'));
  }
}
async function generateDraft(id){
  if(state.busy)return;state.busy=true;const btn=$('generate-btn');if(btn){btn.disabled=true;btn.textContent='Generating…';}
  try{const draft=await api(`/api/tickets/${id}/draft`,{method:'POST'});showToast(draft.provider==='gemini'?'Gemini draft generated — please review.':'Demo draft generated — please review.');await selectTicket(id);await refreshOverview();}
  catch(e){showToast(e.message,true);if(btn){btn.disabled=false;btn.textContent='✳ Generate AI draft';}}
  finally{state.busy=false;}
}
async function reviewDraft(id,decision){
  const edited=$('draft-text')?.value?.trim()||'';
  if(decision==='approve'&&!edited){showToast('Approved text cannot be empty.',true);return;}
  try{await api(`/api/drafts/${id}/review`,{method:'POST',body:JSON.stringify({decision,edited_text:decision==='approve'?edited:null})});showToast(decision==='approve'?'Draft approved (not sent).':'Draft rejected.');await refreshOverview();await selectTicket(state.selectedId);}
  catch(e){showToast(e.message,true);}
}
async function refreshOverview(){
  const [ticketData,metrics]=await Promise.all([api('/api/tickets'),api('/api/metrics')]);
  state.tickets=ticketData.tickets;renderTickets();
  $('metric-tickets').textContent=metrics.total_tickets;
  $('metric-pending').textContent=metrics.pending_drafts;
  $('metric-approved').textContent=metrics.approved_drafts;
  $('metric-knowledge').textContent=metrics.knowledge_articles;
  const cats=metrics.category_breakdown;const maximum=Math.max(...Object.values(cats),1);
  $('category-bars').innerHTML=Object.entries(cats).map(([cat,count])=>`<div class="category-row"><div class="category-heading"><span>${h(cat.charAt(0).toUpperCase()+cat.slice(1))}</span><strong>${count}</strong></div><div class="bar-track"><div class="bar-fill" style="width:${Math.round(count/maximum*100)}%"></div></div></div>`).join('');
}
async function init(){
  $('sample-btn').addEventListener('click',()=>{$('subject').value='Missing payment';$('message').value='My payment is missing. Can you help me check the transaction status?';});
  $('ticket-form').addEventListener('submit',async event=>{
    event.preventDefault();const btn=$('create-btn');btn.disabled=true;
    try{const ticket=await api('/api/tickets',{method:'POST',body:JSON.stringify({subject:$('subject').value,message:$('message').value})});$('ticket-form').reset();await refreshOverview();await selectTicket(ticket.id);showToast('Ticket created. Generate a draft to continue.');}
    catch(e){showToast(e.message,true);}finally{btn.disabled=false;}
  });
  try{
    const [health,knowledge]=await Promise.all([api('/api/health'),api('/api/knowledge')]);
    $('model-status').textContent=health.gemini_configured?'Gemini connected':'Template demo mode';
    $('knowledge-list').innerHTML=knowledge.documents.map(d=>`<div class="knowledge-row"><div class="knowledge-icon">◇</div><div><strong>${h(d.title)}</strong><p>${h(d.content)}</p></div></div>`).join('');
    await refreshOverview();
    if(state.tickets.length)await selectTicket(state.tickets[0].id);
  }catch(e){showToast(e.message,true);$('ticket-list').innerHTML='<p class="empty">Could not connect to the API.</p>';}
}
document.addEventListener('DOMContentLoaded',init);
