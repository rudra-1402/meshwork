# MeshWork — Form Composition System v2
### Architecture Reference & AI Generation Prompt
#### Covers: Auth, College Registration, Questionnaire, Profile Edit, Team Create, Project Create

---

## THE PROBLEM BEING SOLVED

Without this system, every new form page requires:
- Re-explaining the split-screen layout and animations
- Re-implementing field state, validation, and error handling
- Re-building the pill-morph inputs and arrow-slide button
- Re-wiring multi-step logic from scratch

With this system, a new page is:
1. A config file (plain JS, no JSX, no design knowledge)
2. A 10-line page file (compose shell + engine + config)

The person building the new page writes only what is NEW about it.
Everything visual, animated, and structural is inherited.

---

## ARCHITECTURE OVERVIEW

```
┌──────────────────────────────────────────────────────────────────┐
│  PAGE LAYER                                                       │
│  Auth.jsx  CollegeReg.jsx  Questionnaire.jsx  ProfileEdit.jsx…  │
│  ~10 lines each. Composes shell + engine + config.               │
├──────────────────────────────────────────────────────────────────┤
│  CONFIG LAYER (plain JS, no JSX)                                 │
│  authConfig.js  collegeRegConfig.js  questionnaireConfig.js…    │
│  Defines: steps, fields, left panel, submit logic, navigation.  │
├──────────────────────────────────────────────────────────────────┤
│  ENGINE LAYER                                                     │
│  FormEngine.jsx                                                   │
│  Reads config. Renders fields. Manages step state, validation,  │
│  transitions, submit. Plugin slots for answer types.            │
├──────────────────────────────────────────────────────────────────┤
│  SHELL LAYER                                                      │
│  AuthShell.jsx                                                    │
│  The visual container. Left panel (image OR step info).         │
│  Right floating card. Brand wordmark. Animations.               │
├──────────────────────────────────────────────────────────────────┤
│  PRIMITIVE LAYER                                                  │
│  Field  StyledInput  PasswordInput  SubmitButton                │
│  ModeToggleLink  StepProgressBar  AnswerRegistry                │
└──────────────────────────────────────────────────────────────────┘
```

**Dependency rule (strict, non-negotiable):**
```
Page → Config → FormEngine → AuthShell → Primitives
```
No layer imports from a layer above it. No circular dependencies.

---

## THE SIX PAGES AND THEIR PROFILES

| Page | Steps | Left Panel Mode | Answer Types | Terminal State |
|---|---|---|---|---|
| Auth | 1 (mode toggle) | Image, crossfades on mode change | text, email, password | Navigate to dashboard |
| College Registration | 1 | Image, static | text, email, password | Navigate to admin dashboard |
| Questionnaire | 5–7 | Step metadata (title + description + progress) | likert, multi-select, textarea, single-select | Scoring loader → Results reveal |
| Profile Edit | 1 | Image, static OR no shell (modal) | text, textarea, chip-select | Toast success, stay on page |
| Team Create | 3 | Image, crossfades per step | text, textarea, chip-select | Navigate to team page |
| Project Create | 3 | Image, crossfades per step | text, textarea, chip-select, role-picker | Navigate to project page |

This table is the ground truth. The config schema below must be able to express every row.

---

## LAYER 1 — PRIMITIVES

These are extracted verbatim from Auth.jsx first. No logic changes during extraction.

### Shared Constants
**File:** `components/form/formConstants.js`
```js
export const ACCENT_RGB       = '16, 185, 129'
export const EASE             = [0.25, 0.1, 0.25, 1]
export const MORPH_TRANSITION = { type: 'spring', stiffness: 400, damping: 30 }
export const FIELD_VARIANTS = {
  hidden:  { opacity: 0, y: -14 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.26, ease: [0.25, 0.1, 0.25, 1] } },
  exit:    { opacity: 0, y: -10, transition: { duration: 0.18, ease: [0.25, 0.1, 0.25, 1] } },
}
export const FIELD_CONTAINER_VARIANTS = {
  hidden:  { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.055, delayChildren: 0.02 } },
  exit:    { opacity: 0, transition: { staggerChildren: 0.03, staggerDirection: -1 } },
}
```
Every other file imports from here. Constants are never redefined locally.

