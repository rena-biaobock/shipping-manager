USING OpenEdge.Web.WebHandler                FROM PROPATH.
USING OpenEdge.Web.IWebRequest               FROM PROPATH.
USING OpenEdge.Core.Json.JsonConverter       FROM PROPATH.
USING Progress.Json.ObjectModel.JsonObject   FROM PROPATH.
USING Progress.Json.ObjectModel.JsonArray    FROM PROPATH.
USING Progress.Json.ObjectModel.JsonConstant FROM PROPATH.
USING business.LoadService                   FROM PROPATH.
USING data.LoadRepository                    FROM PROPATH.
USING data.LoadItemRepository                FROM PROPATH.
USING data.StockLabelRepository              FROM PROPATH.
USING model.AppError                         FROM PROPATH.

/*
 * Handles:
 *   GET    /api/v1/loads[?status=]
 *   GET    /api/v1/loads/:id
 *   GET    /api/v1/loads/:id/items
 *   POST   /api/v1/loads
 *   PATCH  /api/v1/loads/:id/status
 */
CLASS api.v1.LoadsHandler INHERITS WebHandler:

    METHOD OVERRIDE PROTECTED INTEGER HandleGet(INPUT poRequest AS IWebRequest):
        DEFINE VARIABLE pcId      AS CHARACTER NO-UNDO.
        DEFINE VARIABLE pcSegment AS CHARACTER NO-UNDO.
        DEFINE VARIABLE pcStatus  AS CHARACTER NO-UNDO.
        DEFINE VARIABLE oJson     AS JsonObject NO-UNDO.
        DEFINE VARIABLE oArray    AS JsonArray  NO-UNDO.

        DEFINE TEMP-TABLE ttLoad     NO-UNDO LIKE loads.
        DEFINE TEMP-TABLE ttItems    NO-UNDO LIKE load_items.

        pcId      = poRequest:GetPathParameter("id").
        pcSegment = poRequest:GetPathParameter("segment"). /* "items" sub-resource */

        IF pcId <> ? AND pcId <> "" THEN DO:
            DEFINE VARIABLE lFound AS LOGICAL NO-UNDO.
            lFound = NEW LoadRepository():FindById(pcId,
                         OUTPUT TABLE ttLoad BY-REFERENCE).
            IF NOT lFound THEN DO:
                THIS-OBJECT:StatusCode = 404.
                oJson = NEW JsonObject().
                oJson:Add("detail", "Load not found").
                THIS-OBJECT:WriteResponse(oJson:GetJsonText()).
                RETURN 0.
            END.

            /* /loads/:id/items */
            IF pcSegment = "items" THEN DO:
                NEW LoadItemRepository():ListByLoad(pcId,
                    OUTPUT TABLE ttItems BY-REFERENCE).
                oArray = LoadItemsToJson(TEMP-TABLE ttItems:HANDLE).
                THIS-OBJECT:WriteResponse(oArray:GetJsonText()).
                RETURN 0.
            END.

            THIS-OBJECT:WriteResponse(LoadToJson(TEMP-TABLE ttLoad:HANDLE):GetJsonText()).
            RETURN 0.
        END.

        /* /loads[?status=] */
        pcStatus = poRequest:GetQueryString("status").
        NEW LoadRepository():ListLoads(pcStatus, OUTPUT TABLE ttLoad BY-REFERENCE).
        oArray = NEW JsonArray().
        DEFINE VARIABLE hBuf AS HANDLE NO-UNDO.
        hBuf = TEMP-TABLE ttLoad:DEFAULT-BUFFER-HANDLE.
        hBuf:FIND-FIRST() NO-ERROR.
        DO WHILE hBuf:AVAILABLE:
            oArray:Add(LoadBufToJson(hBuf)).
            hBuf:FIND-NEXT() NO-ERROR.
        END.
        THIS-OBJECT:WriteResponse(oArray:GetJsonText()).
        RETURN 0.
    END METHOD.

    METHOD OVERRIDE PROTECTED INTEGER HandlePost(INPUT poRequest AS IWebRequest):
        DEFINE VARIABLE pcBody       AS LONGCHAR  NO-UNDO.
        DEFINE VARIABLE oBody        AS JsonObject NO-UNDO.
        DEFINE VARIABLE pcId         AS CHARACTER NO-UNDO.
        DEFINE VARIABLE pdCapacity   AS DECIMAL   NO-UNDO.
        DEFINE VARIABLE pcDest       AS CHARACTER NO-UNDO.
        DEFINE VARIABLE pcCustomer   AS CHARACTER NO-UNDO.
        DEFINE VARIABLE pcPlate      AS CHARACTER NO-UNDO.

        DEFINE TEMP-TABLE ttLoad NO-UNDO LIKE loads.

        poRequest:Body:ReadCharacters(OUTPUT pcBody, poRequest:ContentLength).
        oBody = CAST(JsonConverter:Parse(pcBody), JsonObject).

        pdCapacity = oBody:GetDecimal("truck_capacity_tons").
        pcDest     = oBody:GetCharacter("destination").
        pcCustomer = IF oBody:Has("customer") THEN oBody:GetCharacter("customer") ELSE ?.
        pcPlate    = IF oBody:Has("truck_plate") THEN oBody:GetCharacter("truck_plate") ELSE ?.

        pcId = NEW LoadRepository():CreateLoad(pdCapacity, pcDest, pcCustomer, pcPlate).

        NEW LoadRepository():FindById(pcId, OUTPUT TABLE ttLoad BY-REFERENCE).
        THIS-OBJECT:StatusCode = 201.
        THIS-OBJECT:WriteResponse(LoadToJson(TEMP-TABLE ttLoad:HANDLE):GetJsonText()).
        RETURN 0.
    END METHOD.

    METHOD OVERRIDE PROTECTED INTEGER HandlePatch(INPUT poRequest AS IWebRequest):
        DEFINE VARIABLE pcId        AS CHARACTER NO-UNDO.
        DEFINE VARIABLE pcNewStatus AS CHARACTER NO-UNDO.
        DEFINE VARIABLE pcBody      AS LONGCHAR  NO-UNDO.
        DEFINE VARIABLE oBody       AS JsonObject NO-UNDO.
        DEFINE VARIABLE oJson       AS JsonObject NO-UNDO.
        DEFINE VARIABLE lFound      AS LOGICAL    NO-UNDO.

        DEFINE TEMP-TABLE ttLoad NO-UNDO LIKE loads.

        pcId = poRequest:GetPathParameter("id").
        lFound = NEW LoadRepository():FindById(pcId, OUTPUT TABLE ttLoad BY-REFERENCE).
        IF NOT lFound THEN DO:
            THIS-OBJECT:StatusCode = 404.
            oJson = NEW JsonObject().
            oJson:Add("detail", "Load not found").
            THIS-OBJECT:WriteResponse(oJson:GetJsonText()).
            RETURN 0.
        END.

        poRequest:Body:ReadCharacters(OUTPUT pcBody, poRequest:ContentLength).
        oBody = CAST(JsonConverter:Parse(pcBody), JsonObject).
        pcNewStatus = oBody:GetCharacter("new_status").

        DO ON ERROR UNDO, THROW:
            NEW LoadService():LoadTransition(
                TEMP-TABLE ttLoad:DEFAULT-BUFFER-HANDLE:BUFFER-FIELD("status"):BUFFER-VALUE,
                pcNewStatus).
        END.
        CATCH e AS AppError:
            THIS-OBJECT:StatusCode = 422.
            oJson = NEW JsonObject().
            oJson:Add("detail", e:GetMessageText(0)).
            THIS-OBJECT:WriteResponse(oJson:GetJsonText()).
            RETURN 0.
        END CATCH.

        DEFINE VARIABLE oLoadRepo  AS LoadRepository        NO-UNDO.
        DEFINE VARIABLE oLabelRepo AS StockLabelRepository  NO-UNDO.
        oLoadRepo  = NEW LoadRepository().
        oLabelRepo = NEW StockLabelRepository().

        oLoadRepo:UpdateStatus(pcId, pcNewStatus).

        /* When a load is confirmed (pending), transition all its labels to in_load */
        IF pcNewStatus = "pending" THEN
            oLabelRepo:BulkUpdateStatus(pcId, "in_load").

        lFound = oLoadRepo:FindById(pcId, OUTPUT TABLE ttLoad BY-REFERENCE).
        THIS-OBJECT:WriteResponse(LoadToJson(TEMP-TABLE ttLoad:HANDLE):GetJsonText()).
        RETURN 0.
    END METHOD.

    /* ── serialization helpers ─────────────────────────────────── */

    METHOD PRIVATE JsonObject LoadToJson(INPUT phTable AS HANDLE):
        DEFINE VARIABLE hBuf AS HANDLE NO-UNDO.
        hBuf = phTable:DEFAULT-BUFFER-HANDLE.
        hBuf:FIND-FIRST() NO-ERROR.
        RETURN LoadBufToJson(hBuf).
    END METHOD.

    METHOD PRIVATE JsonObject LoadBufToJson(INPUT phBuf AS HANDLE):
        DEFINE VARIABLE oObj AS JsonObject NO-UNDO.
        oObj = NEW JsonObject().
        oObj:Add("id",                   phBuf:BUFFER-FIELD("id"):BUFFER-VALUE).
        oObj:Add("truck_capacity_tons",  DECIMAL(phBuf:BUFFER-FIELD("truck_capacity_tons"):BUFFER-VALUE)).
        oObj:Add("truck_plate",          NullableChar(phBuf, "truck_plate")).
        oObj:Add("status",               phBuf:BUFFER-FIELD("status"):BUFFER-VALUE).
        oObj:Add("destination",          NullableChar(phBuf, "destination")).
        oObj:Add("customer",             NullableChar(phBuf, "customer")).
        oObj:Add("total_weight_tons",    DECIMAL(phBuf:BUFFER-FIELD("total_weight_tons"):BUFFER-VALUE)).
        oObj:Add("created_at",           STRING(phBuf:BUFFER-FIELD("created_at"):BUFFER-VALUE)).
        oObj:Add("dispatched_at",        NullableDatetime(phBuf, "dispatched_at")).
        oObj:Add("delivered_at",         NullableDatetime(phBuf, "delivered_at")).
        RETURN oObj.
    END METHOD.

    METHOD PRIVATE JsonArray LoadItemsToJson(INPUT phTable AS HANDLE):
        DEFINE VARIABLE hBuf  AS HANDLE   NO-UNDO.
        DEFINE VARIABLE oArr  AS JsonArray NO-UNDO.
        DEFINE VARIABLE oItem AS JsonObject NO-UNDO.

        oArr = NEW JsonArray().
        hBuf = phTable:DEFAULT-BUFFER-HANDLE.
        hBuf:FIND-FIRST() NO-ERROR.

        DO WHILE hBuf:AVAILABLE:
            oItem = NEW JsonObject().
            oItem:Add("id",             hBuf:BUFFER-FIELD("id"):BUFFER-VALUE).
            oItem:Add("load_id",        hBuf:BUFFER-FIELD("load_id"):BUFFER-VALUE).
            oItem:Add("stock_label_id", hBuf:BUFFER-FIELD("stock_label_id"):BUFFER-VALUE).
            oArr:Add(oItem).
            hBuf:FIND-NEXT() NO-ERROR.
        END.
        RETURN oArr.
    END METHOD.

    METHOD PRIVATE Progress.Lang.Object NullableChar(INPUT phBuf AS HANDLE, INPUT pcField AS CHARACTER):
        DEFINE VARIABLE pcVal AS CHARACTER NO-UNDO.
        pcVal = phBuf:BUFFER-FIELD(pcField):BUFFER-VALUE.
        IF pcVal = ? THEN RETURN JsonConstant:NULL.
        RETURN pcVal.
    END METHOD.

    METHOD PRIVATE Progress.Lang.Object NullableDatetime(INPUT phBuf AS HANDLE, INPUT pcField AS CHARACTER):
        DEFINE VARIABLE dtVal AS DATETIME-TZ NO-UNDO.
        dtVal = phBuf:BUFFER-FIELD(pcField):BUFFER-VALUE.
        IF dtVal = ? THEN RETURN JsonConstant:NULL.
        RETURN STRING(dtVal).
    END METHOD.

END CLASS.
