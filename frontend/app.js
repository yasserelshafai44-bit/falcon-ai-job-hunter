const api='/api/v1';let token=localStorage.getItem('falcon_token')||'';let analysisId=null;let currentProfile=null;

const $=id=>document.getElementById(id);const notice=message=>{$('notice').textContent=message;setTimeout(()=>{if($('notice').textContent===message)$('notice').textContent=''},5000)};

async function request(path,options={}){const headers={...(options.headers||{})};if(token)headers.Authorization=`Bearer ${token}`;if(options.body&&!(options.body instanceof FormData)){headers['Content-Type']='application/json';options.body=JSON.stringify(options.body)}const response=await fetch(api+path,{...options,headers});const data=await response.json().catch(()=>({}));if(!response.ok){const message=typeof data.error?.message==='string'?data.error.message:typeof data.detail==='string'?data.detail:`Request failed (${response.status})`;if(response.status===401&&token){lock();throw new Error(`${message}. Please sign in again.`)}const error=new Error(message);error.status=response.status;throw error}return data}

function lock(){token='';analysisId=null;$('analysis').innerHTML='';$('profileSuggestions').innerHTML='';localStorage.removeItem('falcon_token');$('workspace').classList.add('locked');$('authCard').style.display='grid';$('session').textContent='Sign in required'}

function evidenceValue(item){return item?.value||''}

const csv=value=>value.split(',').map(item=>item.trim()).filter(Boolean);

const triState=value=>value===''?null:value==='true';

const setTriState=(id,value)=>{$(id).value=value===null||value===undefined?'':String(value)};

$('searchRadius').placeholder='Maximum commute distance (miles, optional)';

$('searchRadius').insertAdjacentHTML('afterend','<input id="maximumCommuteMinutes" type="number" min="0" max="600" placeholder="Maximum commute time (minutes, optional)">');

const sourceGroups=$('jobProvider').querySelectorAll('optgroup');

sourceGroups[0].insertAdjacentHTML('beforeend','<option value="hospitality">Hospitality &amp; Contract Catering</option>');

let liveDirectProviders=[];

let liveEmployerEntries=[];

function employerStatusLabel(status){return {LIVE:'Searchable now',AUTHORIZATION_REQUIRED:'Awaiting authorised source',MANUAL_ONLY:'Manual vacancy import only',UNAVAILABLE:'Currently unavailable'}[status]||status}

async function loadEmployerRegistry(){try{const employers=await request('/jobs/employers');liveEmployerEntries=employers.filter(item=>item.status==='LIVE'&&item.provider);liveDirectProviders=liveEmployerEntries.map(item=>item.provider);directEmployerProviders.clear();liveDirectProviders.forEach(provider=>directEmployerProviders.add(provider));sourceGroups[1].innerHTML=liveEmployerEntries.map(item=>`<option value="${escapeHtml(item.provider)}">${escapeHtml(item.employer)} Careers</option>`).join('');const rows=employers.map(item=>{const vacancies=item.status==='LIVE'&&item.live_vacancies!==null&&item.live_vacancies!==undefined?`${item.live_vacancies}${item.latest_refresh_status==='failed'?' (previously verified)':''}`:'—';const checked=item.last_checked_at?new Date(item.last_checked_at).toLocaleString():'Not checked';return `<tr><td><a href="${escapeHtml(item.careers_url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.employer)}</a><small>${escapeHtml(item.reason)}</small></td><td><span class="tag">${escapeHtml(item.status)}</span><small>${escapeHtml(employerStatusLabel(item.status))}</small><small>${escapeHtml(item.latest_refresh_error||(!item.latest_refresh_status&&item.status==='LIVE'?'Not yet refreshed':''))}</small></td><td>${escapeHtml(vacancies)}</td><td><time datetime="${escapeHtml(item.last_checked_at||'')}">${escapeHtml(checked)}</time></td></tr>`}).join('');$('employerRegistry').innerHTML=`<div class="coverage-table-wrap"><table class="coverage-table"><thead><tr><th>Employer</th><th>Search status</th><th>Live vacancies</th><th>Last checked</th></tr></thead><tbody>${rows}</tbody></table></div>`}catch(error){$('employerRegistry').innerHTML=`<div class="item error">Employer coverage unavailable: ${escapeHtml(error.message)}</div>`}}

async function loadPreferences(){try{const p=await request('/preferences');$('targetTitles').value=p.target_titles.join(', ');$('alternativeTitles').value=p.alternative_titles.join(', ');$('homeLocation').value=p.home_location||'';$('preferredLocations').value=p.preferred_locations.join(', ');$('preferredRegions').value=p.preferred_regions.join(', ');$('searchRadius').value=p.search_radius_miles??'';$('maximumCommuteMinutes').value=p.maximum_commute_minutes??'';$('workArrangements').value=p.work_arrangements.join(', ');setTriState('londonAcceptable',p.london_acceptable);setTriState('anywhereUkAcceptable',p.anywhere_uk_acceptable);setTriState('remoteAcceptable',p.remote_acceptable);setTriState('hybridAcceptable',p.hybrid_acceptable);setTriState('relocationAcceptable',p.relocation_acceptable);$('minimumSalary').value=p.minimum_salary||'';$('preferredIndustries').value=p.industries.join(', ');$('excludedIndustries').value=p.excluded_industries.join(', ');$('excludedCompanies').value=p.excluded_companies.join(', ');$('employmentTypes').value=p.employment_types.join(', ');$('willingTravel').checked=p.willing_to_travel;$('willingRelocate').checked=p.willing_to_relocate;$('locationPreferencesStatus').textContent='Saved preferences loaded. Career fit remains separate.'}catch(error){if(!error.message.includes('not found'))throw error;$('preferencesForm').reset();$('locationPreferencesStatus').textContent='No location preferences saved. Choose locations or use the Tunbridge Wells preset, then save.'}}

