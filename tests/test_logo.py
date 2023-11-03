from panama._logo import get_logo

def test_logo():
    logo = get_logo()
    assert len(logo) > 500
    assert "v" in logo
