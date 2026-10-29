# SKILLS.md — Frontend Common Project Standards

### Component Architecture (The Three-Tier System)
- **Tier 1 (Base UI — `components/ui/`):** All base Shadcn components must live untouched in `src/components/ui/`. Install them via the CLI (`npx shadcn@latest add`). Never hand-edit these files.
- **Tier 2 (Controls — `components/controls/`):** All custom reusable components requested in `SETUP.md` must be built inside `src/components/controls/`. These components MUST import the base UI components from `@/components/ui/` and wrap them with the required business logic (e.g., React Hook Form `Controller` integrations, Zod error message displays, custom variant props). All Tier 2 components MUST use `React.forwardRef` and define a `displayName`.
- **Tier 3 (Common — `components/common/`):** Larger composed pieces used across multiple pages (Navbar, Sidebar, OrderCard, SchoolCard, ConfirmationModal, PageHeader, EmptyState). Built from Tier 1 and Tier 2 components.


### Logging & Debugging

- Remove console.log statements before merging to production.

- Use structured error logging for caught API exceptions.

- Do not log sensitive user data (passwords, PII, tokens) in the browser console.


### Styling Rules (Tailwind Only)

- No custom .scss files unless absolutely necessary for complex animations.

- No inline styles (style={{ color: 'red' }}).

- Use standard Tailwind utility classes.

- Use responsive prefixes consistently: mobile-first (`sm:`, `md:`, `lg:`).

```javascript
<div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3" />
```

### Install Core Frontend Dependencies
```bash
npm install axios @tanstack/react-query react-hook-form @hookform/resolvers zod react-router-dom lucide-react
```

### State Management Rules

| State Type          | Tool                  | Purpose                                                                            |
|---------------------|-----------------------|------------------------------------------------------------------------------------|
| Server State        | TanStack Query        | API data fetching, caching, loading states, and mutations.                         |
| Global Client State | Context API           | App-wide state: auth session, cart items, user role, sidebar toggle.               |
| Local UI State      | useState              | Component-specific state (e.g., opening a dropdown, modal visibility, tab index).  |


### React Component Standards

- All Tier 2 wrapper components (Buttons, Inputs, Dropdowns) MUST be wrapped in `React.forwardRef` to support Radix UI triggers and React Hook Form refs.
- Always append `ComponentName.displayName = "ComponentName"` at the bottom of every Tier 2 file.
- Use `<Controller>` from `react-hook-form` for all custom form components — never use `register` directly on a Tier 2 control.


## Don't

- Do not mutate React state directly (e.g., state.value = "new").

- Do not forget to handle loading (`isLoading`) and error (`isError`) states in UI components.

- Do not build complex UI components from scratch if a Shadcn/UI component already exists.

- Do not store sensitive keys or secrets in the frontend repository.

- Do not install or use `@reduxjs/toolkit` or `react-redux` — this project uses Context API.

- Do not make API calls directly from components — always go through a custom hook in `src/hooks/`.

- Do not write TypeScript (`.ts` / `.tsx`) — this project uses plain JavaScript.

---

**Note:** This file only contains common standards followed across the entire project.