function analysisGroup(title,items){return `<section><h4>${escapeHtml(title)}</h4>${evidenceList(items||[])}</section>`}

function renderAnalysis(result){const a=result.analysis;const suggestions=[['full_name','Full name',a.full_name],['primary_location','Location',a.primary_location],['years_experience','Years experience',a.years_experience],['professional_summary','Professional summary',a.professional_summary_evidence],['seniority','Seniority',a.seniority],['role_family','Role family',a.role_family],['skills','Core skills',a.skills],['industries','Industries',a.industries],['leadership_scope','Leadership scope',a.leadership_scope],['certifications_qualifications','Qualifications',a.certifications_qualifications]].filter(([, ,value])=>Array.isArray(value)?value.length:value);$('profileSuggestions').innerHTML=suggestions.length?`<div class="suggestions"><h3>CV-derived suggestions</h3><p>Nothing changes until you select and accept it.</p>${suggestions.map(([field,label,value])=>`<label><input type="checkbox" name="profileSuggestion" value="${field}" checked> <b>${escapeHtml(label)}</b>: ${escapeHtml(Array.isArray(value)?value.map(evidenceValue).join(' · '):evidenceValue(value))}</label>`).join('')}<button id="applySuggestions" type="button">Apply selected suggestions</button></div>`:'';$('analysis').innerHTML=`${analysisGroup('Professional summary',a.professional_summary_evidence?[a.professional_summary_evidence]:[])}${analysisGroup('Role and seniority',[a.role_family,a.seniority].filter(Boolean))}${analysisGroup('Core skills',a.skills)}${analysisGroup('Industries',a.industries)}${analysisGroup('Leadership scope',a.leadership_scope)}${analysisGroup('Qualifications',a.certifications_qualifications)}<details><summary>Raw analysis / debug</summary><pre>${escapeHtml(JSON.stringify(a,null,2))}</pre></details>`}

async function loadProfile(){try{currentProfile=await request('/profile');$('fullName').value=currentProfile.full_name||'';$('location').value=currentProfile.location||'';$('years').value=currentProfile.years_experience||''}catch(error){if(!error.message.includes('not found'))throw error}}

async function restoreCandidateAnalysis(){const cvs=await request('/cvs');for(const cv of cvs){try{const result=await request(`/candidate-intelligence/cvs/${cv.id}`);analysisId=result.id;renderAnalysis(result);return}catch(error){if(error.status!==404)throw error}}$('analysis').textContent='No analysed CV found. Upload and analyse a CV first.'}

async function unlock(){if(!token)return lock();try{await request('/auth/me')}catch(error){notice(error.message);return}$('workspace').classList.remove('locked');$('authCard').style.display='none';$('session').textContent='Workspace active';const results=await Promise.allSettled([loadApplications(),loadProfile(),loadPreferences(),restoreCandidateAnalysis(),loadCalibration(),loadEmployerRegistry()]);const failed=results.find(result=>result.status==='rejected');if(failed)notice(failed.reason.message)}

$('authForm').addEventListener('submit',async e=>{e.preventDefault();try{const mode=e.submitter.value;const email=$('email').value;const password=$('password').value;if(mode==='local-reset-password'){const data=await request('/auth/local-reset-password',{method:'POST',body:{email,new_password:password}});notice(data.message);return}const data=await request(`/auth/${mode}`,{method:'POST',body:{email,password}});token=data.access_token;localStorage.setItem('falcon_token',token);await unlock();notice('Workspace ready')}catch(error){notice(error.message)}});

$('profileForm').addEventListener('submit',async e=>{e.preventDefault();try{currentProfile=await request('/profile',{method:'PUT',body:{full_name:$('fullName').value,email:currentProfile?.email||$('email').value,location:$('location').value||null,phone:currentProfile?.phone||null,years_experience:Number($('years').value||0),right_to_work_uk:currentProfile?.right_to_work_uk||false,full_uk_driving_licence:currentProfile?.full_uk_driving_licence||false,profile_data:currentProfile?.profile_data||{}}});notice('Candidate profile saved')}catch(error){notice(error.message)}});

$('cvForm').addEventListener('submit',async e=>{e.preventDefault();try{const form=new FormData();form.append('file',$('cv').files[0]);const cv=await request('/cvs',{method:'POST',body:form});const result=await request(`/candidate-intelligence/cvs/${cv.id}/analyze`,{method:'POST'});analysisId=result.id;renderAnalysis(result);notice('CV analysed locally')}catch(error){notice(error.message)}});

$('profileSuggestions').addEventListener('click',async event=>{if(event.target.id!=='applySuggestions')return;const fields=[...document.querySelectorAll('input[name="profileSuggestion"]:checked')].map(input=>input.value);try{currentProfile=await request(`/candidate-intelligence/${analysisId}/apply-profile`,{method:'POST',body:{fields}});await loadProfile();notice('Selected CV suggestions applied to your profile')}catch(error){notice(`Unable to apply suggestions: ${error.message}`)}});

$('kentLondonPreset').addEventListener('click',()=>{
 $('homeLocation').value='Royal Tunbridge Wells, Kent, UK';
 $('preferredLocations').value='London';$('preferredRegions').value='Kent';
 setTriState('londonAcceptable',true);setTriState('remoteAcceptable',true);
 setTriState('hybridAcceptable',true);setTriState('anywhereUkAcceptable',null);
 $('locationPreferencesStatus').textContent='Preset selected but not saved. Other locations remain unconfirmed. Save preferences to apply.';
});

