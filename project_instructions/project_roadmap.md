# Freelance Marketplace System

# Development Roadmap

## Week 1: Project Setup & User Authentication

### Tasks

-   Install Django and MySQL, and set up a Python virtual environment to isolate
    dependencies.
-   Start a new Django project using `django-admin startproject`.
-   Create core apps: `users`, `jobs`, `services`, `orders`, `payments`, and `reviews`.
-   Configure MySQL as the backend database in `settings.py`.
-   Extend Django's default User model using `AbstractUser` to include roles like Admin,
    Client, Freelancer.
-   Implement registration and login forms with role-based redirection after login.
-   Collect additional user info such as bio, profile picture, and set account status to inactive
    until payment.

### Deliverables

-   Django project initialized and connected to MySQL.
-   User model with roles and additional profile info.
-   Working registration and login system.
-   Account activation logic stubbed for payment integration.

## Week 2: Profiles, Dashboards, Job and Service CRUD

### Tasks

-   Create separate dashboards for clients and freelancers with role-based access control.
-   For clients: implement Create, Read, Update, Delete (CRUD) operations for job posts.
-   For freelancers: implement CRUD for service listings including descriptions, price tiers,
    and delivery time.
-   Enable portfolio file uploads with Django’s `FileField` and configure `MEDIA_ROOT`.
-   Use Django generic views or class-based views (CBVs) for code reuse and clarity.

### Deliverables

-   Profile pages accessible and editable by users.
-   Functional CRUD for jobs (client side).
-   Functional CRUD for services (freelancer side).

## Week 3: Proposals and Messaging

### Tasks

-   Create models and forms for freelancers to submit proposals to job posts.
-   Proposals should include message, proposed price, and delivery duration.
-   Clients can view, accept, or reject proposals.
-   Implement a messaging system for client-freelancer communication. Start with basic
    threaded messages.
-   Use polling or Django Channels (if aiming for real-time) to fetch messages asynchronously.

### Deliverables

-   Proposal submission and management system functional.
-   Messaging interface established between clients and freelancers.

## Week 4: Order Management

### Tasks

-   Once a client accepts a proposal, create an `Order` entry linking both users.
-   Define order states: initiated, in progress, delivered, approved.
-   Allow freelancers to upload delivery files.
-   Clients should be able to approve or request revisions.

### Deliverables

-   Order model with life cycle logic.
-   File upload system for deliveries.
-   Client-side order approval and revision workflow.

## Week 5: Reviews and Ratings

### Tasks

-   Allow clients and freelancers to leave reviews once an order is completed.
-   Reviews should include a star rating (1–5) and an optional comment.
-   Calculate average ratings and display them on freelancer profiles.
-   Create views and forms for submitting and displaying reviews.

### Deliverables

-   Review and rating system in place.
-   Ratings displayed on freelancer profile pages.

## Week 6: Payment Integration

### Tasks

-   Integrate AzamPesa API for handling payments (simulate if credentials unavailable).
-   Implement one-time registration fee logic: user becomes active after payment.
-   Implement job payment workflow when a client accepts a freelancer’s proposal.
-   Use Django signals or Celery tasks to confirm and update payment status.

### Deliverables

-   Simulated or actual AzamPesa payment flow implemented.
-   User account activation tied to payment.
-   Payment processing connected to job order creation.

## Week 7: Admin Dashboard

### Tasks

-   Customize Django admin interface to manage users, jobs, services, and payments.
-   Add custom admin actions like banning users or resolving disputes.
-   Add analytics views for platform metrics (e.g., number of jobs posted, active freelancers).

### Deliverables

-   Admin panel configured with enhanced control.
-   Admin-only access enforced.
-   Basic site analytics available to admin.

## Week 8: Testing, Bug Fixes, Deployment

### Tasks

-   Write unit tests for models and views using Django’s test framework.
-   Fix any major bugs or usability issues.
-   Prepare the application for production by updating settings, securing secrets, and
    optimizing static files.
-   Deploy using Gunicorn + Nginx on Ubuntu server.
-   Configure HTTPS, firewall, and secure DB access.

### Deliverables

-   Fully deployed MVP with all core features.
-   Tested and production-ready application.
-   Deployment documentation and security measures in place.
