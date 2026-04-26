/*------------------------------------------------------------------------
  StockSnapshotAgent.p — Daily 02:00
  Appends one row per (warehouse_code, status) to stock_history with
  the current label count and total volume_tons.
------------------------------------------------------------------------*/

DEFINE TEMP-TABLE ttSnapshot NO-UNDO
    FIELD snapshot_date  AS DATE
    FIELD warehouse_code AS CHARACTER
    FIELD status         AS CHARACTER
    FIELD label_count    AS INTEGER
    FIELD total_tons     AS DECIMAL.

DEFINE VARIABLE pdDate AS DATE NO-UNDO.
pdDate = TODAY.

/* Aggregate: one pass over stock_labels grouped by warehouse + status */
DEFINE BUFFER bLabel FOR stock_labels.

FOR EACH bLabel NO-LOCK
    BREAK BY bLabel.warehouse_code BY bLabel.status:

    IF FIRST-OF(bLabel.status) THEN DO:
        CREATE ttSnapshot.
        ASSIGN
            ttSnapshot.snapshot_date  = pdDate
            ttSnapshot.warehouse_code = bLabel.warehouse_code
            ttSnapshot.status         = bLabel.status
            ttSnapshot.label_count    = 0
            ttSnapshot.total_tons     = 0.
    END.

    FIND LAST ttSnapshot WHERE ttSnapshot.warehouse_code = bLabel.warehouse_code
                           AND ttSnapshot.status         = bLabel.status
                           AND ttSnapshot.snapshot_date  = pdDate NO-ERROR.
    IF AVAILABLE ttSnapshot THEN
        ASSIGN
            ttSnapshot.label_count = ttSnapshot.label_count + 1
            ttSnapshot.total_tons  = ttSnapshot.total_tons  + bLabel.volume_tons.
END.

/* Persist to stock_history */
DEFINE BUFFER bHist FOR stock_history.

FOR EACH ttSnapshot NO-LOCK:
    CREATE bHist.
    ASSIGN
        bHist.id            = GENERATE-UUID()
        bHist.snapshot_date = ttSnapshot.snapshot_date
        bHist.warehouse_code = ttSnapshot.warehouse_code
        bHist.status        = ttSnapshot.status
        bHist.label_count   = ttSnapshot.label_count
        bHist.total_tons    = ttSnapshot.total_tons
        bHist.created_at    = NOW.
END.
