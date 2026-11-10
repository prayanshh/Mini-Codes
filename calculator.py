"""Modern dark-themed calculator (tkinter, no external dependencies).
 
Run:  python calculator.py
Keyboard: digits, + - * / . % ( ), Enter/= to evaluate, Backspace, Esc to clear.
"""
import ast
import operator
import re
import tkinter as tk
 
# ---------- Safe expression evaluation (no eval) ----------
OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}
 
 
def safe_eval(expr: str):
    def _ev(n):
        if isinstance(n, ast.Expression):
            return _ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            return OPS[type(n.op)](_ev(n.left), _ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in OPS:
            return OPS[type(n.op)](_ev(n.operand))
        raise ValueError("Invalid expression")
 
    return _ev(ast.parse(expr, mode="eval"))
 
 
def fmt(x) -> str:
    if isinstance(x, float):
        if x.is_integer() and abs(x) < 1e15:
            return str(int(x))
        return f"{x:.10g}"
    return str(x)
 
 
# ---------- Theme ----------
BG, DISPLAY_BG = "#14161a", "#14161a"
NUM, NUM_H = "#262a31", "#323741"
OPR, OPR_H = "#3b82f6", "#5b9bff"
FUNC, FUNC_H = "#3a3f48", "#4a505b"
EQ, EQ_H = "#22c55e", "#4ade80"
TXT, SUBTXT = "#f3f4f6", "#8b93a1"
FONT = "Segoe UI"
 
LAYOUT = [
    [("AC", "func"), ("⌫", "func"), ("%", "func"), ("÷", "op")],
    [("7", "num"), ("8", "num"), ("9", "num"), ("×", "op")],
    [("4", "num"), ("5", "num"), ("6", "num"), ("−", "op")],
    [("1", "num"), ("2", "num"), ("3", "num"), ("+", "op")],
    [("±", "func"), ("0", "num"), (".", "num"), ("=", "eq")],
]
STYLE = {
    "num": (NUM, NUM_H), "op": (OPR, OPR_H),
    "func": (FUNC, FUNC_H), "eq": (EQ, EQ_H),
}
OPERATORS = "+−×÷"
PROMPT = "Enter a number"
DONE_PROMPT = "Press any key for a new calculation"
 
 
class Calculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculator")
        self.configure(bg=BG)
        self.resizable(False, False)
 
        self.expr = ""
        self.just_done = False
 
        # Display
        disp = tk.Frame(self, bg=DISPLAY_BG)
        disp.pack(fill="x", padx=18, pady=(20, 8))
        self.history = tk.Label(disp, text="", bg=DISPLAY_BG, fg=SUBTXT,
                                font=(FONT, 12), anchor="e")
        self.history.pack(fill="x")
        self.main = tk.Label(disp, text="0", bg=DISPLAY_BG, fg=TXT,
                             font=(FONT, 38, "bold"), anchor="e")
        self.main.pack(fill="x")
        self.hint = tk.Label(disp, text="", bg=DISPLAY_BG, fg=SUBTXT,
                             font=(FONT, 11), anchor="e")
        self.hint.pack(fill="x")
        self._reset_job = None
 
        # Buttons
        grid = tk.Frame(self, bg=BG)
        grid.pack(padx=12, pady=(4, 14))
        for r, row in enumerate(LAYOUT):
            for c, (label, kind) in enumerate(row):
                self._make_button(grid, label, kind, r, c)
 
        self.bind("<Key>", self._on_key)
        self.reset()
 
    def _make_button(self, parent, label, kind, r, c):
        base, hover = STYLE[kind]
        b = tk.Label(parent, text=label, bg=base, fg=TXT, width=4, height=1,
                     font=(FONT, 18, "bold"), cursor="hand2")
        b.grid(row=r, column=c, padx=5, pady=5, ipadx=8, ipady=10)
        b.bind("<Enter>", lambda e: b.config(bg=hover))
        b.bind("<Leave>", lambda e: b.config(bg=base))
        b.bind("<ButtonPress-1>", lambda e: b.config(bg=base))
        b.bind("<ButtonRelease-1>", lambda e: (b.config(bg=hover), self.press(label)))
 
    # ---------- Logic ----------
    def _to_python(self, s: str) -> str:
        s = s.replace("÷", "/").replace("×", "*").replace("−", "-")
        return s.replace("%", "/100")
 
    def _preview(self):
        if not self.expr:
            self.main.config(text="0")
            self.hint.config(text=PROMPT)
            return
        self.hint.config(text="")
        try:
            self.main.config(text=fmt(safe_eval(self._to_python(self.expr))))
        except Exception:
            self.main.config(text=self.expr[-14:] or "0")
 
    def reset(self):
        """Return to the default state and ask for new input."""
        if self._reset_job:
            self.after_cancel(self._reset_job)
            self._reset_job = None
        self.expr, self.just_done = "", False
        self.history.config(text="")
        self.main.config(text="0", fg=TXT)
        self.hint.config(text=PROMPT)
 
    def press(self, key: str):
        if key == "AC":
            self.reset()
            return
        if self.just_done:  # result/error on screen: next input starts fresh
            if key == "=":
                return
            self.reset()
            if key in ("⌫", "±"):
                return
        if key == "⌫":
            self.expr = self.expr[:-1]
        elif key == "=":
            self._evaluate()
            return
        elif key == "±":
            m = re.search(r"(−?\d*\.?\d+)$", self.expr)
            if m:
                tok = m.group(1)
                new = tok[1:] if tok.startswith("−") else "−" + tok
                self.expr = self.expr[:m.start()] + new
        elif key in OPERATORS:
            if not self.expr:
                if key == "−":
                    self.expr = "−"
            elif self.expr[-1] in OPERATORS:
                self.expr = self.expr[:-1] + key
            else:
                self.expr += key
        else:  # digit, '.', '%'
            if key == "%" and (not self.expr or self.expr[-1] in OPERATORS):
                return
            if key == ".":
                last = re.split(r"[+−×÷]", self.expr)[-1]
                if "." in last:
                    return
                if not last:
                    key = "0."
            self.expr += key
        self.history.config(text=self.expr)
        self._preview()
 
    def _evaluate(self):
        if not self.expr:
            return
        shown = self.expr
        try:
            result = fmt(safe_eval(self._to_python(self.expr)))
        except ZeroDivisionError:
            self._show_error("Cannot divide by 0")
            return
        except Exception:
            self._show_error("Invalid input")
            return
        self.history.config(text=f"{shown} =")
        self.main.config(text=result)
        self.hint.config(text=DONE_PROMPT)
        self.expr, self.just_done = "", True
 
    def _show_error(self, msg):
        self.expr, self.just_done = "", True
        self.history.config(text="")
        self.main.config(text=msg, fg="#f87171")
        self.hint.config(text="Resetting…")
        self._reset_job = self.after(1500, self.reset)
 
    # ---------- Keyboard ----------
    def _on_key(self, e):
        k = e.char
        mapping = {"*": "×", "/": "÷", "-": "−", "+": "+"}
        if k.isdigit() or k in ".%":
            self.press(k)
        elif k in mapping:
            self.press(mapping[k])
        elif k in ("=", "\r"):
            self.press("=")
        elif e.keysym == "BackSpace":
            self.press("⌫")
        elif e.keysym == "Escape":
            self.press("AC")
 
 
if __name__ == "__main__":
    Calculator().mainloop()
 
