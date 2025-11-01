# UI Tests (Playwright)

Automated UI tests for filling forms, clicking through workflows, testing responsive designs, validating error messages, and failing on JavaScript console errors.

## Prerequisites
- Node.js 18+
- App running locally and reachable (default `http://localhost:8080`)

## Install (already done by setup)
```
npm i
npx playwright install
```

## Quick start
- Base URL defaults to `http://localhost:8080`. Override with `BASE_URL`.
- Targeted paths are controlled by environment variables per test.

### Run all tests
```
npm test
```

### Headed mode
```
npm run test:headed
```

### UI mode (debugger)
```
npm run test:ui
```

### Show last HTML report
```
npm run report
```

## Environment variables
- `BASE_URL` (default `http://localhost:8080`)
- `FORM_PATH` (e.g. `/login` or full URL) — enables form tests
- `WORKFLOW_START_PATH` (e.g. `/checkout`) — enables workflow tests
- `RESPONSIVE_PATH` (defaults to `/`) — page used for responsive screenshots
- `ERROR_PAGE_PATH` (e.g. `/signup`) — enables validation/error tests

## Notes
- Tests automatically fail if any `console.error` occurs on the page.
- Selectors are generic and may need refinement for your app; adjust as needed in the spec files.
- Screenshots are saved under `tests/screenshots`.