$('preferencesForm').addEventListener('submit',async event=>{event.preventDefault();try{await request('/preferences',{method:'PUT',body:{target_titles:csv($('targetTitles').value),alternative_titles:csv($('alternativeTitles').value),home_location:$('homeLocation').value||null,preferred_locations:csv($('preferredLocations').value),preferred_regions:csv($('preferredRegions').value),search_radius_miles:Number($('searchRadius').value)||null,maximum_commute_minutes:Number($('maximumCommuteMinutes').value)||null,london_acceptable:triState($('londonAcceptable').value),anywhere_uk_acceptable:triState($('anywhereUkAcceptable').value),remote_acceptable:triState($('remoteAcceptable').value),hybrid_acceptable:triState($('hybridAcceptable').value),relocation_acceptable:triState($('relocationAcceptable').value),work_arrangements:csv($('workArrangements').value),minimum_salary:Number($('minimumSalary').value)||null,industries:csv($('preferredIndustries').value),excluded_industries:csv($('excludedIndustries').value),excluded_companies:csv($('excludedCompanies').value),employment_types:csv($('employmentTypes').value),willing_to_travel:$('willingTravel').checked,willing_to_relocate:$('willingRelocate').checked,currency:'GBP',requires_sponsorship:false}});$('locationPreferencesStatus').textContent='Preferences saved. Existing match locations updated; career-fit scores unchanged.';if(currentRankedJobs.length){const saved=await request('/matches');const byId=new Map(saved.items.map(m=>[m.id,m]));currentRankedJobs=currentRankedJobs.map(r=>({...r,match:byId.get(r.match.id)||r.match}));renderRankedJobs()}notice('Job-search preferences saved')}catch(error){notice(`Unable to save preferences: ${error.message}`)}});

let currentRankedJobs=[];

let lastResolvedDirectProviders=new Set();

async function loadProviderJobs(provider,signal){const items=[];let page=1;let batch;do{batch=await request(`/jobs?${new URLSearchParams({provider,page:String(page),page_size:'100'})}`,{signal});items.push(...batch.items);page++}while(batch.items.length&&items.length<batch.total);return{items}}

function selectedProviders(selection){if(selection==='all_verified_direct')return ['all_verified_direct'];const categories={qsr_restaurants:'QSR & Restaurants',hospitality:'Hospitality & Contract Catering',delivery_marketplace:'Delivery & Marketplace'};return categories[selection]?liveEmployerEntries.filter(item=>item.category===categories[selection]||selection==='hospitality'&&item.category.includes('Hospitality')).map(item=>item.provider):[selection]}

const directEmployerProviders=new Set();

const normal=value=>String(value??'').trim().toLowerCase();

function applyJobFilters(){const minScore=Number($('minimumMatchScore').value||0);const recommendation=$('recommendationFilter').value;const family=normal($('familyFilter').value);const seniority=normal($('seniorityFilter').value);const company=normal($('companyFilter').value);const location=normal($('resultLocationFilter').value);const workplace=$('workplaceFilter').value;const showRejects=$('showRejects').checked;const directOnly=$('directOnly').checked;const liveProviders=new Set([...liveEmployerEntries.filter(item=>item.status==='LIVE'&&item.provider).map(item=>item.provider),...lastResolvedDirectProviders]);let ranked=[...currentRankedJobs];const stages=[];const apply=(label,predicate)=>{const before=ranked.length;ranked=ranked.filter(predicate);const removed=before-ranked.length;if(removed)stages.push(`${label} removed ${removed}`)};apply(`Minimum career fit ${minScore}%`,({match})=>Number(match.career_fit_score)>=minScore);if(recommendation)apply('Recommendation',({match})=>match.recommendation===recommendation);else if(!showRejects)apply('Rejected-job setting',({match})=>match.recommendation!=='reject');if(family)apply('Occupational family',({match})=>normal(match.occupational_family).includes(family));if(seniority)apply('Seniority',({match})=>normal(match.seniority_assessment).includes(seniority));if(company)apply('Company',({job})=>normal(job.company).includes(company));if(location)apply('Location',({job})=>normal(job.location).includes(location));if(workplace)apply('Workplace',({job})=>job.workplace_type===workplace);if(directOnly)apply('Direct-employer only',({job})=>liveProviders.has(job.provider)||job.provider==='manual_official');return{ranked,stages,total:currentRankedJobs.length}}

function syncRecommendationControls(){const recommendation=$('recommendationFilter');const rejects=$('showRejects');if(recommendation.value)rejects.checked=recommendation.value==='reject';rejects.disabled=Boolean(recommendation.value);recommendation.options[0].textContent=rejects.checked?'All recommendations including Reject':'All recommendations except Reject'}

