# Technical Reference Guide: UAT Automation Implementation

This document provides technical implementation details, code examples, and configuration templates to supplement the Comprehensive Plan.

---

## 1. JIRA Integration Implementation

### 1.1 JIRA Client Setup (Python)

```python
"""
JIRA Connector Module
Handles authentication and communication with JIRA REST API
"""
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
import json


@dataclass
class JiraConfig:
    """Configuration for JIRA connection"""
    base_url: str  # e.g., "https://your-domain.atlassian.net" or "https://jira.internal.com"
    username: str  # Email for Cloud, username for Data Center
    api_token: str  # API token or PAT
    project_key: str
    is_cloud: bool = True


@dataclass
class TestCase:
    """Represents a test case from JIRA"""
    key: str
    summary: str
    description: str
    preconditions: str
    test_steps: List[Dict[str, str]]
    expected_results: List[str]
    test_data: Dict[str, Any]
    environment: str
    priority: str
    labels: List[str]
    attachments: List[str]
    created: datetime
    updated: datetime


class JiraConnector:
    """
    Connector for JIRA REST API operations
    Supports both JIRA Cloud and Data Center
    """
    
    def __init__(self, config: JiraConfig):
        self.config = config
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(config.username, config.api_token)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        # API version differs between Cloud and Data Center
        self.api_base = f"{config.base_url}/rest/api/{'3' if config.is_cloud else '2'}"
    
    def get_test_case(self, issue_key: str) -> TestCase:
        """
        Fetch a single test case by issue key
        """
        url = f"{self.api_base}/issue/{issue_key}"
        params = {"expand": "renderedFields"}
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return self._parse_test_case(data)
    
    def search_test_cases(
        self, 
        jql: str = None, 
        max_results: int = 100,
        start_at: int = 0
    ) -> List[TestCase]:
        """
        Search for test cases using JQL
        
        Example JQL:
        - project = FCC AND issuetype = "Test Case" AND status = "Ready for Automation"
        - project = FCC AND labels = "regression" AND updated >= -7d
        """
        if jql is None:
            jql = f'project = {self.config.project_key} AND issuetype = "Test Case"'
        
        url = f"{self.api_base}/search"
        payload = {
            "jql": jql,
            "maxResults": max_results,
            "startAt": start_at,
            "expand": ["renderedFields"],
            "fields": [
                "summary", "description", "priority", "labels",
                "created", "updated", "attachment",
                "customfield_10100",  # Preconditions (example)
                "customfield_10101",  # Test Steps (example)
                "customfield_10102",  # Expected Results (example)
                "customfield_10103",  # Test Data (example)
                "customfield_10104",  # Environment (example)
            ]
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        return [self._parse_test_case(issue) for issue in data.get("issues", [])]
    
    def _parse_test_case(self, data: Dict) -> TestCase:
        """
        Parse JIRA issue data into TestCase object
        Customize field mappings based on your JIRA configuration
        """
        fields = data.get("fields", {})
        
        # Parse test steps from custom field or description
        test_steps = self._parse_test_steps(
            fields.get("customfield_10101") or fields.get("description", "")
        )
        
        return TestCase(
            key=data.get("key"),
            summary=fields.get("summary", ""),
            description=fields.get("description", ""),
            preconditions=fields.get("customfield_10100", ""),
            test_steps=test_steps,
            expected_results=self._parse_expected_results(fields.get("customfield_10102", "")),
            test_data=self._parse_test_data(fields.get("customfield_10103", "")),
            environment=fields.get("customfield_10104", "UAT"),
            priority=fields.get("priority", {}).get("name", "Medium"),
            labels=fields.get("labels", []),
            attachments=[att.get("filename") for att in fields.get("attachment", [])],
            created=datetime.fromisoformat(fields.get("created", "").replace("Z", "+00:00")),
            updated=datetime.fromisoformat(fields.get("updated", "").replace("Z", "+00:00"))
        )
    
    def _parse_test_steps(self, content: str) -> List[Dict[str, str]]:
        """
        Parse test steps from structured text
        Expected format:
        1. [Action]: Description
           Expected: Expected result
        """
        steps = []
        lines = content.split("\n")
        current_step = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for step number pattern
            if line[0].isdigit() and "." in line[:3]:
                if current_step:
                    steps.append(current_step)
                current_step = {
                    "action": line.split(".", 1)[1].strip(),
                    "expected": ""
                }
            elif line.lower().startswith("expected:") and current_step:
                current_step["expected"] = line.split(":", 1)[1].strip()
        
        if current_step:
            steps.append(current_step)
        
        return steps
    
    def _parse_expected_results(self, content: str) -> List[str]:
        """Parse expected results from custom field"""
        if not content:
            return []
        return [r.strip() for r in content.split("\n") if r.strip()]
    
    def _parse_test_data(self, content: str) -> Dict[str, Any]:
        """Parse test data from custom field (JSON or key-value format)"""
        if not content:
            return {}
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Parse key-value format
            data = {}
            for line in content.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    data[key.strip()] = value.strip()
            return data
    
    def create_test_execution(
        self,
        test_case_key: str,
        status: str,
        results: Dict[str, Any],
        evidence_links: List[str]
    ) -> str:
        """
        Create a test execution record linked to the test case
        Returns the created issue key
        """
        url = f"{self.api_base}/issue"
        
        # Build execution summary
        execution_summary = self._build_execution_summary(results)
        
        payload = {
            "fields": {
                "project": {"key": self.config.project_key},
                "issuetype": {"name": "Test Execution"},
                "summary": f"Execution: {test_case_key} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "description": execution_summary,
                "customfield_10200": {"key": test_case_key},  # Link to test case
                "customfield_10201": status,  # Execution status
                "labels": ["automated", "uat"]
            }
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        execution_key = response.json().get("key")
        
        # Add comment with detailed results
        self._add_execution_comment(execution_key, results, evidence_links)
        
        return execution_key
    
    def _build_execution_summary(self, results: Dict[str, Any]) -> str:
        """Build formatted execution summary"""
        return f"""
h2. Test Execution Summary

*Status*: {results.get('overall_status', 'UNKNOWN')}
*Duration*: {results.get('duration_seconds', 0)} seconds
*Environment*: {results.get('environment', 'UAT')}
*Executed*: {datetime.now().isoformat()}

h3. Step Results
{self._format_step_results(results.get('step_results', []))}
        """
    
    def _format_step_results(self, step_results: List[Dict]) -> str:
        """Format step results as JIRA table"""
        if not step_results:
            return "No step results available"
        
        rows = ["||Step||Status||Duration||"]
        for step in step_results:
            status_icon = "(/) " if step.get("status") == "PASSED" else "(x) "
            rows.append(
                f"|{step.get('step_number', '')}|{status_icon}{step.get('status', '')}|{step.get('duration_ms', 0)}ms|"
            )
        return "\n".join(rows)
    
    def _add_execution_comment(
        self,
        issue_key: str,
        results: Dict[str, Any],
        evidence_links: List[str]
    ):
        """Add detailed comment to execution issue"""
        url = f"{self.api_base}/issue/{issue_key}/comment"
        
        evidence_section = "\n".join([f"* [{link}]" for link in evidence_links])
        
        comment_body = f"""
h3. Detailed Execution Results

*Run ID*: {results.get('run_id', 'N/A')}
*AI Translation Hash*: {results.get('ai_translation_hash', 'N/A')}
*App Version*: {results.get('app_version', 'N/A')}

h4. Evidence
{evidence_section}

h4. Execution Metadata
{{code:json}}
{json.dumps(results.get('metadata', {}), indent=2)}
{{code}}
        """
        
        payload = {"body": comment_body}
        self.session.post(url, json=payload)
    
    def update_test_case_status(self, issue_key: str, status: str):
        """
        Update the status of a test case
        Requires appropriate workflow transitions
        """
        # First, get available transitions
        url = f"{self.api_base}/issue/{issue_key}/transitions"
        response = self.session.get(url)
        response.raise_for_status()
        
        transitions = response.json().get("transitions", [])
        target_transition = None
        
        for t in transitions:
            if t.get("name", "").lower() == status.lower():
                target_transition = t
                break
        
        if target_transition:
            payload = {"transition": {"id": target_transition["id"]}}
            self.session.post(url, json=payload)


# Xray-specific connector (if using Xray plugin)
class XrayConnector:
    """
    Connector for Xray Test Management REST API
    """
    
    def __init__(self, config: JiraConfig):
        self.config = config
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(config.username, config.api_token)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        self.xray_base = f"{config.base_url}/rest/raven/1.0/api"
    
    def get_test(self, test_key: str) -> Dict:
        """Get test case from Xray"""
        url = f"{self.xray_base}/test/{test_key}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_test_steps(self, test_key: str) -> List[Dict]:
        """Get test steps for a test case"""
        url = f"{self.xray_base}/test/{test_key}/step"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def create_test_execution(self, test_exec_data: Dict) -> str:
        """Create a test execution in Xray"""
        url = f"{self.xray_base}/testexec"
        response = self.session.post(url, json=test_exec_data)
        response.raise_for_status()
        return response.json().get("key")
    
    def import_execution_results(self, results: Dict) -> str:
        """
        Import test execution results in Xray JSON format
        """
        url = f"{self.xray_base}/import/execution"
        response = self.session.post(url, json=results)
        response.raise_for_status()
        return response.json().get("testExecIssue", {}).get("key")
```

