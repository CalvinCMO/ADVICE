# ADVICE — Django-Only Web Platform

> Digital Counseling & Wellness Platform for Universities  
> Built with Django 4.2, SQLite (dev) / PostgreSQL (prod), Tailwind CSS CDN

---

## 🚀 Quick Start (5 minutes)

### 1. Create virtual environment & install
```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Apply migrations
```bash
python manage.py migrate
```

### 3. Seed demo data (institutions, users, sessions, wellness checks)
```bash
python manage.py setup_advice
```

### 4. Run the server
```bash
python manage.py runserver
```

### 5. Visit http://127.0.0.1:8000/

---

## 🔑 Demo Login Credentials

| Role | Email | Password |
|---|---|---|
| Student | student@demo.edu | Demo1234! |
| Counselor | counselor@demo.edu | Demo1234! |
| Institution Admin | admin@demo.edu | Demo1234! |
| Super Admin | super@advice.com | Demo1234! |

---

## 🏗 Project Structure

```
advice_platform/
├── manage.py
├── requirements.txt
├── advice_project/
│   ├── settings.py          # All configuration (env-driven)
│   ├── urls.py              # Root URL routing
│   └── wsgi.py
│
├── apps/
│   ├── accounts/            # User model, auth, RBAC, invitations
│   │   ├── models.py        # Custom User (email auth, roles, lockout)
│   │   ├── views.py         # Login, register, profile, admin views
│   │   ├── forms.py         # Login, register, profile forms
│   │   ├── backends.py      # Email authentication backend
│   │   ├── middleware.py    # Last-activity tracking
│   │   └── urls.py
│   │
│   ├── institutions/        # Institution management
│   │   ├── models.py        # Institution model
│   │   ├── views.py         # Home, about, contact, institution pages
│   │   ├── urls.py
│   │   └── management/commands/setup_advice.py   # Demo data seeder
│   │
│   ├── counseling/          # Session scheduling & management
│   │   ├── models.py        # CounselingSession, GroupSession, Feedback, Availability
│   │   ├── views.py         # Book, start, complete, cancel, reschedule, group sessions
│   │   └── urls.py
│   │
│   ├── messaging/           # Messaging & notifications
│   │   ├── models.py        # Conversation, Message, Notification
│   │   ├── views.py         # Conversations, messages, notifications
│   │   └── urls.py
│   │
│   ├── progress/            # Wellness & progress tracking
│   │   ├── models.py        # WellnessCheck, ProgressGoal, CrisisAlert, ProgressReport
│   │   ├── views.py         # Wellness check-in, goals, analytics, crisis alerts
│   │   └── urls.py
│   │
│   └── payments/            # Billing & subscriptions
│       ├── models.py        # SubscriptionPlan, InstitutionSubscription, PaymentRecord
│       ├── views.py         # Billing page, plans page
│       └── urls.py
│
└── templates/
    ├── base.html            # Full sidebar + public nav layout
    ├── home.html            # Public landing page
    ├── about.html           # About page
    ├── contact.html         # Contact form
    ├── privacy.html         # Privacy policy
    ├── terms.html           # Terms of service
    ├── 404.html             # Error page
    ├── accounts/            # Login, register, profile, password reset
    ├── dashboard/           # Student & counselor dashboards
    ├── counseling/          # Session booking, detail, group sessions, counselors
    ├── messaging/           # Conversations, messages, notifications
    ├── progress/            # Wellness, goals, analytics, crisis alerts
    ├── payments/            # Billing, plans
    └── admin/               # Institution dashboard, manage users, invitations
```

---

## 👤 User Roles & Access

| Role | Access |
|---|---|
| **Super Admin** | Platform-wide overview, all institutions, Django admin |
| **Institution Admin** | Manage users, invitations, analytics, billing for their institution |
| **Counselor** | Sessions, student goals, crisis alerts, analytics, group sessions |
| **Student** | Book sessions, wellness check-ins, goals, messaging, group sessions |

---

## 🔑 Key Features

### Authentication
- Email-based login (no username)
- Brute-force protection: 5 failed logins → 1-hour lockout
- Password reset via email
- Invitation code system for controlled registration

### Sessions
- Book individual and crisis sessions with any verified counselor
- Start / complete / cancel / reschedule sessions
- Counselor notes (private) + summary (shared with student)
- Pre/post session mood tracking
- Student feedback with star rating

### Wellness Tracking
- Daily check-in: mood, anxiety, sleep, energy, stress, social connection
- Auto-calculated overall wellness score (1–10)
- Auto-flagging of distress scores → crisis alert
- 14-day visual trend chart

### Goals
- Collaborative goal creation (counselor or student)
- 11 categories (anxiety, stress, academic, career, etc.)
- Progress slider + counselor notes + student reflection
- Milestone tracking via JSON field

### Crisis Alerts
- Auto-generated when wellness scores are critically low
- Severity levels: Low / Medium / High / Critical
- Counselor can review, message student, book session, or resolve

### Messaging
- Private conversations between students and counselors
- Real-time-style chat (form-based, no WebSocket needed)
- In-app notifications for sessions, messages, goals, crisis alerts

### Analytics
- Institution-wide: sessions, completion rates, avg wellness, flagged checks
- 30-day wellness trend chart (bar chart via HTML/CSS)
- Crisis alert count, open alerts

### Admin Panel
- Institution Admin: manage users, send invitations, view billing
- Super Admin: platform overview, all institutions
- Django Admin: full CRUD for all models

---

## 🗄 Database

**Development**: SQLite (zero config, `db.sqlite3`)  
**Production**: Set `DATABASE_URL` or configure `DATABASES` in `settings.py` for PostgreSQL

```bash
# Switch to PostgreSQL:
pip install psycopg2-binary
# Then update DATABASES in settings.py
```

---

## 🌐 Environment Variables (Production)

Create a `.env` file:

```env
SECRET_KEY=your-50-char-random-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# PostgreSQL
DB_NAME=advice_db
DB_USER=advice_user
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# Email (SendGrid or SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

BASE_DOMAIN=yourdomain.com
```

---

## 🚢 Production Deployment

```bash
# 1. Set environment variables
# 2. Switch to PostgreSQL
# 3. Collect static files
python manage.py collectstatic --noinput

# 4. Apply migrations
python manage.py migrate

# 5. Seed data
python manage.py setup_advice

# 6. Run with Gunicorn
gunicorn advice_project.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

Use **Nginx** as a reverse proxy in front of Gunicorn.

---

## 🔄 Reset Demo Data

```bash
python manage.py setup_advice --reset
```

This deletes all data and re-seeds fresh demo content.

---

## 📧 Email in Development

By default, emails print to the **console** (no SMTP needed).  
Check your terminal after registering or requesting a password reset.

---

## License

Proprietary — ADVICE Platform. All rights reserved.
