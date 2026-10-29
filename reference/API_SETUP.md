# API Architecture & Data Fetching Setup

This project uses **Axios** (for the HTTP transport layer) and **TanStack Query** (for React server state, caching, and loading management).

We strictly use a modern hook-based architecture. Do NOT use class-based API wrappers and do NOT use Redux for loading/error states. Follow the exact folder structure and implementation rules below.

---

## 1. Folder Structure

All core API configurations live in the `src/services/` directory. All data fetching hooks live in `src/hooks/`.

```
src/
├── services/
│   ├── apiConstants.js   ← ONLY file allowed to read VITE_ env variables
│   ├── apiUrls.js        ← Single source of truth for all endpoint strings
│   └── api.js            ← Axios instance with interceptors + HTTP helpers
└── hooks/
    ├── use-auth.js
    ├── use-schools.js
    ├── use-uniforms.js
    ├── use-cart.js
    ├── use-orders.js
    └── use-delivery.js
```

---

## 2. File Implementation Rules

### A. `services/apiConstants.js`
- **Purpose:** This is the ONLY file allowed to read from environment variables (`import.meta.env`).
- **Implementation:** Export your base URL here. Do not read `.env` files directly in components or inside Axios instances.

```javascript
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
```

---

### B. `services/apiUrls.js`
- **Purpose:** A single source of truth for all API endpoint strings.
- **Rule:** You are strictly forbidden from hardcoding URL strings inside TanStack Query hooks or Axios calls.
- **Format:** Export grouped constant objects — one group per domain.

```javascript
export const ENDPOINTS = {

  ping: {
    health: '/api/ping',                                  // GET
  },

  auth: {
    register: '/api/auth/register',                       // POST
    login: '/api/auth/login',                             // POST
  },

  schools: {
    create: '/api/schools',                               // POST
    list: '/api/schools/list',                            // POST  ← uses POST for search/pagination
    detail: (id) => `/api/schools/${id}`,                 // GET
    update: (id) => `/api/schools/${id}`,                 // PUT
    delete: (id) => `/api/schools/${id}`,                 // DELETE
  },

  uniforms: {
    create: '/api/uniforms',                              // POST
    list: '/api/uniforms/list',                           // POST  ← uses POST for school_id filter
    detail: (id) => `/api/uniforms/${id}`,                // GET
  },

  cart: {
    get: '/api/cart',                                     // GET
    addItem: '/api/cart',                                 // POST
    updateItem: (cartItemId) => `/api/cart/${cartItemId}`,// PUT
    removeItem: (cartItemId) => `/api/cart/${cartItemId}`,// DELETE
  },

  orders: {
    create: '/api/orders',                                // POST
    list: '/api/orders/list',                             // POST  ← uses POST for status filter
    updateStatus: (orderId) => `/api/orders/${orderId}/status`, // PUT
  },

  delivery: {
    assign: (orderId) => `/api/delivery/${orderId}`,      // POST
    track: (orderId) => `/api/delivery/${orderId}`,       // GET
  },

};
```

> **Important:** Several list endpoints (`schools/list`, `uniforms/list`, `orders/list`) use **POST** instead of GET. They accept filter parameters in the request body and pagination via query params. Always call them with `api.post()`, not `api.get()`.

---

### C. `services/api.js` (Core Axios Instance)
- **Purpose:** Handles base URL, auth headers, and centralized error responses.
- **Implementation:**
  - Create a base Axios instance using `axios.create({ baseURL: API_BASE_URL })`.
  - Provide a common helper function for each HTTP verb: `get`, `post`, `put`, `patch`, `del`.
- **Request Interceptor:** Attaches `Authorization: Bearer <token>` to every request. Token is read from `localStorage` under the key `authToken`. Skip injection on the `/api/auth/login` and `/api/auth/register` routes.
- **Response Interceptor:** On a `401` response — clear `authToken` from `localStorage` and redirect to `/admin/login`.

