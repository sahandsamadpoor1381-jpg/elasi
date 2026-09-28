# ELASI System Architecture Overview

## 1. Purpose

ELASI is a custom-built luxury jewelry e-commerce platform.

The system uses a separated frontend and backend architecture so that presentation, business logic, security, and data management remain clearly isolated.

The architecture must support future growth without coupling the user interface directly to the database.

---

## 2. High-Level Architecture

```text
User Browser
     |
     v
Next.js Frontend
     |
     | HTTPS / REST API
     v
Django REST API
     |
     | Django ORM
     v
PostgreSQL
```

Primary responsibilities:

- Next.js handles presentation and user interaction.
- Django handles business logic and API operations.
- PostgreSQL stores persistent application data.
- Django ORM is the only application layer allowed to manage the database schema.

---

## 3. Frontend

Technology:

- Next.js
- React
- TypeScript

Responsibilities:

- User interface
- Responsive layouts
- Product browsing
- Product filtering
- Search
- Product detail presentation
- Shopping cart interface
- Checkout interface
- Customer account interface
- Form interaction
- API communication
- Client-side state where appropriate
- SEO presentation layer

The frontend must never connect directly to PostgreSQL.

The frontend must never be treated as the source of truth for:

- prices
- inventory
- discounts
- order totals
- permissions
- payment state
- shipping state

All commerce-critical values must be validated by the backend.

---

## 4. Backend

Technology:

- Python
- Django
- Django REST Framework

Responsibilities:

- Authentication
- Authorization
- User management
- Role and permission management
- Product management
- Category management
- Collection management
- Attribute management
- Product variants
- Inventory
- Shopping carts
- Orders
- Payments
- Shipping
- Custom size requests
- Contact messages
- Business rules
- Validation
- Admin operations
- API security
- Data integrity

Django is the authoritative source of business rules.

---

## 5. Database

Technology:

- PostgreSQL

Database access must occur through Django ORM.

The frontend must never receive direct database credentials.

The database will eventually contain domains such as:

- users
- addresses
- products
- categories
- collections
- product images
- product attributes
- attribute values
- product variants
- variant attributes
- inventory
- carts
- cart items
- wishlists
- orders
- order items
- order status history
- payments
- shipping records
- custom size requests
- contact messages

The final database schema must be designed before production product and customer data are inserted.

---

## 6. API

The application API will use versioned endpoints.

Initial API base path:

```text
/api/v1/
```

Example endpoints:

```text
GET    /api/v1/products/
GET    /api/v1/products/{slug}/
GET    /api/v1/categories/
POST   /api/v1/cart/items/
POST   /api/v1/orders/
POST   /api/v1/custom-size-requests/
```

The exact API contract will be documented separately under:

```text
docs/api/
```

The frontend must communicate with the backend through documented API contracts.

---

## 7. Source of Truth

The backend is the source of truth for all commerce-critical data.

For example, the frontend may send:

```json
{
  "variant_id": 42,
  "quantity": 2
}
```

The backend must independently verify:

- the variant exists
- the product exists
- the product is active
- the variant is active
- the variant is purchasable
- sufficient inventory exists
- the current authoritative price
- applicable discounts
- shipping eligibility
- final order totals

The frontend must never be trusted to provide authoritative pricing, inventory, discount, payment, or permission values.

---

## 8. Security Boundary

The browser is considered an untrusted environment.

Therefore:

- secrets must never be exposed to the frontend
- database credentials must never reach the browser
- payment secrets must remain server-side
- authorization must be enforced by Django
- client-submitted prices must never be trusted
- inventory changes must be validated server-side
- sensitive operations must require authentication and permission checks
- user input must be validated and sanitized
- backend responses must avoid exposing unnecessary sensitive information

---

## 9. Development Architecture

Local development services:

```text
Frontend:
http://localhost:3000

Backend:
http://127.0.0.1:8000

API:
http://127.0.0.1:8000/api/v1

PostgreSQL:
127.0.0.1:5432
```

Local request flow:

```text
Browser
   |
   v
Next.js :3000
   |
   v
Django :8000
   |
   v
PostgreSQL :5432
```

---

## 10. Project Boundaries

### Frontend owns

- presentation
- user interaction
- client-side routing
- visual behavior
- responsive behavior
- frontend form state
- API consumption
- appropriate client-side state

### Backend owns

- business logic
- validation
- authentication
- authorization
- persistence
- transactional operations
- inventory decisions
- pricing decisions
- order calculations
- payment state
- shipping state

### Database owns

- durable data
- relational constraints
- indexes
- uniqueness constraints
- referential integrity
- persistence-level consistency

---

## 11. Initial Project Structure

