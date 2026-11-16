// Editor state only: the hold ends without this client asking (term expired, another client took over).
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../web/editor-state.js',import.meta.url),'utf8');
const {InboxEditor}=await import('data:text/javascript,'+encodeURIComponent(source));
const token={v:1,version:'source-A',edit_version:0,held:false,holder:null,manual_followup:false};
const held=(e)=>{
  e.hold('hold');
  const t={...token,edit_version:1,held:true,holder:'web-tab'};
  assert.equal(e.receive({kind:'draft_state',id:'source',rid:'hold',inbox:t}),true);return t;
};
const make=()=>new InboxEditor({id:'source',post:'p42',inbox:token},'web-tab','Typed and kept');

// the term ended: nobody holds, the text stays, the next edit needs a hold again
{
  const e=make(),t=held(e);
  const expired={...t,edit_version:2,held:false,holder:null};
  assert.equal(e.receive({kind:'draft_state',id:'source',rid:'expired:2:source',reason:'expired',inbox:expired}),true);
  assert.equal(e.token.held,false);assert.equal(e.needsHold,true);assert.equal(e.text,'Typed and kept');
  assert.throws(()=>e.send('r1','Typed and kept'),/Confirm this editor/);
  assert.doesNotThrow(()=>e.hold('again'));       // a fresh hold is possible
}
// another client took it over after the term ended: the field is no longer ours; it can take over explicitly
{
  const e=make(),t=held(e);
  assert.equal(e.receive({kind:'draft_state',id:'source',rid:'phone-take',inbox:{...t,edit_version:3,holder:'phone-1'}}),true);
  assert.equal(e.needsHold,true);assert.equal(e.canTakeover(),true);assert.equal(e.text,'Typed and kept');
}
// what must NOT count: an older token, another conversation version, another item, a plain unrelated state
{
  const e=make(),t=held(e);
  assert.equal(e.receive({kind:'draft_state',id:'source',rid:'expired:1:source',reason:'expired',inbox:{...t,edit_version:1,held:false,holder:null}}),false);
  assert.equal(e.receive({kind:'draft_state',id:'source',rid:'expired:5:source',reason:'expired',inbox:{...t,version:'source-B',edit_version:5,held:false,holder:null}}),false);
  assert.equal(e.receive({kind:'draft_state',id:'other',rid:'expired:5:other',reason:'expired',inbox:{...t,edit_version:5,held:false,holder:null}}),false);
  assert.equal(e.receive({kind:'draft_state',id:'source',rid:'x',inbox:{...t,edit_version:5}}),false);   // still ours: nothing to do
  assert.equal(e.needsHold,false);assert.equal(e.token.held,true);
}
// a pending request of ours decides by its own rid, not by this rule
{
  const e=make(),t=held(e);e.direct('Suggest 11.');e.revise('ask');
  assert.equal(e.receive({kind:'draft_state',id:'source',rid:'expired:2:source',reason:'expired',inbox:{...t,edit_version:2,held:false,holder:null}}),false);
}
console.log('hold-expired ok');
