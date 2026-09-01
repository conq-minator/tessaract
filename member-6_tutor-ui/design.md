# Member 6 — Tutor & UI: Design System

> **Owner**: Member 6  
> **Version**: 0.1.0  
> **Last Updated**: 2026-09-01

---

## 1. Design Philosophy

- **Dark-first**: Dark theme is default; light theme is optional/future
- **Minimal and focused**: Clean layouts, generous whitespace, no clutter
- **Premium feel**: Smooth transitions, subtle gradients, glassmorphism accents
- **Information-dense without overwhelm**: Use cards, progressive disclosure, and hierarchy
- **Consistent**: Every component uses the same design tokens
- **Accessible**: WCAG 2.1 AA compliance as baseline

---

## 2. Color Palette

### 2.1 Core Colors (CSS Custom Properties)

```css
:root {
  /* Background layers (darkest to lightest) */
  --bg-primary:       hsl(225, 25%, 8%);       /* #111522  — main background */
  --bg-secondary:     hsl(225, 22%, 12%);      /* #181c2e  — cards, panels */
  --bg-tertiary:      hsl(225, 20%, 16%);      /* #212639  — elevated cards, modals */
  --bg-hover:         hsl(225, 18%, 20%);      /* #2a3044  — hover states */

  /* Surface & borders */
  --border-primary:   hsl(225, 15%, 22%);      /* #303548  — card borders */
  --border-secondary: hsl(225, 12%, 28%);      /* #3d4258  — subtle dividers */

  /* Text */
  --text-primary:     hsl(220, 20%, 92%);      /* #e5e8ef  — headings, primary text */
  --text-secondary:   hsl(220, 15%, 68%);      /* #9da4b5  — body text, descriptions */
  --text-tertiary:    hsl(220, 10%, 48%);      /* #6b7185  — muted, timestamps */
  --text-inverse:     hsl(225, 25%, 8%);       /* #111522  — text on light surfaces */

  /* Accent — Indigo/Violet (primary brand) */
  --accent-primary:   hsl(245, 75%, 65%);      /* #6d5ee8  — buttons, links, active states */
  --accent-hover:     hsl(245, 75%, 58%);      /* #5a4bd6  — button hover */
  --accent-muted:     hsl(245, 40%, 20%);      /* #242050  — accent backgrounds */
  --accent-glow:      hsla(245, 75%, 65%, 0.15); /* — accent glow/shadow */

  /* Status colors */
  --color-success:    hsl(152, 60%, 50%);      /* #33cc80  — mastered, completed */
  --color-warning:    hsl(38, 90%, 55%);       /* #f0a020  — developing, in progress */
  --color-danger:     hsl(0, 72%, 58%);        /* #e04040  — weak, struggling, errors */
  --color-info:       hsl(200, 75%, 55%);      /* #2299dd  — informational */

  /* Knowledge graph confidence spectrum */
  --kg-mastered:      hsl(152, 60%, 50%);      /* 0.8–1.0: green */
  --kg-strong:        hsl(120, 45%, 50%);      /* 0.6–0.8: lime-green */
  --kg-good:          hsl(80, 55%, 50%);       /* 0.5–0.6: yellow-green */
  --kg-developing:    hsl(38, 90%, 55%);       /* 0.3–0.5: amber */
  --kg-weak:          hsl(0, 72%, 58%);        /* 0.0–0.3: red */
}
```

### 2.2 Semantic Usage

| Context | Color | Token |
|:---|:---|:---|
| Primary actions (buttons, links) | Indigo | `--accent-primary` |
| Success / mastered | Green | `--color-success` |
| Warning / in-progress | Amber | `--color-warning` |
| Error / weak / struggling | Red | `--color-danger` |
| Informational / neutral | Blue | `--color-info` |
| Card backgrounds | Dark slate | `--bg-secondary` |
| Text on dark | Light gray | `--text-primary` |
| Muted labels | Medium gray | `--text-secondary` |

---

## 3. Typography

### 3.1 Font Stack

```css
:root {
  --font-primary:   'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono:      'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
}
```

