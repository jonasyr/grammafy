"""custom begin routines"""

# ----------------------------------------
# FUNCTIONS
# ----------------------------------------


def _title(env) -> None:
    """add title to CLEAN"""
    env.clean.add(env.command.title() + ".")


def _thm(env) -> None:
    """add theorem to CLEAN"""
    env.clean.add("Theorem.")


def _equation(env) -> None:
    """add [_] and move to the end of the equation command"""
    env.clean.add("[_]")
    # find the index where the whole portion ends
    i = env.source.text.find("\\end{" + env.command + "}")
    if i > 0 and env.source.text[: i - 1].rstrip() and env.source.text[: i - 1].rstrip()[-1] in [",", ";", "."]:
        env.clean.add(env.source.text[: i - 1].rstrip()[-1])
    env.source.move_index("\\end{" + env.command + "}")


# ----------------------------------------
# VARIABLES
# ----------------------------------------

dic_commands_c = {
    # Original custom environments
    "assumption": _title,
    "example": _title,
    "exercise": _title,
    "thm": _thm,
    # Table environments - replace with [_]
    "tabularx": _equation,
}

# Transparent environments (preserve content)
void_c = (
    "quote",      # Quotation environment - preserve text
    "tcolorbox",  # Colored box - preserve text
)

# TEMPLATE
# dic_commands_c = {
#     "{name_command}": {name_function},
# }
