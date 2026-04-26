USING model.AppError FROM PROPATH.

CLASS business.LoadService:

    /*
     * Load status state machine per CLAUDE.md:
     *
     * draft      → pending | cancelled
     * pending    → in_transit | cancelled
     * in_transit → dispatched | cancelled
     * dispatched → delivered | cancelled
     * delivered  → (terminal)
     * cancelled  → (terminal)
     */
    METHOD PUBLIC CHARACTER LoadTransition(
        INPUT pcFrom AS CHARACTER,
        INPUT pcTo   AS CHARACTER
    ):
        DEFINE VARIABLE lValid AS LOGICAL NO-UNDO INITIAL FALSE.

        CASE pcFrom:
            WHEN "draft" THEN
                lValid = CAN-DO("pending,cancelled", pcTo).
            WHEN "pending" THEN
                lValid = CAN-DO("in_transit,cancelled", pcTo).
            WHEN "in_transit" THEN
                lValid = CAN-DO("dispatched,cancelled", pcTo).
            WHEN "dispatched" THEN
                lValid = CAN-DO("delivered,cancelled", pcTo).
            WHEN "delivered" OR WHEN "cancelled" THEN
                lValid = FALSE.
            OTHERWISE
                UNDO, THROW NEW AppError(
                    SUBSTITUTE("Unknown load status: '&1'", pcFrom)).
        END CASE.

        IF NOT lValid THEN
            UNDO, THROW NEW AppError(
                SUBSTITUTE("Invalid load transition: '&1' → '&2'", pcFrom, pcTo)).

        RETURN pcTo.
    END METHOD.

    /*
     * Returns TRUE when pcWeight fits within pcCapacity.
     * Used before confirming a load to guard against overloading.
     */
    METHOD PUBLIC LOGICAL WeightFits(
        INPUT pcWeight   AS DECIMAL,
        INPUT pcCapacity AS DECIMAL
    ):
        RETURN pcWeight <= pcCapacity.
    END METHOD.

END CLASS.