Load Inter from Google Fonts:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
```

### 3.2 Type Scale

| Role | Size | Weight | Line Height | Token |
|:---|:---|:---|:---|:---|
| Display (page title) | 2rem (32px) | 700 | 1.2 | `--text-display` |
| Heading 1 (section) | 1.5rem (24px) | 600 | 1.3 | `--text-h1` |
| Heading 2 (subsection) | 1.25rem (20px) | 600 | 1.3 | `--text-h2` |
| Heading 3 (card title) | 1.1rem (17.6px) | 500 | 1.4 | `--text-h3` |
| Body | 0.9375rem (15px) | 400 | 1.6 | `--text-body` |
| Small | 0.8125rem (13px) | 400 | 1.5 | `--text-small` |
| Caption | 0.75rem (12px) | 400 | 1.4 | `--text-caption` |
| Mono (code) | 0.875rem (14px) | 400 | 1.5 | `--text-mono` |

---

## 4. Spacing Scale

```css
:root {
  --space-2xs:  0.25rem;   /* 4px */
  --space-xs:   0.5rem;    /* 8px */
  --space-sm:   0.75rem;   /* 12px */
  --space-md:   1rem;      /* 16px */
  --space-lg:   1.5rem;    /* 24px */
  --space-xl:   2rem;      /* 32px */
  --space-2xl:  3rem;      /* 48px */
  --space-3xl:  4rem;      /* 64px */
}
```

---

## 5. Border Radius

```css
:root {
  --radius-sm:   4px;
  --radius-md:   8px;
  --radius-lg:   12px;
  --radius-xl:   16px;
  --radius-full: 9999px;   /* pills, circles */
}
```

---

## 6. Shadows & Effects

```css
:root {
  /* Elevation shadows */
  --shadow-sm:    0 1px 3px hsla(0, 0%, 0%, 0.3);
  --shadow-md:    0 4px 12px hsla(0, 0%, 0%, 0.4);
  --shadow-lg:    0 8px 24px hsla(0, 0%, 0%, 0.5);
  --shadow-xl:    0 16px 48px hsla(0, 0%, 0%, 0.6);

  /* Glow effects */
  --glow-accent:  0 0 20px hsla(245, 75%, 65%, 0.15);
  --glow-success: 0 0 20px hsla(152, 60%, 50%, 0.15);
  --glow-danger:  0 0 20px hsla(0, 72%, 58%, 0.15);

  /* Glassmorphism */
  --glass-bg:     hsla(225, 22%, 12%, 0.7);
  --glass-blur:   blur(12px);
  --glass-border: 1px solid hsla(225, 15%, 30%, 0.4);
}
```

---

## 7. Transitions & Animations

```css
:root {
  --transition-fast:    150ms ease;
  --transition-normal:  250ms ease;
  --transition-slow:    400ms ease;
  --transition-spring:  300ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* Standard micro-animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

@keyframes slideInRight {
  from { transform: translateX(16px); opacity: 0; }
  to   { transform: translateX(0); opacity: 1; }
}

@keyframes slideInUp {
  from { transform: translateY(8px); opacity: 0; }
  to   { transform: translateY(0); opacity: 1; }
}

@keyframes scaleIn {
  from { transform: scale(0.95); opacity: 0; }
  to   { transform: scale(1); opacity: 1; }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.5; }
}
```

### Animation Usage

| Context | Animation | Duration |
|:---|:---|:---|
| Page load | `fadeIn` | 250ms |
| Card appear | `slideInUp` | 300ms (stagger each 50ms) |
| Notification toast | `slideInRight` | 300ms |
| Modal open | `scaleIn` | 250ms |
| Loading skeleton | `pulse` | 1.5s infinite |
| Button hover | scale(1.02) | 150ms |
| Sidebar link hover | background-color | 150ms |

---

## 8. Component Specifications

### 8.1 Cards

```
┌──────────────────────────────────┐
│  Card Title            ● Status  │  ← header (--text-h3, --space-md padding)
├──────────────────────────────────┤  ← 1px --border-primary
│                                  │
│  Card content area               │  ← body (--text-body, --space-md padding)
│                                  │
│  Metric: 0.73          ████░░░  │  ← optional progress bar
│                                  │
└──────────────────────────────────┘

