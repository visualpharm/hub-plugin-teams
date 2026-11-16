// Page-side bookkeeping of editor holds. No browser, accounts or sends: a fake collector with the real control rules
// (docs/inbox-management.md: only the holder releases; navigation, time and restart never do).
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../web/hold-guard.js',import.meta.url),'utf8');
const g=await import('data:text/javascript,'+encodeURIComponent(source));
const store=()=>{const m=new Map();return {getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,String(v))};};
const base={v:1,version:'source-A',edit_version:0,held:false,holder:null};
// The collector: one conversation, one holder; release only by the same editor identity.
const collector=()=>{
  const c={token:{...base},control(q){
    if(q.action==='hold'){if(c.token.held&&c.token.holder!==q.editor)throw Error('Another client holds this editor');
      c.token={...c.token,edit_version:c.token.edit_version+1,held:true,holder:q.editor};}
    else{if(c.token.holder!==q.editor)throw Error('Another client holds this editor');
      c.token={...c.token,edit_version:c.token.edit_version+1,held:false,holder:null};}
    return c.token;}};
  return c;
};
const feed=(c)=>new Map([['m1',{id:'m1',inbox:c.token}]]);
const apply=(c,r,m)=>c.control(g.releaseRequest(m,r.editor||r,'rid'));

// 1. Open the letter, the hold stands, the page vanishes without a word (crash, killed tab, lost keepalive).
{
  const s=store(),c=collector(),T0=1_700_000_000_000;
  c.control({action:'hold',editor:'web-A'});g.remember(s,'web-A','m1',T0);g.beat(s,'web-A',T0);
  assert.equal(c.token.held,true);
  // another web tab of the same browser, while the first still beats: nothing to take
  assert.deepEqual(g.plan(s,'web-B',feed(c),{now:T0+10_000}).orphans,[]);
  // the first page stopped answering: the next open page releases it as the recorded holder
  const p=g.plan(s,'web-B',feed(c),{now:T0+40_000});
  assert.deepEqual(p.orphans,[{id:'m1',editor:'web-A'}]);
  apply(c,p.orphans[0],feed(c).get('m1'));
  assert.equal(c.token.held,false);
  // released: the registry forgets it by itself, no repeat
  assert.deepEqual(g.plan(s,'web-B',feed(c),{now:T0+50_000}).orphans,[]);
}
// 2. Same tab after a reload keeps its identity: an editor not on screen is its own stale hold.
{
  const s=store(),c=collector();
  c.control({action:'hold',editor:'web-A'});
  assert.deepEqual(g.plan(s,'web-A',feed(c),{inUse:new Set(['m1'])}).own,[]);   // editor on screen: keep
  const p=g.plan(s,'web-A',feed(c),{inUse:new Set()});
  assert.deepEqual(p.own,['m1']);
  c.control(g.releaseRequest({id:'m1',inbox:c.token},'web-A','r'));
  assert.equal(c.token.held,false);
}
// 3. Never touch what this browser did not take: another device, an Android/iPhone holder, an unknown web id.
{
  const s=store(),c=collector();
  c.control({action:'hold',editor:'AA804525-ANDROID'});
  const p=g.plan(s,'web-B',feed(c),{now:9e9});
  assert.deepEqual(p,{own:[],orphans:[]});
  const other=collector();other.control({action:'hold',editor:'web-OTHER-DEVICE'});
  assert.deepEqual(g.plan(s,'web-B',feed(other),{now:9e9}),{own:[],orphans:[]});
  // a hold this browser recorded but another client now owns is dropped, never released
  g.remember(s,'web-A','m1');
  assert.deepEqual(g.plan(s,'web-B',feed(c),{now:9e9}).orphans,[]);
  assert.deepEqual(g.plan(s,'web-B',feed(c),{now:9e9}).orphans,[]);
}
// 4. A page that left properly stops being alive at once, so its hold is not guarded by a stale beat.
{
  const s=store(),c=collector(),T0=1_700_000_000_000;
  c.control({action:'hold',editor:'web-A'});g.remember(s,'web-A','m1',T0);g.beat(s,'web-A',T0);g.leave(s,'web-A');
  assert.equal(g.plan(s,'web-B',feed(c),{now:T0+1}).orphans.length,1);
}
// 5. The release request is the collector's own control: current token, stable editor, explicit action.
{
  const c=collector();c.control({action:'hold',editor:'web-A'});
  const q=g.releaseRequest({id:'m1',inbox:c.token},'web-A','r1');
  assert.deepEqual(q,{kind:'draft_control',id:'m1',rid:'r1',inbox:c.token,editor:'web-A',action:'release'});
  assert.ok(JSON.stringify(q).length<1900);
}
// 6. A refused release is not repeated every beat.
{
  const a=g.attempts(),T0=0;
  assert.equal(a.due('k',T0),true);a.mark('k',T0);
  assert.equal(a.due('k',T0+5_000),false);assert.equal(a.due('k',T0+g.RETRY_MS),true);
  for(let i=0;i<g.MAX_TRIES;i++)a.mark('k',T0+(i+2)*g.RETRY_MS);
  assert.equal(a.due('k',1e12),false);
  a.clear('k');assert.equal(a.due('k',T0),true);
}
// 7. Blocked or corrupt storage never throws.
{
  const bad={getItem(){throw Error('blocked');},setItem(){throw Error('blocked');}};
  g.remember(bad,'web-A','m1');g.beat(bad,'web-A');g.leave(bad,'web-A');g.forget(bad,'web-A','m1');
  assert.deepEqual(g.plan(bad,'web-A',new Map(),{}),{own:[],orphans:[]});
  assert.deepEqual(g.plan({getItem:()=>'not json',setItem(){}},'web-A',new Map(),{}),{own:[],orphans:[]});
}
console.log('hold-guard ok');
