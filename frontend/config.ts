/**
 * Configuration for Nextflow Chat Assistant frontend.
 * Auto-generated from config.yaml - DO NOT EDIT MANUALLY
 * Run: node scripts/sync-config.js to regenerate
 * 
 * Values can be overridden via environment variables.
 */

// Default values from config.yaml (fallback if env vars not set)
const DEFAULT_CONFIG = {
  api: {
    google_vertex_api_key: "REMOVED",
    gemini_api_base_url: "https://generativelanguage.googleapis.com/v1beta",
    gemini_model: "gemini-2.0-flash-exp",
  },
  frontend: {
    api_url: "http://localhost:8000",
    loading_messages: ["Thinking","Pondering","Noodling","Considering","Examining","Researching","Reflecting","Evaluating","Deliberating"],
  },
  system_prompt: "You are a helpful Nextflow documentation assistant. You answer questions about Nextflow with accuracy and clarity.\n\nNextflow is a workflow management system for data-intensive computational pipelines. It enables scalable and reproducible scientific workflows using a simple DSL (Domain-Specific Language).\n\nFocus on:\n- 70% documentation Q&A about Nextflow features, syntax, and capabilities\n- 30% pragmatic troubleshooting guidance\n\nWhen you have relevant context from documentation, use it. When something is unknown, be transparent and suggest how to verify it (e.g., check the docs at https://www.nextflow.io/docs/latest/).\n\nKeep responses concise but informative. If asked for citations, provide them.\n",
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
  return `${GEMINI_API_BASE_URL}/models/${GEMINI_MODEL}:generateContent?key=${GOOGLE_VERTEX_API_KEY}`
}
