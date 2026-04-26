USING model.AppError FROM PROPATH.

CLASS data.LoadItemRepository:

    /*
     * Inserts a load_items row linking a label to a load.
     */
    METHOD PUBLIC VOID AddItem(
        INPUT pcLoadId      AS CHARACTER,
        INPUT pcProgressivo AS CHARACTER
    ):
        DEFINE BUFFER bItem FOR load_items.

        CREATE bItem.
        ASSIGN
            bItem.id             = GENERATE-UUID()
            bItem.load_id        = pcLoadId
            bItem.stock_label_id = pcProgressivo.
    END METHOD.

    /*
     * Returns all load_items rows for a given load into the caller's temp-table.
     */
    METHOD PUBLIC VOID ListByLoad(
        INPUT  pcLoadId  AS CHARACTER,
        OUTPUT TABLE-HANDLE phResult
    ):
        DEFINE BUFFER bItem FOR load_items.

        phResult:EMPTY-TEMP-TABLE().

        FOR EACH bItem NO-LOCK WHERE bItem.load_id = pcLoadId:
            phResult:DEFAULT-BUFFER-HANDLE:BUFFER-COPY(BUFFER bItem:HANDLE).
            phResult:DEFAULT-BUFFER-HANDLE:BUFFER-CREATE().
        END.
    END METHOD.

    /*
     * Returns the sum of volume_tons for all labels in a load.
     * Used to recompute loads.total_weight_tons.
     */
    METHOD PUBLIC DECIMAL SumWeightByLoad(INPUT pcLoadId AS CHARACTER):
        DEFINE BUFFER bItem  FOR load_items.
        DEFINE BUFFER bLabel FOR stock_labels.
        DEFINE VARIABLE pdSum AS DECIMAL NO-UNDO INITIAL 0.

        FOR EACH bItem NO-LOCK WHERE bItem.load_id = pcLoadId:
            FIND FIRST bLabel WHERE bLabel.progressivo = bItem.stock_label_id
                NO-LOCK NO-ERROR.
            IF AVAILABLE bLabel THEN
                pdSum = pdSum + bLabel.volume_tons.
        END.

        RETURN pdSum.
    END METHOD.

END CLASS.