### Extracted Primitives (verbatim from Auth.jsx)
| File | Component | Notes |
|---|---|---|
| `components/form/Field.jsx` | `Field` | Label + children + animated error |
| `components/form/StyledInput.jsx` | `StyledInput` | Pill morph, icon slot, suffix slot |
| `components/form/PasswordInput.jsx` | `PasswordInput` | Wraps StyledInput, show/hide |
| `components/form/SubmitButton.jsx` | `SubmitButton` | Arrow slide on hover, loading state |
| `components/form/ModeToggleLink.jsx` | `ModeToggleLink` | Accent-coloured mode switch button |
| `components/auth/EmailMetaCard.jsx` | `EmailMetaCard` | College name + user type badge |

### New Primitives (do not exist yet)
| File | Component | Responsibility |
|---|---|---|
| `components/form/StepProgressBar.jsx` | `StepProgressBar` | Horizontal step indicator. Shows step N of total, filled segments, step labels. No click navigation — linear only. |
| `components/form/AnswerRegistry.jsx` | `AnswerRegistry` | Maps answer type strings to their renderer components. The plugin slot. |

---

## LAYER 2 — SHELL

**File:** `components/shell/AuthShell.jsx`

The shell has two left panel modes, selected by config:

### Left Panel Mode A — `image`
Used by: Auth, College Registration, Team Create, Project Create

```
Left panel renders:
- A full-bleed background image (path from config)
- Right-edge gradient bleed (subtle — does not obscure the image)
- Top gradient for wordmark legibility
- Bottom gradient for tagline legibility
- Brand wordmark (top-left)
- Tagline (bottom-left)
- AnimatePresence crossfade when image path changes (step changes)
```

### Left Panel Mode B — `stepInfo`
Used by: Questionnaire (and any future form where image is not meaningful)

```
Left panel renders:
- Solid dark background (--bg-primary)
- Brand wordmark (top-left)
- Current step title (large, Clash Display)
- Current step description (Satoshi, --text-secondary)
- StepProgressBar
- Step counter "Step N of Total" (bottom-left)
```

### Shell Props API
```js
AuthShell({
  leftPanel: {
    mode: 'image' | 'stepInfo',

    // mode: 'image'
    image: string,            // current image path — changes trigger crossfade
    tagline: string?,         // bottom-left caption

    // mode: 'stepInfo'
    stepTitle: string,        // current step title
    stepDescription: string,  // current step description
    currentStep: number,      // 0-indexed
    totalSteps: number,
    stepLabels: string[],     // for StepProgressBar
  },
  brandTo: string?,           // wordmark href, default '/'
  children: ReactNode,        // right panel content
})
```

The shell owns layout only. It has no form knowledge. It renders whatever
the engine passes as `children` into the right floating card.

---

## LAYER 3 — FORM ENGINE

**File:** `components/form/FormEngine.jsx`

The engine reads a config and renders a complete, stateful, animated form.
It is the only component with form knowledge. It has no layout knowledge.

### What FormEngine always renders:
1. Animated title (mask-wipe y ±105%, AnimatePresence mode="wait")
2. Subtitle fade (AnimatePresence mode="wait")
3. Global error banner (AnimatePresence, conditional)
4. Field sequence — rendered from current step's fields, staggered entrance
5. Navigation — Back button (disabled on step 0) + Submit/Next button
6. Footer slot — mode toggle, back link, or nothing

### What FormEngine owns internally:
- `values` — flat object, all field values keyed by field `id`
- `meta` — flat object, keyed by `${fieldId}Meta`, from onBlur side-effects
- `errors` — flat object, field-level error strings
- `globalError` — string
- `currentStep` — number (0-indexed, always 0 for single-step forms)
- `submitting` — boolean
- `mode` — string | null (for mode-toggle forms like Auth)

### FormEngine Props API
```js
FormEngine({
  config,       // FormConfig object
  onSuccess,    // (result) => void
  className,    // string?
})
```

### Navigation model
- Linear only. No step jumping.
- "Next" validates current step fields before advancing.
- "Back" never validates. Clears globalError.
- On the last step, "Next" becomes the submit trigger.
- If config has a `terminal` definition, the engine enters terminal state
  after successful submit instead of calling onSuccess immediately.

### Terminal state
When `config.terminal` exists and submit succeeds:
1. Engine replaces the form with the terminal renderer
2. Terminal renderer receives the submit result
3. Terminal renderer calls its own completion callback (e.g. navigate)

