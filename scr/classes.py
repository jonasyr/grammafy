"""Core data structures for grammafy LaTeX processing.

This module provides the fundamental classes for parsing and transforming LaTeX documents:
- Node: Represents a chunk of source text with position tracking
- Source: Stack-based text source manager for recursive file inclusion
- Clean: Output accumulator for cleaned text
"""

from __future__ import annotations
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class Node:
    """Represents a chunk of LaTeX source text with position tracking.

    This class manages a text buffer with an index pointer that tracks the current
    parsing position. It automatically filters out LaTeX comment lines (starting with %)
    during initialization and caches positions of special characters for efficient lookup.

    Attributes:
        _text: The complete text content (immutable)
        _index: Current parsing position
        root: Optional parent node for stack-based inclusion
        symbols: Cache of special character positions
    """

    def __init__(self, text: str, root: Optional[Node] = None) -> None:
        """Initialize a Node with LaTeX text, filtering comment lines.

        Args:
            text: LaTeX source text to parse
            root: Optional parent node (for file inclusion stack)
        """
        # Filter out comment lines (starting with %)
        self._text = (
            "\n".join(
                filter(lambda x: not x.lstrip().startswith("%"), text.splitlines())
            )
            + "\n"
        )
        self._index = 0
        self.root = root
        # Cache for special character positions (optimization)
        self.symbols: Dict[str, int] = {
            "\\": -1, "{": -1, "}": -1, "$": -1, "%": -1, "~": -1
        }

    @property
    def text(self) -> str:
        """Return the text from the current index onward.

        Returns:
            Substring from current index to end
        """
        return self._text[self.index:]

    @text.setter
    def text(self, text: str) -> None:
        """Prevent modification of source text.

        Raises:
            ValueError: Always raised to prevent text modification
        """
        raise ValueError("text is a constant and should not be changed")

    @property
    def index(self) -> int:
        """Get the current parsing position.

        Returns:
            Current index in the text
        """
        return self._index

    @index.setter
    def index(self, index: int) -> None:
        """Set the parsing position with safety check.

        If attempting to move backwards (which would cause infinite loops),
        automatically jumps to end of text instead.

        Args:
            index: New index position
        """
        if index < self._index:
            logger.warning(
                "Index overload detected: attempted to move backwards from %d to %d. "
                "Jumping to end of text to prevent infinite loop.",
                self._index, index
            )
            self._index = len(self._text)
        else:
            self._index = index

    @property
    def inter(self) -> int:
        """Find distance to the next special character.

        This property efficiently finds the closest special character (\\, {, }, $, %, ~)
        by maintaining a cache of their positions. Only recomputes positions that are
        behind the current index.

        Returns:
            Distance to next special character, or -1 if none found
        """
        # Update cached positions for symbols behind current index
        for symbol in list(self.symbols.keys()):
            if self.symbols[symbol] < self.index:
                if symbol not in self.text:
                    # Symbol no longer exists in remaining text
                    self.symbols.pop(symbol)
                else:
                    # Update cached position
                    self.symbols[symbol] = self._text.find(symbol, self.index)

        # Return distance to closest symbol
        if any(self.symbols):
            return min(self.symbols.values()) - self.index
        return -1

    def move_index(self, text_to_find: str) -> None:
        """Search for text and move index to the end of it.

        Args:
            text_to_find: Text pattern to search for

        Raises:
            ValueError: If text_to_find is not found
        """
        pos = self._text.find(text_to_find, self.index)
        if pos == -1:
            logger.error("Could not find '%s' in text starting at index %d",
                        text_to_find[:50], self.index)
            raise ValueError(f"Text pattern not found: {text_to_find[:50]}")
        self.index = pos + len(text_to_find)


