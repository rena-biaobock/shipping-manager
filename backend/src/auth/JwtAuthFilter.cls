USING OpenEdge.Web.IWebRequest     FROM PROPATH.
USING OpenEdge.Web.IWebResponse    FROM PROPATH.
USING OpenEdge.Web.IWebAuthFilter  FROM PROPATH.
USING Progress.Json.ObjectModel.*  FROM PROPATH.
USING OpenEdge.Core.Json.JsonConverter FROM PROPATH.

/*
 * Validates a Bearer JWT on every request before it reaches a handler.
 * The secret and expiry are read from openedge.properties:
 *   shipping.jwt.secret=<value>
 *   shipping.jwt.expire-minutes=60
 *
 * Validation steps:
 *   1. Extract "Authorization: Bearer <token>" header.
 *   2. Split token into header.payload.signature (base64url).
 *   3. Verify HMAC-SHA256(secret, header.payload) == signature.
 *   4. Verify exp claim has not passed.
 *
 * Note: ABL does not ship a SHA-256 HMAC primitive in the standard library.
 * Use OpenEdge.Security.* (OE 12.4+) or delegate to a Java class via JNI.
 * The skeleton below documents the integration point; implement the HMAC
 * call against the available OE version in the target environment.
 */
CLASS auth.JwtAuthFilter IMPLEMENTS IWebAuthFilter:

    DEFINE PRIVATE VARIABLE pcSecret AS CHARACTER NO-UNDO.

    CONSTRUCTOR PUBLIC JwtAuthFilter():
        /* Read secret from PROPATH-accessible properties */
        pcSecret = OS-GETENV("SHIPPING_JWT_SECRET").
        IF pcSecret = ? OR pcSecret = "" THEN
            pcSecret = "changeme".
    END CONSTRUCTOR.

    METHOD PUBLIC LOGICAL Authenticate(
        INPUT  poRequest  AS IWebRequest,
        OUTPUT poResponse AS IWebResponse
    ):
        DEFINE VARIABLE pcHeader AS CHARACTER NO-UNDO.
        DEFINE VARIABLE pcToken  AS CHARACTER NO-UNDO.
        DEFINE VARIABLE pcParts  AS CHARACTER EXTENT 3 NO-UNDO.

        pcHeader = poRequest:GetHeader("Authorization").

        IF pcHeader = ? OR NOT pcHeader BEGINS "Bearer " THEN DO:
            poResponse:StatusCode = 401.
            poResponse:SetHeader("WWW-Authenticate", "Bearer").
            RETURN FALSE.
        END.

        pcToken = SUBSTRING(pcHeader, 8). /* strip "Bearer " */

        /* Split into [header, payload, signature] */
        IF NUM-ENTRIES(pcToken, ".") <> 3 THEN DO:
            poResponse:StatusCode = 401.
            RETURN FALSE.
        END.
        pcParts[1] = ENTRY(1, pcToken, ".").
        pcParts[2] = ENTRY(2, pcToken, ".").
        pcParts[3] = ENTRY(3, pcToken, ".").

        /* Signature verification — integration point for HMAC-SHA256 */
        IF NOT VerifySignature(pcParts[1] + "." + pcParts[2], pcParts[3]) THEN DO:
            poResponse:StatusCode = 401.
            RETURN FALSE.
        END.

        /* Expiry check */
        IF NOT VerifyExpiry(BASE64-DECODE(pcParts[2])) THEN DO:
            poResponse:StatusCode = 401.
            RETURN FALSE.
        END.

        RETURN TRUE.
    END METHOD.

    /* ── private helpers ─────────────────────────────────────────── */

    /*
     * VerifySignature — compute HMAC-SHA256(secret, pcData) and
     * compare to pcSignature (base64url-encoded).
     * Replace the stub RETURN TRUE with the real HMAC call.
     */
    METHOD PRIVATE LOGICAL VerifySignature(
        INPUT pcData      AS CHARACTER,
        INPUT pcSignature AS CHARACTER
    ):
        /* TODO: call OpenEdge.Security.MessageDigest or a Java helper */
        RETURN TRUE. /* stub — implement per target OE version */
    END METHOD.

    /*
     * VerifyExpiry — decode the payload JSON and check "exp" > NOW.
     */
    METHOD PRIVATE LOGICAL VerifyExpiry(INPUT pcPayload AS CHARACTER):
        DEFINE VARIABLE oJson  AS JsonObject  NO-UNDO.
        DEFINE VARIABLE piExp  AS INTEGER     NO-UNDO.
        DEFINE VARIABLE piNow  AS INTEGER     NO-UNDO.

        DO ON ERROR UNDO, RETURN FALSE:
            oJson = CAST(JsonConverter:Parse(pcPayload), JsonObject).
            piExp = oJson:GetInteger("exp").
            /* Unix epoch seconds */
            piNow = INTEGER((NOW - DATETIME-TZ(1970, 1, 1, 0, 0, 0, 0, 0)) / 1000).
            RETURN piExp > piNow.
        END.
        RETURN FALSE.
    END METHOD.

END CLASS.
