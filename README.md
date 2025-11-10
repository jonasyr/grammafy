# Grammafy 2.0

**Convert LaTeX documents to clean text for grammar checking**

Grammafy is a Python tool that strips LaTeX commands from `.tex` files, producing clean text suitable for grammar checkers like Grammarly. Mathematical formulas are replaced with `[_]` placeholders, and document structure is preserved while formatting commands are removed.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)

---

## Features

- **Comprehensive LaTeX support**: Handles 40+ built-in commands and 20+ environments
- **Recursive file inclusion**: Processes `\include{}` and `\input{}` commands
- **Nested structure support**: Correctly processes nested lists, equations, and unknown commands
- **Cross-platform**: Works on Linux, Windows, and macOS
- **Interactive file picker**: Browse and select files with keyboard navigation (optional)
- **Extensible**: Easy to add custom command handlers
- **Clean output**: Produces well-formatted text with normalized whitespace
- **Unknown command tracking**: Reports unrecognized LaTeX commands for review

---

## Quick Start

### Installation

**Requirements:** Python 3.10 or higher

```bash
# Clone the repository
git clone https://github.com/yourusername/grammafy.git
cd grammafy

# Install dependencies
pip install -r requirements.txt

# Run grammafy
python3 scr/grammafy.py
```

### Basic Usage

**Interactive mode** (with file picker):
```bash
python3 scr/grammafy.py
```

**Command-line mode** (specify file directly):
```bash
python3 scr/grammafy.py -c path/to/document.tex
```

**Quiet mode** (minimal output):
```bash
python3 scr/grammafy.py -q -c document.tex
```

**Verbose mode** (detailed logging):
```bash
python3 scr/grammafy.py -v -c document.tex
```

### Output Files

Grammafy creates two output files in the same directory as your input file:

1. **`document_grammafied.txt`** - Clean text ready for grammar checking
2. **`document_unknowns.txt`** - List of unrecognized LaTeX commands (if any)

---

## Installation Options

### Option 1: Standard Installation

```bash
# Install from source
git clone https://github.com/yourusername/grammafy.git
cd grammafy
pip install -r requirements.txt
```

### Option 2: Editable Install (for development)

```bash
pip install -e .
```

After installation, you can run:
```bash
grammafy -c document.tex
```

### Option 3: Standalone Executable

Build a portable executable that doesn't require Python:

```bash
# Install build dependency
pip install pyinstaller

# Build executable
./compile.sh  # Linux/Mac
# or
bash compile.sh  # Windows (Git Bash)

# Run standalone executable
./dist/grammafy -c document.tex
```

---

## How It Works

Grammafy processes LaTeX documents in several stages:

### 1. **Preamble Removal**
Everything before `\begin{document}` is discarded.

### 2. **Character-by-Character Parsing**
The document is scanned for special characters:
- `\` - LaTeX command
- `{`, `}` - Grouping brackets
- `$`, `$$` - Math mode
- `%` - Comment
- `~` - Non-breaking space

### 3. **Command Processing**
Each LaTeX command is routed to an appropriate handler:

| Command | Result |
|---------|--------|
| `\textbf{bold}` | `bold` (formatting removed) |
| `\section{Title}` | `Title` (section commands removed) |
| `$x^2$` | `[_]` (math replaced with placeholder) |
| `\cite{ref}` | `[_]` (citations replaced) |
| `\footnote{text}` | `(FOOTNOTE: text)` |
| `\begin{itemize}\item A\item B\end{itemize}` | `- A\n- B` |

### 4. **Environment Processing**

**Equations** → `[_]`
```latex
\begin{equation}
    E = mc^2.
\end{equation}
```
Output: `[_].`

**Lists** → Formatted plaintext
```latex
\begin{enumerate}
    \item First item
    \item Second item
\end{enumerate}
```
Output: `1. First item\n2. Second item`

**Theorems** → Labeled text
```latex
\begin{theorem}
    Statement here.
\end{theorem}
```
Output: `Theorem. Statement here.`

### 5. **Post-Processing**
- Remove empty brackets and excessive whitespace
- Normalize spacing around `[_]` placeholders
- Format list items consistently

---

## Customization

### Adding Custom Commands

Create custom handlers by editing the files in `scr/exceptions/`:

#### Void Commands (no output)

Edit `scr/exceptions/routines_custom.py`:

```python
void_c = (
    "mycommand",  # \mycommand will be removed
    "anothercommand",
)
```

#### Custom Command Handlers

Edit `scr/exceptions/routines_custom.py`:

```python
def _mycommand(env):
    """Handle \mycommand{arg}"""
    i = env.source.text.find("}")
    arg = env.source.text[1:i]
    env.clean.add(f"[CUSTOM: {arg}]")
    env.source.index += i + 1

dic_commands_c = {
    "mycommand": _mycommand,
}
```

#### Custom Environments

Edit `scr/exceptions/sub_begin/begin_custom.py`:

```python
def _myenv(env):
    """Handle \begin{myenv}"""
    env.clean.add("My Environment: ")
    env.source.move_index("\\end{myenv}")

