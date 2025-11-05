# AI Visual Testing Framework (Scaffold)

This is the Phase 1.1 scaffold for the AI-driven web testing framework.

## What’s included (Phase 1.1)
- Project structure under `src/`
- YAML config with env overrides (`config/default.yaml`)
- Logging setup utility (`src/utils/logging_setup.py`)
- Requirements file with pinned versions
- CLI stub `run_ai_test.py`
- `.env.example`

## Quick start
```bash
# From ai-visual-testing/
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

pip install -r requirements.txt
python -m playwright install

# Try the CLI stub
python run_ai_test.py --requirements ..\JspDemo1\AIInputData\Order\ Flow\ Requirements.txt --provider openai --config config/default.yaml --output-dir ./test-reports
```

## Config
- Base YAML at `config/default.yaml`
- Environment variables override via `.env` and process env

## Next (Phase 1.2)
- Define data models: TestSuite, TestStep, Verification, Action, StepResult, TestResults, Verdict

