# SL APEX RIDER - Smart Motorcycle Spare Parts and Predictive Maintenance Management System
MGT/2022/450 - WWUD Pemarathne - Rajarata University of Sri Lanka

## Tech (per proposal)
HTML, CSS, JavaScript, Bootstrap 5, Python Django, MySQL (XAMPP), Chart.js, VS Code, Git

## Quick Run (current: SQLite dev)
```
cd C:\Users\ujith\Desktop\SL_APEX_RIDER
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Open: http://127.0.0.1:8000/

All pages now require login (see "Authentication" below) — sign in with the
superuser you created, or run `python manage.py shell < seed_test.py` for a
ready-made `staff / pass12345` account plus sample data.

Pages:
- / = Dashboard (low stock + predictive alerts + recent sales)
/customers/ Week 7-8, /bikes/ Week 7-8 with compatibility + predictions,
/parts/ Week 9-10 with ?q=&bike=FZ filter, /sales/ Week 9-10,
/service/ Week 11, /service/alerts/ Week 14-15

## Authentication
Every page (dashboard, customers, bikes, parts, sales, service) requires a
logged-in user — `/accounts/login/` and `/accounts/logout/` use Django's
built-in auth views. Create an account with `python manage.py createsuperuser`,
or use the `staff / pass12345` account created by `seed_test.py`.

## Configuration (.env)
`SECRET_KEY` and `DEBUG` are no longer hardcoded in `config/settings.py`.
Copy `.env.example` to `.env` and fill in real values before deploying;
`.env` is gitignored so secrets never get committed. `python-dotenv` loads it
automatically.

## Switch to MySQL (XAMPP) for final submission
1. Install full XAMPP, start MySQL, create DB `slapexrider_db` in phpMyAdmin
2. In config/settings.py uncomment MySQL DATABASES block, comment SQLite block
3. `pip install pymysql`, `python manage.py migrate`

## Smart Features (Objective 4)
- Compatibility: SparePart.compatible_models icontains bike.model, shown in bike detail + parts filter
- Predictive: maintenance.models.MAINTENANCE_RULES (Oil 2500, Air Filter 6000, Plug 8000, Brake 8000, Chain 12000) + 500km early warning via generate_predictions()

## Appendix mapping
Week 7-8 customers/motorcycles DONE, 9-10 inventory/sales DONE, 11 service DONE, 12-13 compatibility DONE, 14-15 predictive DONE, 16 dashboard DONE, 17-18 test with `seed_test.py` and `python manage.py test` (22 automated tests covering models + auth-gating + sale stock/transaction logic).
