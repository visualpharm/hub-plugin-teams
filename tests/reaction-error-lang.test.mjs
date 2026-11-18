// The fallback reasons of a failed reaction (refused by the hub, transport error) follow the owner's language like the rest of the bubble
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source=readFileSync(process.argv[2],'utf8').replace(/^import .*;\s*$/gm,'').replace(/^export default /gm,'').replace(/^export /gm,'');
const uiText=await import('data:text/javascript,'+encodeURIComponent(readFileSync('web/ui-text.js','utf8')));
const mod=f=>import('data:text/javascript,'+encodeURIComponent(readFileSync('web/'+f,'utf8')));
const parts=await Promise.all(['provider-read.js','working-hours.js','read-state.js','conversation-pins.js','conversation-chain.js','open-target.js','list-advance.js'].map(mod));
const ctx={console,URL,Map,Set,JSON,localStorage:{getItem:()=>null,setItem:()=>{}},document:{documentElement:{lang:'ru'}},...Object.assign({},...parts),T:uiText.T};
vm.createContext(ctx);
vm.runInContext(source+'\nlet clearAlert=false;paint=()=>{if(clearAlert){clearAlert=false;error="";}};globalThis.t={reactTo,msgs,reactionSends,clearAlertOnPaint:()=>{clearAlert=true;},setHub:v=>{hub=v;}};',ctx);
const expected={
  ru:['Реакция отклонена','Не удалось отправить реакцию. Попробуйте ещё раз.'],
  en:['Reaction refused','Could not send reaction. Try again.'],
  es:['Reacción rechazada','No se pudo enviar la reacción. Inténtalo de nuevo.'],
};
for (const [lang,[refused,broken]] of Object.entries(expected)) {
  uiText.bindHub({snapshot:()=>({owner:{lang}})});
  const m={id:'one-'+lang,src:'telegram',contact:'synthetic',react:true};
  ctx.t.msgs.set(m.id,m);
  // the hub refused the post and the shared alert was cleared before reactTo read it: the bubble keeps its own reason
  const page={snapshot:()=>({sessions:[]}),postFeed:async()=>{ctx.t.clearAlertOnPaint();return {error:'refused'};}};ctx.t.setHub(page);
  await ctx.t.reactTo(m,'👍');
  assert.deepEqual({state:ctx.t.reactionSends.get(m.id).state,error:ctx.t.reactionSends.get(m.id).error},{state:'fail',error:refused},lang+': refused reaction');
  ctx.t.reactionSends.delete(m.id);
  page.postFeed=async()=>{throw Error('offline');};
  await ctx.t.reactTo(m,'👍');
  assert.deepEqual({state:ctx.t.reactionSends.get(m.id).state,error:ctx.t.reactionSends.get(m.id).error},{state:'fail',error:broken},lang+': transport failure');
}
console.log('A failed reaction explains itself in the owner language');
