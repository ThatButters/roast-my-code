"""Input validation, markdown sanitization, share ID generation."""

import re
import secrets

import bleach
import markdown as md

from app.config import get_config

# Words that could look offensive in a URL
BLOCKLIST = {'ass', 'fuk', 'fck', 'nig', 'fag', 'cum', 'sex', 'wtf', 'die', 'kys'}

# Allowed HTML tags in rendered roast markdown
ALLOWED_TAGS = ['p', 'h1', 'h2', 'h3', 'h4', 'strong', 'em', 'code', 'pre',
                'ul', 'ol', 'li', 'br', 'blockquote', 'hr', 'span']
ALLOWED_ATTRS = {
    'code': ['class'],
    'span': ['class'],
}


def validate_input(code: str) -> tuple[bool, str]:
    """Validate code input. Returns (valid, error_message)."""
    if not code or not code.strip():
        return False, "Paste some code first. We can't roast nothing."

    max_chars = int(get_config('max_input_chars', '15000'))
    max_lines = int(get_config('max_input_lines', '500'))

    if len(code) > max_chars:
        return False, f"Too long ({len(code):,} chars). Max is {max_chars:,}."

    line_count = len(code.split('\n'))
    if line_count > max_lines:
        return False, f"Too many lines ({line_count}). Max is {max_lines}. Paste the worst part."

    return True, ""


def render_roast_markdown(text: str) -> str:
    """Convert markdown to sanitized HTML."""
    html = md.markdown(text, extensions=['fenced_code', 'codehilite', 'tables'])
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS,
                        protocols=['http', 'https', 'mailto'], strip=True)


def generate_share_id(length: int = 8) -> str:
    """Generate a URL-safe share ID, avoiding offensive substrings."""
    while True:
        candidate = secrets.token_urlsafe(length)[:length]
        lower = candidate.lower()
        if not any(word in lower for word in BLOCKLIST):
            return candidate


def get_roast_preview(roast_text: str, max_length: int = 150) -> str:
    """Get a plain text preview of a roast for OG tags and feeds."""
    # Strip markdown formatting
    plain = re.sub(r'[#*_`\[\]()]', '', roast_text)
    plain = re.sub(r'\n+', ' ', plain).strip()
    if len(plain) > max_length:
        return plain[:max_length].rsplit(' ', 1)[0] + '...'
    return plain
