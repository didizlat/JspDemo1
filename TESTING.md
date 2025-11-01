# Testing Guide

## Running the Application

Start the Spring Boot server:
```bash
.\mvnw.cmd spring-boot:run
```

The app will be available at: **http://localhost:8080**

## Available Pages for Testing

### 1. Registration Form (`/registration`)
**Perfect for form testing!**

- **URL**: http://localhost:8080/registration
- **Features**:
  - Text inputs (first name, last name)
  - Email input with validation
  - Phone number input
  - Date picker
  - Dropdown (country selection)
  - Radio buttons (gender)
  - Multiple checkboxes (interests)
  - Textarea (comments)
  - Newsletter checkbox
  - Form validation with error messages
  - Client-side JavaScript validation
  - Responsive design

**Test with Playwright:**
```bash
cd ui-tests
cross-env FORM_PATH=/registration BASE_URL=http://localhost:8080 npm test -- tests/form.spec.ts
cross-env ERROR_PAGE_PATH=/registration BASE_URL=http://localhost:8080 npm test -- tests/errors.spec.ts
```

### 2. Multi-Step Workflow (`/workflow`)
**Perfect for workflow testing!**

- **URL**: http://localhost:8080/workflow
- **Features**:
  - 4-step process with progress indicator
  - Step 1: Product selection (clickable cards)
  - Step 2: Quantity input with +/- buttons
  - Step 3: Review page
  - Step 4: Completion page
  - Navigation between steps
  - Form validation at each step
  - Disabled/enabled button states

**Test with Playwright:**
```bash
cd ui-tests
cross-env WORKFLOW_START_PATH=/workflow BASE_URL=http://localhost:8080 npm test -- tests/workflow.spec.ts
```

### 3. Login Form (`/login`)
**Simple validation testing**

- **URL**: http://localhost:8080/login
- **Features**:
  - Username and password fields
  - Required field validation
  - Error display

### 4. Responsive Design Testing

All pages are fully responsive. Test across devices:

```bash
cd ui-tests
cross-env RESPONSIVE_PATH=/registration BASE_URL=http://localhost:8080 npm test -- tests/responsive.spec.ts
```

This will capture screenshots at:
- Desktop (1280x800)
- Tablet (768x1024)
- Mobile (390x844)

## Run All Tests

```bash
cd ui-tests
cross-env BASE_URL=http://localhost:8080 FORM_PATH=/registration WORKFLOW_START_PATH=/workflow ERROR_PAGE_PATH=/registration npm test
```

## Console Error Monitoring

All tests automatically monitor for JavaScript console errors and fail if any are detected. The pages include intentional `console.log` statements (which are OK) but no `console.error` calls.

## Test Data

Use these sample values for testing:

**Registration Form:**
- First Name: John
- Last Name: Doe
- Email: john.doe@example.com
- Phone: +1 555-0100
- Country: United States
- Gender: Any option
- Interests: Check any boxes
- Comments: Any text

**Workflow:**
- Select any product (Laptop, Phone, Tablet, Watch)
- Enter quantity: 1-99
- Review and confirm

## Expected Behaviors

### Validation Errors (Test These!)

1. **Registration**: Submit empty → "First name is required"
2. **Registration**: Invalid email → "Valid email is required"
3. **Workflow Step 1**: Click continue without selection → "Please select a product"
4. **Workflow Step 2**: Submit empty quantity → "Please enter quantity"
5. **Workflow Step 2**: Submit 0 or negative → "Quantity must be at least 1"

### Success Flows

1. **Registration**: Fill required fields → Success page with confirmation
2. **Workflow**: Complete all 4 steps → Order complete with order number
3. **Login**: Fill username and password → Welcome page

## Debugging

### View test results:
```bash
cd ui-tests
npm run report
```

### Run tests in headed mode (see browser):
```bash
cd ui-tests
npm run test:headed
```

### Run tests in UI mode (interactive debugger):
```bash
cd ui-tests
npm run test:ui
```

## What to Test with Browser Interface

✅ **Form Filling**: All input types (text, email, tel, date, select, radio, checkbox, textarea)  
✅ **Workflows**: Multi-step process with navigation  
✅ **Validation**: Empty submit, invalid data, error messages  
✅ **Responsive**: Mobile, tablet, desktop layouts  
✅ **Console Errors**: JavaScript error detection  
✅ **Interactive Controls**: Buttons, links, clickable cards  
✅ **Dynamic Updates**: Button enable/disable, card selection  

