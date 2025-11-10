"""LaTeX command handlers for grammafy.

This module provides the command interpretation system and built-in handlers
for common LaTeX commands. The interpret() function acts as a dispatcher,
routing commands to appropriate handlers based on command name.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from grammafy import Environment

logger = logging.getLogger(__name__)

# ----------------------------------------
# BUILT-IN FUNCTIONS
# ----------------------------------------


def _reprint(env) -> None:
    """add the command to env.clean the command"""
    env.clean.add(env.command)


def _curly(env) -> None:
    """move to the end of curly brackets"""
    env.source.move_index("}")


def _curly_curly(env) -> None:
    """move to the end for 2 consecutive curly brackets"""
    env.source.move_index("}")
    env.source.move_index("}")


def _color(env) -> None:
    """add color to env.source and move to the end of curly brackets"""
    env.clean.add("Color:")
    i = env.source.text.find("}")
    env.clean.add(env.source.text[1:i].upper())
    env.source.index += i + 1


def _footnote(env) -> None:
    """add footnote to env.source and move to the end of nested curly brackets"""
    i = 1
    j = i  # index for open brackets
    while i >= j and j > 0:
        i = env.source.text.find("}", i) + 1
        j = env.source.text.find("{", j) + 1

    # add the text in the footnote to the queue in parenthesis
    env.source.add("(FOOTNOTE: " + env.source.text[1 : i - 1] + ")")
    env.source.root.index += i


def _include(env) -> None:
    r"""Handle \include and \input commands for recursive file inclusion.

    Loads the specified file and pushes its content onto the source stack.
    Automatically appends .tex extension if missing. Skips .bbl bibliography files.

    Args:
        env: Processing environment
    """
    i = env.source.text.find("}")
    include_path_str = env.source.text[1:i]

    # Skip bibliography files
    if include_path_str.endswith(".bbl"):
        logger.debug("Skipping bibliography file: %s", include_path_str)
        env.source.index += i + 1
        return

    # Auto-append .tex extension
    if not include_path_str.endswith(".tex"):
        include_path_str += ".tex"

    # Resolve path relative to current folder
    include_path = env.folder_path / include_path_str

    try:
        # Check if file exists
        if not include_path.exists():
            logger.warning("Included file not found: %s", include_path)
            env.source.root.index += i + 1
            env.clean.add(f"[FILE NOT FOUND: {include_path_str}]")
            return

        # Load and push file content
        with open(include_path, encoding="utf-8") as include_tex:
            content = include_tex.read()
            env.source.add(content)
            logger.debug("Included file: %s (%d bytes)", include_path, len(content))

        env.source.root.index += i + 1

    except IOError as e:
        logger.error("Failed to read included file %s: %s", include_path, e)
        env.source.root.index += i + 1
        env.clean.add(f"[ERROR READING: {include_path_str}]")


def _print_curly(env) -> None:
    """[_] to env.clean when meeting curly brackets and move to the end of curly brackets"""
    env.clean.add("[_]")
    env.source.move_index("}")


def _print_square_curly(env) -> None:
    """add [_] for env.clean and move to the end of square if present, and then curly brackets"""
    env.clean.add("[_]")
    if env.source.text[0] == "[":
        env.source.move_index("]")
    env.source.move_index("}")


from exceptions import sub_begin


def _begin(env) -> None:
    """responds to the command being and move to the function begin and its subroutines"""
    i = env.source.text.find("}")  # right next after the brackets
    env.command = env.source.text[1:i]  # remove asterisk if any
    env.source.move_index("}")
    sub_begin.interpret(env)


from exceptions import sub_end


def _end(env) -> None:
    """responds to the command end and move to the function end and its subroutines"""
    i = env.source.text.find("}")
    env.command = env.source.text[1:i]
    env.source.move_index("}")
    sub_end.interpret(env)


# special commands (not include command to avoid string problems)


def _new_line(env) -> None:
    """add a new line to env.clean"""
    env.clean.add("\n")
    env.source.index += 1


def _square_equation(env) -> None:
    r"""add [_] when meeting an equation called via \[ and move index to the end if it"""
    i = env.source.text.find("\\]")
    env.clean.add("[_]")
    if env.source.text[:i].rstrip()[-1] in [
        ",",
        ";",
        ".",
    ]:  # add punctuation to non-inline equations
        env.clean.add(env.source.text[:i].rstrip()[-1])
    env.source.move_index("\\]")


def _round_equation(env) -> None:
    r"""add [_] when meeting an equation called via \( and move index to the end if it"""
    i = env.source.text.find("\\)")
    env.clean.add("[_]")
    if env.source.text[:i].rstrip()[-1] in [
        ",",
        ";",
        ".",
    ]:  # add punctuation to non-inline equations
        env.clean.add(env.source.text[:i].rstrip()[-1])
    env.source.move_index("\\)")


def _apostrofe(env) -> None:
    """skip letter when meeting an apostrofe"""
    if env.source.text[1] in ("a", "e", "i", "o", "u"):
        env.source.index += 1


def _tilde(env) -> None:
    """add tilde to env.clean"""
    env.clean.add("~")
    env.source.index += 1


def _null_function(env) -> None:
    """null function, does nothing"""


# ----------------------------------------
# VARIABLES
# ----------------------------------------

from .routines_custom import void_c

void = (
    "centering",
    "small",
    "large",
    "Large",
    "newpage",
    "textbf",
    "textit",
    "emph",
    "maketitle",
    "tableofcontents",
    "footnotesize",
    "selectfont",
    "author",
    "title",
    "date",
    "Huge",
    "huge",
    "underline",
    "chapter",
    "section",
    "subsection",
    "subsubsection",
    "section*",
    "subsection*",
    "subsubsection*",
    "text",
    "bbox",
    "clearpage",
    "appendix",
    "p",
    "S",
    "compat",
    "bf",
    "em",
    "printbibliography",
    "bigskip",
    "mbox",
    "preprint",
    "affiliation",
    "noindent",
    "texorpdfstring",
    "it",
    "address",
    "thanks",
    "textsc",
    "texttt",
)

from .routines_custom import dic_commands_c

dic_commands = {
    "addchap": _curly,
    "addsec": _curly,
    "begin": _begin,
    "bibliography": _curly,
    "bibliographystyle": _curly,
    "chaptermark": _curly,
    "cite": _print_square_curly,
    "color": _color,
    "cref": _print_curly,
    "Cref": _print_curly,
    "email": _curly,
    "end": _end,
    "eqref": _print_curly,
    "fontfamily": _curly,
    "footnote": _footnote,
    "hspace": _curly,
    "include": _include,
    "includegraphics": _curly,
    "input": _include,
    "label": _curly,
    "pagenumbering": _curly,
    "pagestyle": _curly,
    "ref": _print_curly,
    "renewcommand": _curly_curly,
    "setlength": _curly_curly,
    "thispagestyle": _curly,
    "vspace": _curly,
    "&": _reprint,
    "%": _reprint,
    "#": _reprint,
}

special_commands = {
    "[": _square_equation,
    "(": _round_equation,
    '"': _apostrofe,
    "'": _apostrofe,
    "\\": _new_line,
    "\n": _new_line,
    "~": _tilde,
}

# ----------------------------------------
# INTERPRETER
# ----------------------------------------


def interpret(env) -> None:
    """this is the custom interpreter that recalls first custom subroutines, then built-in subroutines and then skip the command if not recognised"""
    if env.command:
        if env.command in void or env.command in void_c:
            pass
        elif env.command in dic_commands_c:
            dic_commands_c[env.command](env)
        elif env.command in dic_commands:
            dic_commands[env.command](env)
        else:
            while env.source.text[0] in [
                "{",
                "[",
            ]:  # check if opening and closing brackets
                if env.source.text[0] == "{":
                    i = env.source.text.find("{", 1)
                    j = env.source.text.find("}", 1)
                    while 0 < i < j:
                        i = env.source.text.find("{", i + 1)
                        j = env.source.text.find("}", j + 1)
                    env.source.index += j + 1
                else:
                    i = env.source.text.find("[", 1)
                    j = env.source.text.find("]", 1)
                    while 0 < i < j:
                        i = env.source.text.find("[", i + 1)
                        j = env.source.text.find("]", j + 1)
                    env.source.index += j + 1
            env.clean.aggro.add(env.command)
    else:  # empty string
        env.command = env.source.text[0]
        if env.command in special_commands:
            special_commands[env.command](env)
        else:
            env.clean.add(" ")
            env.source.index += 1


# ----------------------------------------
