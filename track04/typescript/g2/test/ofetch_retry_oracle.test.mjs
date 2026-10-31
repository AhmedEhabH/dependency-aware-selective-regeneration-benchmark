import test from 'node:test';
import assert from 'node:assert/strict';
import { BASE, EXPECTED, classifyTrace, parseArgs } from '../scripts/ofetch_retry_oracle.mjs';

test('historical duplicated-base trace classified RED',()=>{
  assert.equal(classifyTrace([EXPECTED, BASE+EXPECTED],{ok:true}), 'RED_DUPLICATED_BASEURL');
});
test('idempotent retry trace classified GREEN',()=>{
  assert.equal(classifyTrace([EXPECTED, EXPECTED],{ok:true}), 'GREEN_STABLE_BASEURL');
});
test('missing retry cannot yield false RED or GREEN',()=>{
  assert.equal(classifyTrace([EXPECTED],{ok:true}), 'UNEXPECTED_OR_INCOMPLETE_TRACE');
});
test('unexpected wrong path cannot be mislabelled regression',()=>{
  assert.equal(classifyTrace([EXPECTED, BASE+'wrong'],{ok:true}), 'UNEXPECTED_OR_INCOMPLETE_TRACE');
});
test('failed request cannot be mislabelled correct',()=>{
  assert.equal(classifyTrace([EXPECTED, EXPECTED],{ok:false}), 'UNEXPECTED_OR_INCOMPLETE_TRACE');
});
test('CLI requires both module and report paths',()=>{
  assert.deepEqual(Object.keys(parseArgs(['--module','/tmp/m.mjs','--out','/tmp/r.json'])),['module','out']);
  assert.throws(()=>parseArgs(['--module','/tmp/m.mjs']),/USAGE/);
});