```javascript
import axios from 'axios';
import { API_BASE_URL } from '@/services/apiConstants';

const AUTH_EXEMPT = ['/api/auth/login', '/api/auth/register'];

const axiosInstance = axios.create({ baseURL: API_BASE_URL });

axiosInstance.interceptors.request.use((config) => {
  const isExempt = AUTH_EXEMPT.some((url) => config.url?.includes(url));
  if (!isExempt) {
    const token = localStorage.getItem('authToken');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/admin/login';
    }
    return Promise.reject(error);
  }
);

export const api = {
  get:   (url, config) => axiosInstance.get(url, config),
  post:  (url, data, config) => axiosInstance.post(url, data, config),
  put:   (url, data, config) => axiosInstance.put(url, data, config),
  patch: (url, data, config) => axiosInstance.patch(url, data, config),
  del:   (url, config) => axiosInstance.delete(url, config),
};

export default api;
```

---

## 3. Complete API Reference (from Postman Collection)

Use this section as the ground truth when writing hooks and form schemas. Every field listed here must be accounted for in the corresponding Zod schema and TanStack Query hook.

---

### 🔹 Ping

| Method | Endpoint    | Auth | Purpose       |
|--------|-------------|------|---------------|
| GET    | `/api/ping` | No   | Health check  |

No request body. Use this to verify the backend is reachable.

---

### 🔹 Auth

#### Register Parent
| Method | Endpoint              | Auth |
|--------|-----------------------|------|
| POST   | `/api/auth/register`  | No   |

**Request Body:**
```json
{
  "name": "string",        // required — full name of the parent
  "email": "string",       // required — valid email address
  "password": "string"     // required — min 8 characters
}
```

#### Login
| Method | Endpoint           | Auth |
|--------|--------------------|------|
| POST   | `/api/auth/login`  | No   |

**Request Body:**
```json
{
  "email": "string",       // required
  "password": "string"     // required
}
```

**Response Shape:**
```json
{
  "data": {
    "token": "string"      // ← JWT token; store in localStorage as 'authToken'
  }
}
```

> The `authToken` must be extracted from `response.data.data.token` (note the nested `data` wrapper). Store it as `authToken` in `localStorage` and update `AuthContext` immediately after login.

---

### 🔹 Schools  *(Admin / Bearer token required)*

#### Create School
| Method | Endpoint       | Auth   |
|--------|----------------|--------|
| POST   | `/api/schools` | Bearer |

**Request Body:**
```json
{
  "name": "string",            // required — school name
  "address": "string",         // required — full address
  "contact_number": "string",  // required — 10-digit phone number
  "email": "string"            // required — valid email
}
```

#### List Schools
| Method | Endpoint              | Auth   | Query Params        |
|--------|-----------------------|--------|---------------------|
| POST   | `/api/schools/list`   | Bearer | `page`, `limit`     |

**Request Body:**
```json
{
  "search": "string"           // optional — empty string returns all schools
}
```

#### Get School Details
| Method | Endpoint                | Auth   |
|--------|-------------------------|--------|
| GET    | `/api/schools/:schoolId`| Bearer |

No request body.

#### Update School
| Method | Endpoint                | Auth   |
|--------|-------------------------|--------|
| PUT    | `/api/schools/:schoolId`| Bearer |

**Request Body:** (all fields optional — send only what needs updating)
```json
{
  "name": "string",
  "address": "string",
  "contact_number": "string",
  "email": "string"
}
```

#### Delete School
| Method | Endpoint                | Auth   |
|--------|-------------------------|--------|
| DELETE | `/api/schools/:schoolId`| Bearer |

No request body.

---

### 🔹 Uniforms  *(Admin / Bearer token required)*

#### Create Uniform
| Method | Endpoint        | Auth   |
|--------|-----------------|--------|
| POST   | `/api/uniforms` | Bearer |

**Request Body:**
```json
{
  "school_id": "string",       // required — ID of the school this uniform belongs to
  "name": "string",            // required — uniform item name (e.g., "Summer Shirt")
  "category": "string",        // required — e.g., "Summer Wear", "Winter Wear", "Sports Wear"
  "price": "number",           // required — unit price as a decimal (e.g., 25.00)
  "sizes": "string"            // required — JSON-stringified array (e.g., "[\"S\",\"M\",\"L\"]")
}
```

> **`sizes` field:** The backend expects a **JSON-stringified array** of size strings, not a plain array. Always call `JSON.stringify(sizesArray)` before sending. Valid size values: `"S"`, `"M"`, `"L"`, `"XL"`, `"XXL"`, or numeric sizes like `"28"`, `"30"`, etc.

