"""
سيستم كافيه - برنامج ديسكتوب
Python + Tkinter + SQLite (مفيش مكتبات خارجية)
تشغيل:  python cafe_system.py
"""
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

DB_FILE = "cafe.db"
FONT = ("Tahoma", 11)
CURRENCY = "ج.م"


# ---------------------------------------------------------------- قاعدة البيانات
def db():
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 5);
        CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created TEXT, total REAL, payment TEXT);
        CREATE TABLE IF NOT EXISTS order_items(
            order_id INTEGER, product_id INTEGER,
            name TEXT, qty INTEGER, price REAL);
        """)
        if c.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            c.executemany(
                "INSERT INTO products(name,category,price,stock,min_stock) VALUES(?,?,?,?,?)",
                [
                    ("قهوة تركي", "مشروبات ساخنة", 30, 100, 10),
                    ("اسبريسو", "مشروبات ساخنة", 35, 100, 10),
                    ("كابتشينو", "مشروبات ساخنة", 45, 80, 10),
                    ("شاي", "مشروبات ساخنة", 20, 150, 10),
                    ("آيس لاتيه", "مشروبات باردة", 55, 60, 10),
                    ("عصير برتقال", "مشروبات باردة", 40, 40, 8),
                    ("كرواسون", "مخبوزات", 35, 25, 5),
                    ("تشيز كيك", "حلويات", 60, 15, 4),
                ],
            )


def money(x):
    return f"{x:,.2f} {CURRENCY}"


def make_tree(parent, cols, widths=None, height=15):
    """cols: list of (key, heading)"""
    tree = ttk.Treeview(parent, columns=[k for k, _ in cols], show="headings", height=height)
    for i, (k, h) in enumerate(cols):
        tree.heading(k, text=h)
        tree.column(k, width=(widths[i] if widths else 100), anchor="center")
    sb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    return tree, sb


# ---------------------------------------------------------------- الكاشير
class POSTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.cart = {}  # product_id -> [name, price, qty]

        # يمين: المنتجات
        left = ttk.Frame(self)
        left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        top = ttk.Frame(left)
        top.pack(fill="x")
        ttk.Label(top, text="بحث:").pack(side="right")
        self.q = tk.StringVar()
        self.q.trace_add("write", lambda *_: self.load())
        ttk.Entry(top, textvariable=self.q, font=FONT).pack(side="right", fill="x", expand=True, padx=4)

        wrap = ttk.Frame(left)
        wrap.pack(fill="both", expand=True, pady=6)
        self.prod, sb = make_tree(
            wrap,
            [("name", "المنتج"), ("cat", "القسم"), ("price", "السعر"), ("stock", "المتاح")],
            [180, 120, 80, 70],
        )
        self.prod.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self.prod.bind("<Double-1>", lambda e: self.add_selected())
        ttk.Button(left, text="إضافة للطلب  ➕", command=self.add_selected).pack(fill="x")

        # شمال: الطلب
        right = ttk.Frame(self)
        right.pack(side="left", fill="both", padx=8, pady=8)
        wrap2 = ttk.Frame(right)
        wrap2.pack(fill="both", expand=True)
        self.cart_tree, sb2 = make_tree(
            wrap2,
            [("name", "الصنف"), ("qty", "الكمية"), ("sub", "الإجمالي")],
            [150, 60, 90],
            height=12,
        )
        self.cart_tree.pack(side="left", fill="both", expand=True)
        sb2.pack(side="left", fill="y")

        btns = ttk.Frame(right)
        btns.pack(fill="x", pady=4)
        ttk.Button(btns, text="+", width=4, command=lambda: self.change_qty(1)).pack(side="left")
        ttk.Button(btns, text="−", width=4, command=lambda: self.change_qty(-1)).pack(side="left", padx=2)
        ttk.Button(btns, text="حذف", command=self.remove_item).pack(side="left")
        ttk.Button(btns, text="مسح الكل", command=self.clear).pack(side="right")

        self.total_var = tk.StringVar(value=money(0))
        ttk.Label(right, textvariable=self.total_var, font=("Tahoma", 16, "bold")).pack(pady=6)

        pay = ttk.Frame(right)
        pay.pack(fill="x")
        ttk.Label(pay, text="الدفع:").pack(side="right")
        self.payment = ttk.Combobox(pay, values=["كاش", "كارت", "محفظة"], state="readonly", width=10)
        self.payment.current(0)
        self.payment.pack(side="right", padx=4)

        ttk.Button(right, text="تأكيد الطلب ✔", command=self.checkout).pack(fill="x", pady=8, ipady=6)
        self.load()

    # --- المنتجات
    def load(self):
        self.prod.delete(*self.prod.get_children())
        q = f"%{self.q.get().strip()}%"
        with db() as c:
            rows = c.execute(
                "SELECT * FROM products WHERE name LIKE ? OR category LIKE ? ORDER BY category, name", (q, q)
            ).fetchall()
        for r in rows:
            self.prod.insert("", "end", iid=str(r["id"]),
                             values=(r["name"], r["category"], r["price"], r["stock"]))

    # --- الطلب
    def add_selected(self):
        sel = self.prod.selection()
        if not sel:
            return
        pid = int(sel[0])
        with db() as c:
            p = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        in_cart = self.cart.get(pid, [0, 0, 0])[2]
        if in_cart + 1 > p["stock"]:
            messagebox.showwarning("المخزون", f"المتاح من «{p['name']}» هو {p['stock']} بس")
            return
        if pid in self.cart:
            self.cart[pid][2] += 1
        else:
            self.cart[pid] = [p["name"], p["price"], 1]
        self.render_cart()

    def selected_cart_id(self):
        sel = self.cart_tree.selection()
        return int(sel[0]) if sel else None

    def change_qty(self, d):
        pid = self.selected_cart_id()
        if pid is None:
            return
        with db() as c:
            stock = c.execute("SELECT stock FROM products WHERE id=?", (pid,)).fetchone()["stock"]
        new = self.cart[pid][2] + d
        if new > stock:
            messagebox.showwarning("المخزون", f"المتاح {stock} بس")
            return
        if new <= 0:
            del self.cart[pid]
        else:
            self.cart[pid][2] = new
        self.render_cart(keep=pid)

    def remove_item(self):
        pid = self.selected_cart_id()
        if pid is not None:
            self.cart.pop(pid, None)
            self.render_cart()

    def clear(self):
        self.cart.clear()
        self.render_cart()

    def render_cart(self, keep=None):
        self.cart_tree.delete(*self.cart_tree.get_children())
        total = 0
        for pid, (name, price, qty) in self.cart.items():
            total += price * qty
            self.cart_tree.insert("", "end", iid=str(pid), values=(name, qty, f"{price * qty:g}"))
        if keep in self.cart:
            self.cart_tree.selection_set(str(keep))
        self.total_var.set(money(total))

    def checkout(self):
        if not self.cart:
            messagebox.showinfo("الطلب", "الطلب فاضي")
            return
        total = sum(p * q for _, p, q in self.cart.values())
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with db() as c:
            # تأكد من المخزون قبل الحفظ
            for pid, (name, _, qty) in self.cart.items():
                stock = c.execute("SELECT stock FROM products WHERE id=?", (pid,)).fetchone()["stock"]
                if qty > stock:
                    messagebox.showerror("المخزون", f"«{name}» متاح منه {stock} بس")
                    return
            oid = c.execute("INSERT INTO orders(created,total,payment) VALUES(?,?,?)",
                            (now, total, self.payment.get())).lastrowid
            for pid, (name, price, qty) in self.cart.items():
                c.execute("INSERT INTO order_items VALUES(?,?,?,?,?)", (oid, pid, name, qty, price))
                c.execute("UPDATE products SET stock = stock - ? WHERE id=?", (qty, pid))

        lines = [f"{n}  x{q}  =  {p * q:g}" for n, p, q in self.cart.values()]
        receipt = f"طلب رقم {oid}\n{now}\n{'-' * 28}\n" + "\n".join(lines) + \
                  f"\n{'-' * 28}\nالإجمالي: {money(total)}\nالدفع: {self.payment.get()}"
        self.cart.clear()
        self.render_cart()
        self.app.refresh_all()
        messagebox.showinfo("تم الطلب ✔", receipt)


# ---------------------------------------------------------------- المنتجات والمخزون
class ProductDialog(tk.Toplevel):
    def __init__(self, parent, on_save, product=None):
        super().__init__(parent)
        self.title("تعديل منتج" if product else "منتج جديد")
        self.resizable(False, False)
        self.on_save, self.product = on_save, product
        self.vars = {}
        fields = [("name", "الاسم"), ("category", "القسم"), ("price", "السعر"),
                  ("stock", "الكمية"), ("min_stock", "حد التنبيه")]
        for i, (k, label) in enumerate(fields):
            ttk.Label(self, text=label).grid(row=i, column=1, padx=10, pady=5, sticky="e")
            v = tk.StringVar(value=str(product[k]) if product else ("5" if k == "min_stock" else ""))
            self.vars[k] = v
            ttk.Entry(self, textvariable=v, width=25, font=FONT).grid(row=i, column=0, padx=10, pady=5)
        ttk.Button(self, text="حفظ", command=self.save).grid(row=len(fields), column=0, columnspan=2, pady=10)
        self.grab_set()

    def save(self):
        try:
            d = {
                "name": self.vars["name"].get().strip(),
                "category": self.vars["category"].get().strip(),
                "price": float(self.vars["price"].get()),
                "stock": int(self.vars["stock"].get()),
                "min_stock": int(self.vars["min_stock"].get()),
            }
            if not d["name"]:
                raise ValueError
        except ValueError:
            messagebox.showerror("خطأ", "راجع البيانات (الاسم مطلوب، والسعر/الكمية أرقام)", parent=self)
            return
        try:
            with db() as c:
                if self.product:
                    c.execute("UPDATE products SET name=?,category=?,price=?,stock=?,min_stock=? WHERE id=?",
                              (*d.values(), self.product["id"]))
                else:
                    c.execute("INSERT INTO products(name,category,price,stock,min_stock) VALUES(?,?,?,?,?)",
                              tuple(d.values()))
        except sqlite3.IntegrityError:
            messagebox.showerror("خطأ", "الاسم ده موجود قبل كده", parent=self)
            return
        self.on_save()
        self.destroy()


class InventoryTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=8)
        ttk.Button(bar, text="منتج جديد", command=self.add).pack(side="right")
        ttk.Button(bar, text="تعديل", command=self.edit).pack(side="right", padx=4)
        ttk.Button(bar, text="إضافة مخزون", command=self.restock).pack(side="right")
        ttk.Button(bar, text="حذف", command=self.delete).pack(side="left")
        self.warn = tk.StringVar()
        ttk.Label(bar, textvariable=self.warn, foreground="#c0392b").pack(side="left", padx=12)

        wrap = ttk.Frame(self)
        wrap.pack(fill="both", expand=True, padx=8, pady=4)
        self.tree, sb = make_tree(
            wrap,
            [("name", "المنتج"), ("cat", "القسم"), ("price", "السعر"), ("stock", "المخزون"), ("min", "حد التنبيه")],
            [200, 140, 90, 90, 90], height=18)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self.tree.tag_configure("low", foreground="#c0392b")
        self.load()

    def load(self):
        self.tree.delete(*self.tree.get_children())
        low = 0
        with db() as c:
            for r in c.execute("SELECT * FROM products ORDER BY category, name"):
                is_low = r["stock"] <= r["min_stock"]
                low += is_low
                self.tree.insert("", "end", iid=str(r["id"]), tags=("low",) if is_low else (),
                                 values=(r["name"], r["category"], r["price"], r["stock"], r["min_stock"]))
        self.warn.set(f"⚠ {low} منتج قرب يخلص" if low else "")

    def current(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("اختار منتج", "اختار منتج من الجدول الأول")
            return None
        with db() as c:
            return c.execute("SELECT * FROM products WHERE id=?", (int(sel[0]),)).fetchone()

    def add(self):
        ProductDialog(self, self.app.refresh_all)

    def edit(self):
        p = self.current()
        if p:
            ProductDialog(self, self.app.refresh_all, p)

    def restock(self):
        p = self.current()
        if not p:
            return
        win = tk.Toplevel(self)
        win.title("إضافة مخزون")
        v = tk.StringVar()
        ttk.Label(win, text=f"الكمية الجديدة لـ «{p['name']}»").pack(padx=12, pady=8)
        ttk.Entry(win, textvariable=v, font=FONT).pack(padx=12)

        def ok():
            try:
                n = int(v.get())
            except ValueError:
                return
            with db() as c:
                c.execute("UPDATE products SET stock = stock + ? WHERE id=?", (n, p["id"]))
            win.destroy()
            self.app.refresh_all()
        ttk.Button(win, text="إضافة", command=ok).pack(pady=10)
        win.grab_set()

    def delete(self):
        p = self.current()
        if p and messagebox.askyesno("حذف", f"تحذف «{p['name']}»؟"):
            with db() as c:
                c.execute("DELETE FROM products WHERE id=?", (p["id"],))
            self.app.refresh_all()


# ---------------------------------------------------------------- المبيعات
class SalesTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=8)
        ttk.Label(bar, text="الفترة:").pack(side="right")
        self.period = ttk.Combobox(bar, values=["النهاردة", "الكل"], state="readonly", width=10)
        self.period.current(0)
        self.period.pack(side="right", padx=4)
        self.period.bind("<<ComboboxSelected>>", lambda e: self.load())
        self.summary = tk.StringVar()
        ttk.Label(bar, textvariable=self.summary, font=("Tahoma", 12, "bold")).pack(side="left")

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=8)
        l = ttk.Frame(body)
        l.pack(side="left", fill="both", expand=True)
        ttk.Label(l, text="الطلبات").pack()
        self.orders, sb = make_tree(
            l, [("id", "#"), ("time", "الوقت"), ("total", "الإجمالي"), ("pay", "الدفع")],
            [50, 150, 90, 70], height=18)
        self.orders.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")

        r = ttk.Frame(body)
        r.pack(side="left", fill="both", expand=True, padx=(10, 0))
        ttk.Label(r, text="الأكثر مبيعًا").pack()
        self.top, sb2 = make_tree(r, [("name", "المنتج"), ("qty", "الكمية"), ("rev", "الإيراد")],
                                  [150, 70, 90], height=18)
        self.top.pack(side="left", fill="both", expand=True)
        sb2.pack(side="left", fill="y")
        self.load()

    def load(self):
        self.orders.delete(*self.orders.get_children())
        self.top.delete(*self.top.get_children())
        today = datetime.now().strftime("%Y-%m-%d")
        flt, args = ("WHERE created LIKE ?", (today + "%",)) if self.period.get() == "النهاردة" else ("", ())
        with db() as c:
            rows = c.execute(f"SELECT * FROM orders {flt} ORDER BY id DESC", args).fetchall()
            for r in rows:
                self.orders.insert("", "end", values=(r["id"], r["created"], f"{r['total']:g}", r["payment"]))
            ids = [r["id"] for r in rows]
            if ids:
                ph = ",".join("?" * len(ids))
                for r in c.execute(
                    f"SELECT name, SUM(qty) q, SUM(qty*price) rev FROM order_items "
                    f"WHERE order_id IN ({ph}) GROUP BY name ORDER BY q DESC LIMIT 20", ids):
                    self.top.insert("", "end", values=(r["name"], r["q"], f"{r['rev']:g}"))
        total = sum(r["total"] for r in rows)
        self.summary.set(f"عدد الطلبات: {len(rows)}   |   إجمالي المبيعات: {money(total)}")


# ---------------------------------------------------------------- التطبيق
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("سيستم الكافيه ☕")
        self.geometry("1000x620")
        ttk.Style(self).configure(".", font=FONT)
        ttk.Style(self).configure("Treeview", rowheight=26)
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)
        self.pos = POSTab(nb, self)
        self.inv = InventoryTab(nb, self)
        self.sales = SalesTab(nb, self)
        nb.add(self.pos, text="  الكاشير  ")
        nb.add(self.inv, text="  المنتجات والمخزون  ")
        nb.add(self.sales, text="  المبيعات  ")

    def refresh_all(self):
        self.pos.load()
        self.inv.load()
        self.sales.load()


if __name__ == "__main__":
    init_db()
    App().mainloop()
