"""Core security utilities for input validation, sanitization, and protection.

This module provides security hardening utilities as per Issue #197:
- Input sanitization for XSS prevention
- SQL injection prevention utilities
- Wallet address validation
- Content security utilities
"""

import re
import html
import logging
from typing import Optional, Any, Set
from urllib.parse import urlparse

import bleach

logger = logging.getLogger(__name__)

# Solana wallet address pattern (base58, 32-44 characters)
SOLANA_WALLET_PATTERN = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

# Maximum lengths for user inputs
MAX_TITLE_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 10000
MAX_COMMENT_LENGTH = 5000
MAX_WALLET_ADDRESS_LENGTH = 44

# Allowed HTML tags for sanitized content
ALLOWED_TAGS = ["p", "br", "b", "i", "u", "strong", "em", "ul", "ol", "li", "code", "pre", "a"]

# Allowed HTML attributes (only safe href for anchor tags)
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
}

# Allowed URL schemes for href attributes
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def sanitize_html(content: str, max_length: Optional[int] = None) -> str:
    """Sanitize HTML content using bleach library for robust XSS protection.
    
    Uses bleach.clean() with a proper HTML parser to remove dangerous elements
    and attributes while preserving safe formatting.
    
    Args:
        content: The HTML content to sanitize.
        max_length: Maximum allowed length (default: MAX_DESCRIPTION_LENGTH).
    
    Returns:
        Sanitized content safe for rendering.
    """
    if not content:
        return ""
    
    # Truncate if needed
    if max_length and len(content) > max_length:
        content = content[:max_length]
        logger.warning(f"Content truncated to {max_length} characters")
    
    # Use bleach for robust, parser-based HTML sanitization
    sanitized = bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,  # Remove disallowed tags entirely instead of escaping
    )
    
    return sanitized


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """Sanitize plain text input by removing potential XSS vectors.
    
    Args:
        text: The text to sanitize.
        max_length: Maximum allowed length.
    
    Returns:
        Sanitized text.
    """
    if not text:
        return ""
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    # Remove any HTML/script tags
    text = re.sub(r"<[^>]+>", "", text)
    
    # Remove control characters except newlines and tabs
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    
    # Normalize whitespace
    text = " ".join(text.split())
    
    return text.strip()


def validate_solana_wallet(address: str) -> bool:
    """Validate a Solana wallet address format.
    
    Args:
        address: The wallet address to validate.
    
    Returns:
        True if valid, False otherwise.
    """
    if not address or len(address) > MAX_WALLET_ADDRESS_LENGTH:
        return False
    return bool(SOLANA_WALLET_PATTERN.match(address))


def validate_url(url: str, allowed_schemes: Optional[list] = None) -> bool:
    """Validate a URL format and scheme.
    
    Args:
        url: The URL to validate.
        allowed_schemes: List of allowed schemes (default: ['http', 'https']).
    
    Returns:
        True if valid, False otherwise.
    """
    if not url:
        return False
    
    allowed_schemes = allowed_schemes or ["http", "https"]
    
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        if parsed.scheme.lower() not in allowed_schemes:
            return False
        return True
    except Exception:
        return False


def validate_github_url(url: str) -> bool:
    """Validate a GitHub URL.
    
    Args:
        url: The URL to validate.
    
    Returns:
        True if valid GitHub URL, False otherwise.
    """
    if not validate_url(url):
        return False
    
    parsed = urlparse(url)
    allowed_hosts = ["github.com", "www.github.com"]
    
    # Use hostname to avoid credential-based URLs like user:pass@github.com
    if not parsed.hostname:
        return False
    
    if parsed.hostname.lower() not in allowed_hosts:
        return False
    
    return True