#### List Uniforms
| Method | Endpoint              | Auth   | Query Params    |
|--------|-----------------------|--------|-----------------|
| POST   | `/api/uniforms/list`  | Bearer | `page`, `limit` |

**Request Body:**
```json
{
  "school_id": "string"        // required — filter uniforms by school
}
```

#### Get Uniform Details
| Method | Endpoint                   | Auth   |
|--------|----------------------------|--------|
| GET    | `/api/uniforms/:uniformId` | Bearer |

No request body.

---

### 🔹 Cart  *(Parent / Bearer token required)*

#### Get Active Cart
| Method | Endpoint    | Auth   |
|--------|-------------|--------|
| GET    | `/api/cart` | Bearer |

No request body. Returns the current user's active cart with all items.

#### Add Item to Cart
| Method | Endpoint    | Auth   |
|--------|-------------|--------|
| POST   | `/api/cart` | Bearer |

**Request Body:**
```json
{
  "uniform_id": "string",      // required — ID of the uniform to add
  "quantity": "number",        // required — must be ≥ 1
  "size": "string"             // required — must match one of the uniform's available sizes
}
```

#### Update Cart Item
| Method | Endpoint                     | Auth   |
|--------|------------------------------|--------|
| PUT    | `/api/cart/:cartItemId`      | Bearer |

**Request Body:**
```json
{
  "quantity": "number"         // required — must be ≥ 1
}
```

#### Remove Cart Item
| Method | Endpoint                     | Auth   |
|--------|------------------------------|--------|
| DELETE | `/api/cart/:cartItemId`      | Bearer |

No request body.

---

### 🔹 Orders  *(Bearer token required)*

#### Create Order from Cart
| Method | Endpoint      | Auth   |
|--------|---------------|--------|
| POST   | `/api/orders` | Bearer |

No request body. The backend converts the active cart into an order. Always validate that the cart is non-empty before calling this.

#### List Orders
| Method | Endpoint             | Auth   | Query Params    |
|--------|----------------------|--------|-----------------|
| POST   | `/api/orders/list`   | Bearer | `page`, `limit` |

**Request Body:**
```json
{
  "status": "string"           // optional — filter by order status (see ORDER_STATUS constants)
}
```

**Valid Status Values:** `"PENDING"`, `"CONFIRMED"`, `"DISPATCHED"`, `"DELIVERED"`, `"CANCELLED"`

#### Update Order Status
| Method | Endpoint                         | Auth   |
|--------|----------------------------------|--------|
| PUT    | `/api/orders/:orderId/status`   | Bearer |

**Request Body:**
```json
{
  "status": "string"           // required — new status value
}
```

---

### 🔹 Delivery  *(Admin / Bearer token required)*

#### Assign / Update Tracking
| Method | Endpoint                   | Auth   |
|--------|----------------------------|--------|
| POST   | `/api/delivery/:orderId`   | Bearer |

**Request Body:**
```json
{
  "status": "string"           // required — e.g., "SHIPPED"
}
```

#### Track Delivery
| Method | Endpoint                   | Auth   |
|--------|----------------------------|--------|
| GET    | `/api/delivery/:orderId`   | Bearer |

No request body. Returns the current delivery/tracking status for the order.

---

## 4. Hook Implementations per Domain

One hook file per domain inside `src/hooks/`. Naming convention: `use-{domain}.js`.

---

### `use-auth.js`

```javascript
import { useMutation } from '@tanstack/react-query';
import api from '@/services/api';
import { ENDPOINTS } from '@/services/apiUrls';

// POST /api/auth/register
export const useRegister = () => {
  return useMutation({
    mutationFn: (body) => api.post(ENDPOINTS.auth.register, body),
  });
};

// POST /api/auth/login  → extract token from response.data.data.token
export const useLogin = () => {
  return useMutation({
    mutationFn: (body) => api.post(ENDPOINTS.auth.login, body),
  });
};
```

---

### `use-schools.js`

