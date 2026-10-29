# School Accessories Mart – Frontend Setup

This project is a scalable frontend system for digitizing the school uniform ordering process — enabling parents to browse, select, and order uniforms online, while giving the owner a dashboard to manage schools, uniforms, orders, and deliveries.

---

## Agent Reading Order

Before writing any code, read the following files **in order**. All rules in every file apply to every task.

1. **ARCHITECTURE.md** — Project folder structure, Frontend Tech Stack, Component Architecture, State Management strategy (Context API & TanStack Query), Routing logic, and API Consumption rules.
2. **API_SETUP.md** — Complete API endpoint reference (derived from Postman collection), Axios instance setup, `apiConstants.js`, `apiUrls.js`, TanStack Query hook patterns per domain, Zod schemas for every API payload, and constants for enums (ORDER_STATUS, UNIFORM_SIZES, etc.). **Read this before creating any service file, hook, or form.**
3. **SKILLS.md** — React best practices, Custom Hook boundaries, UI Component structure, Tailwind CSS styling guidelines, and Frontend Code Quality standards.
4. **AGENT.md** — Frontend coding standards, React/JSX naming conventions, Vite build/run commands, and UI form/API response validation rules that apply to every task.

Use ARCHITECTURE.md, SKILLS.md, and AGENT.md to create README.md.

---

## Frontend Technology Stack

| Layer               | Technology                  | Purpose                                                              |
|---------------------|-----------------------------|----------------------------------------------------------------------|
| Framework           | React.js (via Vite)         | Core UI rendering and fast local development builds.                 |
| Language            | JavaScript (ES6+)           | Core logic and application structure. No TypeScript.                 |
| Routing             | React Router DOM v6         | Client-side routing for public pages and admin dashboard.            |
| Styling             | Tailwind CSS                | Utility-first responsive styling.                                    |
| Component Library   | Shadcn/UI                   | Pre-built accessible UI components styled with Tailwind.             |
| Font                | Inter                       | https://fonts.googleapis.com/css2?family=Inter                       |
| Forms & Validation  | React Hook Form + Zod       | Dynamic form state management with strict schema validation.         |
| Server State        | TanStack React Query        | API data fetching, caching, background refetching, and mutations.    |
| Client State        | createContext + useContext   | Auth session, cart items, user role, global UI flags.                |
| Data Fetching       | Axios                       | Interceptor-ready HTTP client for backend REST API calls.            |
| Icons               | Lucide React                | Modern SVG icons integrated with Shadcn/UI.                          |

---

## Colors

| Token     | Hex       |
|-----------|-----------|
| Primary   | `#1E3A5F` |
| Secondary | `#F97316` |
| Neutral   | `#F8FAFC` |
| Danger    | `#EF4444` |

---

## Install Core Dependencies

```bash
npm install axios @tanstack/react-query react-hook-form @hookform/resolvers zod react-router-dom lucide-react
```

---

## Environment Configuration

```env
# .env
VITE_API_BASE_URL=http://localhost:3000
```

> `VITE_API_BASE_URL` must only be read inside `src/services/apiConstants.js`. Never import `import.meta.env` anywhere else.

---

## Build and Run

```bash
npm install     # install all dependencies
npm run dev     # start local dev server
npm run build   # production build
npm run lint    # run linter / formatter
```

---

## Services Layer — Build These First

Before any hook or page, create the three service files in order. Full implementation details are in **API_SETUP.md → Section 2**.

| File                        | Purpose                                              |
|-----------------------------|------------------------------------------------------|
| `src/services/apiConstants.js` | Reads `VITE_API_BASE_URL` from env                |
| `src/services/apiUrls.js`   | All endpoint strings grouped by domain               |
| `src/services/api.js`       | Axios instance with request/response interceptors    |

---

## API Hooks — One File per Domain

After the service layer is set up, create these hook files in `src/hooks/`. Full implementation for each is in **API_SETUP.md → Section 4**.

| File                    | Hooks Exported                                                              |
|-------------------------|-----------------------------------------------------------------------------|
| `hooks/use-auth.js`     | `useLogin`, `useRegister`                                                   |
| `hooks/use-schools.js`  | `useSchools`, `useSchoolDetail`, `useCreateSchool`, `useUpdateSchool`, `useDeleteSchool` |
| `hooks/use-uniforms.js` | `useUniforms`, `useUniformDetail`, `useCreateUniform`                       |
| `hooks/use-cart.js`     | `useCart`, `useAddToCart`, `useUpdateCartItem`, `useRemoveCartItem`         |
| `hooks/use-orders.js`   | `useOrders`, `useCreateOrder`, `useUpdateOrderStatus`                       |
| `hooks/use-delivery.js` | `useAssignTracking`, `useTrackDelivery`                                     |

