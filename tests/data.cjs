const assert=require('node:assert/strict'),fs=require('node:fs');
global.window={};require('../data.js');const d=window.WORKBOOK;
assert.equal(d.questions.length,157);assert.equal(new Set(d.questions.map(q=>q.id)).size,157);
for(const q of d.questions){assert.ok(q.prompt);assert.ok(q.explanation);assert.ok(q.answer.length);assert.equal(new Set(q.choices.map(c=>c.key)).size,q.choices.length);for(const a of q.answer)assert.ok(q.choices.some(c=>c.key===a),`Question ${q.id}: answer ${a}`);for(const p of [...q.images,...q.explanationImages])assert.ok(fs.existsSync(require('node:path').join(__dirname,'..',p)),p);}
for(const n of d.notes){assert.ok(n.lines.length);for(const i of n.images)assert.ok(fs.existsSync(require('node:path').join(__dirname,'..',i.src)));}
console.log('PASS: 157 unique questions, answer/choice consistency, explanations, notes, and image files.');
