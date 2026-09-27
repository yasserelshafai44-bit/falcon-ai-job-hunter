import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const js=readFileSync(new URL('../frontend/app.js',import.meta.url),'utf8');
const html=readFileSync(new URL('../frontend/index.html',import.meta.url),'utf8');
const controls=Object.fromEntries([...html.matchAll(/id="([^"]+)"/g)].map(([,id])=>[id,{value:'',checked:false,textContent:'',listeners:{},addEventListener(e,fn){this.listeners[e]=fn}}]));
let saved;
const context=vm.createContext({$:id=>{assert.ok(controls[id],`Missing real DOM element ${id}`);return controls[id]},currentRankedJobs:[],notice:()=>{},request:async(path,options)=>{
 assert.equal(path,'/preferences');if(options){saved=options.body;return saved}return saved;
}});
const lines=js.split('\n');
for(const prefix of ['const csv=', 'const triState=', 'const setTriState=', 'async function loadPreferences()']){
 const line=lines.find(l=>l.startsWith(prefix));assert.ok(line,prefix);vm.runInContext(line,context);
}
vm.runInContext(js.slice(js.indexOf("$('kentLondonPreset').addEventListener"),js.indexOf("$('preferencesForm').addEventListener")),context);
vm.runInContext(lines.find(l=>l.startsWith("$('preferencesForm').addEventListener")),context);
controls.kentLondonPreset.listeners.click();
await controls.preferencesForm.listeners.submit({preventDefault(){}});
assert.ok(saved,'preferences must actually save');
assert.equal(saved.home_location,'Royal Tunbridge Wells, Kent, UK');
assert.deepEqual([...saved.preferred_regions],['Kent']);
assert.equal(saved.anywhere_uk_acceptable,null);
controls.homeLocation.value='';controls.preferredRegions.value='';
await vm.runInContext('loadPreferences()',context);
assert.equal(controls.homeLocation.value,saved.home_location);
assert.equal(controls.preferredRegions.value,'Kent');
assert.equal(controls.hybridAcceptable.value,'true');
context.analysisId=1;
context.renderRankedJobs=()=>{};
context.request=async()=>({job:{id:5},match:{career_fit_score:95,location_fit:'good'},message:'Imported'});
vm.runInContext(lines.find(l=>l.startsWith('function locationFitLabel(')),context);
vm.runInContext(lines.find(l=>l.startsWith("$('manualJobForm').addEventListener")),context);
await controls.manualJobForm.listeners.submit({preventDefault(){}});
assert.match(controls.manualJobStatus.textContent,/Location fit: Suitable/);
console.log('Location preferences saved and reloaded through the actual form code');
