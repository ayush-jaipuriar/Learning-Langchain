from .ir_models import IR


def quote_identifier(identifier: str) -> str:
    if identifier.startswith('"') and identifier.endswith('"'):
        return identifier
    return f'"{identifier}"'


def render_sql(ir: IR) -> str:
    select_parts = []
    for projection in ir.projections:
        if projection.alias:
            select_parts.append(f"{projection.expr} AS {quote_identifier(projection.alias)}")
        else:
            select_parts.append(projection.expr)

    select_clause = ", ".join(select_parts) if select_parts else "*"

    where_clause = ""
    if ir.filters:
        where_clause = " WHERE " + " AND ".join(filter_.expr for filter_ in ir.filters)

    group_clause = ""
    if ir.group_by:
        group_clause = " GROUP BY " + ", ".join(quote_identifier(expr) if expr.isidentifier() else expr for expr in ir.group_by)

    order_clause = ""
    if ir.order_by:
        order_clause = " ORDER BY " + ", ".join(
            f"{quote_identifier(order.expr) if order.expr.isidentifier() else order.expr} {order.direction}"
            for order in ir.order_by
        )

    limit_clause = f" LIMIT {ir.limit}" if ir.limit else ""

    return (
        f"SELECT {select_clause} FROM {quote_identifier(ir.table)}"
        f"{where_clause}{group_clause}{order_clause}{limit_clause};"
    )