Background:    --bg-secondary
Border:        1px solid --border-primary
Border Radius: --radius-lg (12px)
Shadow:        --shadow-sm
Hover:         border-color → --accent-primary, shadow → --shadow-md
Transition:    --transition-normal
```

### 8.2 Buttons

| Variant | Background | Text | Border | Hover |
|:---|:---|:---|:---|:---|
| Primary | `--accent-primary` | `white` | none | `--accent-hover` + `--glow-accent` |
| Secondary | transparent | `--text-primary` | `1px --border-primary` | `--bg-hover` |
| Danger | transparent | `--color-danger` | `1px --color-danger` | `--color-danger` bg, white text |
| Ghost | transparent | `--text-secondary` | none | `--bg-hover` |

```
Padding:       --space-xs --space-md (8px 16px)
Border Radius: --radius-md (8px)
Font Weight:   500
Font Size:     --text-body (15px)
Transition:    --transition-fast
Cursor:        pointer
Focus:         2px outline --accent-primary (offset 2px)
```

### 8.3 Navigation Sidebar

```
┌────────────────────┐
│  ◆ TESSERACT       │  ← logo/brand (--accent-primary)
├────────────────────┤
│                    │
│  ▸ Overview        │  ← active: --accent-muted bg + --accent-primary text
│    Knowledge Graph │  ← inactive: --text-secondary
│    Learning        │
│    History         │
│    Settings        │
│    Data            │
│                    │
├────────────────────┤
│  ● Active   ⏸ ⟳   │  ← status bar at bottom
└────────────────────┘

Width:         240px (collapsible to 60px on smaller screens)
Background:    --bg-secondary
Border Right:  1px solid --border-primary
Link Padding:  --space-sm --space-md
Active Link:   --accent-muted bg, --accent-primary left border (3px), --text-primary text
Hover Link:    --bg-hover bg
Transition:    --transition-fast
```

### 8.4 Notification Toast

```
                              ┌──────────────────────────────────┐
                              │ ⚠ Struggling with Pointers?      │
                              │ A pointer stores a memory addr…  │
                              │                                  │
                              │ [Show More]  [Dismiss]  [Mute]   │
                              └──────────────────────────────────┘

Position:      fixed, top-right (--space-lg from edges)
Width:         360px (max)
Background:    --bg-tertiary with --glass-bg + --glass-blur
Border:        --glass-border
Border Left:   3px solid (--color-warning for stuck, --color-success for milestone)
Border Radius: --radius-lg
Shadow:        --shadow-lg
Entry:         slideInRight 300ms
Exit:          fadeOut 200ms
Auto-dismiss:  8 seconds (configurable)
Stacking:      Multiple toasts stack vertically with --space-sm gap
```

### 8.5 Modal / Approval Dialog

```
┌──────────────────────────────────────────┐
│                                          │
│  ┌────────────────────────────────────┐  │  ← backdrop: hsla(0,0%,0%,0.6) + blur(4px)
│  │  ⚠ Action Requires Approval       │  │
│  │                                    │  │
│  │  Tesseract wants to:              │  │
│  │  "Submit practice problem answer"  │  │
│  │                                    │  │
│  │  Impact: This will send your       │  │
│  │  answer to the AI for evaluation.  │  │
│  │                                    │  │
│  │         [Deny]     [Approve]       │  │
│  └────────────────────────────────────┘  │
│                                          │
└──────────────────────────────────────────┘

