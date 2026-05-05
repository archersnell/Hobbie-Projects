from commands.monitor import should_sell_position


def make_result(label="possible buy candidate", score=7, unrealized_plpc=2.0):
    return {
        "metrics": {
            "unrealized_plpc": unrealized_plpc,
        },
        "recommendation": {
            "label": label,
            "score": score,
        },
    }


def test_should_sell_when_loss_tolerance_is_hit():
    should_sell, reason = should_sell_position(
        result=make_result(unrealized_plpc=-6.0),
        loss_tolerance_pct=5.0,
        sell_on_watch=False,
    )

    assert should_sell
    assert "loss tolerance" in reason


def test_should_sell_when_research_says_avoid():
    should_sell, reason = should_sell_position(
        result=make_result(label="avoid", unrealized_plpc=1.0),
        loss_tolerance_pct=5.0,
        sell_on_watch=False,
    )

    assert should_sell
    assert "avoid" in reason


def test_should_only_sell_watch_when_enabled():
    assert not should_sell_position(
        result=make_result(label="watch", unrealized_plpc=1.0),
        loss_tolerance_pct=5.0,
        sell_on_watch=False,
    )[0]
    assert should_sell_position(
        result=make_result(label="watch", unrealized_plpc=1.0),
        loss_tolerance_pct=5.0,
        sell_on_watch=True,
    )[0]
