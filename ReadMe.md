# Backend Project I – FastAPI Production-Ready Backend

A production-style backend system built with FastAPI, designed to demonstrate real-world backend engineering practices including authentication, email workflows, background workers, rate limiting, inventory tracking, environment-safe configuration, and secure local sharing.

This project intentionally goes beyond CRUD to showcase architecture, scalability, security, and operational readiness expected in professional backend systems.

---

##  Key Features

###  Authentication & Security
- JWT-based authentication (Access & Refresh tokens)
- Secure password hashing
- Email confirmation flow
- Password reset flow
- Role-based access handling
- Protected sensitive endpoints

###  Email System
- SMTP-based email sending (Gmail / configurable)
- HTML email templates
- Email confirmation links
- Password reset links
- Email sending executed asynchronously via background jobs

###  Background Workers & Jobs
- Database-backed job queue
- Long-running worker loop
- Retry logic with attempts and max_attempts
- Supported job types:
  - Email sending
  - Product publishing
- Fault-tolerant design (job failures do not crash the system)

###  Inventory & Products
- Product management with categories, pricing, and images
- Inventory tracking using stock_quantity
- Automatic stock availability logic:
  - stock_quantity == 0 → in_stock = false
- Designed to support future order and sales flows
- Inventory movement model ready for in/out operations

###  Clean Update Logic
- Safe partial updates using Pydantic v2 model_dump(exclude_unset=True)
- Prevents accidental overwriting of existing data during PATCH operations

###  Rate Limiting (SlowAPI)
- Per-endpoint rate limits
- Custom 429 Too Many Requests responses
- Protection against brute-force and abuse
- Clean separation of limiter logic to avoid circular imports

###  Environment Configuration (Pydantic v2)
- Uses pydantic_settings
- Supports multiple .env files (dev / staging / demo / prod)
- Explicit env file loading
- Secrets never hard-coded in source code
- .env files protected via .gitignore

###  Ngrok Support (Secure Local Sharing)
- Securely expose local FastAPI server using ngrok
- Suitable for demos, testing, and stakeholder reviews
- Can be combined with rate limiting and API key protection

###  Architecture & Code Quality
- Modular project structure
- Clear separation of concerns:
  - routers
  - services
  - models
  - workers
  - core utilities
- No circular imports
- Async-safe design
- Production-oriented error handling

---

##  Project Structure

    src/app/
    ├── main.py              # FastAPI application entrypoint
    ├── core/
    │   ├── config.py        # Pydantic v2 configuration
    │   ├── rate_limit.py    # SlowAPI limiter setup
    │   ├── globals.py       # Context-local globals
    │   └── middleware.py
    ├── views/
    │   ├── auth.py
    │   ├── products.py
    │   └── inventory.py
    ├── workers/
    │   └── jobs.py          # Background worker loop
    ├── models/              # SQLAlchemy models
    ├── schemas/             # Pydantic schemas
    ├── services/            # Business logic layer
    ├── .env.dev             # Development environment variables
    ├── .env.staging         # Staging environment variables
    └── .env.example         # Public environment template

---

##  Setup & Installation

1. Clone the repository

    git clone <your-repository-url>  
    cd Backend Project I

2. Create and activate virtual environment

    python -m venv .venv  
    source .venv/bin/activate

3. Install dependencies

    pip install -r requirements.txt

4. Create environment configuration

    cp src/app/.env.example src/app/.env.dev

Fill in all required values (SMTP credentials, secrets, etc.).

---

## ️ Running the Application

    uvicorn src.app.main:app --reload

Access:
- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

---

##  Share Locally Using Ngrok

    ngrok http 8000

Example public URL:

    https://xxxx.ngrok-free.app

---

##  Rate Limiting Example

Example login endpoint protected with rate limiting:

    @router.post("/login")
    @limiter.limit("5/minute")
    def login(request: Request, ...):
        ...

Custom 429 response format:

    {
      "detail": "Too many requests. Please try again later."
    }

---

##  Email Confirmation Flow

Email confirmation endpoints return styled HTML pages instead of JSON, providing a professional browser-based confirmation experience without requiring a frontend application.

---

##  Designed for Extension

This backend is intentionally designed to support:
- Orders and payments
- Inventory movement logs
- Admin dashboards
- Frontend integration
- Message queues (Redis / RabbitMQ)
- Observability and logging

---

##  Why This Project Matters

This project demonstrates:
- Real backend engineering decision-making
- Production-level architectural patterns
- Security-first thinking
- Async and concurrency safety
- Clean, maintainable code structure
- Practical system design beyond tutorials

This is a backend engineering portfolio project, not a demo-only application.

---

##  Author

Mahmoud Seddik  