This is how the Questionnaire shows the scoring loader and results reveal
without those components knowing anything about the form engine.

---

## LAYER 4 — CONFIG

**The only thing a page author writes.**
Plain JS object. No JSX. No React imports. No design token knowledge.

### Complete FormConfig Schema

```js
const exampleConfig = {

  // ─── Identity ──────────────────────────────────────────────────────
  id: 'college-registration',

  // ─── Left Panel ────────────────────────────────────────────────────
  // Simple (same throughout):
  leftPanel: {
    mode: 'image',
    image: '/college-reg.jpg',
    tagline: 'Your institution, connected.',
  },

  // OR per-step (image crossfades as steps advance):
  leftPanel: {
    mode: 'image',
    steps: [
      { image: '/team-create-1.jpg', tagline: 'Build your team.' },
      { image: '/team-create-2.jpg', tagline: 'Define your roles.' },
      { image: '/team-create-3.jpg', tagline: 'Launch together.' },
    ],
  },

  // OR step metadata mode (Questionnaire):
  leftPanel: {
    mode: 'stepInfo',
    // stepTitle, stepDescription, stepLabels come from steps[] below
  },

  // ─── Mode Toggle (Auth-style only) ─────────────────────────────────
  // Omit entirely for forms without mode toggle.
  modes: {
    login:  { title: 'Login.',   subtitle: 'Sign in to continue to MeshWork.' },
    signup: { title: 'Sign up.', subtitle: 'Use your institutional email to join.' },
  },
  defaultMode: 'login',

  // ─── Steps ─────────────────────────────────────────────────────────
  // Single-step form: array with one entry.
  // Multi-step form: array with N entries.
  steps: [
    {
      // Used by StepProgressBar and stepInfo left panel:
      id: 'basics',
      title: 'The basics',
      description: 'Tell us about your institution.',

      // Title/subtitle rendered in the right panel form chrome:
      // (If config.modes exists, these are ignored in favour of modes.)
      formTitle: 'Register your college.',
      formSubtitle: 'Add your institution to the MeshWork network.',

      // Fields for this step:
      fields: [
        {
          id: 'college_name',
          type: 'text',
          label: 'College Name',
          placeholder: 'e.g. MIT',
          icon: 'Building2',          // Lucide icon name string
          required: true,
          validation: (value) => {
            if (!value || value.length < 3) return 'Name must be at least 3 characters.'
            return null
          },
        },
        {
          id: 'email',
          type: 'email',
          label: 'Admin Email',
          placeholder: 'admin@college.edu',
          icon: 'Mail',
          required: true,
          onBlur: async (value) => {
            // Return value stored as emailMeta in engine state
            return await validateCollegeEmail(value)
          },
          renderMeta: (meta) => {
            // Return ReactNode or null
            // This is the ONLY place JSX is allowed in config
            // Keep it minimal — just pass meta to an existing component
            if (!meta?.valid) return null
            return <EmailMetaCard meta={meta} />
          },
        },
        {
          id: 'password',
          type: 'password',
          label: 'Password',
          required: true,
        },
        // Row layout: two fields side-by-side
        {
          type: 'row',
          columns: '1fr 1fr',
          fields: [
            { id: 'first_name', type: 'text', label: 'First Name',
              placeholder: 'Jane', required: true },
            { id: 'last_name',  type: 'text', label: 'Last Name',
              placeholder: 'Doe', required: true },
          ],
        },
        // Conditionally shown field:
        {
          id: 'role',
          type: 'text',
          label: 'Your Role',
          placeholder: 'e.g. Professor, Registrar',
          showWhen: (values) => values.user_type === 'personnel',
        },
      ],

      // Step-level submit handler (fires when Next/Submit is clicked
      // and all field validations pass):
      onSubmit: async (stepValues, allValues) => {
        // Return { success: true } to advance, { success: false, error: '...' } to block
        return { success: true }
      },
    },

    // Second step (multi-step example):
    {
      id: 'domains',
      title: 'Email domains',
      description: 'Which email domains belong to your college?',
      formTitle: 'Email domains.',
      formSubtitle: 'Students will be matched by these domains.',
      fields: [
        {
          id: 'domain_list',
          type: 'textarea',
          label: 'Allowed Domains',
          placeholder: 'college.edu, student.college.edu',
          required: true,
        },
      ],
      onSubmit: async (stepValues, allValues) => {
        return { success: true }
      },
    },
  ],

  // ─── Final Submit ───────────────────────────────────────────────────
  // Called after the last step's onSubmit succeeds.
  // This is where the actual API call happens.
  onFinalSubmit: async (allValues) => {
    const result = await registerCollege(allValues)
    // Return { success: true } or { success: false, error: '...' }
    return result
  },

  // ─── Submit Button Labels ───────────────────────────────────────────
  submitLabel: 'Register College',      // last step button label

  // OR mode-aware:
  submitLabels: {
    login:  'Sign In',
    signup: 'Create Account',
  },

  nextLabel: 'Continue',                // non-final step button label (default: 'Continue')
  backLabel: 'Back',                    // default: 'Back'

  // ─── Terminal State (Questionnaire pattern) ─────────────────────────
  // Omit for forms that just navigate away on success.
  terminal: {
    render: (submitResult, onComplete) => {
      // Return a ReactNode.
      // onComplete is called when the terminal state is done
      // (e.g. after results reveal animation finishes).
      // Keep this thin — just render an existing component.
      return (
        <ScoringTerminal
          result={submitResult}
          onComplete={onComplete}
        />
      )
    },
  },

  // ─── Footer ─────────────────────────────────────────────────────────
  // Static:
  footer: {
    text: 'Already registered?',
    linkText: 'Log In',
    linkTo: '/auth',
  },

  // OR mode-aware (Auth pattern):
  footers: {
    login:  { text: "Don't have an account?",   linkText: 'Sign Up',
              linkAction: (setMode) => setMode('signup') },
    signup: { text: 'Already have an account?', linkText: 'Log In',
              linkAction: (setMode) => setMode('login') },
  },

  backLink: { label: '← Back to MeshWork', to: '/' },
}
```

