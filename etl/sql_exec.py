"""Run SQL files with optional psycopg parameters."""

from pathlib import Path

from psycopg import Connection


def statements(sql: str) -> list[str]:
    """Split a script on semicolons after removing SQL line comments.

    Semicolons inside ``--`` comments are ignored. The warehouse scripts do not
    use semicolons inside string literals or function bodies.
    """

    stripped = _strip_line_comments(sql)
    return [part.strip() for part in stripped.split(";") if part.strip()]


def _strip_line_comments(sql: str) -> str:
    lines: list[str] = []
    for line in sql.splitlines():
        in_string = False
        index = 0
        kept: list[str] = []
        while index < len(line):
            character = line[index]
            if character == "'":
                in_string = not in_string
                kept.append(character)
            elif character == "-" and not in_string and line[index : index + 2] == "--":
                break
            else:
                kept.append(character)
            index += 1
        lines.append("".join(kept))
    return "\n".join(lines)


def execute_sql(conn: Connection, sql: str, params: dict | None = None) -> None:
    """Execute every statement in one connection."""

    with conn.cursor() as cursor:
        for statement in statements(sql):
            if params and "%(" in statement:
                cursor.execute(statement, params)
            else:
                cursor.execute(statement)


def execute_file(conn: Connection, path: Path, params: dict | None = None) -> None:
    """Execute a SQL file from the repository."""

    execute_sql(conn, path.read_text(encoding="utf-8"), params)
