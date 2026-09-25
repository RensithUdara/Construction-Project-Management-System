# Construction Project Management System

A Django web application for learning advanced project, cost, procurement, document, workflow, and reporting patterns in a construction-management domain.

## Included Modules

- Organizations, departments, profiles, roles
- Projects, project teams, contracts
- BOQ sections/items with calculated amounts and progress
- Budget vs actual tracking
- Materials, stock movements, purchase requests, purchase orders
- Schedule activities and daily site reports
- RFIs, variations, EOT applications, payment certificates, invoices
- Documents, risks, safety incidents, defects, tasks, approvals
- Django admin plus a custom dashboard and searchable module screens
- DRF API under `/api/`

## Run Locally

```powershell
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

Demo logins:

- `admin` / `admin123`
- `pm` / `pm123`

## Useful Commands

```powershell
python manage.py test
python manage.py createsuperuser
python manage.py makemigrations
```

The project uses SQLite for the learning build. PostgreSQL, Celery, Redis, email notifications, and object storage are natural next upgrades.
