import ast
import math
import operator
import re
import tkinter as tk

# =========================
# PENGATURAN (ubah di sini)
# =========================
TEMA = "gelap"  # pilih: "gelap", "biru", atau "ungu"

# Warna dasar untuk semua tema (kode hex #rrggbb).
WARNA_DASAR = {
    "bg": "#111318",        # latar jendela
    "layar": "#7EC7F5",     # latar layar
    "fungsi": "#1677e6",    # MC MR sin cos asin x^y dst.
    "angka": "#1677e6",     # tombol angka, titik, +/-
    "operator": "#034072",  # C ⌫ % ÷ × − +
    "sama": "#57a3d6",      # tombol =
}

# Tiap tema hanya menulis warna yang BERBEDA dari WARNA_DASAR.
TEMA_WARNA = {
    "gelap": {},
    "biru": {"bg": "#0b1220"},
    "ungu": {"bg": "#140f1f"},
}
WARNA = {**WARNA_DASAR, **TEMA_WARNA[TEMA]}

# Warna khusus untuk tombol tertentu (kunci = tulisan di tombol). Kosongkan {} untuk mematikan.
WARNA_KHUSUS = {"8": "#1677e6", "3": "#1677e6"}

FG_LAYAR = "black"    # tulisan di layar
FG_TOMBOL = "black"   # tulisan di tombol dan daftar riwayat
MAKS_RIWAYAT = 100    # jumlah riwayat yang disimpan
LEBAR_KALKULATOR, LEBAR_RIWAYAT, TINGGI = 430, 270, 640

# =========================
# SUSUNAN TOMBOL
# =========================
BARIS_ATAS = [
    ["MC", "MR", "M+", "M-", "DEG"],
    ["sin", "cos", "tan", "(", ")"],
    ["asin", "acos", "atan", "π", "e"],
    ["x^y", "√", "log", "ln", "x!"],
]
BARIS_UTAMA = [
    ["C", "⌫", "%", "÷"],
    ["7", "8", "9", "×"],
    ["4", "5", "6", "−"],
    ["1", "2", "3", "+"],
    ["+/-", "0", ".", "="],
]
# Tulisan yang diketik ke layar kalau berbeda dari tulisan tombolnya.
SISIP = {
    "sin": "sin(", "cos": "cos(", "tan": "tan(",
    "asin": "asin(", "acos": "acos(", "atan": "atan(",
    "x^y": "^", "√": "√(", "log": "log(", "ln": "ln(", "x!": "!", "−": "-",
}
TOMBOL_OPERATOR = set("C⌫%÷×−+")
PACK_PANEL = dict(side="left", fill="both", expand=True, padx=(0, 8), pady=8)