function locationFitLabel(value){return {good:'Suitable',outside_preference:'Unsuitable',unknown:'Unconfirmed'}[value]||'Unconfirmed'}
function renderRankedJobs(){syncRecommendationControls();const {ranked,stages,total}=applyJobFilters();$('jobFilterSummary').textContent=total?`${ranked.length} of ${total} ranked vacancies shown.${stages.length?' '+stages.join('; ')+'.':''}`:'';$('jobs').innerHTML=ranked.length?ranked.map(({job,match})=>{const salary=job.salary_min||job.salary_max?`${escapeHtml(job.currency||'')} ${job.salary_min||'?'}–${job.salary_max||'?'}`:'Salary not provided';const original=job.is_demo?'<span class="meta">Demo fixture — no original vacancy</span>':job.url?`<a href="${escapeHtml(job.url)}" target="_blank" rel="noopener noreferrer">View original vacancy</a>`:'<span class="meta">Original URL not supplied; verify against the pasted employer text.</span>';return `<div class="item"><span class="score">Career fit: ${match.career_fit_score}%</span><span class="tag">${job.is_demo?'DEMO':'REAL'} · ${escapeHtml(job.provider)}</span><h3>${escapeHtml(job.title)}</h3><div class="meta">${escapeHtml(job.company)} · ${escapeHtml(job.location||'Location not specified')} · ${escapeHtml(job.workplace_type||'Workplace not specified')}</div><div class="location-fit"><strong>Location fit: ${escapeHtml(locationFitLabel(match.location_fit))}</strong> · ${escapeHtml(match.location_fit_explanation||'Location has not been assessed')}</div><div class="meta">${escapeHtml(match.occupational_family||'unknown')} · ${escapeHtml(match.seniority_assessment||'unknown')} · ${salary}</div><details><summary>Full vacancy description and requirements</summary><p>${escapeHtml(job.description)}</p>${(job.requirements||[]).length?`<p><strong>Requirements:</strong> ${escapeHtml(job.requirements.join(', '))}</p>`:''}</details>${componentAssessment(match)}${original}<button class="prepare" data-job-id="${job.id}" data-match-id="${match.id}">Prepare</button><div class="prepare-status" aria-live="polite"></div></div>`}).join(''):`<div class="item">No vacancies satisfy the current Best matches filters.${stages.length?` ${escapeHtml(stages.join('; '))}.`:''} Use Clear filters to inspect the ranked set.</div>`}

['minimumMatchScore','recommendationFilter','familyFilter','seniorityFilter','companyFilter','resultLocationFilter','workplaceFilter','directOnly','showRejects'].forEach(id=>$(id).addEventListener('input',renderRankedJobs));

$('recommendationFilter').addEventListener('change',()=>{const recommendation=$('recommendationFilter').value;const rejects=$('showRejects');if(recommendation){rejects.checked=recommendation==='reject';rejects.disabled=true}else rejects.disabled=false;renderRankedJobs()});

$('showRejects').addEventListener('change',()=>{$('recommendationFilter').options[0].textContent=$('showRejects').checked?'All recommendations including Reject':'All recommendations except Reject';renderRankedJobs()});

$('clearJobFilters').addEventListener('click',()=>{$('minimumMatchScore').value=0;$('recommendationFilter').value='';$('familyFilter').value='';$('seniorityFilter').value='';$('companyFilter').value='';$('resultLocationFilter').value='';$('workplaceFilter').value='';$('directOnly').checked=false;$('showRejects').checked=true;$('showRejects').disabled=false;$('recommendationFilter').options[0].textContent='All recommendations except Reject';renderRankedJobs()});

const RANKING_TIMEOUT_MS=120000;
const newRankingController=()=>typeof AbortController==='function'?new AbortController():{signal:undefined,abort(){}};
function setJobRefreshState(message,{busy=false,error=false}={}){const button=$('refreshRankJobs');button.disabled=busy;button.textContent=busy?'Refreshing and ranking…':'Refresh and rank jobs';$('jobForm').setAttribute('aria-busy',String(busy));const status=$('jobRefreshStatus');status.className=error?'error-text':'';status.textContent=message}

$('jobForm').addEventListener('submit',async e=>{e.preventDefault();if(!analysisId){const message='No analysed CV is available. Upload and analyse a CV first.';$('jobs').innerHTML=`<div class="item error">${message}</div>`;setJobRefreshState(message,{error:true});return notice(message)}const selected=$('jobProvider').value;const providers=selectedProviders(selected);const keyword=$('keyword').value.trim();const location=$('jobLocation').value.trim();const controller=newRankingController();const timeout=setTimeout(()=>controller.abort(),RANKING_TIMEOUT_MS);setJobRefreshState('Contacting verified employers and ranking current vacancies…',{busy:true});$('jobs').innerHTML='<div class="item">Loading and ranking jobs…</div>';try{const sync=await request('/jobs/sync',{method:'POST',body:{keyword:keyword||null,location:location||null,providers,limit_per_provider:10000},signal:controller.signal});const refreshedProviders=sync.providers_requested||[];const failedProviders=Object.keys(sync.provider_errors||{});if(!refreshedProviders.length)throw new Error('No searchable provider was selected. Reload Employer coverage and try again.');const directSelection=selected==='all_verified_direct'||selected==='qsr_restaurants'||selected==='hospitality'||selected==='delivery_marketplace'||liveDirectProviders.includes(selected);lastResolvedDirectProviders=directSelection?new Set(refreshedProviders):new Set();setJobRefreshState(`Refresh complete. Loading vacancies from ${refreshedProviders.length} employer sources…`,{busy:true});const batches=await Promise.all(refreshedProviders.map(provider=>loadProviderJobs(provider,controller.signal)));const jobs=batches.flatMap(batch=>batch.items);if(!jobs.length){currentRankedJobs=[];renderRankedJobs();const suffix=failedProviders.length?` ${failedProviders.length} provider(s) failed: ${failedProviders.join(', ')}.`:'';const message=`No current vacancies were returned by the selected source(s).${suffix}`;setJobRefreshState(message);return notice(message)}const persisted=await request('/matches',{signal:controller.signal});const jobIds=new Set(jobs.map(job=>job.id));const matches=new Map(persisted.items.filter(match=>match.candidate_analysis_id===analysisId&&jobIds.has(match.job_id)).map(match=>[match.job_id,match]));const missing=jobs;for(let offset=0;offset<missing.length;offset+=10){setJobRefreshState(`Ranking ${Math.min(offset+10,missing.length)} of ${missing.length} genuine vacancies…`,{busy:true});const recovered=await Promise.allSettled(missing.slice(offset,offset+10).map(job=>request(`/matches/jobs/${job.id}/score`,{method:'POST',body:{candidate_analysis_id:analysisId},signal:controller.signal}).then(match=>({jobId:job.id,match}))));recovered.forEach(result=>{if(result.status==='fulfilled')matches.set(result.value.jobId,result.value.match)})}currentRankedJobs=jobs.filter(job=>matches.has(job.id)).map(job=>({job,match:matches.get(job.id)}));currentRankedJobs.sort((a,b)=>b.match.overall_score-a.match.overall_score);renderRankedJobs();await loadEmployerRegistry();const warning=failedProviders.length?` ${failedProviders.length} provider(s) failed: ${failedProviders.join(', ')}.`:'';const message=`${currentRankedJobs.length} current vacancies ranked from ${refreshedProviders.length} employer sources.${warning}`;setJobRefreshState(message,{error:failedProviders.length===refreshedProviders.length});notice(message)}catch(error){const timedOut=controller.signal?.aborted;const authExpired=error.message.includes('Please sign in again');const message=authExpired?'Your session expired. Please sign in again.':timedOut?'Ranking timed out after 2 minutes. Try a narrower employer selection or retry.':`Unable to refresh and rank jobs: ${error.message}`;$('jobs').innerHTML=`<div class="item error">${escapeHtml(message)}</div>`;setJobRefreshState(message,{error:true});notice(message)}finally{clearTimeout(timeout);$('refreshRankJobs').disabled=false;$('refreshRankJobs').textContent='Refresh and rank jobs';$('jobForm').setAttribute('aria-busy','false')}});

