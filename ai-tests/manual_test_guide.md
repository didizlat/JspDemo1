# Manual Testing Guide for Persistent Database

## Test 1: Create User Registration

1. **Open browser** and go to: http://localhost:8080/registration

2. **Fill in the form:**
   - First Name: John
   - Last Name: Doe
   - Email: john.doe@test.com
   - Phone: +1-555-0101
   - Country: United States
   - Gender: Male
   - Interests: Check "Technology"
   - Comments: "Test user for persistence"
   - Newsletter: Check it

3. **Click "Register" button**

4. **You should see success page**

5. **Check admin page:**
   - Go to: http://localhost:8080/admin/registrations
   - You should see John Doe in the table

## Test 2: Create Order

1. **Open browser** and go to: http://localhost:8080/workflow

2. **Step 1 - Select Product:**
   - Click on "Laptop" card
   - Click "Continue to Next Step"

3. **Step 2 - Enter Quantity:**
   - Enter: 2
   - Click "Continue to Review"

4. **Step 3 - Review:**
   - Verify: Laptop, Quantity 2
   - Click "Confirm and Complete Order"

5. **You should see completion page with order number**

6. **Check admin page:**
   - Go to: http://localhost:8080/admin/orders
   - You should see your Laptop order

## Test 3: Verify Persistence

1. **Stop the server** (Ctrl+C in terminal)

2. **Check database file exists:**
   ```
   dir C:\Users\dylan\CursorProjects\JspDemo1\data
   ```
   You should see: jspdemo.mv.db

3. **Restart the server:**
   ```
   cd C:\Users\dylan\CursorProjects\JspDemo1
   .\mvnw.cmd spring-boot:run
   ```

4. **Check data still exists:**
   - http://localhost:8080/admin/registrations (John Doe still there?)
   - http://localhost:8080/admin/orders (Laptop order still there?)

5. **✅ If yes: DATABASE IS PERSISTENT!**

## Test 4: Reset Database

1. **Run reset script:**
   ```
   reset-database.bat
   ```

2. **Restart server:**
   ```
   .\mvnw.cmd spring-boot:run
   ```

3. **Check admin pages - should be empty:**
   - http://localhost:8080/admin/registrations (empty)
   - http://localhost:8080/admin/orders (empty)

4. **✅ Database successfully reset!**

## Quick SQL Test

1. **Go to:** http://localhost:8080/h2-console

2. **Connect:**
   - JDBC URL: `jdbc:h2:file:./data/jspdemo`
   - Username: `sa`
   - Password: (leave empty)
   - Click "Connect"

3. **Run queries:**
   ```sql
   -- Count registrations
   SELECT COUNT(*) FROM REGISTRATIONS;
   
   -- See all users
   SELECT * FROM REGISTRATIONS;
   
   -- Count orders
   SELECT COUNT(*) FROM ORDERS;
   
   -- See all orders
   SELECT * FROM ORDERS;
   ```

This confirms the database is working!