class Source:
    """Stack-based text source manager for recursive file inclusion.

    This class maintains a stack of Node objects, allowing for recursive file inclusion
    (\include, \input commands). The current node is accessed via the 'head' property,
    and most operations are proxied to the head node for convenience.

    This enables natural handling of nested LaTeX files:
    - main.tex includes chapter1.tex
    - Push chapter1.tex onto stack
    - Process chapter1.tex
    - Pop stack when done, resume main.tex

    Attributes:
        head: The current (top of stack) Node being processed
    """

    def __init__(self, text: str) -> None:
        """Initialize with initial text content.

        Args:
            text: Initial LaTeX source text
        """
        self.head: Optional[Node] = Node(text)

    # Proxy properties to head node for convenient access
    @property
    def index(self) -> int:
        """Get current parsing position from head node.

        Returns:
            Current index in head node

        Raises:
            AttributeError: If head is None (stack exhausted)
        """
        if self.head is None:
            raise AttributeError("Source stack is empty")
        return self.head.index

    @index.setter
    def index(self, val: int) -> None:
        """Set current parsing position in head node.

        Args:
            val: New index position

        Raises:
            AttributeError: If head is None (stack exhausted)
        """
        if self.head is None:
            raise AttributeError("Source stack is empty")
        self.head.index = val

    @property
    def text(self) -> str:
        """Get remaining text from head node.

        Returns:
            Text from current index to end

        Raises:
            AttributeError: If head is None (stack exhausted)
        """
        if self.head is None:
            raise AttributeError("Source stack is empty")
        return self.head.text

    @text.setter
    def text(self, val: str) -> None:
        """Attempt to set text (always raises error).

        Args:
            val: Attempted new text value

        Raises:
            ValueError: Always (text is immutable)
        """
        if self.head is None:
            raise AttributeError("Source stack is empty")
        self.head.text = val

    @property
    def inter(self) -> int:
        """Get distance to next special character from head node.

        Returns:
            Distance to next special character, or -1 if none

        Raises:
            AttributeError: If head is None (stack exhausted)
        """
        if self.head is None:
            raise AttributeError("Source stack is empty")
        return self.head.inter

    def move_index(self, text_to_find: str) -> None:
        """Search for text in head node and move index past it.

        Args:
            text_to_find: Text pattern to find

        Raises:
            AttributeError: If head is None (stack exhausted)
            ValueError: If text_to_find not found
        """
        if self.head is None:
            raise AttributeError("Source stack is empty")
        self.head.move_index(text_to_find)

    def add(self, text: str) -> None:
        """Push new text onto stack (for file inclusion).

        Creates a new Node with the given text and pushes it onto the stack,
        making it the new head. The previous head becomes the new node's parent.

        Args:
            text: New LaTeX source text to process
        """
        self.head = Node(text, self.head)
        logger.debug("Pushed new text onto source stack (length: %d)", len(text))

    def pop(self) -> None:
        """Pop current node from stack.

        Removes the current head node and restores its parent as the new head.
        Used when finished processing an included file.

        Raises:
            RuntimeError: If attempting to pop when no parent exists
        """
        if self.head is None:
            raise RuntimeError("Cannot pop from empty source stack")
        if self.head.root is None:
            logger.warning("Popping last node from source stack")
        self.head = self.head.root
        logger.debug("Popped node from source stack")


class Clean:
    """Output accumulator for cleaned LaTeX text.

    This class accumulates fragments of cleaned text in a list for efficiency,
    only joining them into a single string when needed. It also tracks all
    unknown LaTeX commands encountered during processing.

    The accumulator pattern allows incremental text building without repeated
    string concatenation (which would be O(n²)). Instead, fragments are stored
    and joined once when needed (O(n)).

    Attributes:
        _text: List of text fragments (private)
        aggro: Set of unknown command names encountered
    """

    def __init__(self) -> None:
        """Initialize empty accumulator."""
        self._text: list[str] = []
        # Set of unknown commands (for diagnostic output)
        self.aggro: set[str] = set()

    def add(self, text: str) -> None:
        """Add a fragment of cleaned text to the accumulator.

        Args:
            text: Text fragment to append
        """
        self._text.append(text)

    @property
    def text(self) -> str:
        """Get the complete assembled text.

        Joins all fragments into a single string on first access, then caches
        the result. Subsequent accesses return the cached string.

        Returns:
            Complete cleaned text as single string
        """
        if len(self._text) == 0:
            return ""
        if len(self._text) > 1:
            # Join fragments and cache result
            self._text = ["".join(self._text)]
        return self._text[0]

    @text.setter
    def text(self, text: str) -> None:
        """Replace all accumulated text with new text.

        Clears the fragment list and sets new content.

        Args:
            text: New text to replace accumulated content
        """
        self._text = [text]

    def clear(self) -> None:
        """Clear all accumulated text and unknown commands."""
        self._text = []
        self.aggro = set()

    def __len__(self) -> int:
        """Return length of accumulated text.

        Returns:
            Total character count of all fragments
        """
        return len(self.text)

    def __str__(self) -> str:
        """Return string representation of accumulated text.

        Returns:
            Complete cleaned text
        """
        return self.text
