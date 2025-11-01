# Database Tracking Guide

## Overview

The JSP Demo now includes **H2 in-memory database** with full tracking of:
- ✅ User registrations
- ✅ Product orders
- ✅ Timestamps for all records

## Database Pages

### 1. **View All Registrations**
**URL**: http://localhost:8080/admin/registrations

Shows all registered users with:
- ID, Name, Email, Phone
- Country, Birthdate, Gender
- Interests selected
- Newsletter subscription status
- Registration timestamp

**Stats displayed**:
- Total registrations count
- Newsletter subscribers count

### 2. **View All Orders**
**URL**: http://localhost:8080/admin/orders

Shows all completed orders with:
- Order ID and Order Number
- Product name with icon
- Quantity ordered
- Order status
- Order timestamp

**Stats displayed**:
- Total orders count
- Total items ordered

### 3. **H2 Database Console** (Advanced)
**URL**: http://localhost:8080/h2-console

Direct SQL access to the database.

**Connection settings**:
- **JDBC URL**: `jdbc:h2:mem:jspdemo`
- **Username**: `sa`
- **Password**: (leave empty)
- **Driver Class**: `org.h2.Driver`

**Tables**:
- `REGISTRATIONS` - User registration data
- `ORDERS` - Order data

## How Data is Saved

### Registration Form (`/registration`)

When you submit the registration form, the following data is saved:

```java
Registration Entity:
- id (auto-generated)
- firstName
- lastName  
- email
- phone
- birthdate
- gender
- country
- interests (comma-separated)
- comments
- newsletter (boolean)
- registeredAt (auto-timestamp)
```

### Workflow Orders (`/workflow`)

When you complete the 4-step workflow, the following data is saved:

```java
Order Entity:
- id (auto-generated)
- orderNumber (e.g., "ORD-45231")
- product (laptop, phone, tablet, watch)
- quantity
- status (default: "Confirmed")
- orderedAt (auto-timestamp)
```

## Testing the Database

### Scenario 1: Register Multiple Users

1. Go to http://localhost:8080/registration
2. Fill out the form with different user data
3. Submit the form
4. Click "View All Registrations" on success page
5. See all registered users in the table

### Scenario 2: Create Multiple Orders

1. Go to http://localhost:8080/workflow
2. Select a product (Laptop, Phone, Tablet, Watch)
3. Enter quantity
4. Complete the workflow
5. Click "View All Orders" on completion page
6. See all orders with product icons and quantities

### Scenario 3: Using Playwright to Populate Database

Run the Playwright tests to automatically fill forms and create test data:

```bash
cd ui-tests

# Register 3 users (run test 3 times on different browsers)
cross-env FORM_PATH=/registration BASE_URL=http://localhost:8080 npm test -- tests/form.spec.ts

# Create 3 orders (run test 3 times)
cross-env WORKFLOW_START_PATH=/workflow BASE_URL=http://localhost:8080 npm test -- tests/workflow.spec.ts
```

After tests run, check:
- http://localhost:8080/admin/registrations
- http://localhost:8080/admin/orders

## Database Lifecycle

**Important**: The H2 database is **in-memory** only. This means:

✅ **During Server Run**:
- All data persists
- You can register users and create orders
- View data anytime at admin pages

❌ **When Server Restarts**:
- All data is cleared
- Database recreates tables from scratch
- Fresh start with empty tables

This is perfect for testing since you always start clean!

## SQL Queries (H2 Console)

Access http://localhost:8080/h2-console and try:

```sql
-- View all registrations
SELECT * FROM REGISTRATIONS ORDER BY REGISTERED_AT DESC;

-- Count registrations by country
SELECT COUNTRY, COUNT(*) as count 
FROM REGISTRATIONS 
GROUP BY COUNTRY;

-- View all orders
SELECT * FROM ORDERS ORDER BY ORDERED_AT DESC;

-- Count orders by product
SELECT PRODUCT, SUM(QUANTITY) as total_quantity 
FROM ORDERS 
GROUP BY PRODUCT;

-- Total items ordered
SELECT SUM(QUANTITY) as total_items FROM ORDERS;

-- Newsletter subscribers
SELECT COUNT(*) as subscribers 
FROM REGISTRATIONS 
WHERE NEWSLETTER = TRUE;
```

## Logging

SQL queries are logged to the console (check your terminal running the server). You'll see:

```
Hibernate: insert into registrations (...) values (...)
Hibernate: select * from registrations order by registered_at desc
```

This helps you understand what's happening in the database.

## Integration with Cursor Browser Testing

When Cursor's browser interface fills out forms:

1. **Registration Form** - Each submission creates a new `Registration` record
2. **Workflow** - Each completion creates a new `Order` record
3. **Admin Pages** - You can see the results immediately
4. **Console Errors** - Monitored by Playwright tests

**Perfect Testing Flow**:
1. Start server: `.\mvnw.cmd spring-boot:run`
2. Run Playwright tests to populate data
3. Visit admin pages to verify data was saved
4. Check H2 console for SQL queries
5. Repeat with different test data

## Entity Details

### Registration Entity
Location: `src/main/java/com/example/demo/entity/Registration.java`

Fields stored:
- All form fields from registration page
- Auto-generated ID
- Auto-timestamp on creation

### Order Entity
Location: `src/main/java/com/example/demo/entity/Order.java`

Fields stored:
- Product and quantity from workflow
- Auto-generated order number
- Auto-generated ID
- Auto-timestamp on creation
- Default status: "Confirmed"

## Configuration

Database settings in `src/main/resources/application.properties`:

```properties
# H2 in-memory database
spring.datasource.url=jdbc:h2:mem:jspdemo
spring.datasource.username=sa
spring.datasource.password=

# Create tables on startup, drop on shutdown
spring.jpa.hibernate.ddl-auto=create-drop

# Show SQL in console
spring.jpa.show-sql=true

# Enable H2 console
spring.h2.console.enabled=true
```

## Summary

Now when you test with Cursor's browser interface or Playwright:
- ✅ Every form submission is saved to the database
- ✅ Every order completion is tracked
- ✅ You can view all data in real-time
- ✅ You can query the database directly
- ✅ Perfect for demonstrating end-to-end functionality!