dic_commands_c = {
    "myenv": _myenv,
}
```

---

## Supported LaTeX Features

### Commands

**Formatting** (removed):
`\textbf`, `\textit`, `\emph`, `\underline`, `\textsc`, `\texttt`, `\small`, `\large`, `\Large`, `\huge`, `\Huge`

**Sectioning** (removed):
`\chapter`, `\section`, `\subsection`, `\subsubsection`, `\paragraph`

**Math** (→ `[_]`):
`$...$`, `$$...$$`, `\[...\]`, `\(...\)`, `\equation`, `\align`, `\gather`, `\eqnarray`

**References** (→ `[_]`):
`\cite`, `\ref`, `\eqref`, `\cref`, `\Cref`

**Special**:
- `\footnote{text}` → `(FOOTNOTE: text)`
- `\include{file}`, `\input{file}` → Recursively includes file content
- `\color{red}` → `Color:RED`
- `\\`, `\newline` → `\n`

### Environments

**Math** (→ `[_]`):
`equation`, `align`, `gather`, `multline`, `figure`, `table`, `tikzpicture`

**Lists**:
- `enumerate` → `1. 2. 3. ...`
- `itemize` → `- - - ...`

**Theorems** (→ `Name.`):
`theorem`, `lemma`, `proof`, `proposition`, `corollary`, `definition`, `remark`

**Transparent** (content preserved):
`center`, `frame`

---

## Advanced Usage

### Processing Multiple Files

```bash
# Process all .tex files in a directory
for file in *.tex; do
    python3 scr/grammafy.py -c "$file"
done
```

### Integration with Grammarly

1. Run grammafy on your LaTeX file
2. Open the `_grammafied.txt` file in a text editor
3. Copy the content to Grammarly (web or app)
4. Review suggestions
5. Manually apply corrections to your original `.tex` file

### Handling Unknown Commands

If `_unknowns.txt` is created:

1. Review the unknown commands
2. Add them to `routines_custom.py` with appropriate handlers
3. Rerun grammafy

---

## Troubleshooting

### Common Issues

**"File picker not available"**
- Solution: Install uni-curses: `pip install uni-curses`
- Or: Use command-line mode: `grammafy -c file.tex`

**"FileNotFoundError" for included files**
- Solution: Ensure included files are in the same directory as the main file
- Check that file names in `\include{}` and `\input{}` are correct

**Math mode warnings**
- Issue: Nested or malformed math delimiters
- Example: `$$ text $$ = $$ more $$` (nested `$$` breaks parsing)
- Solution: Fix the LaTeX source or ignore if output is acceptable

**"Index overload" warning**
- Cause: A command handler attempted to move backwards in the text
- Impact: Parsing jumped to end to prevent infinite loop
- Solution: Review custom command handlers for bugs

### Debug Mode

Enable verbose logging to diagnose issues:

```bash
python3 scr/grammafy.py -v -c document.tex
```

---

## Architecture

Grammafy uses a **character-by-character parsing** approach with a **state machine** and **visitor pattern**:

### Core Components

1. **Node** - Text chunk with position tracking
2. **Source** - Stack of nodes (for file inclusion)
3. **Clean** - Output accumulator
4. **Environment** - Global processing state
5. **Command Handlers** - Functions that process specific commands

### Processing Flow

```
Input File → Environment → Parse Loop → Command Handlers → Post-Process → Output Files
```

See [`TECHNICAL_ANALYSIS.md`](TECHNICAL_ANALYSIS.md) for complete architectural documentation.

---

## Performance

- **Time complexity**: O(n) where n = total text length
- **Space complexity**: O(n + d) where d = inclusion depth
- **Typical performance**: Processes ~1MB LaTeX file in under 1 second

---

## Contributing

Contributions are welcome! Here's how you can help:

### Reporting Issues

- Open an issue on GitHub
- Include sample LaTeX input that demonstrates the problem
- Specify your Python version and operating system

### Adding Command Support

1. Fork the repository
2. Add handler to `scr/exceptions/routines_custom.py`
3. Test with sample LaTeX files
4. Submit pull request

### Code Style

- Follow PEP 8
- Add type hints
- Include docstrings
- Test on Linux and Windows

---

## Version History

### Version 2.0.0 (2025-11-10)

**Major refactoring with breaking changes**

✨ **New Features:**
- Cross-platform path handling with `pathlib`
- Comprehensive error handling
- Logging system (verbose/quiet modes)
- Better unknown command reporting
- Type hints throughout codebase

🐛 **Bug Fixes:**
- Fixed compile.sh error message typo
- Improved math mode delimiter handling
- Better nested structure support

🔧 **Improvements:**
- Modular, scalable code architecture
- Complete documentation
- Setup.py for proper installation
- Requirements.txt for dependency management

### Version 1.4.5 (Previous)

- Original implementation
- Basic LaTeX processing
- File picker support

---

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---

## Credits

**Original Author**: [Original Author Name]
**Version 2.0 Refactoring**: Community Contributors

Built with Python. Inspired by the need for better grammar checking in academic writing.

---

## FAQ

**Q: Does grammafy compile LaTeX?**
A: No, grammafy only processes the text. Your LaTeX must compile correctly for best results.

**Q: Can I use this with Overleaf?**
A: Yes! Download your project as .zip, extract, run grammafy on the main .tex file.

**Q: What about BibTeX/bibliographies?**
A: Bibliography files (.bbl) are automatically skipped. Citations become `[_]` placeholders.

**Q: Does it support custom LaTeX commands?**
A: Yes! Add them to the `routines_custom.py` file. Unknown commands are automatically skipped (brackets removed).

**Q: Is the file picker required?**
A: No. Use `-c` to specify files directly: `grammafy -c file.tex`

**Q: Can I process non-English LaTeX?**
A: Yes! Grammafy works with any UTF-8 text. Unicode characters are preserved.

**Q: What if my document has errors?**
A: Grammafy is forgiving and will process malformed LaTeX. Check the output and `_unknowns.txt` file.

---

## Support

- **Documentation**: See `TECHNICAL_ANALYSIS.md` for detailed information
- **Issues**: Report bugs on GitHub Issues
- **Community**: Star the repo if you find it useful! ⭐

---

**Happy grammar checking!** 📝✨
