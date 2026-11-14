import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const {nextAfter,listAdvance,OWN_WINDOW,UNDO_SECONDS}=await import('data:text/javascript,'+encodeURIComponent(readFileSync('web/list-advance.js','utf8')));

// The one rule of the native lists (ListAdvance.swift): the next row below, else the nearest above, else nothing.
assert.equal(nextAfter('b',['a','b','c'],['a','c']),'c','the next row below opens');
assert.equal(nextAfter('c',['a','b','c'],['a','b']),'b','the last row yields to the nearest above');
assert.equal(nextAfter('b',['a','b','c','d'],['a','d']),'d','rows that left together are skipped');
assert.equal(nextAfter('a',['a'],[]),null,'an empty list opens nothing');
assert.equal(nextAfter('x',['a','b'],['a','b']),null,'a row that was not shown has no neighbour');
assert.equal(nextAfter('b',['a','b','c'],['c','a']),'c','the neighbour comes from the old order, not the new one');

// Own mark: only an owner action here advances; a closure by the hub or another device does not.
const a=listAdvance();
assert.equal(a.mine(['k1'],0),false,'nothing acted: not own');
a.acted(['k1'],0);
assert.equal(a.mine(['k1'],1000),true,'acted here: own');
assert.equal(a.mine(['k1'],1000+500),true,'the same departure seen again within the grace second stays own');
assert.equal(a.mine(['k1'],1000+2500),false,'after the first step the mark is short: a later hub closure is not own');
a.acted(['k2'],0);
assert.equal(a.mine(['k2'],OWN_WINDOW*1000+1),false,'the mark expires after the own window');
a.acted(['k3'],0);a.kept(['k3']);
assert.equal(a.mine(['k3'],10),false,'kept (refused, restored) clears the mark');
a.acted(['k4','k5'],0);
assert.equal(a.mine(['k5'],10),true,'any id of the item counts');
assert.equal(UNDO_SECONDS,10,'the Undo strip lives ten seconds, as in the native lists');
console.log('list-advance ok');
