# AI AGENT BOUNDARIES & GUIDELINES

This document defines the strict boundaries, conventions, and rules the AI coding agent must follow when generating, refactoring, or reviewing code in this repository.

**Note:** This is a Frontend-only project. Do NOT generate Node.js backend logic, Express routes, or database queries. All data is fetched via Axios from a separate backend API.

---

## Code Persona

You are a Senior Frontend Engineer specializing in React.js for building responsive web applications.
- Clean, readable, modular
- No unnecessary comments
- No `console.log` in production
- Avoid deeply nested code
- Reusable logic → move to `helpers/` or `hooks/`

You must always write code that is written in **JavaScript (ES6+)** — do NOT use TypeScript.

## 1. NAMING CONVENTIONS

| Element              | Format                     | Example                              |
|----------------------|----------------------------|--------------------------------------|
| Files & Directories  | kebab-case                 | `school-list.jsx`, `use-orders.js`   |
| UI Components        | PascalCase                 | `SchoolCard`, `UniformVariantPicker` |
| Variables & Hooks    | camelCase                  | `useSchools`, `isAdminLoggedIn`      |
| Global Constants     | UPPER_SNAKE_CASE           | `API_BASE_URL`, `ORDER_STATUS`       |
| Context Files        | PascalCase + Context       | `CartContext`, `AuthContext`         |
| Data Schemas (Zod)   | camelCase + Schema         | `orderSchema`, `loginSchema`         |

---

## Folder Usage Rules

| Folder                 | Purpose                                                                                                                                              |
|------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| `assets/`              | Static assets (images, icons, animations).                                                                                                           |
| `components/pages/`    | Actual full-screen React components representing views/routes. Split into `admin/` and `public/` subfolders.                                         |
| `components/ui/`       | Base, auto-generated Shadcn UI components. **Do not write code here manually.** Only use the `npx shadcn@latest add` CLI.                            |
| `components/controls/` | Smart, customized wrapper components built on top of `components/ui/`. This is where all specific variants, Zod validation, and error states live.   |
| `components/common/`   | Larger reusable UI pieces shared across the app (Navbar, Sidebar, Modal wrappers, StatusBadge, etc.).                                                |
| `constants/`           | Application-wide constants — ORDER_STATUS values, API endpoint keys, uniform categories, size options.                                               |
| `context/`             | React Context files — one per domain. Each file exports its Provider component and a custom `use*` hook.                                             |
| `hooks/`               | Custom React hooks. All TanStack Query fetch/mutation hooks live here — one file per domain (schools, uniforms, orders).                             |
| `helpers/`             | Reusable helper functions for business logic (order total calculation, status label mapping, tracking URL builder).                                   |
| `utils/`               | Generic utility functions (e.g., date formatting, truncate text, debounce).                                                                          |
| `routes/`              | React Router v6 configurations and route guards (Protected Routes).                                                                                  |
| `services/`            | Axios instance with interceptors, API constants, and endpoint URL map. No business logic here — only HTTP configuration.                             |

---

## 2. STANDARD VALIDATIONS
1. Frontend Forms: Always use Zod schemas with React Hook Form. Do not rely solely on basic HTML5 validation.
2. API Responses: Always handle loading states and potential API failures gracefully. Never assume an Axios request will return a 200 OK.
3. Null Checks: Always use optional chaining (`?.`) and nullish coalescing (`??`) to prevent runtime crashes.
4. Error Handling: Wrap async operations in `try/catch` blocks. Never swallow errors silently.
5. Cart Validation: Before placing an order, validate that the cart is non-empty and all quantities are ≥ 1.

---

## 3. CONTEXT API RULES
1. All cart mutations (add, remove, update qty, clear) must go through `CartContext` — never mutate cart state directly in a component.
2. Auth state (token, role) must only be written by `AuthContext` — never stored in arbitrary component state.
3. Do NOT make API calls inside Context providers — use TanStack Query mutations for all server interactions.
4. Consume context only through the exported custom hook (e.g., `useCart()`, `useAuth()`) — never call `useContext` directly in components.
5. Do NOT install or use `@reduxjs/toolkit` or `react-redux` — Context API is the approved pattern for global client state.
6. Keep state local (`useState`) when it is not shared across disjointed components. Only elevate to Context when genuinely needed app-wide.

---

## 4. THEMES, COLORS & UI
1. Styling System: Strictly use Tailwind CSS utility classes. Do not write custom CSS in separate `.scss` files unless absolutely necessary.
2. Color Palette: Only use colors defined in the `tailwind.config.js` theme. No hardcoded hex codes in JSX.
3. Spacing: Adhere to the established Tailwind spacing scale (e.g., `p-4`, `m-2`, `gap-4`).
4. Component Reuse: Utilize the existing shared components from `components/controls/` rather than building new ones from scratch.

---

## 5. STANDARD COMMANDS
The agent should execute these primary commands for running the application:
1. Run Local: `npm run dev`
2. Format Code: Use Prettier. Use `npm run lint` or `npm run format` for manual checks.
3. Build Prod: `npm run build`

---

## 6. GENERAL GUIDELINES & BOUNDARIES
1. Read-Only Scope: Do NOT modify `package.json`, `.env`, or `tailwind.config.js` without explicit human confirmation.
2. No TypeScript: This project uses plain JavaScript (.js / .jsx). Do not introduce `.ts` or `.tsx` files.
3. No Payment Logic: Payment gateway integration is out of scope. Do not add payment-related components, APIs, or flows.
4. Smart Comments: Do not over-comment obvious code. Only explain complex business logic, regex, or specific workarounds.
5. No Direct DOM Manipulation: Do not use `document.querySelector` or manually manipulate DOM elements when React state can handle it.