### 1.2 JIRA Configuration Template

```yaml
# jira_config.yaml
jira:
  # Connection settings
  base_url: "https://your-domain.atlassian.net"  # or internal JIRA URL
  is_cloud: true  # false for Data Center
  
  # Authentication (use environment variables in production)
  username: "${JIRA_USERNAME}"
  api_token: "${JIRA_API_TOKEN}"
  
  # Project settings
  project_key: "FCC"
  
  # Issue type mappings
  issue_types:
    test_case: "Test Case"
    test_execution: "Test Execution"
    bug: "Bug"
  
  # Custom field mappings (update with your field IDs)
  custom_fields:
    preconditions: "customfield_10100"
    test_steps: "customfield_10101"
    expected_results: "customfield_10102"
    test_data: "customfield_10103"
    environment: "customfield_10104"
    execution_status: "customfield_10201"
    linked_test_case: "customfield_10200"
  
  # JQL templates
  jql_templates:
    ready_for_automation: 'project = {project} AND issuetype = "Test Case" AND status = "Ready for Automation"'
    regression_suite: 'project = {project} AND labels = "regression" AND issuetype = "Test Case"'
    smoke_tests: 'project = {project} AND labels = "smoke" AND issuetype = "Test Case"'

# Xray settings (if using Xray plugin)
xray:
  enabled: false
  api_version: "1.0"
```

---

## 2. AI Translator Implementation

### 2.1 Test Plan Schema (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "test-plan-schema-v1",
  "title": "Test Plan Schema",
  "description": "Schema for AI-generated test plans",
  "type": "object",
  "required": ["metadata", "preconditions", "steps"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["source_test_id", "translation_timestamp", "translator_model"],
      "properties": {
        "source_test_id": {
          "type": "string",
          "description": "JIRA issue key of the source test case"
        },
        "translation_timestamp": {
          "type": "string",
          "format": "date-time"
        },
        "translator_model": {
          "type": "string",
          "description": "AI model used for translation"
        },
        "translator_version": {
          "type": "string"
        },
        "prompt_hash": {
          "type": "string",
          "pattern": "^sha256:[a-f0-9]{64}$"
        },
        "confidence_score": {
          "type": "number",
          "minimum": 0,
          "maximum": 1
        },
        "requires_human_review": {
          "type": "boolean",
          "default": false
        },
        "review_notes": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },
    "preconditions": {
      "type": "object",
      "properties": {
        "required_role": {
          "type": "string",
          "enum": ["compliance_analyst", "investigator", "admin", "supervisor", "auditor"]
        },
        "required_environment": {
          "type": "string",
          "enum": ["uat", "qa", "staging", "dev"]
        },
        "required_test_data": {
          "type": "object",
          "additionalProperties": true
        },
        "prior_state": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },
    "steps": {
      "type": "array",
      "minItems": 1,
      "items": {
        "$ref": "#/definitions/TestStep"
      }
    },
    "postconditions": {
      "type": "object",
      "properties": {
        "cleanup_actions": {
          "type": "array",
          "items": {"$ref": "#/definitions/TestStep"}
        },
        "final_assertions": {
          "type": "array",
          "items": {"$ref": "#/definitions/Assertion"}
        }
      }
    }
  },
  "definitions": {
    "TestStep": {
      "type": "object",
      "required": ["step_number", "action_type", "target"],
      "properties": {
        "step_number": {
          "type": "integer",
          "minimum": 1
        },
        "description": {
          "type": "string"
        },
        "action_type": {
          "type": "string",
          "enum": ["navigate", "click", "type", "select", "hover", "wait", "scroll", "upload", "download", "verify", "capability"]
        },
        "capability_name": {
          "type": "string",
          "description": "Name of capability from UI capability library (when action_type is 'capability')"
        },
        "target": {
          "$ref": "#/definitions/Target"
        },
        "parameters": {
          "type": "object",
          "additionalProperties": true
        },
        "assertions": {
          "type": "array",
          "items": {"$ref": "#/definitions/Assertion"}
        },
        "timeout_ms": {
          "type": "integer",
          "default": 10000,
          "minimum": 1000,
          "maximum": 60000
        },
        "retry_count": {
          "type": "integer",
          "default": 3,
          "minimum": 0,
          "maximum": 5
        },
        "screenshot": {
          "type": "boolean",
          "default": true
        },
        "continue_on_failure": {
          "type": "boolean",
          "default": false
        }
      }
    },
    "Target": {
      "type": "object",
      "properties": {
        "page": {
          "type": "string",
          "description": "Page object name"
        },
        "url_pattern": {
          "type": "string"
        },
        "selector_strategy": {
          "type": "string",
          "enum": ["data-testid", "aria-label", "role", "text", "css", "xpath", "id", "name"]
        },
        "selector_value": {
          "type": "string"
        },
        "fallback_selectors": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["strategy", "value"],
            "properties": {
              "strategy": {"type": "string"},
              "value": {"type": "string"}
            }
          }
        }
      }
    },
    "Assertion": {
      "type": "object",
      "required": ["type"],
      "properties": {
        "type": {
          "type": "string",
          "enum": [
            "url_contains", "url_equals",
            "element_visible", "element_hidden", "element_enabled", "element_disabled",
            "element_text_equals", "element_text_contains",
            "element_value", "element_attribute",
            "element_count",
            "page_title_contains",
            "network_request_made",
            "file_downloaded",
            "custom"
          ]
        },
        "selector": {
          "$ref": "#/definitions/Target"
        },
        "value": {
          "type": "string"
        },
        "expected_value": {
          "type": "string"
        },
        "attribute_name": {
          "type": "string"
        },
        "custom_script": {
          "type": "string",
          "description": "JavaScript expression for custom assertions"
        }
      }
    }
  }
}
```

### 2.2 AI Translator Module

```python
"""
AI Translator Module
Converts natural language test cases to structured test plans
"""
import hashlib
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import jsonschema
from openai import OpenAI


@dataclass
class TranslationResult:
    """Result of AI translation"""
    success: bool
    test_plan: Optional[Dict[str, Any]]
    confidence_score: float
    requires_review: bool
    review_notes: List[str]
    prompt_hash: str
    response_hash: str
    error_message: Optional[str] = None


