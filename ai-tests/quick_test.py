"""Quick test to populate database with sample data"""
import asyncio
import sys
import codecs
from playwright.async_api import async_playwright

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

async def create_test_data():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("Creating test users and orders...")
        
        # Create 3 registrations
        for i in range(1, 4):
            print(f"\n[{i}/3] Creating user...")
            await page.goto("http://localhost:8080/registration")
            await page.wait_for_load_state("networkidle")
            
            await page.fill("#firstName", f"TestUser{i}")
            await page.fill("#lastName", f"LastName{i}")
            await page.fill("#email", f"testuser{i}@example.com")
            await page.fill("#phone", f"+1-555-010{i}")
            await page.select_option("#country", "us")
            await page.check('input[name="interests"][value="technology"]')
            await page.fill("#comments", f"Test user #{i} created by automation")
            
            await page.click('button[type="submit"]')
            await page.wait_for_url("**/registration/success**", timeout=5000)
            print(f"   ✅ User {i} registered!")
            await asyncio.sleep(1)
        
        # Create 3 orders
        for i in range(1, 4):
            print(f"\n[{i}/3] Creating order...")
            await page.goto("http://localhost:8080/workflow")
            await page.wait_for_load_state("networkidle")
            
            # Click product card
            products = ["laptop", "phone", "tablet"]
            product = products[i-1]
            await page.click(f'.product-card:has-text("{product.capitalize()}")')
            await asyncio.sleep(0.5)
            await page.click('button#continueBtn')
            
            # Set quantity
            await page.wait_for_url("**/step2", timeout=5000)
            await page.fill("#quantity", str(i))
            await page.click('button[type="submit"]')
            
            # Review
            await page.wait_for_url("**/step3", timeout=5000)
            await page.click('button[type="submit"]')
            
            # Complete
            await page.wait_for_url("**/workflow/complete**", timeout=5000)
            print(f"   ✅ Order {i} created!")
            await asyncio.sleep(1)
        
        print("\n✅ Test data created successfully!")
        print("\nView at:")
        print("  http://localhost:8080/admin/registrations")
        print("  http://localhost:8080/admin/orders")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(create_test_data())

