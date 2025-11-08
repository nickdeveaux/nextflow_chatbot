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
  llm: {
    max_input_length: 500000,
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
