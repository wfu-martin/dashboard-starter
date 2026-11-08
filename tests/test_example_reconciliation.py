"""Worked example of a reconciliation test, on vinyl_vault.

A reconciliation test proves a number on screen is right by computing the
same number a second, independent way and checking that the two agree.
Here the screen adds revenue up from invoice lines; the check adds up the
invoice totals instead, a different table.

Write one of these for every figure your dashboard shows, before you build it.
In your project, start each test's name with the acceptance criterion it
proves, for example `test_ac3_revenue_reconciles_to_invoices`.
"""

from conftest import scalar
from dashboard.metrics import revenue_by_genre


def test_genre_revenue_reconciles_to_invoices(vinyl_vault_engine):
    on_screen = revenue_by_genre(vinyl_vault_engine)["revenue"].sum()
    independent = scalar(vinyl_vault_engine, "SELECT SUM(total) FROM invoice")
    assert round(float(on_screen), 2) == round(float(independent), 2)


def test_each_genre_appears_once(vinyl_vault_engine):
    # A join that repeats rows would list a genre twice and inflate revenue.
    genres = revenue_by_genre(vinyl_vault_engine)["genre"]
    assert genres.is_unique
