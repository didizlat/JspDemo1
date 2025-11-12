"""
Requirement Parser for AI-driven testing framework.

This module parses natural language requirement documents into structured
TestSuite objects that can be executed by the test executor.
"""

import re
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from src.models import (
    TestSuite,
    TestStep,
    Verification,
    Action,
    ActionType,
    Severity,
)


logger = logging.getLogger(__name__)


class RequirementParser:
    """
    Parser for natural language test requirement documents.
    
    Parses text files containing test requirements into structured TestSuite
    objects with TestStep, Verification, and Action objects.
    """
    
    # Patterns for extracting different types of content
    STEP_PATTERN = re.compile(r'^(\d+)\.\s*(.+?)(?=\n\d+\.|$)', re.MULTILINE | re.DOTALL)
    GLOBAL_SECTION_PATTERN = re.compile(
        r'^For all pages:\s*\n((?:[-*•]\s*[^\n]+\n?)+)',
        re.MULTILINE | re.IGNORECASE
    )
    
    # Verification patterns
    VERIFICATION_PATTERNS = [
        re.compile(r'Make sure (?:that )?(.+?)(?:\.|$)', re.IGNORECASE),
        re.compile(r'Verify (?:that )?(.+?)(?:\.|$)', re.IGNORECASE),
        re.compile(r'Check (?:that )?(.+?)(?:\.|$)', re.IGNORECASE),
        re.compile(r'Confirm (?:that )?(.+?)(?:\.|$)', re.IGNORECASE),
        re.compile(r'Ensure (?:that )?(.+?)(?:\.|$)', re.IGNORECASE),
    ]
    
    # Action patterns
    ACTION_PATTERNS = {
        ActionType.CLICK: [
            re.compile(r'Click (?:on )?(?:the )?["\']?([^"\']+?)["\']?(?:\s|\.|$)', re.IGNORECASE),
            re.compile(r'Click on ["\']?([^"\']+?)["\']?(?:\s|\.|$)', re.IGNORECASE),
        ],
        ActionType.NAVIGATE: [
            re.compile(r'Go to (?:the )?["\']?([^"\']+?)["\']?(?:\.|$)', re.IGNORECASE),
            re.compile(r'Navigate to (?:the )?["\']?([^"\']+?)["\']?(?:\.|$)', re.IGNORECASE),
        ],
        ActionType.TYPE: [
            re.compile(r'Type ["\']([^"\']+?)["\'] (?:in|into|to) (?:the )?["\']?([^"\']+?)["\']?(?:\.|$)', re.IGNORECASE),
            re.compile(r'Enter ["\']([^"\']+?)["\'] (?:in|into|to) (?:the )?["\']?([^"\']+?)["\']?(?:\.|$)', re.IGNORECASE),
            re.compile(r'(?:Enter|Type) ["\']([^"\']+?)["\'](?:\.|$)', re.IGNORECASE),  # Simple format: "Enter 'value'"
        ],
        ActionType.SELECT: [
            re.compile(r'Select ["\']([^"\']+?)["\'] (?:from|in) (?:the )?["\']?([^"\']+?)["\']?(?:\.|$)', re.IGNORECASE),
            re.compile(r'Choose ["\']([^"\']+?)["\'] (?:from|in) (?:the )?["\']?([^"\']+?)["\']?(?:\.|$)', re.IGNORECASE),
            re.compile(r'(?:Select|Choose) ["\']([^"\']+?)["\'](?:\.|$)', re.IGNORECASE),  # Simple format: "Select 'value'"
        ],
        ActionType.CHECK: [
            re.compile(r'Check (?:the )?["\']?([^"\']+?)["\']?(?: (?:checkbox|option))?(?:\.|$)', re.IGNORECASE),
            re.compile(r'Select (?:the )?["\']?([^"\']+?)["\']? (?:checkbox|option)(?:\.|$)', re.IGNORECASE),
        ],
        ActionType.UNCHECK: [
            re.compile(r'Uncheck (?:the )?["\']?([^"\']+?)["\']?(?:\.|$)', re.IGNORECASE),
        ],
        ActionType.FILL: [
            re.compile(r'Fill (?:out|in) (?:the )?["\']?([^"\']+?)["\']? (?:with|as) ["\']([^"\']+?)["\'](?:\.|$)', re.IGNORECASE),
        ],
    }
    
    # Expected page/element patterns
    EXPECTED_PAGE_PATTERN = re.compile(
        r'(?:Make sure|Verify|Check|Confirm) (?:that )?(?:the browser goes to|you are on|you see) (?:a page called|page) ["\']([^"\']+?)["\']',
        re.IGNORECASE
    )
    
    EXPECTED_PAGE_PATTERN_ALT = re.compile(
        r'(?:browser|page) (?:goes to|navigates to|shows) (?:a page called|page) ["\']([^"\']+?)["\']',
        re.IGNORECASE
    )
    
    EXPECTED_ELEMENT_PATTERN = re.compile(
        r'(?:Make sure|Verify|Check|Confirm) (?:that )?(?:you see|there is|the page contains|the page has) (?:a )?["\']?([^"\']+?)["\']?(?:\.|$)',
        re.IGNORECASE
    )
    
    def __init__(self):
        """Initialize the requirement parser."""
        logger.info("Initialized RequirementParser")
    
    def parse_file(self, filepath: str) -> TestSuite:
        """
        Parse a requirement file into a TestSuite.
        
        Args:
            filepath: Path to the requirement text file
            
        Returns:
            TestSuite object with parsed steps and requirements
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If parsed suite is invalid
        """
        file_path = Path(filepath)
        if not file_path.exists():
            resolved_path = file_path.resolve()
            raise FileNotFoundError(
                f"Requirement file not found: {filepath}\n"
                f"Current directory: {Path.cwd()}\n"
                f"Resolved path: {resolved_path}"
            )
        
        logger.info(f"Parsing requirement file: {filepath}")
        
        # Read file content
        try:
            # Check file size (warn if very large)
            file_size = file_path.stat().st_size
            if file_size > 1_000_000:  # 1MB
                logger.warning(f"Requirement file '{filepath}' is large ({file_size:,} bytes). Parsing may be slow.")
            
            content = self._read_file(file_path)
        except PermissionError as e:
            raise IOError(f"Permission denied reading requirement file '{filepath}': {e}") from e
        except Exception as e:
            raise IOError(f"Failed to read requirement file '{filepath}': {e}") from e
        
        if not content or len(content.strip()) == 0:
            raise ValueError(f"Requirement file '{filepath}' is empty")
        
        # Extract global requirements
        global_requirements = self._extract_global_requirements(content)
        
        # Extract test steps
        steps = self._extract_steps(content)
        
        if not steps:
            raise ValueError(
                f"No test steps found in file: {filepath}\n"
                f"File contains {len(content)} characters.\n"
                f"Expected numbered steps (1., 2., 3., etc.)"
            )
        
        # Parse each step
        test_steps = []
        for step_num, step_text in steps:
            try:
                # Find line number for better error messages
                # Find the first occurrence of this step number
                step_marker = f"{step_num}."
                step_pos = content.find(step_marker)
                if step_pos >= 0:
                    line_number = content[:step_pos].count('\n') + 1
                else:
                    line_number = None
                
                test_step = self._parse_step(step_num, step_text, global_requirements)
                test_steps.append(test_step)
            except Exception as e:
                line_info = f" (around line {line_number})" if line_number else ""
                logger.error(f"Error parsing step {step_num}{line_info}: {e}", exc_info=True)
                raise ValueError(
                    f"Failed to parse step {step_num} in '{filepath}'{line_info}: {e}"
                ) from e
        
        # Create test suite
        suite_name = file_path.stem.replace(" Requirements", "").replace("_", " ").title()
        
        test_suite = TestSuite(
            name=suite_name,
            global_requirements=global_requirements,
            steps=test_steps,
            source_file=str(file_path.absolute()),
        )
        
        # Validate parsed suite
        self._validate_suite(test_suite)
        
        logger.info(f"Parsed {len(test_steps)} steps from {filepath}")
        return test_suite
    
    def _validate_suite(self, suite: TestSuite):
        """
        Validate parsed test suite.
        
        Args:
            suite: TestSuite to validate
            
        Raises:
            ValueError: If suite is invalid
        """
        if not suite.steps:
            raise ValueError(f"Test suite '{suite.name}' has no steps")
        
        # Check for duplicate step numbers
        step_numbers = [step.step_number for step in suite.steps]
        if len(step_numbers) != len(set(step_numbers)):
            duplicates = [n for n in step_numbers if step_numbers.count(n) > 1]
            raise ValueError(f"Duplicate step numbers found in '{suite.name}': {duplicates}")
        
        # Check for sequential step numbers (warn if gaps)
        sorted_numbers = sorted(step_numbers)
        expected = list(range(sorted_numbers[0], sorted_numbers[-1] + 1))
        missing = [n for n in expected if n not in sorted_numbers]
        if missing:
            logger.warning(f"Test suite '{suite.name}' has missing step numbers: {missing}")
        
        # Validate each step
        for step in suite.steps:
            if not step.description or len(step.description.strip()) < 3:
                logger.warning(
                    f"Step {step.step_number} in '{suite.name}' has very short description: "
                    f"'{step.description}'"
                )
            
            # Warn if step has no actions or verifications
            if not step.actions and not step.verifications:
                logger.warning(
                    f"Step {step.step_number} in '{suite.name}' has no actions or verifications. "
                    f"Description: '{step.description[:50]}...'"
                )
            
            # Validate actions
            for action in step.actions:
                if not action.target or len(action.target.strip()) < 1:
                    logger.warning(
                        f"Step {step.step_number} in '{suite.name}' has action with empty target: "
                        f"{action.type}"
                    )
                if action.type in [ActionType.TYPE, ActionType.FILL, ActionType.SELECT]:
                    if not action.value or len(action.value.strip()) < 1:
                        logger.warning(
                            f"Step {step.step_number} in '{suite.name}' has {action.type} action "
                            f"with empty value on target '{action.target}'"
                        )
    
    def _read_file(self, filepath: Path) -> str:
        """
        Read file content with proper encoding handling.
        
        Args:
            filepath: Path to file to read
            
        Returns:
            File content as string
            
        Raises:
            IOError: If file cannot be read
        """
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
                    logger.debug(f"Successfully read file '{filepath}' with encoding: {encoding}")
                    return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                if encoding == encodings[0]:  # Only raise on first encoding attempt
                    raise IOError(f"Failed to read file '{filepath}': {e}") from e
                continue
        
        # If all encodings fail, try with error handling
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                logger.warning(f"Reading file '{filepath}' with UTF-8 encoding and error replacement")
                return f.read()
        except Exception as e:
            raise IOError(f"Failed to read file '{filepath}' with any encoding: {e}") from e
    
    def _extract_global_requirements(self, content: str) -> List[Verification]:
        """
        Extract global requirements that apply to all pages.
        
        Args:
            content: Full file content
            
        Returns:
            List of Verification objects
        """
        global_reqs = []
        
        # Find "For all pages:" section
        match = self.GLOBAL_SECTION_PATTERN.search(content)
        if match:
            global_section = match.group(1)
            
            # Extract bullet points - process each line separately
            lines = global_section.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Remove bullet markers
                line = re.sub(r'^[-*•]\s*', '', line)
                if not line:
                    continue
                
                # Try to extract verifications first (handles "Make sure that...")
                verifications = self._extract_verifications(line)
                if verifications:
                    global_reqs.extend(verifications)
                else:
                    # If no verification pattern matches, check if line contains requirement keywords
                    # This handles lines like "Every page must have..." or "All buttons need..."
                    line_lower = line.lower()
                    if any(keyword in line_lower for keyword in [
                        'make sure', 'verify', 'check', 'confirm', 'ensure',
                        'must', 'need', 'should', 'require', 'has to'
                    ]):
                        # Determine severity based on keywords
                        severity = Severity.MAJOR
                        if any(word in line_lower for word in ['critical', 'must', 'required', 'has to']):
                            severity = Severity.CRITICAL
                        elif any(word in line_lower for word in ['should', 'preferably']):
                            severity = Severity.MINOR
                        
                        # Use the full line as verification text
                        global_reqs.append(Verification(
                            text=line,
                            severity=severity,
                            description=line,
                        ))
        
        logger.debug(f"Extracted {len(global_reqs)} global requirements")
        return global_reqs
    
    def _extract_steps(self, content: str) -> List[Tuple[int, str]]:
        """
        Extract numbered steps from content.
        
        Args:
            content: Full file content
            
        Returns:
            List of tuples (step_number, step_text)
        """
        steps = []
        
        # Find all numbered step markers
        step_markers = list(re.finditer(r'^(\d+)\.\s*', content, re.MULTILINE))
        
        for i, marker in enumerate(step_markers):
            step_num = int(marker.group(1))
            start_pos = marker.end()
            
            # Find end position (start of next step or end of content)
            if i + 1 < len(step_markers):
                end_pos = step_markers[i + 1].start()
            else:
                end_pos = len(content)
            
            # Extract step text
            step_text = content[start_pos:end_pos].strip()
            steps.append((step_num, step_text))
        
        # Sort by step number
        steps.sort(key=lambda x: x[0])
        
        logger.debug(f"Extracted {len(steps)} steps")
        return steps
    
    def _parse_step(self, step_number: int, step_text: str, global_reqs: Optional[List[Verification]] = None) -> TestStep:
        """
        Parse a single step into TestStep object.
        
        Args:
            step_number: Step number
            step_text: Step text content
            global_reqs: Global requirements to include in this step
            
        Returns:
            TestStep object
        """
        # Extract description (first line or first sentence)
        description = self._extract_description(step_text)
        
        # Extract verifications
        verifications = self._extract_verifications(step_text)
        
        # Add global requirements to each step
        if global_reqs:
            verifications = global_reqs + verifications
        
        # Extract actions
        actions = self._extract_actions(step_text)
        
        # Extract expected page
        expected_page = self._extract_expected_page(step_text)
        
        # Extract expected elements
        expected_elements = self._extract_expected_elements(step_text)
        
        return TestStep(
            step_number=step_number,
            description=description,
            verifications=verifications,
            actions=actions,
            expected_page=expected_page,
            expected_elements=expected_elements,
        )
    
    def _extract_description(self, text: str) -> str:
        """Extract step description (first meaningful line)."""
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('-') and not line.startswith('*'):
                # Remove common prefixes
                line = re.sub(r'^(First|Then|Next|After that|Finally),?\s*', '', line, flags=re.IGNORECASE)
                if line.startswith('Description:'):
                    line = line.replace('Description:', '').strip()
                return line[:200]  # Limit length
        
        return "Step description"
    
    def _extract_verifications(self, text: str) -> List[Verification]:
        """
        Extract verification requirements from text.
        
        Args:
            text: Text to parse
            
        Returns:
            List of Verification objects
        """
        verifications = []
        seen_texts = set()  # Track seen verification texts to avoid duplicates
        
        # Split into sentences/lines
        sentences = self._split_into_sentences(text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check each verification pattern
            for pattern in self.VERIFICATION_PATTERNS:
                match = pattern.search(sentence)
                if match:
                    verification_text = match.group(1).strip()
                    
                    # Skip if verification text is too short or empty
                    if not verification_text or len(verification_text) < 3:
                        continue
                    
                    # Skip if already seen (case-insensitive)
                    if verification_text.lower() in seen_texts:
                        continue
                    
                    seen_texts.add(verification_text.lower())
                    
                    # Determine severity (default to MAJOR)
                    severity = Severity.MAJOR
                    sentence_lower = sentence.lower()
                    if any(word in sentence_lower for word in ['critical', 'must', 'required', 'has to']):
                        severity = Severity.CRITICAL
                    elif any(word in sentence_lower for word in ['should', 'preferably', 'nice to have']):
                        severity = Severity.MINOR
                    
                    verification = Verification(
                        text=verification_text,
                        severity=severity,
                        description=sentence,
                    )
                    verifications.append(verification)
                    break  # Move to next sentence after first match
        
        return verifications
    
    def _extract_actions(self, text: str) -> List[Action]:
        """
        Extract actions from text.
        
        Args:
            text: Text to parse
            
        Returns:
            List of Action objects
        """
        actions = []
        seen_actions = set()  # Track seen actions to avoid duplicates
        
        # Split into sentences/lines
        sentences = self._split_into_sentences(text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Track which action types we've already extracted from this sentence
            extracted_types = set()
            
            # Check each action type pattern
            for action_type, patterns in self.ACTION_PATTERNS.items():
                # Skip if already extracted this type from sentence
                if action_type in extracted_types:
                    continue
                
                for pattern in patterns:
                    match = pattern.search(sentence)
                    if match:
                        if action_type in [ActionType.TYPE, ActionType.SELECT, ActionType.FILL]:
                            # Actions with values
                            if len(match.groups()) >= 2:
                                value = match.group(1).strip()
                                target = match.group(2).strip()
                            elif len(match.groups()) == 1:
                                # Simple format: "Enter 'value'" - try to infer target from context
                                value = match.group(1).strip()
                                # Try to find field name in the sentence
                                target = self._infer_field_name(sentence, value)
                                if not target:
                                    continue  # Skip if we can't infer target
                            else:
                                continue
                            
                            # Validate value is not empty
                            if not value or len(value) < 1:
                                logger.debug(f"Skipping action with empty value: {action_type} on {target}")
                                continue
                        else:
                            # Actions without values
                            target = match.group(1).strip()
                            value = None
                        
                        # Validate target is not empty
                        if not target or len(target) < 1:
                            logger.debug(f"Skipping action with empty target: {action_type}")
                            continue
                        
                        # Create action key for deduplication
                        action_key = (action_type, target.lower(), value.lower() if value else None)
                        if action_key in seen_actions:
                            logger.debug(f"Skipping duplicate action: {action_type} on {target}")
                            continue  # Skip duplicate
                        
                        seen_actions.add(action_key)
                        
                        action = Action(
                            type=action_type,
                            target=target,
                            value=value,
                            description=sentence,
                        )
                        actions.append(action)
                        extracted_types.add(action_type)
                        break  # Move to next action type after first match
        
        return actions
    
    def _infer_field_name(self, sentence: str, value: str) -> Optional[str]:
        """Try to infer field name from sentence context."""
        # Look for field name patterns before the value
        # Pattern: "Field Name: Enter 'value'" or "Field Name: Select 'value'"
        field_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):\s*(?:Enter|Type|Select|Choose)', sentence, re.IGNORECASE)
        if field_match:
            return field_match.group(1).strip()
        
        # Pattern: "- Field Name: Enter 'value'"
        bullet_match = re.search(r'-\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):\s*(?:Enter|Type|Select|Choose)', sentence, re.IGNORECASE)
        if bullet_match:
            return bullet_match.group(1).strip()
        
        return None
    
    def _extract_expected_page(self, text: str) -> Optional[str]:
        """Extract expected page name from text."""
        # Try main pattern first
        match = self.EXPECTED_PAGE_PATTERN.search(text)
        if match:
            return match.group(1).strip()
        
        # Try alternative pattern
        match = self.EXPECTED_PAGE_PATTERN_ALT.search(text)
        if match:
            return match.group(1).strip()
        
        # Try additional patterns
        alt_patterns = [
            re.compile(r'Make sure (?:that )?(?:the browser goes to|you are on) (?:a page called|page) ["\']([^"\']+?)["\']', re.IGNORECASE),
            re.compile(r'Verify (?:that )?(?:you are on|you see) (?:the )?["\']([^"\']+?)["\'] (?:page)', re.IGNORECASE),
            re.compile(r'(?:Make sure|Verify) (?:that )?(?:the browser goes to|you are on) (?:a page called|page) ([^\.]+?)(?:\.|$)', re.IGNORECASE),
        ]
        
        for pattern in alt_patterns:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_expected_elements(self, text: str) -> List[str]:
        """Extract expected element descriptions from text."""
        elements = []
        
        # Find "Make sure you see..." patterns
        matches = self.EXPECTED_ELEMENT_PATTERN.finditer(text)
        for match in matches:
            element = match.group(1).strip()
            if element:
                elements.append(element)
        
        # Also extract bulleted lists
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('*'):
                # Remove bullet marker
                element = re.sub(r'^[-*•]\s*', '', line)
                if element and len(element) > 3:  # Filter out very short items
                    elements.append(element)
        
        return elements
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences, handling various formats.
        
        Handles:
        - Standard sentence endings (. ! ?)
        - Newlines
        - Abbreviations (e.g., "Dr. Smith")
        - Decimal numbers (e.g., "Version 1.2.3")
        - URLs (basic handling)
        """
        # First, protect common abbreviations and patterns
        # Replace common abbreviations temporarily
        protected = text
        replacements = {}
        
        # Protect URLs (basic)
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, protected)
        for i, url in enumerate(urls):
            placeholder = f"__URL_{i}__"
            replacements[placeholder] = url
            protected = protected.replace(url, placeholder)
        
        # Split by periods, exclamation marks, question marks, and newlines
        # Use lookbehind to avoid splitting on abbreviations
        sentences = re.split(
            r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=[.!?])\s+|(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=[.!?])\n+|\n+',
            protected
        )
        
        # Restore URLs
        for placeholder, url in replacements.items():
            for i, sentence in enumerate(sentences):
                sentences[i] = sentence.replace(placeholder, url)
        
        # Clean up sentences
        cleaned = []
        for sentence in sentences:
            sentence = sentence.strip()
            # Filter out very short sentences and empty ones
            if sentence and len(sentence) > 3:
                cleaned.append(sentence)
        
        return cleaned

