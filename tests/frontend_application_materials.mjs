import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source=readFileSync(new URL('../frontend/app.js',import.meta.url),'utf8');
new vm.Script(source);
const status={textContent:''};
const button={disabled:false,dataset:{id:'21'},closest:()=>({querySelector:()=>status})};
const calls=[];
let refreshed=0;
let notice='';
const context=vm.createContext({
  request:async(path,options)=>{calls.push({path,options});},
  loadApplications:async()=>{refreshed++;},
  notice:message=>{notice=message;},
  button,
});
vm.runInContext(source.slice(source.indexOf('async function regenerateMaterials(')),context);
await vm.runInContext('regenerateMaterials(button)',context);
assert.equal(calls.length,1);
assert.equal(calls[0].path,'/application-workflows/21/regenerate-materials');
assert.equal(calls[0].options.method,'POST');
assert.equal(refreshed,1);
assert.match(notice,/Review both before requesting approval/);
context.request=async()=>{throw new Error('Evidence unavailable');};
await vm.runInContext('regenerateMaterials(button)',context);
assert.equal(button.disabled,false);
assert.match(status.textContent,/Regeneration failed: Evidence unavailable/);
assert.equal(refreshed,1);
console.log('PASS: regeneration refreshes review, never approves/submits, and reports failure');
