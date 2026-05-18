from decimal import Decimal
from datetime import date
from app.corporate_actions.base import ActionResult, PortfolioState
from app.timeline.generator import TimelineGenerator
from app.timeline.renderer import TimelineRenderer

def test_timeline_generation_and_rendering():
    generator = TimelineGenerator()
    renderer = TimelineRenderer()
    
    # Setup some dummy ActionResult events
    # Event 1: Split (Structural)
    state1 = PortfolioState(
        date=date(2020, 2, 1),
        quantity=Decimal("200"),
        cost_basis_per_share=Decimal("5.00"),
        total_invested=Decimal("1000.00"),
        cumulative_dividends_received=Decimal("0.00")
    )
    res_split = ActionResult(
        new_state=state1,
        event_type="SPLIT",
        description="split 2:1",
        financial_impact=Decimal("0"),
        impact_type="STRUCTURAL"
    )
    
    # Event 2: Bonus (Structural)
    state2 = PortfolioState(
        date=date(2020, 3, 1),
        quantity=Decimal("400"),
        cost_basis_per_share=Decimal("2.50"),
        total_invested=Decimal("1000.00"),
        cumulative_dividends_received=Decimal("0.00")
    )
    res_bonus = ActionResult(
        new_state=state2,
        event_type="BONUS",
        description="bonus 1:1",
        financial_impact=Decimal("0"),
        impact_type="STRUCTURAL"
    )
    
    # Event 3: Dividend (Realized)
    state3 = PortfolioState(
        date=date(2020, 4, 1),
        quantity=Decimal("400"),
        cost_basis_per_share=Decimal("2.50"),
        total_invested=Decimal("1000.00"),
        cumulative_dividends_received=Decimal("1000.00")
    )
    res_div = ActionResult(
        new_state=state3,
        event_type="DIVIDEND",
        description="dividend 2.50 per share",
        financial_impact=Decimal("1000.00"),
        impact_type="REALIZED"
    )
    
    action_results = [res_split, res_bonus, res_div]
    
    raw_data = generator.generate(
        ticker="TEST",
        exchange="NSE",
        buy_date=date(2020, 1, 1),
        original_quantity=Decimal("100"),
        buy_price=Decimal("10.00"),
        current_price=Decimal("20.00"),
        action_results=action_results
    )
    
    # 1. Assert unrealized_gain_label equals exactly "if sold at current market price"
    assert raw_data["wealth_summary"]["unrealized_gain_label"] == "if sold at current market price"
    
    # 2. Assert first timeline entry event_type is BUY
    assert raw_data["timeline"][0]["event_type"] == "BUY"
    
    # 3. Assert cumulative_dividends is a running total per entry
    assert raw_data["timeline"][0]["cumulative_dividends"] == "0.0000"
    assert raw_data["timeline"][1]["cumulative_dividends"] == "0.0000"
    assert raw_data["timeline"][2]["cumulative_dividends"] == "0.0000"
    assert raw_data["timeline"][3]["cumulative_dividends"] == "1000.0000"
    
    # 4. Assert impact types are correct
    # Split impact_type is STRUCTURAL not REALIZED
    assert raw_data["timeline"][1]["event_type"] == "SPLIT"
    assert raw_data["timeline"][1]["impact_type"] == "STRUCTURAL"
    # Bonus impact_type is STRUCTURAL not REALIZED
    assert raw_data["timeline"][2]["event_type"] == "BONUS"
    assert raw_data["timeline"][2]["impact_type"] == "STRUCTURAL"
    # Dividend impact_type is REALIZED not STRUCTURAL
    assert raw_data["timeline"][3]["event_type"] == "DIVIDEND"
    assert raw_data["timeline"][3]["impact_type"] == "REALIZED"
    
    # Render with Pydantic and dump to check Pydantic schemas work flawlessly
    validated_dict = renderer.render_to_dict(raw_data)
    assert validated_dict["ticker"] == "TEST"
    assert validated_dict["exchange"] == "NSE"

def test_timeline_generation_no_actions():
    generator = TimelineGenerator()
    renderer = TimelineRenderer()
    
    raw_data = generator.generate(
        ticker="TEST",
        exchange="NSE",
        buy_date=date(2020, 1, 1),
        original_quantity=Decimal("100"),
        buy_price=Decimal("10.00"),
        current_price=Decimal("20.00"),
        action_results=[]
    )
    
    assert raw_data["ticker"] == "TEST"
    assert len(raw_data["timeline"]) == 1
    assert raw_data["timeline"][0]["event_type"] == "BUY"
    
    res = renderer.render_to_response(raw_data)
    assert res.ticker == "TEST"

    # Cover 0 investment branch
    raw_data_zero = generator.generate(
        ticker="TEST",
        exchange="NSE",
        buy_date=date(2020, 1, 1),
        original_quantity=Decimal("0"),
        buy_price=Decimal("10.00"),
        current_price=Decimal("20.00"),
        action_results=[]
    )
    assert raw_data_zero["wealth_summary"]["wealth_multiple"] == "0.00x"