### Answer Types (for Questionnaire config)

The Questionnaire uses field types that other forms don't. These are registered
in `AnswerRegistry.jsx` and resolved by type string — the engine doesn't hardcode them.

```js
// In questionnaireConfig.js step fields:
{
  id: 'q1_enthusiasm',
  type: 'likert',              // renders LikertScale component
  label: 'How excited are you about building software from scratch?',
  scale: 7,                    // 1–7
  required: true,
},
{
  id: 'q2_roles',
  type: 'multi-select',        // renders MultiSelectAnswer component
  label: 'Which of these feel most like you?',
  options: ['Builder', 'Architect', 'Designer', 'Leader', 'Explorer'],
  min: 1,
  max: 3,
  required: true,
},
{
  id: 'q3_description',
  type: 'textarea',
  label: 'Describe your ideal project in a few sentences.',
  maxLength: 500,
  required: true,
},
```

### Answer Registry Pattern

```js
// components/form/AnswerRegistry.jsx
import LikertScale        from '../questionnaire/LikertScale'
import MultiSelectAnswer  from '../questionnaire/MultiSelectAnswer'
import TextareaAnswer     from '../questionnaire/TextareaAnswer'

const ANSWER_REGISTRY = {
  'likert':       LikertScale,
  'multi-select': MultiSelectAnswer,
  'textarea':     TextareaAnswer,
  // Standard types handled by FormEngine directly:
  // 'text', 'email', 'password', 'row', 'custom'
}

export function resolveAnswerType(type) {
  return ANSWER_REGISTRY[type] ?? null
}
```

Adding a new answer type = add one import + one line to the registry.
The engine and all configs are untouched.

---

## LAYER 5 — PAGE

**What a page author writes for a new form page:**

```jsx
// pages/CollegeRegistration.jsx
import AuthShell   from '../components/shell/AuthShell'
import FormEngine  from '../components/form/FormEngine'
import { collegeRegConfig } from '../config/forms/collegeRegConfig'
import { useNavigate } from 'react-router-dom'

export default function CollegeRegistration() {
  const navigate = useNavigate()
  return (
    <AuthShell config={collegeRegConfig}>
      <FormEngine
        config={collegeRegConfig}
        onSuccess={() => navigate('/admin/dashboard')}
      />
    </AuthShell>
  )
}
```

