from contextlib import contextmanager
from copy import copy
from typing import Callable, Optional, Any, Mapping

from fastapi import FastAPI

from ffapi.dep import wrap_by_lambda, DepsOverridesProvider


@contextmanager
def override_dependency(overrides: Mapping[Callable, Any], app: Optional[FastAPI] = None):
    overrides_lambda = {}
    for k, v in overrides.items():
        overrides_lambda[k] = wrap_by_lambda(v)

    if app:
        old_overrides = app.dependency_overrides
        new_overrides = copy(old_overrides)
        new_overrides.update(overrides_lambda)
        app.dependency_overrides = new_overrides

    provider_old_overrides = DepsOverridesProvider.default_overrides
    provider_new_overrides = copy(provider_old_overrides)
    provider_new_overrides.update(overrides_lambda)
    DepsOverridesProvider.default_overrides = provider_new_overrides

    yield app
    if app:
        app.dependency_overrides = old_overrides
    DepsOverridesProvider.default_overrides = provider_old_overrides
