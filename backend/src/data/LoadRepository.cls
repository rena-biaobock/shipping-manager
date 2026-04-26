USING model.AppError FROM PROPATH.

CLASS data.LoadRepository:

    /*
     * Creates a new load record and returns its generated GUID.
     */
    METHOD PUBLIC CHARACTER CreateLoad(
        INPUT pdCapacity    AS DECIMAL,
        INPUT pcDestination AS CHARACTER,
        INPUT pcCustomer    AS CHARACTER,
        INPUT pcTruckPlate  AS CHARACTER
    ):
        DEFINE VARIABLE pcId AS CHARACTER NO-UNDO.
        DEFINE BUFFER bLoad FOR loads.

        pcId = GENERATE-UUID().

        CREATE bLoad.
        ASSIGN
            bLoad.id                 = pcId
            bLoad.truck_capacity_tons = pdCapacity
            bLoad.destination        = pcDestination
            bLoad.customer           = pcCustomer
            bLoad.truck_plate        = pcTruckPlate
            bLoad.status             = "draft"
            bLoad.total_weight_tons  = 0
            bLoad.created_at         = NOW
            bLoad.updated_at         = NOW.

        RETURN pcId.
    END METHOD.

    /*
     * Finds a load by ID.
     * Returns TRUE if found; fills phResult with the record.
     */
    METHOD PUBLIC LOGICAL FindById(
        INPUT  pcId     AS CHARACTER,
        OUTPUT TABLE-HANDLE phResult
    ):
        DEFINE BUFFER bLoad FOR loads.

        FIND FIRST bLoad WHERE bLoad.id = pcId NO-LOCK NO-ERROR.
        IF NOT AVAILABLE bLoad THEN RETURN FALSE.

        phResult:EMPTY-TEMP-TABLE().
        phResult:DEFAULT-BUFFER-HANDLE:BUFFER-COPY(BUFFER bLoad:HANDLE).
        RETURN TRUE.
    END METHOD.

    /*
     * Returns all load records into the caller's temp-table.
     * Optionally filters by status (pass ? to skip).
     */
    METHOD PUBLIC VOID ListLoads(
        INPUT  pcStatus  AS CHARACTER,
        OUTPUT TABLE-HANDLE phResult
    ):
        DEFINE BUFFER bLoad FOR loads.

        phResult:EMPTY-TEMP-TABLE().

        FOR EACH bLoad NO-LOCK:
            IF pcStatus <> ? AND bLoad.status <> pcStatus THEN NEXT.
            phResult:DEFAULT-BUFFER-HANDLE:BUFFER-COPY(BUFFER bLoad:HANDLE).
            phResult:DEFAULT-BUFFER-HANDLE:BUFFER-CREATE().
        END.
    END METHOD.

    /*
     * Transitions the status of a load and timestamps the relevant field.
     */
    METHOD PUBLIC VOID UpdateStatus(
        INPUT pcId        AS CHARACTER,
        INPUT pcNewStatus AS CHARACTER
    ):
        DEFINE BUFFER bLoad FOR loads.

        FIND FIRST bLoad WHERE bLoad.id = pcId
            EXCLUSIVE-LOCK NO-WAIT NO-ERROR.

        IF NOT AVAILABLE bLoad THEN
            UNDO, THROW NEW AppError(
                SUBSTITUTE("Load not found: '&1'", pcId)).

        ASSIGN bLoad.status     = pcNewStatus
               bLoad.updated_at = NOW.

        CASE pcNewStatus:
            WHEN "in_transit" THEN bLoad.dispatched_at = NOW.
            WHEN "delivered"  THEN bLoad.delivered_at  = NOW.
        END CASE.
    END METHOD.

    /*
     * Updates total_weight_tons after labels are added/removed.
     */
    METHOD PUBLIC VOID UpdateTotalWeight(
        INPUT pcId         AS CHARACTER,
        INPUT pdTotalTons  AS DECIMAL
    ):
        DEFINE BUFFER bLoad FOR loads.

        FIND FIRST bLoad WHERE bLoad.id = pcId
            EXCLUSIVE-LOCK NO-WAIT NO-ERROR.

        IF NOT AVAILABLE bLoad THEN
            UNDO, THROW NEW AppError(
                SUBSTITUTE("Load not found: '&1'", pcId)).

        ASSIGN
            bLoad.total_weight_tons = pdTotalTons
            bLoad.updated_at        = NOW.
    END METHOD.

END CLASS.