**Note:** AuthShell receives `config` directly so it can read `leftPanel` and step
metadata without prop-drilling through FormEngine. FormEngine is not responsible
for communicating step state to the shell — they are siblings, not parent-child.

This raises a coordination problem: when the user advances a step, both the engine
(right panel) and the shell (left panel) need to know the current step index.

**Solution: a thin context, scoped to the page:**

```jsx
// The page creates a FormStepContext. Both shell and engine consume it.
// FormEngine is the only writer. AuthShell is a reader.

// pages/CollegeRegistration.jsx
import { FormStepProvider } from '../context/FormStepContext'

export default function CollegeRegistration() {
  const navigate = useNavigate()
  return (
    <FormStepProvider config={collegeRegConfig}>
      <AuthShell config={collegeRegConfig} />
      <FormEngine
        config={collegeRegConfig}
        onSuccess={() => navigate('/admin/dashboard')}
      />
    </FormStepProvider>
  )
}
```

`FormStepContext` is minimal — it holds only `{ currentStep, totalSteps, mode }`.
FormEngine writes to it. AuthShell reads from it to know which image/metadata to show.

---

## FILE STRUCTURE

```
src/
├── config/
│   └── forms/
│       ├── authConfig.js
│       ├── collegeRegConfig.js
│       ├── questionnaireConfig.js
│       ├── profileEditConfig.js
│       ├── teamCreateConfig.js
│       └── projectCreateConfig.js
│
├── context/
│   └── FormStepContext.jsx          ← currentStep, totalSteps, mode
│
├── components/
│   ├── form/
│   │   ├── formConstants.js         ← ACCENT_RGB, EASE, MORPH_TRANSITION, variants
│   │   ├── Field.jsx                ← extracted from Auth.jsx
│   │   ├── StyledInput.jsx          ← extracted from Auth.jsx
│   │   ├── PasswordInput.jsx        ← extracted from Auth.jsx
│   │   ├── SubmitButton.jsx         ← extracted from Auth.jsx
│   │   ├── ModeToggleLink.jsx       ← extracted from Auth.jsx
│   │   ├── StepProgressBar.jsx      ← new
│   │   ├── AnswerRegistry.jsx       ← new (plugin slot)
│   │   └── FormEngine.jsx           ← new (the engine)
│   │
│   ├── shell/
│   │   └── AuthShell.jsx            ← new (replaces inlined layout in Auth.jsx)
│   │
│   ├── auth/
│   │   └── EmailMetaCard.jsx        ← extracted from Auth.jsx
│   │
│   └── questionnaire/
│       ├── LikertScale.jsx          ← new answer type
│       ├── MultiSelectAnswer.jsx    ← new answer type
│       ├── TextareaAnswer.jsx       ← new answer type
│       ├── ScoringLoader.jsx        ← new terminal state component
│       └── ScoringSummaryCard.jsx   ← new terminal state component
│
└── pages/
    ├── Auth.jsx                     ← refactored to ~15 lines
    ├── CollegeRegistration.jsx      ← ~15 lines
    ├── Questionnaire.jsx            ← ~15 lines
    ├── ProfileEdit.jsx              ← ~15 lines
    ├── TeamCreate.jsx               ← ~15 lines
    └── ProjectCreate.jsx            ← ~15 lines
```

---

## BUILD ORDER

**Phase 0 — Extract (no new logic)**
Extract verbatim from Auth.jsx. Confirm each renders identically before proceeding.
1. `formConstants.js`
2. `Field.jsx`
3. `StyledInput.jsx`
4. `PasswordInput.jsx`
5. `SubmitButton.jsx`
6. `ModeToggleLink.jsx`
7. `EmailMetaCard.jsx`

**Phase 1 — New Primitives**
8. `StepProgressBar.jsx`
9. `AnswerRegistry.jsx` (empty registry — populated in Phase 3)

**Phase 2 — Infrastructure**
10. `FormStepContext.jsx`
11. `AuthShell.jsx`

**Phase 3 — Engine**
12. `FormEngine.jsx`

**Phase 4 — Migrate Auth (proof of concept)**
13. `authConfig.js` — extract Auth's logic into config
14. `Auth.jsx` refactor — 15 lines, composition only

**Phase 5 — First new page (proves the system)**
15. `collegeRegConfig.js`
16. `CollegeRegistration.jsx`

