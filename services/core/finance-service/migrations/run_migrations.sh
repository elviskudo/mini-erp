#!/bin/bash
# Finance Service Migration Runner
# Usage: ./run_migrations.sh [up|down|seed]

set -e

DATABASE_URL="${DATABASE_URL:-postgres://postgres:postgres@localhost:5433/mini_erp?sslmode=disable}"
MIGRATIONS_DIR="$(dirname "$0")"

echo "🔄 Running Finance Service Migrations..."
echo "Database: $DATABASE_URL"
echo "Migrations: $MIGRATIONS_DIR"

case "${1:-up}" in
  up)
    echo "📊 Applying migrations..."
    psql "$DATABASE_URL" -f "$MIGRATIONS_DIR/001_initial_schema.sql"
    echo "✅ Schema created"
    ;;
  seed)
    echo "🌱 Seeding COA..."
    psql "$DATABASE_URL" -f "$MIGRATIONS_DIR/002_seed_coa.sql"
    echo "✅ COA seeded"
    ;;
  sample)
    echo "📝 Adding sample data..."
    psql "$DATABASE_URL" -f "$MIGRATIONS_DIR/003_sample_data.sql"
    echo "✅ Sample data added"
    ;;
  all)
    echo "📊 Running all migrations..."
    psql "$DATABASE_URL" -f "$MIGRATIONS_DIR/001_initial_schema.sql"
    psql "$DATABASE_URL" -f "$MIGRATIONS_DIR/002_seed_coa.sql"
    psql "$DATABASE_URL" -f "$MIGRATIONS_DIR/003_sample_data.sql"
    echo "✅ All migrations complete"
    ;;
  down)
    echo "⚠️  Dropping Finance tables..."
    psql "$DATABASE_URL" -c "
      DROP TABLE IF EXISTS petty_cash CASCADE;
      DROP TABLE IF EXISTS bank_reconciliations CASCADE;
      DROP TABLE IF EXISTS bank_transactions CASCADE;
      DROP TABLE IF EXISTS bank_accounts CASCADE;
      DROP TABLE IF EXISTS asset_depreciation_log CASCADE;
      DROP TABLE IF EXISTS fixed_assets CASCADE;
      DROP TABLE IF EXISTS journal_details CASCADE;
      DROP TABLE IF EXISTS journal_entries CASCADE;
      DROP TABLE IF EXISTS fiscal_periods CASCADE;
      DROP TABLE IF EXISTS chart_of_accounts CASCADE;
    "
    echo "✅ Tables dropped"
    ;;
  *)
    echo "Usage: $0 [up|seed|sample|all|down]"
    exit 1
    ;;
esac

echo "🎉 Done!"