class AITranslator:
    """
    Translates natural language test cases into structured test plans
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4-turbo",
        capability_library: Dict = None,
        page_objects: Dict = None,
        schema_path: str = None
    ):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.capability_library = capability_library or {}
        self.page_objects = page_objects or {}
        self.schema = self._load_schema(schema_path)
        self.version = "1.0.0"
    
    def _load_schema(self, schema_path: str) -> Dict:
        """Load JSON schema for validation"""
        if schema_path:
            with open(schema_path) as f:
                return json.load(f)
        # Return embedded schema if no path provided
        return {}  # Use the schema defined above
    
    def translate(
        self,
        test_case: 'TestCase',
        environment: str = "uat",
        test_data_catalog: Dict = None
    ) -> TranslationResult:
        """
        Translate a test case into a structured test plan
        """
        # Build the translation prompt
        prompt = self._build_prompt(test_case, environment, test_data_catalog)
        prompt_hash = self._compute_hash(prompt)
        
        try:
            # Call the AI model
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for deterministic output
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content
            response_hash = self._compute_hash(response_text)
            
            # Parse and validate the response
            test_plan = json.loads(response_text)
            
            # Add metadata
            test_plan["metadata"] = {
                "source_test_id": test_case.key,
                "translation_timestamp": datetime.utcnow().isoformat() + "Z",
                "translator_model": self.model,
                "translator_version": self.version,
                "prompt_hash": f"sha256:{prompt_hash}",
                "confidence_score": test_plan.get("metadata", {}).get("confidence_score", 0.8),
                "requires_human_review": test_plan.get("metadata", {}).get("requires_human_review", False),
                "review_notes": test_plan.get("metadata", {}).get("review_notes", [])
            }
            
            # Validate against schema
            validation_errors = self._validate_plan(test_plan)
            
            if validation_errors:
                return TranslationResult(
                    success=False,
                    test_plan=test_plan,
                    confidence_score=0.0,
                    requires_review=True,
                    review_notes=[f"Schema validation failed: {e}" for e in validation_errors],
                    prompt_hash=prompt_hash,
                    response_hash=response_hash,
                    error_message="Schema validation failed"
                )
            
            return TranslationResult(
                success=True,
                test_plan=test_plan,
                confidence_score=test_plan["metadata"]["confidence_score"],
                requires_review=test_plan["metadata"]["requires_human_review"],
                review_notes=test_plan["metadata"]["review_notes"],
                prompt_hash=prompt_hash,
                response_hash=response_hash
            )
            
        except json.JSONDecodeError as e:
            return TranslationResult(
                success=False,
                test_plan=None,
                confidence_score=0.0,
                requires_review=True,
                review_notes=["AI response was not valid JSON"],
                prompt_hash=prompt_hash,
                response_hash="",
                error_message=str(e)
            )
        except Exception as e:
            return TranslationResult(
                success=False,
                test_plan=None,
                confidence_score=0.0,
                requires_review=True,
                review_notes=[f"Translation failed: {str(e)}"],
                prompt_hash=prompt_hash,
                response_hash="",
                error_message=str(e)
            )
    
    def _get_system_prompt(self) -> str:
        """System prompt for the AI translator"""
        return """You are a test automation translator for a Financial Crimes Compliance (FCC) application.

Your task is to convert natural language test cases into structured, executable test plans following a strict JSON schema.

IMPORTANT RULES:
1. Use ONLY the capabilities and selectors from the provided UI capability library
2. If a step cannot be mapped to known capabilities, set requires_human_review to true and add a note
3. Be conservative with confidence scores - lower is better than overconfident
4. Prefer data-testid selectors when available, with fallbacks
5. Include appropriate assertions for each step
6. Set reasonable timeouts based on action complexity
7. Flag any ambiguous or unclear steps for human review

OUTPUT FORMAT:
Return a valid JSON object following the test plan schema. Include:
- metadata with confidence_score (0-1) and any review_notes
- preconditions with required role, environment, and test data
- steps array with detailed action specifications
- postconditions with cleanup and final assertions

Be precise and deterministic. The output must be executable by an automation framework."""
    
    def _build_prompt(
        self,
        test_case: 'TestCase',
        environment: str,
        test_data_catalog: Dict
    ) -> str:
        """Build the translation prompt with context"""
        return f"""
CONTEXT:
- Application: JSP-based Financial Crimes Compliance Tool
- Environment: {environment}
- Application URL: {self._get_env_url(environment)}

AVAILABLE CAPABILITIES:
{json.dumps(self.capability_library, indent=2)}

PAGE OBJECTS AND SELECTORS:
{json.dumps(self.page_objects, indent=2)}

TEST DATA CATALOG:
{json.dumps(test_data_catalog or {}, indent=2)}

TEST CASE TO TRANSLATE:
Issue Key: {test_case.key}
Summary: {test_case.summary}

Preconditions:
{test_case.preconditions}

Test Steps:
{self._format_test_steps(test_case.test_steps)}

Test Data:
{json.dumps(test_case.test_data, indent=2)}

Please translate this test case into a structured test plan following the schema.
"""
    
    def _format_test_steps(self, steps: List[Dict]) -> str:
        """Format test steps for the prompt"""
        formatted = []
        for i, step in enumerate(steps, 1):
            formatted.append(f"{i}. {step.get('action', '')}")
            if step.get('expected'):
                formatted.append(f"   Expected: {step['expected']}")
        return "\n".join(formatted)
    
    def _get_env_url(self, environment: str) -> str:
        """Get application URL for environment"""
        urls = {
            "uat": "https://uat.fcc-tool.internal",
            "qa": "https://qa.fcc-tool.internal",
            "staging": "https://staging.fcc-tool.internal",
            "dev": "https://dev.fcc-tool.internal"
        }
        return urls.get(environment, urls["uat"])
    
    def _validate_plan(self, test_plan: Dict) -> List[str]:
        """Validate test plan against schema"""
        errors = []
        try:
            jsonschema.validate(test_plan, self.schema)
        except jsonschema.ValidationError as e:
            errors.append(str(e.message))
        except jsonschema.SchemaError as e:
            errors.append(f"Schema error: {str(e)}")
        return errors
    
    def _compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content"""
        return hashlib.sha256(content.encode()).hexdigest()


# UI Capability Library
CAPABILITY_LIBRARY = {
    "login": {
        "description": "Authenticate to the FCC application",
        "parameters": ["username", "password"],
        "page_object": "LoginPage",
        "actions": [
            {"action": "navigate", "url": "/login"},
            {"action": "type", "selector": "[data-testid='username-input']", "param": "username"},
            {"action": "type", "selector": "[data-testid='password-input']", "param": "password"},
            {"action": "click", "selector": "[data-testid='login-button']"},
            {"action": "wait", "condition": "url_contains", "value": "/dashboard"}
        ]
    },
    "navigate_to_alert_queue": {
        "description": "Navigate to the alert investigation queue",
        "parameters": ["filter_status"],
        "page_object": "AlertQueuePage",
        "actions": [
            {"action": "click", "selector": "[data-testid='nav-alerts']"},
            {"action": "wait", "condition": "url_contains", "value": "/alerts/queue"}
        ]
    },
    "search_alert": {
        "description": "Search for a specific alert by ID",
        "parameters": ["alert_id"],
        "page_object": "AlertQueuePage",
        "actions": [
            {"action": "type", "selector": "[data-testid='alert-search']", "param": "alert_id"},
            {"action": "click", "selector": "[data-testid='search-button']"},
            {"action": "wait", "condition": "element_visible", "selector": "[data-testid='search-results']"}
        ]
    },
    "open_alert": {
        "description": "Open an alert for investigation",
        "parameters": ["alert_id"],
        "page_object": "AlertDetailPage",
        "actions": [
            {"action": "click", "selector": "[data-testid='alert-row-{alert_id}']"},
            {"action": "wait", "condition": "url_contains", "value": "/alerts/detail"}
        ]
    },
    "disposition_alert": {
        "description": "Set disposition for an alert",
        "parameters": ["disposition_type", "rationale"],
        "page_object": "AlertDetailPage",
        "actions": [
            {"action": "select", "selector": "[data-testid='disposition-dropdown']", "param": "disposition_type"},
            {"action": "type", "selector": "[data-testid='rationale-input']", "param": "rationale"},
            {"action": "click", "selector": "[data-testid='submit-disposition']"},
            {"action": "wait", "condition": "element_visible", "selector": "[data-testid='disposition-success']"}
        ]
    },
    "search_customer": {
        "description": "Search for a customer profile",
        "parameters": ["search_term", "search_type"],
        "page_object": "CustomerSearchPage",
        "actions": [
            {"action": "click", "selector": "[data-testid='nav-customers']"},
            {"action": "select", "selector": "[data-testid='search-type']", "param": "search_type"},
            {"action": "type", "selector": "[data-testid='customer-search']", "param": "search_term"},
            {"action": "click", "selector": "[data-testid='search-button']"}
        ]
    },
    "create_sar": {
        "description": "Initiate SAR filing workflow",
        "parameters": ["alert_id", "sar_type"],
        "page_object": "SARFilingPage",
        "actions": [
            {"action": "click", "selector": "[data-testid='create-sar-button']"},
            {"action": "select", "selector": "[data-testid='sar-type']", "param": "sar_type"},
            {"action": "wait", "condition": "element_visible", "selector": "[data-testid='sar-form']"}
        ]
    },
    "export_report": {
        "description": "Export investigation report",
        "parameters": ["report_type", "format"],
        "page_object": "ReportingPage",
        "actions": [
            {"action": "click", "selector": "[data-testid='nav-reports']"},
            {"action": "select", "selector": "[data-testid='report-type']", "param": "report_type"},
            {"action": "select", "selector": "[data-testid='export-format']", "param": "format"},
            {"action": "click", "selector": "[data-testid='export-button']"}
        ]
    }
}

