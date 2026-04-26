USING model.BinPackingModel FROM PROPATH.

CLASS business.BinPackingService:

    /*
     * Pack — First Fit Decreasing bin-packing on volume_tons.
     *
     * Parameters
     *   phLabels       — HANDLE to a temp-table with fields:
     *                    progressivo, volume_tons, market_type,
     *                    warehouse_code, order_condition, country, exit_date
     *   pdCapacity     — truck capacity in metric tons
     *   piMaxIter      — iteration cap (? = unlimited)
     *   pcWarehouse    — warehouse_code filter (? = any)
     *   pcCondition    — order_condition filter (? = any)
     *   pcCountry      — country filter (? = any)
     *
     * Only "ME" (Mercado Externo) labels are packed; "MI" labels are always excluded.
     * Returns a BinPackingModel with the packed items, total weight, and partial flag.
     */
    METHOD PUBLIC BinPackingModel Pack(
        INPUT phLabels    AS HANDLE,
        INPUT pdCapacity  AS DECIMAL,
        INPUT piMaxIter   AS INTEGER,
        INPUT pcWarehouse AS CHARACTER,
        INPUT pcCondition AS CHARACTER,
        INPUT pcCountry   AS CHARACTER
    ):
        /* Working temp-table of candidates */
        DEFINE VARIABLE hBuf         AS HANDLE  NO-UNDO.
        DEFINE VARIABLE hQuery       AS HANDLE  NO-UNDO.
        DEFINE VARIABLE hSortQuery   AS HANDLE  NO-UNDO.

        DEFINE TEMP-TABLE ttCand NO-UNDO
            FIELD progressivo AS CHARACTER
            FIELD volume_tons AS DECIMAL
            INDEX idxVol volume_tons DESCENDING.

        DEFINE VARIABLE oPlan        AS BinPackingModel NO-UNDO.
        DEFINE VARIABLE pdTotal      AS DECIMAL  NO-UNDO INITIAL 0.
        DEFINE VARIABLE piIter       AS INTEGER  NO-UNDO INITIAL 0.
        DEFINE VARIABLE lPartial     AS LOGICAL  NO-UNDO INITIAL FALSE.
        DEFINE VARIABLE pcProgressivo AS CHARACTER NO-UNDO.
        DEFINE VARIABLE pdVol        AS DECIMAL  NO-UNDO.

        oPlan = NEW BinPackingModel().

        /* — Build candidate list from caller's buffer ————————————— */
        hBuf = phLabels:DEFAULT-BUFFER-HANDLE.

        CREATE QUERY hQuery.
        hQuery:SET-BUFFERS(hBuf).
        hQuery:QUERY-PREPARE(SUBSTITUTE("FOR EACH &1 NO-LOCK", hBuf:NAME)).
        hQuery:QUERY-OPEN().

        DO WHILE hQuery:GET-NEXT():
            /* Exclude MI market */
            IF hBuf:BUFFER-FIELD("market_type"):BUFFER-VALUE <> "ME" THEN NEXT.

            /* Warehouse filter */
            IF pcWarehouse <> ? THEN DO:
                IF hBuf:BUFFER-FIELD("warehouse_code"):BUFFER-VALUE <> pcWarehouse THEN NEXT.
            END.

            /* Country filter */
            IF pcCountry <> ? THEN DO:
                IF hBuf:BUFFER-FIELD("country"):BUFFER-VALUE <> pcCountry THEN NEXT.
            END.

            /* Order condition filter */
            IF pcCondition <> ? THEN DO:
                IF hBuf:BUFFER-FIELD("order_condition"):BUFFER-VALUE <> pcCondition THEN NEXT.
            END.

            CREATE ttCand.
            ASSIGN
                ttCand.progressivo = hBuf:BUFFER-FIELD("progressivo"):BUFFER-VALUE
                ttCand.volume_tons = DECIMAL(hBuf:BUFFER-FIELD("volume_tons"):BUFFER-VALUE).
        END.
        hQuery:QUERY-CLOSE().
        DELETE OBJECT hQuery NO-ERROR.

        /* — FFD: iterate candidates sorted by volume DESC ——————————— */
        FOR EACH ttCand NO-LOCK BY ttCand.volume_tons DESCENDING:
            IF piMaxIter <> ? THEN DO:
                piIter = piIter + 1.
                IF piIter > piMaxIter THEN DO:
                    lPartial = TRUE.
                    LEAVE.
                END.
            END.

            IF pdTotal + ttCand.volume_tons <= pdCapacity THEN DO:
                CREATE oPlan.ttItems.
                ASSIGN
                    oPlan.ttItems.progressivo = ttCand.progressivo
                    oPlan.ttItems.volume_tons = ttCand.volume_tons.
                pdTotal = pdTotal + ttCand.volume_tons.
            END.
        END.

        ASSIGN
            oPlan:TotalWeightTons = pdTotal
            oPlan:Partial         = lPartial.

        RETURN oPlan.
    END METHOD.

END CLASS.
