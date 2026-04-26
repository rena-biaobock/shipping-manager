CLASS model.AppError INHERITS Progress.Lang.AppError:

    CONSTRUCTOR PUBLIC AppError(INPUT pcMessage AS CHARACTER):
        SUPER().
        AddMessage(pcMessage, 0).
    END CONSTRUCTOR.

END CLASS.
