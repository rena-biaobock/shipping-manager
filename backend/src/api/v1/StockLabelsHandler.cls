USING OpenEdge.Web.WebHandler                FROM PROPATH.
USING OpenEdge.Web.IWebRequest               FROM PROPATH.
USING OpenEdge.Web.SendExceptionError        FROM PROPATH.
USING OpenEdge.Core.Json.JsonConverter       FROM PROPATH.
USING Progress.Json.ObjectModel.JsonObject   FROM PROPATH.
USING Progress.Json.ObjectModel.JsonArray    FROM PROPATH.
USING Progress.Json.ObjectModel.JsonConstant FROM PROPATH.
USING business.StockService                  FROM PROPATH.
USING data.StockLabelRepository              FROM PROPATH.
USING model.AppError                         FROM PROPATH.

/*
 * Handles:
 *   GET  /api/v1/stock-labels[?status=&warehouse=]
 *   GET  /api/v1/stock-labels/:progressivo
 *   PATCH /api/v1/stock-labels/:progressivo/status
 */
CLASS api.v1.StockLabelsHandler INHERITS WebHandler:

    METHOD OVERRIDE PROTECTED INTEGER HandleGet(INPUT poRequest AS IWebRequest):
        DEFINE VARIABLE pcProgressivo AS CHARACTER NO-UNDO.
        DEFINE VARIABLE pcStatus      AS CHARACTER NO-UNDO.
        DEFINE VARIABLE pcWarehouse   AS CHARACTER NO-UNDO.
        DEFINE VARIABLE oRepo         AS StockLabelRepository NO-UNDO.
        DEFINE VARIABLE oJson         AS JsonObject NO-UNDO.
        DEFINE VARIABLE oArray        AS JsonArray  NO-UNDO.
        DEFINE VARIABLE lFound        AS LOGICAL    NO-UNDO.

        DEFINE TEMP-TABLE ttResult NO-UNDO LIKE stock_labels.

        oRepo = NEW StockLabelRepository().

        /* /stock-labels/:progressivo */
        pcProgressivo = poRequest:GetPathParameter("progressivo").
        IF pcProgressivo <> ? AND pcProgressivo <> "" THEN DO:
            lFound = oRepo:FindByProgressivo(pcProgressivo,
                         OUTPUT TABLE ttResult BY-REFERENCE).
            IF NOT lFound THEN DO:
                THIS-OBJECT:StatusCode = 404.
                oJson = NEW JsonObject().
                oJson:Add("detail", "Label not found").
                THIS-OBJECT:WriteResponse(oJson:GetJsonText()).
                RETURN 0.
            END.
            THIS-OBJECT:WriteResponse(LabelToJson(TEMP-TABLE ttResult:HANDLE):GetJsonText()).
            RETURN 0.
        END.

        /* /stock-labels[?status=&warehouse=] */
        pcStatus    = poRequest:GetQueryString("status").
        pcWarehouse = poRequest:GetQueryString("warehouse").
        oRepo:ListLabels(pcStatus, pcWarehouse, OUTPUT TABLE ttResult BY-REFERENCE).

        oArray = LabelsToJsonArray(TEMP-TABLE ttResult:HANDLE).
        THIS-OBJECT:WriteResponse(oArray:GetJsonText()).
        RETURN 0.
    END METHOD.

    METHOD OVERRIDE PROTECTED INTEGER HandlePatch(INPUT poRequest AS IWebRequest):
        DEFINE VARIABLE pcProgressivo AS CHARACTER NO-UNDO.
        DEFINE VARIABLE pcNewStatus   AS CHARACTER NO-UNDO.
        DEFINE VARIABLE pcBody        AS LONGCHAR  NO-UNDO.
        DEFINE VARIABLE oBody         AS JsonObject NO-UNDO.
        DEFINE VARIABLE oSvc          AS StockService NO-UNDO.
        DEFINE VARIABLE oRepo         AS StockLabelRepository NO-UNDO.
        DEFINE VARIABLE oJson         AS JsonObject NO-UNDO.
        DEFINE VARIABLE lFound        AS LOGICAL    NO-UNDO.

        DEFINE TEMP-TABLE ttResult NO-UNDO LIKE stock_labels.

        pcProgressivo = poRequest:GetPathParameter("progressivo").
        oRepo = NEW StockLabelRepository().

        lFound = oRepo:FindByProgressivo(pcProgressivo,
                     OUTPUT TABLE ttResult BY-REFERENCE).
        IF NOT lFound THEN DO:
            THIS-OBJECT:StatusCode = 404.
            oJson = NEW JsonObject().
            oJson:Add("detail", "Label not found").
            THIS-OBJECT:WriteResponse(oJson:GetJsonText()).
            RETURN 0.
        END.

        /* Parse request body: {"new_status": "..."} */
        poRequest:Body:ReadCharacters(OUTPUT pcBody, poRequest:ContentLength).
        oBody = CAST(JsonConverter:Parse(pcBody), JsonObject).
        pcNewStatus = oBody:GetCharacter("new_status").

        /* Validate transition */
        oSvc = NEW StockService().
        DO ON ERROR UNDO, THROW:
            oSvc:LabelTransition(
                TEMP-TABLE ttResult:DEFAULT-BUFFER-HANDLE:BUFFER-FIELD("status"):BUFFER-VALUE,
                pcNewStatus).
        END.
        CATCH e AS AppError:
            THIS-OBJECT:StatusCode = 422.
            oJson = NEW JsonObject().
            oJson:Add("detail", e:GetMessageText(0)).
            THIS-OBJECT:WriteResponse(oJson:GetJsonText()).
            RETURN 0.
        END CATCH.

        oRepo:UpdateStatus(pcProgressivo, pcNewStatus).

        lFound = oRepo:FindByProgressivo(pcProgressivo,
                     OUTPUT TABLE ttResult BY-REFERENCE).
        THIS-OBJECT:WriteResponse(LabelToJson(TEMP-TABLE ttResult:HANDLE):GetJsonText()).
        RETURN 0.
    END METHOD.

    /* ── serialization helpers ─────────────────────────────────── */

    METHOD PRIVATE JsonObject LabelToJson(INPUT phTable AS HANDLE):
        DEFINE VARIABLE hBuf AS HANDLE    NO-UNDO.
        DEFINE VARIABLE oObj AS JsonObject NO-UNDO.

        hBuf = phTable:DEFAULT-BUFFER-HANDLE.
        hBuf:FIND-FIRST() NO-ERROR.
        oObj = BufferToJson(hBuf).
        RETURN oObj.
    END METHOD.

    METHOD PRIVATE JsonArray LabelsToJsonArray(INPUT phTable AS HANDLE):
        DEFINE VARIABLE hBuf  AS HANDLE   NO-UNDO.
        DEFINE VARIABLE oArr  AS JsonArray NO-UNDO.

        oArr = NEW JsonArray().
        hBuf = phTable:DEFAULT-BUFFER-HANDLE.
        hBuf:FIND-FIRST() NO-ERROR.

        DO WHILE hBuf:AVAILABLE:
            oArr:Add(BufferToJson(hBuf)).
            hBuf:FIND-NEXT() NO-ERROR.
        END.
        RETURN oArr.
    END METHOD.

    METHOD PRIVATE JsonObject BufferToJson(INPUT phBuf AS HANDLE):
        DEFINE VARIABLE oObj AS JsonObject NO-UNDO.
        oObj = NEW JsonObject().
        oObj:Add("progressivo",       phBuf:BUFFER-FIELD("progressivo"):BUFFER-VALUE).
        oObj:Add("item_code",         phBuf:BUFFER-FIELD("item_code"):BUFFER-VALUE).
        oObj:Add("description",       phBuf:BUFFER-FIELD("description"):BUFFER-VALUE).
        oObj:Add("customer_item_ref", NullableChar(phBuf, "customer_item_ref")).
        oObj:Add("actual_length_m",   NullableDecimal(phBuf, "actual_length_m")).
        oObj:Add("market_type",       phBuf:BUFFER-FIELD("market_type"):BUFFER-VALUE).
        oObj:Add("volume_tons",       DECIMAL(phBuf:BUFFER-FIELD("volume_tons"):BUFFER-VALUE)).
        oObj:Add("piece_count",       INTEGER(phBuf:BUFFER-FIELD("piece_count"):BUFFER-VALUE)).
        oObj:Add("status",            phBuf:BUFFER-FIELD("status"):BUFFER-VALUE).
        oObj:Add("order_number",      NullableChar(phBuf, "order_number")).
        oObj:Add("order_condition",   NullableChar(phBuf, "order_condition")).
        oObj:Add("country",           NullableChar(phBuf, "country")).
        oObj:Add("exit_date",         NullableChar(phBuf, "exit_date")).
        oObj:Add("embarque_id",       NullableChar(phBuf, "embarque_id")).
        oObj:Add("avg_days_idle",     NullableInt(phBuf, "avg_days_idle")).
        oObj:Add("is_standard_bundle",NullableBool(phBuf, "is_standard_bundle")).
        oObj:Add("warehouse_code",    NullableChar(phBuf, "warehouse_code")).
        oObj:Add("nf",                NullableChar(phBuf, "nf")).
        oObj:Add("invoice",           NullableChar(phBuf, "invoice")).
        RETURN oObj.
    END METHOD.

    METHOD PRIVATE JsonObject NullableChar(INPUT phBuf AS HANDLE, INPUT pcField AS CHARACTER):
        DEFINE VARIABLE pcVal AS CHARACTER NO-UNDO.
        pcVal = phBuf:BUFFER-FIELD(pcField):BUFFER-VALUE.
        IF pcVal = ? THEN RETURN JsonConstant:NULL.
        RETURN NEW JsonObject():Add(pcField, pcVal). /* wrapped to satisfy return type */
    END METHOD.

    /* Simplified null helpers — return JSON null or value */
    METHOD PRIVATE Progress.Lang.Object NullableDecimal(INPUT phBuf AS HANDLE, INPUT pcField AS CHARACTER):
        DEFINE VARIABLE pdVal AS DECIMAL NO-UNDO.
        pdVal = phBuf:BUFFER-FIELD(pcField):BUFFER-VALUE.
        IF pdVal = ? THEN RETURN JsonConstant:NULL.
        RETURN pdVal.
    END METHOD.

    METHOD PRIVATE Progress.Lang.Object NullableInt(INPUT phBuf AS HANDLE, INPUT pcField AS CHARACTER):
        DEFINE VARIABLE piVal AS INTEGER NO-UNDO.
        piVal = phBuf:BUFFER-FIELD(pcField):BUFFER-VALUE.
        IF piVal = ? THEN RETURN JsonConstant:NULL.
        RETURN piVal.
    END METHOD.

    METHOD PRIVATE Progress.Lang.Object NullableBool(INPUT phBuf AS HANDLE, INPUT pcField AS CHARACTER):
        DEFINE VARIABLE lVal AS LOGICAL NO-UNDO.
        lVal = phBuf:BUFFER-FIELD(pcField):BUFFER-VALUE.
        IF lVal = ? THEN RETURN JsonConstant:NULL.
        RETURN lVal.
    END METHOD.

END CLASS.
