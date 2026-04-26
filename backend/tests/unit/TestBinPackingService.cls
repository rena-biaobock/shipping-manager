USING OpenEdge.Core.Assert      FROM PROPATH.
USING business.BinPackingService FROM PROPATH.
USING model.BinPackingModel      FROM PROPATH.

CLASS tests.unit.TestBinPackingService:

    DEFINE PRIVATE VARIABLE oService AS BinPackingService NO-UNDO.

    /* Shared temp-table used as input across tests */
    DEFINE PRIVATE TEMP-TABLE ttLabel NO-UNDO
        FIELD progressivo    AS CHARACTER
        FIELD volume_tons    AS DECIMAL
        FIELD market_type    AS CHARACTER
        FIELD warehouse_code AS CHARACTER
        FIELD order_condition AS CHARACTER
        FIELD country        AS CHARACTER
        FIELD exit_date      AS CHARACTER  /* ISO date or ? */
        FIELD actual_length_m AS DECIMAL.

    @Before.
    METHOD PUBLIC VOID Setup():
        oService = NEW BinPackingService().
        EMPTY TEMP-TABLE ttLabel.
    END METHOD.

    @After.
    METHOD PUBLIC VOID Teardown():
        DELETE OBJECT oService NO-ERROR.
    END METHOD.

    /* ── helpers ─────────────────────────────────────────────────── */

    METHOD PRIVATE VOID AddLabel(
        INPUT pcProgressivo   AS CHARACTER,
        INPUT pdVolume        AS DECIMAL,
        INPUT pcMarketType    AS CHARACTER,
        INPUT pcWarehouse     AS CHARACTER,
        INPUT pcCondition     AS CHARACTER,
        INPUT pcCountry       AS CHARACTER
    ):
        CREATE ttLabel.
        ASSIGN
            ttLabel.progressivo    = pcProgressivo
            ttLabel.volume_tons    = pdVolume
            ttLabel.market_type    = pcMarketType
            ttLabel.warehouse_code = pcWarehouse
            ttLabel.order_condition = pcCondition
            ttLabel.country        = pcCountry
            ttLabel.exit_date      = ?
            ttLabel.actual_length_m = ?.
    END METHOD.

    /* ── pack fills truck without exceeding capacity ─────────────── */

    @Test.
    METHOD PUBLIC VOID PackFitsLabelsUnderCapacity():
        AddLabel("A001", 10.0, "ME", "2", "pedido_ate_hoje", "Paraguai").
        AddLabel("A002",  8.0, "ME", "2", "pedido_ate_hoje", "Paraguai").
        AddLabel("A003",  5.0, "ME", "2", "pedido_ate_hoje", "Paraguai").

        DEFINE VARIABLE oPlan AS BinPackingModel NO-UNDO.
        oPlan = oService:Pack(TEMP-TABLE ttLabel:HANDLE, 27.0, ?, ?, ?, ?).

        Assert:IsTrue(oPlan:TotalWeightTons <= 27.0).
        Assert:IsFalse(oPlan:Partial).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID PackUsesFFDOrder():
        /* FFD — largest first.  10 + 8 = 18, capacity 20 → both fit.
           3 does not push over, so all 3 fit (18 + 3 = 21 > 20, 3rd must be left out). */
        AddLabel("A001",  3.0, "ME", "2", "pedido_ate_hoje", "Paraguai").
        AddLabel("A002", 10.0, "ME", "2", "pedido_ate_hoje", "Paraguai").
        AddLabel("A003",  8.0, "ME", "2", "pedido_ate_hoje", "Paraguai").

        DEFINE VARIABLE oPlan AS BinPackingModel NO-UNDO.
        oPlan = oService:Pack(TEMP-TABLE ttLabel:HANDLE, 18.0, ?, ?, ?, ?).

        /* 10 + 8 = 18 exactly; 3 t label is left out */
        Assert:Equals(18.0, oPlan:TotalWeightTons).
        Assert:IsFalse(oPlan:Partial).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID PackSetsPartialWhenMaxIterationsHit():
        AddLabel("A001", 5.0, "ME", "2", "pedido_ate_hoje", "Paraguai").
        AddLabel("A002", 5.0, "ME", "2", "pedido_ate_hoje", "Paraguai").
        AddLabel("A003", 5.0, "ME", "2", "pedido_ate_hoje", "Paraguai").

        DEFINE VARIABLE oPlan AS BinPackingModel NO-UNDO.
        /* cap at 1 iteration so only first label is evaluated */
        oPlan = oService:Pack(TEMP-TABLE ttLabel:HANDLE, 27.0, 1, ?, ?, ?).

        Assert:IsTrue(oPlan:Partial).
    END METHOD.

    /* ── filters ─────────────────────────────────────────────────── */

    @Test.
    METHOD PUBLIC VOID PackFiltersToWarehouse():
        AddLabel("A001", 10.0, "ME", "2",   "pedido_ate_hoje", "Paraguai").
        AddLabel("A002",  8.0, "ME", "B08", "pedido_ate_hoje", "Paraguai").

        DEFINE VARIABLE oPlan AS BinPackingModel NO-UNDO.
        oPlan = oService:Pack(TEMP-TABLE ttLabel:HANDLE, 27.0, ?, "2", ?, ?).

        Assert:Equals(10.0, oPlan:TotalWeightTons).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID PackFiltersToCountry():
        AddLabel("A001", 10.0, "ME", "2", "pedido_ate_hoje", "Paraguai").
        AddLabel("A002",  8.0, "ME", "2", "pedido_ate_hoje", "Bolivia").

        DEFINE VARIABLE oPlan AS BinPackingModel NO-UNDO.
        oPlan = oService:Pack(TEMP-TABLE ttLabel:HANDLE, 27.0, ?, ?, ?, "Paraguai").

        Assert:Equals(10.0, oPlan:TotalWeightTons).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID PackFiltersToOrderCondition():
        AddLabel("A001", 10.0, "ME", "2", "pedido_ate_hoje",  "Paraguai").
        AddLabel("A002",  8.0, "ME", "2", "antecipa_futuro",  "Paraguai").

        DEFINE VARIABLE oPlan AS BinPackingModel NO-UNDO.
        oPlan = oService:Pack(TEMP-TABLE ttLabel:HANDLE, 27.0, ?, ?, "pedido_ate_hoje", ?).

        Assert:Equals(10.0, oPlan:TotalWeightTons).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID PackExcludesMILabels():
        AddLabel("A001", 10.0, "ME", "2", "pedido_ate_hoje", "Paraguai").
        AddLabel("A002",  8.0, "MI", "2", "pedido_ate_hoje", "Brasil").

        DEFINE VARIABLE oPlan AS BinPackingModel NO-UNDO.
        oPlan = oService:Pack(TEMP-TABLE ttLabel:HANDLE, 27.0, ?, ?, ?, ?).

        /* MI label is excluded — only 10 t packed */
        Assert:Equals(10.0, oPlan:TotalWeightTons).
    END METHOD.

    @Test.
    METHOD PUBLIC VOID PackEmptyInputReturnsZero():
        DEFINE VARIABLE oPlan AS BinPackingModel NO-UNDO.
        oPlan = oService:Pack(TEMP-TABLE ttLabel:HANDLE, 27.0, ?, ?, ?, ?).

        Assert:Equals(0.0, oPlan:TotalWeightTons).
        Assert:IsFalse(oPlan:Partial).
    END METHOD.

END CLASS.