$('manualJobForm').addEventListener('submit',async event=>{event.preventDefault();const status=$('manualJobStatus');if(!analysisId){status.textContent='Analyse a CV before importing a vacancy.';return}status.textContent='Importing and ranking the employer text…';try{const result=await request('/jobs/manual',{method:'POST',body:{candidate_analysis_id:analysisId,source_url:$('manualJobUrl').value||null,employer:$('manualEmployer').value,title:$('manualTitle').value,location:$('manualLocation').value,description:$('manualDescription').value,workplace_type:$('manualWorkplace').value,requirements:$('manualRequirements').value.split('\n').map(value=>value.trim()).filter(Boolean)}});currentRankedJobs=[{job:result.job,match:result.match}];renderRankedJobs();status.textContent=`${result.message}. Career fit: ${result.match.career_fit_score}%. Location fit: ${locationFitLabel(result.match.location_fit)}.`;notice('Manual official vacancy imported and ranked; no application was submitted.')}catch(error){const message=`Vacancy was not imported: ${error.message}`;status.textContent=message;notice(message)}});



function sourceLabel(provider){return provider==='local'?'DEMO':'REAL'}

const recommendationLabels={strong_apply:'STRONG APPLY',apply:'APPLY',review:'CONSIDER',weak_match:'WEAK MATCH',reject:'DO NOT RECOMMEND'};

const dimensionLabels={role_family:'Role fit',seniority:'Seniority',responsibilities:'Responsibilities',industry:'Industry',leadership_scope:'Leadership scope',location:'Location',experience:'Experience',mandatory:'Mandatory requirements'};

function componentAssessment(match){return `<details class="match-assessment"><summary>Why this career fit · ${escapeHtml(recommendationLabels[match.recommendation]||match.recommendation)}</summary><dl>${(match.evidence||[]).filter(item=>item.dimension!=='location').map(item=>`<dt>${escapeHtml(dimensionLabels[item.dimension]||item.dimension)} — ${item.contribution}/${item.max_score} — ${escapeHtml(String(item.status).toUpperCase())}</dt><dd>${escapeHtml(item.explanation)}</dd>`).join('')}</dl><h5>Strongest career evidence</h5>${evidenceList(match.strengths)}<h5>Important career gaps</h5>${evidenceList([...(match.gaps||[]),...(match.mandatory_failures||[])])}<h5>Unknowns and uncertainties</h5>${evidenceList(match.uncertainty)}</details>`}

const humanLabels=['strong_match','good_match','adjacent','weak_match','reject'];

function summaryValue(value){return value&&value!=='NOT STATED'?escapeHtml(value):'<span class="not-stated">NOT STATED</span>'}

function summaryItems(items){return items?.length?`<ul>${items.map(item=>`<li>${escapeHtml(item)}</li>`).join('')}</ul>`:'<p class="not-stated">NOT STATED</p>'}

