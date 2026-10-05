from cinerocket.llm.catalog import FALLBACK_ROUTER, select_available

CONFIGURED = ["vendor/fast:free", "vendor/removed:free", "openrouter/free"]


def test_drops_models_missing_from_catalog_but_keeps_routers() -> None:
    assert select_available(CONFIGURED, frozenset({"vendor/fast:free"})) == [
        "vendor/fast:free",
        "openrouter/free",
    ]


def test_keeps_configuration_when_catalog_is_unreachable() -> None:
    assert select_available(CONFIGURED, None) == CONFIGURED


def test_falls_back_to_free_router_when_nothing_survives() -> None:
    assert select_available(["vendor/removed:free"], frozenset()) == [FALLBACK_ROUTER]
