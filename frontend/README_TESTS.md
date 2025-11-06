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

Tests are located in `__tests__/page.test.tsx` and cover:

- **Rendering**: Header, welcome message, input, buttons
- **User interactions**: Sending messages, button states
- **API integration**: Fetch calls, error handling
- **Theme toggle**: Dark mode functionality
- **Error handling**: Network errors, fallback behavior

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

