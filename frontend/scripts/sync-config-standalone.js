/**
 * Standalone config sync script that works from frontend/ directory.
 * Safe for Vercel deployments where only frontend/ is accessible.
 * 
 * This script:
 * 1. Tries to find config.yaml in parent directory
 * 2. If found, syncs to config.ts
 * 3. If not found (Vercel), exits gracefully (config.ts is already committed)
 * 4. Environment variables will override defaults anyway
 */
const fs = require('fs');
const path = require('path');

// Try to find config.yaml (could be in parent directory)
const possibleConfigPaths = [
  path.join(process.cwd(), '..', 'config.yaml'),  // Parent of frontend/
  path.join(process.cwd(), 'config.yaml'),  // Current directory (unlikely)
];

// Find config.ts in current directory
const configTsPath = path.join(process.cwd(), 'config.ts');

let configPath = null;
for (const possiblePath of possibleConfigPaths) {
  if (fs.existsSync(possiblePath)) {
    configPath = possiblePath;
    break;
  }
}

// If config.yaml doesn't exist, exit gracefully (Vercel scenario)
if (!configPath) {
  // config.ts is already committed, and env vars will override defaults
  process.exit(0);
}

// Try to load js-yaml from node_modules
const nodeModulesPath = path.join(process.cwd(), 'node_modules');
const yamlPath = path.join(nodeModulesPath, 'js-yaml');

if (!fs.existsSync(yamlPath)) {
  // js-yaml not installed, exit gracefully
  process.exit(0);
}

try {
  const yaml = require(yamlPath);
  const config = yaml.load(fs.readFileSync(configPath, 'utf8'));
  
  const configContent = `/**
 * Configuration for Nextflow Chat Assistant frontend.
 * Auto-generated from config.yaml - DO NOT EDIT MANUALLY
 * Run: node scripts/sync-config.js to regenerate
 * 
 * Values can be overridden via environment variables.
 */

// Default values from config.yaml (fallback if env vars not set)
const DEFAULT_CONFIG = {
  frontend: {
    api_url: ${JSON.stringify(config.frontend.api_url)},
    loading_messages: ${JSON.stringify(config.frontend.loading_messages)},
  },
  llm: {
    max_input_length: ${config.llm?.max_input_length},
  },
}

// API Configuration (env var overrides default)
export const API_URL = 
  process.env.NEXT_PUBLIC_API_URL || 
  DEFAULT_CONFIG.frontend.api_url

export const LOADING_MESSAGES: string[] = 
  process.env.NEXT_PUBLIC_LOADING_MESSAGES?.split(',') || DEFAULT_CONFIG.frontend.loading_messages

export const MAX_INPUT_LENGTH: number = 
  parseInt(process.env.NEXT_PUBLIC_MAX_INPUT_LENGTH || String(DEFAULT_CONFIG.llm.max_input_length), 10)
`;

  fs.writeFileSync(configTsPath, configContent, 'utf8');
} catch (error) {
  // Silently fail - config.ts is already committed
  process.exit(0);
}