```javascript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/services/api';
import { ENDPOINTS } from '@/services/apiUrls';

// POST /api/schools/list  (page, limit as query params; search in body)
export const useSchools = ({ page = 1, limit = 10, search = '' } = {}) => {
  return useQuery({
    queryKey: ['schools', page, limit, search],
    queryFn: () =>
      api.post(`${ENDPOINTS.schools.list}?page=${page}&limit=${limit}`, { search }),
  });
};

// GET /api/schools/:id
export const useSchoolDetail = (schoolId) => {
  return useQuery({
    queryKey: ['school', schoolId],
    queryFn: () => api.get(ENDPOINTS.schools.detail(schoolId)),
    enabled: !!schoolId,
  });
};

// POST /api/schools
export const useCreateSchool = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body) => api.post(ENDPOINTS.schools.create, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['schools'] }),
  });
};

// PUT /api/schools/:id
export const useUpdateSchool = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }) => api.put(ENDPOINTS.schools.update(id), body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['schools'] }),
  });
};

// DELETE /api/schools/:id
export const useDeleteSchool = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id) => api.del(ENDPOINTS.schools.delete(id)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['schools'] }),
  });
};
```

---

### `use-uniforms.js`

```javascript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/services/api';
import { ENDPOINTS } from '@/services/apiUrls';

// POST /api/uniforms/list  (school_id in body; page, limit as query params)
export const useUniforms = ({ schoolId, page = 1, limit = 10 } = {}) => {
  return useQuery({
    queryKey: ['uniforms', schoolId, page, limit],
    queryFn: () =>
      api.post(`${ENDPOINTS.uniforms.list}?page=${page}&limit=${limit}`, { school_id: schoolId }),
    enabled: !!schoolId,
  });
};

// GET /api/uniforms/:id
export const useUniformDetail = (uniformId) => {
  return useQuery({
    queryKey: ['uniform', uniformId],
    queryFn: () => api.get(ENDPOINTS.uniforms.detail(uniformId)),
    enabled: !!uniformId,
  });
};

// POST /api/uniforms — sizes must be JSON.stringify(array) before sending
export const useCreateUniform = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body) =>
      api.post(ENDPOINTS.uniforms.create, {
        ...body,
        sizes: JSON.stringify(body.sizes),   // ← always stringify the sizes array
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['uniforms'] }),
  });
};
```

---

### `use-cart.js`

```javascript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/services/api';
import { ENDPOINTS } from '@/services/apiUrls';

// GET /api/cart
export const useCart = () => {
  return useQuery({
    queryKey: ['cart'],
    queryFn: () => api.get(ENDPOINTS.cart.get),
  });
};

// POST /api/cart  →  { uniform_id, quantity, size }
export const useAddToCart = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body) => api.post(ENDPOINTS.cart.addItem, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cart'] }),
  });
};

// PUT /api/cart/:cartItemId  →  { quantity }
export const useUpdateCartItem = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ cartItemId, quantity }) =>
      api.put(ENDPOINTS.cart.updateItem(cartItemId), { quantity }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cart'] }),
  });
};

// DELETE /api/cart/:cartItemId
export const useRemoveCartItem = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (cartItemId) => api.del(ENDPOINTS.cart.removeItem(cartItemId)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cart'] }),
  });
};
```

---

### `use-orders.js`

```javascript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/services/api';
import { ENDPOINTS } from '@/services/apiUrls';

// POST /api/orders  (no body — creates order from active cart)
export const useCreateOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post(ENDPOINTS.orders.create),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['cart'] });
    },
  });
};

// POST /api/orders/list  (status in body; page, limit as query params)
export const useOrders = ({ page = 1, limit = 10, status = '' } = {}) => {
  return useQuery({
    queryKey: ['orders', page, limit, status],
    queryFn: () =>
      api.post(`${ENDPOINTS.orders.list}?page=${page}&limit=${limit}`, { status }),
  });
};

// PUT /api/orders/:orderId/status  →  { status }
export const useUpdateOrderStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ orderId, status }) =>
      api.put(ENDPOINTS.orders.updateStatus(orderId), { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['orders'] }),
  });
};
```

---

### `use-delivery.js`

