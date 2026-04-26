USING OpenEdge.Core.Assert FROM PROPATH.
USING business.LoadService  FROM PROPATH.
USING model.AppError        FROM PROPATH.

CLASS tests.unit.TestLoadService:

    DEFINE PRIVATE VARIABLE oService AS LoadService NO-UNDO.

    @Before.
    METHOD PUBLIC VOID Setup():
        oService = NEW LoadService().
    END METHOD.

    @After.
    METHOD PUBLIC VOID Teardown():
        DELETE OBJECT oService NO-ERROR.
    END METHOD.

    /* ── load status forward transitions ─────────────────────────── */

    @Test.
    METHOD PUBLIC VOID TransitionDraftToPending():
        Assert:Equals("pending",
            oService:LoadTransition("draft", "pending")).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID TransitionPendingToInTransit():
        Assert:Equals("in_transit",
            oService:LoadTransition("pending", "in_transit")).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID TransitionInTransitToDispatched():
        Assert:Equals("dispatched",
            oService:LoadTransition("in_transit", "dispatched")).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID TransitionDispatchedToDelivered():
        Assert:Equals("delivered",
            oService:LoadTransition("dispatched", "delivered")).
    END METHOD.

    /* ── cancellation from any non-terminal status ───────────────── */

    @Test.
    METHOD PUBLIC VOID CancelFromDraft():
        Assert:Equals("cancelled",
            oService:LoadTransition("draft", "cancelled")).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID CancelFromPending():
        Assert:Equals("cancelled",
            oService:LoadTransition("pending", "cancelled")).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID CancelFromInTransit():
        Assert:Equals("cancelled",
            oService:LoadTransition("in_transit", "cancelled")).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID CancelFromDispatched():
        Assert:Equals("cancelled",
            oService:LoadTransition("dispatched", "cancelled")).
    END METHOD.

    /* ── invalid transitions ─────────────────────────────────────── */

    @Test.
    METHOD PUBLIC VOID CannotTransitionDelivered():
        DEFINE VARIABLE lThrew AS LOGICAL NO-UNDO INITIAL FALSE.
        DO ON ERROR UNDO, THROW:
            oService:LoadTransition("delivered", "cancelled").
        END.
        CATCH e AS AppError:
            lThrew = TRUE.
        END CATCH.
        Assert:IsTrue(lThrew).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID CannotTransitionCancelled():
        DEFINE VARIABLE lThrew AS LOGICAL NO-UNDO INITIAL FALSE.
        DO ON ERROR UNDO, THROW:
            oService:LoadTransition("cancelled", "draft").
        END.
        CATCH e AS AppError:
            lThrew = TRUE.
        END CATCH.
        Assert:IsTrue(lThrew).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID CannotSkipToDispatched():
        DEFINE VARIABLE lThrew AS LOGICAL NO-UNDO INITIAL FALSE.
        DO ON ERROR UNDO, THROW:
            oService:LoadTransition("draft", "dispatched").
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
            oService:LoadTransition("nonexistent", "pending").
        END.
        CATCH e AS AppError:
            lThrew = TRUE.
        END CATCH.
        Assert:IsTrue(lThrew).
    END METHOD.

    /* ── weight validation ───────────────────────────────────────── */

    @Test.
    METHOD PUBLIC VOID WeightWithinCapacityIsValid():
        /* 25 t on a 27 t truck → valid */
        Assert:IsTrue(oService:WeightFits(25.000, 27.000)).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID WeightExactlyAtCapacityIsValid():
        Assert:IsTrue(oService:WeightFits(27.000, 27.000)).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID WeightExceedingCapacityIsInvalid():
        Assert:IsFalse(oService:WeightFits(27.001, 27.000)).
    END METHOD.

END CLASS.
