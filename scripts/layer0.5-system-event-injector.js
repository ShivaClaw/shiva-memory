#!/usr/bin/env node
/**
 * Layer 0.5 System Event Injector (Option C)
 * 
 * Reads latest staging file from Layer 0.5 sidecar and posts as system event
 * to the current session. Runs every 30 seconds (via cron).
 * 
 * This provides semantic context without needing lossless-claw plugin hooks.
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

const STAGING_DIR = '/data/.openclaw/workspace/memory/layer0.5';
const GATEWAY_URL = process.env.OPENCLAW_GATEWAY || 'http://localhost:3000';
const GATEWAY_TOKEN = process.env.OPENCLAW_TOKEN;

function readLatestStaging() {
  try {
    const files = fs.readdirSync(STAGING_DIR)
      .filter(f => f.startsWith('context-injection-'))
      .sort()
      .reverse();
    
    if (!files.length) return null;
    
    const latest = fs.readFileSync(
      path.join(STAGING_DIR, files[0]),
      'utf-8'
    );
    return JSON.parse(latest);
  } catch (err) {
    console.error(`[L0.5-event] Read error: ${err.message}`);
    return null;
  }
}

async function postSystemEvent(text) {
  return new Promise((resolve, reject) => {
    const url = new URL('/api/sessions/send', GATEWAY_URL);
    
    const body = JSON.stringify({
      sessionKey: 'agent:main:main', // Current session
      message: text,
    });
    
    const options = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
        'Authorization': `Bearer ${GATEWAY_TOKEN}`,
      },
      timeout: 10000,
    };
    
    const proto = GATEWAY_URL.startsWith('https') ? https : require('http');
    const req = proto.request(url, options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(data);
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${data}`));
        }
      });
    });
    
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

async function main() {
  const injection = readLatestStaging();
  if (!injection || injection.results_count === 0) {
    process.exit(0); // Silent exit if no results
  }
  
  // Format as system event
  const systemText = `## Semantic Context (Layer 0.5)
**Updated:** ${injection.timestamp}
**Confidence:** ${(injection.confidence * 100).toFixed(0)}%

${injection.context_markdown}`;
  
  try {
    await postSystemEvent(systemText);
    console.log(`[L0.5-event] ✓ Posted ${injection.results_count} memories to session`);
    process.exit(0);
  } catch (err) {
    console.error(`[L0.5-event] Post error: ${err.message}`);
    process.exit(1);
  }
}

if (!GATEWAY_TOKEN) {
  console.error('[L0.5-event] ERROR: OPENCLAW_TOKEN not set');
  process.exit(1);
}

main();
