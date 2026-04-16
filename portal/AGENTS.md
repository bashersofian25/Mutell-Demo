<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

<!-- BEGIN:ui-reference-template -->
# UI Reference Template

The TailAdmin free Next.js admin dashboard template at `/home/bash/Repos/free-nextjs-admin-dashboard-main` is the canonical reference for all UI/UX decisions. When building new pages, components, or layouts, always check the template first for:

- Component structure, props, and patterns
- Tailwind CSS class conventions and styling approach
- Layout composition (sidebar, header, page structure)
- Form element patterns (inputs, selects, switches, date pickers)
- Table and data display patterns
- Chart integration patterns (ApexCharts)
- Dark mode implementation (class-based, `dark:` variants)
- Responsive breakpoint usage
- Animation and transition patterns

Keep all UI work consistent with this template's conventions.
<!-- END:ui-reference-template -->

<!-- BEGIN:project-info -->
# Mutell Portal

- **Product**: Mutell (AI-Powered POS Monitoring & Evaluation Platform)
- **Logo**: `/mutell-logo.svg` (use `dark:invert` for theme switching)
- **Toast library**: `react-hot-toast` (NOT sonner)
- **Chart library**: ApexCharts via `dynamic(() => import("react-apexcharts"), { ssr: false })`
- **Date picker**: flatpickr via `@/components/form/date-picker`
- **API Manual**: `/home/bash/Repos/pos-monitoring-draft/API_MANUAL.md`
- **API Suggestions**: `/home/bash/Repos/pos-monitoring-draft/API_SUGGESTIONS.md`
- **Auth store**: `@/stores/auth-store.tsx` (uses `authService` from services)
<!-- END:project-info -->