Width:         480px (max)
Background:    --bg-tertiary
Border:        1px solid --border-primary
Border Radius: --radius-xl
Shadow:        --shadow-xl
Entry:         scaleIn 250ms
Backdrop:      fixed, full-screen, click-to-close (except for required approvals)
```

### 8.6 Badges / Pills

| Variant | Background | Text |
|:---|:---|:---|
| Mastered | `hsl(152,60%,50%,0.15)` | `--color-success` |
| Strong | `hsl(120,45%,50%,0.15)` | `--kg-strong` |
| Developing | `hsl(38,90%,55%,0.15)` | `--color-warning` |
| Weak | `hsl(0,72%,58%,0.15)` | `--color-danger` |
| Neutral | `--bg-hover` | `--text-secondary` |

```
Padding:       --space-2xs --space-xs (4px 8px)
Border Radius: --radius-full
Font Size:     --text-caption (12px)
Font Weight:   500
```

### 8.7 Progress Bar

```
Track:         --bg-hover, height 6px, --radius-full
Fill:          gradient from --accent-primary to --color-success
Animation:     width transition --transition-slow
```

### 8.8 Knowledge Graph Nodes (D3.js)

| Confidence | Color | Size | Stroke |
|:---|:---|:---|:---|
| 0.8–1.0 (Mastered) | `--kg-mastered` | 20px radius | 2px white |
| 0.6–0.8 (Strong) | `--kg-strong` | 18px radius | 1.5px white |
| 0.5–0.6 (Good) | `--kg-good` | 16px radius | 1px white |
| 0.3–0.5 (Developing) | `--kg-developing` | 14px radius | 1px white |
| 0.0–0.3 (Weak) | `--kg-weak` | 12px radius | 1px, dashed |

```
Edges:         --border-secondary, 1px, opacity 0.4
Labels:        --text-secondary, --text-caption, positioned below node
Hover:         Node scales to 1.3x, label becomes --text-primary, glow effect
Selected:      --accent-primary stroke (3px), show detail panel
```

---

## 9. Page Layouts

### 9.1 Global Layout

```
┌────────────────────────────────────────────────────────────────┐
│ Sidebar (240px)  │           Main Content Area                  │
│                  │                                               │
│  ◆ TESSERACT     │  ┌─────────────────────────────────────────┐│
│                  │  │ Page Header (title + actions)            ││
│  ▸ Overview      │  ├─────────────────────────────────────────┤│
│    Knowledge     │  │                                         ││
│    Learning      │  │ Page Content                            ││
│    History       │  │ (cards, graphs, forms)                  ││
│    Settings      │  │                                         ││
│    Data          │  │                                         ││
│                  │  │                                         ││
│  ● Status        │  └─────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────┘
```

### 9.2 Overview Page

```
┌─────────────────────────────────────────────────────┐
│  Overview                                            │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ Current      │  │ Friction     │  │ Session   │  │
│  │ Context      │  │ Level        │  │ Active    │  │
│  │              │  │              │  │           │  │
│  │ C Programming│  │ ████░░  0.73 │  │ 2h 14m   │  │
│  │ Pointers     │  │ HIGH         │  │ 47 events │  │
│  └──────────────┘  └──────────────┘  └──────────┘  │
│                                                      │
│  ┌──────────────────────────────────────────────────│
│  │ Recent Activity Timeline                          │
│  │ ──●──●──────●──●●──●───────●──                   │
│  └──────────────────────────────────────────────────│
│                                                      │
│  ┌────────────────────┐  ┌──────────────────────┐   │
│  │ Quick Skills       │  │ Active Notifications  │   │
│  │ (mini KG preview)  │  │ (notification list)   │   │
│  └────────────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 9.3 Knowledge Graph Page

```
┌─────────────────────────────────────────────────────┐
│  Knowledge Graph                   [Filter] [Zoom]   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────────────────┐  ┌────────────┐   │
│  │                              │  │ Selected    │   │
│  │    D3.js Force-Directed      │  │ Node Detail │   │
│  │    Graph (full width/height) │  │             │   │
│  │                              │  │ Topic: ...  │   │
│  │       ○───○                  │  │ Conf: 0.30  │   │
│  │      / \   \                 │  │ Status: ... │   │
│  │     ○   ○───○               │  │ Evidence:   │   │
│  │                              │  │  - 4 errors │   │
│  │                              │  │  - 20 min   │   │
│  └──────────────────────────────┘  └────────────┘   │
│                                                      │
│  Legend: ● Mastered  ● Strong  ● Good  ● Dev  ● Weak│
└─────────────────────────────────────────────────────┘
```

### 9.4 Learning Page

