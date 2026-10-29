from django.core.management.base import BaseCommand
from apps.reports.models import TechStackBlueprint


class Command(BaseCommand):
    help = "Seed pre-configured, battle-tested Tech Stack Blueprints into the database"

    def handle(self, *args, **options):
        blueprints = [
            {
                "name": "Django REST Framework + Modern Frontend",
                "slug": "django-drf-modern",
                "description": "Production-ready Python backend with Django REST Framework, JWT authentication, modular apps, and a modern frontend.",
                "keywords": ["django", "drf", "python", "rest framework", "sqlite", "postgresql", "jwt", "vanilla", "react"],
                "file_structure": r"""project_root/
├── config/                  # Project configuration root
│   ├── settings.py          # Environment-driven settings (python-dotenv)
│   ├── urls.py              # Root URL routing
│   └── wsgi.py
├── apps/                    # Feature apps directory
│   ├── accounts/            # Identity, custom User, JWT auth
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   └── [core_feature]/      # Domain business feature
│       ├── models.py
│       ├── views.py         # Thin API views
│       ├── services.py      # Fat service layer (business logic & external APIs)
│       ├── serializers.py
│       └── urls.py
├── agent-prompts/           # External prompt templates for LLMs
├── static/                  # CSS/JS assets (Vanilla CSS design system)
├── templates/               # HTML5 templates
├── .env.example             # Environment variable template
├── requirements.txt         # Pinned python dependencies
└── manage.py""",
                "coding_standards": """1. Architectural Pattern:
   - Thin Views, Fat Services: Views only handle HTTP request parsing, status codes, and authorization. All business rules, state transitions, and external AI/API calls belong in services.py.
2. Identity & Access Management:
   - Always use a Custom User model inheriting from AbstractUser with email as USERNAME_FIELD.
   - Stateless JWT Authentication via rest_framework_simplejwt.
3. Multi-Tenancy & Data Isolation:
   - Use OwnedModelsMixin / get_queryset scoping (filter by owner=request.user) on every user-facing query.
4. Error Handling & State Machines:
   - Explicit state tracking on long-running tasks: Pending (0), Processing (1), Completed (2), Failed (3).
   - Never let external API calls crash the application. Catch exceptions, persist error details on the model, and return descriptive HTTP status codes (409 Conflict, 502 Bad Gateway).""",
                "agent_instructions": """- Read existing files and settings before proposing modifications.
- Preserve all existing comments and docstrings.
- Always use environment variables for sensitive secrets (API keys, secret keys).
- Write self-contained, modular applications inside the apps/ folder.
- Ensure all interactive frontend elements have unique, accessible IDs and responsive styling.""",
                "setup_commands": """# 1. Create and activate virtual environment
python -m venv .venv
# Windows PowerShell:
.\\.venv\\Scripts\\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env

# 4. Run migrations
python manage.py migrate

# 5. Start development server
python manage.py runserver"""
            },
            {
                "name": "FastAPI + Next.js (Fullstack App)",
                "slug": "fastapi-nextjs",
                "description": "High-performance async Python API backend paired with Next.js 14+ App Router, Tailwind CSS, and TypeScript.",
                "keywords": ["fastapi", "nextjs", "next.js", "tailwind", "python", "typescript", "react", "async", "pydantic"],
                "file_structure": r"""project_root/
├── backend/
│   ├── app/
│   │   ├── api/             # API route handlers organized by version (v1)
│   │   ├── core/            # Config, security, database session
│   │   ├── models/          # SQLAlchemy database models
│   │   ├── schemas/         # Pydantic schemas (request/response validation)
│   │   ├── services/        # Business logic & external AI integrations
│   │   └── main.py          # FastAPI application entrypoint
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router (pages, layouts)
│   │   ├── components/      # Reusable UI components
│   │   ├── lib/             # API client, state, auth helpers
│   │   └── types/           # TypeScript definitions
│   └── package.json
├── docker-compose.yml
└── README.md""",
                "coding_standards": """1. Type Safety & Validation:
   - Strict Pydantic v2 schemas for every endpoint input and output.
   - TypeScript strict mode enabled on frontend (zero 'any' types allowed).
2. Asynchronous Architecture:
   - Async endpoints and async SQLAlchemy database sessions for all I/O operations.
3. Separation of Concerns:
   - Route handlers must not write raw queries; all data manipulation must go through crud/ or services/.
4. Frontend Architecture:
   - Server Components by default; use 'use client' only when hooks/interactivity are necessary.""",
                "agent_instructions": """- Ensure backend schemas align 1:1 with frontend TypeScript interfaces.
- Use dependency injection for database sessions and current user retrieval (Depends(get_db), Depends(get_current_user)).
- Use modern Next.js App Router conventions.""",
                "setup_commands": """# Backend setup:
cd backend
python -m venv .venv
source .venv/bin/activate  # or .\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend setup:
cd ../frontend
npm install
npm run dev"""
            },
            {
                "name": "Node.js (Express / TypeScript) + PostgreSQL + React",
                "slug": "express-postgres-react",
                "description": "Enterprise-grade 3-tier Node.js API with Prisma ORM, PostgreSQL, Zod validation, and React frontend.",
                "keywords": ["node", "nodejs", "express", "typescript", "postgres", "postgresql", "prisma", "zod", "react"],
                "file_structure": r"""project_root/
├── server/
│   ├── src/
│   │   ├── controllers/     # HTTP route handlers
│   │   ├── services/        # Business logic & integrations
│   │   ├── repositories/    # Prisma database access layer
│   │   ├── middleware/      # Auth, error handling, rate limiting
│   │   ├── routes/          # Express route definitions
│   │   ├── config/          # Environment configuration
│   │   └── app.ts           # App entrypoint
│   ├── prisma/
│   │   └── schema.prisma    # Data models & migrations
│   └── package.json
├── client/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── App.tsx
│   └── package.json
└── package.json""",
                "coding_standards": """1. 3-Tier Layered Architecture:
   - Controller -> Service -> Repository. Controllers parse requests and return HTTP responses. Services contain business logic. Repositories communicate with Prisma.
2. Input Validation:
   - Validate 100% of request bodies, query params, and route params using Zod middleware.
3. Database Hygiene:
   - Never write raw SQL in controllers. Use Prisma schema migrations.
4. Error Handling:
   - Centralized error handling middleware. Custom AppError classes for 400, 401, 403, 404, 409.""",
                "agent_instructions": """- Strictly avoid any types. Every variable, parameter, and return value must be typed.
- Handle all async operations with try/catch or async handler wrappers.""",
                "setup_commands": """# Install root and workspace dependencies
npm install

# Run database migrations
npx prisma migrate dev
npm run dev"""
            },
            {
                "name": "React.js (Vite) + Tailwind + Shadcn/UI (REST Client)",
                "slug": "react-vite-shadcn",
                "description": "Production frontend architecture strictly using React.js (Vite), JavaScript ES6+ (no TypeScript), Tailwind CSS, Shadcn/UI, React Hook Form + Zod, TanStack Query, and Axios.",
                "keywords": ["react", "vite", "tailwind", "shadcn", "axios", "tanstack", "query", "zod", "javascript", "uniform", "mart", "frontend"],
                "file_structure": r"""src/
|-- assets/                     # Static assets (images, icons, animations)
|-- components/
|   |-- ui/                     # Tier 1: Base auto-generated Shadcn components (DO NOT EDIT MANUALLY)
|   |-- controls/               # Tier 2: Custom wrapper components (Inputs, Buttons with Zod validation)
|   |-- common/                 # Tier 3: Larger reusable pieces (Navbar, Sidebar, Cards, Modals)
|   \-- pages/                  # Full-screen React components representing views/routes
|       |-- admin/              # Admin dashboard pages
|       \-- public/             # Public/Customer facing pages
|-- constants/                  # App constants, API endpoint names, status enums
|-- context/                    # React Context providers (AuthContext, CartContext)
|-- hooks/                      # Custom React hooks (TanStack Query hooks per domain)
|-- helpers/                    # Reusable business logic helper functions
|-- utils/                      # Generic utility functions (date formatting, status labels)
|-- routes/                     # React Router v6 & ProtectedRoute
|-- services/
|   |-- apiConstants.js         # ONLY file allowed to read VITE_ env variables
|   |-- apiUrls.js              # Single source of truth for all endpoint strings
|   \-- api.js                  # Axios instance with interceptors for Bearer token & 401 redirect
|-- App.jsx                     # Root component (<Providers> and <AppRouter>)
\-- main.jsx                    # Vite entry point""",
                "coding_standards": """1. Strict Three-Tier Component Architecture:
   - Tier 1: Base UI (components/ui/) installed via Shadcn CLI. Never hand-edited.
   - Tier 2: Controls (components/controls/) wrapping base UI with React.forwardRef, displayName, and Zod/RHF controllers.
   - Tier 3: Common composed pieces (Navbar, Sidebar, Modals, Cards).
   - Tier 4: Pages and Route Guards.
2. Services Layer Protocol:
   - apiConstants.js: ONLY file allowed to read VITE_ env variables.
   - apiUrls.js: Single source of truth for all endpoint strings grouped by domain.
   - api.js: Axios instance with request/response interceptors for Bearer token and 401 redirect.
3. State Management Protocol:
   - Server State: TanStack Query (one hook file per domain in src/hooks/).
   - Global Client State: Context API (Auth, Cart). No Redux.
   - Local UI State: useState.
4. Styling:
   - Strictly Tailwind CSS utility classes. No custom .scss files.
   - Palette tokens: Primary, Secondary, Neutral, Danger.""",
                "agent_instructions": """- Write plain JavaScript (ES6+) — do NOT use TypeScript.
- Follow strict naming conventions: kebab-case for files, PascalCase for components, camelCase for hooks/schemas.
- Never mutate React state directly.
- Never make direct API calls inside Context providers or components; always go through hooks/.
- All Tier 2 controls MUST use React.forwardRef and declare a displayName.""",
                "setup_commands": """# Install core dependencies
npm install axios @tanstack/react-query react-hook-form @hookform/resolvers zod react-router-dom lucide-react

# Local development
npm run dev

# Build & lint
npm run build
npm run lint"""
            }
        ]

        for bp_data in blueprints:
            bp, created = TechStackBlueprint.objects.update_or_create(
                slug=bp_data["slug"],
                defaults=bp_data,
            )
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} blueprint: {bp.name}"))

        self.stdout.write(self.style.SUCCESS("All blueprints seeded successfully!"))
