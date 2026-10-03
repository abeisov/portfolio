"""Интерпретация: какие коэффициенты важны, какие правила выделяет дерево
и что модель даёт на практике при разных порогах тревоги."""
import sys, json, pathlib
import numpy as np, pandas as pd
sys.path.insert(0, "src")
from ratios import RATIOS
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.impute import SimpleImputer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import average_precision_score

SEED, TEST = 42, 0.30
df = pd.read_csv("data/year5.csv")                 # горизонт 1 год
X = df.drop(columns=["bankrupt","horizon_years"]); y = df["bankrupt"].astype(int)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=TEST, stratify=y, random_state=SEED)

# ---- важность признаков у бустинга ----
gb = HistGradientBoostingClassifier(max_iter=400, learning_rate=0.05, max_leaf_nodes=31,
                                    l2_regularization=1.0, random_state=SEED).fit(Xtr, ytr)
pi = permutation_importance(gb, Xte, yte, n_repeats=10, random_state=SEED,
                            scoring="average_precision", n_jobs=-1)
imp = pd.DataFrame({"признак": X.columns, "важность": pi.importances_mean,
                    "sd": pi.importances_std}).sort_values("важность", ascending=False)
imp["смысл"] = imp["признак"].map(RATIOS)
imp.to_csv("outputs/importance.csv", index=False)
print("=== Что важнее всего для прогноза банкротства за год ===")
for _, r in imp.head(10).iterrows():
    print(f"  {r['признак']:7} {r['важность']:+.4f}  {r['смысл']}")

# ---- дерево как кредитная политика ----
imputer = SimpleImputer(strategy="median").fit(Xtr)
tree = DecisionTreeClassifier(max_depth=3, class_weight="balanced", random_state=SEED,
                              min_samples_leaf=50).fit(imputer.transform(Xtr), ytr)
rules = export_text(tree, feature_names=list(X.columns), decimals=3)
pathlib.Path("outputs/tree_rules.txt").write_text(rules, encoding="utf-8")
print("\n=== Правила дерева глубины 3 ===")
print(rules)
used = sorted({f for f in X.columns if f"{f} " in rules})
print("использованные коэффициенты:")
for f in used: print(f"  {f}: {RATIOS[f]}")

# ---- бизнес-срез: порог тревоги ----
p = gb.predict_proba(Xte)[:, 1]
rows = []
for q in [0.02, 0.05, 0.10, 0.15, 0.20, 0.30]:
    thr = np.quantile(p, 1 - q)
    flag = p >= thr
    caught = yte[flag].sum() / yte.sum()
    prec = yte[flag].mean()
    rows.append({"доля компаний на проверке": q, "порог вероятности": thr,
                 "поймано банкротств": caught, "точность сигнала": prec,
                 "ложных тревог на одно банкротство": (flag.sum() - yte[flag].sum()) / max(yte[flag].sum(), 1)})
cut = pd.DataFrame(rows)
cut.to_csv("outputs/cutoffs.csv", index=False)
print("\n=== Сколько проверять и сколько поймаем ===")
print(cut.assign(**{"доля компаний на проверке": lambda d: (d["доля компаний на проверке"]*100).round(0),
                    "поймано банкротств": lambda d: (d["поймано банкротств"]*100).round(1),
                    "точность сигнала": lambda d: (d["точность сигнала"]*100).round(1),
                    "порог вероятности": lambda d: d["порог вероятности"].round(3),
                    "ложных тревог на одно банкротство": lambda d: d["ложных тревог на одно банкротство"].round(1)}
                 ).to_string(index=False))

# ---- сравнение: полная модель против политики из правил ----
p_tree = tree.predict_proba(imputer.transform(Xte))[:, 1]
print(f"\nPR-AUC: бустинг {average_precision_score(yte, p):.3f} против дерева {average_precision_score(yte, p_tree):.3f}"
      f" при базовом уровне {yte.mean():.3f}")
json.dump({"used_rules_feats": used}, open("outputs/rules_meta.json","w"))
