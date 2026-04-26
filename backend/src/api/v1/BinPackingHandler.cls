USING OpenEdge.Web.WebHandler                FROM PROPATH.
USING OpenEdge.Web.IWebRequest               FROM PROPATH.
USING OpenEdge.Core.Json.JsonConverter       FROM PROPATH.
USING Progress.Json.ObjectModel.JsonObject   FROM PROPATH.
USING Progress.Json.ObjectModel.JsonArray    FROM PROPATH.
USING business.BinPackingService             FROM PROPATH.
USING model.BinPackingModel                  FROM PROPATH.

/*
 * Handles:
 *   POST /api/v1/bin-packing/pack
 *
 * Request body:
 * {
 *   "truck_capacity_tons": 27,
 *   "max_iterations": null,          // optional
 *   "filters": {
 *     "warehouse_code": "2",         // optional
 *     "order_condition": "...",      // optional
 *     "country": "Paraguai"          // optional
 *   }
 * }
 */
CLASS api.v1.BinPackingHandler INHERITS WebHandler:

    METHOD OVERRIDE PROTECTED INTEGER HandlePost(INPUT poRequest AS IWebRequest):
        DEFINE VARIABLE pcBody       AS LONGCHAR  NO-UNDO.
        DEFINE VARIABLE oBody        AS JsonObject NO-UNDO.
        DEFINE VARIABLE oFilters     AS JsonObject NO-UNDO.
        DEFINE VARIABLE pdCapacity   AS DECIMAL   NO-UNDO.
        DEFINE VARIABLE piMaxIter    AS INTEGER   NO-UNDO.
        DEFINE VARIABLE pcWarehouse  AS CHARACTER NO-UNDO.
        DEFINE VARIABLE pcCondition  AS CHARACTER NO-UNDO.
        DEFINE VARIABLE pcCountry    AS CHARACTER NO-UNDO.
        DEFINE VARIABLE oPlan        AS BinPackingModel NO-UNDO.
        DEFINE VARIABLE oResponse    AS JsonObject NO-UNDO.
        DEFINE VARIABLE oItems       AS JsonArray  NO-UNDO.
        DEFINE VARIABLE oItem        AS JsonObject NO-UNDO.
        DEFINE VARIABLE hItemBuf     AS HANDLE    NO-UNDO.

        /* Load all available stock_labels into a temp-table for packing */
        DEFINE TEMP-TABLE ttLabels NO-UNDO
            FIELD progressivo     AS CHARACTER
            FIELD volume_tons     AS DECIMAL
            FIELD market_type     AS CHARACTER
            FIELD warehouse_code  AS CHARACTER
            FIELD order_condition AS CHARACTER
            FIELD country         AS CHARACTER
            FIELD exit_date       AS CHARACTER
            FIELD actual_length_m AS DECIMAL.

        /* Parse request */
        poRequest:Body:ReadCharacters(OUTPUT pcBody, poRequest:ContentLength).
        oBody = CAST(JsonConverter:Parse(pcBody), JsonObject).

        pdCapacity = oBody:GetDecimal("truck_capacity_tons").
        piMaxIter  = IF oBody:Has("max_iterations") AND NOT oBody:IsNull("max_iterations")
                     THEN oBody:GetInteger("max_iterations")
                     ELSE ?.

        IF oBody:Has("filters") AND NOT oBody:IsNull("filters") THEN DO:
            oFilters = oBody:GetJsonObject("filters").
            pcWarehouse = IF oFilters:Has("warehouse_code")  AND NOT oFilters:IsNull("warehouse_code")
                          THEN oFilters:GetCharacter("warehouse_code") ELSE ?.
            pcCondition = IF oFilters:Has("order_condition") AND NOT oFilters:IsNull("order_condition")
                          THEN oFilters:GetCharacter("order_condition") ELSE ?.
            pcCountry   = IF oFilters:Has("country")         AND NOT oFilters:IsNull("country")
                          THEN oFilters:GetCharacter("country") ELSE ?.
        END.

        /* Populate candidates from the stock_labels table */
        DEFINE BUFFER bLabel FOR stock_labels.
        FOR EACH bLabel NO-LOCK WHERE bLabel.status = "available_in_stock"
                                   OR bLabel.status = "reserved":
            CREATE ttLabels.
            ASSIGN
                ttLabels.progressivo     = bLabel.progressivo
                ttLabels.volume_tons     = bLabel.volume_tons
                ttLabels.market_type     = bLabel.market_type
                ttLabels.warehouse_code  = bLabel.warehouse_code
                ttLabels.order_condition = bLabel.order_condition
                ttLabels.country         = bLabel.country
                ttLabels.exit_date       = bLabel.exit_date
                ttLabels.actual_length_m = bLabel.actual_length_m.
        END.

        /* Run FFD packing */
        oPlan = NEW BinPackingService():Pack(
                    TEMP-TABLE ttLabels:HANDLE,
                    pdCapacity, piMaxIter,
                    pcWarehouse, pcCondition, pcCountry).

        /* Serialize response */
        oItems   = NEW JsonArray().
        hItemBuf = oPlan:ttItems:DEFAULT-BUFFER-HANDLE.
        hItemBuf:FIND-FIRST() NO-ERROR.
        DO WHILE hItemBuf:AVAILABLE:
            oItem = NEW JsonObject().
            oItem:Add("progressivo",
                      hItemBuf:BUFFER-FIELD("progressivo"):BUFFER-VALUE).
            oItem:Add("volume_tons",
                      DECIMAL(hItemBuf:BUFFER-FIELD("volume_tons"):BUFFER-VALUE)).
            oItems:Add(oItem).
            hItemBuf:FIND-NEXT() NO-ERROR.
        END.

        oResponse = NEW JsonObject().
        oResponse:Add("items",              oItems).
        oResponse:Add("total_weight_tons",  oPlan:TotalWeightTons).
        oResponse:Add("partial",            oPlan:Partial).

        THIS-OBJECT:WriteResponse(oResponse:GetJsonText()).
        RETURN 0.
    END METHOD.

END CLASS.