# SQL identifier pattern: alphanumeric + underscore, starts with letter or underscore
SQL_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def is_valid_sql_identifier(identifier: str) -> bool:
    """Check if a SQL identifier is valid (no transformation).
    
    Valid identifiers:
    - Only alphanumeric characters and underscores
    - Starts with a letter or underscore
    - Non-empty
    
    Args:
        identifier: The SQL identifier to check.
    
    Returns:
        True if valid, False otherwise.
    """
    if not identifier:
        return False
    return bool(SQL_IDENTIFIER_PATTERN.match(identifier))


def sanitize_sql_identifier(identifier: str) -> str:
    """Validate and return a SQL identifier (table name, column name, etc).
    
    Only allows alphanumeric characters and underscores.
    Raises ValueError for invalid identifiers instead of silently transforming.
    
    Args:
        identifier: The SQL identifier to validate.
    
    Returns:
        The identifier if valid.
    
    Raises:
        ValueError: If identifier is empty or contains invalid characters.
    """
    if not identifier:
        raise ValueError("SQL identifier cannot be empty")
    
    if not SQL_IDENTIFIER_PATTERN.match(identifier):
        raise ValueError(
            f"Invalid SQL identifier '{identifier}': "
            "must contain only alphanumeric characters and underscores, "
            "and start with a letter or underscore"
        )
    
    return identifier


def escape_like_pattern(pattern: str) -> str:
    """Escape special characters in a LIKE pattern.
    
    Escapes %, _, and \\ to prevent wildcard injection.
    
    Args:
        pattern: The LIKE pattern to escape.
    
    Returns:
        Escaped pattern safe for LIKE queries.
    """
    if not pattern:
        return ""
    
    # Escape backslash first, then % and _
    pattern = pattern.replace("\\", "\\\\")
    pattern = pattern.replace("%", "\\%")
    pattern = pattern.replace("_", "\\_")
    
    return pattern


def is_safe_redirect(url: str, allowed_hosts: list) -> bool:
    """Check if a redirect URL is safe (same-origin or allowed host).
    
    Args:
        url: The redirect URL to check.
        allowed_hosts: List of allowed host names.
    
    Returns:
        True if safe, False otherwise.
    """
    if not url:
        return False
    
    # Relative URLs are safe
    if url.startswith("/") and not url.startswith("//"):
        return True
    
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower() in [h.lower() for h in allowed_hosts]
    except Exception:
        return False


class SecurityValidator:
    """Validator class for common security checks."""
    
    @staticmethod
    def validate_bounty_title(title: str) -> tuple[bool, str]:
        """Validate a bounty title.
        
        Args:
            title: The title to validate.
        
        Returns:
            Tuple of (is_valid, error_message).
        """
        if not title:
            return False, "Title is required"
        
        if len(title) > MAX_TITLE_LENGTH:
            return False, f"Title must be {MAX_TITLE_LENGTH} characters or less"
        
        # Check for suspicious patterns
        suspicious = ["<script", "javascript:", "onerror="]
        for pattern in suspicious:
            if pattern.lower() in title.lower():
                return False, "Invalid characters in title"
        
        return True, ""
    
    @staticmethod
    def validate_bounty_description(description: str) -> tuple[bool, str]:
        """Validate a bounty description.
        
        Args:
            description: The description to validate.
        
        Returns:
            Tuple of (is_valid, error_message).
        """
        if not description:
            return False, "Description is required"
        
        if len(description) > MAX_DESCRIPTION_LENGTH:
            return False, f"Description must be {MAX_DESCRIPTION_LENGTH} characters or less"
        
        return True, ""
    
    @staticmethod
    def validate_comment(comment: str) -> tuple[bool, str]:
        """Validate a comment.
        
        Args:
            comment: The comment to validate.
        
        Returns:
            Tuple of (is_valid, error_message).
        """
        if not comment:
            return False, "Comment is required"
        
        if len(comment) > MAX_COMMENT_LENGTH:
            return False, f"Comment must be {MAX_COMMENT_LENGTH} characters or less"
        
        return True, ""