from almatest.check_ruff import check_ruff


def test_ruff(request) -> None:
    check_ruff(root=request.config.rootpath, paths=["almatest", "tests"])
