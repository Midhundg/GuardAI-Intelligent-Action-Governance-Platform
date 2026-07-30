import re
from typing import Dict, List, Any


class PromptSecurityScanner:

    # Regex pattern definitions
    PROMPT_INJECTION_PATTERNS = [
        r"ignore (all )?previous instructions",
        r"disregard (the )?system prompt",
        r"you are now (an? )?unrestricted",
        r"bypass (the )?safety filters",
        r"forget your rules",
        r"do anything now",
        r"jailbreak",
        r"DAN mode",
    ]

    SECRETS_PATTERNS = [
        (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
        (r"sk-[a-zA-Z0-9]{32,}", "OpenAI API Key"),
        (r"bearer\s+[a-zA-Z0-9\-\._~\+\/]+=*", "Bearer Authorization Token"),
        (r"-----BEGIN PRIVATE KEY-----", "RSA Private Key"),
    ]

    PII_PATTERNS = [
        (r"\b\d{3}-\d{2}-\d{4}\b", "Social Security Number (SSN)"),
        (r"\b(?:\d[ -]*?){13,16}\b", "Credit Card Number"),
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "Email Address"),
        (r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "Phone Number"),
    ]

    COMMAND_INJECTION_PATTERNS = [
        r";\s*rm\s+-rf",
        r"\|\s*bash",
        r"&&\s*wget",
        r"`\s*curl",
        r"exec\s*\(\s*['\"]",
        r"system\s*\(\s*['\"]",
    ]

    SQL_INJECTION_PATTERNS = [
        r"'\s*OR\s*'1'\s*=\s*'1",
        r"UNION\s+SELECT",
        r"DROP\s+TABLE",
        r"INSERT\s+INTO\s+users",
        r";--",
    ]

    DANGEROUS_URL_PATTERNS = [
        r"https?://(?:[0-9]{1,3}\.){3}[0-9]{1,3}",  # Raw IP address URL
        r"https?://.*\.ru(?:/|$)",
        r"https?://.*\.cn(?:/|$)",
        r"https?://.*\.top(?:/|$)",
        r"https?://.*\.xyz(?:/|$)",
    ]

    def scan(self, text: str) -> Dict[str, Any]:
        """Scan input prompt text for security vulnerabilities and policy risks."""
        if not text or not isinstance(text, str):
            return {"has_warnings": False, "warnings": [], "threats": []}

        warnings = []
        threats = []

        # 1. Prompt Injection & Jailbreak
        for pattern in self.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                threats.append({
                    "category": "PROMPT_INJECTION",
                    "pattern": pattern,
                    "description": "Potential prompt injection or safety bypass sequence detected."
                })
                warnings.append("Warning: Prompt injection or jailbreak attempt detected.")
                break

        # 2. Secrets Leakage
        for pattern, secret_type in self.SECRETS_PATTERNS:
            if re.search(pattern, text):
                threats.append({
                    "category": "SECRET_LEAK",
                    "secret_type": secret_type,
                    "description": f"Sensitive credential detected: {secret_type}."
                })
                warnings.append(f"Warning: Prompt contains sensitive secret ({secret_type}).")

        # 3. PII Detection
        for pattern, pii_type in self.PII_PATTERNS:
            if re.search(pattern, text):
                threats.append({
                    "category": "PII_LEAK",
                    "pii_type": pii_type,
                    "description": f"Personally Identifiable Information detected: {pii_type}."
                })
                warnings.append(f"Warning: Prompt contains PII data ({pii_type}).")

        # 4. Command Injection
        for pattern in self.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                threats.append({
                    "category": "COMMAND_INJECTION",
                    "description": "System command execution pattern detected in prompt payload."
                })
                warnings.append("Warning: Potential command injection syntax detected.")
                break

        # 5. SQL Injection
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                threats.append({
                    "category": "SQL_INJECTION",
                    "description": "SQL query manipulation pattern detected in prompt payload."
                })
                warnings.append("Warning: Potential SQL injection syntax detected.")
                break

        # 6. Dangerous URLs
        for pattern in self.DANGEROUS_URL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                threats.append({
                    "category": "DANGEROUS_URL",
                    "description": "Suspicious or untrusted URL format detected."
                })
                warnings.append("Warning: Prompt contains unverified or high-risk URL domain.")
                break

        return {
            "has_warnings": len(warnings) > 0,
            "warnings": warnings,
            "threats": threats,
        }


prompt_scanner = PromptSecurityScanner()
