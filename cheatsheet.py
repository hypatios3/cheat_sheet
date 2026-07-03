import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os

if getattr(sys, 'frozen', False):
    # Running as a PyInstaller exe — save next to the exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as a plain .py script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(BASE_DIR, "snippets.json")

DEFAULT_DATA = {
    "Django": {
        "Setup": [
            {"title": "Install Django", "code": "pipenv install django"},
            {"title": "Start project", "code": "pipenv run django-admin startproject config ."},
            {"title": "Start app", "code": "pipenv run python manage.py startapp"},
            {"title": "Run server", "code": "pipenv run python manage.py runserver"},
        ],
        "Migrations": [
            {"title": "Make migrations", "code": "pipenv run python manage.py makemigrations"},
            {"title": "Apply migrations", "code": "pipenv run python manage.py migrate"},
        ],
        "Models": [
            {"title": "__str__ method", "code": "def __str__(self):\n    return self.title"},
            {"title": "get_object_or_404", "code": "get_object_or_404(Model, pk=pk)"},
            {"title": "Register in admin", "code": "admin.site.register(MyModel)"},
        ],
        "URLs": [
            {"title": "URL imports", "code": "from django.urls import path, include"},
            {"title": "urlpatterns", "code": "urlpatterns = []"},
        ],
        "Settings": [
            {"title": "Templates dir", "code": 'BASE_DIR / "templates"'},
            {"title": "Static files", "code": 'STATICFILES_DIRS = [BASE_DIR / "static"]'},
        ],
        "Admin": [
            {"title": "Create superuser", "code": "pipenv run python manage.py createsuperuser"},
        ],
        "Testing": [
            {"title": "Run tests", "code": "pipenv run python manage.py test"},
        ],
    },
    "Git": {
        "Basics": [
            {"title": "Init repo", "code": "git init"},
            {"title": "Check status", "code": "git status"},
            {"title": "Stage all", "code": "git add -A"},
            {"title": "Commit", "code": 'git commit -m "message"'},
        ],
        "Remote": [
            {"title": "Add remote", "code": "git remote add origin <url>"},
            {"title": "Rename branch to main", "code": "git branch -M main"},
            {"title": "Push and track", "code": "git push -u origin main"},
        ],
        "Other": [
            {"title": ".gitignore note", "code": "# Add .gitignore to project root"},
        ],
    },
}


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_DATA


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


class CheatSheetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Programmer's Cheat Sheet")
        self.root.geometry("820x560")
        self.root.configure(bg="#1e1e2e")
        self.root.minsize(700, 450)

        self.data = load_data()
        self.selected_path = []  # [lang] or [lang, topic]

        self._build_ui()
        self._populate_tree()

    # ── UI construction ────────────────────────────────────────────────────
    def _build_ui(self):
        # ── left panel: tree ──
        left = tk.Frame(self.root, bg="#181825", width=220)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 0), pady=8)
        left.pack_propagate(False)

        tk.Label(left, text="📂 Snippets", bg="#181825", fg="#cdd6f4",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=8, pady=(8, 4))

        tree_frame = tk.Frame(left, bg="#181825")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=4)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#1e1e2e", foreground="#cdd6f4",
                         fieldbackground="#1e1e2e", rowheight=24, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#313244", foreground="#cdd6f4")
        style.map("Treeview", background=[("selected", "#45475a")], foreground=[("selected", "#cdd6f4")])

        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # tree buttons
        btn_row = tk.Frame(left, bg="#181825")
        btn_row.pack(fill=tk.X, padx=4, pady=(2, 6))
        self._small_btn(btn_row, "+ Lang", self._add_language).pack(side=tk.LEFT, padx=2)
        self._small_btn(btn_row, "+ Topic", self._add_topic).pack(side=tk.LEFT, padx=2)
        self._small_btn(btn_row, "🗑", self._delete_node, danger=True).pack(side=tk.RIGHT, padx=2)

        # ── right panel: snippets ──
        right = tk.Frame(self.root, bg="#1e1e2e")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.panel_title = tk.Label(right, text="Select a topic", bg="#1e1e2e",
                                    fg="#89b4fa", font=("Segoe UI", 13, "bold"), anchor="w")
        self.panel_title.pack(fill=tk.X, pady=(0, 6))

        # snippet list frame (scrollable)
        canvas_container = tk.Frame(right, bg="#1e1e2e")
        canvas_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_container, bg="#1e1e2e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.snippet_frame = tk.Frame(self.canvas, bg="#1e1e2e")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.snippet_frame, anchor="nw")

        self.snippet_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # add snippet button
        add_row = tk.Frame(right, bg="#1e1e2e")
        add_row.pack(fill=tk.X, pady=(6, 0))
        self._btn(add_row, "+ Add Snippet", self._add_snippet).pack(side=tk.LEFT)

    def _btn(self, parent, text, cmd, danger=False):
        c = "#f38ba8" if danger else "#89b4fa"
        b = tk.Button(parent, text=text, command=cmd, bg="#313244", fg=c,
                      activebackground="#45475a", activeforeground=c,
                      relief=tk.FLAT, padx=10, pady=4, font=("Segoe UI", 9),
                      cursor="hand2")
        return b

    def _small_btn(self, parent, text, cmd, danger=False):
        c = "#f38ba8" if danger else "#a6e3a1"
        return tk.Button(parent, text=text, command=cmd, bg="#313244", fg=c,
                         activebackground="#45475a", activeforeground=c,
                         relief=tk.FLAT, padx=5, pady=2, font=("Segoe UI", 8),
                         cursor="hand2")

    # ── tree helpers ───────────────────────────────────────────────────────
    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        for lang, topics in self.data.items():
            lang_node = self.tree.insert("", "end", text=f"  {lang}", iid=lang, open=True)
            for topic in topics:
                self.tree.insert(lang_node, "end", text=f"    {topic}", iid=f"{lang}||{topic}")

    def _on_tree_select(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        if "||" in iid:
            lang, topic = iid.split("||", 1)
            self.selected_path = [lang, topic]
            self._render_snippets(lang, topic)
        else:
            self.selected_path = [iid]
            self._clear_snippets(iid)

    # ── snippet rendering ──────────────────────────────────────────────────
    def _clear_snippets(self, title="Select a topic"):
        for w in self.snippet_frame.winfo_children():
            w.destroy()
        self.panel_title.config(text=title)

    def _render_snippets(self, lang, topic):
        self._clear_snippets(f"{lang}  ›  {topic}")
        snippets = self.data.get(lang, {}).get(topic, [])

        if not snippets:
            tk.Label(self.snippet_frame, text="No snippets yet. Add one below!",
                     bg="#1e1e2e", fg="#6c7086", font=("Segoe UI", 10)).pack(pady=20)
            return

        for idx, snippet in enumerate(snippets):
            self._snippet_card(idx, snippet, lang, topic)

    def _snippet_card(self, idx, snippet, lang, topic):
        card = tk.Frame(self.snippet_frame, bg="#313244", pady=6, padx=8)
        card.pack(fill=tk.X, pady=4)

        # header row
        header = tk.Frame(card, bg="#313244")
        header.pack(fill=tk.X)

        tk.Label(header, text=snippet["title"], bg="#313244", fg="#cba6f7",
                 font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

        # action buttons
        tk.Button(header, text="🗑", command=lambda i=idx: self._delete_snippet(lang, topic, i),
                  bg="#313244", fg="#f38ba8", activebackground="#45475a",
                  relief=tk.FLAT, font=("Segoe UI", 9), cursor="hand2").pack(side=tk.RIGHT, padx=(2, 0))
        tk.Button(header, text="✏", command=lambda i=idx: self._edit_snippet(lang, topic, i),
                  bg="#313244", fg="#fab387", activebackground="#45475a",
                  relief=tk.FLAT, font=("Segoe UI", 9), cursor="hand2").pack(side=tk.RIGHT, padx=2)

        # copy button
        copy_btn = tk.Button(header, text="⎘ Copy",
                             command=lambda c=snippet["code"]: self._copy(c),
                             bg="#89b4fa", fg="#1e1e2e", activebackground="#74c7ec",
                             relief=tk.FLAT, font=("Segoe UI", 9, "bold"),
                             padx=8, cursor="hand2")
        copy_btn.pack(side=tk.RIGHT, padx=4)

        # code block
        code_bg = "#181825"
        code_frame = tk.Frame(card, bg=code_bg, pady=4, padx=6)
        code_frame.pack(fill=tk.X, pady=(4, 0))

        code_lbl = tk.Text(code_frame, bg=code_bg, fg="#a6e3a1", font=("Courier New", 10),
                           relief=tk.FLAT, height=snippet["code"].count("\n") + 1,
                           wrap=tk.NONE, state=tk.DISABLED, cursor="arrow",
                           selectbackground="#45475a")
        code_lbl.config(state=tk.NORMAL)
        code_lbl.insert("1.0", snippet["code"])
        code_lbl.config(state=tk.DISABLED)
        code_lbl.pack(fill=tk.X)

    def _copy(self, code):
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        self.root.update()

    # ── scroll wiring ──────────────────────────────────────────────────────
    def _on_frame_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── CRUD operations ────────────────────────────────────────────────────
    def _add_language(self):
        lang = simpledialog.askstring("New Language/Framework", "Enter name:", parent=self.root)
        if lang and lang.strip():
            lang = lang.strip()
            if lang not in self.data:
                self.data[lang] = {}
                save_data(self.data)
                self._populate_tree()

    def _add_topic(self):
        if not self.selected_path:
            messagebox.showinfo("Select first", "Select a language first.")
            return
        lang = self.selected_path[0]
        topic = simpledialog.askstring("New Topic", f"Topic under '{lang}':", parent=self.root)
        if topic and topic.strip():
            topic = topic.strip()
            if topic not in self.data.get(lang, {}):
                self.data[lang][topic] = []
                save_data(self.data)
                self._populate_tree()
                self.tree.selection_set(f"{lang}||{topic}")
                self._render_snippets(lang, topic)

    def _delete_node(self):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        if "||" in iid:
            lang, topic = iid.split("||", 1)
            if messagebox.askyesno("Delete", f"Delete topic '{topic}' and all its snippets?"):
                del self.data[lang][topic]
                save_data(self.data)
                self._populate_tree()
                self._clear_snippets()
        else:
            if messagebox.askyesno("Delete", f"Delete language '{iid}' and everything in it?"):
                del self.data[iid]
                save_data(self.data)
                self._populate_tree()
                self._clear_snippets()

    def _add_snippet(self):
        if len(self.selected_path) < 2:
            messagebox.showinfo("Select a topic", "Select a topic from the tree first.")
            return
        lang, topic = self.selected_path[0], self.selected_path[1]
        dlg = SnippetDialog(self.root, "Add Snippet")
        if dlg.result:
            self.data[lang][topic].append(dlg.result)
            save_data(self.data)
            self._render_snippets(lang, topic)

    def _edit_snippet(self, lang, topic, idx):
        snippet = self.data[lang][topic][idx]
        dlg = SnippetDialog(self.root, "Edit Snippet", snippet)
        if dlg.result:
            self.data[lang][topic][idx] = dlg.result
            save_data(self.data)
            self._render_snippets(lang, topic)

    def _delete_snippet(self, lang, topic, idx):
        if messagebox.askyesno("Delete", "Delete this snippet?"):
            self.data[lang][topic].pop(idx)
            save_data(self.data)
            self._render_snippets(lang, topic)


class SnippetDialog(simpledialog.Dialog):
    def __init__(self, parent, title, existing=None):
        self.existing = existing or {}
        self.result = None
        super().__init__(parent, title)

    def body(self, master):
        master.configure(bg="#1e1e2e")
        tk.Label(master, text="Title:", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", pady=4, padx=4)
        self.title_var = tk.StringVar(value=self.existing.get("title", ""))
        tk.Entry(master, textvariable=self.title_var, width=40,
                 bg="#313244", fg="#cdd6f4", insertbackground="#cdd6f4",
                 relief=tk.FLAT, font=("Segoe UI", 10)).grid(row=0, column=1, pady=4, padx=4)

        tk.Label(master, text="Code:", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Segoe UI", 10)).grid(row=1, column=0, sticky="nw", pady=4, padx=4)
        self.code_text = tk.Text(master, width=40, height=5, bg="#313244", fg="#a6e3a1",
                                 insertbackground="#cdd6f4", relief=tk.FLAT,
                                 font=("Courier New", 10))
        self.code_text.insert("1.0", self.existing.get("code", ""))
        self.code_text.grid(row=1, column=1, pady=4, padx=4)
        return self.code_text

    def apply(self):
        title = self.title_var.get().strip()
        code = self.code_text.get("1.0", tk.END).strip()
        if title and code:
            self.result = {"title": title, "code": code}

    def buttonbox(self):
        box = tk.Frame(self, bg="#1e1e2e")
        tk.Button(box, text="Save", command=self.ok, bg="#89b4fa", fg="#1e1e2e",
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=12, pady=4).pack(side=tk.LEFT, padx=4)
        tk.Button(box, text="Cancel", command=self.cancel, bg="#313244", fg="#cdd6f4",
                  font=("Segoe UI", 10), relief=tk.FLAT, padx=12, pady=4).pack(side=tk.LEFT)
        box.pack(pady=8)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)


if __name__ == "__main__":
    root = tk.Tk()
    app = CheatSheetApp(root)
    root.mainloop()
