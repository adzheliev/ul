"""SQL script splitting keeps comment semicolons out of statements."""

from etl.sql_exec import statements


def test_comment_semicolon_is_not_a_statement_boundary():
    script = """
    -- dq.quarantine_prices; the view below is the spec alias.
    CREATE TABLE example (id int);
    """
    parsed = statements(script)
    assert parsed == ["CREATE TABLE example (id int)"]
