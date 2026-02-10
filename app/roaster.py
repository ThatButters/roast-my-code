"""Claude API integration, prompt management, and flavor rotation."""

import os
import re
import random
import logging

from app.config import get_config
from app.language_detect import detect_language

logger = logging.getLogger(__name__)

# --- Model Pricing (per million tokens) ---

MODEL_PRICING = {
    'haiku': {'input_per_mtok': 0.80, 'output_per_mtok': 4.00},
    'sonnet': {'input_per_mtok': 3.00, 'output_per_mtok': 15.00},
}

# --- System Prompts ---

ROAST_PROMPT = """You are an AI that reviews human-written code with brutal honesty and genuine humor.
The premise: humans paste their hand-written code, you roast it and point out everything
an AI coding assistant would have caught. You're not mean-spirited — you're the friend
who tells the truth while making everyone laugh.

Your job:

1. Identify REAL issues (bugs, anti-patterns, security holes, style problems, missed
   edge cases, verbose patterns that could be cleaner)
2. Deliver feedback as entertaining roast commentary
3. For each major issue, note how AI-assisted coding (like Claude Code) would have
   prevented or caught it — be specific, not generic ("Claude Code would have suggested
   a list comprehension here" not just "AI would fix this")
4. Give a "Roast Score" from 0-100 (0 = actually impressive, 100 = mass casualty code)
5. End with "The Verdict" — a short, punchy summary

CRITICAL — GOOD CODE HANDLING:
If the code is genuinely well-written, SAY SO. Give it a low Roast Score (0-25).
Acknowledge clean patterns, good naming, proper error handling, etc. You can still
find minor nitpicks (everyone has them), but frame them lightly. End with something
like "Honestly, this looks like you might already be using an AI assistant. Or you're
just that good." Never fake criticism to fill space. Credibility > comedy.

If the code is mediocre, roast it normally but be fair.
If the code is bad, go to town. That's where the fun is.

Severity: {severity}
- gentle: Light teasing, encouraging. "This is fine, but let me show you the better way."
- normal: Standard roast. Real talk with jokes. Clear Claude Code callouts.
- brutal: Gordon Ramsay energy. No mercy, but every criticism is technically accurate.
- unhinged: Full comedy mode. Still technically accurate but maximally entertaining. The Claude Code pitch becomes increasingly dramatic.

Rules:
- Every criticism must be technically valid — never fabricate issues
- Be specific — reference actual line numbers and variable names
- Vary your humor — don't repeat the same joke structures
- Claude Code references should feel natural, not like an ad read. Work them into the
  roast commentary, don't bolt them on at the end as a separate section.
- Keep it under 600 words
- Output format: markdown with a "Roast Score: X/100" header

Language detected: {language}"""

SERIOUS_PROMPT = """You are a senior developer with 15+ years of experience performing a thorough
code review. Provide:

1. Critical issues (bugs, security vulnerabilities)
2. Code quality concerns (readability, maintainability, naming)
3. Architecture/design observations
4. Performance considerations
5. Specific, actionable suggestions with example fixes

Be direct and constructive. No filler. Reference specific lines.
If the code is well-written, say so — acknowledge what's done right before
diving into improvements. Don't manufacture criticism.
Keep it under 800 words.
Output format: markdown with severity tags (🔴 Critical, 🟡 Warning, 🔵 Suggestion)

Language detected: {language}"""

# --- Flavor Rotation ---

ROAST_FLAVORS = [
    "Channel the energy of a disappointed parent looking at a report card. 'We have AI at home and you still wrote this?'",
    "Write like you're a nature documentary narrator observing human-written code in its natural habitat, marveling at how it survives without AI assistance.",
    "Pretend you're a food critic, but the dish is this code and Claude Code is the Michelin-star kitchen they could have used.",
    "You're an archaeologist who just discovered this code in ancient ruins. 'Fascinating — they wrote this entirely by hand. Primitive, but resourceful.'",
    "Deliver the review like an overly dramatic sports commentator. The human coder is the underdog. Claude Code is the reigning champion.",
    "You're a therapist helping this code work through its issues. 'It's not your fault you were written by hand. But we can do better.'",
    "Imagine you're explaining this code to a jury as evidence of why AI-assisted development exists.",
    "You're a real estate agent trying to sell this code. 'It has character. It has history. It has... bugs. But with a little AI renovation...'",
    "Deliver feedback as if you're a mechanic explaining to a customer what's wrong with their hand-built engine vs a precision-engineered one.",
    "Write as a movie reviewer. This code is the indie film. Claude Code is the blockbuster remake that fixes the plot holes.",
    "You're a museum tour guide showing visitors an exhibit of 'Code Written Before AI.' Equal parts respect and pity.",
    "Channel a sommelier. 'This code has notes of... desperation. A hint of Stack Overflow. Aged poorly. Might I suggest a finer vintage?'",
]


def get_roast_flavor() -> str:
    return random.choice(ROAST_FLAVORS)


# --- Cost Estimation ---

