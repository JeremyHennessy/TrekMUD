'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const src=fs.readFileSync(path.join(root,'ui/3d-layout/index.html'),'utf8');

test('Asteria layout embeds a valid 117-component glTF 2.0 model',()=>{
 const m=src.match(/<script id="glb-source" type="application\/octet-stream">([\s\S]*?)<\/script>/);
 assert.ok(m,'embedded glTF is missing');
 const b=Buffer.from(m[1].trim(),'base64');
 assert.ok(b.length>60000&&b.length<100000,'unexpected GLB payload');
 assert.equal(b.readUInt32LE(0),0x46546c67,'wrong GLB magic');
 assert.equal(b.readUInt32LE(4),2,'wrong GLB version');
 assert.equal(b.readUInt32LE(8),b.length,'GLB length mismatch');
 assert.equal(b.readUInt32LE(16),0x4e4f534a,'first GLB chunk must be JSON');
 const j=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)).toString('utf8'));
 assert.equal(j.meshes.length,117);
 assert.ok(j.nodes.some(x=>x.name==='AST_Captain_Chair_Back'));
 assert.ok(j.nodes.some(x=>x.name==='AST_Aft_Access_Hub_Opening'));
 assert.ok(j.nodes.some(x=>x.name==='AST-D01-BRIDGE__floor-ellipse'));
 assert.equal(j.asset.version,'2.0');
});

test('Independent walkable browser page parses and does not access campaign or external CDNs',()=>{
 assert.ok(src.includes("roomId:'AST-D01-BRIDGE'"));
 assert.ok(src.includes('function walk('));
 assert.ok(src.includes('function parseGLB('));
 assert.ok(src.includes("getContext('webgl'"));
 assert.ok(src.includes('data-view="science"'));
 assert.doesNotMatch(src,/<script[^>]+src=|<link[^>]+href="https?:|<img[^>]+src="https?:/i);
 for(const t of ['TrekMUD-GM','secretSeedHex','npc-private','plot-clocks','future-events','localStorage.setItem','fetch(']) assert.ok(!src.includes(t),'unexpected browser data access: '+t);
 const parts=src.match(/<script>([\s\S]*?)<\/script><\/body>/);
 assert.ok(parts,'viewer JS not embedded');
 assert.doesNotThrow(()=>new vm.Script(parts[1]));
});