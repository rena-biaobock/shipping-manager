USING OpenEdge.Core.Assert           FROM PROPATH.
USING business.StockService          FROM PROPATH.
USING model.AppError                 FROM PROPATH.

CLASS tests.unit.TestStockService:

    DEFINE PRIVATE VARIABLE oService AS StockService NO-UNDO.

    @Before.
    METHOD PUBLIC VOID Setup():
        oService = NEW StockService().
    END METHOD.

    @After.
    METHOD PUBLIC VOID Teardown():
        DELETE OBJECT oService NO-ERROR.
    END METHOD.

    /* ── valid forward transitions ─────────────────────────────────── */

    @Test.
    METHOD PUBLIC VOID TransitionAvailableToReserved():
        Assert:Equals("reserved",
            oService:LabelTransition("available_in_stock", "reserved")).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID TransitionAvailableToIdle():
        Assert:Equals("idle",
            oService:LabelTransition("available_in_stock", "idle")).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID TransitionAvailableToDamaged():
        Assert:Equals("damaged",
            oService:LabelTransition("available_in_stock", "damaged")).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID TransitionReservedToInLoad():
        Assert:Equals("in_load",
            oService:LabelTransition("reserved", "in_load")).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID TransitionReservedBackToAvailable():
        Assert:Equals("available_in_stock",
            oService:LabelTransition("reserved", "available_in_stock")).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID TransitionInLoadToInTransitToTerminal():
        Assert:Equals("in_transit_to_terminal",
            oService:LabelTransition("in_load", "in_transit_to_terminal")).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID TransitionInTransitToTerminalToAvailableAtTerminal():
        Assert:Equals("available_in_terminal",
            oService:LabelTransition("in_transit_to_terminal", "available_in_terminal")).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID TransitionAvailableAtTerminalToInTransitToClient():
        Assert:Equals("in_transit_to_client",
            oService:LabelTransition("available_in_terminal", "in_transit_to_client")).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID TransitionInTransitToClientToDelivered():
        Assert:Equals("delivered",
            oService:LabelTransition("in_transit_to_client", "delivered")).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID TransitionIdleBackToAvailable():
        Assert:Equals("available_in_stock",
            oService:LabelTransition("idle", "available_in_stock")).
    END METHOD.

    /* ── invalid transitions throw AppError ───────────────────────── */

    @Test.
    METHOD PUBLIC VOID InvalidTransitionAvailableToDelivered():
        DEFINE VARIABLE lThrew AS LOGICAL NO-UNDO INITIAL FALSE.
        DO ON ERROR UNDO, THROW:
            oService:LabelTransition("available_in_stock", "delivered").
        END.
        CATCH e AS AppError:
            lThrew = TRUE.
        END CATCH.
        Assert:IsTrue(lThrew).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID InvalidTransitionDeliveredToAny():
        DEFINE VARIABLE lThrew AS LOGICAL NO-UNDO INITIAL FALSE.
        DO ON ERROR UNDO, THROW:
            oService:LabelTransition("delivered", "available_in_stock").
        END.
        CATCH e AS AppError:
            lThrew = TRUE.
        END CATCH.
        Assert:IsTrue(lThrew).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID InvalidTransitionDamagedToAny():
        DEFINE VARIABLE lThrew AS LOGICAL NO-UNDO INITIAL FALSE.
        DO ON ERROR UNDO, THROW:
            oService:LabelTransition("damaged", "available_in_stock").
        END.
        CATCH e AS AppError:
            lThrew = TRUE.
        END CATCH.
        Assert:IsTrue(lThrew).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID UnknownFromStatusThrows():
        DEFINE VARIABLE lThrew AS LOGICAL NO-UNDO INITIAL FALSE.
        DO ON ERROR UNDO, THROW:
            oService:LabelTransition("nonexistent", "available_in_stock").
        END.
        CATCH e AS AppError:
            lThrew = TRUE.
        END CATCH.
        Assert:IsTrue(lThrew).
    END METHOD.

END CLASS.