---

## Constants — Build Before Pages

Create these files in `src/constants/` before building any page. Full values are in **API_SETUP.md → Section 5**.

| File                            | Exports                                                    |
|---------------------------------|------------------------------------------------------------|
| `constants/orderStatus.js`      | `ORDER_STATUS` — PENDING, CONFIRMED, DISPATCHED, DELIVERED, CANCELLED |
| `constants/deliveryStatus.js`   | `DELIVERY_STATUS` — SHIPPED, DELIVERED                    |
| `constants/uniformCategories.js`| `UNIFORM_CATEGORIES` — array of category strings          |
| `constants/uniformSizes.js`     | `UNIFORM_SIZES` — S, M, L, XL, XXL + numeric sizes        |

---

## Reusable Components

Before building any page, implement all controls in `src/components/controls/`. All controls must use `React.forwardRef` and define a `displayName`. See **SKILLS.md** for the three-tier component architecture rules.

---

### 1. TextField
Variants:
- Default
- With label
- With placeholder
- Disabled
- Error state (Zod validation message)
- With icon (prefix / suffix)

---

### 2. Button
Variants:
- Styles: `"default"`, `"outline"`, `"ghost"`, `"destructive"`, `"secondary"`, `"link"`
- With icon + label (prefix / suffix)
- Icon only
- Disabled state
- Loading state (with spinner)

---

### 3. Checkbox
Variants:
- Default / Checked / Disabled
- With label
- Error state (Zod validation)

---

### 4. Dropdown (Select)
Variants:
- Standard select
- Searchable (Combobox pattern)
- Disabled
- Error state (Zod validation)

---

### 5. StatusBadge
Maps directly to `ORDER_STATUS` constants:
- `PENDING` — Yellow
- `CONFIRMED` — Blue
- `DISPATCHED` — Orange
- `DELIVERED` — Green
- `CANCELLED` — Red

---

### 6. Card (SchoolCard / OrderCard)
- **SchoolCard:** school name, logo placeholder, active/inactive indicator, "Select" CTA
- **OrderCard:** order ID, school name, total items, StatusBadge, action buttons
- Hoverable with subtle shadow

---

### 7. Alert
Variants: Success, Error, Warning, Info

---

### 8. ConfirmationModal
Variants:
- Default (title + description + confirm/cancel)
- Danger action (deactivate school, cancel order)
- Loading state while mutation is in flight

---

### 9. QuantitySelector
- Increment/Decrement with min=1 enforced
- Disabled state
- Validation error if qty exceeds available stock

---

### 10. PageHeader
Variants:
- Title + subtitle
- With back navigation arrow
- With action button (e.g., "Add School", "Dispatch Order")

---

### 11. EmptyState
One variant per domain — each includes an icon, heading, subtext, and optional CTA button:
- No schools found
- No uniforms configured
- No orders yet
- Cart is empty

---

### 12. SkeletonLoader
Variants:
- Card skeleton (3-col grid)
- Table row skeleton
- Full-page skeleton

Use while `isLoading` from TanStack Query is `true`.

---

## Pages & Forms — Field Reference

This section defines exactly which fields each form must render, derived directly from the API payloads in **API_SETUP.md → Section 3**. Always pair each form with its matching Zod schema from **API_SETUP.md → Section 6**.

---

### Auth Pages (`components/pages/public/`)

#### Login Page (`/login` and `/admin/login`)
Form fields:
- `email` — TextField, type=email, label "Email"
- `password` — TextField, type=password, label "Password"

Zod schema: `loginSchema`
On success: extract token from `response.data.data.token`, store as `authToken` in localStorage, update `AuthContext`.

#### Register Page (`/register`)
Form fields:
- `name` — TextField, label "Full Name"
- `email` — TextField, type=email, label "Email"
- `password` — TextField, type=password, label "Password" (min 8 chars)

Zod schema: `registerSchema`

---

### School Management (`components/pages/admin/`)

#### School List Page (`/admin/schools`)
- Uses `useSchools({ page, limit, search })` hook
- Search TextField bound to the `search` body param
- Pagination controls bound to `page` and `limit` query params
- Each row/card shows: name, email, contact_number, address + Edit and Delete actions

