"""
Demo: Automated JSP Testing with Playwright
Simulates multiple users registering and purchasing items
"""

import asyncio
import random
import sys
from playwright.async_api import async_playwright
from faker import Faker

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

fake = Faker()

BASE_URL = "http://localhost:8080"

# Sample test data
PRODUCTS = ["laptop", "phone", "tablet", "watch"]
COUNTRIES = ["us", "ca", "uk", "au", "de", "fr", "jp"]
GENDERS = ["male", "female", "other", "prefer-not"]
INTERESTS = ["technology", "sports", "music", "travel", "reading"]


async def register_user(page, user_num):
    """Simulate a user registration"""
    print(f"\n🔹 User #{user_num}: Starting registration...")
    
    await page.goto(f"{BASE_URL}/registration")
    await page.wait_for_load_state("networkidle")
    
    # Fill form with fake data
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = f"{first_name.lower()}.{last_name.lower()}@example.com"
    
    print(f"   Filling form for {first_name} {last_name}")
    
    await page.fill("#firstName", first_name)
    await page.fill("#lastName", last_name)
    await page.fill("#email", email)
    await page.fill("#phone", fake.phone_number())
    
    # Select random country
    country = random.choice(COUNTRIES)
    await page.select_option("#country", country)
    
    # Select random gender
    gender = random.choice(GENDERS)
    await page.click(f'input[name="gender"][value="{gender}"]')
    
    # Check random interests (1-3)
    num_interests = random.randint(1, 3)
    selected_interests = random.sample(INTERESTS, num_interests)
    for interest in selected_interests:
        await page.check(f'input[name="interests"][value="{interest}"]')
    
    # Add comment
    await page.fill("#comments", f"Test user created by automation #{user_num}")
    
    # Maybe subscribe to newsletter
    if random.choice([True, False]):
        await page.check("#newsletter")
    
    # Submit
    print(f"   Submitting registration...")
    await page.click('button[type="submit"]')
    
    # Wait for success page
    await page.wait_for_url("**/registration-success", timeout=10000)
    print(f"   ✅ Registration successful for {first_name} {last_name}")
    
    return {"name": f"{first_name} {last_name}", "email": email}


async def create_order(page, user_num):
    """Simulate a purchase workflow"""
    print(f"\n🔹 User #{user_num}: Starting purchase workflow...")
    
    # Step 1: Select product
    await page.goto(f"{BASE_URL}/workflow")
    await page.wait_for_load_state("networkidle")
    
    product = random.choice(PRODUCTS)
    print(f"   Selecting product: {product}")
    
    # Click on the product card using a more specific selector
    await page.click(f'.product-card:has-text("{product.capitalize()}")')
    await asyncio.sleep(0.5)  # Wait for UI update
    
    # Click continue button
    await page.click('button[type="submit"]')
    
    # Step 2: Enter quantity
    await page.wait_for_url("**/workflow/step2")
    quantity = random.randint(1, 5)
    print(f"   Setting quantity: {quantity}")
    
    await page.fill('#quantity', str(quantity))
    await page.click('button[type="submit"]')
    
    # Step 3: Review
    await page.wait_for_url("**/workflow/step3")
    print(f"   Reviewing order...")
    await asyncio.sleep(0.5)
    
    await page.click('button[type="submit"]')
    
    # Step 4: Complete
    await page.wait_for_url("**/workflow-complete")
    
    # Extract order number
    order_number = await page.locator('.order-number').text_content()
    print(f"   ✅ Order completed: {order_number}")
    
    return {"product": product, "quantity": quantity, "order_number": order_number}


async def run_demo(num_users=3, num_orders=3):
    """Run the complete demo"""
    print("="*60)
    print("🤖 AUTOMATED JSP TESTING DEMO")
    print("="*60)
    print(f"\nSimulating {num_users} user registrations and {num_orders} purchases...")
    
    async with async_playwright() as p:
        # Launch browser in headed mode so you can see it
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        
        registrations = []
        orders = []
        
        # Register multiple users
        print("\n" + "="*60)
        print("PHASE 1: USER REGISTRATIONS")
        print("="*60)
        
        for i in range(1, num_users + 1):
            page = await browser.new_page()
            try:
                user_data = await register_user(page, i)
                registrations.append(user_data)
                await asyncio.sleep(1)
            except Exception as e:
                print(f"   ❌ Registration failed: {e}")
            finally:
                await page.close()
        
        # Create multiple orders
        print("\n" + "="*60)
        print("PHASE 2: PURCHASE ORDERS")
        print("="*60)
        
        for i in range(1, num_orders + 1):
            page = await browser.new_page()
            try:
                order_data = await create_order(page, i)
                orders.append(order_data)
                await asyncio.sleep(1)
            except Exception as e:
                print(f"   ❌ Order failed: {e}")
            finally:
                await page.close()
        
        # Summary
        print("\n" + "="*60)
        print("📊 DEMO SUMMARY")
        print("="*60)
        print(f"\n✅ Registered {len(registrations)} users:")
        for reg in registrations:
            print(f"   • {reg['name']} ({reg['email']})")
        
        print(f"\n✅ Created {len(orders)} orders:")
        for order in orders:
            print(f"   • {order['order_number']}: {order['quantity']}x {order['product']}")
        
        print("\n" + "="*60)
        print("🔍 VIEW RESULTS AT:")
        print("="*60)
        print(f"   Registrations: {BASE_URL}/admin/registrations")
        print(f"   Orders:        {BASE_URL}/admin/orders")
        print(f"   H2 Console:    {BASE_URL}/h2-console")
        
        # Open admin pages
        admin_page = await browser.new_page()
        await admin_page.goto(f"{BASE_URL}/admin/registrations")
        print("\n✨ Opening admin dashboard...")
        await asyncio.sleep(3)
        
        await admin_page.goto(f"{BASE_URL}/admin/orders")
        await asyncio.sleep(3)
        
        print("\n🎉 Demo complete! Browser will close in 5 seconds...")
        await asyncio.sleep(5)
        
        await browser.close()


if __name__ == "__main__":
    # Run demo: 5 registrations, 5 orders
    asyncio.run(run_demo(num_users=5, num_orders=5))

