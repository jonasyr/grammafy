# Grammafy - Complete Technical Analysis

**Version Analyzed:** 1.4.5
**Analysis Date:** 2025-11-10
**Purpose:** Reference document for understanding architecture and implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Repository Structure](#repository-structure)
3. [Architecture Overview](#architecture-overview)
4. [Core Components](#core-components)
5. [LaTeX Processing Logic](#latex-processing-logic)
6. [Data Flow](#data-flow)
7. [Platform Compatibility](#platform-compatibility)
8. [Dependencies](#dependencies)
9. [Known Issues](#known-issues)
10. [Extension Points](#extension-points)

---

## Executive Summary

**Grammafy** is a Python-based LaTeX-to-text converter designed to strip LaTeX commands from `.tex` files, producing clean text suitable for grammar checking tools like Grammarly. The application replaces mathematical formulas with `[_]` placeholders and preserves document structure while removing formatting commands.

### Key Characteristics
- **Language:** Python 3.10+ (uses structural pattern matching)
- **Lines of Code:** ~1,492 across 13 files
- **Architecture:** State machine with visitor pattern
- **Extensibility:** Modular custom command system
- **UI:** Terminal-based file picker using ncurses

---

## Repository Structure

```
grammafy/
├── .git/                          # Version control
├── .gitignore                     # Python standard ignores
├── LICENSE.md                     # MIT License
├── README.md                      # User documentation
├── compile.sh                     # PyInstaller build script
└── scr/                          # Source code directory
    ├── grammafy.py               # Main entry point (173 lines)
    ├── classes.py                # Core data structures (131 lines)
    ├── pyle_manager.py           # Terminal file manager (646 lines)
    └── exceptions/               # LaTeX command processors
        ├── __init__.py           # Built-in handlers (290 lines)
        ├── routines_custom.py    # User custom handlers (33 lines)
        ├── sub_begin/            # \begin{} processors
        │   ├── __init__.py       # Built-in begin handlers (130 lines)
        │   └── begin_custom.py   # Custom begin handlers (34 lines)
        └── sub_end/              # \end{} processors
            ├── __init__.py       # Built-in end handlers (37 lines)
            └── end_custom.py     # Custom end handlers (18 lines)
```

### File Responsibilities

| File | Purpose | Key Functions |
|------|---------|--------------|
| `grammafy.py` | Orchestration, CLI, main loop | `grammafy()`, `Environment` class |
| `classes.py` | Data structures | `Node`, `Source`, `Clean` |
| `pyle_manager.py` | Interactive file picker | `file_manager()` |
| `exceptions/__init__.py` | Command routing & handlers | `interpret()`, 40+ command handlers |
| `sub_begin/__init__.py` | Environment start handlers | `interpret()`, 20+ environment handlers |
| `sub_end/__init__.py` | Environment end handlers | `interpret()`, cleanup functions |

---

## Architecture Overview

### Design Pattern: State Machine with Visitor Pattern

**Core Philosophy:** *"Every command knows exactly what it's doing and nothing else"*

```
┌─────────────────────────────────────────────────────────────┐
│                        grammafy.py                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Main Processing Loop                      │  │
│  │  1. Find next special character (\, {, }, $, %, ~)    │  │
│  │  2. Copy text before character to Clean               │  │
│  │  3. Dispatch to appropriate handler                   │  │
│  │  4. Repeat until source exhausted                     │  │
│  └───────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  Environment Object                    │  │
│  │  • source: Source (input text stack)                  │  │
│  │  • clean: Clean (output accumulator)                  │  │
│  │  • command: str (current command name)                │  │
│  │  • folder_path: str (working directory)               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                               ↓
        ┌──────────────────────┴──────────────────────┐
        ↓                                              ↓
┌──────────────────┐                        ┌──────────────────┐
│  exceptions/     │                        │   classes.py     │
│  interpret()     │                        │                  │
│                  │                        │  Node: text chunk│
│  Command Router  │←──────────────────────→│  Source: stack   │
│  • void lists    │                        │  Clean: output   │
│  • dic_commands  │                        └──────────────────┘
│  • custom hooks  │
└──────────────────┘
        ↓
┌──────────────────────────────────────────┐
│     Specialized Handlers                 │
│  • _begin() → sub_begin/interpret()     │
│  • _end() → sub_end/interpret()         │
│  • _include() → recursive file load     │
│  • _footnote() → nested bracket extract │
│  • _equation() → math replacement       │
└──────────────────────────────────────────┘
```

### Key Architectural Decisions

1. **Linked List Source Management**
   - `Source` uses a stack of `Node` objects
   - Enables recursive file inclusion (`\include`, `\input`)
   - Each node tracks current position with `index`

2. **Accumulator Pattern for Output**
   - `Clean` accumulates text fragments in a list
   - Assembled only when needed (lazy evaluation)
   - Tracks unknown commands in `aggro` set

3. **Modular Command Dispatch**
   - Priority: custom void → custom handlers → built-in void → built-in handlers → unknown
   - Easy extension without modifying core code

4. **Character-Level Parsing**
   - No tokenization or AST construction
   - Direct string manipulation for performance
   - Minimal memory footprint

---

## Core Components

### 1. classes.py - Data Structures

#### Node Class
Represents a chunk of LaTeX source text with position tracking.

```python
Node(text: str, root: Node | None = None)
```

**Key Features:**
- **Automatic comment filtering:** Removes lines starting with `%` during initialization
- **Index safety:** Setting index backwards triggers reset (prevents infinite loops)
- **Symbol tracking:** Caches positions of `\`, `{`, `}`, `$`, `%`, `~` for performance
- **inter property:** Returns distance to next special character

**Properties:**
- `.text` → Returns text from current index onward (read-only)
- `.index` → Current parsing position (read/write with safety checks)
- `.inter` → Distance to next special character (computed lazily)
- `.symbols` → Dictionary caching character positions

**Methods:**
- `move_index(text_to_find)` → Advances index past specified text

#### Source Class
Manages stack of Node objects (for nested file inclusion).

```python
Source(text: str)
```

**Proxy Pattern:** Forwards most operations to `.head` node

**Key Operations:**
- `add(text)` → Push new text node (for file inclusion)
- `pop()` → Remove current node, return to parent file
- `index`, `text`, `inter` → Proxied to current head node

#### Clean Class
Accumulates cleaned output text.

```python
Clean()
```

**Accumulator Pattern:** Stores fragments, assembles on demand

**Properties:**
- `._text` → List of text fragments (private)
- `.text` → Assembled text (getter joins fragments, setter replaces)
- `.aggro` → Set of unknown commands

**Methods:**
- `add(text)` → Append text fragment

---

### 2. grammafy.py - Main Orchestrator

#### Environment Class
Global state container passed to all handlers.

```python
Environment(file_path: str)
```

**Initialized with:**
- `source: Source` → Loaded from file
- `clean: Clean` → Empty accumulator
- `folder_path: str` → Directory for relative includes
- `command: str` → Current command being processed

#### grammafy() Function
Main execution function.

**Execution Flow:**

```python
def grammafy(file_path: str = "") -> None:
    # 1. File Selection
    if not file_path:
        file_path = pyle_manager.file_manager(True)

    # 2. Validation
    if not file_path.endswith(".tex"):
        # Prompt user to continue

    # 3. Initialize Environment
    env = Environment(file_path)

    # 4. Skip Preamble
    env.source.move_index("\\begin{document}")

    # 5. MAIN PARSING LOOP
    while env.source.head:
        next_index = env.source.inter  # Find next special char

        if next_index == -1:  # No more special chars
            env.clean.add(env.source.text)
            env.source.pop()
            continue

        # Copy text before special char
        env.clean.add(env.source.text[:next_index])
        env.source.index += next_index

        # Handle special character
        match env.source.text[0]:
            case "\\":  # LaTeX command
                # Extract command name
                i = min(env.source.text.find(x, 1) for x in end_command)
                env.command = env.source.text[1:i]
                env.source.index += i
                interpret(env)

            case "$":  # Math mode
                env.clean.add("[_]")
                # Skip to closing $

            case "%":  # Comment
                env.source.move_index("\n")

            case "{" | "}":  # Brackets
                env.source.index += 1

            case "~":  # Non-breaking space
                env.clean.add(" ")
                env.source.index += 1

    # 6. POST-PROCESSING (Regex cleanup)
    env.clean.text = cleanup_regex(env.clean.text)

    # 7. WRITE OUTPUT
    write_grammafied_file(env, file_name)
    write_unknowns_file(env, file_name)
```

**Command Name Extraction:**
Command terminators: ` `, `{`, `}`, `.`, `,`, `:`, `;`, `[`, `]`, `(`, `)`, `$`, `\`, `\n`, `"`, `'`, `~`

**Post-Processing Regex:**
1. Strip trailing spaces
2. Remove empty `[]` and `()`
3. Normalize whitespace: `( )*\n( )*` → `\n`
4. Remove excess newlines: `\n\n\s*` → `\n\n`
5. Remove double spacing: `( )+` → ` `
6. Format `[_]` spacing around text and punctuation

---

### 3. exceptions/__init__.py - Command Handlers

#### interpret() Function
**Primary command dispatcher** - routes commands to appropriate handlers.

```python
def interpret(env) -> None:
    if env.command:
        # Priority order:
        if env.command in void or env.command in void_c:
            pass  # Void commands - do nothing
        elif env.command in dic_commands_c:
            dic_commands_c[env.command](env)  # Custom handlers
        elif env.command in dic_commands:
            dic_commands[env.command](env)  # Built-in handlers
        else:
            # Unknown command - skip brackets, track in aggro
            skip_all_brackets(env)
            env.clean.aggro.add(env.command)
    else:  # Special characters (\[, \(, \\, etc.)
        if env.command in special_commands:
            special_commands[env.command](env)
```

#### Built-in Command Lists

**Void Commands** (~40 commands):
Commands that are simply removed without processing arguments.
```python
void = (
    "centering", "small", "large", "newpage", "textbf", "textit",
    "emph", "maketitle", "chapter", "section", "subsection",
    "author", "title", "date", "underline", ...
)
```

**Command Handlers** (25 handlers):

| Command | Handler | Behavior |
|---------|---------|----------|
| `\begin{}` | `_begin()` | Delegates to `sub_begin/interpret()` |
| `\end{}` | `_end()` | Delegates to `sub_end/interpret()` |
| `\include{}`, `\input{}` | `_include()` | Recursively loads file |
| `\footnote{}` | `_footnote()` | Extracts to "(FOOTNOTE: ...)" |
| `\cite[]{}` | `_print_square_curly()` | Replaces with `[_]` |
| `\ref{}`, `\eqref{}`, `\cref{}` | `_print_curly()` | Replaces with `[_]` |
| `\color{}` | `_color()` | Outputs "Color:NAME" |
| `\label{}`, `\hspace{}`, `\vspace{}` | `_curly()` | Skips content |
| `\renewcommand{}{}`, `\setlength{}{}` | `_curly_curly()` | Skips both args |
| `\&`, `\%`, `\#` | `_reprint()` | Outputs the symbol |
| `\\`, `\newline` | `_new_line()` | Outputs `\n` |
| `\~` | `_tilde()` | Outputs `~` |

**Special Commands:**
```python
special_commands = {
    "[": _square_equation,    # \[...\] → [_]
    "(": _round_equation,     # \(...\) → [_]
    '"': _apostrofe,          # Skip accents
    "'": _apostrofe,          # Skip accents
    "\\": _new_line,          # Line break
    "~": _tilde,              # Non-breaking space
}
```

#### Key Handler Implementations

**_include() - Recursive File Loading**
```python
def _include(env) -> None:
    i = env.source.text.find("}")
    include_path = env.source.text[1:i]

    if include_path.endswith(".bbl"):  # Skip bibliography
        env.source.index += i + 1
    else:
        if not include_path.endswith(".tex"):
            include_path += ".tex"
        with open(f"{env.folder_path}{include_path}") as f:
            env.source.add(f.read())  # Push onto stack
        env.source.root.index += i + 1  # Advance parent
```

**_footnote() - Nested Bracket Handling**
```python
def _footnote(env) -> None:
    i = 1  # Position of closing }
    j = 1  # Position of opening {
    # Find matching closing bracket
    while i >= j and j > 0:
        i = env.source.text.find("}", i) + 1
        j = env.source.text.find("{", j) + 1

    # Extract and wrap footnote text
    env.source.add("(FOOTNOTE: " + env.source.text[1:i-1] + ")")
    env.source.root.index += i
```

**_square_equation() - Display Math**
```python
def _square_equation(env) -> None:
    # \[...\] → [_]
    i = env.source.text.find("\\]")
    env.clean.add("[_]")
    # Preserve punctuation at end
    if env.source.text[:i].rstrip()[-1] in [",", ";", "."]:
        env.clean.add(env.source.text[:i].rstrip()[-1])
    env.source.move_index("\\]")
```

---

### 4. sub_begin/__init__.py - Environment Handlers

Handles `\begin{environment}` commands.

#### Built-in Environments

**Void Environments:** `center`, `frame` (transparent - content preserved)

**Titled Environments:**
```python
"abstract", "theorem", "lemma", "proof", "definition", "proposition",
"corollary", "conjecture", "remark", "question", "comment"
```
→ Replaced with capitalized name: `Theorem.`

**Equation Environments:**
```python
"equation", "equation*", "align", "align*", "gather", "gather*",
"multline", "multline*", "eqnarray", "eqnarray*",
"figure", "figure*", "table", "tikzpicture", "verbatim"
```
→ Replaced with `[_]`, punctuation preserved

**List Environments:**
- `enumerate` → `\item` replaced with `1.`, `2.`, `3.`, ...
- `itemize` → `\item` replaced with `-`

#### Key Handlers

**_equation() - Math Environments**
```python
def _equation(env) -> None:
    env.clean.add("[_]")
    # Find matching \end{...}
    i = env.source.text.find("\\end{" + env.command + "}")
    # Preserve trailing punctuation
    if env.source.text[:i-1].rstrip()[-1] in [",", ";", "."]:
        env.clean.add(env.source.text[:i-1].rstrip()[-1])
    env.source.move_index("\\end{" + env.command + "}")
```

**_enumerate() - Numbered Lists**
```python
def _enumerate(env) -> None:
    # Skip optional [] parameter
    if env.source.text[0] == "[":
        env.source.move_index("]")

    # Extract environment content
    i = env.source.text.find("\\end{enumerate}")
    new_text = env.source.text[:i]

    # Replace \item with numbers
    index_enum = 1
    while "\\item" in new_text:
        new_text = new_text.replace("\\item", str(index_enum) + ".", 1)
        index_enum += 1

    # Push processed text onto stack
    env.source.add(new_text)
    env.source.root.move_index("\\end{enumerate}")
```

**Unknown Environment Handler:**
```python
# Automatically handles nested unknown environments
i = env.source.text.find("\\begin{" + env.command + "}", 6)
j = env.source.text.find("\\end{" + env.command + "}", 6)
while 0 < i < j:  # Handle nesting
    i = env.source.text.find("\\begin{" + env.command + "}", i + 6)
    j = env.source.text.find("\\end{" + env.command + "}", j + 6)
env.source.index += j + 5 + len(env.command)
env.clean.aggro.add("begin{" + env.command + "}")
```

---

### 5. pyle_manager.py - Terminal File Manager

Cross-platform terminal-based file picker using `unicurses`.

**Features:**
- Keyboard navigation (arrow keys, vim keys)
- File sorting (name, size, date)
- Hidden file toggle
- File size display (B, KB, MB, GB)
- Permissions display (Unix-style: rwxrwxrwx)
- File opening and editing
- Breadcrumb navigation

**Platform Support:**
- Linux: Uses `xdg-open`, `$EDITOR`
- macOS: Uses `open`, `open -e`
- Windows: Direct file opening (no CLI editor support)

**Key Functions:**
- `file_manager(picker=True)` → Returns selected file path
- `open_file(path)` → Opens file with OS default
- `edit_file(path)` → Opens in text editor

---

## LaTeX Processing Logic

### Philosophy

*"Every command knows exactly what it's doing and nothing else"*

Each handler is responsible only for:
1. Reading its own arguments
2. Advancing the source index past itself
3. Adding appropriate output to clean
4. Nothing else

### Special Character Processing

| Character | Meaning | Action |
|-----------|---------|--------|
| `\` | Command start | Extract name, call `interpret()` |
| `{` | Group start | Skip (unless in handler) |
| `}` | Group end | Skip (unless in handler) |
| `$` | Inline math | Replace `$...$` with `[_]` |
| `$$` | Display math | Replace `$$...$$` with `[_]` |
| `%` | Comment | Skip to newline |
| `~` | Non-breaking space | Replace with space |

### Math Mode Detection

**Inline Math:**
```latex
This is $x^2$ inline     →  This is [_] inline
This is \(x^2\) inline   →  This is [_] inline
```

**Display Math:**
```latex
The equation:            The equation:
$$x = 5$$                [_]

Or:                      Or:
\[x = 5.\]               [_].
```

**Punctuation Preservation:**
Display math environments preserve trailing punctuation:
```latex
\begin{equation}         [_],
    x = 5,
\end{equation}

\[x = 5.\]               [_].
```

### Environment Processing

**Transparent Environments:**
```latex
\begin{center}           The content is
The content is           preserved as-is
preserved as-is
\end{center}
```

**Titled Environments:**
```latex
\begin{theorem}          Theorem.
The statement            The statement
\end{theorem}
```

**List Environments:**
```latex
\begin{enumerate}        1. First item
\item First item         2. Second item
\item Second item
\end{enumerate}

\begin{itemize}          - First item
\item First item         - Second item
\item Second item
\end{itemize}
```

### Nesting Support

**Nested Lists:**
```latex
\begin{itemize}          - Outer
\item Outer              - Nested start
\begin{itemize}          - Inner
\item Inner              - Nested end
\end{itemize}            - Back to outer
\item Back to outer
\end{itemize}
```

**Nested Unknown Environments:**
```latex
\begin{customenv}        [Content preserved, environment skipped]
Content
\begin{customenv}
Nested content
\end{customenv}
More content
\end{customenv}
```

### File Inclusion

**Recursive Loading:**
```latex
% main.tex
\input{chapter1}         [Contents of chapter1.tex inserted here]
```

**Features:**
- Auto-appends `.tex` extension if missing
- Skips `.bbl` bibliography files
- Files must be in same directory
- Unlimited nesting depth (stack-based)

### Unknown Commands

**Automatic Bracket Skipping:**
```latex
\unknowncommand[opt]{arg1}{arg2}
```
→ Skips all `[]` and `{}` arguments, tracks `unknowncommand` in `aggro` set

**Output:**
Creates `{filename}_unknowns.txt` with set of unrecognized commands:
```
{'unknowncommand', 'anothercmd', 'begin{customenv}'}
```

---

## Data Flow

### Complete Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. INPUT                                                        │
├─────────────────────────────────────────────────────────────────┤
│ • User selects .tex file via pyle_manager or CLI                │
│ • File loaded into memory as single string                      │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. INITIALIZATION                                               │
├─────────────────────────────────────────────────────────────────┤
│ • Environment object created                                    │
│ • Source initialized with file text                             │
│ • Node filters out comment lines (starting with %)              │
│ • Clean initialized (empty)                                     │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. PREAMBLE REMOVAL                                             │
├─────────────────────────────────────────────────────────────────┤
│ • Find \begin{document}                                         │
│ • Advance source index past it                                  │
│ • Everything before is discarded                                │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. MAIN PARSING LOOP                                            │
├─────────────────────────────────────────────────────────────────┤
│ WHILE source.head exists:                                       │
│                                                                 │
│   A. Find next special character (\ { } $ % ~)                  │
│      ↓                                                          │
│   B. Copy text BEFORE character to clean                        │
│      ↓                                                          │
│   C. Advance index to character                                 │
│      ↓                                                          │
│   D. DISPATCH based on character:                               │
│      • \ → Extract command → interpret(env)                     │
│      • $ → Add [_], skip to closing $                           │
│      • % → Skip to newline                                      │
│      • { } → Skip                                               │
│      • ~ → Add space                                            │
│      ↓                                                          │
│   E. Handler executes:                                          │
│      • Reads its arguments                                      │
│      • Advances source index                                    │
│      • Adds output to clean                                     │
│      • May push new text onto source (include, footnote)        │
│      ↓                                                          │
│   F. Loop continues                                             │
│                                                                 │
│ END WHILE                                                       │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. POST-PROCESSING                                              │
├─────────────────────────────────────────────────────────────────┤
│ • Assemble clean.text (join all fragments)                      │
│ • Apply regex cleanup:                                          │
│   - Remove trailing spaces                                      │
│   - Remove empty brackets []()                                  │
│   - Normalize whitespace                                        │
│   - Remove excess newlines                                      │
│   - Format [_] spacing                                          │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. OUTPUT                                                       │
├─────────────────────────────────────────────────────────────────┤
│ • Write {filename}_grammafied.txt (clean text)                  │
│ • Write {filename}_unknowns.txt (if unknown commands exist)     │
│ • Print success messages                                        │
└─────────────────────────────────────────────────────────────────┘
```

### Memory Management

**Source Stack Example:**
```
Initial:
    head → Node("main.tex content")

After \input{chapter1}:
    head → Node("chapter1.tex content")
      ↓
    root → Node("main.tex content [index at \input{...}]")

After chapter1 exhausted:
    head → Node("main.tex content [index after \input]")
```

**Clean Accumulator:**
```python
clean._text = []                    # Initially empty
clean.add("Hello ")                 # ["Hello "]
clean.add("world")                  # ["Hello ", "world"]
clean.text                          # "Hello world" (joined lazily)
clean.text = clean.text.strip()     # ["Hello world"] (replaced)
```

---

## Platform Compatibility

### Current Platform-Specific Code

**File Opening (pyle_manager.py:561-577):**
```python
match platform.system():
    case "Linux":
        os.system(f'xdg-open "{selection_os}"')
    case "Windows":
        os.system(selection_os)
    case "Darwin":
        os.system(f'open "{selection_os}"')
```

**File Editing (pyle_manager.py:584-607):**
```python
match platform.system():
    case "Linux":
        os.system(f'$EDITOR "{selection_os}"')
    case "Windows":
        # Error: No built-in CLI editor
        print("Cannot edit on Windows from CLI")
    case "Darwin":
        os.system(f'open -e "{selection_os}"')
```

### Cross-Platform Dependencies

**unicurses (Uni-Curses):**
- Provides ncurses functionality on all platforms
- Windows: Uses PDCurses backend
- Unix: Uses ncurses library
- Installation: `pip install uni-curses`

**Path Handling:**
- Uses `os.sep` for separators
- Uses `os.path` functions (cross-platform)
- **Issue:** No `pathlib` usage (less modern)

### Known Platform Issues

1. **Windows:**
   - No command-line text editor support
   - File editing functionality disabled

2. **Linux:**
   - Requires `xdg-open` (standard on most distros)
   - Requires `$EDITOR` environment variable

3. **macOS:**
   - Assumes `open` command available (standard)

---

## Dependencies

### Runtime Dependencies

**Required:**
- `uni-curses` (Uni-Curses on PyPI)
  - Cross-platform ncurses wrapper
  - Used for terminal UI in file picker

**Standard Library:**
- `os`, `sys`, `re`, `argparse`, `time`, `ctypes`
- `itertools.chain`
- `platform.system`

### Development Dependencies

**Build Tool:**
- `pyinstaller`
  - Creates standalone executable
  - Specified in `compile.sh`

### Python Version

**Minimum:** Python 3.10

**Reason:** Uses structural pattern matching (`match`/`case`)

**Example:**
```python
match env.source.text[0]:
    case "\\":
        # Handle command
    case "$":
        # Handle math
```

### Missing Dependency Management

**No requirements.txt** - Dependencies not formally tracked

**Should contain:**
```txt
uni-curses>=1.5
```

**No setup.py or pyproject.toml** - Not packaged as installable module

---

## Known Issues

### 1. Build Script Bug (compile.sh:12)

**Line 12:**
```bash
echo "Error: pyinstaller is not installed via pip, run pip install mypy"
```

**Problem:** Says "mypy" instead of "pyinstaller"

**Impact:** Misleading error message

### 2. Missing Dependency File

**Issue:** No `requirements.txt`

**Impact:** Users must manually determine dependencies

### 3. Limited Error Handling

**Examples:**
- File not found in `\include{}` → crash
- Malformed LaTeX → unexpected behavior
- Missing `\end{document}` → processes to EOF
- Missing closing brackets → crash

### 4. Platform-Specific Code Not Abstracted

**Issue:** Platform detection mixed with business logic

**Impact:** Hard to test, maintain, extend

### 5. No Testing Infrastructure

**Issue:** No unit tests, integration tests, or CI/CD

**Impact:** Refactoring risk, regression risk

### 6. Hard-Coded Command Lists

**Issue:** Commands in Python tuples/dicts, not config files

**Impact:** Users must edit Python code to add commands permanently

### 7. Type Hints Incomplete

**Examples:**
- `pyle_manager.py`: No type hints
- Many function signatures missing return types
- `env` parameter not typed

### 8. Regex Post-Processing Could Be More Robust

**Current approach:** Fixed set of regex patterns

**Potential improvements:**
- Configurable patterns
- Pattern testing/validation
- More comprehensive whitespace handling

### 9. No Logging System

**Issue:** Uses `print()` statements

**Impact:** No log levels, no log file output, hard to debug

### 10. Nested Math Mode Not Detected

**Example:**
```latex
$$ (e^x)^{-1} \text{ $$ = $$ } e^{-x} $$.
```

**Issue:** Inner `$$` breaks parsing

**Note:** README acknowledges this limitation

---

## Extension Points

### 1. Custom Command Handlers

**Location:** `scr/exceptions/routines_custom.py`

**Add to void list:**
```python
void_c = (
    "yourcustomcommand",
)
```

**Add custom handler:**
```python
def _your_handler(env) -> None:
    # Your logic here
    pass

dic_commands_c = {
    "yourcmd": _your_handler,
}
```

### 2. Custom Begin Environments

**Location:** `scr/exceptions/sub_begin/begin_custom.py`

**Example:**
```python
def _your_env(env) -> None:
    env.clean.add("Custom Environment: ")
    env.source.move_index("\\end{yourenv}")

dic_commands_c = {
    "yourenv": _your_env,
}
```

### 3. Custom End Environments

**Location:** `scr/exceptions/sub_end/end_custom.py`

**Example:**
```python
def _your_end(env) -> None:
    env.clean.add(" [End of custom env]")

dic_commands_c = {
    "yourenv": _your_end,
}
```

### 4. Modifying Post-Processing

**Location:** `scr/grammafy.py` lines 133-151

**Add regex patterns:**
```python
# Your custom cleanup
env.clean.text = re.sub(r'pattern', r'replacement', env.clean.text)
```

---

## Performance Characteristics

### Time Complexity

**Overall:** O(n) where n = total text length (including included files)

**Bottlenecks:**
- `inter` property: O(k) where k = number of special characters
- `find()` operations: O(m) where m = substring search length
- Regex post-processing: O(n)

### Space Complexity

**Overall:** O(n + d) where:
- n = total text length
- d = maximum include depth

**Memory Usage:**
- Source stack: One node per active include
- Clean fragments: One entry per `add()` call (consolidates on `.text` access)
- Unknown commands: O(u) where u = unique unknown commands

### Optimization Opportunities

1. **Symbol caching in Node** - Already implemented, good
2. **Lazy text assembly in Clean** - Already implemented, good
3. **Could improve:** Compile regex patterns once (currently recompiled)
4. **Could improve:** Use `mmap` for very large files

---

## Security Considerations

### File Access

**Current behavior:**
- Reads any file specified by user
- `\include{}` can reference any file in same directory
- No sandboxing

**Risks:**
- Accidental data exposure if `.tex` file includes sensitive files
- No validation of include paths

**Recommendation:** Validate include paths, restrict to specific directory

### Command Injection

**Potential risk:** `pyle_manager.py` uses `os.system()`

**Current code:**
```python
os.system(f'xdg-open "{selection_os}"')
```

**Risk:** If filename contains shell metacharacters, could execute commands

**Mitigation:** Use `subprocess.run()` with argument list instead

### Resource Exhaustion

**Risk:** Deeply nested includes could exhaust memory/stack

**Mitigation:** Add include depth limit

---

## Testing Strategy Recommendations

### Unit Tests

**Core Classes:**
- `Node`: Index manipulation, inter property, move_index
- `Source`: Stack operations, add/pop
- `Clean`: Text accumulation, aggro tracking

**Handlers:**
- Each command handler in isolation
- Mock `env` object

### Integration Tests

**End-to-End:**
- Sample `.tex` files → expected output
- Test cases for each environment type
- Test nested structures
- Test file inclusion

### Platform Tests

**File Manager:**
- Run on Linux, Windows, macOS
- Verify file opening, editing work correctly

### Regression Tests

**Unknown Commands:**
- Verify all unknown commands tracked correctly
- Verify bracket skipping works for nested cases

---

## Refactoring Recommendations

### High Priority

1. **Add requirements.txt**
2. **Fix compile.sh error message**
3. **Abstract platform-specific code** into separate module
4. **Add error handling** for file operations
5. **Add type hints** throughout

### Medium Priority

6. **Use `pathlib` instead of `os.path`**
7. **Replace `os.system()` with `subprocess.run()`**
8. **Add logging** instead of print statements
9. **Add configuration file** for commands (JSON/YAML)
10. **Compile regex patterns** once at module level

### Low Priority

11. **Add CLI progress indicators** for large files
12. **Add `--quiet` mode** to suppress output
13. **Add `--output` flag** to specify output directory
14. **Add `--format` flag** for different output formats

---

## Conclusion

Grammafy is a well-architected, focused tool that effectively solves its specific problem: converting LaTeX to clean text for grammar checking. The codebase is readable, maintainable, and extensible.

**Strengths:**
- Clear separation of concerns
- Modular command system
- Handles complex nesting
- Cross-platform file picker
- Efficient parsing (single-pass, O(n))

**Areas for Improvement:**
- Dependency management
- Error handling
- Platform abstraction
- Testing infrastructure
- Type safety

With the refactoring recommendations implemented, this tool could be production-ready and suitable for wider distribution.

---

**Document Version:** 1.0
**Last Updated:** 2025-11-10
**Maintainer:** [Your Name/Organization]
