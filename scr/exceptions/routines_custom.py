"""custom routines"""

# ----------------------------------------
# FUNCTIONS
# ----------------------------------------


def _print_curly(env) -> None:
    """add [_] to CLEAN when meeting curly brackets and move to the end of curly brackets"""
    env.clean.add("[_]")
    env.source.move_index("}")


def _print_square_curly(env) -> None:
    """add [_] for CLEAN and move to the end of square if present, and then curly brackets"""
    env.clean.add("[_]")
    if env.source.text[0] == "[":
        env.source.move_index("]")
    env.source.move_index("}")


# ----------------------------------------
# VARIABLES
# ----------------------------------------

dic_commands_c = {
    # Original custom commands
    "citep": _print_curly,
    "eqrefp": _print_curly,
    "refp": _print_curly,
    # Citation commands - replace with [_]
    "parencite": _print_square_curly,  # \parencite[prenote][postnote]{key}
}

void_c = (
    # Original void commands
    "marker",
    "bookmark",
    # Font size commands - just remove
    "LARGE",
    "normalsize",
    # Font style commands - just remove
    "bfseries",
    # Bibliography commands - just remove
    "nocite",
    # Layout commands - just remove
    "rule",
    "vfill",
)


# TEMPLATE
# dic_commands_c = {
#     "{name_command}" : "_{name_function}",
# }