# Page Objects with Selectors
PAGE_OBJECTS = {
    "LoginPage": {
        "url_pattern": "/login",
        "selectors": {
            "username_input": {"primary": "[data-testid='username-input']", "fallback": "#username"},
            "password_input": {"primary": "[data-testid='password-input']", "fallback": "#password"},
            "login_button": {"primary": "[data-testid='login-button']", "fallback": "button[type='submit']"},
            "error_message": {"primary": "[data-testid='login-error']", "fallback": ".error-message"}
        }
    },
    "AlertQueuePage": {
        "url_pattern": "/alerts/queue",
        "selectors": {
            "alert_table": {"primary": "[data-testid='alert-queue-table']", "fallback": "#alertQueueTable"},
            "search_input": {"primary": "[data-testid='alert-search']", "fallback": "input[name='alertSearch']"},
            "search_button": {"primary": "[data-testid='search-button']", "fallback": "button.search-btn"},
            "filter_dropdown": {"primary": "[data-testid='status-filter']", "fallback": "select[name='statusFilter']"},
            "alert_row": {"primary": "[data-testid='alert-row-{id}']", "fallback": "tr[data-alert-id='{id}']"}
        }
    },
    "AlertDetailPage": {
        "url_pattern": "/alerts/detail/{id}",
        "selectors": {
            "alert_header": {"primary": "[data-testid='alert-header']", "fallback": ".alert-detail-header"},
            "customer_info": {"primary": "[data-testid='customer-info']", "fallback": ".customer-section"},
            "transaction_table": {"primary": "[data-testid='transaction-table']", "fallback": "#transactionTable"},
            "disposition_dropdown": {"primary": "[data-testid='disposition-dropdown']", "fallback": "select[name='disposition']"},
            "rationale_input": {"primary": "[data-testid='rationale-input']", "fallback": "textarea[name='rationale']"},
            "submit_button": {"primary": "[data-testid='submit-disposition']", "fallback": "button.submit-disposition"},
            "status_badge": {"primary": "[data-testid='alert-status']", "fallback": ".status-badge"}
        }
    },
    "CustomerSearchPage": {
        "url_pattern": "/customers/search",
        "selectors": {
            "search_type": {"primary": "[data-testid='search-type']", "fallback": "select[name='searchType']"},
            "search_input": {"primary": "[data-testid='customer-search']", "fallback": "input[name='searchTerm']"},
            "search_button": {"primary": "[data-testid='search-button']", "fallback": "button.search-btn"},
            "results_table": {"primary": "[data-testid='customer-results']", "fallback": "#customerResultsTable"}
        }
    },
    "SARFilingPage": {
        "url_pattern": "/sar/filing",
        "selectors": {
            "sar_form": {"primary": "[data-testid='sar-form']", "fallback": "#sarFilingForm"},
            "sar_type": {"primary": "[data-testid='sar-type']", "fallback": "select[name='sarType']"},
            "subject_info": {"primary": "[data-testid='subject-info']", "fallback": ".subject-section"},
            "narrative": {"primary": "[data-testid='narrative']", "fallback": "textarea[name='narrative']"},
            "submit_button": {"primary": "[data-testid='submit-sar']", "fallback": "button.submit-sar"}
        }
    }
}
```

---

## 3. Browser Executor Implementation

### 3.1 Playwright-Based Executor

```python
"""
Browser Executor Module
Executes structured test plans using Playwright
"""
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
from playwright.async_api import async_playwright, Page, Browser, BrowserContext


@dataclass
class StepResult:
    """Result of a single test step"""
    step_number: int
    status: str  # PASSED, FAILED, SKIPPED
    duration_ms: int
    assertions_passed: int = 0
    assertions_failed: int = 0
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    retry_count: int = 0


