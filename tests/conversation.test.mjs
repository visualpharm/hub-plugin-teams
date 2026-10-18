import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source=readFileSync(process.argv[2],'utf8').replace(/^import .*;\s*$/gm,'').replace(/^export default /gm,'').replace(/^export /gm,'');
const {providerReadState}=await import('data:text/javascript,'+encodeURIComponent(readFileSync('web/provider-read.js','utf8')));
const hoursModule=await import('data:text/javascript,'+encodeURIComponent(readFileSync('web/working-hours.js','utf8')));
const {localReadState}=await import('data:text/javascript,'+encodeURIComponent(readFileSync('web/read-state.js','utf8')));
const {conversationPins}=await import('data:text/javascript,'+encodeURIComponent(readFileSync('web/conversation-pins.js','utf8')));
const ctx={console,URL,Map,Set,conversationPins,localReadState,providerReadState,...hoursModule};vm.createContext(ctx);
vm.runInContext(source+'\nglobalThis.t={byPerson,pinKey,conversationSource};',ctx);
const message=(id,contact,src='dm')=>({id,contact,src,from:'Alex'});
assert.equal(ctx.t.byPerson([message('a','account-a/chat-a'),message('b','account-a/chat-b')]).size,2,'Same name is not conversation identity');
assert.equal(ctx.t.byPerson([message('a','account-a/chat-a'),message('b','account-a/chat-a')]).size,1);
assert.equal(ctx.t.byPerson([message('a',null),message('b',null)]).size,2,'Missing identities must not merge histories');
assert.equal(ctx.t.byPerson([message('a','shared','telegram'),message('b','shared','whatsapp')]).size,2,'Contact identifiers belong to their source family');
assert.equal(ctx.t.byPerson([message('a','shared','dm'),message('b','shared','mention'),message('c','shared','channel')]).size,1,'Teams surfaces share one conversation');
assert.equal(ctx.t.pinKey(message('a','shared','telegram')),JSON.stringify(['telegram','shared']),'Existing saved pin/read identity must remain stable');
console.log('Inbox grouping preserves exact conversations despite repeated display names');

assert.equal(ctx.t.pinKey({src:'channel',contact:'teams/thread',id:'1'}),ctx.t.pinKey({src:'mention',contact:'teams/thread',id:'2'}));
assert.notEqual(ctx.t.pinKey({src:'telegram',contact:'same',id:'1'}),ctx.t.pinKey({src:'email',contact:'same',id:'2'}));
for (const [src,where,expected] of [
  ['dm','Личка','Teams · Личка'],['mention','Команда › Релиз','Teams · Команда › Релиз'],
  ['channel','','Teams'],['telegram','Telegram','Telegram'],['whatsapp','Mint','WhatsApp · Mint'],
  ['email','Почта','Почта'],['telegram','   ','Telegram'],
]) assert.equal(ctx.t.conversationSource({src,where}),expected,'Source context must not repeat the provider or add an extra category');
