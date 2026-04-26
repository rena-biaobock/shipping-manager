USING model.AppError FROM PROPATH.

CLASS data.StockLabelRepository:

    /*
     * Returns a single stock_labels record by progressivo into output buffer.
     * Caller's buffer must be a buffer for the stock_labels table.
     */
    METHOD PUBLIC LOGICAL FindByProgressivo(
        INPUT  pcProgressivo AS CHARACTER,
        OUTPUT TABLE-HANDLE phResult
    ):
        DEFINE BUFFER bLabel FOR stock_labels.

        FIND FIRST bLabel WHERE bLabel.progressivo = pcProgressivo
            NO-LOCK NO-ERROR.

        IF NOT AVAILABLE bLabel THEN RETURN FALSE.

        /* Copy to caller's output table-handle — caller allocates temp-table */
        phResult:EMPTY-TEMP-TABLE().
        phResult:DEFAULT-BUFFER-HANDLE:FIND-FIRST("WHERE progressivo = '" + pcProgressivo + "'") NO-ERROR.
        RETURN TRUE.
    END METHOD.

    /*
     * Returns all stock_labels records into a caller-supplied temp-table handle.
     * Optionally filters by status or warehouse_code (pass ? to skip each filter).
     */
    METHOD PUBLIC VOID ListLabels(
        INPUT  pcStatus    AS CHARACTER,
        INPUT  pcWarehouse AS CHARACTER,
        OUTPUT TABLE-HANDLE phResult
    ):
        DEFINE BUFFER bLabel FOR stock_labels.

        phResult:EMPTY-TEMP-TABLE().

        FOR EACH bLabel NO-LOCK:
            IF pcStatus    <> ? AND bLabel.status         <> pcStatus    THEN NEXT.
            IF pcWarehouse <> ? AND bLabel.warehouse_code <> pcWarehouse THEN NEXT.

            phResult:DEFAULT-BUFFER-HANDLE:BUFFER-COPY(BUFFER bLabel:HANDLE).
            phResult:DEFAULT-BUFFER-HANDLE:BUFFER-CREATE().
        END.
    END METHOD.

    /*
     * Updates the status field for a given label.
     * Throws AppError if the record is not found.
     */
    METHOD PUBLIC VOID UpdateStatus(
        INPUT pcProgressivo AS CHARACTER,
        INPUT pcNewStatus   AS CHARACTER
    ):
        DEFINE BUFFER bLabel FOR stock_labels.

        FIND FIRST bLabel WHERE bLabel.progressivo = pcProgressivo
            EXCLUSIVE-LOCK NO-WAIT NO-ERROR.

        IF NOT AVAILABLE bLabel THEN
            UNDO, THROW NEW AppError(
                SUBSTITUTE("Label not found: '&1'", pcProgressivo)).

        ASSIGN
            bLabel.status     = pcNewStatus
            bLabel.updated_at = NOW.
    END METHOD.

    /*
     * Bulk-updates status for all progressivos in a given load.
     * Used when a load is confirmed (all labels → in_load).
     */
    METHOD PUBLIC VOID BulkUpdateStatus(
        INPUT pcLoadId    AS CHARACTER,
        INPUT pcNewStatus AS CHARACTER
    ):
        DEFINE BUFFER bItem  FOR load_items.
        DEFINE BUFFER bLabel FOR stock_labels.

        FOR EACH bItem NO-LOCK WHERE bItem.load_id = pcLoadId:
            FIND FIRST bLabel WHERE bLabel.progressivo = bItem.stock_label_id
                EXCLUSIVE-LOCK NO-WAIT NO-ERROR.
            IF AVAILABLE bLabel THEN
                ASSIGN
                    bLabel.status     = pcNewStatus
                    bLabel.updated_at = NOW.
        END.
    END METHOD.

END CLASS.