@dataclass
class ExecutionResult:
    """Result of test plan execution"""
    run_id: str
    test_case_id: str
    overall_status: str  # PASSED, FAILED, ERROR
    duration_seconds: float
    steps_total: int
    steps_passed: int
    steps_failed: int
    steps_skipped: int
    step_results: List[StepResult] = field(default_factory=list)
    artifacts: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BrowserExecutor:
    """
    Executes structured test plans using Playwright
    """
    
    def __init__(
        self,
        evidence_dir: str,
        headless: bool = True,
        slow_mo: int = 0,
        timeout: int = 30000
    ):
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.headless = headless
        self.slow_mo = slow_mo
        self.default_timeout = timeout
        
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        self.page_objects = PAGE_OBJECTS  # From translator module
        self.capabilities = CAPABILITY_LIBRARY  # From translator module
    
    async def setup(self, storage_state: str = None):
        """Initialize browser and context"""
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "record_video_dir": str(self.evidence_dir / "videos"),
            "record_video_size": {"width": 1920, "height": 1080}
        }
        
        if storage_state:
            context_options["storage_state"] = storage_state
        
        self.context = await self.browser.new_context(**context_options)
        
        # Enable tracing
        await self.context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True
        )
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.default_timeout)
    
    async def teardown(self, run_id: str):
        """Clean up browser resources and save artifacts"""
        # Stop tracing and save
        trace_path = self.evidence_dir / f"{run_id}_trace.zip"
        await self.context.tracing.stop(path=str(trace_path))
        
        # Close browser
        await self.context.close()
        await self.browser.close()
        
        return str(trace_path)
    
    async def execute(
        self,
        test_plan: Dict[str, Any],
        run_id: str,
        base_url: str
    ) -> ExecutionResult:
        """
        Execute a test plan and return results
        """
        start_time = datetime.utcnow()
        step_results = []
        artifacts = {"screenshots": [], "videos": [], "traces": []}
        
        test_case_id = test_plan["metadata"]["source_test_id"]
        steps = test_plan.get("steps", [])
        
        try:
            await self.setup()
            
            # Navigate to base URL
            await self.page.goto(base_url)
            
            # Execute each step
            for step in steps:
                step_result = await self._execute_step(step, run_id)
                step_results.append(step_result)
                
                if step_result.screenshot_path:
                    artifacts["screenshots"].append(step_result.screenshot_path)
                
                # Stop on failure unless continue_on_failure is set
                if step_result.status == "FAILED" and not step.get("continue_on_failure", False):
                    break
            
            # Execute postcondition assertions
            postconditions = test_plan.get("postconditions", {})
            for assertion in postconditions.get("final_assertions", []):
                await self._execute_assertion(assertion)
            
            # Calculate results
            passed = sum(1 for r in step_results if r.status == "PASSED")
            failed = sum(1 for r in step_results if r.status == "FAILED")
            skipped = len(steps) - len(step_results)
            
            overall_status = "PASSED" if failed == 0 and skipped == 0 else "FAILED"
            
        except Exception as e:
            overall_status = "ERROR"
            passed = sum(1 for r in step_results if r.status == "PASSED")
            failed = sum(1 for r in step_results if r.status == "FAILED")
            skipped = len(steps) - len(step_results)
            
            # Capture error screenshot
            error_screenshot = await self._capture_screenshot(run_id, "error", "execution_error")
            artifacts["screenshots"].append(error_screenshot)
        
        finally:
            trace_path = await self.teardown(run_id)
            artifacts["traces"].append(trace_path)
            
            # Get video path
            video_path = await self.page.video.path()
            if video_path:
                artifacts["videos"].append(str(video_path))
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        return ExecutionResult(
            run_id=run_id,
            test_case_id=test_case_id,
            overall_status=overall_status,
            duration_seconds=duration,
            steps_total=len(steps),
            steps_passed=passed,
            steps_failed=failed,
            steps_skipped=skipped,
            step_results=step_results,
            artifacts=artifacts,
            metadata={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "base_url": base_url,
                "ai_translation_hash": test_plan["metadata"].get("prompt_hash", "")
            }
        )
    
    async def _execute_step(self, step: Dict, run_id: str) -> StepResult:
        """Execute a single test step"""
        step_number = step["step_number"]
        action_type = step["action_type"]
        start_time = datetime.utcnow()
        
        retry_count = 0
        max_retries = step.get("retry_count", 3)
        timeout = step.get("timeout_ms", self.default_timeout)
        
        while retry_count <= max_retries:
            try:
                # Execute the action
                if action_type == "capability":
                    await self._execute_capability(step)
                else:
                    await self._execute_action(step, timeout)
                
                # Execute assertions
                assertions_passed = 0
                assertions_failed = 0
                
                for assertion in step.get("assertions", []):
                    try:
                        await self._execute_assertion(assertion, timeout)
                        assertions_passed += 1
                    except AssertionError:
                        assertions_failed += 1
                
                # Capture screenshot if requested
                screenshot_path = None
                if step.get("screenshot", True):
                    screenshot_path = await self._capture_screenshot(
                        run_id, step_number, step.get("description", action_type)
                    )
                
                duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                status = "PASSED" if assertions_failed == 0 else "FAILED"
                
                return StepResult(
                    step_number=step_number,
                    status=status,
                    duration_ms=duration,
                    assertions_passed=assertions_passed,
                    assertions_failed=assertions_failed,
                    screenshot_path=screenshot_path,
                    retry_count=retry_count
                )
                
            except Exception as e:
                retry_count += 1
                if retry_count > max_retries:
                    duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    screenshot_path = await self._capture_screenshot(
                        run_id, step_number, f"failure_{step.get('description', action_type)}"
                    )
                    
                    return StepResult(
                        step_number=step_number,
                        status="FAILED",
                        duration_ms=duration,
                        error_message=str(e),
                        screenshot_path=screenshot_path,
                        retry_count=retry_count - 1
                    )
                
                await asyncio.sleep(1)  # Wait before retry
    
    async def _execute_action(self, step: Dict, timeout: int):
        """Execute a browser action"""
        action_type = step["action_type"]
        target = step.get("target", {})
        params = step.get("parameters", {})
        
        # Get selector with fallback
        selector = await self._get_selector(target)
        
        if action_type == "navigate":
            url = target.get("url_pattern", params.get("url", ""))
            await self.page.goto(url, timeout=timeout)
            
        elif action_type == "click":
            await self.page.click(selector, timeout=timeout)
            
        elif action_type == "type":
            text = params.get("text", params.get("value", ""))
            await self.page.fill(selector, text, timeout=timeout)
            
        elif action_type == "select":
            value = params.get("value", "")
            await self.page.select_option(selector, value, timeout=timeout)
            
        elif action_type == "hover":
            await self.page.hover(selector, timeout=timeout)
            
        elif action_type == "wait":
            wait_time = params.get("duration_ms", 1000)
            await asyncio.sleep(wait_time / 1000)
            
        elif action_type == "scroll":
            direction = params.get("direction", "down")
            distance = params.get("distance", 500)
            if direction == "down":
                await self.page.evaluate(f"window.scrollBy(0, {distance})")
            else:
                await self.page.evaluate(f"window.scrollBy(0, -{distance})")
                
        elif action_type == "upload":
            file_path = params.get("file_path", "")
            await self.page.set_input_files(selector, file_path, timeout=timeout)
            
        elif action_type == "verify":
            # Verification is handled by assertions
            pass
    
    async def _execute_capability(self, step: Dict):
        """Execute a capability from the capability library"""
        capability_name = step.get("capability_name")
        params = step.get("parameters", {})
        
        capability = self.capabilities.get(capability_name)
        if not capability:
            raise ValueError(f"Unknown capability: {capability_name}")
        
        for action in capability.get("actions", []):
            action_type = action.get("action")
            selector = action.get("selector", "")
            
            # Substitute parameters in selector
            for key, value in params.items():
                selector = selector.replace(f"{{{key}}}", str(value))
            
            if action_type == "navigate":
                await self.page.goto(action.get("url"))
            elif action_type == "click":
                await self.page.click(selector)
            elif action_type == "type":
                param_name = action.get("param")
                text = params.get(param_name, "")
                await self.page.fill(selector, text)
            elif action_type == "select":
                param_name = action.get("param")
                value = params.get(param_name, "")
                await self.page.select_option(selector, value)
            elif action_type == "wait":
                condition = action.get("condition")
                value = action.get("value", "")
                await self._wait_for_condition(condition, value, selector)
    
    async def _execute_assertion(self, assertion: Dict, timeout: int = None):
        """Execute an assertion"""
        timeout = timeout or self.default_timeout
        assertion_type = assertion["type"]
        
        if assertion_type == "url_contains":
            await self.page.wait_for_url(f"**{assertion['value']}**", timeout=timeout)
            
        elif assertion_type == "url_equals":
            current_url = self.page.url
            assert current_url == assertion["value"], f"URL mismatch: {current_url} != {assertion['value']}"
            
        elif assertion_type == "element_visible":
            selector = await self._get_selector(assertion.get("selector", {}))
            await self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            
        elif assertion_type == "element_hidden":
            selector = await self._get_selector(assertion.get("selector", {}))
            await self.page.wait_for_selector(selector, state="hidden", timeout=timeout)
            
        elif assertion_type == "element_text_contains":
            selector = await self._get_selector(assertion.get("selector", {}))
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            text = await element.text_content()
            expected = assertion.get("expected_value", assertion.get("value", ""))
            assert expected in text, f"Text '{expected}' not found in '{text}'"
            
        elif assertion_type == "element_text_equals":
            selector = await self._get_selector(assertion.get("selector", {}))
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            text = await element.text_content()
            expected = assertion.get("expected_value", assertion.get("value", ""))
            assert text.strip() == expected.strip(), f"Text mismatch: '{text}' != '{expected}'"
            
        elif assertion_type == "element_value":
            selector = await self._get_selector(assertion.get("selector", {}))
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            value = await element.input_value()
            expected = assertion.get("expected_value", "")
            assert value == expected, f"Value mismatch: '{value}' != '{expected}'"
            
        elif assertion_type == "element_count":
            selector = await self._get_selector(assertion.get("selector", {}))
            elements = await self.page.query_selector_all(selector)
            expected_count = int(assertion.get("value", 0))
            assert len(elements) == expected_count, f"Element count: {len(elements)} != {expected_count}"
            
        elif assertion_type == "page_title_contains":
            title = await self.page.title()
            expected = assertion.get("value", "")
            assert expected in title, f"Title '{expected}' not found in '{title}'"
    
    async def _get_selector(self, target: Dict) -> str:
        """Get selector from target with fallback support"""
        if not target:
            return ""
        
        strategy = target.get("selector_strategy", "css")
        value = target.get("selector_value", "")
        
        if strategy == "data-testid":
            return f"[data-testid='{value}']"
        elif strategy == "aria-label":
            return f"[aria-label='{value}']"
        elif strategy == "role":
            return f"[role='{value}']"
        elif strategy == "text":
            return f"text={value}"
        elif strategy == "xpath":
            return f"xpath={value}"
        elif strategy == "id":
            return f"#{value}"
        elif strategy == "name":
            return f"[name='{value}']"
        else:
            return value
    
    async def _wait_for_condition(self, condition: str, value: str, selector: str = None):
        """Wait for a specific condition"""
        if condition == "url_contains":
            await self.page.wait_for_url(f"**{value}**")
        elif condition == "element_visible":
            await self.page.wait_for_selector(selector or value, state="visible")
        elif condition == "element_hidden":
            await self.page.wait_for_selector(selector or value, state="hidden")
        elif condition == "network_idle":
            await self.page.wait_for_load_state("networkidle")
    
    async def _capture_screenshot(self, run_id: str, step: Any, description: str) -> str:
        """Capture and save a screenshot"""
        filename = f"{run_id}_step{step}_{description}.png"
        filepath = self.evidence_dir / filename
        await self.page.screenshot(path=str(filepath), full_page=True)
        return str(filepath)
