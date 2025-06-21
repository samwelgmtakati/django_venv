# 📦 App Documentation: Freelance Marketplace System

## 1\. accounts

### 📌 Purpose

Handles **user authentication**, **role management** (Client/Freelancer), **profile creation**, and **dashboard logic**.

### 🔧 Features Handled

-   User Signup/Login/Logout
-   Role selection at signup
-   Profile: Bio, Picture, Skills
-   Account activation status
-   Role-based dashboards

### 📂 Modules

-   models.py: CustomUser, UserProfile
-   views/: Auth views, profile views, dashboard views
-   forms/: Signup/Login/Profile forms
-   signals.py: Auto-create UserProfile on user creation

### 🔁 Dependencies

-   Used by jobs, services, orders, etc. to link users
-   Payment system checks account status before enabling access

## 2\. jobs

### 📌 Purpose

Allows **clients to post jobs**, and **freelancers to apply via proposals**.

### 🔧 Features Handled

-   Job posting, editing, and deleting
-   Proposal submission
-   Proposal review and status change (accept/reject)

### 📂 Modules

-   models.py: Job, Proposal
-   views/: JobList, JobCreate, ProposalSubmit, ProposalReview
-   forms/: JobForm, ProposalForm

### 🔁 Dependencies

-   Requires accounts for user roles
-   Triggers orders app when a proposal is accepted

## 3\. services

### 📌 Purpose

Allows **freelancers to offer predefined services** with pricing tiers and portfolios.

### 🔧 Features Handled

-   Service listing, editing, deleting
-   Portfolio upload (images/docs)

### 📂 Modules

-   models.py: Service, PortfolioItem
-   views/: ServiceList, ServiceCreate, ServiceEdit
-   forms/: ServiceForm, PortfolioForm

### 🔁 Dependencies

-   Freelancer dashboard uses it
-   Ratings from reviews affect freelancer reputation

## 4\. orders

### 📌 Purpose

Manages **accepted proposals** and **service purchases**, tracks **work delivery lifecycle**.

### 🔧 Features Handled

-   Order creation after proposal acceptance
-   Order status: Initiated → In Progress → Delivered → Approved
-   File delivery and revision requests

### 📂 Modules

-   models.py: Order, OrderFile, OrderRevision
-   views/: OrderDetail, UploadWork, RequestRevision, ApproveOrder

### 🔁 Dependencies

-   Created by jobs or services
-   Interacts with payments, reviews, messaging

## 5\. reviews

### 📌 Purpose

Allows **clients to rate and review freelancers** after order completion.

### 🔧 Features Handled

-   Submit review after order
-   Show average rating on freelancer profiles
-   1-5 star system + text

### 📂 Modules

-   models.py: Review
-   views/: SubmitReview, FreelancerRatings
-   forms/: ReviewForm

### 🔁 Dependencies

-   Depends on orders for completion status
-   Affects accounts.UserProfile (avg. rating field)

## 6\. payments

### 📌 Purpose

Handles **AzamPesa-based payments** for:

-   Account activation
-   Order payments

### 🔧 Features Handled

-   Payment initiation and confirmation
-   Logs and security
-   AzamPesa API integration

### 📂 Modules

-   models.py: PaymentTransaction, AccountActivation
-   views/: ProcessPayment, ConfirmPayment
-   utils/: AzamPesa API client

### 🔁 Dependencies

-   Validates accounts (activation)
-   Ties into orders for payment before progress

## 7\. messaging

### 📌 Purpose

Supports **messaging between clients and freelancers** — per job/service/order.

### 🔧 Features Handled

-   Chat threads scoped to jobs or orders
-   Real-time messaging support (optional: Django Channels)

### 📂 Modules

-   models.py: MessageThread, Message
-   views/: SendMessage, ViewThread
-   consumers.py (if using Channels)

### 🔁 Dependencies

-   Connects users from accounts
-   Threads may be job-, order-, or service-specific

## 8\. dashboard (Optional UI Routing App)

### 📌 Purpose

Serves as a **frontend UI dispatcher**:

-   Renders dashboards
-   Redirects users based on role
-   Pulls stats from other apps

### 🔧 Features Handled

-   User-specific dashboards
-   Overview of jobs, services, orders, earnings, ratings

### 📂 Modules

-   views.py: ClientDashboard, FreelancerDashboard
-   Template includes: Orders, Stats, Notifications

### 🔁 Dependencies

-   Aggregates data from all core apps

## 9\. core

### 📌 Purpose

Houses **shared functionality** and **system-wide configs**.

### 🔧 Features Handled

-   Custom admin classes
-   Signal handlers
-   Utilities/helpers
-   Central constants and enums

### 📂 Modules

-   admin.py: Custom dashboard
-   utils.py: File validators, global choices
-   signals.py: Centralized signals (optional)

### 🔁 Dependencies

-   Used by all other apps indirectly