function calibrationCard(review){const job=review.vacancy_snapshot;const match=review.falcon_snapshot;const summary=review.human_review_summary;const options=['<option value="">Choose an independent human label…</option>',...humanLabels.map(label=>`<option value="${label}" ${review.human_label===label?'selected':''}>${label.replaceAll('_',' ').toUpperCase()}</option>`)].join('');const saved=review.reviewed?`<strong>Reviewed:</strong> ${escapeHtml(review.human_label.replaceAll('_',' ').toUpperCase())} · <strong>Reviewer:</strong> ${escapeHtml(review.reviewer_email)} · <time datetime="${escapeHtml(review.reviewed_at)}">${escapeHtml(new Date(review.reviewed_at).toLocaleString())}</time>`:'<strong>Independent review:</strong> Not yet reviewed';const falconComparison=review.reviewed?`<div class="falcon-comparison"><strong>Falcon comparison after review:</strong> ${match.score}% · ${escapeHtml(match.recommendation)}</div>`:'';return `<article class="item calibration-review" data-review-id="${review.id}"><h3>${escapeHtml(summary.title)}</h3><div class="meta">${escapeHtml(summary.employer)} · ${summaryValue(summary.location)} · ${summaryValue(summary.workplace_type)}</div><div class="reviewed-status" aria-live="polite">${saved}</div><section class="human-review-summary" aria-label="Human review summary"><h4>Human review summary</h4><p class="evidence-source">${escapeHtml(summary.source)}</p><dl><dt>Role purpose</dt><dd>${summaryItems(summary.role_purpose)}</dd><dt>Main responsibilities</dt><dd>${summaryItems(summary.main_responsibilities)}</dd><dt>Essential / mandatory requirements</dt><dd>${summaryItems(summary.mandatory_requirements)}</dd><dt>Leadership scope</dt><dd>${summaryItems(summary.leadership_scope)}</dd><dt>Experience / qualifications</dt><dd>${summaryItems(summary.experience_qualifications)}</dd><dt>Salary</dt><dd>${summaryValue(summary.salary)}</dd><dt>Practical constraints</dt><dd>${summaryItems(summary.practical_constraints)}</dd></dl></section><details><summary>Full vacancy — employer source text</summary><p>${escapeHtml(job.description)}</p>${evidenceList(job.requirements)}<a href="${escapeHtml(job.source_url)}" target="_blank" rel="noopener noreferrer">Open original vacancy</a></details>${falconComparison}<details class="falcon-assessment"><summary>Reveal Falcon assessment</summary><p><strong>${match.score}% · ${escapeHtml(match.recommendation)}</strong></p><div class="meta">${escapeHtml(match.occupational_family)} · ${escapeHtml(match.seniority_assessment)}</div>${evidenceList(match.evidence)}<h5>Gaps</h5>${evidenceList([...(match.gaps||[]),...(match.uncertainty||[])])}</details><form class="human-review-form"><label>Human label<select class="human-label" required>${options}</select></label><label>Reviewer notes<textarea class="review-notes" rows="5" placeholder="Record your independent assessment, supporting evidence, and reservations">${escapeHtml(review.reviewer_notes||'')}</textarea></label><div class="review-save-controls"><button class="save-calibration" type="submit">${review.reviewed?'Update':'Save'} human review</button><div class="review-action-status" role="status" aria-live="polite"></div></div></form></article>`}

async function loadCalibration(){const corpus=$('calibrationCorpus').value;try{const query=`?corpus_version=${encodeURIComponent(corpus)}`;const [reviews,metrics]=await Promise.all([request(`/calibration/reviews${query}`),request(`/calibration/evaluation${query}`)]);$('calibrationReviews').innerHTML=reviews.items.length?reviews.items.map(calibrationCard).join(''):'This validation set has not been created yet.';$('calibrationMetrics').textContent=`${reviews.reviewed}/${reviews.total} independently reviewed. Strong precision: ${metrics.strong_apply_precision??'not measurable'}; Apply precision: ${metrics.apply_precision??'not measurable'}; false-positive rate: ${metrics.false_positive_rate??'not measurable'}; false-negative rate: ${metrics.false_negative_rate??'not measurable'}.`}catch(error){$('calibrationReviews').textContent=`Calibration unavailable: ${error.message}`}}

$('buildValidationSample').addEventListener('click',async()=>{if(!analysisId)return notice('Analyse a CV first.');const button=$('buildValidationSample');button.disabled=true;try{await request('/calibration/validation-sample',{method:'POST',body:{candidate_analysis_id:analysisId,providers:liveDirectProviders,corpus_version:'beta-validation-v1',sample_size:12}});$('calibrationCorpus').value='beta-validation-v1';await loadCalibration();notice('12-job independent validation sample is ready.')}catch(error){notice(`Could not build validation sample: ${error.message}`)}finally{button.disabled=false}});

$('buildCorpus').addEventListener('click',async()=>{if(!analysisId)return notice('Analyse a CV first.');try{await request('/calibration/corpus',{method:'POST',body:{candidate_analysis_id:analysisId,providers:['deliveroo','kfc_uk'],corpus_version:'live-v1'}});$('calibrationCorpus').value='live-v1';await loadCalibration();notice('Versioned real-vacancy corpus updated; human labels were not inferred.')}catch(error){notice(error.message)}});

$('refreshCalibration').addEventListener('click',loadCalibration);

$('calibrationCorpus').addEventListener('change',loadCalibration);

$('calibrationReviews').addEventListener('submit',async event=>{const form=event.target.closest('.human-review-form');if(!form)return;event.preventDefault();const card=form.closest('.calibration-review');const label=form.querySelector('.human-label').value;const status=form.querySelector('.review-action-status');const button=form.querySelector('.save-calibration');if(!label){status.className='review-action-status error-text';status.textContent='Choose a human label before saving.';return notice('Choose a human label independently.')}button.disabled=true;status.className='review-action-status';status.textContent='Saving review…';try{const saved=await request(`/calibration/reviews/${card.dataset.reviewId}`,{method:'PUT',body:{human_label:label,reviewer_notes:form.querySelector('.review-notes').value||null}});card.outerHTML=calibrationCard(saved);await loadCalibration();notice(`Human review saved successfully for ${saved.vacancy_snapshot.title}.`)}catch(error){button.disabled=false;const message=`Review was not saved: ${error.message}. Check that you are signed in, then retry.`;status.className='review-action-status error-text';status.textContent=message;notice(message)}});

$('jobs').addEventListener('click',event=>{const button=event.target.closest('button.prepare');if(button)prepare(Number(button.dataset.jobId),Number(button.dataset.matchId),button)});

