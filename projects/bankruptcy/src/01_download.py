"""Загрузка датасета UCI «Polish companies bankruptcy data».

Пять файлов ARFF. Внимание на горизонт: в файле 1year финансовые коэффициенты
за первый год периода наблюдения, а метка — банкротство ЧЕРЕЗ ПЯТЬ лет.
В файле 5year — коэффициенты пятого года и банкротство через год.
То есть чем больше номер файла, тем короче горизонт прогноза.
"""
import io, zipfile, urllib.request, pathlib
import pandas as pd

URL = "https://archive.ics.uci.edu/static/public/365/polish+companies+bankruptcy+data.zip"
OUT = pathlib.Path("data")

def read_arff(text: str) -> pd.DataFrame:
    """Минимальный разбор ARFF: нам нужны только имена колонок и числа."""
    cols, rows, in_data = [], [], False
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("%"):
            continue
        low = s.lower()
        if low.startswith("@attribute"):
            cols.append(s.split()[1])
        elif low.startswith("@data"):
            in_data = True
        elif in_data:
            rows.append([None if v.strip() == "?" else float(v) for v in s.split(",")])
    return pd.DataFrame(rows, columns=cols)

def main() -> None:
    OUT.mkdir(exist_ok=True)
    raw = urllib.request.urlopen(URL, timeout=180).read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for n in sorted(z.namelist()):
            if not n.endswith(".arff"):
                continue
            year = int(n[0])
            df = read_arff(z.read(n).decode("utf-8", "ignore"))
            df = df.rename(columns={df.columns[-1]: "bankrupt"})
            df["horizon_years"] = 6 - year          # 1year -> 5 лет, 5year -> 1 год
            df.to_csv(OUT / f"year{year}.csv", index=False)
            print(f"{n}: {len(df):>6} компаний | банкротств {int(df.bankrupt.sum()):>4} "
                  f"({df.bankrupt.mean():.1%}) | горизонт {6-year} г.")

if __name__ == "__main__":
    main()
