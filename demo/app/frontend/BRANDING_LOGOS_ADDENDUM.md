# Branding plan addendum: logo usage

You have provided logos to use. This addendum updates the on-brand plan to **include logo placement** in the app.

## Where logo files are (React app)

**Note:** The app uses the real Databricks and AGL logos. Place the official assets in `public/logos/` with the filenames below.

For Vite to serve them at build and runtime, either:

- **Option A:** Place (or symlink) them under `demo/app/frontend/public/logos/`
  - Files here are served from the site root, e.g. `public/logos/databricks.svg` → `/logos/databricks.svg`
- **Option B:** Logos are already elsewhere in the repo — implementation will use the paths you provide (e.g. import from `src` or copy into `public` at build time).

**Suggested filenames** (adjust to match the files you have):

| Brand      | Filename        | Use in UI        |
|-----------|----------------------------|------------------|
| Databricks| `databricks-full.svg` | Sidebar “Powered by”, hero, footer |
| AGL       | `AGL_Energy_logo.svg`       | Sidebar title area, hero, footer   |

SVG is preferred (sharp at any size, smaller files). Add the official Databricks logo from [Databricks brand](https://databricks.com/company/brand) and the AGL Energy logo to `demo/app/frontend/public/logos/` with the filenames above.

## Logo placement in the UI

### 1. Sidebar ([`src/components/Sidebar.tsx`](src/components/Sidebar.tsx))

- **Top block:** AGL logo (small, e.g. 32–40px height) + “AGL OT Lakehouse” text in AGL blue.
- **Below title:** “Powered by” + Databricks logo (small, e.g. 24–32px height) in Databricks primary styling, or “Powered by Databricks” text in Databricks primary if logo is icon-only.
- Keep nav and “Asset Framework” as in the plan; active state in Databricks primary.

### 2. Landing hero ([`src/pages/Landing.tsx`](src/pages/Landing.tsx))

- **Option A:** Side-by-side logos above or beside the headline (“From SCADA to Lakehouse”) — AGL left, Databricks right, both modest size.
- **Option B:** Single “Powered by Databricks” with Databricks logo under the hero copy; AGL accent in the “AGL” / fleet copy only.
- Primary CTA and key phrase remain Databricks primary (no logo required on the button).

### 3. Footer (Landing and/or global)

- One line: AGL logo (small) + “AGL OT Lakehouse” + “·” + “Powered by” + Databricks logo (small), or the same in text with optional small logos.
- Keeps both brands visible without crowding.

### 4. Elsewhere

- **Comparison table:** Keep “Databricks + Zerobus” in Databricks primary (text only); no need for logo in the table.
- **Architecture / Data Generation:** Optional small Databricks logo next to “Databricks” in a diagram label; AGL logo only if you add an explicit “AGL” callout.

## Implementation notes

- Use `<img src="/logos/databricks.svg" alt="Databricks" />` (or your filenames) so paths work in dev and production.
- Add `height` (and optional `width`) so layout is stable; use `className` for size (e.g. `h-8 w-auto`) and optional `object-contain`.
- Ensure contrast: if logos are light, use them on dark (Databricks teal/sidebar) or add a subtle background; if dark, ensure background is light enough (e.g. cream) or use a light variant of the logo if you have one.

## Summary

- **Colors/typography:** Unchanged from main plan (Databricks primary/teal, AGL blue, semantic green/amber/red).
- **New:** Use your Databricks and AGL logos in Sidebar, Landing hero (and/or footer), and a small footer line so the app is on-brand for both with the logos you provided.
- **Asset location:** Prefer `public/logos/` with the filenames above; if you’ve placed them somewhere else, tell us the paths and we’ll wire them up accordingly.
