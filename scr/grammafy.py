"""Grammafy - LaTeX to clean text converter.

This module provides the main entry point and orchestration logic for converting
LaTeX documents to clean text suitable for grammar checking tools like Grammarly.
"""

import sys
import argparse
import re
import logging
from pathlib import Path
from typing import Optional

from classes import Source, Clean
from exceptions import interpret

try:
    import pyle_manager  # type: ignore
    HAS_FILE_PICKER = True
except ImportError:
    HAS_FILE_PICKER = False
    logging.warning("File picker not available - pyle_manager import failed")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class Environment:
    """Global state container for LaTeX processing.

    This class holds all the state needed during LaTeX processing, including
    the source text stack, output accumulator, file path information, and
    current command being processed.

    Attributes:
        source: Stack-based source text manager
        clean: Output text accumulator
        folder_path: Directory path for resolving relative includes
        command: Current LaTeX command being processed
    """

    def __init__(self, file_path: Path) -> None:
        """Initialize environment from LaTeX file.

        Args:
            file_path: Path to the main LaTeX file

        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read
        """
        if not file_path.exists():
            raise FileNotFoundError(f"LaTeX file not found: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as source_file:
                self.source = Source(source_file.read())
        except IOError as e:
            raise IOError(f"Failed to read file {file_path}: {e}") from e

        self.clean = Clean()
        self.folder_path = file_path.parent
        self.command = ""

        logger.info("Initialized environment from: %s", file_path)


# Command name terminators - characters that end a LaTeX command name
COMMAND_TERMINATORS = (
    " ", "{", "}", ".", ",", ":", ";", "[", "]", "(", ")",
    "$", "\\", "\n", '"', "'", "~"
)

# Compiled regex patterns (for performance)
REGEX_PATTERNS = {
    'trailing_spaces': re.compile(r"( )*\n( )*"),
    'excess_newlines': re.compile(r"\n\n\s*"),
    'double_spacing': re.compile(r"( )+"),
    'equation_before': re.compile(r"(\S)\n?(?<!-)\[_\]"),
    'equation_after': re.compile(r"\[_\](\.|,|;)?\n(?!(?:\d+\.|-))(\S)"),
}


def select_file(file_path: Optional[str] = None) -> Path:
    """Select LaTeX file interactively or validate provided path.

    Args:
        file_path: Optional file path string

    Returns:
        Path object for selected/validated file

    Raises:
        SystemExit: If no file selected or file picker not available
    """
    if not file_path:
        if not HAS_FILE_PICKER:
            logger.error("File picker not available. Please provide file path via -c option.")
            sys.exit(1)

        logger.info("Press enter to select a .tex file...")
        input()
        file_path = pyle_manager.file_manager(True)

        if not file_path:
            logger.error("No file selected")
            sys.exit(1)

    path = Path(file_path)

    # Validate file exists
    if not path.exists():
        logger.error("File not found: %s", path)
        sys.exit(1)

    # Warn if not .tex file
    if path.suffix != ".tex":
        response = input(
            f"Warning: File '{path.name}' is not a .tex file. Continue anyway? (y/N): "
        ).lower()
        if response != "y":
            logger.info("Operation cancelled")
            sys.exit(0)

    return path


def get_output_filename(file_path: Path) -> str:
    """Extract base filename for output files.

    Args:
        file_path: Path to input LaTeX file

    Returns:
        Base filename without extension
    """
    if file_path.suffix == ".tex":
        return file_path.stem
    return file_path.name


def process_document(env: Environment) -> None:
    """Main document processing loop.

    Iterates through source text, finding special characters and dispatching
    to appropriate handlers.

    Args:
        env: Processing environment containing source and output
    """
    # Find \begin{document} and skip preamble
    if "\\begin{document}" not in env.source.head._text:
        logger.warning("\\begin{document} not found - processing entire file")
    else:
        try:
            env.source.move_index("\\begin{document}")
        except ValueError:
            logger.warning("Could not skip to \\begin{document}")

    # Main parsing loop
    while env.source.head:
        next_index = env.source.inter

        if next_index == -1:
            # No more special characters - add remaining text and pop stack
            env.clean.add(env.source.text)
            env.source.pop()
            continue

        # Add text before special character
        env.clean.add(env.source.text[:next_index])
        env.source.index += next_index

        # Process special character
        char = env.source.text[0]

        match char:
            case "\\":  # LaTeX command
                handle_command(env)

            case "$":  # Math mode
                handle_math_mode(env)

            case "%":  # Comment
                env.source.move_index("\n")

            case "{" | "}":  # Brackets - skip
                env.source.index += 1

            case "~":  # Non-breaking space
                env.clean.add(" ")
                env.source.index += 1

            case _:  # Unknown special character
                logger.warning(
                    "Unknown special character: '%s' at index %d",
                    char, env.source.index
                )
                env.source.index += 1


def handle_command(env: Environment) -> None:
    """Extract and process LaTeX command.

    Args:
        env: Processing environment
    """
    # Find command terminator
    terminators = [
        pos for pos in (env.source.text.find(t, 1) for t in COMMAND_TERMINATORS)
        if pos > 0
    ]

    if not terminators:
        logger.warning("No command terminator found after backslash")
        env.source.index += 1
        return

    i = min(terminators)
    env.command = env.source.text[1:i]
    env.source.index += i

    # Dispatch to command handler
    interpret(env)


def handle_math_mode(env: Environment) -> None:
    """Handle inline and display math modes.

    Args:
        env: Processing environment
    """
    env.clean.add("[_]")
    env.source.index += 1

    # Check for display math ($$)
    if env.source.text and env.source.text[0] == "$":
        try:
            env.source.move_index("$$")
        except ValueError:
            logger.warning("Unclosed display math mode ($$)")
    else:
        # Inline math mode
        try:
            env.source.move_index("$")
        except ValueError:
            logger.warning("Unclosed inline math mode ($)")



def post_process(text: str) -> str:
    """Apply regex-based cleanup to processed text.

    Args:
        text: Raw processed text

    Returns:
        Cleaned text with normalized whitespace and formatting
    """
    # Strip outer whitespace
    text = text.strip()

    # Remove empty brackets and tabs
    text = text.replace("[]", "").replace("()", "").replace("\t", " ")

    # Normalize whitespace around newlines
    text = REGEX_PATTERNS['trailing_spaces'].sub("\n", text)

    # Remove excess newlines (max 2 consecutive)
    text = REGEX_PATTERNS['excess_newlines'].sub("\n\n", text)

    # Remove double spacing
    text = REGEX_PATTERNS['double_spacing'].sub(" ", text)

    # Format [_] spacing before equations (unless preceded by -)
    text = REGEX_PATTERNS['equation_before'].sub(r"\1 [_]", text)

    # Format [_] spacing after equations (unless followed by list item)
    text = REGEX_PATTERNS['equation_after'].sub(r"[_]\1 \2", text)

    return text


def write_output_files(env: Environment, base_filename: str, output_dir: Path) -> None:
    """Write cleaned text and unknown commands to output files.

    Args:
        env: Processing environment with results
        base_filename: Base name for output files
        output_dir: Directory for output files
    """
    # Write cleaned text
    output_file = output_dir / f"{base_filename}_grammafied.txt"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(env.clean.text)
        logger.info("Successfully wrote: %s", output_file)
    except IOError as e:
        logger.error("Failed to write output file: %s", e)
        sys.exit(1)

    # Write unknown commands if any
    if env.clean.aggro:
        unknowns_file = output_dir / f"{base_filename}_unknowns.txt"
        try:
            with open(unknowns_file, "w", encoding="utf-8") as f:
                f.write("Unknown LaTeX commands encountered:\n\n")
                for cmd in sorted(env.clean.aggro):
                    f.write(f"  \\{cmd}\n")
            logger.warning("Unknown commands found. See: %s", unknowns_file)
        except IOError as e:
            logger.error("Failed to write unknowns file: %s", e)


def grammafy(file_path: Optional[str] = None) -> None:
    """Main function to convert LaTeX file to clean text.

    This function orchestrates the entire conversion process:
    1. Select/validate input file
    2. Initialize processing environment
    3. Process document (parse and transform)
    4. Apply post-processing cleanup
    5. Write output files

    Args:
        file_path: Optional path to LaTeX file (if not provided, uses file picker)

    Raises:
        SystemExit: On errors or user cancellation
    """
    try:
        # Step 1: Select input file
        input_file = select_file(file_path)
        logger.info("Processing: %s", input_file)

        # Step 2: Initialize environment
        env = Environment(input_file)

        # Step 3: Process document
        logger.info("Parsing LaTeX document...")
        process_document(env)

        # Step 4: Post-process
        logger.info("Applying post-processing cleanup...")
        env.clean.text = post_process(env.clean.text)

        # Step 5: Write output
        base_filename = get_output_filename(input_file)
        write_output_files(env, base_filename, env.folder_path)

        logger.info("Grammification complete!")

    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        sys.exit(1)


def main() -> None:
    """Entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        prog="grammafy",
        description="Convert LaTeX files to clean text for grammar checking",
        epilog="Example: grammafy -c document.tex"
    )
    parser.add_argument(
        "-c", "--commandline",
        metavar="FILE",
        help="LaTeX file to process (if not provided, use interactive picker)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors"
    )

    args = parser.parse_args()

    # Configure logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    grammafy(args.commandline)


if __name__ == "__main__":
    main()
