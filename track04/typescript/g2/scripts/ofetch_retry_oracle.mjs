#!/usr/bin/env node
// Track 04 G2 diagnostic oracle. Intentionally public, NOT a blinded holdout.
// No external network, no child patch, no model inference. Uses the built historical library.
import assert from 'node:assert/strict';
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

export const BASE = 'https://oracle.invalid/';
export const RELATIVE = '404';
export const EXPECTED = 'https://oracle.invalid/404';

export function classifyTrace(trace, returnedData) {
  if (!Array.isArray(trace) || trace.length !== 2 || trace[0] !== EXPECTED || !returnedData || returnedData.ok !== true)
    return 'UNEXPECTED_OR_INCOMPLETE_TRACE';
  if (trace[1] === EXPECTED) return 'GREEN_STABLE_BASEURL';
  // Historical defect is *repeated base URL*, not merely a nonmatching URL.
  if (trace[1].startsWith(BASE) && trace[1].slice(BASE.length).startsWith(BASE))
    return 'RED_DUPLICATED_BASEURL';
  return 'UNEXPECTED_OR_INCOMPLETE_TRACE';
}

export function parseArgs(argv) {
  if (argv.length !== 4 || argv[0] !== '--module' || argv[2] !== '--out' || !argv[1] || !argv[3])
    throw new Error('USAGE: node ofetch_retry_oracle.mjs --module absolute_or_relative_dist_index.mjs --out report.json');
  return { module: resolve(argv[1]), out: resolve(argv[3]) };
}

export async function execute(modulePath) {
  const requests = [];
  let returnedData = null;
  let error = null;
  try {
    // Import actual upstream-built artifact, not a source rewrite or test double of library code.
    const library = await import(pathToFileURL(modulePath).href);
    assert.equal(typeof library.createFetch, 'function', 'Historical build must export createFetch');
    if (typeof Response !== 'function') throw new Error('Node runtime lacks standard Response');
    const mockTransport = async (input) => {
      requests.push(String(input));
      const success = requests.length > 1;
      return new Response(JSON.stringify({ok: success}), {
        status: success ? 200 : 503,
        headers: {'content-type': 'application/json'}
      });
    };
    const client = library.createFetch({ fetch: mockTransport });
    returnedData = await client(RELATIVE, { baseURL: BASE, retry: 1 });
  } catch (e) {
    error = { name: e?.name || 'Error', message: String(e?.message || e) };
  }
  const classification = error ? 'HARNESS_OR_RUNTIME_ERROR' : classifyTrace(requests, returnedData);
  return {
    schema: 'track04-g2-oracle-v1',
    issue: 'unjs/ofetch#24',
    parent: 'a183b02048c5323bcb79f2a03862008466771104',
    reference: '7e1b54d1363ba3f5fe57fe8089babab921a8e9ea',
    classification,
    expected_request: EXPECTED,
    observed_requests: requests,
    returned_data: returnedData,
    error,
  };
}

async function main() {
  let opts;
  try { opts = parseArgs(process.argv.slice(2)); }
  catch (e) { console.error(String(e)); process.exitCode=2; return; }
  const result=await execute(opts.module);
  mkdirSync(dirname(opts.out),{recursive:true});
  writeFileSync(opts.out, JSON.stringify(result, null, 2) + '\n', 'utf8');
  console.log('TRACK04_G2_ORACLE_CLASSIFICATION=' + result.classification);
  console.log('TRACK04_G2_OBSERVED_URLS=' + JSON.stringify(result.observed_requests));
  // Red is an expected oracle failure, but this command itself is not a failed harness.
  process.exitCode = result.classification === 'HARNESS_OR_RUNTIME_ERROR' || result.classification === 'UNEXPECTED_OR_INCOMPLETE_TRACE' ? 2 : 0;
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) await main();
