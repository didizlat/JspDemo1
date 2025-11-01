# AI-Powered Testing with Python + Playwright

Python-based automation for testing JSP pages with both traditional and AI-powered approaches.

## Setup

### 1. Install Python Dependencies

```bash
cd ai-tests
pip install -r requirements.txt
playwright install chromium
```

### 2. For AI Testing (Optional)

Create `.env` file:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Run Demos

### Demo 1: Traditional Automation

Simulates multiple users registering and purchasing items:

```bash
python demo_automation.py
```

**What it does**:
- Creates 5 fake users with realistic data (using Faker library)
- Registers them through the `/registration` form
- Creates 5 purchase orders through the `/workflow`
- Shows results in terminal
- Opens admin dashboards to show saved data
- Browser runs in headed mode so you can watch!

**Customization**:
```python
# Edit the last line to change numbers:
asyncio.run(run_demo(num_users=10, num_orders=15))
```

### Demo 2: AI-Powered Testing (Requires OpenAI API Key)

Uses GPT-4 to intelligently analyze pages and decide what to test:

```bash
python ai_testing.py
```

**What it does**:
- Visits each page
- Extracts page structure (forms, fields, buttons)
- Sends to GPT-4 for analysis
- GPT-4 decides what actions to take
- Executes AI-generated test actions
- Validates results

## Script Descriptions

### `demo_automation.py`

Traditional automated testing with predefined scenarios:

**Features**:
- Uses **Faker** library for realistic test data
- Random selection of products, countries, interests
- Parallel browser contexts
- Error handling and retry logic
- Summary reporting
- Visual browser mode (slow_mo=500ms)

**Test Data Generated**:
- Names: John Doe, Jane Smith, etc. (from Faker)
- Emails: Based on names
- Phone numbers: Realistic format
- Countries: Random from list
- Interests: 1-3 random selections
- Comments: With user number tag

### `ai_testing.py`

AI-powered testing using GPT-4:

**How it works**:
1. **Page Analysis**: JavaScript extracts all forms, fields, buttons, links
2. **AI Decision**: GPT-4 receives page structure and decides actions
3. **Action Execution**: Playwright executes AI-generated actions
4. **Validation**: Checks expected results

**AI Prompt Engineering**:
- Provides page context in JSON format
- Asks for specific action format
- Temperature: 0.7 (balanced creativity/consistency)
- Model: GPT-4 (better reasoning than GPT-3.5)

**Actions AI Can Generate**:
- `fill`: Fill input fields
- `select`: Choose dropdown options
- `check`: Check checkboxes/radios
- `click`: Click buttons/links
- `wait`: Pause between actions

## Advantages Over Playwright TypeScript Tests

### Python Tests

✅ **More flexible** - Dynamic test generation  
✅ **Better libraries** - Faker, NumPy, Pandas for data  
✅ **AI integration** - OpenAI, Anthropic, local LLMs  
✅ **Easier scripting** - Quick iteration  
✅ **Data analysis** - Built-in data science tools

### TypeScript Tests

✅ **Type safety** - Compile-time error catching  
✅ **Better IDE support** - IntelliSense, refactoring  
✅ **Playwright native** - Official language  
✅ **Faster execution** - V8 engine

## Extending with AI

### Use Case 1: Exploratory Testing

Let AI discover bugs by freely exploring:

```python
await ai_test_page(
    page,
    f"{BASE_URL}/",
    "Explore this website and find any broken links or forms that don't work"
)
```

### Use Case 2: Accessibility Testing

```python
await ai_test_page(
    page,
    f"{BASE_URL}/registration",
    "Check this form for accessibility issues like missing labels or keyboard navigation problems"
)
```

### Use Case 3: Visual Regression

```python
# AI analyzes screenshots
await page.screenshot(path="before.png")
# ... make changes ...
await page.screenshot(path="after.png")

# Ask AI: "Compare these screenshots and identify visual differences"
```

### Use Case 4: Test Generation

```python
# AI generates test scenarios
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{
        "role": "user",
        "content": "Generate 10 edge case test scenarios for a user registration form"
    }]
)
# Execute generated scenarios
```

## Advanced: Local LLM Integration

Replace OpenAI with local models:

```python
# Use Ollama, LM Studio, or HuggingFace
import ollama

response = ollama.chat(model='llama3', messages=[...])
```

**Benefits**:
- No API costs
- Data privacy
- Offline testing
- Faster for simple tasks

## Database Verification

After running tests, check the database:

```python
import requests

# Check registrations via API (add REST endpoints)
response = requests.get(f"{BASE_URL}/api/registrations")
assert len(response.json()) == expected_count
```

Or query H2 directly:

```python
import jaydebeapi

conn = jaydebeapi.connect(
    "org.h2.Driver",
    "jdbc:h2:mem:jspdemo",
    ["sa", ""],
    "h2.jar"
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM REGISTRATIONS")
count = cursor.fetchone()[0]
print(f"Registered users: {count}")
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run AI Tests
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    pip install -r ai-tests/requirements.txt
    python ai-tests/demo_automation.py
```

### Jenkins

```groovy
stage('AI Testing') {
    steps {
        sh 'python ai-tests/demo_automation.py'
    }
}
```

## Performance

**demo_automation.py**:
- 5 registrations: ~30 seconds
- 5 orders: ~40 seconds
- Total: ~70 seconds

**ai_testing.py**:
- Per page: ~5-10 seconds (includes AI API call)
- Depends on OpenAI API latency

## Tips

1. **Slow Motion**: Adjust `slow_mo` parameter to see actions clearly
2. **Headless**: Set `headless=True` for CI/CD
3. **Screenshots**: Add `await page.screenshot(path="test.png")` for debugging
4. **Videos**: Playwright records videos automatically on failure
5. **Parallel**: Use `asyncio.gather()` to run tests in parallel

## Next Steps

- Add REST API endpoints for programmatic data access
- Integrate with pytest for better test reporting
- Add Allure reports for beautiful test results
- Create test data factories with more scenarios
- Add performance testing with locust
- Implement visual regression testing
- Create custom AI prompts for your domain

