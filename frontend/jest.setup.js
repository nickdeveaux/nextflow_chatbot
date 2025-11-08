// Learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom'

// Mock react-markdown and related modules (ES modules)
jest.mock('react-markdown', () => {
  const React = require('react')
  return function ReactMarkdown({ children }) {
    return React.createElement('div', { 'data-testid': 'react-markdown' }, children)
  }
})

jest.mock('remark-gfm', () => () => {})
jest.mock('rehype-raw', () => () => {})

// Mock window.matchMedia for dark mode tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock scrollIntoView for message scrolling
Element.prototype.scrollIntoView = jest.fn()

