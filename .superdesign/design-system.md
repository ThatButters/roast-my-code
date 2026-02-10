# Roast My Code — Design System

## Product Context
**Roast My Code** is an AI-powered code review tool with a comedic premise: "Paste your puny human-written code. An AI will tell you what you did wrong." Claude roasts user code, pointing out real issues while showing how AI-assisted coding would have caught them. If the code is good, it gets genuine praise. A serious mode drops humor for legitimate code review.

**Target users:** Developers who enjoy humor, want code feedback, and share results socially.
**Core value:** Entertaining, shareable code roasts backed by real technical analysis.
**Key pages:** Landing page (code input), Result page (roast output + score gauge).

## Visual Identity

### Overall Vibe
A smug, confident AI terminal reviewing human work. Dark theme but alive — futuristic command center meets roast comedy stage. Playful arrogance, not generic SaaS. Think: a late-night comedy roast hosted by a machine.

### Color Palette
- **Background Primary:** #050505 (near-black)
- **Background Secondary:** #111111 (cards, elevated surfaces)
- **Background Input:** #0a0a14 (code textarea)
- **Accent Fire (Roast Mode):** #FF6B35 (primary action, fire/ember)
- **Accent Ember:** #FF8C5A (hover states, secondary fire)
- **Accent Serious (Serious Mode):** #3B82F6 (cool blue — visual shift when toggling modes)
- **Text Primary:** #E8E8F0
- **Text Secondary:** #8888A0
- **Text Muted:** #555570
- **Border:** #2A2A3E
- **Score Green (good code):** #22C55E
- **Score Yellow (mediocre):** #F59E0B
- **Score Red (bad code):** #EF4444

### Typography
- **Display/Headings:** 'Satoshi' or 'Space Grotesk', bold 700, tight tracking
- **Code areas:** 'JetBrains Mono' or 'Geist Mono', monospace
- **Body:** 'Inter', weight 400
- **Technical labels:** Monospace, uppercase, tracking 0.2em, 10-12px

### Key Design Elements
- Glassmorphism navigation with backdrop blur
- The Roast Score is a dramatic, animated SVG gauge/dial — not just a number. It dominates the result page.
- Fire/ember glow effects on the score (subtle, not distracting)
- Severity selector styled like difficulty levels in a game: Gentle 😏 / Normal 🔥 / Brutal 💀 / Unhinged 🤯
- Mode toggle between "Roast Mode" (warm fire tones) and "Serious Review" (cool blue shift)
- Share button designed to be irresistible — people share when the presentation is fun
- Subtle "Powered by Claude" badge in footer
- Dark code textarea with monospace font, character/line counter

### Copy & Microcopy
- Hero title: "Roast My Code"
- Hero subtitle: "Paste your puny human-written code. An AI will tell you what you did wrong."
- Textarea placeholder: "Paste your puny human-written code here. Let's see what you've done."
- Submit button: "Roast My Human Code 🔥"
- Loading: "Analyzing your human craftsmanship..."
- Error: "😵 Claude is having a moment. Your code was SO bad it broke the reviewer."
- Rate limited: "Easy there, glutton for punishment. You've used all your roasts for today."

### Result Page Personality
- Roast Score gauge dominates — big, animated, impossible to miss
- Low scores (good code, 0-25): green tones, congratulatory vibe
- High scores (bad code, 75-100): red/fire tones, dramatic presentation
- Share buttons prominent with pre-filled social text
- Code collapsible section if user opted to share

### Don't
- Don't make it look like a generic SaaS dashboard
- Don't use stock illustrations or bland placeholders
- Don't make serious mode an afterthought — it should feel premium and professional when toggled