```

### 3.2 Page Object Base Class

```python
"""
Page Object Model Base Classes
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
from playwright.async_api import Page


class BasePage(ABC):
    """Base class for all page objects"""
    
    def __init__(self, page: Page, selectors: Dict[str, Dict[str, str]]):
        self.page = page
        self.selectors = selectors
    
    @property
    @abstractmethod
    def url_pattern(self) -> str:
        """URL pattern for this page"""
        pass
    
    async def get_selector(self, element_name: str) -> str:
        """Get selector for an element with fallback"""
        selector_config = self.selectors.get(element_name, {})
        primary = selector_config.get("primary")
        fallback = selector_config.get("fallback")
        
        if primary:
            try:
                element = await self.page.wait_for_selector(primary, timeout=2000)
                if element:
                    return primary
            except:
                pass
        
        return fallback or primary
    
    async def is_loaded(self) -> bool:
        """Check if the page is loaded"""
        return self.url_pattern in self.page.url
    
    async def wait_for_load(self, timeout: int = 10000):
        """Wait for the page to load"""
        await self.page.wait_for_url(f"**{self.url_pattern}**", timeout=timeout)


class AlertQueuePage(BasePage):
    """Page object for Alert Queue"""
    
    @property
    def url_pattern(self) -> str:
        return "/alerts/queue"
    
    async def search_alert(self, alert_id: str):
        """Search for an alert by ID"""
        search_selector = await self.get_selector("search_input")
        button_selector = await self.get_selector("search_button")
        
        await self.page.fill(search_selector, alert_id)
        await self.page.click(button_selector)
        await self.page.wait_for_selector(await self.get_selector("alert_table"))
    
    async def open_alert(self, alert_id: str):
        """Open an alert for investigation"""
        row_selector = (await self.get_selector("alert_row")).replace("{id}", alert_id)
        await self.page.click(row_selector)
    
    async def get_alert_count(self) -> int:
        """Get the number of alerts in the queue"""
        table_selector = await self.get_selector("alert_table")
        rows = await self.page.query_selector_all(f"{table_selector} tbody tr")
        return len(rows)


class AlertDetailPage(BasePage):
    """Page object for Alert Detail"""
    
    @property
    def url_pattern(self) -> str:
        return "/alerts/detail"
    
    async def get_alert_status(self) -> str:
        """Get the current alert status"""
        status_selector = await self.get_selector("status_badge")
        element = await self.page.wait_for_selector(status_selector)
        return await element.text_content()
    
    async def set_disposition(self, disposition: str, rationale: str):
        """Set the disposition for the alert"""
        dropdown_selector = await self.get_selector("disposition_dropdown")
        rationale_selector = await self.get_selector("rationale_input")
        submit_selector = await self.get_selector("submit_button")
        
        await self.page.select_option(dropdown_selector, disposition)
        await self.page.fill(rationale_selector, rationale)
        await self.page.click(submit_selector)
    
    async def get_customer_name(self) -> str:
        """Get the customer name from the alert"""
        customer_selector = await self.get_selector("customer_info")
        element = await self.page.wait_for_selector(customer_selector)
        return await element.text_content()
```

---

## 4. Evidence and Redaction

### 4.1 PII Redaction Module

```python
"""
PII/PCI Redaction Module
Redacts sensitive information from evidence before storage
"""
import re
from typing import List, Tuple, Dict
from dataclasses import dataclass
from PIL import Image, ImageDraw
import pytesseract
import json


@dataclass
class RedactionRule:
    """Rule for redacting sensitive data"""
    name: str
    pattern: str
    replacement: str
    description: str


# Standard redaction rules for FCC
REDACTION_RULES = [
    RedactionRule(
        name="ssn",
        pattern=r"\b\d{3}-\d{2}-\d{4}\b",
        replacement="XXX-XX-XXXX",
        description="Social Security Number"
    ),
    RedactionRule(
        name="ssn_no_dash",
        pattern=r"\b\d{9}\b",
        replacement="XXXXXXXXX",
        description="SSN without dashes"
    ),
    RedactionRule(
        name="credit_card",
        pattern=r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        replacement="XXXX-XXXX-XXXX-XXXX",
        description="Credit Card Number"
    ),
    RedactionRule(
        name="email",
        pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        replacement="[EMAIL REDACTED]",
        description="Email Address"
    ),
    RedactionRule(
        name="phone",
        pattern=r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        replacement="[PHONE REDACTED]",
        description="Phone Number"
    ),
    RedactionRule(
        name="account_number",
        pattern=r"\b[A-Z]{2}\d{10,18}\b",
        replacement="[ACCOUNT REDACTED]",
        description="Account Number"
    ),
    RedactionRule(
        name="date_of_birth",
        pattern=r"\b(?:DOB|Date of Birth|Birth Date)[\s:]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        replacement="[DOB REDACTED]",
        description="Date of Birth"
    ),
]


class PIIRedactor:
    """
    Redacts PII/PCI from text and images
    """
    
    def __init__(self, rules: List[RedactionRule] = None):
        self.rules = rules or REDACTION_RULES
        self.redaction_log = []
    
    def redact_text(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Redact PII from text content
        Returns redacted text and log of redactions
        """
        redacted = text
        redactions = []
        
        for rule in self.rules:
            matches = re.finditer(rule.pattern, redacted, re.IGNORECASE)
            for match in matches:
                redactions.append({
                    "rule": rule.name,
                    "description": rule.description,
                    "position": match.span(),
                    "length": len(match.group())
                })
            redacted = re.sub(rule.pattern, rule.replacement, redacted, flags=re.IGNORECASE)
        
        self.redaction_log.extend(redactions)
        return redacted, redactions
    
    def redact_json(self, data: Dict) -> Tuple[Dict, List[Dict]]:
        """
        Redact PII from JSON/dict content recursively
        """
        redactions = []
        
        def redact_value(value):
            if isinstance(value, str):
                redacted, r = self.redact_text(value)
                redactions.extend(r)
                return redacted
            elif isinstance(value, dict):
                return {k: redact_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [redact_value(item) for item in value]
            return value
        
        redacted_data = redact_value(data)
        return redacted_data, redactions
    
    def redact_image(self, image_path: str, output_path: str) -> List[Dict]:
        """
        Redact PII from screenshot using OCR
        Returns list of redacted regions
        """
        # Load image
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)
        
        # Perform OCR to get text and positions
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        redactions = []
        n_boxes = len(ocr_data['text'])
        
        for i in range(n_boxes):
            text = ocr_data['text'][i]
            if not text.strip():
                continue
            
            # Check each redaction rule
            for rule in self.rules:
                if re.search(rule.pattern, text, re.IGNORECASE):
                    # Get bounding box
                    x = ocr_data['left'][i]
                    y = ocr_data['top'][i]
                    w = ocr_data['width'][i]
                    h = ocr_data['height'][i]
                    
                    # Draw black rectangle over sensitive data
                    draw.rectangle([x, y, x + w, y + h], fill='black')
                    
                    redactions.append({
                        "rule": rule.name,
                        "description": rule.description,
                        "region": {"x": x, "y": y, "width": w, "height": h}
                    })
        
        # Save redacted image
        image.save(output_path)
        
        self.redaction_log.extend(redactions)
        return redactions
    
    def get_redaction_report(self) -> Dict:
        """
        Generate a report of all redactions performed
        """
        return {
            "total_redactions": len(self.redaction_log),
            "by_type": self._group_by_type(),
            "details": self.redaction_log
        }
    
    def _group_by_type(self) -> Dict[str, int]:
        """Group redactions by type"""
        counts = {}
        for r in self.redaction_log:
            rule = r.get("rule", "unknown")
            counts[rule] = counts.get(rule, 0) + 1
        return counts
