import tkinter as tk
from tkinter import ttk, font as tkfont, filedialog, messagebox, simpledialog
from lexer.lexer import tokenize
from errors import format_error
from parser.syntax import check_syntax
from parser.ast import build_ast, format_ast
from semantics.values import to_yarn
from semantics.interpreter import execute_program


def run_analysis():
    clear_results()
    source = code_editor.get("1.0", "end-1c")
    tokens, errors = tokenize(source)
    symbols = {}
    phase = "Lexical"

    if not errors:
        errors = check_syntax(tokens)
        phase = "Syntax"


    if not errors:
        program = build_ast(tokens)
        symbols, errors = execute_program(program,write_console,request_input)
        phase = "Runtime"

    # print(format_ast(program))

    for item in token_table.get_children():
        token_table.delete(item)

    for token in tokens:
        token_table.insert(
            "", tk.END,
            values=tuple(
                token[key] for key in ("type", "lexeme", "line", "column")
            )
        )

    show_symbols(symbols)

    if errors:
        message = f"{phase} errors:\n\n"
        message += "\n".join(format_error(error) for error in errors)

        if phase == "Lexical":
            message += "\n\nSyntax checking skipped. Fix lexical errors first."
    else:
        message = "No lexical or syntax errors found by the implemented checks."

    error_output.config(
        state=tk.NORMAL,
        foreground="red" if errors else "green"
    )
    error_output.delete("1.0", tk.END)
    error_output.insert(tk.END, message)
    error_output.config(state=tk.DISABLED)

def show_symbols(symbols):
    
    names = [name for name in symbols if name != "IT"]
    names += [name for name in symbols if name == "IT"]

    for name in names:
        symbol_table.insert(
            "", tk.END, values=(name, symbols[name]["type"], format_value(symbols[name]))
        )

def format_value(value):
    """Show a LOLCODE value the way the language writes it."""
    if value["type"] == "NOOB":
        return "NOOB"

    if value["type"] == "TROOF":
        return "WIN" if value["value"] else "FAIL"

    return str(value["value"])

def clear_results():
    for table in (token_table, symbol_table):
        for item in table.get_children():
            table.delete(item)

    for output in (error_output, console_output):
        output.config(state=tk.NORMAL)
        output.delete("1.0", tk.END)
        output.config(state=tk.DISABLED)


def clear_all():
    code_editor.delete("1.0", tk.END)
    clear_results()


def open_file():
    file_path = filedialog.askopenfilename(
        title="Open LOLCODE File",
        filetypes=[
            ("LOLCODE Files", "*.lol"),
            ("All Files", "*.*")
        ]
    )

    if not file_path:
        return

    try:
        with open(file_path, "r", encoding="utf-8-sig") as file:
            source = file.read()
    except (OSError, UnicodeError) as error:
        messagebox.showerror(
            "Unable to Open File",
            str(error)
        )
        return

    # Clear the previous source and analysis results.
    clear_all()
    code_editor.insert("1.0", source)

def write_console(text):
    console_output.config(state=tk.NORMAL)
    console_output.insert(tk.END, text)
    console_output.see(tk.END)
    console_output.config(state=tk.DISABLED)


def run_program(program):
    symbols, errors = execute_program(
        program,
        write_console,
        request_input,
    )

    update_symbol_table(symbols)

    if errors:
        message = "Semantic errors:\n\n"
        message += "\n".join(format_error(error) for error in errors)
    else:
        message = "Program finished successfully."

    error_output.config(
        state=tk.NORMAL,
        foreground="red" if errors else "green",
    )
    error_output.delete("1.0", tk.END)
    error_output.insert(tk.END, message)
    error_output.config(state=tk.DISABLED)

    return errors


def update_symbol_table(symbols):
    for item in symbol_table.get_children():
        symbol_table.delete(item)

    for name, value in symbols.items():
        if value["type"] == "NOOB":
            text = "NOOB"
        elif value["type"] == "NUMBAR":
            text = str(value["value"])
        else:
            text = to_yarn(value)["value"]

        symbol_table.insert(
            "",
            tk.END,
            values=(name, value["type"], text),
        )


def request_input(variable_name):
    value = simpledialog.askstring(
        "LOLCODE Input",
        f"Enter a value for {variable_name}:",
        parent=code_editor.winfo_toplevel()
    )

    if value is not None:
        write_console(f"> {value}\n")

    return value


