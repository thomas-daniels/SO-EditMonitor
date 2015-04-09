from checkspam import check_spam

def test_checkspam():
    assert len(check_spam('<a href="http://example.com">something</a>')) > 0
    assert len(check_spam('<a href="https://example.com">something</a>')) > 0
    assert len(check_spam('Non-spammy summary')) == 0