async function prepare(jobId,matchId,button){

  const status=button.parentElement.querySelector('.prepare-status');

  button.disabled=true;status.className='prepare-status';status.textContent='Preparing both application drafts…';

  try{

    const workflow=await request('/application-workflows/prepare',{method:'POST',body:{job_match_id:matchId}});

    await loadApplications(workflow.id);

    status.className='prepare-status success';status.textContent=`Application #${workflow.id} is ready to review below.`;

    document.querySelector(`[data-workflow-id="${workflow.id}"]`)?.scrollIntoView({behavior:'smooth',block:'start'});

    notice('Draft materials prepared for your review');

  }catch(error){const message=`Prepare failed: ${error.message}`;status.className='prepare-status error-text';status.textContent=message;notice(message)}

  finally{button.disabled=false}

}

const statusLabels={draft:'PREPARING',materials_ready:'READY FOR REVIEW',awaiting_approval:'READY FOR REVIEW — APPROVE APPLICATION',approved:'APPROVED',submitted:'SUBMITTED',withdrawn:'Withdrawn',rejected:'Rejected',interview:'Interview',offer:'Offer'};

function evidenceList(items){return items?.length?`<ul>${items.map(item=>`<li>${escapeHtml(typeof item==='string'?item:item.explanation||item.value||JSON.stringify(item))}</li>`).join('')}</ul>`:'<p>None identified.</p>'}

function uniqueReviewItems(...groups){const seen=new Set();return groups.flat().filter(item=>{const value=typeof item==='string'?item:item?.explanation||item?.value||JSON.stringify(item);const key=String(value).trim().toLowerCase();if(!key||seen.has(key))return false;seen.add(key);return true})}

function matchEvidenceItems(match){return uniqueReviewItems(match.strengths||[],match.evidence||[])}

function matchGapItems(match){return uniqueReviewItems(match.gaps||[],match.mandatory_failures||[],match.uncertainty||[])}

function originalEvidence(data){const groups=['skills','achievements','industries','leadership_scope'];return groups.map(key=>`<details><summary>${escapeHtml(key.replace('_',' '))}</summary>${evidenceList((data[key]||[]).map(item=>`${item.value}: ${item.source_text}`))}</details>`).join('')}

function safeEmployerUrl(value){try{const url=new URL(value);return ['http:','https:'].includes(url.protocol)?url.href:''}catch{return ''}}

function reviewCard(review,open=false){

  const w=review.workflow;const m=review.match;const editable=['materials_ready','awaiting_approval'].includes(w.status);

  const employerUrl=safeEmployerUrl(review.job.url);const questions=review.unanswered_employer_questions||[];

  return `<article class="item application-review" data-workflow-id="${w.id}">

    <span class="score">${m.overall_score}% match</span><h3>Application #${w.id} · ${escapeHtml(review.job.title)}</h3>

    <div class="company">${escapeHtml(review.job.company)}</div><div class="meta">${escapeHtml(review.job.location)}</div>

    <p class="workflow-state" role="status" aria-live="polite"><strong>${escapeHtml(statusLabels[w.status]||w.status)}</strong></p>

    <p><strong>Application route: ${escapeHtml(review.application_route?.method||'ASSISTED_APPLY')}</strong> — ${escapeHtml(review.application_route?.reason||'Employer site completion required.')}</p>

    ${w.status==='approved'?`<p><strong>${review.application_route?.method==='UNAVAILABLE'?'BLOCKED':'ASSISTED APPLY REQUIRED'}</strong></p>${employerUrl&&review.application_route?.method!=='UNAVAILABLE'?`<a class="continue-assisted button" data-id="${w.id}" href="${escapeHtml(employerUrl)}" target="_blank" rel="noopener noreferrer">Continue — Assisted Apply on employer site</a>`:''}<div class="application-assistant" data-assistant-for="${w.id}" aria-live="polite">${review.assisted_pack&&typeof assistedApplyCard==='function'?assistedApplyCard(review.assisted_pack):''}</div>`:''}

    <details class="review-details" ${open||editable?'open':''}><summary>Review application</summary>

      <section><h4>Vacancy</h4><p>${escapeHtml(review.job.description)}</p>${employerUrl?`<a href="${escapeHtml(employerUrl)}" target="_blank" rel="noopener noreferrer">View original vacancy</a>`:''}</section>

      <section><h4>Match assessment</h4>${componentAssessment(m)}<h5>Strengths and evidence</h5>${evidenceList(matchEvidenceItems(m))}<h5>Gaps and unsupported requirements</h5>${evidenceList(matchGapItems(m))}</section>

      <section class="source-evidence"><h4>Original CV evidence</h4><p>Extracted directly from your uploaded CV. Generated drafts below must remain consistent with this evidence.</p>${originalEvidence(review.original_cv_evidence)}</section>

      <section><h4>Tailored résumé <small>Draft for human review</small></h4><details><summary>Changes from original CV</summary>${evidenceList(review.resume.change_summary)}</details>

        <textarea class="document-content" data-document-id="${review.resume.id}" aria-label="Tailored resume" ${editable?'':'readonly'}>${escapeHtml(review.resume.content)}</textarea>

        ${editable?`<button class="save-document" data-document-id="${review.resume.id}">Save résumé revision</button>`:''}</section>

      <section><h4>Cover letter / application statement <small>Draft for human review</small></h4><details><summary>Generated content not present verbatim in original CV</summary>${evidenceList(review.cover_letter.change_summary)}</details>

        <textarea class="document-content" data-document-id="${review.cover_letter.id}" aria-label="Cover letter" ${editable?'':'readonly'}>${escapeHtml(review.cover_letter.content)}</textarea>

        ${editable?`<button class="save-document" data-document-id="${review.cover_letter.id}">Save cover-letter revision</button>`:''}</section>

      <section><h4>Employer questions</h4><p>${escapeHtml(review.employer_questions_note||(questions.length?'Known employer questions require answers on the employer site.':'Employer questions: not yet checked.'))}</p>${questions.length?evidenceList(questions):''}${employerUrl?`<a href="${escapeHtml(employerUrl)}" target="_blank" rel="noopener noreferrer">Review questions on employer site</a>`:''}</section>

    </details>

      <div class="review-actions">

        ${['draft','materials_ready'].includes(w.status)?`<details><summary>Replace draft materials</summary><button class="regenerate-materials" data-id="${w.id}">Regenerate drafts for fresh review</button></details>`:''}

        ${editable?`<p>By pressing Approve, I confirm I reviewed these CV and cover-letter materials. This does not authorise or perform external submission.</p><button class="workflow-approve" data-id="${w.id}">APPROVE APPLICATION</button>`:''}

        <span class="action-status" role="status" aria-live="polite"></span>

      </div>

  </article>`;

}

