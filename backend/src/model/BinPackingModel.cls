CLASS model.BinPackingModel:

    DEFINE PUBLIC PROPERTY TotalWeightTons AS DECIMAL  NO-UNDO GET. SET.
    DEFINE PUBLIC PROPERTY Partial         AS LOGICAL  NO-UNDO GET. SET.

    /* Items packed into this plan */
    DEFINE PUBLIC TEMP-TABLE ttItems NO-UNDO
        FIELD progressivo AS CHARACTER
        FIELD volume_tons AS DECIMAL.

    CONSTRUCTOR PUBLIC BinPackingModel():
        ASSIGN
            TotalWeightTons = 0.0
            Partial         = FALSE.
    END CONSTRUCTOR.

END CLASS.
