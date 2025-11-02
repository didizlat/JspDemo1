#!/bin/bash
echo "============================================================"
echo "Database Reset Script"
echo "============================================================"
echo ""
echo "This will delete all data and reset the database to clean state."
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

echo ""
echo "[1/2] Stopping Spring Boot server..."
pkill -f "spring-boot:run" 2>/dev/null || true
sleep 2

echo "[2/2] Deleting database files..."
if [ -f "data/jspdemo.mv.db" ]; then
    rm -f data/jspdemo.mv.db
    echo "  - Deleted: data/jspdemo.mv.db"
fi
if [ -f "data/jspdemo.trace.db" ]; then
    rm -f data/jspdemo.trace.db
    echo "  - Deleted: data/jspdemo.trace.db"
fi
if ls data/*.lock.db 1> /dev/null 2>&1; then
    rm -f data/*.lock.db
    echo "  - Deleted: lock files"
fi

echo ""
echo "============================================================"
echo "Database reset complete!"
echo "============================================================"
echo ""
echo "The database will be recreated on next server start."
echo "Tables will be empty with fresh schema."
echo ""
echo "To start the server:"
echo "  ./mvnw spring-boot:run"
echo ""

