import assert from 'node:assert/strict';

import {readFileSync} from 'node:fs';

import vm from 'node:vm';



const source=readFileSync(new URL('../frontend/app.js',import.meta.url),'utf8');

new vm.Script(source);

const status={textContent:''};

const fields=[{value:'Saved CV',defaultValue:'Saved CV',dataset:{documentId:'1'}}];

const card={dataset:{workflowId:'21'},querySelector:selector=>selector==='.action-status'?status:{open:true},querySelectorAll:()=>fields};

const button={disabled:false,closest:()=>card,dataset:{id:'21'},parentElement:{querySelector:()=>status}};

const applications={innerHTML:'',addEventListener(){}};

const workflow={id:21,status:'materials_ready',reviewed_at:null};

const review={workflow,job:{title:'Area Leader',company:'Stored Employer',location:'London',description:'Stored vacancy responsibilities',url:'https://employer.example/apply'},match:{overall_score:95},original_cv_evidence:{},resume:{id:1,content:'Verified CV <evidence>',change_summary:[]},cover_letter:{id:2,content:'Verified cover letter',change_summary:[]},unanswered_employer_questions:['Can you work in this location?']};

const calls=[];

let fail=false;

const context=vm.createContext({

  URL,token:'test',unlock(){},notice(){},componentAssessment:()=>'',

  $:()=>applications,

  document:{querySelectorAll:selector=>selector==='.application-review'?[card]:fields,querySelector:()=>({scrollIntoView(){}})},

  request:async(path,options={})=>{

    calls.push({path,options});if(fail)throw new Error('Approval service unavailable');

    if(options.method==='POST'){

      if(path.endsWith('/reviewed'))workflow.reviewed_at='2026-01-01';

      if(path.endsWith('/request-approval'))workflow.status='awaiting_approval';

      if(path.endsWith('/approve-materials'))workflow.status='approved';

      return workflow;

    }

    return path.endsWith('/review')?review:{items:[workflow]};

  },button,

});

vm.runInContext(source.slice(source.indexOf('const statusLabels=')),context);

await vm.runInContext('markReviewed(21,button)',context);

assert.match(applications.innerHTML,/APPROVE APPLICATION/);

await vm.runInContext("advance(21,'request-approval',button)",context);

assert.match(applications.innerHTML,/READY FOR REVIEW/);

assert.match(applications.innerHTML,/>APPROVE APPLICATION<\/button>/);

assert.match(applications.innerHTML,/<details class="review-details" open>/);

assert.match(applications.innerHTML,/Verified CV &lt;evidence&gt;/);

assert.match(applications.innerHTML,/Stored vacancy responsibilities/);

assert.match(applications.innerHTML,/Can you work in this location/);

assert.doesNotMatch(applications.innerHTML,/class="button continue-employer"/);

await vm.runInContext('approve(21,button)',context);

assert.match(applications.innerHTML,/APPROVED/);

assert.match(applications.innerHTML,/class="continue-assisted button"/);

assert.match(applications.innerHTML,/href="https:\/\/employer.example\/apply"/);

assert.equal(calls.filter(call=>call.path.endsWith('/submitted')).length,0);

assert.equal(vm.runInContext("safeEmployerUrl('javascript:alert(1)')",context),'');

const before=calls.length;

fields[0].value='Unsaved edit';

await vm.runInContext('approve(21,button)',context);

assert.equal(calls.length,before);

assert.match(status.textContent,/Save your draft revisions/);

fields[0].value=fields[0].defaultValue;

fail=true;

await vm.runInContext("advance(21,'request-approval',button)",context);

assert.match(status.textContent,/Action failed: Approval service unavailable/);

assert.equal(button.disabled,false);

fail=false;

vm.runInContext(source.slice(source.indexOf('async function prepare('),source.indexOf('const statusLabels=')),context);

await vm.runInContext('prepare(99,77,button)',context);

const prepareCall=calls.find(call=>call.path==='/application-workflows/prepare');

assert.equal(prepareCall.options.body.job_match_id,77);

assert.equal('candidate_analysis_id' in prepareCall.options.body,false);

assert.equal(calls.filter(call=>call.path.endsWith('/resume/generate')).length,0);

console.log('PASS: Prepare uses match; review stays open; approval is visible, explicit, and separate from submission; unsaved edits are protected');



if(process.argv[2]){

  const actual=JSON.parse(readFileSync(process.argv[2],'utf8'));

  for(const [state,payload] of Object.entries(actual)){

    context.actualReview=payload;

    const html=vm.runInContext('reviewCard(actualReview)',context);

    assert.match(html,/Application #21/);

    assert.match(html,/Employer questions require review on employer site/);

    assert.doesNotMatch(html,/Unanswered employer questions|Regenerate drafts/);

    if(state==='awaiting_approval'){

      assert.match(html,/>APPROVE APPLICATION<\/button>/);

      assert.ok(html.indexOf('class="review-actions"')>html.lastIndexOf('</details>'));

    }else{

      assert.match(html,/APPROVED/);

      assert.match(html,/Continue — Assisted Apply/);

      assert.match(html,/jobs.smartrecruiters.com\/RaisingCanes\/744000140850342/);

    }

  }

  console.log('PASS: actual #21 API payloads render visible approval and official employer handoff');

}
