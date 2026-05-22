# VyaparLens

Smart Billing, Inventory & Profit Tracking for Clothing Stores.

VyaparLens is a Flask and SQLite merchant web app for Indian clothing stores. It includes merchant login, product variants, inventory, billing, receipts, udhar tracking, reports, and rule-based analytics.

## Setup

```powershell
cd "D:\MerchantApp"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Open:

```text
http://127.0.0.1:5000
```

## Demo Login

Email:

```text
guru@example.com
```

Password:

```text
123456
```

Demo shop:

```text
Guru Fashion
Main Road, Nashik
```

## Implemented Features

- Merchant signup and login with Werkzeug password hashing.
- 7-day permanent Flask session after login.
- Demo merchant and demo Bhugoal Shirt product seeded on first run.
- Product entry with size and colour variants.
- Equal, recommended, and manual quantity distribution.
- Inventory search, filters, stock updates, low stock flags, and internal details.
- Billing cart with product search, variant selection, stock checks, discounts, and payment modes.
- Cash, UPI, Card, Mixed, Udhar, and Partial Payment tracking.
- Short receipt with print and text download actions.
- Stock deduction at bill creation.
- Udhar customer creation, credit transactions, and payment collection.
- Dashboard stats, payment summary, recent bills, low stock alerts, and rule-based insights.
- Reports with Chart.js charts and tables for sales, profit, payment modes, top products, variants, margins, stock, and udhar.
- Settings page for merchant and receipt footer details.

## Notes

- SQLite database is created at `instance\merchantapp.db` on first run.
- This MVP does not integrate AI. All insights and reports are calculated with backend rules.
- For production, replace the default `SECRET_KEY`, add HTTPS, database backups, and stronger operational monitoring.
