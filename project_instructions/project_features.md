# Freelance Marketplace System –

## Features Breakdown

This document outlines the key features of the Freelance Marketplace System for better
planning, task allocation, and milestone tracking. Each feature represents a core part of the
system, designed to be developed, tested, and integrated in a modular fashion by the project
team.

## 1. User Authentication & Role Management

-   -   Signup with email and password
-   -   Login and logout functionality
-   -   Role selection during registration: Client or Freelancer
-   -   Profile info: bio, profile picture, skills
-   -   Account status toggle (inactive until payment confirmed)
-   -   Optional: Google login integration

## 2. User Profiles & Dashboards

-   -   User-specific dashboard based on role
-   -   Profile view and edit functionality
-   -   Client: see jobs posted, orders made
-   -   Freelancer: see services, orders received

## 3. Job Posting System (Client)

-   -   Clients can post new jobs with detailed fields
-   -   Edit and delete their jobs
-   -   Track jobs posted and view freelancer proposals

## 4. Service Listing (Freelancer)

-   -   Freelancers can list services with title, description, price tiers
-   -   Upload portfolio items (images/docs)
-   -   Edit and manage their service listings

## 5. Proposal & Bidding System

-   -   Freelancers apply to jobs via proposals
-   -   Proposal includes message, price, and duration

-   -   Clients can view, accept, or reject proposals
-   -   Proposal status management

## 6. Messaging System

-   -   Threaded messaging per job/service
-   -   Basic chat functionality between client and freelancer
-   -   Optional: Real-time using Django Channels

## 7. Order Management System

### Order Creation & Workflow
- **Automated Order Creation**
  - Order is automatically generated when a proposal is accepted
  - Clear summary of terms, deliverables, and timeline
  - Secure escrow payment system for fund holding

### Order Lifecycle
1. **Initiated** 
   - Order is created with all agreed terms
   - Client funds are secured in escrow
   - Both parties receive confirmation and order details

2. **In Progress**
   - Freelancer can update progress with milestones
   - Automatic reminders for upcoming deadlines
   - Built-in time tracking (optional)

3. **Delivery**
   - Secure file upload system for deliverables
   - Version control for multiple submissions
   - Delivery checklist to ensure all requirements are met

4. **Review & Approval**
   - Client has X days to review work
   - Request revisions with specific feedback
   - Accept delivery and release payment

### Key Features
- **Revision Management**
  - Structured revision requests
  - Clear revision history and tracking
  - Limit on number of included revisions

- **Payment Protection**
  - Escrow system for security
  - Milestone-based payments for larger projects
  - Clear refund policy and dispute resolution

- **Communication & Updates**
  - Dedicated order communication channel
  - Automated status updates
  - Activity log for transparency

- **Delivery & Approval**
  - Digital signature for acceptance
  - Rating and review system
  - Downloadable invoice and receipt

### User Experience
- Intuitive dashboard for order tracking
- Email/SMS notifications for important updates
- Mobile-responsive interface
- Help center and support access

## 8. Reviews & Ratings

-   -   Rating and review system after order completion
-   -   1 - 5 star rating + text comment
-   -   Average ratings shown on freelancer profiles

## 9. Payment System

### 9.1 Payment Processing

- **AzamPesa Integration**
  - One-time account activation fee (TZS 5,000)
  - Secure order payments processing
  - Support for partial payments and installments
  - Automatic currency conversion with TZS as default
  - Payment method management (AzamPesa, mobile money, bank transfer)

### 9.2 Payment Tracking & Security

- Real-time payment status updates
- Detailed transaction history with timestamps
- Secure payment logs with IP tracking
- Failed payment handling and retry mechanisms
- Automatic receipt generation (PDF/email)

### 9.4 Financial Reporting

- Earnings dashboard for freelancers
- Expense tracking for clients
- Tax documentation (TRA compliant)
- Transaction export (CSV/Excel)
- Monthly/quarterly financial summaries


### 9.6 Notifications

- Payment confirmation alerts
- Invoice generation and delivery
- Payment reminder system
- Low balance alerts for clients
- Payout notifications for freelancers

## 10. Admin Panel

-   -   Custom admin dashboard
-   -   User, job, service, and order management
-   -   Dispute resolution and analytics views

## 11. Deployment & Environment

-   -   Ubuntu server setup with Gunicorn + Nginx
-   -   Configure HTTPS and static/media file handling
-   -   Production-ready MySQL DB configuration
-   -   Basic monitoring and backup strategy

## 12. Testing & Debugging

-   -   Unit tests for models and views
-   -   Manual and automated testing for major workflows
-   -   Bug tracking and fixing sessions before deployment
