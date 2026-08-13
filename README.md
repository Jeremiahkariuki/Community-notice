# CommuNotice

A community notice board built with **Django 6.1** — a styled landing page, user
registration & login, and a notice board where members can post announcements,
alerts, and events **with a photo**, browse them by category, and open any
notice for full details.

## Features
- **Landing page** — hero section, live preview of the 3 latest notices, feature
  highlights, community stats, "how it works", about & contact sections
- **Accounts** — sign up (`/accounts/register/`), log in, log out, all
  session-based via Django's built-in auth
- **Notices with photos** — `Notice` model has an `ImageField`; the post form
  accepts an optional photo (`enctype="multipart/form-data"`), shown as a
  thumbnail on the list and full-width on the detail page
- **Categories** — filterable notice list, seeded with starter categories
- Login-protected "post a notice" page (`@login_required`)
- Pagination on the notice list
- Custom CSS (no framework) matching a green, card-based visual style
- Django admin panel for managing categories, notices, and users

## Run it locally

```bash
cd communotice-project
python3 -m venv venv
source venv/bin/activate      # venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_categories   # creates a starter set of categories
python manage.py createsuperuser   # optional, for /admin/

python manage.py runserver
```

Visit:
- `http://127.0.0.1:8000/` — landing page
- `http://127.0.0.1:8000/accounts/register/` — create an account
- `http://127.0.0.1:8000/notices/` — browse notices
- `http://127.0.0.1:8000/notices/new/` — post a notice (photo optional, must be logged in)
- `http://127.0.0.1:8000/admin/` — admin panel (superuser only)

Uploaded photos are saved under `media/` and served automatically while
`DEBUG = True`.

## Run the tests

```bash
python manage.py test
```

## Project structure

```
communotice/                Django project config (settings, urls, wsgi/asgi)
notices/                    App: models, views, forms, admin, templates
notices/templates/notices/  home, notice_list, notice_detail, notice_form, base
notices/templates/registration/  login.html, register.html
notices/management/commands/seed_categories.py
static/css/                 Site stylesheet (single file, no framework)
media/                      User-uploaded notice photos (created at runtime)
manage.py
requirements.txt
```

## Notes for production
- Set `DEBUG = False` and a real `SECRET_KEY` via environment variable
- Set `ALLOWED_HOSTS` to your real domain(s)
- Serve `media/` and `staticfiles/` (after `python manage.py collectstatic`)
  from your web server or a storage service — Django does not serve them
  itself outside of `DEBUG`
