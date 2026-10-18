# frame.md: StockPulse pitch film design spec

Source of truth: the app's `frontend/css/tokens.css`. The film is light-only.

## Color
| Token | Hex | Use |
|---|---|---|
| `--bg` | `#F7F9FC` | Every scene background |
| `--surface` | `#FFFFFF` | Cards, browser frame |
| `--ink` | `#202A3B` | Headlines, body |
| `--ink-2` | `#667085` | Secondary text, footnotes |
| `--line` | `#E3E8EF` | Hairlines, card borders |
| `--indigo` | `#4F67E8` | Brand accent (logo, promise line, the travelling dot) |
| `--blue` | `#3478F6` | Anything **calculated** (deterministic): figures, equation tiles, forecast |
| `--ember` | `#E86A4A` | Anything an **AI model reads or writes**: extraction fields, agent briefing |
| `--green` | `#289879` | **Human approval** only |
| `--red` | `#D94F61` | The single risk moment (S07) |
| tints | `--blue-tint #EAF2FE`, `--ember-tint #FDF0EC`, `--green-tint #E7F5F0`, `--red-tint #FCEDEF`, `--indigo-tint #EEF1FD` | Chip and tile fills |

## Type
- Geist (variable, 400–600) for everything; Geist Mono for data, file names, and rules. Both are vendored in `assets/fonts/` (OFL-1.1).
- Scale at 1920×1080:
  - Display: 72 px / 600 / −0.025em
  - Headline: 56 px / 600
  - Title: 40 px / 500
  - Body: 28 px / 400
  - Label: 22 px / 500
  - Mono data: 24 px
  - Footnote: 18 px (minimum on screen)
- Ink-colored headlines, with the accent color used on at most one word per frame.

## Layout
- 12-column grid with a 120 px outer margin and 32 px gutters. Safe area: 96 px top and bottom.
- The bottom 150 px is reserved for burned-in captions. Content never sits there in scenes with VO.
- Cards: white, 1 px `--line` border, 14 px radius, shadow `0 18px 48px rgba(32,42,59,.08)`.
- App footage sits in a browser frame: white, 16 px radius, 1 px border, a 40 px top bar with three `--line` dots and a URL pill reading `stockpulse.app/#/…`. Default size 1440×810 (75%); punch-ins scale the inner still, never the frame chrome.

## Recurring elements
- **Legend** (S05–S09, lower left above the caption band): `● Calculated` (blue) and `● AI` (ember), 18 px.
- **Beam motif:** a 2 px ink hairline balance beam (S01, returns level in S12).
- **Thread:** a small indigo dot carrying "Cola 330ml" (S10).

## Motion
- Eases: `power3.out` for entrances, `power2.inOut` for camera moves, `sine.inOut` for ambient drift.
- Durations: 0.4–0.8 s for UI, 1.2–2 s for camera. Scene crossfades are 0.5 s.
- No bounces, glitches, whips, or 3D.
