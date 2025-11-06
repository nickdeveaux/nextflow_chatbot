/**
 * Script to sync config.yaml values to frontend config.ts
 * Run with: node scripts/sync-config.js
 * 
 * This ensures frontend config stays in sync with the shared YAML file.
 */
const fs = require('fs');
const path = require('path');

// Use frontend's node_modules for js-yaml
const frontendNodeModules = path.join(__dirname, '..', 'frontend', 'node_modules');
const yaml = require(path.join(frontendNodeModules, 'js-yaml'));

const configPath = path.join(__dirname, '..', 'config.yaml');
const frontendConfigPath = path.join(__dirname, '..', 'frontend', 'config.ts');

try {
  // Read YAML config
  const config = yaml.load(fs.readFileSync(configPath, 'utf8'));
  
  // Generate frontend config content
  const configContent = `/**
 * Configuration for Nextflow Chat Assistant frontend.
 * Auto-generated from config.yaml - DO NOT EDIT MANUALLY
 * Run: node scripts/sync-config.js to regenerate
 * 
 * Values can be overridden via environment variables.
 */

// Default values from config.yaml (fallback if env vars not set)
const DEFAULT_CONFIG = {
  api: {
    google_vertex_api_key: ${JSON.stringify(config.api.google_vertex_api_key)},
    gemini_api_base_url: ${JSON.stringify(config.api.gemini_api_base_url)},
    gemini_model: ${JSON.stringify(config.api.gemini_model)},
  },
  frontend: {
    api_url: ${JSON.stringify(config.frontend.api_url)},
    loading_messages: ${JSON.stringify(config.frontend.loading_messages)},
  },
  system_prompt: ${JSON.stringify(config.system_prompt)},
}

// API Configuration (env var overrides default)
export const API_URL = 
  process.env.NEXT_PUBLIC_API_URL || 
  DEFAULT_CONFIG.frontend.api_url

export const GOOGLE_VERTEX_API_KEY = 
  process.env.NEXT_PUBLIC_GOOGLE_VERTEX_API_KEY || 
  DEFAULT_CONFIG.api.google_vertex_api_key

// Gemini API Configuration (env var overrides default)
export const GEMINI_API_BASE_URL = 
  process.env.NEXT_PUBLIC_GEMINI_API_BASE_URL || 
  DEFAULT_CONFIG.api.gemini_api_base_url

export const GEMINI_MODEL = 
  process.env.NEXT_PUBLIC_GEMINI_MODEL || 
  DEFAULT_CONFIG.api.gemini_model

// Loading Messages (from config, can be overridden via env)
export const LOADING_MESSAGES: string[] = 
  (process.env.NEXT_PUBLIC_LOADING_MESSAGES 
    ? process.env.NEXT_PUBLIC_LOADING_MESSAGES.split(',')
    : DEFAULT_CONFIG.frontend.loading_messages)

// System Prompt (from config)
export const SYSTEM_PROMPT = 
  process.env.NEXT_PUBLIC_SYSTEM_PROMPT || 
  DEFAULT_CONFIG.system_prompt

// Helper function to build Gemini API URL
export function getGeminiApiUrl(): string {
  return \`\${GEMINI_API_BASE_URL}/models/\${GEMINI_MODEL}:generateContent?key=\${GOOGLE_VERTEX_API_KEY}\`
}
`;

  // Write to frontend config
  fs.writeFileSync(frontendConfigPath, configContent, 'utf8');
  console.log('✓ Frontend config synced from config.yaml');
} catch (error) {
  console.error('Error syncing config:', error);
  process.exit(1);
}

