# Freelance Market

A Django-based freelance marketplace platform.

## Features

- User authentication (Freelancers and Clients)
- Job posting and bidding system
- Proposal management
- Real-time messaging
- Payment integration (TZS)

## Local Development

### Prerequisites

- Python 3.8+
- PostgreSQL (for production)
- Git

### Setup

1. Clone the repository:
   ```bash
   git clone <your-repository-url>
   cd freelance_market
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:

   ```bash
   cp .env.example .env
   ```

   Then edit `.env` with your configuration.

5. Run migrations:

   ```bash
   python manage.py migrate
   ```

6. Create a superuser:

   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:

   ```bash
   python manage.py runserver
   ```

## Deployment to Render

1. Push your code to a Git repository (GitHub, GitLab, or Bitbucket).

2. Sign up or log in to [Render](https://render.com/).

3. Click "New" and select "Blueprint".

4. Connect your repository and select the branch to deploy.

5. Render will automatically detect the `render.yaml` file and configure your services.

6. After deployment, set up any required environment variables in the Render dashboard.

## Environment Variables

Create a `.env` file with the following variables:

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=.onrender.com,localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/yourdbname

# Email (for production)
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=your-email@example.com
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
