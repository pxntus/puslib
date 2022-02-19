from puslib.ident import PusIdent


def test_ident():
    ident = PusIdent(1)
    assert ident.apid == 1
    assert ident.seq_count() == 0

    for _ in range(2 ** 14 - 2):
        ident.seq_count()
    assert ident.seq_count() == 16383
    assert ident.seq_count() == 0
