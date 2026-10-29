# School Accessories Mart – Frontend Architecture

School Accessories Mart is a responsive, web-based uniform ordering platform built with React.js for managing school uniform orders.

It has two main parts:
1. A mobile-friendly site for parents/students to browse schools, select uniforms, and place orders.
2. A secure desktop dashboard for the Owner/Admin to manage schools, uniforms, orders, and dispatch tracking.

**Note:** This repository contains the Frontend application only, without any server-side API.

This React application is strictly a client that consumes REST APIs. All API communication is handled via Axios, and the base API URL is managed through environment variables (VITE_API_BASE_URL).

## Frontend Technology Stack

| Layer               | Technology                  | Purpose                                                              |
|---------------------|-----------------------------|----------------------------------------------------------------------|
| Framework           | React.js (via Vite)         | Core UI rendering and lightning-fast local development builds.       |
| Language            | JavaScript (ES6+)           | Core logic and application structure.                                |
| Routing             | React Router DOM v6         | Client-side routing for public pages and admin dashboard.            |
| Styling             | Tailwind CSS                | Utility-first styling for responsive layouts.                        |
| Component Library   | Shadcn/UI                   | Pre-built accessible components styled with Tailwind.                |
| Font                | Inter                       | Inter font (https://fonts.googleapis.com/css2?family=Inter).         |
| Forms & Validation  | React Hook Form + Zod       | Managing form state and strict schema validation.                    |
| Server State        | TanStack React Query        | API data fetching, caching, loading states, and mutations.           |
| Client State        | createContext + useContext   | App-wide state: auth session, cart, active school, user role.        |
| Data Fetching       | Axios                       | Clean, interceptor-ready HTTP requests to the Node.js backend.       |
| Icons               | Lucide React                | Clean, modern SVG icons that integrate seamlessly with Shadcn/UI.    |


## Folder Structure

```
src/
├── assets/                     # Static assets
│   ├── images/                 # Images used across the app
│   ├── icons/                  # Custom icons
│   └── animations/             # Lottie or CSS animations
├── components/
│   ├── ui/                     # Tier 1: Base auto-generated Shadcn components (DO NOT EDIT MANUALLY)
│   ├── controls/               # Tier 2: Custom wrapper components (Inputs, Buttons with Zod validation)
│   ├── common/                 # Tier 3: Larger reusable pieces (Navbar, Sidebar, Cards, Modals)
│   └── pages/                  # Full-screen React components representing views/routes
│       ├── admin/              # Admin-only pages (school mgmt, uniform config, orders)
│       └── public/             # Parent/student-facing pages (school selection, cart, order)
├── constants/                  # App constants, API endpoint names, magic numbers
├── context/                    # React Context providers (AuthContext, CartContext, AppContext)
├── hooks/                      # Custom React hooks (TanStack Query hooks per module)
├── helpers/                    # Reusable business logic helper functions
├── utils/                      # Generic utility functions (date formatting, status labels)
├── routes/
│   ├── AppRouter.jsx           # Main routing logic — public vs admin
│   └── ProtectedRoute.jsx      # Route guard for admin/owner access
├── services/
│   ├── apiConstants.js         # ONLY file allowed to read VITE_ env variables
│   ├── apiUrls.js              # All API endpoint strings — never hardcode URLs elsewhere
│   └── api.js                  # Axios instance with base URL & interceptors
├── App.jsx                     # Root component (renders <Providers> and <AppRouter>)
└── main.jsx                    # Vite entry point (ReactDOM.createRoot)
```
