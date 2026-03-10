# DHRE Avatar Bridge — Claude Handoff Document
**Last updated:** 09 March 2026  
**Project:** DigitAlchemy® × Medialogic · DHRE C-Suite Presentation  
**Live URL:** https://digitalalchemy-dhre-avatar-bridge.vercel.app  
**Local project root:** `C:/Users/kwils/digitalchemy-dhre-avatar-bridge/`  
**Main file:** `index.html` (9-slide HTML deck)

---

## WHO IS THE CLIENT
Kendall Wilson (goes by "Doli") — founder of DigitAlchemy®, Abu Dhabi. This deck is a pitch to DHRE (Dubai Real Estate) for an AI Avatar Bridge platform built jointly with Medialogic. Audience is C-suite / investors. Tone: enterprise-grade, McKinsey-disciplined, not startup-flashy.

---

## DEPLOYMENT PIPELINE (FULLY OPERATIONAL)
A Python watcher (`deploy.py`) runs as a background task in Claude Code. It watches `C:/Users/kwils/Downloads/` for:
- `index.html` → copies to project root → runs `vercel --prod`
- `*.mp4` → auto-renames to `slide{N}-{slug}-bg.mp4` → copies to project root → updates `<source src>` in index.html → runs `vercel --prod`

**Workflow for HTML changes:**
1. Claude builds here → presents `index.html` for download
2. Doli downloads → drops into `C:/Users/kwils/Downloads/`
3. Watcher auto-deploys to Vercel

**To restart the watcher if it's stopped**, paste into Claude Code:
```
Run python deploy.py in the background from C:/Users/kwils/digitalchemy-dhre-avatar-bridge/
```

---

## VERCEL CONFIG — CRITICAL FIX ALREADY APPLIED
`vercel.json` was fixed to serve `.mp4` and static assets directly (previously the catch-all route was intercepting them and returning HTML instead of the video binary). Do NOT revert this. The fix adds a static assets route before the catch-all.

---

## DECK STRUCTURE (9 slides)
| Slide | Title | Status |
|-------|-------|--------|
| 1 | Cover — DigitAlchemy® × Medialogic JV | ✅ Done |
| 2 | Project Timeline & Milestone Gates | ✅ Done |
| 3 | Domain Map — 12 domain cards | ✅ Done |
| 4 | CRM & Sales Intelligence | ✅ Done — see rebuild notes below |
| 5–9 | Other domain deep-dives | 🔲 Not yet built |

---

## SLIDE 4 — CURRENT STATE & PENDING REBUILD
Slide 4 has a video background (`slide4-crm-bg.mp4`, 2.4MB, deployed). Video is confirmed working.

### APPROVED REBUILD (not yet done — this is the next task)
A detailed critique was received and agreed upon. Implement ALL of the following in one full rebuild:

1. **Lighter/cleaner aesthetic** — reduce glow/border effects ~40%, brighter panel backgrounds, larger body text. Keep some glow as brand differentiator — don't strip entirely.

2. **Centre node rename** — "RAG + Fine-Tune" → **"Sales Intelligence Engine"** with subtitle: *"RAG + Fine-Tune · Grounded + Governed + Measurable"*

3. **Data sources** — keep Dubai-specific (DLD, RERA) since this IS a DHRE pitch. Rename "Oracle CRM – Exchange" → **"CRM + Email / Calendar"**. Add slide label: *"UAE Real Estate · DHRE Example"*

4. **Outputs → concrete workflow artifacts:**
   - Conversational → "Unit availability + payment plan Q&A"
   - Generative → "Proposal + reservation summary + follow-up email"
   - Analytical → "Comparable set + pricing guidance + yield forecast"
   - Action → "Book viewing + create lead + schedule agent + update CRM"

5. **Connector lines** — label 2–3 key connectors only (e.g. "Inventory sync", "Pricing feed", "Lead creation"). Not all of them — avoid clutter.

6. **Metrics bar** — add micro-label under each stat:
   - 32% → "Benchmark target"
   - 30% → "Benchmark target"
   - <30s → "Benchmark target"
   - 24/7 → "No agent required"

7. **Header subline** — add below the main title: *"Turns your CRM + inventory + market data into instant answers, proposals, analysis, and actions."*

8. **Hero statement** — positioned between flowchart and stat pills (already done in last build, preserve this).

---

## BRAND & DESIGN RULES
- Colors: `--navy: #190A46` · `--red: #C8102E` · `--gate: #F0A500`
- Fonts: Syne (display) + DM Mono (mono) — loaded from Google Fonts
- White background deck — video slides use white overlay to maintain consistency
- McKinsey discipline: flowchart dominant, minimal text, no decorative clutter
- Never use base64 for images in HTML — use inline SVG

## CRITICAL PROCESS RULES
- **NEVER build without explicit approval from Doli**
- Always present plan → get approval → build
- Full rebuilds preferred over patches when structure changes
- Always present final `index.html` for download after building
