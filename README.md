# ELASI

ELASI is a production-oriented luxury jewelry e-commerce platform built as a fully custom application.

The project uses a separated frontend and backend architecture to keep presentation, business logic, security, and data management clearly isolated.

## Technology Stack

### Frontend

- Next.js
- React
- TypeScript

### Backend

- Python
- Django
- Django REST Framework

### Database

- PostgreSQL

## High-Level Architecture

```text
User Browser
     |
     v
Next.js Frontend
     |
     | REST API
     v
Django Backend
     |
     | Django ORM
     v
PostgreSQL
```

Django is the authoritative source of business logic.

Django ORM is the only application layer responsible for managing the PostgreSQL schema.

The frontend must never connect directly to PostgreSQL.

## Project Structure

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
|   |-- api/
|   `-- decisions/
|
|-- .env.example
|-- .gitignore
`-- README.md
```

## Development Services

### Frontend

```text
http://localhost:3000
```

### Backend

```text
http://127.0.0.1:8000
```

### API

```text
http://127.0.0.1:8000/api/v1
```

### PostgreSQL

```text
127.0.0.1:5432
```

## Architecture Responsibilities

### Frontend

The frontend is responsible for:

- user interface
- responsive layouts
- navigation
- product presentation
- user interaction
- frontend form state
- API consumption
- client-side state where appropriate

The frontend must not be treated as the authoritative source for:

- product prices
- inventory
- discounts
- order totals
- permissions
- payment state
- shipping state

### Backend

The backend is responsible for:

- authentication
- authorization
- validation
- business logic
- product management
- category management
- product variants
- inventory
- carts
- orders
- payments
- shipping
- custom size requests
- admin operations
- API security
- data integrity

### Database

PostgreSQL is responsible for persistent application data.

Database access must happen through Django ORM.

## Environment Variables

Environment-specific configuration and secrets must remain outside source code.

The expected variables are documented in:

```text
.env.example
```

Real credentials must never be committed to Git.

Examples of sensitive configuration include:

- database passwords
- Django secret keys
- payment gateway credentials
- email credentials
- storage credentials
- monitoring credentials

## Development Principles

Each major feature should follow this implementation sequence:

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

A feature is not considered complete only because its interface exists.

Backend behavior, validation, security, failure states, and tests must also be completed.

## Documentation

Architecture documentation:

```text
docs/architecture/
```

API documentation:

```text
docs/api/
```

Architecture and engineering decisions:

```text
docs/decisions/
```

## Current Development Phase

```text
Phase 01 - Repository and architecture foundation
```

Current objectives:

1. Establish repository structure.
2. Document system architecture.
3. Establish environment configuration conventions.
4. Create the initial Git baseline.

The frontend and backend applications have not been initialized yet.

## Next Phases

After the repository foundation is complete:

1. Initialize the Next.js frontend.
2. Initialize the Django backend.
3. Configure PostgreSQL.
4. Verify communication between Next.js and Django.
5. Design the commerce domain model.
6. Implement the backend incrementally.
7. Build and integrate the frontend.
8. Add automated testing.
9. Perform security and performance reviews.
10. Deploy to staging before production.

## Production Status

ELASI is currently under active development.

The application is not production-ready until all required implementation, testing, security, deployment, and client acceptance stages are completed.