async function loadApplications(focusId=null){

  const openIds=new Set([...document.querySelectorAll('.application-review')].filter(card=>card.querySelector('.review-details')?.open).map(card=>Number(card.dataset.workflowId)));

  if(focusId)openIds.add(Number(focusId));

  const unsaved=new Map([...document.querySelectorAll('.document-content')].filter(field=>field.value!==field.defaultValue).map(field=>[field.dataset.documentId,field.value]));

  try{

    const data=await request('/application-workflows');

    if(!data.items.length){$('applications').innerHTML='No applications prepared.';return}

    const reviews=await Promise.all(data.items.map(async workflow=>{try{const review=await request(`/application-workflows/${workflow.id}/review`);if(workflow.status==='approved'){review.assisted_pack=await request(`/application-assistant/applications/${workflow.id}/assisted`)}return review}catch(error){return{workflow,error:error.message}}}));

    $('applications').innerHTML=reviews.map(result=>result.error?`<div class="item error" data-workflow-id="${result.workflow.id}"><h3>Application #${result.workflow.id}</h3><p>Review unavailable: ${escapeHtml(result.error)}</p><button class="repair-materials" data-id="${result.workflow.id}">Prepare missing drafts</button><span class="action-status" role="status"></span></div>`:reviewCard(result,openIds.has(result.workflow.id))).join('');

    document.querySelectorAll('.document-content').forEach(field=>{if(unsaved.has(field.dataset.documentId))field.value=unsaved.get(field.dataset.documentId)});

  }catch(error){if(token){$('applications').innerHTML=`<div class="item error">Unable to load applications: ${escapeHtml(error.message)}</div>`;notice(error.message)}throw error}

}

$('applications').addEventListener('click',event=>{

  const regenerate=event.target.closest('button.regenerate-materials,button.repair-materials');if(regenerate)return regenerateMaterials(regenerate);

  const action=event.target.closest('button.workflow-action');if(action)return advance(Number(action.dataset.id),action.dataset.action,action);

  const approval=event.target.closest('button.workflow-approve');if(approval)return approve(Number(approval.dataset.id),approval);

  const reviewed=event.target.closest('button.mark-reviewed');if(reviewed)return markReviewed(Number(reviewed.dataset.id),reviewed);

  const save=event.target.closest('button.save-document');if(save)return saveDocument(save);

});

function hasUnsavedDrafts(button){return [...button.closest('[data-workflow-id]').querySelectorAll('.document-content')].some(field=>field.value!==field.defaultValue)}

async function workflowAction(id,action,button,message,body){

  const status=button.closest('[data-workflow-id]').querySelector('.action-status');

  if(hasUnsavedDrafts(button)){status.textContent='Save your draft revisions before continuing.';return}

  button.disabled=true;status.textContent=message;

  try{const result=await request(`/application-workflows/${id}/${action}`,{method:'POST',...(body?{body}:{})});

    status.textContent=statusLabels[result.status]||result.status;await loadApplications(id);notice(statusLabels[result.status]||result.status);

  }catch(error){status.textContent=`Action failed: ${error.message}`;notice(status.textContent)}finally{button.disabled=false}

}

async function markReviewed(id,button){return workflowAction(id,'reviewed',button,'Recording your review…')}

async function advance(id,action,button){return workflowAction(id,action,button,'Requesting approval…')}

async function approve(id,button){return workflowAction(id,'approve-materials',button,'Recording your approval...',{explicit_review_and_approval:true})}
async function saveDocument(button){

  const card=button.closest('.application-review');const textarea=card.querySelector(`textarea[data-document-id="${button.dataset.documentId}"]`);const status=card.querySelector('.action-status');

  button.disabled=true;status.textContent='Saving revision…';

  try{await request(`/generation/${button.dataset.documentId}`,{method:'PATCH',body:{content:textarea.value}});textarea.defaultValue=textarea.value;await loadApplications(Number(card.dataset.workflowId));notice('Draft saved. Review it again before requesting approval.')}

  catch(error){status.textContent=`Save failed: ${error.message}`;notice(status.textContent)}finally{button.disabled=false}

}

function escapeHtml(value){return String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}unlock();



async function regenerateMaterials(button){button.disabled=true;const status=button.closest('[data-workflow-id]').querySelector('.action-status');status.textContent='Generating drafts from your saved CV and this vacancy…';try{await request(`/application-workflows/${Number(button.dataset.id)}/regenerate-materials`,{method:'POST'});await loadApplications(Number(button.dataset.id));notice('New drafts are ready. Review both before requesting approval.')}catch(error){status.textContent=`Regeneration failed: ${error.message}`;button.disabled=false}}
