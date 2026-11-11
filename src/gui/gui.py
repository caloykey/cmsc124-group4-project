import tkinter as tk
from tkinter import ttk

from lexer.lexer import tokenize
from errors import format_error
from parser.syntax import check_syntax


SAMPLE_CODE = '''HAI
BTW Sample of currently supported syntax
WAZZUP
I HAS A name ITZ "Juan Dela Cruz"
I HAS A age ITZ 18
BUHBYE

age R SUM OF age AN 1
VISIBLE SMOOSH "Hello, " AN name MKAY
VISIBLE MAEK age A YARN
VISIBLE BOTH OF WIN AN NOT FAIL
VISIBLE ANY OF FAIL AN WIN MKAY

BOTH SAEM age AN 21
O RLY?
YA RLY
    VISIBLE "Age is twenty-one"
NO WAI
    VISIBLE "Age is different"
OIC

KTHXBYE'''


def run_analysis():
    source = code_editor.get("1.0", "end-1c")
    tokens, errors = tokenize(source)
    phase = "Lexical"

    if not errors:
        errors = check_syntax(tokens)
        phase = "Syntax"

    for item in token_table.get_children():
        token_table.delete(item)

    for token in tokens:
        token_table.insert(
            "", tk.END,
            values=tuple(
                token[key] for key in ("type", "lexeme", "line", "column")
            )
        )

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

def load_sample():
    code_editor.delete("1.0", tk.END)
    code_editor.insert("1.0", SAMPLE_CODE)


def clear_all():
    code_editor.delete("1.0", tk.END)

    for item in token_table.get_children():
        token_table.delete(item)

    error_output.config(state=tk.NORMAL)
    error_output.delete("1.0", tk.END)
    error_output.config(state=tk.DISABLED)


def create_gui():
    global code_editor, token_table, error_output

    root = tk.Tk()
    root.title("LOLCODE INTERPRETER")
    root.geometry("1000x750")
    root.minsize(700, 500)

    # Main heading.
    heading = ttk.Label(
        root,
        text="LOLCODE INTERPRETER",
        font=("Arial", 18, "bold")
    )
    heading.pack(pady=10)

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
        font=("Arial", 11, "bold")
    ).pack(anchor="w", padx=12)

    editor_frame = ttk.Frame(left_panel)
    editor_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,5))

    code_editor = tk.Text(
        editor_frame,
        height=6,
        wrap=tk.NONE,
        font=("Consolas", 11),
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
        text="Analyze",
        command=run_analysis
    ).pack(side=tk.LEFT, padx=(0, 5))

    ttk.Button(
        button_frame,
        text="Load Sample",
        command=load_sample
    ).pack(side=tk.LEFT, padx=5)

    ttk.Button(
        button_frame,
        text="Clear",
        command=clear_all
    ).pack(side=tk.LEFT, padx=5)

    # Token results table.
    ttk.Label(
        right_panel,
        text="Tokens",
        font=("Arial", 11, "bold")
    ).grid(row=0, column=0, sticky="w", padx=(12, 0), pady=(0, 5))

    table_frame = ttk.Frame(right_panel)
    table_frame.grid(
        row=1,
        column=0,
        sticky="nsew",
        padx=(12, 0),
        pady=(0, 10)
    )

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

    # Error output section.
    # Error output section.
    ttk.Label(
        right_panel,
        text="Errors",
        font=("Arial", 11, "bold")
    ).grid(row=2, column=0, sticky="w", padx=(12, 0), pady=(0, 5))

    error_frame = ttk.Frame(right_panel)
    error_frame.grid(
        row=3,
        column=0,
        sticky="nsew",
        padx=(12, 0)
    )

    error_output = tk.Text(
        error_frame,
        height=8,
        wrap=tk.WORD,
        font=("Consolas", 10),
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

    load_sample()
    root.mainloop()