class KalkulatorIlmiah:
    KONSTANTA = {"pi": math.pi, "e": math.e}
    OPERATOR = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    }
    UNARY = {ast.USub: operator.neg, ast.UAdd: operator.pos}

    def __init__(self, root):
        self.root = root
        root.title("Kalkulator Ilmiah")
        root.geometry(f"{LEBAR_KALKULATOR + LEBAR_RIWAYAT}x{TINGGI}")
        root.resizable(False, False)
        root.configure(bg=WARNA["bg"])

        self.expression = tk.StringVar()
        self.result = tk.StringVar()
        self.expression.trace_add("write", lambda *a: self.result.set(""))
        self.mode = "DEG"
        self.memory = 0
        self.riwayat = []          # daftar (ekspresi, hasil); terbaru di akhir
        self.riwayat_terlihat = True

        # Perintah tombol. Tombol yang tidak ada di sini hanya mengetik tulisannya.
        self.aksi = {
            "C": self.clear, "⌫": self.backspace, "=": self.hitung, "+/-": self.negatif,
            "MC": self.memory_clear, "MR": lambda: self.tambah(str(self.memory)),
            "M+": lambda: self.memori(1), "M-": lambda: self.memori(-1),
            "DEG": self.change_mode,
        }
        self.fungsi = self.buat_fungsi()
        self.buat_gui()

        root.bind("<Return>", lambda e: self.hitung())
        root.bind("<Escape>", lambda e: self.clear())
        root.bind("<Control-h>", lambda e: self.toggle_riwayat())

    # =========================
    # GUI
    # =========================
    def buat_gui(self):
        bg = WARNA["bg"]
        self.kiri = tk.Frame(self.root, bg=bg, width=LEBAR_KALKULATOR)
        self.kiri.pack(side="left", fill="y")
        self.kiri.pack_propagate(False)

        # Layar
        layar = tk.Frame(self.kiri, bg=WARNA["layar"], height=130)
        layar.pack(fill="x", padx=8, pady=8)

        self.buat_tombol(layar, "Riwayat", self.toggle_riwayat, WARNA["fungsi"],
                         font=("Arial", 9, "bold"), width=0, padx=8, pady=1).place(x=8, y=4)

        self.entry = tk.Entry(
            layar, textvariable=self.expression, font=("Arial", 22), bd=0,
            bg=WARNA["layar"], fg=FG_LAYAR, insertbackground=FG_LAYAR, justify="right",
        )
        self.entry.pack(fill="x", padx=15, pady=(25, 5))
        self.entry.focus_set()

        tk.Label(
            layar, textvariable=self.result, font=("Arial", 28, "bold"),
            bg=WARNA["layar"], fg=FG_LAYAR, anchor="e",
        ).pack(fill="x", padx=15, pady=(0, 10))

        # Baris tombol atas (memory, trigonometri, dst.)
        for baris in BARIS_ATAS:
            frame = tk.Frame(self.kiri, bg=bg)
            frame.pack(fill="x", padx=8)
            for t in baris:
                btn = self.buat_tombol(frame, t, self.perintah(t), WARNA["fungsi"])
                btn.pack(side="left", expand=True, fill="x", padx=2, pady=3)
                if t == "DEG":
                    self.btn_mode = btn  # simpan agar tulisannya bisa diubah

        # Tombol utama (4 kolom x 5 baris)
        grid = tk.Frame(self.kiri, bg=bg)
        grid.pack(fill="both", expand=True, padx=8, pady=5)
        for r, baris in enumerate(BARIS_UTAMA):
            grid.rowconfigure(r, weight=1)
            for c, t in enumerate(baris):
                if t in TOMBOL_OPERATOR:
                    warna = WARNA["operator"]
                elif t == "=":
                    warna = WARNA["sama"]
                else:
                    warna = WARNA["angka"]
                btn = self.buat_tombol(grid, t, self.perintah(t), WARNA_KHUSUS.get(t, warna),
                                       font=("Arial", 15, "bold"))
                btn.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")
        for c in range(4):
            grid.columnconfigure(c, weight=1, uniform="kolom")

        self.buat_panel_riwayat()

    def buat_tombol(self, parent, teks, perintah, bg,
                    font=("Arial", 11, "bold"), width=6, **opsi):
        return tk.Button(
            parent, text=teks, command=perintah, bg=bg, fg=FG_TOMBOL, font=font, width=width,
            activebackground="#555555", activeforeground=FG_TOMBOL, relief="flat", bd=0, **opsi,
        )

    def perintah(self, t):
        """Perintah untuk tombol bertulisan t."""
        return self.aksi.get(t) or (lambda: self.tambah(SISIP.get(t, t)))

    # =========================
    # Input (mengikuti posisi kursor / teks yang diblok)
    # =========================
    def hapus_pilihan(self):
        """Hapus teks yang diblok di layar. True jika ada yang dihapus."""
        if self.entry.selection_present():
            awal = self.entry.index("sel.first")
            self.entry.delete(awal, self.entry.index("sel.last"))
            self.entry.icursor(awal)  # kursor ke tempat teks yang dihapus tadi
            return True
        return False

    def tambah(self, nilai):
        self.hapus_pilihan()  # teks yang diblok diganti
        self.entry.insert(self.entry.index("insert"), nilai)
        self.entry.focus_set()

    def clear(self):
        self.expression.set("")
        self.result.set("")

    def backspace(self):
        if not self.expression.get():
            self.result.set("")
        elif not self.hapus_pilihan():
            pos = self.entry.index("insert")
            if pos > 0:
                self.entry.delete(pos - 1)  # hapus karakter di kiri kursor
        self.entry.focus_set()

    def negatif(self):
        teks = self.expression.get()
        if teks:
            self.expression.set(teks[1:] if teks.startswith("-") else "-" + teks)

    # =========================
    # Riwayat
    # =========================
    def buat_panel_riwayat(self):
        bg = WARNA["bg"]
        self.panel_riwayat = tk.Frame(self.root, bg=bg)
        self.panel_riwayat.pack(**PACK_PANEL)

        tk.Label(self.panel_riwayat, text="Riwayat", font=("Arial", 14, "bold"),
                 bg=bg, fg="white", anchor="w").pack(fill="x", padx=4, pady=(0, 6))

        # Tombol hapus (di bawah panel)
        frame_btn = tk.Frame(self.panel_riwayat, bg=bg)
        frame_btn.pack(side="bottom", fill="x", pady=(6, 0))
        for teks, perintah, warna in [("Hapus Terpilih", self.hapus_terpilih, WARNA["angka"]),
                                      ("Hapus Semua", self.hapus_riwayat, WARNA["operator"])]:
            self.buat_tombol(frame_btn, teks, perintah, warna, font=("Arial", 9, "bold"),
                             width=12).pack(side="left", expand=True, fill="x", padx=2)

        # Daftar riwayat + scrollbar
        frame_list = tk.Frame(self.panel_riwayat, bg=bg)
        frame_list.pack(fill="both", expand=True)
        scroll_y = tk.Scrollbar(frame_list, orient="vertical")
        scroll_x = tk.Scrollbar(frame_list, orient="horizontal")
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")

        self.list_riwayat = tk.Listbox(
            frame_list, font=("Arial", 12), bg=WARNA["fungsi"], fg=FG_TOMBOL,
            selectbackground=WARNA["angka"], selectforeground=FG_TOMBOL,
            activestyle="none", bd=0, highlightthickness=0, exportselection=False,
            yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set,
        )
        self.list_riwayat.pack(side="left", fill="both", expand=True)
        scroll_y.config(command=self.list_riwayat.yview)
        scroll_x.config(command=self.list_riwayat.xview)
        self.segarkan_riwayat()

    def toggle_riwayat(self):
        """Tampilkan / sembunyikan panel riwayat."""
        self.riwayat_terlihat = not self.riwayat_terlihat
        if self.riwayat_terlihat:
            self.panel_riwayat.pack(**PACK_PANEL)
            lebar = LEBAR_KALKULATOR + LEBAR_RIWAYAT
        else:
            self.panel_riwayat.pack_forget()
            lebar = LEBAR_KALKULATOR
        self.root.geometry(f"{lebar}x{TINGGI}")

    def segarkan_riwayat(self):
        """Isi ulang daftar (terbaru di paling atas)."""
        self.list_riwayat.delete(0, "end")
        if not self.riwayat:
            self.list_riwayat.insert("end", "(belum ada riwayat)")
        for ekspresi, hasil in reversed(self.riwayat):
            self.list_riwayat.insert("end", f"{ekspresi} = {hasil}")

    def catat_riwayat(self, ekspresi, hasil):
        if self.riwayat and self.riwayat[-1] == (ekspresi, hasil):
            return  # hindari duplikat berturut-turut
        self.riwayat.append((ekspresi, hasil))
        del self.riwayat[:-MAKS_RIWAYAT]  # batasi jumlahnya
        self.segarkan_riwayat()

    def hapus_terpilih(self):
        pilihan = self.list_riwayat.curselection()
        if not self.riwayat or not pilihan:
            return
        idx = pilihan[0]
        del self.riwayat[-1 - idx]  # daftar ditampilkan terbalik
        self.segarkan_riwayat()
        if self.riwayat:  # pilih baris di dekatnya agar bisa langsung hapus lagi
            self.list_riwayat.selection_set(min(idx, len(self.riwayat) - 1))

    def hapus_riwayat(self):
        self.riwayat.clear()
        self.segarkan_riwayat()

    # =========================
    # Hitung
    # =========================
    def buat_fungsi(self):
        """Fungsi ilmiah yang boleh dipakai di ekspresi."""
        ke_radian = lambda x: math.radians(x) if self.mode == "DEG" else x
        dari_radian = lambda x: math.degrees(x) if self.mode == "DEG" else x

        def fakt(x):
            if x < 0 or x > 170 or not float(x).is_integer():
                raise ValueError("Faktorial tidak valid")
            return float(math.factorial(int(x)))

        return {
            "sin": lambda x: math.sin(ke_radian(x)),
            "cos": lambda x: math.cos(ke_radian(x)),
            "tan": lambda x: math.tan(ke_radian(x)),
            "asin": lambda x: dari_radian(math.asin(x)),
            "acos": lambda x: dari_radian(math.acos(x)),
            "atan": lambda x: dari_radian(math.atan(x)),
            "sqrt": math.sqrt, "log": math.log10, "ln": math.log, "fakt": fakt,
        }

    def evaluasi(self, node):
        """Evaluator aman berbasis AST (pengganti eval)."""
        if isinstance(node, ast.Expression):
            return self.evaluasi(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id in self.KONSTANTA:
            return self.KONSTANTA[node.id]
        if isinstance(node, ast.UnaryOp) and type(node.op) in self.UNARY:
            return self.UNARY[type(node.op)](self.evaluasi(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in self.OPERATOR:
            return self.OPERATOR[type(node.op)](self.evaluasi(node.left), self.evaluasi(node.right))
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in self.fungsi and len(node.args) == 1 and not node.keywords):
            return self.fungsi[node.func.id](self.evaluasi(node.args[0]))
        raise ValueError("Ekspresi tidak valid")

    def hitung(self):
        try:
            asli = self.expression.get().strip()
            if not asli:
                return
            if len(asli) > 200:
                raise ValueError("Terlalu panjang")

            # Simbol tampilan -> bentuk yang dipahami Python
            teks = (asli.replace("÷", "/").replace("×", "*")
                    .replace("√", "sqrt").replace("π", "pi"))

            # Persen ala kalkulator HP: 50+10% -> 55
            m = re.fullmatch(r"(\d+\.?\d*)\s*([+\-])\s*(\d+\.?\d*)%", teks)
            if m:
                a, op, b = m.groups()
                teks = f"{a}{op}({a}*{b}/100)"
            else:
                teks = teks.replace("%", "/100")

            teks = self.proses_faktorial(teks).replace("^", "**")
            teks = self.perkalian_implisit(teks)
            hasil = self.evaluasi(ast.parse(teks, mode="eval"))

            if isinstance(hasil, complex) or not math.isfinite(hasil):
                raise ValueError("Hasil tidak valid")

            hasil = round(hasil, 10)
            if hasil.is_integer() and abs(hasil) < 1e15:
                tampil = str(int(hasil))
            else:
                tampil = f"{hasil:.10g}"

            self.result.set(tampil)
            self.catat_riwayat(asli, tampil)
        except Exception:
            self.result.set("Error")

    def perkalian_implisit(self, teks):
        """2pi -> 2*pi, 3sin(30) -> 3*sin(30), )( -> )*("""
        token = re.findall(r"\d+\.?\d*|\.\d+|[A-Za-z_]+|\S", teks)
        angka = lambda t: t[0].isdigit() or (t[0] == "." and len(t) > 1)

        hasil = []
        for t in token:
            akhir_operand = hasil and (angka(hasil[-1]) or hasil[-1] == ")" or hasil[-1] in self.KONSTANTA)
            awal_operand = angka(t) or t == "(" or t[0].isalpha()
            if akhir_operand and awal_operand:
                if angka(hasil[-1]) and angka(t):
                    raise ValueError("Dua angka berurutan")
                hasil.append("*")
            hasil.append(t)
        return "".join(hasil)

    def proses_faktorial(self, teks):
        """5! atau (3+2)! atau (3!)! -> fakt(...)"""
        while "!" in teks:
            pos = teks.find("!")
            i = pos - 1
            if i >= 0 and teks[i] == ")":  # kasus (3+2)!: cari kurung buka pasangannya
                level = 0
                while i >= 0:
                    if teks[i] == ")":
                        level += 1
                    elif teks[i] == "(":
                        level -= 1
                        if level == 0:
                            break
                    i -= 1
                if i < 0:
                    raise ValueError("Kurung tidak seimbang")
            else:  # kasus 5!: ambil angka di sebelah kirinya
                while i >= 0 and (teks[i].isdigit() or teks[i] == "."):
                    i -= 1
                i += 1
                if i == pos:
                    raise ValueError("Faktorial tidak valid")
            teks = teks[:i] + f"fakt({teks[i:pos]})" + teks[pos + 1:]
        return teks

    # =========================
    # Mode DEG / RAD dan memory
    # =========================
    def change_mode(self):
        self.mode = "RAD" if self.mode == "DEG" else "DEG"
        self.btn_mode.config(text=self.mode)

    def memory_clear(self):
        self.memory = 0

    def memori(self, tanda):
        """M+ (tanda=1) atau M- (tanda=-1) dengan nilai hasil/ekspresi saat ini."""
        try:
            self.memory += tanda * float(self.result.get() or self.expression.get())
        except ValueError:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    KalkulatorIlmiah(root)
    root.mainloop()