def create_gui():
    global code_editor, token_table, error_output, symbol_table, console_output

    root = tk.Tk()
    root.title("LOLCODE INTERPRETER")
    root.geometry("1000x750")
    root.minsize(700, 500)

    # Interface font.
    default_font = tkfont.nametofont("TkDefaultFont")
    default_font.configure(family="Segoe UI", size=10)

    # Use an installed monospace font.
    available_fonts = set(tkfont.families())
    code_font = next(
        (
            name for name in ("Cascadia Code", "Consolas", "DejaVu Sans Mono")
            if name in available_fonts
        ),
        "TkFixedFont"
    )

    style = ttk.Style(root)

    style.configure("TLabel", font=("Segoe UI", 10))
    style.configure("TButton", font=("Segoe UI", 10), padding=(10, 6))
    style.configure("Treeview", font=("Segoe UI", 10), rowheight=28)
    style.configure(
        "Treeview.Heading",
        font=("Segoe UI", 10, "bold")
    )

    # Main heading.
    heading = ttk.Label(
        root,
        text="LOLCODE Interpreter",
        font=("Segoe UI", 20, "bold")
    )
    heading.pack(anchor="w", padx=24, pady=(18, 16))

    # Resizable left and right panels.
    workspace = ttk.Panedwindow(root, orient=tk.HORIZONTAL)
    workspace.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

    left_panel = ttk.Frame(workspace)
    right_panel = ttk.Frame(workspace)

    workspace.add(left_panel, weight=1)
    workspace.add(right_panel, weight=1)

    # Right panel: tokens above errors.
    right_panel.columnconfigure(0, weight=1)
    right_panel.rowconfigure(1, weight=3)
    right_panel.rowconfigure(3, weight=2)

    # Source code section.
    ttk.Label(
        left_panel,
        text="Source Code",
        font=("Segoe UI", 11, "bold")
    ).pack(anchor="w", padx=12)

    editor_frame = ttk.Frame(left_panel)
    editor_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,5))

    code_editor = tk.Text(
        editor_frame,
        height=6,
        wrap=tk.NONE,
        font=(code_font, 11),
        padx=12,
        pady=10,
        undo=True
    )
    editor_scroll = ttk.Scrollbar(
        editor_frame,
        orient=tk.VERTICAL,
        command=code_editor.yview
    )
    code_editor.configure(yscrollcommand=editor_scroll.set)

    code_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    editor_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # Buttons.
    button_frame = ttk.Frame(left_panel)
    button_frame.pack(
        fill=tk.X,
        padx=12,
        pady=(5, 8),
        before=editor_frame
    )

    ttk.Button(
        button_frame,
        text="Open File",
        command=open_file
    ).pack(side=tk.LEFT, padx=(0, 5))

    ttk.Button(
        button_frame,
        text="Analyze",
        command=run_analysis
    ).pack(side=tk.LEFT, padx=(0, 5))

    ttk.Button(
        button_frame,
        text="Clear",
        command=clear_all
    ).pack(side=tk.LEFT, padx=5)

    ttk.Label(
        right_panel,
        text="Analysis Results",
        font=("Segoe UI", 11, "bold")
    ).grid(row=0, column=0, sticky="w", padx=(12, 0), pady=(0, 5))

    results_notebook = ttk.Notebook(right_panel)
    results_notebook.grid(
        row=1,
        column=0,
        sticky="nsew",
        padx=(12, 0),
        pady=(0, 10)
    )

    table_frame = ttk.Frame(results_notebook)
    symbol_frame = ttk.Frame(results_notebook)

    results_notebook.add(table_frame, text="Tokens")
    results_notebook.add(symbol_frame, text="Symbol Table")

    columns = ("type", "lexeme", "line", "column")

    token_table = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=10
    )

    token_table.heading("type", text="Token Type")
    token_table.heading("lexeme", text="Lexeme")
    token_table.heading("line", text="Line")
    token_table.heading("column", text="Column")

    token_table.column("type", width=130, anchor=tk.W)
    token_table.column("lexeme", width=200, anchor=tk.W)
    token_table.column("line", width=50, stretch=False, anchor=tk.CENTER)
    token_table.column("column", width=65, stretch=False, anchor=tk.CENTER)

    table_scroll = ttk.Scrollbar(
        table_frame,
        orient=tk.VERTICAL,
        command=token_table.yview
    )
    token_table.configure(yscrollcommand=table_scroll.set)

    token_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    table_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # Symbol table: populated when semantic execution is connected.
    symbol_columns = ("identifier", "type", "value")

    symbol_table = ttk.Treeview(
        symbol_frame,
        columns=symbol_columns,
        show="headings",
        height=10
    )

    symbol_table.heading("identifier", text="Identifier")
    symbol_table.heading("type", text="Type")
    symbol_table.heading("value", text="Value")

    symbol_table.column("identifier", width=150, anchor=tk.W)
    symbol_table.column("type", width=100, anchor=tk.W)
    symbol_table.column("value", width=200, anchor=tk.W)

    symbol_scroll = ttk.Scrollbar(
        symbol_frame,
        orient=tk.VERTICAL,
        command=symbol_table.yview
    )
    symbol_table.configure(yscrollcommand=symbol_scroll.set)

    symbol_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    symbol_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # Program Output section.
    ttk.Label(
        right_panel,
        text="Program Output",
        font=("Segoe UI", 11, "bold")
    ).grid(row=2, column=0, sticky="w", padx=(12, 0), pady=(0, 5))

    output_notebook = ttk.Notebook(right_panel)
    output_notebook.grid(
        row=3,
        column=0,
        sticky="nsew",
        padx=(12, 0)
    )

    error_frame = ttk.Frame(output_notebook)
    console_frame = ttk.Frame(output_notebook)

    output_notebook.add(error_frame, text="Errors")
    output_notebook.add(console_frame, text="Console")

    error_output = tk.Text(
        error_frame,
        height=8,
        wrap=tk.WORD,
        font=(code_font, 11),
        padx=12,
        pady=10,
        foreground="red",
        state=tk.DISABLED
    )

    error_scroll = ttk.Scrollbar(
        error_frame,
        orient=tk.VERTICAL,
        command=error_output.yview
    )
    error_output.configure(yscrollcommand=error_scroll.set)

    error_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    error_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    console_output = tk.Text(
        console_frame,
        height=8,
        wrap=tk.WORD,
        font=(code_font, 11),
        padx=12,
        pady=10,
        state=tk.DISABLED
    )

    console_scroll = ttk.Scrollbar(
        console_frame,
        orient=tk.VERTICAL,
        command=console_output.yview
    )
    console_output.configure(yscrollcommand=console_scroll.set)

    console_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    console_scroll.pack(side=tk.RIGHT, fill=tk.Y)


    root.mainloop()
