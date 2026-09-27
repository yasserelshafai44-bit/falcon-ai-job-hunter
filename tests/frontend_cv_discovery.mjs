import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source=readFileSync(new URL('../frontend/app.js',import.meta.url),'utf8');
const controls=new Map();
const control=id=>{
  if(!controls.has(id))controls.set(id,{value:'',textContent:'',innerHTML:'',style:{},
    files:[new Blob(['Operations manager'])],classList:{add(){},remove(){}},
    listeners:{},addEventListener(event,fn){this.listeners[event]=fn},setAttribute(){}});
  return controls.get(id);
};
const calls=[];
const analysis={id:37,cv_document_id:12,analysis:{skills:[{value:'Team leadership'}]}};
let rejectApplications;
let persisted=false;
const background=new Promise((resolve,reject)=>{rejectApplications=reject});
const context=vm.createContext({
  $:control,FormData,URLSearchParams,
  localStorage:{getItem:()=> 'authenticated-user-token',removeItem(){}},
  notice:()=>{},setTimeout:()=>{},escapeHtml:String,evidenceList:items=>JSON.stringify(items),
  loadApplications:()=>background,loadProfile:async()=>{},loadPreferences:async()=>{},
  loadCalibration:async()=>{},loadEmployerRegistry:async()=>{},
  selectedProviders:()=>['local'],setJobRefreshState:()=>{},
  liveDirectProviders:[],renderRankedJobs:()=>{},
  loadProviderJobs:async()=>({items:[{id:91}]}),
  fetch:async(url,options={})=>{
    calls.push({url,options});
    if(url==='/api/v1/auth/me')return {ok:true,json:async()=>({id:8})};
    if(url==='/api/v1/cvs'&&options.method==='POST')return {ok:true,json:async()=>({id:12})};
    if(url==='/api/v1/cvs')return {ok:true,json:async()=>persisted?[{id:12}]:[]};
    if(url==='/api/v1/candidate-intelligence/cvs/12/analyze')persisted=true;
    if(url.startsWith('/api/v1/candidate-intelligence/'))return {ok:true,json:async()=>analysis};
    if(url==='/api/v1/jobs/sync')return {ok:true,json:async()=>({providers_requested:['local']})};
    if(url==='/api/v1/matches/jobs/91/score')return {ok:true,json:async()=>({job_id:91,candidate_analysis_id:37,overall_score:80})};
    if(url==='/api/v1/matches')return {ok:true,json:async()=>({items:[{job_id:91,candidate_analysis_id:37,overall_score:80}]})};
    throw new Error(`Unexpected API request ${url}`);
  },
});
const prefixes=["const api=",'async function request(', 'function lock(',
  'function evidenceValue(', 'function analysisGroup(', 'function renderAnalysis(',
  'async function restoreCandidateAnalysis(', 'async function unlock(',
  "$('cvForm').addEventListener(","$('jobForm').addEventListener(",
  'let currentRankedJobs=', 'let lastResolvedDirectProviders='];
vm.runInContext(source.split('\n').filter(line=>prefixes.some(p=>line.startsWith(p))).join('\n'),context);
const run=code=>vm.runInContext(code,context);

// Workspace loads run concurrently; upload completes before a background 503.
const opening=run('unlock()');
await new Promise(resolve=>setImmediate(resolve));
await control('cvForm').listeners.submit({preventDefault(){}});
assert.match(control('analysis').innerHTML,/Team leadership/);
assert.equal(run('analysisId'),37);
rejectApplications(new Error('Application history temporarily unavailable'));
await opening;
assert.equal(run('analysisId'),37,'A background API failure must not erase a persisted CV selection');
assert.equal(run('token'),'authenticated-user-token','Non-authentication errors must not sign out the user');
await control('jobForm').listeners.submit({preventDefault(){}});
const sync=calls.find(c=>c.url==='/api/v1/jobs/sync');
assert.ok(sync,'Discover & Rank must reach the backend after displaying an analysed CV');
const scored=calls.find(c=>c.url==='/api/v1/matches/jobs/91/score');
assert.ok(scored);
assert.equal(JSON.parse(scored.options.body).candidate_analysis_id,37);
assert.equal(sync.options.headers.Authorization,'Bearer authenticated-user-token');
assert.equal(run('currentRankedJobs.length'),1);

// Reload restores the database analysis, without relying on the original file.
run('analysisId=null');
await run('restoreCandidateAnalysis()');
assert.equal(run('analysisId'),37);
run('lock()');
assert.equal(run('analysisId'),null);
assert.equal(control('analysis').innerHTML,'','Signing out must clear stale candidate intelligence');

// A database/API error is not equivalent to an absent CV analysis.
run("token='authenticated-user-token'");
context.fetch=async url=>url==='/api/v1/cvs'
  ? {ok:true,json:async()=>[{id:12}]}
  : {ok:false,status:503,json:async()=>({error:{message:'Database unavailable'}})};
await assert.rejects(run('restoreCandidateAnalysis()'),/Database unavailable/);
assert.equal(run('token'),'authenticated-user-token');

// Real authentication failures still invalidate the session and clear its UI.
context.fetch=async()=>({ok:false,status:401,json:async()=>({error:{message:'Invalid token'}})});
await assert.rejects(run("request('/auth/me')"),/Please sign in again/);
assert.equal(run('token'),'');
assert.equal(run('analysisId'),null);
console.log('CV upload, background failure, discovery, restoration and sign-out passed');
