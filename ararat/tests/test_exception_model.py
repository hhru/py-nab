import pytest

from ararat.common.error import ErrorEnum, auto_error


class ErrorClass(ErrorEnum):
    Type1Error = auto_error()
    Type2Error = auto_error()


class OtherErrorClass(ErrorEnum):
    Type1Error = auto_error()


def test_catch_expected_exception():
    with pytest.raises(ErrorClass.Exception):
        raise ErrorClass.Type1Error.exception()

    with pytest.raises(ErrorClass.Type1Error.Exception):
        raise ErrorClass.Type1Error.exception()

    with pytest.raises(ErrorEnum.Exception):
        raise ErrorClass.Type1Error.exception()

    try:
        raise ErrorClass.Type1Error.exception()
    except ErrorClass.Type2Error.Exception:
        assert False
    except OtherErrorClass.Type1Error.Exception:
        assert False
    except ErrorClass.Type1Error.Exception:
        assert True
    except Exception:
        assert False
