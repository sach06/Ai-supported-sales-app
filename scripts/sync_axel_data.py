"""
scripts/sync_axel_data.py
=========================
One-shot ETL: reads Axel's work_apps data → writes the exact DuckDB tables
that data_service queries (bcg_installed_base + crm_data).

⚠️  Stop the Streamlit app before running this script!

Usage (from project root):
    .\\venv\\Scripts\\python.exe scripts\\sync_axel_data.py

Dry-run (no DB write):
    .\\venv\\Scripts\\python.exe scripts\\sync_axel_data.py --dry-run
"""
from __future__ import annotations

import argparse
import logging
import sys
import warnings
from pathlib import Path
from datetime import datetime

warnings.filterwarnings("ignore")

ROOT       = Path(__file__).parent.parent
WORK_APPS  = ROOT / "temp_repos" / "work_apps" / "templates"
DB_PATH    = ROOT / "data" / "sales_app.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
)
logger = logging.getLogger("sync_axel")

CURRENT_YEAR = datetime.now().year

# ─────────────────────────────────────────────────────────────────────────────
# BCG / Installed-Base  →  bcg_installed_base schema
# Mandatory internal columns (queried by SQL in data_service):
#   company_internal, country_internal, region, equipment_type,
#   latitude_internal, longitude_internal, start_year_internal, capacity_internal
# ─────────────────────────────────────────────────────────────────────────────

def build_bcg_installed_base(ib_path: Path):
    import pandas as pd

    logger.info("  Reading %s", ib_path)
    df = pd.read_excel(ib_path)
    logger.info("  Raw: %d rows × %d cols", len(df), len(df.columns))

    # ── internal columns (used by SQL queries in data_service) ────────────────
    df["company_internal"]   = df.get("ib_customer",        pd.Series(dtype=str)).fillna("").astype(str)
    df["country_internal"]   = df.get("ib_customer_country",pd.Series(dtype=str)).fillna("").astype(str)
    df["region"]             = df.get("ib_region",          pd.Series(dtype=str)).fillna("").astype(str)

    # Startup year → integer
    raw_year = pd.to_datetime(df.get("ib_startup"), errors="coerce").dt.year
    df["start_year_internal"]  = pd.to_numeric(raw_year, errors="coerce").astype("float64")

    df["latitude_internal"]  = pd.to_numeric(df.get("lat"),  errors="coerce").astype("float64")
    df["longitude_internal"] = pd.to_numeric(df.get("lon"),  errors="coerce").astype("float64")
    df["capacity_internal"]  = 1.0   # IB list has no capacity field; default to 1 for counts

    # equipment_type is the sheet-name equivalent — use pbs_plant_type
    df["equipment_type"] = df.get("pbs_plant_type", pd.Series(dtype=str)).fillna("Unknown").astype(str)

    # ── extra display columns ─────────────────────────────────────────────────
    df["Machine Description"] = df.get("ib_machine",    pd.Series(dtype=str)).astype(str)
    df["Product"]             = df.get("ib_product",    pd.Series(dtype=str)).astype(str)
    df["Business Unit"]       = df.get("pbs_coe",       pd.Series(dtype=str)).astype(str)
    df["CoC"]                 = df.get("pbs_coc",       pd.Series(dtype=str)).astype(str)
    df["City"]                = df.get("ib_city",       pd.Series(dtype=str)).astype(str)
    df["Status"]              = df.get("ib_status",     pd.Series(dtype=str)).astype(str)
    df["Key Account"]         = df.get("key_account",   pd.Series(dtype=str)).astype(str)
    df["Sub-Region"]          = df.get("sub_region",    pd.Series(dtype=str)).astype(str)
    df["Responsible"]         = df.get("ib_responsible",pd.Series(dtype=str)).astype(str)
    df["Product Family"]      = df.get("pbs_product_family", pd.Series(dtype=str)).astype(str)
    df["IB_ID"]               = pd.to_numeric(df.get("ib_id"), errors="coerce").astype("float64")
    df["Equipment Age"]       = (CURRENT_YEAR - df["start_year_internal"]).clip(0, 100)
    df["OEM"]                 = "SMS"

    # Trim unwanted raw columns that could confuse DuckDB type inference
    # Note: some column names may be datetime objects (Excel artefact), stringify first
    df.columns = [str(c) for c in df.columns]
    drop_cols = [c for c in df.columns if c.startswith("Unnamed") or c.startswith("last change")]
    df = df.drop(columns=drop_cols, errors="ignore")

    # ── standardise all object cols to str to avoid DuckDB type mismatches ────
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).replace({"nan": None, "None": None, "__NULL__": None})

    logger.info("  bcg_installed_base ready: %d rows × %d cols", len(df), len(df.columns))
    return df


