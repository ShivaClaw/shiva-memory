#!/usr/bin/env node
/**
 * Layer 0.5 Pre-Turn Hook for lossless-claw
 * 
 * Runs before context expansion.
 * Reads latest staging file and injects relevant memories.
 */

const fs = require('fs');
const path = require('path');

const STAGING_DIR = '/data/.openclaw/workspace/memory/layer0.5';
const MAX_RESULTS = 3;

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
    console.error(`[L0.5-hook] Read error: ${err.message}`);
    return null;
  }
}

function injectIntoContext(contextBuffer, injection) {
  if (!injection || !injection.context_markdown) return contextBuffer;
  
  // Prepend semantic recall before existing context
  const header = `\n## Semantic Recall (Layer 0.5)\n*Confidence: ${(injection.confidence * 100).toFixed(0)}%*\n`;
  return header + injection.context_markdown + '\n\n' + contextBuffer;
}

module.exports = {
  // lossless-claw hook interface
  preExpansion: async (contextBuffer, metadata) => {
    const injection = readLatestStaging();
    if (!injection || injection.results_count === 0) {
      return contextBuffer; // No results, pass through
    }
    
    return injectIntoContext(contextBuffer, injection);
  },
  
  // Test mode
  test: () => {
    const inj = readLatestStaging();
    console.log('Latest staging:', inj ? 'OK' : 'EMPTY');
    if (inj) {
      console.log(`  Results: ${inj.results_count}`);
      console.log(`  Confidence: ${inj.confidence}`);
      console.log(`  Markdown length: ${inj.context_markdown.length}`);
    }
  }
};

// Allow testing from CLI
if (require.main === module) {
  const hook = module.exports;
  hook.test();
}
