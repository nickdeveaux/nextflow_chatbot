/**
 * Configuration for Nextflow Chat Assistant frontend.
 * Auto-generated from config.yaml - DO NOT EDIT MANUALLY
 * Run: node scripts/sync-config.js to regenerate
 * 
 * Values can be overridden via environment variables.
 */

// Default values from config.yaml (fallback if env vars not set)
const DEFAULT_CONFIG = {
  frontend: {
    api_url: "http://localhost:8000",
    loading_messages: ["Thinking","Pondering","Noodling","Considering","Examining","Researching","Reflecting","Evaluating","Deliberating"],
  },
}

// API Configuration (env var overrides default)
export const API_URL = 
  process.env.NEXT_PUBLIC_API_URL || 
  DEFAULT_CONFIG.frontend.api_url

// Loading Messages (from config, can be overridden via env)
export const LOADING_MESSAGES: string[] = 
  (process.env.NEXT_PUBLIC_LOADING_MESSAGES 
    ? process.env.NEXT_PUBLIC_LOADING_MESSAGES.split(',')
    : DEFAULT_CONFIG.frontend.loading_messages)
