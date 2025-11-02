"""
Populate database with test data using direct HTTP requests
"""
import requests
from faker import Faker
import time

fake = Faker()
BASE_URL = "http://localhost:8080"

def create_registration(num):
    """Create a registration via HTTP POST"""
    data = {
        'firstName': fake.first_name(),
        'lastName': fake.last_name(),
        'email': fake.email(),
        'phone': fake.phone_number(),
        'country': 'us',
        'gender': 'male',
        'interests': ['technology', 'sports'],
        'comments': f'Test user #{num} created via API',
        'newsletter': 'yes'
    }
    
    response = requests.post(f"{BASE_URL}/registration", data=data)
    return response.status_code == 200

def create_order(product, quantity):
    """Create an order via HTTP POST (multi-step)"""
    session = requests.Session()
    
    # Step 1: Select product
    response = session.post(f"{BASE_URL}/workflow/step2", data={'product': product})
    if response.status_code != 200:
        return False
    
    # Step 2: Set quantity
    response = session.post(f"{BASE_URL}/workflow/step3", data={'product': product, 'quantity': quantity})
    if response.status_code != 200:
        return False
    
    # Step 3: Complete
    response = session.post(f"{BASE_URL}/workflow/complete", data={'product': product, 'quantity': quantity})
    return response.status_code == 200

print("="*60)
print("DATABASE POPULATION SCRIPT")
print("="*60)
print()

# Create registrations
print("Creating 5 user registrations...")
success_count = 0
for i in range(1, 6):
    print(f"  [{i}/5] Creating user...", end=" ")
    if create_registration(i):
        print("✅")
        success_count += 1
    else:
        print("❌")
    time.sleep(0.5)

print(f"\n✅ Created {success_count} registrations\n")

# Create orders
print("Creating 5 orders...")
products = ['laptop', 'phone', 'tablet', 'watch', 'laptop']
order_count = 0
for i, product in enumerate(products, 1):
    print(f"  [{i}/5] Creating {product} order...", end=" ")
    if create_order(product, i):
        print("✅")
        order_count += 1
    else:
        print("❌")
    time.sleep(0.5)

print(f"\n✅ Created {order_count} orders\n")

print("="*60)
print("RESULTS")
print("="*60)
print(f"✅ Registrations: {success_count}/5")
print(f"✅ Orders: {order_count}/5")
print()
print("View results at:")
print(f"  {BASE_URL}/admin/registrations")
print(f"  {BASE_URL}/admin/orders")
print("="*60)

