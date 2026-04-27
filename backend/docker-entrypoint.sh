#!/bin/bash
set -e

CORS_ORIGINS="${OE_CORS_ORIGINS:-http://localhost}"
JWT_SECRET="${OE_JWT_SECRET:-changeme}"
DB_PATH="${OE_DB_PATH:-/data/shipping_manager}"
IDLE_THRESHOLD="${OE_IDLE_THRESHOLD_DAYS:-30}"

# Write runtime openedge.properties from environment
cat > /shipping_manager/conf/openedge.properties <<EOF
psc.as.appdir=shipping_manager
psc.as.oe.url=http://localhost:8080
psc.as.db.1=-db ${DB_PATH} -H localhost -S 8090
psc.as.db.connect.wait=30
shipping.cors.allowed-origins=${CORS_ORIGINS}
shipping.jwt.secret=${JWT_SECRET}
shipping.jwt.expire-minutes=60
shipping.page.default-size=25
shipping.page.max-size=100
shipping.idle.threshold-days=${IDLE_THRESHOLD}
shipping.report.dir=/reports
EOF

# Bootstrap the database on first run
if [ ! -f "${DB_PATH}.db" ]; then
  echo "[entrypoint] Initializing OpenEdge database at ${DB_PATH}..."
  prodb "${DB_PATH}"
  proserve -db "${DB_PATH}" -S 8090
  proutil "${DB_PATH}" -C updatedb -df /shipping_manager/schema/shipping_manager.df
  proshut "${DB_PATH}" -by
fi

# Start the database server
echo "[entrypoint] Starting OpenEdge database server..."
proserve -db "${DB_PATH}" -S 8090

# Give the DB a moment to accept connections
sleep 5

echo "[entrypoint] Starting PASOE..."
exec "$DLC/bin/tcman" start shipping_manager
