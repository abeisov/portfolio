"""WoE-биннинг и расчёт Information Value — стандартный шаг построения скоркарты.

Биннинг настраивается ТОЛЬКО на обучающей выборке и затем применяется к тестовой,
иначе информация о тесте протекает в модель.
"""
import json, pathlib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

SRC = pathlib.Path("data/features.csv")
SEED, TEST_SIZE, MAX_BINS, MIN_FRAC = 42, 0.30, 6, 0.05

def fit_bins(x: pd.Series, y: pd.Series) -> list[float]:
    """Границы бинов по квантилям; категориальные колонки остаются как есть."""
    if x.nunique() <= MAX_BINS:
        return sorted(x.unique().tolist())
    qs = np.linspace(0, 1, MAX_BINS + 1)[1:-1]
    edges = sorted(set(np.quantile(x, qs)))
    return [-np.inf] + edges + [np.inf]

def apply_bins(x: pd.Series, edges: list[float]) -> pd.Series:
    if edges[0] != -np.inf:                      # дискретная переменная
        return x.astype(str)
    return pd.cut(x, bins=edges, labels=False, include_lowest=True).astype(str)

def woe_table(binned: pd.Series, y: pd.Series) -> pd.DataFrame:
    t = pd.crosstab(binned, y)
    t.columns = ["good", "bad"]
    t["n"] = t["good"] + t["bad"]
    t["bad_rate"] = t["bad"] / t["n"]
    # сглаживание 0.5, чтобы пустые бины не давали бесконечность
    gd = (t["good"] + 0.5) / (t["good"].sum() + 0.5 * len(t))
    bd = (t["bad"] + 0.5) / (t["bad"].sum() + 0.5 * len(t))
    t["woe"] = np.log(gd / bd)
    t["iv"] = (gd - bd) * t["woe"]
    return t

def main() -> None:
    df = pd.read_csv(SRC)
    X, y = df.drop(columns="target"), df["target"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=TEST_SIZE, stratify=y, random_state=SEED)

    bins, tables, iv = {}, {}, {}
    Wtr, Wte = pd.DataFrame(index=Xtr.index), pd.DataFrame(index=Xte.index)
    for c in X.columns:
        edges = fit_bins(Xtr[c], ytr)
        btr, bte = apply_bins(Xtr[c], edges), apply_bins(Xte[c], edges)
        t = woe_table(btr, ytr)
        m = t["woe"].to_dict()
        Wtr[c] = btr.map(m).astype(float)
        Wte[c] = bte.map(m).fillna(0).astype(float)
        bins[c], tables[c], iv[c] = [float(e) for e in edges], t, float(t["iv"].sum())

    ivs = pd.Series(iv).sort_values(ascending=False)
    print("=== Information Value ===")
    for k, v in ivs.items():
        sила = "очень сильный" if v > 0.5 else "сильный" if v > 0.3 else \
               "средний" if v > 0.1 else "слабый" if v > 0.02 else "бесполезный"
        print(f"  {k:18} {v:6.3f}   {sила}")

    pathlib.Path("data").mkdir(exist_ok=True)
    Wtr.assign(target=ytr.values).to_csv("data/woe_train.csv", index=False)
    Wte.assign(target=yte.values).to_csv("data/woe_test.csv", index=False)
    Xtr.assign(target=ytr.values).to_csv("data/raw_train.csv", index=False)
    Xte.assign(target=yte.values).to_csv("data/raw_test.csv", index=False)
    json.dump({"bins": bins, "iv": iv}, open("outputs/binning.json", "w"), ensure_ascii=False, indent=1)
    pd.concat({k: v for k, v in tables.items()}).to_csv("outputs/woe_tables.csv")
    print(f"\nобучение: {len(Xtr)}, тест: {len(Xte)} | дефолтов в тесте: {yte.mean():.1%}")

if __name__ == "__main__":
    main()
