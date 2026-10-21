# Warehouse Capacity Planner (Flask + MySQL)

## Struktur
```
warehouse_planner/
├── app.py            # Entry point (application factory)
├── config.py         # Konfigurasi (DB URI, secret key, upload folder)
├── database.py       # Instance SQLAlchemy + connection pool
├── models/           # Model ORM (master_sku, inbound_history, inbound_detail)
├── routes/           # Blueprint endpoint (tipis, hanya HTTP)
├── services/         # Logika bisnis
├── templates/        # HTML (Jinja2)
├── static/           # CSS / JS
├── uploads/          # Penyimpanan sementara file upload
└── sql/              # Script DDL
```

## Menjalankan
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # lalu isi kredensial DB
mysql -u root -p < sql/db_whs_planner.sql            # buat DB, tabel, dan seed data
python app.py
```

## Uji
- `GET http://localhost:5000/api/healthcheck` -> `{"status":"ok","database":"connected"}`
- `GET http://localhost:5000/api/sku` -> daftar Master SKU
- `GET http://localhost:5000/api/sku?q=matcha&limit=5`

## API Master SKU (Fase 3)
```bash
curl "localhost:5000/api/sku?q=matcha"
curl -X POST localhost:5000/api/sku -H "Content-Type: application/json" \
     -d '{"item_id":"ITEM020","description":"TEST ITEM","cpp":40}'
curl -X PUT localhost:5000/api/sku/ITEM020 -H "Content-Type: application/json" \
     -d '{"description":"TEST ITEM V2","cpp":48}'
curl -X POST localhost:5000/api/sku/upload -F "file=@master_sku.xlsx"
```
Unit test (tanpa database): `python -m unittest discover -s tests -v`