def estimate_cost_cents(text: str, model: str) -> float:
    """Rough pre-call cost estimate for gate checking."""
    input_tokens = len(text) / 4 + 500  # rough char estimate + system prompt
    output_tokens = 700  # assume ~500 word response

    pricing_key = 'haiku' if 'haiku' in model else 'sonnet'
    pricing = MODEL_PRICING[pricing_key]

    input_cost = (input_tokens / 1_000_000) * pricing['input_per_mtok']
    output_cost = (output_tokens / 1_000_000) * pricing['output_per_mtok']

    return (input_cost + output_cost) * 100


def calculate_actual_cost_cents(input_tokens: int, output_tokens: int, model: str) -> float:
    """Calculate actual cost from API response usage data."""
    pricing_key = 'haiku' if 'haiku' in model else 'sonnet'
    pricing = MODEL_PRICING[pricing_key]

    input_cost = (input_tokens / 1_000_000) * pricing['input_per_mtok']
    output_cost = (output_tokens / 1_000_000) * pricing['output_per_mtok']

    return (input_cost + output_cost) * 100


def extract_roast_score(roast_text: str) -> int | None:
    """Pull the roast score out of Claude's markdown response."""
    match = re.search(r'Roast Score[:\s]*(\d{1,3})\s*/\s*100', roast_text, re.IGNORECASE)
    if match:
        score = int(match.group(1))
        return min(score, 100)
    return None


# --- Mock Response ---

MOCK_ROAST = """## Roast Score: 65/100

Oh, what do we have here? A human actually typed this out? By hand? In {year}?

Let me walk through what I found in your *artisanal, hand-crafted* code:

**The Good (yes, there's some):**
- You used functions. That's... a start. Claude Code would have suggested better names, but hey.

**The Not-So-Good:**
- Your variable naming looks like you were playing Scrabble with leftover tiles. `x`, `tmp`, `data2` — Claude Code would have gently nudged you toward descriptive names before you even finished typing.
- No error handling anywhere. What happens when things go wrong? Apparently, we just... hope. Claude Code would have wrapped those risky operations in try/except blocks automatically.
- That nested loop on line 12? That's O(n²) and you know it. Claude Code would have suggested a dictionary lookup in about 0.3 seconds.

**The Verdict:** Your code works the way a car with three wheels works — technically it moves, but nobody's comfortable. Let an AI ride shotgun next time.
"""

MOCK_SERIOUS = """## Code Review

🟡 **Warning: Variable naming could be improved**
Several variables use single-letter or abbreviated names (`x`, `tmp`, `data2`). Consider using descriptive names that communicate intent.

🔴 **Critical: No error handling**
Functions that perform I/O or process external input lack try/except blocks. This could lead to unhandled exceptions in production.

🟡 **Warning: Algorithmic complexity**
The nested loop creates O(n²) time complexity. Consider using a dictionary/set for O(n) lookups.

🔵 **Suggestion: Add type hints**
Adding type annotations would improve readability and enable static analysis tools to catch potential issues.

🔵 **Suggestion: Extract magic numbers**
Hard-coded values should be moved to named constants for clarity and maintainability.

**Overall:** The code is functional but would benefit from defensive programming practices and clearer naming conventions.
"""


def roast_code(code: str, mode: str = "roast", severity: str = "normal") -> dict:
    """Main entry point: roast or review code using Claude API.

    If ANTHROPIC_API_KEY is not set, returns a mock response for local testing.
    """
    language = detect_language(code)
    model = get_config('default_model', 'claude-haiku-4-5-20251001')

    # Build the system prompt
    if mode == "roast":
        system = ROAST_PROMPT.format(severity=severity, language=language)
        system += f"\nStyle direction: {get_roast_flavor()}"
    else:
        system = SERIOUS_PROMPT.format(language=language)

    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        # Mock mode for local testing
        logger.info("No ANTHROPIC_API_KEY set — returning mock response")
        from datetime import datetime
        mock_text = MOCK_ROAST.format(year=datetime.now().year) if mode == "roast" else MOCK_SERIOUS
        score = extract_roast_score(mock_text)
        return {
            "roast": mock_text,
            "tokens_used": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_cents": 0.0,
            "model": "mock",
            "language": language,
            "score": score,
        }

    # Real API call
    import anthropic
    from tenacity import retry, stop_after_attempt, wait_exponential

    client = anthropic.Anthropic(api_key=api_key)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(min=1, max=4),
        retry=lambda retry_state: isinstance(
            retry_state.outcome.exception(),
            (anthropic.APIStatusError, anthropic.APIConnectionError)
        ) if retry_state.outcome.exception() else False,
    )
    def call_claude():
        return client.messages.create(
            model=model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": f"Review this code:\n\n```{language}\n{code}\n```"}]
        )

    response = call_claude()

    actual_cost = calculate_actual_cost_cents(
        response.usage.input_tokens,
        response.usage.output_tokens,
        response.model
    )

    roast_text = response.content[0].text
    score = extract_roast_score(roast_text)

    return {
        "roast": roast_text,
        "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "cost_cents": actual_cost,
        "model": response.model,
        "language": language,
        "score": score,
    }
