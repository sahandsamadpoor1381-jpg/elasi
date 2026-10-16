# ELASI — Design tokens, contrast and accessibility audit

Audited with the **Redesign Skill** (`plugin87/ux-ui-agent-skills`,
`.claude/skills/redesign` + `workflows/redesign-audit.md`,
`taste/design-taste.md`, `frameworks/nextjs.md`) following
Scan → Diagnose → Direct → Apply → Verify. The kit was fetched from its
official repository for this audit; it is **not** vendored into this
repo. Re-run the checks with:

```bash
python3 scripts/validate_contrast.py        # token contrast (kit)
python3 scripts/lint_hardcodes.py src       # theme/token drift (kit)
```

## Scan

| Item | Finding |
| --- | --- |
| Framework / styling | Next.js 16 App Router + Tailwind v4, token layer in `frontend/src/app/globals.css` (`:root` custom properties + `@theme inline`) |
| Token reality | A real token layer exists (brand, surfaces, feedback, type scale, spacing, radius, motion, layering) but only six colors were mapped into Tailwind |
| Must preserve | Persian RTL, Peyda, deep green `#152A24`, gold `#B8945A`, ivory `#F8F4EC`, all existing flows and routes |

## Diagnose (measured, not guessed)

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| 1 | Gold used as **text** failed WCAG AA | `#B8945A` on ivory = **2.58:1** (needs 4.5) — used for ~95 labels, eyebrows, links | Critical |
| 2 | **Control borders** were decorative-light | `rgba(21,42,36,0.2)` on ivory = **1.48:1** (WCAG 1.4.11 needs 3:1) | Critical |
| 3 | Focus ring used the brand gold | same 2.58:1 → a focus indicator that is hard to see | Critical |
| 4 | Semantic utilities **emitted no CSS at all** | `text-elasi-danger`, `bg-elasi-danger`, `border-elasi-danger`, `…surface-soft` returned **0 rules** in the built CSS because those tokens were missing from `@theme inline`. Error states rendered unstyled. | Critical |
| 5 | Raw Tailwind palette drift | 21 violations (`text-red-700`, `bg-red-50/30`, `border-red-900/10`, `text-red-900`…) across auth/cart/checkout | Major |
| 6 | One raw hex in JSX | `color: "#FFFFFF"` inline style in checkout | Minor |
| 7 | Focus-visible & reduced-motion | Already present and correct — preserved, not replaced | — |
| 8 | Spacing/radius literals | 206 px literals, mostly arbitrary Tailwind values in pre-existing screens | Minor (tracked below) |

## Apply (surgical, tokens first)

1. **New token `--elasi-gold-text: #7e6029`** — the gold for *text*:
   5.33:1 on ivory, 5.85:1 on white, 5.10:1 on the soft surface.
   `--elasi-gold` (#B8945A) remains the decorative accent (rules,
   borders, fills) and the gold on the deep green surface, where it
   already measures 5.34:1. 95 `text-elasi-gold` usages moved to
   `text-elasi-gold-text`; no decorative usage changed.
2. **`--elasi-border-strong` strengthened** to `rgba(21,42,36,0.55)`
   (~3.48:1 on ivory) and applied to control boundaries (inputs, chips,
   secondary buttons, pagination): 21 borders. Decorative hairlines
   (`/10`, `/8`) keep their soft look.
3. **Focus ring** now uses the compliant gold (5.33:1) via
   `--focus-ring-width` / `--focus-ring-offset`.
4. **`@theme inline` completed** — every semantic token is mapped
   (gold-text, surface, surface-soft, border, border-strong, success,
   warning, danger) plus `--radius-card`. Verified in the built CSS:
   each previously-missing utility now emits a rule.
5. **Palette drift removed** — all 21 raw red-palette utilities map to
   `elasi-danger`, and the inline hex uses `var(--elasi-white)`.
6. **Tokenized foundations & motion** — `--elasi-min-width`,
   `--elasi-base-font-size(-compact)`, `--control-height`, `--space-7`,
   `--transition-slow`, `--transition-deliberate`; drawer motion and the
   button control size now read from tokens.
7. **Product grid owned by the token layer** — `--grid-product-min` /
   `--card-max-width` + `.elasi-product-grid` / `.elasi-product-card`,
   shared by the listing and its loading skeleton so the skeleton always
   matches the loaded layout.
8. Canonical recipes that must stay literal (`sr-only` clip,
   `prefers-reduced-motion` overrides) carry `ds-allow-hardcode`
   annotations with the reason.

## Verify

```
validate_contrast.py   before: 2 required pairs FAILED (2.58:1, 1.48:1)  →  after: all required pairs pass
lint_hardcodes.py      before: 239 violations (21 palette, 1 hex, 206 px, 11 time)
                       after:  166 violations, ZERO colour/palette violations;
                               all 23 authored/touched files: clean
```

Remaining 166 are layout `px`/`ms` literals inside pre-existing screens
(`app/login/page.tsx` 59, `auth/account-client.tsx` 51,
`checkout/checkout-client.tsx` 18, `app/page.tsx` 11, gallery/cart/
purchase panel ≈ 20). They are single-value layout constants, not colour
drift, so the visual system is consistent today; converting them to
spacing tokens is a mechanical follow-up and was deliberately kept out
of this phase to avoid rewriting working screens.

## Usage rules (keep this true)

- Text on light surfaces: `text-elasi-text`, `text-elasi-muted`,
  `text-elasi-gold-text`, `text-elasi-green`, `text-elasi-danger`.
- `elasi-gold` (bright): decorative rules, borders, fills, and text on
  `elasi-green` only.
- Interactive boundaries (anything a customer can operate): use
  `border-elasi-border-strong`; `border-elasi-border` is decorative.
- Never introduce a raw Tailwind palette colour or hex literal; add or
  map a semantic token instead.
