from app.core.constants import ActionType, Exchange, ConfidenceLevel, ImpactType

def test_action_types():
    assert ActionType.SPLIT == "SPLIT"
    assert ActionType.BONUS == "BONUS"
    assert ActionType.DIVIDEND == "DIVIDEND"

def test_exchanges():
    assert Exchange.NSE == "NSE"
    assert Exchange.BSE == "BSE"

def test_confidence_levels():
    assert ConfidenceLevel.HIGH == "HIGH"
    assert ConfidenceLevel.MEDIUM == "MEDIUM"
    assert ConfidenceLevel.LOW == "LOW"

def test_impact_types():
    assert ImpactType.STRUCTURAL == "STRUCTURAL"
    assert ImpactType.REALIZED == "REALIZED"