**Phase 6 — Questionnaire (proves multi-step + terminal + answer types)**
17. `LikertScale.jsx`
18. `MultiSelectAnswer.jsx`
19. `TextareaAnswer.jsx`
20. `ScoringLoader.jsx`
21. `ScoringSummaryCard.jsx`
22. `questionnaireConfig.js`
23. `Questionnaire.jsx`

**Phase 7 — Remaining pages**
24–29. `profileEditConfig.js`, `teamCreateConfig.js`, `projectCreateConfig.js`
        + their page files

---
---

# AI GENERATION PROMPT
## Paste this as the ENTIRE first message of a new session.
## Do not add anything before or after it.

---

```
You are a senior React engineer. You are building the MeshWork form composition
system. Read the entire brief before responding. Do not generate any code until
I give the explicit build command.

══════════════════════════════════════════════════════
WHAT THIS SYSTEM DOES
══════════════════════════════════════════════════════

MeshWork has 6 form-heavy pages:
  Auth, College Registration, Questionnaire,
  Profile Edit, Team Create, Project Create

Without this system, building each page requires re-explaining the visual
design, animations, multi-step logic, and validation every time.

With this system, a new page author writes:
  1. A config file (plain JS object, no JSX, no design knowledge)
  2. A ~15-line page file (compose shell + engine + config)

Everything else — layout, animations, field rendering, step transitions,
validation, error states, pill-morph inputs, arrow-slide button — is inherited.

══════════════════════════════════════════════════════
ARCHITECTURE (strict, non-negotiable)
══════════════════════════════════════════════════════

Five layers. Dependency flows strictly downward. No layer imports from above.

  LAYER 5 — PAGE
    ~15 lines. Composes FormStepProvider + AuthShell + FormEngine.
    Imports config. Provides onSuccess handler. Nothing else.

  LAYER 4 — CONFIG (plain JS, no React imports except in renderMeta)
    Defines: leftPanel mode, steps, fields, validation, submit handlers,
    footer, terminal state. This is ALL a page author writes.

  LAYER 3 — FORM ENGINE  (FormEngine.jsx)
    Reads config. Renders fields. Manages all state: values, errors,
    currentStep, mode, submitting. Runs validation. Calls submit handlers.
    Writes currentStep to FormStepContext. No layout knowledge.

  LAYER 2 — SHELL  (AuthShell.jsx)
    The 50/50 split layout. Left panel in two modes:
      'image'    — full-bleed photo, crossfades when image prop changes
      'stepInfo' — dark panel with step title, description, StepProgressBar
    Right panel — floating card, renders children.
    Reads currentStep from FormStepContext. No form knowledge.

  LAYER 1 — PRIMITIVES
    Field, StyledInput, PasswordInput, SubmitButton, ModeToggleLink,
    EmailMetaCard, StepProgressBar, AnswerRegistry, FormStepContext

══════════════════════════════════════════════════════
TECH STACK — FIXED
══════════════════════════════════════════════════════

- React 18, functional components and hooks only
- Framer Motion for all animations — no CSS keyframes for motion
- React Router v6
- Lucide React for icons — resolved via ICON_MAP inside FormEngine,
  never imported directly in config files
- No UI component libraries (no MUI, Shadcn, Radix, etc.)
- Inline styles only in JSX — no Tailwind utility classes
- CSS custom properties for all colour and spacing tokens

══════════════════════════════════════════════════════
DESIGN TOKENS — THE ONLY VALUES ALLOWED IN COMPONENTS
══════════════════════════════════════════════════════

--bg-primary:           #0E1113
--bg-surface:           #14181B
--bg-surface-elevated:  #1B2024
--text-primary:         #E6EDF3
--text-secondary:       #9AA4AE
--border-subtle:        rgba(255,255,255,0.06)
--accent-primary:       #10B981
--accent-hover:         #0EA371
--accent-soft:          rgba(16,185,129,0.12)
--color-error:          #EF4444
--color-warning:        #EAB308
--focus-ring:           #10B981

In JS: ACCENT_RGB = '16, 185, 129' (for rgba() usage)
Never use raw hex values in component JSX. Always use var(--token) or ACCENT_RGB.

══════════════════════════════════════════════════════
SHARED CONSTANTS — formConstants.js
══════════════════════════════════════════════════════

Every form component imports from this file. Never redefine locally.

export const ACCENT_RGB       = '16, 185, 129'
export const EASE             = [0.25, 0.1, 0.25, 1]
export const MORPH_TRANSITION = { type: 'spring', stiffness: 400, damping: 30 }
export const FIELD_VARIANTS = {
  hidden:  { opacity: 0, y: -14 },
  visible: { opacity: 1, y: 0,  transition: { duration: 0.26, ease: [0.25,0.1,0.25,1] } },
  exit:    { opacity: 0, y: -10, transition: { duration: 0.18, ease: [0.25,0.1,0.25,1] } },
}
export const FIELD_CONTAINER_VARIANTS = {
  hidden:  { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.055, delayChildren: 0.02 } },
  exit:    { opacity: 0, transition: { staggerChildren: 0.03, staggerDirection: -1 } },
}

══════════════════════════════════════════════════════
TYPOGRAPHY
══════════════════════════════════════════════════════

Headings (h1, form titles): 'Clash Display', sans-serif — weight 600–700
Body, labels, inputs, UI text: 'Satoshi', sans-serif — weight 400–600

══════════════════════════════════════════════════════
ANIMATION PATTERNS — USE EXACTLY AS SPECIFIED
══════════════════════════════════════════════════════

Title entrance (right panel):
  Parent: overflow:hidden
  motion.h1: initial={{ y:'105%' }} animate={{ y:'0%' }} exit={{ y:'-105%' }}
  AnimatePresence mode="wait" — key changes on mode or step

Field stagger:
  Container: motion.div with FIELD_CONTAINER_VARIANTS
  Each field: motion.div with FIELD_VARIANTS
  AnimatePresence wraps the container when fields change between steps

Input pill morph:
  Default border-radius: 8px
  On focus OR when value is non-empty: border-radius: 999px
  Transition: 'border-radius 300ms cubic-bezier(0.16,1,0.3,1)'

Submit button arrow slide:
  Button: overflow:hidden, position:relative, border-radius:999px
  Label text: motion.span, on hover x shifts to -6
  ChevronRight: motion.span, starts at x:24 opacity:0,
    on hover animates to x:6 opacity:1
  Both animate at duration:0.22, ease:EASE

Left panel image crossfade:
  AnimatePresence initial={false}
  motion.img key={image}: initial opacity:0 scale:1.04,
    animate opacity:1 scale:1, exit opacity:0 scale:0.97
  transition duration:0.85, ease:EASE

══════════════════════════════════════════════════════
FORMCONFIG SCHEMA (what config files must conform to)
══════════════════════════════════════════════════════

{
  id: string,

  leftPanel: {
    mode: 'image' | 'stepInfo',
    // if mode === 'image':
    image: string,                   // static image, OR omit and use steps[]
    tagline: string?,
    steps: Array<{ image, tagline }>, // per-step images (overrides static image)
    // if mode === 'stepInfo': title/description come from steps[].title/description
  },

  modes: {                           // OPTIONAL — Auth-style toggle only
    [modeName]: { title, subtitle },
  },
  defaultMode: string,               // required if modes present

  steps: Array<{
    id: string,
    title: string,                   // used in stepInfo left panel + StepProgressBar
    description: string,             // used in stepInfo left panel
    formTitle: string,               // right panel h1 (ignored if config.modes present)
    formSubtitle: string,            // right panel subtitle
    fields: Field[],
    onSubmit: async (stepValues, allValues) => { success, error? },
  }>,

  onFinalSubmit: async (allValues) => { success, error? },

  submitLabel: string,               // last step button, OR
  submitLabels: { [mode]: string },  // mode-aware version

  nextLabel: string?,                // default: 'Continue'
  backLabel: string?,                // default: 'Back'

  terminal: {                        // OPTIONAL — Questionnaire pattern
    render: (result, onComplete) => ReactNode,
  },

  footer: { text, linkText, linkTo?, linkAction? },   // static OR
  footers: { [mode]: { text, linkText, linkAction } }, // mode-aware

  backLink: { label, to },           // optional
}

Field shape:
{
  id: string,
  type: 'text'|'email'|'password'|'textarea'|'select'|'row'|'custom'
        |'likert'|'multi-select'|'single-select',
  label: string,
  placeholder: string?,
  icon: string?,                     // Lucide name, resolved by FormEngine ICON_MAP
  required: boolean?,
  validation: (value, allValues) => string | null,
  showWhen: (allValues) => boolean,
  onBlur: async (value, allValues) => any,   // result stored as {id}Meta
  renderMeta: (meta) => ReactNode | null,
  // type:'row' only:
  columns: string,
  fields: Field[],
  // type:'custom' only:
  render: (value, onChange, error, allValues) => ReactNode,
  // type:'likert' only:
  scale: number,
  // type:'multi-select' only:
  options: string[],
  min: number?,
  max: number?,
}

══════════════════════════════════════════════════════
COMPONENT RULES — ALL COMPONENTS MUST FOLLOW THESE
══════════════════════════════════════════════════════

1. Named function exports only. No arrow function default exports.
2. Props destructured in function signature.
3. No raw hex in JSX. Semantic tokens (var(--...)) or ACCENT_RGB only.
4. Error states: role="alert", visually distinct border + background.
5. Icon-only interactive elements: aria-label required.
6. AnimatePresence wraps every conditionally rendered motion element.
7. Import from formConstants.js — never redefine EASE, ACCENT_RGB, etc.
8. FormEngine resolves icon strings via ICON_MAP — configs never import Lucide.
9. Sub-component extraction: if a JSX block exceeds ~40 lines, extract a
   named function in the same file.
10. FormEngine is the ONLY component that writes to FormStepContext.
    AuthShell is a reader only.

══════════════════════════════════════════════════════
BUILD ORDER — STRICTLY SEQUENTIAL
══════════════════════════════════════════════════════

Never reference a component that has not been built yet.
Build in this exact order:

PHASE 0 — EXTRACT (verbatim from Auth.jsx, no logic changes)
  1.  formConstants.js
  2.  Field.jsx
  3.  StyledInput.jsx
  4.  PasswordInput.jsx
  5.  SubmitButton.jsx
  6.  ModeToggleLink.jsx
  7.  EmailMetaCard.jsx

PHASE 1 — NEW PRIMITIVES
  8.  StepProgressBar.jsx
  9.  AnswerRegistry.jsx          (empty registry to start)
  10. FormStepContext.jsx

PHASE 2 — SHELL
  11. AuthShell.jsx

PHASE 3 — ENGINE
  12. FormEngine.jsx

PHASE 4 — MIGRATE AUTH (proves engine works)
  13. authConfig.js
  14. Auth.jsx refactor

PHASE 5 — FIRST NEW PAGE (proves plug-and-play)
  15. collegeRegConfig.js
  16. CollegeRegistration.jsx

PHASE 6 — QUESTIONNAIRE (proves multi-step + terminal + answer types)
  17. LikertScale.jsx
  18. MultiSelectAnswer.jsx
  19. TextareaAnswer.jsx
  20. ScoringLoader.jsx
  21. ScoringSummaryCard.jsx
  22. questionnaireConfig.js
  23. Questionnaire.jsx

PHASE 7 — REMAINING PAGES
  24. profileEditConfig.js + ProfileEdit.jsx
  25. teamCreateConfig.js + TeamCreate.jsx
  26. projectCreateConfig.js + ProjectCreate.jsx

══════════════════════════════════════════════════════
INTERACTION PROTOCOL
══════════════════════════════════════════════════════

We build one step at a time, in the order above.

For each step:
  I say: "Build step N" or name the component.
  You ask: Only questions whose answers change the component's API or
           internal behaviour. Maximum 2 questions. Skip anything you
           can resolve from this brief.
  I answer (or say "use best judgement").
  You produce: The complete file, production-quality.
  You output after each file:
    EXPORTS:        [everything this file exports]
    IMPORTS NEEDED: [what must exist before anything imports this]
    NEXT:           [step N+1 name]

If a step is a pure composition of already-built components with no novel
logic, skip the questions and build directly.

Do not skip steps. Do not combine steps unless I explicitly say to.
Do not generate anything until I give the build command.

══════════════════════════════════════════════════════
CONFIRM AND WAIT
══════════════════════════════════════════════════════

Respond with:
1. One sentence confirming you have read and understood the architecture.
2. One sentence confirming the build order.
3. "Waiting for build command."

Do not generate any code yet.
```
