# Astra Library Management System

A complete Django 6 library management application with member accounts, role-aware dashboards, book CRUD, search, borrowing, fines, requests, notifications, legal eBook lookup links, sample data, and optional Docker/PostgreSQL support.

## Features

- Authentication: registration, login, logout, password reset templates, session-based access.
- Roles: Admin, Librarian, Member via `accounts.Profile`.
- Catalog: A-Z classification, genre filters, cover uploads, stock tracking, admin customization.
- Circulation: issue, return, due dates, borrowing history, duplicate active checkout prevention.
- Fines: automatic overdue-day calculation using `LIBRARY_FINE_RATE_PER_DAY`.
- Requests: members request unavailable or missing books; staff approve or reject; users receive notifications.
- Recommendations: rule-based suggestions from borrowing genres plus popular books.
- eBooks: legal-safe links to Open Library, Project Gutenberg, Internet Archive, WorldCat, or a configured provider URL.
- Dashboards: interactive member dashboard and operations dashboard with a canvas analytics chart.
- API: lightweight JSON endpoints at `/api/books/`, `/api/books/<id>/`, and `/dashboard/api/analytics/`.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_library
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Sample Accounts

| Role | Username | Password |
| --- | --- | --- |
| Admin | `admin` | `AdminPass123!` |
| Librarian | `librarian` | `LibraryPass123!` |
| Member | `maya` | `MemberPass123!` |

## PostgreSQL

Set `DATABASE_URL` to a PostgreSQL URL:

```bash
DATABASE_URL=postgres://library:library@localhost:5432/library
```

The settings parser supports SQLite and PostgreSQL URLs without requiring `dj-database-url`.

## Docker

```bash
docker compose up --build
```

The compose stack starts PostgreSQL, applies migrations, seeds the library, and runs Django on `http://127.0.0.1:8000/`.

## Useful Commands

```bash
python manage.py check
python manage.py test
python manage.py seed_library
python manage.py createsuperuser
python manage.py collectstatic
```

## Project Structure

```text
accounts/      user profiles, roles, registration, permissions
catalog/       books, catalog CRUD, search, eBook links, seed command
circulation/   borrowing, returns, fines, requests, notifications
dashboards/    member and admin dashboards plus analytics JSON
templates/     responsive Django templates
static/        custom CSS and JavaScript
media/         uploaded/generated covers in development
```
