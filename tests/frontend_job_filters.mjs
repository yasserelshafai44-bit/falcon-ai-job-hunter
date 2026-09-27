import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

// Execute the actual UI filter and refresh-loader code with DOM controls.
const source=readFileSync(new URL('../frontend/app.js',import.meta.url),'utf8');
new vm.Script(source);
const controls={};
for(const id of ['minimumMatchScore','recommendationFilter','familyFilter','seniorityFilter','companyFilter','resultLocationFilter','workplaceFilter','directOnly','showRejects','clearJobFilters','jobFilterSummary','jobs']){
 controls[id]={value:'',checked:false,disabled:false,options:[{textContent:'All recommendations except Reject'}],listeners:{},addEventListener(event,fn){this.listeners[event]=fn}};
}
controls.minimumMatchScore.value='35';
controls.directOnly.checked=true;
controls.showRejects.checked=true;
const context=vm.createContext({$:id=>controls[id],URLSearchParams,liveEmployerEntries:[],escapeHtml:String,componentAssessment:()=>'',request:async()=>({items:[],total:0})});
vm.runInContext(source.slice(source.indexOf('let currentRankedJobs=[];'),source.indexOf('function setJobRefreshState')),context);
const run=code=>vm.runInContext(code,context);
run(`lastResolvedDirectProviders=new Set(['wsh_group_uk']);currentRankedJobs=['strong_apply','apply','review','weak_match','reject'].map((recommendation,id)=>({job:{id,provider:'wsh_group_uk',company:'Employer',title:'Role',location:'London',workplace_type:'on-site'},match:{id,career_fit_score:35,recommendation}}));currentRankedJobs.push({job:{provider:'wsh_group_uk'},match:{career_fit_score:34,recommendation:'apply'}});`);
assert.equal(run('applyJobFilters().ranked.length'),5,'35 is inclusive and rejects explicitly included');
run('renderRankedJobs()');
assert.equal(controls.recommendationFilter.options[0].textContent,'All recommendations including Reject','restored checkbox state must update label without a change event');
assert.match(controls.jobFilterSummary.textContent,/5 of 6/);
controls.showRejects.checked=false;
assert.equal(run('applyJobFilters().ranked.length'),4);
for(const rec of ['strong_apply','apply','review','weak_match','reject']){
 controls.recommendationFilter.value=rec;
 run('renderRankedJobs()');
 assert.equal(run('applyJobFilters().ranked.length'),1);
 assert.equal(controls.showRejects.disabled,true);
 assert.equal(controls.showRejects.checked,rec==='reject');
}
controls.recommendationFilter.value='';controls.showRejects.checked=true;
for(const id of ['familyFilter','seniorityFilter','companyFilter','resultLocationFilter'])controls[id].value='   ';
assert.equal(run('applyJobFilters().ranked.length'),5,'whitespace text filters are empty');
controls.workplaceFilter.value='remote';run('renderRankedJobs()');
assert.match(controls.jobs.innerHTML,/Workplace removed 5/);
controls.workplaceFilter.value='';
run("lastResolvedDirectProviders.clear()");run('renderRankedJobs()');
assert.match(controls.jobs.innerHTML,/Direct-employer only removed 5/);
controls.clearJobFilters.listeners.click();
assert.equal(run('applyJobFilters().ranked.length'),6,'Clear filters reveals entire ranked set');
assert.equal(controls.showRejects.disabled,false);
assert.equal(controls.recommendationFilter.options[0].textContent,'All recommendations including Reject');
let requests=[];
context.request=async path=>{requests.push(path);const page=Number(new URLSearchParams(path.split('?')[1]).get('page'));return {items:Array(page===1?100:9).fill({id:page}),total:109}};
assert.equal((await run("loadProviderJobs('wsh_group_uk')")).items.length,109);
assert.equal(requests.length,2);
assert.ok(requests.every(path=>!path.includes('recommendation')&&!path.includes('remote=')&&!path.includes('minimum')),'Best matches filtering remains client-side');
console.log('PASS: owner filter boundary, all recommendation enums, restored state, blanks, workplace/direct exclusions, zero-result explanation, clear filters, pagination, JavaScript syntax');
