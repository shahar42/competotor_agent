#!/bin/bash
set -e

echo "🗑️  Dropping old tables..."
psql postgresql://product_scanner:Pinkfloys69!@localhost:5432/product_scanner <<SQL
DROP TABLE IF EXISTS scan_history CASCADE;
DROP TABLE IF EXISTS competitors CASCADE;
DROP TABLE IF EXISTS ideas CASCADE;
DROP TABLE IF EXISTS users CASCADE;
SQL

echo "✅ Tables dropped"
echo ""
echo "🧪 Running test (will recreate tables)..."
echo ""

python tests/test_local_flow.py
