from __future__ import annotations
from enum import Enum
from typing import Generic, Any, TypeVar

T = TypeVar("T", bound=Enum)


class _ExceptionWithErrorAndData(Exception, Generic[T]):
    def __init__(self, error: T, data: Any = None):
        self.error = error
        self.data = data


class _class_or_instancemethod(classmethod):
    def __get__(self, instance, type_):
        descr_get = super().__get__ if instance is None else self.__func__.__get__
        return descr_get(instance, type_)


class ErrorEnum(Enum):
    @_class_or_instancemethod
    @property
    def Exception(self_or_cls) -> type[_ExceptionWithErrorAndData["Self"]]:
        if self_or_cls is ErrorEnum:
            return _ExceptionWithErrorAndData

        if isinstance(self_or_cls, type):
            if not hasattr(self_or_cls, "_exception_class"):
                self_or_cls._exception_class = type(
                    self_or_cls.__name__ + "Exception",
                    (_ExceptionWithErrorAndData,),
                    {},
                )
            return self_or_cls._exception_class

        if not hasattr(self_or_cls, "_exception_class_instance"):
            self_or_cls._exception_class_instance = type(
                self_or_cls.name + "Exception",
                (self_or_cls.__class__.Exception,),
                {},
            )
        return self_or_cls._exception_class_instance

    def exception(self, data=None) -> _ExceptionWithErrorAndData:
        return self.Exception(self, data)


class ErrorValue:
    def __init__(self, default_response_code: int):
        self.default_response_code = default_response_code


def auto_error(default_response_code: int = 400):
    return ErrorValue(default_response_code=default_response_code)
