"""Загрузка датасета UCI «Default of credit card clients» (Тайвань, 2005).

30 000 заёмщиков, 23 признака, целевая переменная — выход в дефолт в следующем
месяце. Регистрация и ключи не нужны.
"""
import io, zipfile, urllib.request, pathlib
import pandas as pd

URL = "https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip"
OUT = pathlib.Path("data/credit.csv")

def main() -> None:
    OUT.parent.mkdir(exist_ok=True)
    raw = urllib.request.urlopen(URL, timeout=120).read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name = z.namelist()[0]
        with z.open(name) as f:
            df = pd.read_excel(f, header=1)          # первая строка — служебная
    df = df.rename(columns={"default payment next month": "default"})
    df.to_csv(OUT, index=False)
    print(f"сохранено: {OUT} | {df.shape[0]} строк, {df.shape[1]} столбцов")
    print(f"доля дефолтов: {df['default'].mean():.1%}")

if __name__ == "__main__":
    main()