#### Create / Edit School Form (modal or page)
Form fields:
- `name` — TextField, label "School Name"
- `address` — TextField, label "Address"
- `contact_number` — TextField, label "Contact Number" (10 digits)
- `email` — TextField, type=email, label "Email"

Zod schema: `schoolSchema`
Hooks: `useCreateSchool` / `useUpdateSchool`

---

### Uniform Management (`components/pages/admin/`)

#### Uniform List Page (`/admin/schools/:schoolId/uniforms`)
- Uses `useUniforms({ schoolId, page, limit })` hook
- Filter is driven by `school_id` — must always be passed
- Each row shows: name, category, price, sizes (parsed from JSON string), actions

#### Create Uniform Form
Form fields:
- `school_id` — Dropdown, label "School" (populated from `useSchools`)
- `name` — TextField, label "Uniform Name"
- `category` — Dropdown, label "Category" (options from `UNIFORM_CATEGORIES` constant)
- `price` — TextField, type=number, label "Price (₹)"
- `sizes` — Checkbox group, label "Available Sizes" (options from `UNIFORM_SIZES` constant, value is `string[]`)

Zod schema: `uniformSchema`
Hook: `useCreateUniform`
**Important:** Convert `sizes` array → `JSON.stringify(sizes)` inside the hook before sending. See **API_SETUP.md → `use-uniforms.js`**.

---

### Parent-Facing Pages (`components/pages/public/`)

#### School Selection Page (`/`)
- Uses `useSchools()` hook
- Renders a grid of SchoolCards
- Selecting a school stores it in context and navigates to the uniform listing

#### Uniform Listing Page (`/schools/:schoolId/uniforms`)
- Uses `useUniforms({ schoolId })` hook
- Each uniform shows: name, category, price, available sizes
- "Add to Cart" triggers a size picker + quantity selector

#### Add to Cart — Inline or Modal Form
Form fields:
- `uniform_id` — hidden (from the selected uniform)
- `size` — Dropdown / button group, label "Select Size" (populated from parsed `sizes` array of that uniform)
- `quantity` — QuantitySelector, min=1, label "Quantity"

Zod schema: `addToCartSchema`
Hook: `useAddToCart`

#### Cart Page (`/cart`)
- Uses `useCart()` hook
- Lists all cart items: uniform name, size, quantity (editable via QuantitySelector), line total
- Update quantity: `useUpdateCartItem({ cartItemId, quantity })`
- Remove item: `useRemoveCartItem(cartItemId)`
- "Place Order" button: validate cart is non-empty, then call `useCreateOrder`

#### Order Confirmation / Order History Page (`/orders`)
- Uses `useOrders({ page, limit, status })` hook
- Status filter Dropdown bound to `ORDER_STATUS` constants
- Each OrderCard shows: order ID, school, total items, status badge

---

### Admin Order & Delivery Pages (`components/pages/admin/`)

#### Admin Order List Page (`/admin/orders`)
- Uses `useOrders({ page, limit, status })` hook
- Status filter Dropdown
- Each row shows: order ID, parent name, school, item count, status badge, "Update Status" action

#### Update Order Status Form (inline or modal)
Form fields:
- `status` — Dropdown, label "New Status" (options from `ORDER_STATUS` constant)

Zod schema: `updateOrderStatusSchema`
Hook: `useUpdateOrderStatus({ orderId, status })`

#### Delivery Management Page (`/admin/delivery`)
- Track delivery: `useTrackDelivery(orderId)` — displays current tracking status
- Assign/update tracking: `useAssignTracking({ orderId, status })` — status field from `DELIVERY_STATUS` constant

---

## Component Viewer (Development Only)

Create a `/component-viewer` route that renders all reusable components with all their variants on a single scrollable page. Gate behind an env flag (`VITE_SHOW_COMPONENT_VIEWER=true`) in production.

---

## Critical API Conventions (must follow everywhere)

| Convention | Rule |
|------------|------|
| List endpoints use POST | `schools/list`, `uniforms/list`, `orders/list` all use HTTP POST. Always call `api.post()`. |
| Pagination is in query params | `?page=1&limit=10` appended to the URL string. |
| Filters are in the request body | `search`, `school_id`, `status` go in the POST body. |
| Token extraction path | `response.data.data.token` — note the double `.data`. |
| Sizes serialization | Uniform `sizes` is sent as `JSON.stringify(array)` and received as a JSON string — always `JSON.parse()` before rendering. |
| Cart pre-validation | Always verify cart is non-empty before calling `useCreateOrder`. |
| Auth-exempt routes | `/api/auth/login` and `/api/auth/register` skip the `Authorization` header. |
