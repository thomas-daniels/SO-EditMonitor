from restrictedmode import RestrictedMode
import rejectionreasons


def test_restrictedmode_all():
    mode = RestrictedMode(63)
    assert mode.should_report(rejectionreasons.vandalism)
    assert mode.should_report(rejectionreasons.no_improvement)
    assert mode.should_report(rejectionreasons.irrelevant_tags)
    assert mode.should_report(rejectionreasons.intent_conflict)
    assert mode.should_report(rejectionreasons.reply)
    assert mode.should_report("This is a custom reason.")


def test_restrictedmode_all_except_noimprovement():
    mode = RestrictedMode(47)
    assert mode.should_report(rejectionreasons.vandalism)
    assert not mode.should_report(rejectionreasons.no_improvement)
    assert mode.should_report(rejectionreasons.irrelevant_tags)
    assert mode.should_report(rejectionreasons.intent_conflict)
    assert mode.should_report(rejectionreasons.reply)
    assert mode.should_report("This is a custom reason.")


def test_restrictedmode_only_custom():
    mode = RestrictedMode(1)
    assert not mode.should_report(rejectionreasons.vandalism)
    assert not mode.should_report(rejectionreasons.no_improvement)
    assert not mode.should_report(rejectionreasons.irrelevant_tags)
    assert not mode.should_report(rejectionreasons.intent_conflict)
    assert not mode.should_report(rejectionreasons.reply)
    assert mode.should_report("This is a custom reason.")

