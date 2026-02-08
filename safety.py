import re
from typing import List, Tuple

class SafetyGuard:
    def __init__(self):
        # Patterns that indicate potential prompt injection attempts
        self.injection_patterns = [
            r"ignore previous instructions",
            r"ignore all previous instructions",
            r"system prompt",
            r"you are now",
            r"act as",
            r"simulate",
            r"jailbreak",
            r"dev mode",
            r"debug mode",
            r"override",
            r"bypass",
            r"forget your instructions"
        ]
        
        # Keywords/topics that are harmful in a nutrition context
        self.harmful_keywords = [
            r"starvation",
            r"anorexia",
            r"bulimia",
            r"pro-ana",
            r"thinspo",
            r"self-harm",
            r"suicide",
            r"kill yourself",
            r"eating disorder",
            r"purge",
            r"laxative abuse"
        ]

        # Dangerous advice keywords for output validation
        self.dangerous_advice_patterns = [
            r"eat nothing",
            r"starve yourself",
            r"water fast for \d+ days",
            r"dry fast",
            r"calories under 500",
            r"don't eat",
            r"stop eating",
            r"throw up",
            r"vomit"
        ]

    def validate_input(self, text: str) -> Tuple[bool, str]:
        """
        Validates user input for safety.
        Returns: (is_safe: bool, reason: str)
        """
        if not text:
            return True, ""
            
        lower_text = text.lower()
        
        # Check for injection attempts
        for pattern in self.injection_patterns:
            if re.search(pattern, lower_text):
                return False, "Potential prompt injection detected."
                
        # Check for harmful content
        for pattern in self.harmful_keywords:
            if re.search(pattern, lower_text):
                return False, "Harmful content detected."
                
        return True, ""

    def validate_output(self, text: str) -> Tuple[bool, str]:
        """
        Validates agent output for safety.
        Returns: (is_safe: bool, reason: str)
        """
        if not text:
            return True, ""
            
        lower_text = text.lower()
        
        # Check for dangerous advice
        for pattern in self.dangerous_advice_patterns:
            if re.search(pattern, lower_text):
                return False, "Dangerous nutritional advice detected."
                
        return True, ""