```

---

## 5. Orchestration and Main Entry Point

### 5.1 Test Orchestrator

```python
"""
Test Orchestrator
Coordinates the entire test execution pipeline
"""
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path


@dataclass
class TestRun:
    """Represents a complete test run"""
    run_id: str
    test_case_id: str
    environment: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    translation_result: Optional[Dict] = None
    execution_result: Optional[Dict] = None
    evidence_paths: List[str] = None
    jira_execution_key: Optional[str] = None


class TestOrchestrator:
    """
    Orchestrates the complete test automation pipeline
    """
    
    def __init__(
        self,
        jira_connector: 'JiraConnector',
        ai_translator: 'AITranslator',
        browser_executor: 'BrowserExecutor',
        pii_redactor: 'PIIRedactor',
        config: Dict[str, Any]
    ):
        self.jira = jira_connector
        self.translator = ai_translator
        self.executor = browser_executor
        self.redactor = pii_redactor
        self.config = config
        
        self.evidence_dir = Path(config.get("evidence_dir", "./evidence"))
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        self.ledger_path = Path(config.get("ledger_path", "./execution_ledger.jsonl"))
    
    async def run_test(
        self,
        test_case_key: str,
        environment: str = "uat",
        require_human_review: bool = True
    ) -> TestRun:
        """
        Execute a single test case through the complete pipeline
        """
        run_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        test_run = TestRun(
            run_id=run_id,
            test_case_id=test_case_key,
            environment=environment,
            status="STARTED",
            start_time=start_time,
            evidence_paths=[]
        )
        
        try:
            # Step 1: Fetch test case from JIRA
            print(f"[{run_id}] Fetching test case {test_case_key} from JIRA...")
            test_case = self.jira.get_test_case(test_case_key)
            
            # Step 2: Translate to structured test plan
            print(f"[{run_id}] Translating test case to structured plan...")
            translation_result = self.translator.translate(
                test_case=test_case,
                environment=environment,
                test_data_catalog=self.config.get("test_data_catalog", {})
            )
            
            test_run.translation_result = asdict(translation_result)
            
            if not translation_result.success:
                test_run.status = "TRANSLATION_FAILED"
                test_run.end_time = datetime.utcnow()
                self._log_to_ledger(test_run)
                return test_run
            
            # Step 3: Human review gate (if required)
            if require_human_review and translation_result.requires_review:
                print(f"[{run_id}] Test plan requires human review. Pausing execution.")
                test_run.status = "PENDING_REVIEW"
                self._log_to_ledger(test_run)
                # In production, this would trigger a notification and wait for approval
                return test_run
            
            # Step 4: Execute test plan
            print(f"[{run_id}] Executing test plan...")
            base_url = self.config.get("environments", {}).get(environment, {}).get("url")
            
            execution_result = await self.executor.execute(
                test_plan=translation_result.test_plan,
                run_id=run_id,
                base_url=base_url
            )
            
            test_run.execution_result = asdict(execution_result)
            test_run.evidence_paths = (
                execution_result.artifacts.get("screenshots", []) +
                execution_result.artifacts.get("videos", []) +
                execution_result.artifacts.get("traces", [])
            )
            
            # Step 5: Redact PII from evidence
            print(f"[{run_id}] Redacting PII from evidence...")
            redacted_paths = await self._redact_evidence(test_run.evidence_paths)
            
            # Step 6: Report results to JIRA
            print(f"[{run_id}] Reporting results to JIRA...")
            execution_key = self.jira.create_test_execution(
                test_case_key=test_case_key,
                status=execution_result.overall_status,
                results={
                    "run_id": run_id,
                    "overall_status": execution_result.overall_status,
                    "duration_seconds": execution_result.duration_seconds,
                    "step_results": [asdict(r) for r in execution_result.step_results],
                    "ai_translation_hash": translation_result.prompt_hash,
                    "app_version": self.config.get("app_version", "unknown"),
                    "metadata": execution_result.metadata
                },
                evidence_links=redacted_paths
            )
            
            test_run.jira_execution_key = execution_key
            test_run.status = execution_result.overall_status
            test_run.end_time = datetime.utcnow()
            
            # Step 7: Log to execution ledger
            self._log_to_ledger(test_run)
            
            print(f"[{run_id}] Test execution complete: {test_run.status}")
            return test_run
            
        except Exception as e:
            test_run.status = "ERROR"
            test_run.end_time = datetime.utcnow()
            test_run.execution_result = {"error": str(e)}
            self._log_to_ledger(test_run)
            raise
    
    async def run_test_suite(
        self,
        jql: str,
        environment: str = "uat",
        parallel: int = 1
    ) -> List[TestRun]:
        """
        Execute multiple test cases matching a JQL query
        """
        # Fetch test cases
        test_cases = self.jira.search_test_cases(jql=jql)
        print(f"Found {len(test_cases)} test cases to execute")
        
        results = []
        
        if parallel == 1:
            # Sequential execution
            for tc in test_cases:
                result = await self.run_test(tc.key, environment)
                results.append(result)
        else:
            # Parallel execution
            semaphore = asyncio.Semaphore(parallel)
            
            async def run_with_semaphore(tc):
                async with semaphore:
                    return await self.run_test(tc.key, environment)
            
            tasks = [run_with_semaphore(tc) for tc in test_cases]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Generate suite report
        self._generate_suite_report(results, jql, environment)
        
        return results
    
    async def _redact_evidence(self, evidence_paths: List[str]) -> List[str]:
        """Redact PII from all evidence files"""
        redacted_paths = []
        
        for path in evidence_paths:
            if path.endswith(('.png', '.jpg', '.jpeg')):
                redacted_path = path.replace('.', '_redacted.')
                self.redactor.redact_image(path, redacted_path)
                redacted_paths.append(redacted_path)
            else:
                redacted_paths.append(path)
        
        return redacted_paths
    
    def _log_to_ledger(self, test_run: TestRun):
        """Append test run to execution ledger"""
        with open(self.ledger_path, 'a') as f:
            record = {
                "run_id": test_run.run_id,
                "test_case_id": test_run.test_case_id,
                "environment": test_run.environment,
                "status": test_run.status,
                "start_time": test_run.start_time.isoformat(),
                "end_time": test_run.end_time.isoformat() if test_run.end_time else None,
                "jira_execution_key": test_run.jira_execution_key,
                "translation_hash": test_run.translation_result.get("prompt_hash") if test_run.translation_result else None,
                "evidence_count": len(test_run.evidence_paths) if test_run.evidence_paths else 0
            }
            f.write(json.dumps(record) + "\n")
    
    def _generate_suite_report(
        self,
        results: List[TestRun],
        jql: str,
        environment: str
    ):
        """Generate a summary report for the test suite"""
        passed = sum(1 for r in results if r.status == "PASSED")
        failed = sum(1 for r in results if r.status == "FAILED")
        errors = sum(1 for r in results if r.status == "ERROR")
        
        report = {
            "suite_run_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "jql": jql,
            "environment": environment,
            "summary": {
                "total": len(results),
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "pass_rate": passed / len(results) * 100 if results else 0
            },
            "test_runs": [
                {
                    "run_id": r.run_id,
                    "test_case_id": r.test_case_id,
                    "status": r.status,
                    "jira_execution_key": r.jira_execution_key
                }
                for r in results
            ]
        }
        
        report_path = self.evidence_dir / f"suite_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nSuite Report: {report_path}")
        print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
        print(f"Pass Rate: {report['summary']['pass_rate']:.1f}%")


