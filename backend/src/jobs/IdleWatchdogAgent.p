/*------------------------------------------------------------------------
  IdleWatchdogAgent.p — Every 15 minutes
  Sets status = 'idle' on labels where days_without_scan exceeds the
  configured threshold AND the label is still in available_in_stock.
  Labels already in a downstream status (reserved, in_load, …) are not
  touched — they are actively being processed.
------------------------------------------------------------------------*/

DEFINE VARIABLE piThreshold AS INTEGER NO-UNDO.

/* Read threshold from environment; fall back to 30 days */
piThreshold = INTEGER(OS-GETENV("SHIPPING_IDLE_THRESHOLD_DAYS")) NO-ERROR.
IF piThreshold = ? OR piThreshold <= 0 THEN piThreshold = 30.

DEFINE BUFFER bLabel FOR stock_labels.

FOR EACH bLabel EXCLUSIVE-LOCK
    WHERE bLabel.status = "available_in_stock"
      AND bLabel.days_without_scan >= piThreshold:

    ASSIGN
        bLabel.status     = "idle"
        bLabel.updated_at = NOW.
END.