# ─────────────────────────────────────────────────────────────────────────────
# CRM / Projects  →  crm_data schema
# Mandatory columns (queried by SQL in data_service):
#   name, country, region, industry, rating, status,
#   fte, revenue, latitude, longitude, company_ceo, fte_count
# ─────────────────────────────────────────────────────────────────────────────

def build_crm_data(proj_path: Path):
    import pandas as pd

    logger.info("  Reading %s", proj_path)
    df = pd.read_excel(proj_path)
    logger.info("  Raw: %d rows × %d cols", len(df), len(df.columns))

    # Fix datetimes
    for col in ["CP_created_on", "CP_changed_on", "cp_close_date", "sp_oi_date", "date_of_inquiry"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            try:
                df[col] = df[col].dt.tz_localize(None)
            except Exception:
                pass

    out = pd.DataFrame()

    # ── mandatory identity columns used in SQL joins ───────────────────────────
    out["name"]       = df.get("account_name", pd.Series(dtype=str)).fillna("").astype(str)
    out["country"]    = df.get("account_country", pd.Series(dtype=str)).fillna("").astype(str)
    out["region"]     = df.get("cp_region", pd.Series(dtype=str)).fillna("").astype(str)
    out["industry"]   = "Steel"   # default — Axel's data doesn't carry this

    # rating A/B/C/D from win probability
    prob = pd.to_numeric(df.get("cp_chance_realization"), errors="coerce").fillna(0)
    out["rating"] = pd.cut(
        prob,
        bins=[-1, 25, 50, 75, 101],
        labels=["D", "C", "B", "A"],
    ).astype(str)

    # status
    out["status"]     = df.get("cp_status_hot", pd.Series(dtype=str)).fillna("").astype(str)

    # enrichment-ready columns (no data from Axel, but data_service needs them)
    out["fte"]         = None
    out["revenue"]     = None
    out["latitude"]    = None
    out["longitude"]   = None
    out["company_ceo"] = None
    out["fte_count"]   = None

    # ── rich CRM columns ──────────────────────────────────────────────────────
    out["Sub-Region"]            = df.get("sub_region", pd.Series(dtype=str)).fillna("").astype(str)
    out["Key Account"]           = df.get("key_account", pd.Series(dtype=str)).fillna("").astype(str)
    out["Equipment Type"]        = df.get("pbs_plant_type", pd.Series(dtype=str)).fillna("").astype(str)
    out["Business Unit"]         = df.get("pbs_coe", pd.Series(dtype=str)).fillna("").astype(str)
    out["CoC"]                   = df.get("pbs_coc", pd.Series(dtype=str)).fillna("").astype(str)
    out["Sales Phase"]           = df.get("cp_sales_phase", pd.Series(dtype=str)).fillna("").astype(str)
    out["Expected Value (EUR)"]  = pd.to_numeric(df.get("cp_expected_value_eur"), errors="coerce")
    out["SP Expected Value (EUR)"] = pd.to_numeric(df.get("sp_expected_value_eur"), errors="coerce")
    out["Win Probability"]       = prob
    out["Close Date"]            = df.get("cp_close_date")
    out["Created On"]            = df.get("CP_created_on")
    out["Changed On"]            = df.get("CP_changed_on")
    out["Project Name"]          = df.get("customer_project", pd.Series(dtype=str)).fillna("").astype(str)
    out["Codeword"]              = df.get("codeword_sales", pd.Series(dtype=str)).fillna("").astype(str)
    out["CP_ID"]                 = pd.to_numeric(df.get("cp_id"), errors="coerce")
    out["SP_ID"]                 = pd.to_numeric(df.get("sp_id"), errors="coerce")
    out["Sales Unit"]            = df.get("sales_unit", pd.Series(dtype=str)).fillna("").astype(str)
    out["Entity Area"]           = df.get("entity_area", pd.Series(dtype=str)).fillna("").astype(str)
    out["City"]                  = df.get("account_city", pd.Series(dtype=str)).fillna("").astype(str)
    out["latest_notes"]          = df.get("latest_notes", pd.Series(dtype=str)).fillna("").astype(str)

    # ── standardise all object cols ───────────────────────────────────────────
    for col in out.columns:
        if out[col].dtype == object:
            out[col] = out[col].astype(str).replace({"nan": None, "None": None, "NaT": None})

    logger.info("  crm_data ready: %d rows × %d cols", len(out), len(out.columns))
    return out


# ─────────────────────────────────────────────────────────────────────────────
# DB write
# ─────────────────────────────────────────────────────────────────────────────

def write_to_db(db_path: Path, bcg_df, crm_df):
    import duckdb

    logger.info("Opening DB: %s", db_path)
    conn = duckdb.connect(str(db_path))

    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    logger.info("Existing tables: %s", tables)

    # ── BCG installed base ────────────────────────────────────────────────────
    for archive in ("bcg_installed_base_archive",):
        conn.execute(f"DROP TABLE IF EXISTS {archive}")
    if "bcg_installed_base" in tables:
        old_cnt = conn.execute("SELECT COUNT(*) FROM bcg_installed_base").fetchone()[0]
        logger.info("  Archiving old bcg_installed_base (%d rows)", old_cnt)
        conn.execute("ALTER TABLE bcg_installed_base RENAME TO bcg_installed_base_archive")

    conn.execute("CREATE TABLE bcg_installed_base AS SELECT * FROM bcg_df")
    new_cnt = conn.execute("SELECT COUNT(*) FROM bcg_installed_base").fetchone()[0]
    logger.info("  ✅ bcg_installed_base: %d rows", new_cnt)

    # ── CRM data ──────────────────────────────────────────────────────────────
    for archive in ("crm_data_archive",):
        conn.execute(f"DROP TABLE IF EXISTS {archive}")
    if "crm_data" in tables:
        old_cnt = conn.execute("SELECT COUNT(*) FROM crm_data").fetchone()[0]
        logger.info("  Archiving old crm_data (%d rows)", old_cnt)
        conn.execute("ALTER TABLE crm_data RENAME TO crm_data_archive")

    conn.execute("CREATE TABLE crm_data AS SELECT * FROM crm_df")
    new_cnt = conn.execute("SELECT COUNT(*) FROM crm_data").fetchone()[0]
    logger.info("  ✅ crm_data: %d rows", new_cnt)

    # Invalidate unified view so data_service rebuilds it on next app launch
    conn.execute("DROP TABLE IF EXISTS unified_companies")
    conn.execute("DROP TABLE IF EXISTS company_mappings")
    try:
        conn.execute("DELETE FROM _meta WHERE key = 'data_fingerprint'")
    except Exception:
        pass  # _meta table may not exist yet on a fresh DB
    logger.info("  ✅ unified_companies + company_mappings invalidated → will rebuild on next app start")

    conn.close()
    logger.info("DB closed.")


# ─────────────────────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--ib",   default=str(WORK_APPS / "ib_list.xlsx"))
    p.add_argument("--proj", default=str(WORK_APPS / "gh_current_projects.xlsx"))
    p.add_argument("--db",   default=str(DB_PATH))
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    logger.info("=" * 60)
    logger.info("Axel Data Sync  %s", datetime.now().isoformat(timespec="seconds"))
    logger.info("IB   → %s", args.ib)
    logger.info("CRM  → %s", args.proj)
    logger.info("DB   → %s", args.db)
    logger.info("=" * 60)

    ib_path   = Path(args.ib)
    proj_path = Path(args.proj)
    db_path   = Path(args.db)

    if not ib_path.exists():
        logger.error("IB file not found: %s", ib_path); sys.exit(1)
    if not proj_path.exists():
        logger.error("Projects file not found: %s", proj_path); sys.exit(1)

    bcg_df = build_bcg_installed_base(ib_path)
    crm_df = build_crm_data(proj_path)

    if args.dry_run:
        logger.info("DRY RUN — no DB write.")
        logger.info("BCG schema: %s", list(bcg_df.columns))
        logger.info("CRM schema: %s", list(crm_df.columns))
        logger.info("BCG sample:\n%s", bcg_df[["company_internal","country_internal","region",
                                                 "equipment_type","start_year_internal",
                                                 "latitude_internal","longitude_internal"]].head(3).to_string())
        logger.info("CRM sample:\n%s", crm_df[["name","country","region","rating",
                                                 "Equipment Type","Sales Phase",
                                                 "Expected Value (EUR)"]].head(3).to_string())
        return

    if not db_path.exists():
        logger.error("DB not found at %s — start the Streamlit app once to initialise it first.", db_path)
        sys.exit(1)

    write_to_db(db_path, bcg_df, crm_df)

    logger.info("=" * 60)
    logger.info("✅  Done!  Now start the Streamlit app and click 'Load Data'.")
    logger.info("   The app will rebuild company mappings and the unified view automatically.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