```text
elasi/
|
|-- frontend/
|   `-- Next.js application
|
|-- backend/
|   `-- Django application
|
|-- docs/
|   |-- architecture/
|   |   `-- system-overview.md
|   |
|   |-- api/
|   |
|   `-- decisions/
|
|-- .env.example
|-- .gitignore
`-- README.md
```

The structure will expand gradually as features are implemented.

Unnecessary folders or abstractions must not be created before they are needed.

---

## 12. Architecture Rules

1. Django ORM is the only owner of the PostgreSQL schema.

2. Next.js must never directly query PostgreSQL.

3. Business rules must not be duplicated between frontend and backend.

4. Critical commerce validation must happen on the backend.

5. Production secrets must never be committed to Git.

6. API contracts must be versioned and documented.

7. Database migrations must be tracked in Git.

8. Changes to core architecture must be documented before implementation.

9. New dependencies must have a clear technical purpose.

10. User input must never be trusted without backend validation.

11. Payment calculations must be performed or verified by the backend.

12. Inventory changes must use safe transactional logic.

13. Production readiness requires automated testing.

14. Production readiness requires a security review.

15. Production readiness requires staging validation before deployment.

---

## 13. Development Principles

The project will be built incrementally.

Each major feature should follow this development sequence:

```text
Requirement
    |
    v
Domain Model
    |
    v
Database Model
    |
    v
Backend Business Logic
    |
    v
API
    |
    v
Validation
    |
    v
Automated Tests
    |
    v
Frontend UI
    |
    v
API Integration
    |
    v
QA
```

A feature is not considered complete only because its UI exists.

Its backend behavior, validation, tests, failure states, and security requirements must also be complete.

---

## 14. Planned Business Domains

The platform is expected to contain the following main domains.

### Accounts

- users
- authentication
- roles
- permissions
- customer profiles
- addresses

### Catalog

- products
- categories
- collections
- images
- attributes
- attribute values
- variants

### Inventory

- stock
- availability
- inventory movements

### Cart

- carts
- cart items
- quantity validation

### Orders

- orders
- order items
- order totals
- order statuses
- order history

### Custom Size

- custom size requests
- review workflow
- approval
- rejection
- pricing quote
- preparation estimate

### Payments

- payment attempts
- payment status
- gateway reference
- callback verification

### Shipping

- shipping methods
- shipping costs
- shipping status
- tracking information

### Support

- contact messages
- customer service data

---

## 15. ELASI Product Model Direction

Products may have multiple variants.

Examples:

```text
Ring
`-- Ring Size

Bracelet
`-- Bracelet Length

Necklace
`-- Necklace Length

Anklet
`-- Anklet Length
```

A product variant may have its own:

- SKU
- price
- stock
- status
- attribute values

The product itself must not use a single generic size field for every jewelry type.

The final product and variant model will be designed during the commerce domain modeling phase.

---

## 16. Custom Size Workflow Direction

Custom sizes must not be treated as normal immediately purchasable variants.

Expected workflow:

```text
Customer submits custom size request
              |
              v
Backend validates request
              |
              v
Admin reviews feasibility
              |
       +------+------+
       |             |
       v             v
   Approved       Rejected
       |
       v
Price and preparation time confirmed
       |
       v
Customer receives payment path
       |
       v
Payment
       |
       v
Preparation / fulfillment
```

The detailed implementation will be designed later.

---

## 17. Authentication Direction

Authentication will be owned by Django.

The frontend must not implement an independent authentication authority.

Authentication architecture will be designed before account and admin features are implemented.

Sensitive authentication tokens must not be stored insecurely in browser storage.

Authorization must always be enforced by the backend.

---

## 18. Admin Direction

Django Admin may be used initially for reliable internal management.

Business administration may include:

- products
- categories
- attributes
- variants
- inventory
- customers
- orders
- custom size requests
- payments
- shipping
- contact messages

A custom administration interface may be added later only where product requirements justify it.

---

## 19. Environment Configuration

Secrets and deployment-specific values must be stored outside source code.

Example categories:

```text
Database configuration
Django secret key
Allowed hosts
CORS configuration
API base URL
Payment credentials
Email credentials
Storage credentials
Monitoring credentials
```

Real secrets must never be committed to Git.

Safe variable names and example values belong in:

```text
.env.example
```

---

## 20. Current Phase

Current project phase:

```text
Phase 01 - Repository and architecture foundation
```

The new frontend and backend applications have not yet been initialized.

Current objectives:

1. Establish repository structure.
2. Document architecture.
3. Establish environment configuration conventions.
4. Create the initial Git baseline.

After this phase:

1. Initialize the Next.js frontend.
2. Initialize the Django backend.
3. Configure PostgreSQL.
4. Verify frontend/backend communication.
5. Design the commerce domain model.