# Main entry point
async def main():
    """Main entry point for test execution"""
    import os
    
    # Load configuration
    config = {
        "evidence_dir": "./evidence",
        "ledger_path": "./execution_ledger.jsonl",
        "app_version": "3.2.1",
        "environments": {
            "uat": {"url": "https://uat.fcc-tool.internal"},
            "qa": {"url": "https://qa.fcc-tool.internal"}
        },
        "test_data_catalog": {
            "test_customer_001": {"id": "CUST-001", "name": "Test Customer"},
            "test_alert_001": {"id": "ALT-2025-001", "type": "High Risk"}
        }
    }
    
    # Initialize components
    jira_config = JiraConfig(
        base_url=os.environ.get("JIRA_URL", "https://your-domain.atlassian.net"),
        username=os.environ.get("JIRA_USERNAME"),
        api_token=os.environ.get("JIRA_API_TOKEN"),
        project_key="FCC"
    )
    
    jira = JiraConnector(jira_config)
    translator = AITranslator(
        api_key=os.environ.get("OPENAI_API_KEY"),
        capability_library=CAPABILITY_LIBRARY,
        page_objects=PAGE_OBJECTS
    )
    executor = BrowserExecutor(evidence_dir=config["evidence_dir"])
    redactor = PIIRedactor()
    
    orchestrator = TestOrchestrator(
        jira_connector=jira,
        ai_translator=translator,
        browser_executor=executor,
        pii_redactor=redactor,
        config=config
    )
    
    # Run a single test
    # result = await orchestrator.run_test("FCC-1234", environment="uat")
    
    # Or run a test suite
    # results = await orchestrator.run_test_suite(
    #     jql='project = FCC AND labels = "regression"',
    #     environment="uat",
    #     parallel=2
    # )


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 6. Configuration Templates

### 6.1 Main Configuration File

```yaml
# config.yaml
# Main configuration for UAT Automation System

# Application settings
application:
  name: "FCC UAT Automation"
  version: "1.0.0"

# Environment configurations
environments:
  uat:
    url: "https://uat.fcc-tool.internal"
    app_version: "3.2.1"
    auth_method: "sso"  # sso, ldap, local
  qa:
    url: "https://qa.fcc-tool.internal"
    app_version: "3.2.0"
    auth_method: "sso"
  staging:
    url: "https://staging.fcc-tool.internal"
    app_version: "3.3.0-beta"
    auth_method: "local"

# JIRA configuration
jira:
  base_url: "${JIRA_URL}"
  username: "${JIRA_USERNAME}"
  api_token: "${JIRA_API_TOKEN}"
  project_key: "FCC"
  is_cloud: true
  
  # Test management plugin (optional)
  test_plugin: "xray"  # xray, zephyr, or none
  
  # Custom field mappings
  custom_fields:
    preconditions: "customfield_10100"
    test_steps: "customfield_10101"
    expected_results: "customfield_10102"
    test_data: "customfield_10103"
    environment: "customfield_10104"

# AI Translator configuration
ai:
  provider: "openai"  # openai, azure, local
  model: "gpt-4-turbo"
  api_key: "${OPENAI_API_KEY}"
  temperature: 0.1
  max_tokens: 4096
  
  # Azure OpenAI settings (if using Azure)
  azure:
    endpoint: "${AZURE_OPENAI_ENDPOINT}"
    deployment: "gpt-4-turbo"
    api_version: "2024-02-15-preview"

# Browser automation configuration
browser:
  engine: "playwright"  # playwright or selenium
  headless: true
  slow_mo: 0  # milliseconds between actions
  default_timeout: 30000  # milliseconds
  viewport:
    width: 1920
    height: 1080
  
  # Video recording
  record_video: true
  video_size:
    width: 1920
    height: 1080

# Evidence configuration
evidence:
  base_dir: "./evidence"
  retention_days: 365
  
  # Storage backend
  storage:
    type: "local"  # local, s3, azure_blob
    # S3 settings (if using S3)
    s3:
      bucket: "fcc-uat-evidence"
      region: "us-east-1"
      prefix: "evidence/"
  
  # Redaction settings
  redaction:
    enabled: true
    rules:
      - ssn
      - credit_card
      - email
      - phone
      - account_number
      - date_of_birth

# Execution settings
execution:
  parallel_tests: 2
  retry_failed: true
  max_retries: 3
  
  # Human review settings
  require_review_for_new_tests: true
  require_review_threshold: 0.8  # confidence score below this requires review
  
  # Scheduling
  schedule:
    enabled: false
    cron: "0 6 * * *"  # Daily at 6 AM

# Logging and monitoring
logging:
  level: "INFO"
  format: "json"
  output:
    - console
    - file
  file_path: "./logs/uat_automation.log"

# Notifications
notifications:
  enabled: true
  channels:
    - type: "email"
      recipients:
        - "qa-team@company.com"
      on_failure: true
      on_success: false
    - type: "slack"
      webhook: "${SLACK_WEBHOOK_URL}"
      channel: "#uat-automation"
      on_failure: true
      on_success: true
```

### 6.2 Test Data Catalog Template

```yaml
# test_data_catalog.yaml
# Catalog of test data available for automated tests

customers:
  test_customer_001:
    id: "CUST-001"
    name: "John Test Smith"
    type: "individual"
    risk_rating: "high"
    account_numbers:
      - "ACC-001-001"
      - "ACC-001-002"
    
  test_customer_002:
    id: "CUST-002"
    name: "Test Corporation LLC"
    type: "business"
    risk_rating: "medium"
    account_numbers:
      - "ACC-002-001"

alerts:
  test_alert_001:
    id: "ALT-2025-001"
    type: "unusual_activity"
    customer_id: "CUST-001"
    status: "open"
    risk_score: 85
    
  test_alert_002:
    id: "ALT-2025-002"
    type: "large_transaction"
    customer_id: "CUST-002"
    status: "open"
    risk_score: 72

transactions:
  test_transaction_001:
    id: "TXN-001"
    amount: 50000.00
    currency: "USD"
    type: "wire_transfer"
    customer_id: "CUST-001"

watchlist_entries:
  test_watchlist_001:
    id: "WL-001"
    name: "Test Watchlist Entity"
    type: "individual"
    source: "OFAC"
```

---

## 7. Deployment and CI/CD

### 7.1 Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright browsers
RUN pip install playwright && playwright install chromium && playwright install-deps

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create evidence directory
RUN mkdir -p /app/evidence /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV EVIDENCE_DIR=/app/evidence
ENV LOG_DIR=/app/logs

# Run the application
CMD ["python", "-m", "uat_automation.main"]
```

### 7.2 Requirements File

```
# requirements.txt
playwright>=1.40.0
requests>=2.31.0
openai>=1.6.0
jsonschema>=4.20.0
pydantic>=2.5.0
PyYAML>=6.0.1
Pillow>=10.1.0
pytesseract>=0.3.10
structlog>=23.2.0
python-dotenv>=1.0.0
aiohttp>=3.9.0
```

### 7.3 GitHub Actions Workflow

```yaml
# .github/workflows/uat-automation.yml
name: UAT Automation

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM UTC
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'uat'
        type: choice
        options:
          - uat
          - qa
          - staging
      jql:
        description: 'JQL query for test selection'
        required: false
        default: 'project = FCC AND labels = "regression"'

jobs:
  run-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
          playwright install-deps
      
      - name: Run UAT Tests
        env:
          JIRA_URL: ${{ secrets.JIRA_URL }}
          JIRA_USERNAME: ${{ secrets.JIRA_USERNAME }}
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python -m uat_automation.main \
            --environment ${{ github.event.inputs.environment || 'uat' }} \
            --jql "${{ github.event.inputs.jql || 'project = FCC AND labels = regression' }}"
      
      - name: Upload Evidence
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-evidence
          path: evidence/
          retention-days: 30
      
      - name: Upload Reports
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-reports
          path: |
            evidence/suite_report_*.json
            execution_ledger.jsonl
```

---

This technical reference guide provides implementation details and code examples for all major components of the UAT automation system. Use this alongside the Comprehensive Plan document for implementation guidance.
