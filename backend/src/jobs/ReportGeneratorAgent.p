/*------------------------------------------------------------------------
  ReportGeneratorAgent.p — Monday 06:00
  Generates a weekly stock and load summary report.
  Outputs:
    - /reports/weekly_stock_<YYYYMMDD>.csv   — label counts + tons by status
    - /reports/weekly_loads_<YYYYMMDD>.csv   — load counts + tons by status
------------------------------------------------------------------------*/

DEFINE VARIABLE pcDate    AS CHARACTER NO-UNDO.
DEFINE VARIABLE pcStockCsv AS CHARACTER NO-UNDO.
DEFINE VARIABLE pcLoadCsv  AS CHARACTER NO-UNDO.
DEFINE VARIABLE pcReportDir AS CHARACTER NO-UNDO.
DEFINE VARIABLE iFile     AS INTEGER   NO-UNDO.

pcDate      = STRING(TODAY, "99999999"). /* YYYYMMDD via format */
pcReportDir = OS-GETENV("SHIPPING_REPORT_DIR").
IF pcReportDir = ? OR pcReportDir = "" THEN pcReportDir = "/reports".

pcStockCsv = pcReportDir + "/weekly_stock_" + pcDate + ".csv".
pcLoadCsv  = pcReportDir + "/weekly_loads_" + pcDate + ".csv".

/* ── Stock summary ──────────────────────────────────────────────── */
OUTPUT TO VALUE(pcStockCsv).
PUT UNFORMATTED "status,label_count,total_tons" SKIP.

DEFINE BUFFER bLabel FOR stock_labels.

FOR EACH bLabel NO-LOCK
    BREAK BY bLabel.status:

    DEFINE VARIABLE piCount AS INTEGER NO-UNDO INITIAL 0.
    DEFINE VARIABLE pdTons  AS DECIMAL NO-UNDO INITIAL 0.

    ACCUMULATE bLabel.volume_tons (TOTAL BY bLabel.status).
    piCount = ACCUMULATE COUNT bLabel.progressivo (BY bLabel.status).
    pdTons  = ACCUMULATE TOTAL bLabel.volume_tons (BY bLabel.status).

    IF LAST-OF(bLabel.status) THEN
        PUT UNFORMATTED
            bLabel.status "," piCount "," pdTons SKIP.
END.

OUTPUT CLOSE.

/* ── Load summary ───────────────────────────────────────────────── */
OUTPUT TO VALUE(pcLoadCsv).
PUT UNFORMATTED "status,load_count,total_tons" SKIP.

DEFINE BUFFER bLoad FOR loads.

FOR EACH bLoad NO-LOCK
    BREAK BY bLoad.status:

    DEFINE VARIABLE piLCount AS INTEGER NO-UNDO INITIAL 0.
    DEFINE VARIABLE pdLTons  AS DECIMAL NO-UNDO INITIAL 0.

    ACCUMULATE bLoad.total_weight_tons (TOTAL BY bLoad.status).
    piLCount = ACCUMULATE COUNT bLoad.id (BY bLoad.status).
    pdLTons  = ACCUMULATE TOTAL bLoad.total_weight_tons (BY bLoad.status).

    IF LAST-OF(bLoad.status) THEN
        PUT UNFORMATTED
            bLoad.status "," piLCount "," pdLTons SKIP.
END.

OUTPUT CLOSE.
