def test_api_imports():
    # Smoke test: importing the API module should succeed when deps are installed.
    import imessage_analysis.api  # noqa: F401
