// The owner's own reaction pressed again comes off (Teams), and the owner's pill follows the later fact in the feed:
// the outcome of the owner's own reaction or the reactions Teams reported with the conversation. Event replay only.
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const mod=f=>import('data:text/javascript,'+encodeURIComponent(readFileSync('web/'+f,'utf8')));
const parts=await Promise.all(['provider-read.js','working-hours.js','read-state.js','conversation-pins.js','conversation-chain.js','open-target.js','list-advance.js'].map(mod));
const source=readFileSync(process.argv[2],'utf8').replace(/^import .*;\s*$/gm,'').replace(/^export default /gm,'').replace(/^export /gm,'');
const key='teams:chat:c1:m1';
const post=(n,data,by='плагин teams')=>({id:`p${n}`,by,text:JSON.stringify(data)});
const start=[post(1,{kind:'config',reaction_target:1,reaction_unset:1}),post(2,{kind:'msg',id:key,src:'dm',from:'Colleague',text:'Look',reply:true,react:true})];
const thread=(n,reactions)=>post(n,{kind:'thread',id:key,part:0,of:1,items:[
  {at:'2026-11-17T21:28:00Z',from:'Colleague',me:false,text:'Look',id:'m1',source:true,...(reactions ? {reactions} : {})},
  {at:'2026-11-17T21:20:00Z',from:'Colleague',me:false,text:'Before',id:'m0',reactions:[{emoji:'🔥',n:1,mine:true}]}]});

async function page(batches) {
  const ctx={console,URL,Map,Set,JSON,setTimeout,clearTimeout,localStorage:{getItem:()=>null,setItem:()=>{}},...Object.assign({},...parts),T:(ru)=>ru};vm.createContext(ctx);
  vm.runInContext(source+'\npaint=()=>{};globalThis.t={offline:()=>offline,sync,reactTo,ownReactionOf,msgs,reactionSends,setHub:h=>hub=h};',ctx);
  const posted=[];let at=0;
  ctx.t.setHub({feed:async()=>batches[at++]||[],postFeed:async text=>{posted.push(JSON.parse(text));return {};},snapshot:()=>({sessions:[]})});
  const more=async extra=>{if(extra)batches.push(extra);await ctx.t.sync();};
  for(let i=0;i<batches.length;i++)await ctx.t.sync();
  assert.equal(ctx.t.offline(),null,'the feed replays without an error');
  return {...ctx.t,posted,more,m:()=>ctx.t.msgs.get(key)};
}

// set through the hub, then pressed again: the second press is an unreact, and its outcome takes the pill off
{
  const p=await page([start,[post(3,{kind:'react',id:key,rid:'r1',emoji:'👍'},'owner'),post(4,{kind:'reacted',id:key,rid:'r1',emoji:'👍'})]]);
  assert.equal(p.ownReactionOf(p.m()),'👍');
  await p.reactTo(p.m(),'👍','',true);
  assert.equal(p.posted.at(-1).kind,'unreact');
  assert.equal(p.posted.at(-1).emoji,'👍');
  const rid=p.posted.at(-1).rid;
  assert.equal(p.reactionSends.get(key).unset,true);
  await p.more([post(5,{kind:'unreact',id:key,rid,emoji:'👍'},'owner'),post(6,{kind:'unreacted',id:key,rid,emoji:'👍'})]);
  assert.equal(p.reactionSends.get(key).state,'ok');
  assert.equal(p.ownReactionOf(p.m()),null,'after unreacted the pill is gone');
  // a set outcome cannot settle an unset request with the same rid
  await p.more([post(7,{kind:'reacted',id:key,rid,emoji:'👍'})]);
  assert.equal(p.ownReactionOf(p.m()),null);
}

// taken off in Teams itself: a later read of the conversation without the owner wins over the earlier "reacted"
{
  const p=await page([start,[post(3,{kind:'react',id:key,rid:'r1',emoji:'👍'},'owner'),post(4,{kind:'reacted',id:key,rid:'r1',emoji:'👍'}),
    thread(5,[{emoji:'👍',n:1}])]]);
  assert.equal(p.ownReactionOf(p.m()),null,'Graph is newer: no owner reaction');
  assert.equal(p.ownReactionOf(p.m(),'m0'),'🔥','a history bubble reads its own reactions');
}

// an older read does not undo the owner's newer reaction; a newer read with the owner keeps it
{
  const p=await page([start,[thread(3,null),post(4,{kind:'react',id:key,rid:'r1',emoji:'👍'},'owner'),post(5,{kind:'reacted',id:key,rid:'r1',emoji:'👍'})]]);
  assert.equal(p.ownReactionOf(p.m()),'👍');
  await p.more([thread(6,[{emoji:'❤️',n:2,mine:true}])]);
  assert.equal(p.ownReactionOf(p.m()),'❤️','reacted in Teams to another emoji: Teams wins');
}

// a refused unset keeps the reaction
{
  const p=await page([start,[post(3,{kind:'react',id:key,rid:'r1',emoji:'👍'},'owner'),post(4,{kind:'reacted',id:key,rid:'r1',emoji:'👍'}),
    post(5,{kind:'unreact',id:key,rid:'u1',emoji:'👍'},'owner'),post(6,{kind:'unreact_failed',id:key,rid:'u1',error:'Forbidden'})]]);
  assert.equal(p.reactionSends.get(key).state,'fail');
  assert.equal(p.ownReactionOf(p.m()),'👍');
}
console.log('The owner takes a Teams reaction off, and the pill follows Teams');
