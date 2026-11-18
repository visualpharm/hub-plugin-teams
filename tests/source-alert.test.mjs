// A source that stopped reading is named in plain words, never the raw provider error with its URLs; a lost sign-in has
// "Reconnect" (a request to the hub), a network failure is no lost sign-in
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const uiText=await import('data:text/javascript,'+encodeURIComponent(readFileSync('web/ui-text.js','utf8')));
globalThis.document={documentElement:{lang:'ru'}};
const code=readFileSync('web/source-alert.js','utf8').replace(/^import .*;\s*$/gm,'');
globalThis.__T=uiText.T;
const {sourceAlert,reconnectAsk,plain}=await import('data:text/javascript,'+encodeURIComponent('const T=(...a)=>globalThis.__T(...a);'+code));
const names={teams:'Teams',email:'Mail'};
// as the reader sends it: source "email", the account first, the line cut to 160 characters in the middle of the URL
const lost=('me@example.com: oauth2: "invalid_grant" "Token has been expired or revoked." visit https://accounts.google.com/o/oauth2/v2/auth?client_id=synthetic.apps.googleusercontent.com&redirect_uri=http%3A%2F%2F127.0.0.1%3A8080').slice(0,160);
const net='me@example.com: Post "https://oauth2.googleapis.com/token": dial tcp: lookup oauth2.googleapis.com: no such host';
const cases={
  ru:['Gmail отключился — новые письма сюда не приходят.','Не могу прочитать Gmail: me@example.com: Post : dial tcp: lookup oauth2.googleapis.com: no such host. Новые письма сюда не приходят.',
      'Не могу прочитать Teams: timed out. Новые сообщения сюда не приходят. Возможно, истёк вход ms365.'],
  en:['Gmail disconnected — new mail is not coming in.','Cannot read Gmail: me@example.com: Post : dial tcp: lookup oauth2.googleapis.com: no such host. New mail is not coming in.',
      'Cannot read Teams: timed out. New messages are not coming in. The ms365 sign-in may have expired.'],
  es:['Gmail se desconectó: el correo nuevo no llega.','No puedo leer Gmail: me@example.com: Post : dial tcp: lookup oauth2.googleapis.com: no such host. El correo nuevo no llega.',
      'No puedo leer Teams: timed out. Los mensajes nuevos no llegan. Quizás venció el inicio de sesión de ms365.'],
};
for (const [lang,[gone,down,teams]] of Object.entries(cases)) {
  uiText.bindHub({snapshot:()=>({owner:{lang}})});
  assert.deepEqual(sourceAlert('email',lost,names),{text:gone,reconnect:true},lang+': a lost sign-in');
  assert.deepEqual(sourceAlert('email',net,names),{text:down,reconnect:false},lang+': a network failure on the token address is no lost sign-in');
  assert.deepEqual(sourceAlert('teams','timed out https://status.example.com/x',names),{text:teams,reconnect:false},lang+': other failures drop the URL');
}
uiText.bindHub({snapshot:()=>({owner:{lang:'en'}})});
assert.equal(sourceAlert('teams','HTTP 401 Unauthorized',names).text,'Teams disconnected — new messages are not coming in.');
assert.equal(sourceAlert('teams','Not logged in. Run m365 login',names).reconnect,true,'an ms365 sign-in that ran out');
assert.equal(sourceAlert('teams','GET https://graph.microsoft.com/v1.0/chats/401/messages: timeout',names).reconnect,false,'a 401 inside a URL is no sign-in');
assert.equal(sourceAlert('email','',names).reconnect,false);
assert.equal(plain('a: see https://x.example/a?b=1": and more.'),'a: see : and more');
const ask=reconnectAsk('email',lost,names);
assert.ok(ask.startsWith('Gmail disconnected (source email): ')&&ask.endsWith('Sign it in again.')&&!ask.includes('http'),ask);
console.log('A disconnected source is one plain line; Reconnect asks the hub');
