"""Regex pattern-based language detection. No heavy dependencies needed."""

import re

LANGUAGE_PATTERNS = [
    ('python', [r'\bdef\s+\w+\s*\(', r'\bimport\s+\w+', r':\s*$', r'\bself\b', r'print\s*\(', r'if\s+__name__']),
    ('javascript', [r'\bfunction\s+\w+', r'\bconst\s+\w+', r'\blet\s+\w+', r'=>', r'console\.log', r'\brequire\(']),
    ('typescript', [r':\s*(string|number|boolean|any)\b', r'\binterface\s+\w+', r'<[A-Z]\w*>', r'\bas\s+\w+', r'\w+\s*:\s*\w+\s*[;,)]', r'\)\s*:\s*\w+\s*=>']),
    ('java', [r'\bpublic\s+(static\s+)?class\b', r'System\.out', r'\bvoid\s+\w+', r'@Override']),
    ('csharp', [r'\bnamespace\s+\w+', r'\busing\s+System', r'\bvar\s+\w+\s*=', r'\basync\s+Task']),
    ('go', [r'\bfunc\s+\w+', r'\bpackage\s+\w+', r':=', r'\bfmt\.\w+', r'\bgo\s+\w+']),
    ('rust', [r'\bfn\s+\w+', r'\blet\s+mut\b', r'\bimpl\s+\w+', r'->', r'\bpub\s+(fn|struct)']),
    ('ruby', [r'\bdef\s+\w+', r'\bend\s*$', r'\bputs\b', r'\brequire\s+', r'\battr_\w+']),
    ('php', [r'<\?php', r'\$\w+', r'\becho\b', r'\bfunction\s+\w+', r'->']),
    ('html', [r'<(!DOCTYPE|html|div|span|body|head)\b', r'class="', r'<script']),
    ('css', [r'\{[^}]*:\s*\w+;', r'\.([\w-]+)\s*\{', r'@media', r'#[\w-]+\s*\{']),
    ('sql', [r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\b', r'\bFROM\b.*\bWHERE\b']),
    ('bash', [r'^#!/bin/(bash|sh)', r'\becho\b', r'\bif\s+\[', r'\bfi\b', r'\besac\b']),
    ('c', [r'#include\s*<\w+\.h>', r'\bint\s+main\s*\(', r'printf\s*\(', r'\bmalloc\s*\(']),
    ('cpp', [r'#include\s*<\w+>', r'\bstd::', r'\bcout\b', r'\bclass\s+\w+\s*[:{]', r'\btemplate\s*<']),
    ('swift', [r'\bfunc\s+\w+', r'\bvar\s+\w+\s*:', r'\bguard\s+let\b', r'\bimport\s+Foundation']),
    ('kotlin', [r'\bfun\s+\w+', r'\bval\s+\w+', r'\bvar\s+\w+', r'\bwhen\s*\(']),
]


def detect_language(code: str) -> str:
    """Score each language by how many of its patterns match. Highest wins."""
    scores = {}
    for lang, patterns in LANGUAGE_PATTERNS:
        score = sum(1 for p in patterns if re.search(p, code, re.MULTILINE))
        if score > 0:
            scores[lang] = score

    if not scores:
        return "unknown"

    # TypeScript is a superset of JavaScript — if both match, prefer TS
    if 'typescript' in scores and 'javascript' in scores:
        scores['typescript'] += scores['javascript']

    return max(scores, key=scores.get)
