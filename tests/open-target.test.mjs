import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const {openTarget,openFolder,OPEN_FOLDERS}=await import('data:text/javascript,'+encodeURIComponent(readFileSync('web/open-target.js','utf8')));

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
assert.ok(main.includes('openNotice'),'a message that is not found says so instead of a silent empty list');
console.log('Inbox open target: any notifying plugin by id, answered messages open in the done folder');