```javascript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/services/api';
import { ENDPOINTS } from '@/services/apiUrls';

// POST /api/delivery/:orderId  →  { status: "SHIPPED" }
export const useAssignTracking = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ orderId, status }) =>
      api.post(ENDPOINTS.delivery.assign(orderId), { status }),
    onSuccess: (_, { orderId }) =>
      queryClient.invalidateQueries({ queryKey: ['delivery', orderId] }),
  });
};

// GET /api/delivery/:orderId
export const useTrackDelivery = (orderId) => {
  return useQuery({
    queryKey: ['delivery', orderId],
    queryFn: () => api.get(ENDPOINTS.delivery.track(orderId)),
    enabled: !!orderId,
  });
};
```

---

## 5. Constants — `src/constants/`

These constants must be defined before building any page. They are derived directly from the API's accepted values.

### `constants/orderStatus.js`
```javascript
export const ORDER_STATUS = {
  PENDING:    'PENDING',
  CONFIRMED:  'CONFIRMED',
  DISPATCHED: 'DISPATCHED',
  DELIVERED:  'DELIVERED',
  CANCELLED:  'CANCELLED',
};
```

### `constants/deliveryStatus.js`
```javascript
export const DELIVERY_STATUS = {
  SHIPPED:   'SHIPPED',
  DELIVERED: 'DELIVERED',
};
```

### `constants/uniformCategories.js`
```javascript
export const UNIFORM_CATEGORIES = [
  'Summer Wear',
  'Winter Wear',
  'Sports Wear',
  'Formal Wear',
  'Lab Coat',
];
```

### `constants/uniformSizes.js`
```javascript
export const UNIFORM_SIZES = ['S', 'M', 'L', 'XL', 'XXL', '28', '30', '32', '34', '36'];
```

---

## 6. Zod Schemas — Derived from API Payloads

One schema file per domain inside the same file as its form component, or in `src/helpers/` if reused. All schemas are in camelCase + `Schema` suffix.

```javascript
// registerSchema
import { z } from 'zod';
export const registerSchema = z.object({
  name:     z.string().min(1, 'Name is required'),
  email:    z.string().email('Enter a valid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

// loginSchema
export const loginSchema = z.object({
  email:    z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
});

// schoolSchema
export const schoolSchema = z.object({
  name:           z.string().min(1, 'School name is required'),
  address:        z.string().min(1, 'Address is required'),
  contact_number: z.string().length(10, 'Enter a valid 10-digit number'),
  email:          z.string().email('Enter a valid email'),
});

// uniformSchema
export const uniformSchema = z.object({
  school_id: z.string().min(1, 'School is required'),
  name:      z.string().min(1, 'Uniform name is required'),
  category:  z.string().min(1, 'Category is required'),
  price:     z.number({ invalid_type_error: 'Price must be a number' }).positive('Price must be greater than 0'),
  sizes:     z.array(z.string()).min(1, 'Select at least one size'),
  // Note: sizes is stored as string[] in the form; converted to JSON.stringify() before API call
});

// addToCartSchema
export const addToCartSchema = z.object({
  uniform_id: z.string().min(1, 'Uniform is required'),
  quantity:   z.number().int().min(1, 'Quantity must be at least 1'),
  size:       z.string().min(1, 'Size is required'),
});

// updateOrderStatusSchema
export const updateOrderStatusSchema = z.object({
  status: z.enum(['PENDING', 'CONFIRMED', 'DISPATCHED', 'DELIVERED', 'CANCELLED']),
});
```

---

## 7. AI Agent Strict Boundaries

- **NO CLASSES:** Do not create monolithic API classes with static methods. Use functional instances only.
- **NO MANUAL STATE:** Do not track `loading` or `error` with `useState`. Use TanStack Query's `isLoading`, `isError`, and `isSuccess`.
- **NO HARDCODED URLS:** Every endpoint string must come from `apiUrls.js`. Writing URL strings directly inside hooks or components is forbidden.
- **NO DIRECT ENV READS:** Never call `import.meta.env.VITE_API_BASE_URL` outside of `apiConstants.js`.
- **LIST ENDPOINTS USE POST:** `schools/list`, `uniforms/list`, and `orders/list` all use the HTTP POST method with filters in the request body and pagination in query params. Never call them with `api.get()`.
- **SIZES MUST BE STRINGIFIED:** The uniform `sizes` field must be `JSON.stringify(array)` before sending to the API. Receive and parse it back with `JSON.parse(sizes)` when rendering.
- **TOKEN PATH:** The login token lives at `response.data.data.token`. Do not assume `response.data.token`.