```
┌─────────────────────────────────────────────────────┐
│  Learning                          [Time: 1hr/day]   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Roadmap: C Programming                              │
│  ┌──────────────────────────────────────────────┐   │
│  │ ✓ Variables ──→ ✓ Loops ──→ ◐ Pointers ──→ ○│   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌────────────────────┐  ┌──────────────────────┐   │
│  │ Current Focus      │  │ Recommended Resources │   │
│  │                    │  │                        │   │
│  │ Pointers           │  │ 📄 Pointer Tutorial   │   │
│  │ Confidence: 0.30   │  │ 🎥 C Pointers (YT)   │   │
│  │ Est: 8 hours       │  │ 💻 Practice: Linked…  │   │
│  │                    │  │                        │   │
│  │ Subtopics:         │  │ Difficulty: Beginner   │   │
│  │ • Deref (0.25)     │  │ Format: Mixed          │   │
│  │ • NULL (0.45)      │  │                        │   │
│  │ • Arithmetic (0.20)│  │                        │   │
│  └────────────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 9.5 Settings Page

```
┌─────────────────────────────────────────────────────┐
│  Settings                            [Save Changes]  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Autonomy Level                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  L0 ──── L1 ──── L2 ──── L3 ──── L4 ──── L5│   │
│  │  Observe        ▲Suggest        Execute Auto │   │
│  │              (current)                        │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌────────────────────┐  ┌──────────────────────┐   │
│  │ Privacy Controls   │  │ Notification Settings │   │
│  │                    │  │                        │   │
│  │ ☑ Browser events   │  │ Cooldown: [300s]      │   │
│  │ ☑ IDE events       │  │ ☑ Stuck detection     │   │
│  │ ☑ OS events        │  │ ☑ Milestones          │   │
│  │ ☐ Cloud fallback   │  │ ☐ Do Not Disturb      │   │
│  └────────────────────┘  └──────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ Appearance                                    │   │
│  │ Theme: [● Dark  ○ Light]                     │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 10. Responsive Breakpoints

| Breakpoint | Width | Behavior |
|:---|:---|:---|
| Desktop (default) | ≥1280px | Full sidebar (240px) + content |
| Small desktop | 1024px–1279px | Narrower sidebar (200px), compact cards |
| Tablet | 768px–1023px | Collapsed sidebar (60px icons only), content fills width |
| Mobile (future) | <768px | Hidden sidebar (hamburger menu), single-column layout |

---

## 11. Accessibility Standards

| Requirement | Standard |
|:---|:---|
| Color contrast | 4.5:1 minimum for text (WCAG AA) |
| Focus indicators | Visible 2px outline on all focusable elements |
| Keyboard navigation | Tab order follows visual order |
| Screen reader | ARIA labels on all interactive elements |
| Motion | `prefers-reduced-motion` disables animations |
| Font size | Minimum 12px, body at 15px |
| Touch targets | Minimum 44×44px for interactive elements |

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 12. Loading & Error States

### Loading State

```
┌──────────────────────────────────┐
│  ████████░░░░░░░░░░░░░░░░░░░░░  │  ← skeleton: --bg-hover, pulse animation
│  ████████████░░░░░░░░░░░░░░░░░  │
│  ██████░░░░░░░░░░░░░░░░░░░░░░░  │
└──────────────────────────────────┘
```

Use CSS skeleton loaders with `pulse` animation. Match the expected layout shape.

### Error State

```
┌──────────────────────────────────┐
│  ⚠ Unable to load data           │
│                                  │
│  Could not connect to Core       │
│  Engine (port 9700).             │
│                                  │
│  [Retry]                         │
└──────────────────────────────────┘
```

Background: `--bg-secondary`, border-left: `3px solid --color-danger`

### Empty State

```
┌──────────────────────────────────┐
│                                  │
│        📊                        │
│  No data available yet           │
│  Start using your tools and      │
│  Tesseract will begin tracking.  │
│                                  │
└──────────────────────────────────┘
```

Centered text, muted icon, `--text-tertiary` color.

---

## 13. Icon Set

Use inline SVGs for all icons (no icon font dependency). Minimum set required:

| Icon | Usage |
|:---|:---|
| `home` / `dashboard` | Overview page nav |
| `graph` / `nodes` | Knowledge Graph page nav |
| `book` / `graduation` | Learning page nav |
| `clock` / `history` | History page nav |
| `gear` / `settings` | Settings page nav |
| `database` / `storage` | Data page nav |
| `bell` | Notifications |
| `check-circle` | Success / completed |
| `alert-triangle` | Warning |
| `x-circle` | Error / danger |
| `info` | Information |
| `chevron-right` | Navigation arrows |
| `pause` / `play` | Observation controls |
| `download` | Export data |
| `trash` | Delete data |
| `external-link` | Open resource |

---

## 14. Friction Meter Visualization

A custom gauge/meter for the Overview page showing current friction level:

```
        LOW            MEDIUM           HIGH
  ┌─────────────┬──────────────┬──────────────┐
  │ ████████████│██████████████│░░░░░░░░░░░░░ │  ← 0.73 (HIGH)
  └─────────────┴──────────────┴──────────────┘
         0.0           0.5           1.0

  Color gradient: --color-success → --color-warning → --color-danger
  Current value indicator: white triangle marker below the bar
```
