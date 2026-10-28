// Editor state only. No browser, accounts or outbound sends.
// Ivan m612908: a pressed reply goes even if the draft changed version meanwhile; "not sent" only on a real refusal.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../web/editor-state.js',import.meta.url),'utf8');
const {InboxEditor}=await import('data:text/javascript,'+encodeURIComponent(source));
const token={v:1,version:'source-A',edit_version:0,held:false,holder:null};
const message={id:'source',post:'p42',inbox:token};
const STALE='Inbox changed; refresh the current item before acting';
const start=()=>{
  const e=new InboxEditor(message,'web-tab','Owner exact draft');
  e.hold('hold');
  const held={...token,edit_version:1,held:true,holder:'web-tab'};
  assert.equal(e.receive({kind:'draft_state',id:'source',rid:'hold',inbox:held}),true);
  return e;
};

// Apply never asks for another gesture: a newer edit is replaced by the proposal the owner chose.
{
  const e=start();e.direct('Suggest 11.');e.revise('ask');
  const current={...e.token,edit_version:2};
  e.receive({kind:'draft_state',id:'source',rid:'ask',inbox:current});
  assert.equal(e.receive({kind:'draft_proposal',id:'source',post:'p42',rid:'ask',editor:'web-tab',inbox:current,
    text:'Could we meet at 11?',context:'c',next_action:'n',requires_apply:true}),true);
  e.edit('My newer edit');e.direct('Another instruction');
  assert.equal(e.apply().text,'Could we meet at 11?');
  assert.equal(e.text,'Could we meet at 11?');assert.equal(e.error,'');
}

// CAS-only refusal: one automatic resend of the same text with a new rid, the fresh token and replaces.
{
  const e=start();e.send('first','Pressed reply',{target:'recipient-a'});
  const fresh={v:1,version:'source-B',edit_version:3,held:true,holder:'web-tab'};
  assert.equal(e.receive({kind:'send_blocked',id:'source',rid:'first',target:'recipient-a',error:STALE,inbox:fresh}),true);
  assert.equal(e.error,'');assert.equal(e.delivery,null);
  assert.deepEqual(e.retry,{replaces:'first',text:'Pressed reply',target:'recipient-a'});
  assert.throws(()=>e.send('manual','Pressed reply'),/Wait/);   // the owner's second press waits for the resend
  const q=e.resend('second');
  assert.deepEqual(q,{kind:'send',id:'source',rid:'second',inbox:fresh,editor:'web-tab',text:'Pressed reply',
    replaces:'first',target:'recipient-a'});
  assert.equal(e.retry,null);assert.equal(e.delivery.rid,'second');
  // The resend is refused again — shown as "not sent" with its reason, never a third attempt.
  assert.equal(e.receive({kind:'send_blocked',id:'source',rid:'second',target:'recipient-a',error:STALE,
    inbox:{...fresh,edit_version:4}}),true);
  assert.equal(e.retry,null);assert.equal(e.delivery,null);assert.match(e.error,/Inbox changed/);
}

// Fresh token not held by this editor: the resend needs a hold first; refused hold gives up.
{
  const e=start();e.send('first','Pressed reply');
  const fresh={v:1,version:'source-A',edit_version:5,held:false,holder:null};
  e.receive({kind:'send_blocked',id:'source',rid:'first',error:STALE,inbox:fresh});
  assert.ok(e.retry);assert.equal(e.needsHold,true);
  assert.throws(()=>e.resend('second'),/Confirm/);
  e.hold('rehold');
  e.receive({kind:'draft_state',id:'source',rid:'rehold',inbox:{...fresh,edit_version:6,held:true,holder:'web-tab'}});
  assert.equal(e.resend('second').inbox.edit_version,6);
}
{
  const e=start();e.send('first','Pressed reply');
  e.receive({kind:'send_blocked',id:'source',rid:'first',error:STALE,inbox:{...token,edit_version:5}});
  e.giveUp('Another client holds this editor; retain local text');
  assert.equal(e.retry,null);assert.match(e.error,/Another client/);
  assert.throws(()=>e.resend('second'),/Nothing to resend/);
}

// Any other refusal, unknown delivery, a scheduled reply or a refusal without a fresh token — no resend.
for (const d of [
  {kind:'send_blocked',reason:'newer_messages',error:'New messages arrived in this conversation. Review them before sending.'},
  {kind:'send_blocked',reason:'source_unreadable',error:'Could not read the conversation to verify it.',inbox:token},
  {kind:'send_blocked',error:'Owner is editing or directing this conversation; explicit release required',inbox:token},
  {kind:'send_failed',error:'Night hours'},
  {kind:'send_blocked',error:STALE},   // collector without a fresh token
]) {
  const e=start();e.send('first','Pressed reply');
  assert.equal(e.receive({...d,id:'source',rid:'first'}),true);
  assert.equal(e.retry ?? null,null,JSON.stringify(d));assert.ok(e.error);
}
for (const d of [{kind:'send_failed',unresolved:true,error:STALE},{kind:'send_uncertain',error:STALE,inbox:token}]) {
  const e=start();e.send('first','Pressed reply');
  e.receive({...d,id:'source',rid:'first'});
  assert.equal(e.retry ?? null,null);assert.equal(e.delivery.state,'unresolved');
}
{
  const e=start();e.send('later','Future reply',{at:'2099-06-17T15:30:00.000Z'});
  e.receive({kind:'send_blocked',id:'source',rid:'later',error:STALE,inbox:{...token,edit_version:4,held:true,holder:'web-tab'}});
  assert.equal(e.retry ?? null,null);assert.match(e.error,/Inbox changed/);
}
// A changed conversation (new post) is not a version-only refusal.
{
  const e=start();e.send('first','Pressed reply');e.observe({...message,post:'p43'});
  e.receive({kind:'send_blocked',id:'source',rid:'first',error:STALE,inbox:{...token,edit_version:4,held:true,holder:'web-tab'}});
  assert.equal(e.retry ?? null,null);
}
console.log('Inbox editor: apply without a second gesture, one CAS resend with replaces, real refusals shown passed');
