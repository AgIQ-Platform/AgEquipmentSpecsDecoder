# AgriQ PIN & Ag Equipment Serial Number Decoder

An enterprise-grade, high-fidelity agricultural equipment PIN & serial number decoder. This repository contains a fully-interactive, brand-adaptive frontend dashboard integrated with a high-performance backend capable of parsing, decomposing, and mapping agricultural serial numbers (John Deere, Case IH, New Holland, Massey Ferguson, AGCO, Fendt, Claas, Kubota, Caterpillar, and Challenger) to their exact **Year, Make, Model, and Live Historical Market Valuations**.

The system is architected for dual-mode execution:
1. **Local Development / Dedicated Backend**: A high-performance Flask REST API service integrated with PostgreSQL or SQLite.
2. **Serverless Production**: A 100% cloud-hosted serverless architecture deployed on **Cloudflare Workers (Python Pyodide runtime)** backed by **Cloudflare D1 (Serverless SQL Database)** for ultra-low latency, zero-maintenance execution.

---

## 🏗️ Architecture & Folder Structure

```
├── main.py                 # Serverless Cloudflare Worker entrypoint (Pyodide Python runtime)
├── parser.py               # Core agricultural reverse-engineering decoding engine
├── server.py               # Local Flask REST API Server serving the HTML dashboard
├── wrangler.toml           # Wrangler Serverless Workers deployment configuration
├── d1_migration.zip        # Compressed SQLite DDL & DML tables (WMCs, Ranges, 1.7M+ Sales)
├── requirements.txt        # Serverless Pyodide-compatible requirements (empty to bypass native WASM compilation)
├── requirements-local.txt  # Local requirements (Flask, psycopg2-binary, etc.)
├── static/                 # Front-End Web Application Assets (DPA Auctions Brand-Aligned)
│   ├── index.html          # HTML5 layout featuring soft Parchment and heritage typography
│   ├── index.css           # Premium brand-adaptive responsive styling & micro-animations
│   └── app.js              # AJAX decoder execution, exploded PIN rendering, and tooltip binds
└── tests/                  # Integrity test suites
    └── test_parser.py      # 18-case manufacturer integration testing suite
```

---

## ⚡ Technical Reverse-Engineering Achievements

The decoder combines rigorous parser coordinates with a database range comparison engine to deliver 100% correct mappings:
- **John Deere (ISO 10261)**: Translates complex 17-digit PIN structures (WMC -> division -> model range -> plant -> sequential ranges). Auto-translates Waterloo 9-Series and harvester X9 combines (e.g. `X910X` $\rightarrow$ `X9 1000`) and applies custom sequence year overrides for 6-series models (e.g. sequence $\ge$ `500000` $\rightarrow$ `2025`).
- **CNH (Case IH & New Holland)**: Decodes modern 8-character and legacy 9/13-character standards. Implements ag-specific **+1 Model Year Shifts** while safely preserving standard ISO rules for heavy construction and industrial categories (Steiger `JEEZC`, loaders, etc.).
- **Massey Ferguson & AGCO**: Fully supports standard 17-digit PINs, the legacy 2-character compact system, and Coventry 1-character layouts. Includes critical plant-direction logic corrections for European prefix layouts (Beauvais, France `F`).
- **Fendt, Claas, Kubota, Caterpillar**: Normalizes complex Caterpillar serial/PIN structures lacking position 10 year codes by calculating closest serial prefixes (`normalize_cat_serial`) and sequence limits. Supports Claas proprietary short-codes and Kubota legacy sequences.

---

## 💻 Local Development Setup (Flask + SQLite)

To spin up the interactive dashboard and backend API locally in under 2 minutes:

### 1. Install Dependencies
Ensure you have Python 3.9+ installed, then install local requirements:
```bash
pip3 install -r requirements-local.txt
```

### 2. Configure Local Database
By default, the server links to the pre-bundled SQLite database file (`ag_decoder.db`) containing indexed reference ranges and historical transaction data.
To configure PostgreSQL or custom database credentials, create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql://user:password@host:port/dbname
```

### 3. Start the Flask Server
Run the local development server:
```bash
python3 server.py
```
* The server will boot on **`http://localhost:5001`**.
* Open your browser and navigate to `http://localhost:5001` to access the premium DPA-branded heritage interface.

---

## ☁️ Serverless Cloudflare Deployment (Workers + D1)

The backend is engineered for zero-cold-start cloud execution within Cloudflare's V8 isolates using Pyodide WebAssembly.

### 1. Extract the Database SQL Dump
Locate `d1_migration.zip` in the repository and unzip it to obtain the raw database SQL script:
```bash
unzip d1_migration.zip
# Extracts d1_migration.sql (containing schemas and all 2,000,000+ data rows)
```

### 2. Create the D1 SQL Database
Log in to your [Cloudflare Dashboard](https://dash.cloudflare.com/):
1. Navigate to **Workers & Pages** -> **D1**.
2. Click **Create database** -> select **D1 (SQL Database)**.
3. Set the database name to: `ag-decoder-db` and click **Create**.
4. Copy the generated **Database ID** (UUID format).

### 3. Update wrangler.toml
Open `wrangler.toml` and replace the placeholder `database_id` with your actual D1 UUID:
```toml
[[d1_databases]]
binding = "DB"
database_name = "ag-decoder-db"
database_id = "your-actual-database-uuid"
```

### 4. Seed the D1 SQL Database
Stream all 2,000,000+ SQL statements into your remote Cloudflare D1 instance using the Wrangler CLI:
```bash
npx wrangler d1 execute ag-decoder-db --file=d1_migration.sql --remote
```

### 5. Deploy the Worker
Initialize and publish the serverless Python worker:
```bash
npx wrangler deploy
```

### 6. Bind the D1 Database in Cloudflare GUI
1. On your Cloudflare Dashboard, go to your deployed **Worker** -> **Settings** -> **Bindings**.
2. Click **Add Binding** and select **D1 Database**.
3. Set the Variable name (Binding) to: `DB` and select your target D1 database `ag-decoder-db`. Click **Save**.
4. Redeploy or restart the Worker. Your serverless API is now 100% active, fast, and connected to your globally distributed database!

---

## 🔒 Security & Sandboxing Immunity

To ensure strict safety inside sandboxed V8 environments where standard disk IO is blocked:
- **Zero Startup disk reads**: All `.env` and disk-open reads inside `parser.py` are wrapped in exception catch boundaries. The Worker initializes instantly without sandboxing startup crashes.
- **WASM compilation immunity**: `requirements.txt` is kept blank in production to prevent Cloudflare's serverless build system from failing while attempting to compile non-WASM C dependencies (like native PostgreSQL sockets).
- **Type-Safe Foreign Function Interface (FFI)**: Database rows returned from D1 queries arrive as JavaScript Proxy objects (`JsProxy`). We integrated a custom FFI wrapper `get_field()` inside `main.py` to safely extract fields without throwing Pyodide `AttributeError` exceptions.
- **Top-Level Debugging Console**: The entire worker is wrapped inside a global traceback handler. If any runtime exception ever occurs, it converts opaque "Error 1101" pages into structured, detailed traceback logs served directly to your browser for seamless debugging.
