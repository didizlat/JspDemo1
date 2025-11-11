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
    GLOBAL_SECTION_PATTERN = re.compile(r'^For all pages:\s*\n(.*?)(?=\n\d+\.|$)', re.MULTILINE | re.DOTALL)
    
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
        """
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"Requirement file not found: {filepath}")
        
        logger.info(f"Parsing requirement file: {filepath}")
        
        # Read file content
        content = self._read_file(file_path)
        
        # Extract global requirements
        global_requirements = self._extract_global_requirements(content)
        
        # Extract test steps
        steps = self._extract_steps(content)
        
        # Parse each step
        test_steps = []
        for step_num, step_text in steps:
            test_step = self._parse_step(step_num, step_text, global_requirements)
            test_steps.append(test_step)
        
        # Create test suite
        suite_name = file_path.stem.replace(" Requirements", "").replace("_", " ").title()
        
        test_suite = TestSuite(
            name=suite_name,
            global_requirements=global_requirements,
            steps=test_steps,
        )
        
        logger.info(f"Parsed {len(test_steps)} steps from {filepath}")
        return test_suite
    
    def _read_file(self, filepath: Path) -> str:
        """Read file content with proper encoding handling."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback to latin-1 if UTF-8 fails
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()
    
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
            
            # Extract bullet points
            lines = global_section.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Remove bullet markers
                line = re.sub(r'^[-*•]\s*', '', line)
                
                # Extract verifications
                verifications = self._extract_verifications(line)
                global_reqs.extend(verifications)
        
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
                    
                    # Determine severity (default to MAJOR)
                    severity = Severity.MAJOR
                    if any(word in sentence.lower() for word in ['critical', 'must', 'required']):
                        severity = Severity.CRITICAL
                    elif any(word in sentence.lower() for word in ['should', 'preferably']):
                        severity = Severity.MINOR
                    
                    verification = Verification(
                        text=verification_text,
                        severity=severity,
                        description=sentence,
                    )
                    verifications.append(verification)
                    break
        
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
        
        # Split into sentences/lines
        sentences = self._split_into_sentences(text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check each action type pattern
            for action_type, patterns in self.ACTION_PATTERNS.items():
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
                        else:
                            # Actions without values
                            target = match.group(1).strip()
                            value = None
                        
                        action = Action(
                            type=action_type,
                            target=target,
                            value=value,
                            description=sentence,
                        )
                        actions.append(action)
                        break
        
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
        """Split text into sentences, handling various formats."""
        # Split by periods, exclamation marks, and newlines
        sentences = re.split(r'[.!?]\s+|\n+', text)
        
        # Clean up sentences
        cleaned = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 3:
                cleaned.append(sentence)
        
        return cleaned

