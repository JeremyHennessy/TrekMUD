'use strict';
const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const page = fs.readFileSync(path.join(root, 'ui/3d/index.html'), 'utf8');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'ui/3d/rooms.json'), 'utf8'));
const topology = JSON.parse(fs.readFileSync(path.join(root, 'world/asteria/topology.json'), 'utf8'));

test('3D room is separately identified and matches approved ship topology', () => {
  assert.equal(manifest.shipId, 'USS-ASTERIA');
  assert.equal(manifest.registry, 'NCC-63542');
  assert.equal(manifest.rooms.length, 1);
  const room = manifest.rooms[0];
  const canonical = topology.locations.find(row => row.id === room.roomId);
  assert.ok(canonical, `unknown topology room ${room.roomId}`);
  assert.equal(room.roomId, 'AST-D01-BRIDGE');
  assert.equal(room.deck, canonical.deck);
  assert.equal(room.campaignAccess, canonical.access);
  const neighbors = topology.edges.filter(edge => edge.to === room.roomId || edge.from === room.roomId)
    .map(edge => edge.to === room.roomId ? edge.from : edge.to).sort();
  assert.deepEqual(room.confirmedTopologyNeighbors, neighbors);
  assert.equal(room.linkedTravelImplemented, false);
});

test('3D page parses as JavaScript without external assets or hidden campaign state', () => {
  const source = page.match(/<script>([\s\S]*?)<\/script>/);
  assert.ok(source, 'missing standalone scene script');
  assert.doesNotThrow(() => new vm.Script(source[1], { filename: 'asteria-3d.js' }));
  assert.ok(page.includes("roomId:'AST-D01-BRIDGE'"));
  assert.ok(page.includes("getContext('webgl'"));
  assert.ok(page.includes("$('enter').addEventListener('click'"));
  assert.ok(page.includes('requestAnimationFrame(frame)'));
  assert.doesNotMatch(page, /<script[^>]+src=|<link[^>]+href="https?:|<img[^>]+src="https?:/i);
  for (const forbidden of ['TrekMUD-GM', 'secretSeedHex', 'npc-private', 'plot-clocks', 'future-events']) {
    assert.ok(!page.includes(forbidden), `potential GM data in 3D page: ${forbidden}`);
  }
});
