// Assisted Apply never launches or controls an employer browser.
function copyField(label,value){
  return `<div class="assisted-field"><b>${escapeHtml(label)}</b><textarea readonly aria-label="${escapeHtml(label)}">${escapeHtml(value||'')}</textarea>${value?'<button type="button" class="copy-assisted">Copy</button>':'<span>NEEDS USER INPUT — only if the employer asks</span>'}</div>`;
}
function assistedApplyCard(pack){
  const id=pack.workflow_id;
  return `<section class="assisted-pack"><h4>${escapeHtml(pack.status)}</h4><p>${escapeHtml(pack.message)}</p><p>${escapeHtml(pack.route.reason)}</p>
    <p>Materials approved. Nothing has been submitted. Review the completed employer form yourself before its final Submit action.</p>
    <button class="download-approved-resume" data-id="${id}">Download tailored CV (.docx)</button>
    <button class="download-cover-letter" data-id="${id}">Download cover letter (.txt)</button>
    ${pack.route.official_url?`<a class="button continue-employer" href="${escapeHtml(safeEmployerUrl(pack.route.official_url))}" target="_blank" rel="noopener noreferrer">Open official employer application</a>`:''}
    ${copyField('Cover letter / application statement',pack.cover_letter)}
    <h5>Reusable application details</h5><button class="copy-all-assisted">Copy all known details</button><div class="reusable-fields">${pack.fields.map(f=>copyField(f.label,f.value)).join('')}
    <h5>Work history</h5>${pack.work_history.map((row,i)=>copyField(`Employment ${i+1}`,row.source_text)).join('')}
    <h5>Education</h5>${pack.education.map((row,i)=>copyField(`Education ${i+1}`,row.source_text||row.description)).join('')}</div>
    <form class="save-application-fact" data-id="${id}"><label>Save or correct a reusable detail once <select name="field">${pack.fields.map(f=>`<option value="${escapeHtml(f.key)}">${escapeHtml(f.label)}${f.status==='NEEDS USER INPUT'?' — NEEDS USER INPUT':''}</option>`).join('')}</select></label><label>Your confirmed answer <input name="value" required maxlength="2000"></label><button>Save for future applications</button></form>
    <h5>Employer questions</h5><p>${escapeHtml(pack.questions_note)}</p>${pack.questions.length?evidenceList(pack.questions):'<p>No questions retrieved. This does not mean none are required.</p>'}
    <h5>What still needs you</h5>${evidenceList(pack.human_actions)}<p>Not stored — only needed if the employer requests them: ${escapeHtml(pack.missing_fields.join(', ')||'None')}.</p>
    <span class="assisted-status" role="status"></span></section>`;
}
async function assistedDownload(id,kind){
  const response=await fetch(`${api}/application-assistant/applications/${id}/${kind}`,{headers:{Authorization:`Bearer ${token}`}});
  if(!response.ok)throw new Error(`Download failed (${response.status})`);
  const url=URL.createObjectURL(await response.blob());const link=document.createElement('a');link.href=url;link.download=`Falcon-application-${id}-${kind}`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function copyAssistedText(text,area){
  try{await navigator.clipboard.writeText(text);notice('Copied')}catch{
    const field=document.createElement('textarea');field.value=text;field.readOnly=true;field.setAttribute('aria-label','Text ready to copy');area.appendChild(field);field.focus();field.select();notice('Clipboard unavailable. The text is selected; press Ctrl+C.');
  }
}
document.getElementById('applications').addEventListener('click',async event=>{
  const link=event.target.closest('a.continue-assisted');
  if(link){try{await request(`/application-assistant/applications/${link.dataset.id}/continue`,{method:'POST'})}catch(error){notice(error.message)}return;}
  const button=event.target.closest('button');if(!button)return;
  const card=button.closest('.application-review');if(!card)return;
  try{
    if(button.matches('.download-approved-resume'))return await assistedDownload(button.dataset.id,'resume.docx');
    if(button.matches('.download-cover-letter'))return await assistedDownload(button.dataset.id,'cover-letter.txt');
    if(button.matches('.copy-assisted'))return await copyAssistedText(button.parentElement.querySelector('textarea').value,button.parentElement);
    if(button.matches('.copy-all-assisted')){
      const area=card.querySelector('.reusable-fields');const text=[...area.querySelectorAll('.assisted-field')].map(f=>{const value=f.querySelector('textarea').value;return value?`${f.querySelector('b').textContent}:\n${value}`:''}).filter(Boolean).join('\n\n');return await copyAssistedText(text,area);
    }
    if(button.matches('.continue-assisted,.start-application-assistant')){
      button.disabled=true;const pack=await request(`/application-assistant/applications/${button.dataset.id}/continue`,{method:'POST'});
      card.querySelector('.application-assistant').innerHTML=assistedApplyCard(pack);
      card.querySelector('.assisted-pack')?.scrollIntoView({behavior:'smooth',block:'start'});
    }
  }catch(error){notice(error.message);const status=card.querySelector('.action-status');if(status)status.textContent=error.message}finally{button.disabled=false}
});
document.getElementById('applications').addEventListener('submit',async event=>{
  const form=event.target.closest('.save-application-fact');if(!form)return;event.preventDefault();const button=form.querySelector('button');button.disabled=true;
  try{
    await request('/application-assistant/profile/fact',{method:'PUT',body:{field:form.elements.field.value,value:form.elements.value.value}});
    const pack=await request(`/application-assistant/applications/${form.dataset.id}/assisted`);
    form.closest('.application-assistant').innerHTML=assistedApplyCard(pack);notice('Saved once for future applications');
  }catch(error){notice(error.message)}finally{button.disabled=false}
});
