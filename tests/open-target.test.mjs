import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const {openTarget,openFolder,OPEN_FOLDERS,feedMessage,canLoadOld,oldMessage}=await import('data:text/javascript,'+encodeURIComponent(readFileSync('web/open-target.js','utf8')));

// Колокольчик хаба: уведомление плагина proactivity, id — id сообщения ленты teams
assert.deepEqual(openTarget({plugin:'proactivity',id:'wa:whatsapp:549@c.us:ABC'}),{id:'wa:whatsapp:549@c.us:ABC'},
  'the bell passes the notifying plugin, not the feed channel: the id is still the Inbox message');
assert.deepEqual(openTarget({plugin:'teams',id:'m1'}),{id:'m1'});
assert.deepEqual(openTarget({plugin:'teams',post:'p12'}),{post:'p12'});
assert.deepEqual(openTarget({post:'p12'}),{post:'p12'});
assert.equal(openTarget({plugin:'proactivity',post:'p12'}),null,'a post number belongs to the teams feed only');
assert.equal(openTarget({plugin:'teams'}),null);
assert.equal(openTarget(null),null);
assert.equal(openTarget(undefined),null);

// Старый пост: колокол кладёт к id номер поста и признак «отвечено»; кривой номер отбрасываем
assert.deepEqual(openTarget({plugin:'proactivity',id:'m1',post:'p12',state:'answered'}),{id:'m1',post:'p12',state:'answered'});
assert.deepEqual(openTarget({plugin:'proactivity',id:'m1',post:'p12'}),{id:'m1',post:'p12'});
assert.deepEqual(openTarget({plugin:'proactivity',id:'m1',post:'12; drop',state:'new'}),{id:'m1'},'a bad post number and an unknown state are dropped');
const FEATURE=['feed.post_by_id'];
assert.equal(canLoadOld({id:'m1',post:'p12'},FEATURE),true);
assert.equal(canLoadOld({id:'m1',post:'p12'},[]),false,'a core without the feature keeps the old notice');
assert.equal(canLoadOld({id:'m1',post:'p12'},undefined),false);
assert.equal(canLoadOld({id:'m1'},FEATURE),false,'no post number — nothing to load');
const AUTHOR='плагин teams';
const raw=(d,over={})=>({id:'p12',by:AUTHOR,text:JSON.stringify(d),...over});
const msg={kind:'msg',id:'m1',src:'whatsapp',text:'hi',at:'2026-10-01T10:00:00Z'};
assert.deepEqual(oldMessage([raw(msg)],{id:'m1',post:'p12'},AUTHOR),{...msg,post:'p12'});
assert.equal(oldMessage([raw(msg)],{id:'other',post:'p12'},AUTHOR),null,'the post holds another message than the address names');
assert.equal(oldMessage([raw(msg,{by:'owner'})],{id:'m1',post:'p12'},AUTHOR),null,'only the plugin process writes messages');
assert.equal(oldMessage([raw(msg,{id:'p13'})],{id:'m1',post:'p12'},AUTHOR),null,'the post number must be the one asked');
assert.equal(oldMessage([raw({kind:'answered',id:'m1'})],{id:'m1',post:'p12'},AUTHOR),null,'a fact is not a message');
assert.equal(oldMessage([{id:'p12',by:AUTHOR,text:'not json'}],{post:'p12'},AUTHOR),null);
assert.equal(oldMessage(undefined,{post:'p12'},AUTHOR),null);
assert.equal(oldMessage([raw(msg)],{post:'p12'},AUTHOR).id,'m1','by post alone the id is whatever the post holds');
assert.equal(feedMessage({kind:'msg',id:'x',src:'support',where:'a · thread'},'p1'),null,'a thread reply without a mention is not shown');
assert.equal(feedMessage({kind:'msg',id:'x',src:'support',where:'a · thread',mention:true},'p1').src,'mention');
assert.equal(feedMessage({kind:'msg',id:'x',src:'support'},'p1').src,'channel');

// Отвеченное сообщение — только в «Разобранных»: раньше переход молча оставался на пустом списке
const answered={id:'a'},fresh={id:'n'},hidden={id:'h'};
const folderOf={a:['done'],n:['new'],h:['archive','done']};
const inFolder=(m,f)=>(folderOf[m.id]||[]).includes(f);
assert.equal(openFolder(answered,inFolder),'done');
assert.equal(openFolder(fresh,inFolder),'new');
assert.equal(openFolder(hidden,inFolder),'archive','a narrower folder wins over «Разобранные»');
assert.equal(openFolder({id:'x'},inFolder),undefined);
assert.equal(openFolder(undefined,inFolder),undefined);
assert.equal(OPEN_FOLDERS.at(-1),'done');
// Подключено в плагине: переход читает адрес через openTarget, папка — через openFolder, а плагин в адресе не сверяется
const main=readFileSync(process.argv[2]||'web/main.js','utf8');
assert.ok(/open\(root, params\) \{[^}]*openTarget\(params\)/.test(main),'open() reads the address via openTarget');
assert.ok(!/params\?\.plugin !== "teams"/.test(main),'open() must not drop a bell address from another plugin');
assert.ok(/openFolder\(m, inFolder\)/.test(main),'openMessage looks in every folder, done included');
assert.ok(/canLoadOld\(target, hub\.snapshot\(\)\?\.features\)/.test(main) && main.includes('hub.feedPosts'),'openMessage loads a post past the feed window by number, gated by the core feature');
assert.ok(!/const reply = d\.src === "support"/.test(main),'the message shape of a feed post is built in one place');
assert.ok(main.includes('openNotice'),'a message that is not found says so instead of a silent empty list');
console.log('Inbox open target: any notifying plugin by id, answered messages open in the done folder');
