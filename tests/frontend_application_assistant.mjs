import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source=readFileSync(new URL('../frontend/application-assistant.js',import.meta.url),'utf8');
const handlers={};const clipboard=[];const downloads=[];
const context=vm.createContext({
  document:{getElementById:()=>({addEventListener:(name,fn)=>handlers[name]=fn}),createElement:()=>({click(){downloads.push(this.download)}})},
  escapeHtml:value=>String(value).replaceAll('<','&lt;').replaceAll('"','&quot;'),evidenceList:items=>items.join(' | '),safeEmployerUrl:value=>value,
  navigator:{clipboard:{writeText:async text=>clipboard.push(text)}},notice(){},api:'/api/v1',token:'test',
  URL:{createObjectURL:()=> 'blob:fixture',revokeObjectURL(){}},setTimeout:fn=>fn(),fetch:async()=>({ok:true,blob:async()=>({})}),
});
vm.runInContext(source,context);
context.pack=process.argv[2]?JSON.parse(readFileSync(process.argv[2],'utf8')):{
  workflow_id:21,status:'ASSISTED APPLY REQUIRED',message:'Prepared — employer site completion required',
  route:{official_url:'https://jobs.smartrecruiters.com/RaisingCanes/123',reason:'SmartRecruiters browser automation disabled'},
  fields:[{key:'application_surname',label:'Legal/application surname',value:'Eldossary',status:'KNOWN'},{key:'notice_period',label:'Notice period',value:null,status:'NEEDS USER INPUT'}],
  cover_letter:'Verified letter <safe>',work_history:[{source_text:'Manager — Employer | Jan 2020 – Present'}],education:[{description:'Verified education'}],
  questions:[],questions_note:'Employer questions: not yet checked.',missing_fields:['Notice period'],human_actions:['Review and submit yourself only when approved'],
};
const html=vm.runInContext('assistedApplyCard(pack)',context);
assert.match(html,/ASSISTED APPLY REQUIRED/);assert.match(html,/Eldossary/);
assert.match(html,/Download tailored CV/);assert.match(html,/Download cover letter/);
assert.match(html,/Copy all known details/);assert.match(html,/NEEDS USER INPUT/);
assert.match(html,/Open official employer application/);
assert.doesNotMatch(source,/prepare-local|refresh-local|window.open|submit-dry-run/);
assert.doesNotMatch(html,/Prepare application form — dry run|Unanswered employer questions/);
await vm.runInContext("copyAssistedText('Known factual answer',{})",context);
assert.deepEqual(clipboard,['Known factual answer']);
await vm.runInContext("assistedDownload(21,'resume.docx')",context);
assert.deepEqual(downloads,['Falcon-application-21-resume.docx']);
console.log('PASS: Assisted Apply route, copy, download, missing fields and no browser automation controls');
