# Frontend Tests

This directory contains tests for the Nextflow Chat Assistant frontend.

## Running Tests

### Prerequisites

Install dependencies:
```bash
npm install
```

Install test dependencies:
```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event jest jest-environment-jsdom
```

### Run All Tests

```bash
npm test
```

### Run Tests in Watch Mode

```bash
npm test -- --watch
```

### Run Tests with Coverage

```bash
npm test -- --coverage
```

## Test Structure

Tests are located in `__tests__/`:

- **page.test.tsx**: Main component tests
  - Rendering (header, welcome message, input, buttons)
  - User interactions (sending messages, button states)
  - API integration (fetch calls, error handling)
  - Theme toggle (dark mode functionality)
  - Citations display
  - Keyboard shortcuts (Enter to send)

- **config.test.ts**: Configuration tests
  - All config values are defined
  - Type validation
  - URL building functions
  - Default values

## Configuration

Add to `package.json`:

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch"
  },
  "jest": {
    "testEnvironment": "jsdom",
    "setupFilesAfterEnv": ["<rootDir>/jest.setup.js"]
  }
}
```

Create `jest.setup.js`:

```javascript
import '@testing-library/jest-dom'
```

## Notes

- Tests use mocked fetch to avoid actual API calls
- localStorage is mocked for theme persistence tests
- Some tests may require additional mocking for Next.js specific features

