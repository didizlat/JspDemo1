# JSP Demo Application

A Spring Boot JSP demonstration application with comprehensive forms and interactive workflows for testing browser automation.

## Features

- **User Registration Form** - Complete form with multiple input types (text, email, date, select, radio, checkbox, textarea)
- **Multi-Step Workflow** - 4-step interactive process with product selection and order completion
- **Form Validation** - Client-side and server-side validation with error messages
- **Responsive Design** - Mobile, tablet, and desktop layouts
- **Playwright Tests** - Automated browser testing suite

## Getting Started

### Prerequisites

- Java 17 or higher
- Node.js 18+ (for UI tests)

### Running the Application

```bash
# Start the Spring Boot server
.\mvnw.cmd spring-boot:run
```

The application will be available at: http://localhost:8080

### Available Pages

- **Homepage**: http://localhost:8080
- **Registration Form**: http://localhost:8080/registration
- **Multi-Step Workflow**: http://localhost:8080/workflow
- **Login Form**: http://localhost:8080/login

## Testing

See [TESTING.md](TESTING.md) for detailed testing instructions.

### Quick Start - UI Tests

```bash
cd ui-tests
npm install
npx playwright install
npm test
```

## Project Structure

```
JspDemo1/
├── src/
│   └── main/
│       ├── java/com/example/demo/
│       │   ├── JspDemoApplication.java
│       │   ├── HomeController.java
│       │   └── FormController.java
│       ├── resources/
│       │   └── application.properties
│       └── webapp/WEB-INF/jsp/
│           ├── index.jsp
│           ├── login.jsp
│           ├── registration.jsp
│           ├── registration-success.jsp
│           ├── workflow-step1.jsp
│           ├── workflow-step2.jsp
│           ├── workflow-step3.jsp
│           └── workflow-complete.jsp
├── ui-tests/
│   ├── tests/
│   │   ├── form.spec.ts
│   │   ├── workflow.spec.ts
│   │   ├── responsive.spec.ts
│   │   ├── errors.spec.ts
│   │   └── helpers/console.ts
│   ├── playwright.config.ts
│   └── package.json
├── pom.xml
├── TESTING.md
└── README.md
```

## Technology Stack

- **Backend**: Spring Boot 3.2.0, Java 17
- **View**: JSP with embedded Tomcat Jasper
- **Build**: Maven
- **Testing**: Playwright (TypeScript)
- **Styling**: Modern CSS with responsive design

## License

ISC

