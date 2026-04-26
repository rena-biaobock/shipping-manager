USING model.AppError FROM PROPATH.

CLASS business.StockService:

    /*
     * Valid label_status transitions.
     * State machine per CLAUDE.md — any status may transition to "damaged".
     *
     * available_in_stock → reserved | idle | damaged
     * reserved           → in_load | available_in_stock | damaged
     * in_load            → in_transit_to_terminal | available_in_stock | damaged
     * in_transit_to_terminal → available_in_terminal | damaged
     * available_in_terminal  → in_transit_to_client | damaged
     * in_transit_to_client   → delivered | damaged
     * idle               → available_in_stock | damaged
     * delivered          → (terminal)
     * damaged            → (terminal)
     */
    METHOD PUBLIC CHARACTER LabelTransition(
        INPUT pcFrom AS CHARACTER,
        INPUT pcTo   AS CHARACTER
    ):
        DEFINE VARIABLE lValid AS LOGICAL NO-UNDO INITIAL FALSE.

        CASE pcFrom:
            WHEN "available_in_stock" THEN
                lValid = CAN-DO("reserved,idle,damaged", pcTo).
            WHEN "reserved" THEN
                lValid = CAN-DO("in_load,available_in_stock,damaged", pcTo).
            WHEN "in_load" THEN
                lValid = CAN-DO("in_transit_to_terminal,available_in_stock,damaged", pcTo).
            WHEN "in_transit_to_terminal" THEN
                lValid = CAN-DO("available_in_terminal,damaged", pcTo).
            WHEN "available_in_terminal" THEN
                lValid = CAN-DO("in_transit_to_client,damaged", pcTo).
            WHEN "in_transit_to_client" THEN
                lValid = CAN-DO("delivered,damaged", pcTo).
            WHEN "idle" THEN
                lValid = CAN-DO("available_in_stock,damaged", pcTo).
            WHEN "delivered" OR WHEN "damaged" THEN
                lValid = FALSE.
            OTHERWISE
                UNDO, THROW NEW AppError(
                    SUBSTITUTE("Unknown label status: '&1'", pcFrom)).
        END CASE.

        IF NOT lValid THEN
            UNDO, THROW NEW AppError(
                SUBSTITUTE("Invalid label transition: '&1' → '&2'", pcFrom, pcTo)).

        RETURN pcTo.
    END METHOD.

END CLASS.
