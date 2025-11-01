"""
AI-Powered Web Testing with OpenAI and Playwright
Uses GPT-4 to intelligently interact with web pages
"""

import asyncio
import json
import os
import sys
from playwright.async_api import async_playwright
from openai import OpenAI
from dotenv import load_dotenv

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

load_dotenv()

BASE_URL = "http://localhost:8080"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def get_page_info(page):
    """Extract page structure for AI analysis"""
    return await page.evaluate("""
        () => {
            const forms = Array.from(document.querySelectorAll('form')).map(form => ({
                action: form.action,
                method: form.method,
                fields: Array.from(form.querySelectorAll('input, select, textarea')).map(field => ({
                    type: field.type,
                    name: field.name,
                    id: field.id,
                    placeholder: field.placeholder,
                    required: field.required
                }))
            }));
            
            const buttons = Array.from(document.querySelectorAll('button, input[type="submit"]')).map(btn => ({
                text: btn.textContent || btn.value,
                type: btn.type,
                disabled: btn.disabled
            }));
            
            const links = Array.from(document.querySelectorAll('a')).map(link => ({
                text: link.textContent,
                href: link.href
            }));
            
            return {
                title: document.title,
                url: window.location.href,
                forms,
                buttons,
                links: links.slice(0, 10)  // Limit to first 10 links
            };
        }
    """)


def ask_ai_what_to_do(page_info, goal):
    """Ask AI to decide what actions to take"""
    prompt = f"""
You are a web testing AI. Analyze this page and provide test actions.

GOAL: {goal}

PAGE INFORMATION:
{json.dumps(page_info, indent=2)}

Provide a JSON response with actions to take. Format:
{{
  "analysis": "Brief analysis of the page",
  "actions": [
    {{"type": "fill", "selector": "#fieldId", "value": "test value"}},
    {{"type": "select", "selector": "#selectId", "value": "option"}},
    {{"type": "check", "selector": "#checkboxId"}},
    {{"type": "click", "selector": "button[type='submit']"}},
    {{"type": "wait", "ms": 1000}}
  ],
  "expected_result": "What should happen after these actions"
}}

Return ONLY valid JSON, no markdown or explanation.
"""
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    
    content = response.choices[0].message.content.strip()
    
    # Remove markdown code blocks if present
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        content = content.rsplit("```", 1)[0]
    
    return json.loads(content)


async def execute_ai_actions(page, actions):
    """Execute the actions suggested by AI"""
    for action in actions:
        action_type = action["type"]
        print(f"   Executing: {action}")
        
        if action_type == "fill":
            await page.fill(action["selector"], action["value"])
        elif action_type == "select":
            await page.select_option(action["selector"], action["value"])
        elif action_type == "check":
            await page.check(action["selector"])
        elif action_type == "click":
            await page.click(action["selector"])
        elif action_type == "wait":
            await asyncio.sleep(action["ms"] / 1000)
        
        await asyncio.sleep(0.5)  # Small delay between actions


async def ai_test_page(page, url, goal):
    """AI-powered testing of a page"""
    print(f"\n🤖 AI Testing: {url}")
    print(f"   Goal: {goal}")
    
    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    
    # Get page info
    page_info = await get_page_info(page)
    print(f"   Page: {page_info['title']}")
    
    # Ask AI what to do
    print(f"   🧠 Consulting AI...")
    ai_response = ask_ai_what_to_do(page_info, goal)
    
    print(f"   Analysis: {ai_response['analysis']}")
    print(f"   Planned actions: {len(ai_response['actions'])}")
    
    # Execute actions
    print(f"   ⚙️ Executing AI-generated actions...")
    await execute_ai_actions(page, ai_response["actions"])
    
    print(f"   ✅ Expected: {ai_response['expected_result']}")
    
    return ai_response


async def run_ai_demo():
    """Run AI-powered testing demo"""
    print("="*60)
    print("🤖 AI-POWERED WEB TESTING DEMO")
    print("="*60)
    print("\nUsing GPT-4 to intelligently test JSP pages...")
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERROR: OPENAI_API_KEY not found in environment")
        print("   Create a .env file with: OPENAI_API_KEY=your_key_here")
        return
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        try:
            # Test 1: Registration form
            await ai_test_page(
                page,
                f"{BASE_URL}/registration",
                "Fill out the registration form with realistic test data and submit it"
            )
            
            await asyncio.sleep(3)
            
            # Test 2: Workflow
            await ai_test_page(
                page,
                f"{BASE_URL}/workflow",
                "Select a product to purchase"
            )
            
            print("\n" + "="*60)
            print("🎉 AI Demo Complete!")
            print("="*60)
            print(f"\nView results at:")
            print(f"   {BASE_URL}/admin/registrations")
            print(f"   {BASE_URL}/admin/orders")
            
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(run_ai_demo())

