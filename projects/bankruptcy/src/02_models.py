"""Обучение и сравнение моделей на всех пяти горизонтах прогноза.

Задача несбалансированная: банкротств от 3,9 % до 6,9 %. Поэтому главная метрика —
PR-AUC (точность-полнота), а не accuracy и даже не ROC-AUC: при доле событий 5 %
модель, которая всем говорит «не обанкротится», даёт 95 % правильных ответов и
нулевую пользу.
"""
import json, pathlib
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, roc_curve

SEED, TEST = 42, 0.30

def ks(y, p):
    fpr, tpr, _ = roc_curve(y, p)
    return float(np.max(tpr - fpr))

def models():
    imp = lambda: SimpleImputer(strategy="median")
    return {
        "Логистическая регрессия": make_pipeline(imp(), StandardScaler(),
            LogisticRegression(max_iter=3000, class_weight="balanced")),
        "Дерево решений (глубина 3)": make_pipeline(imp(),
            DecisionTreeClassifier(max_depth=3, class_weight="balanced", random_state=SEED)),
        "Случайный лес": make_pipeline(imp(),
            RandomForestClassifier(n_estimators=400, min_samples_leaf=5, class_weight="balanced_subsample",
                                   n_jobs=-1, random_state=SEED)),
        "Градиентный бустинг": HistGradientBoostingClassifier(
            max_iter=400, learning_rate=0.05, max_leaf_nodes=31, l2_regularization=1.0, random_state=SEED),
    }

def main() -> None:
    rows, store = [], {}
    for year in range(1, 6):
        df = pd.read_csv(f"data/year{year}.csv")
        h = int(df["horizon_years"].iloc[0])
        X = df.drop(columns=["bankrupt", "horizon_years"]); y = df["bankrupt"].astype(int)
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=TEST, stratify=y, random_state=SEED)
        cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
        for name, m in models().items():
            cvs = cross_val_score(m, Xtr, ytr, cv=cv, scoring="average_precision", n_jobs=1)
            m.fit(Xtr, ytr)
            p = m.predict_proba(Xte)[:, 1]
            auc = roc_auc_score(yte, p)
            rows.append({"горизонт": h, "модель": name, "ROC-AUC": auc, "Gini": 2*auc-1,
                         "PR-AUC": average_precision_score(yte, p), "KS": ks(yte, p),
                         "Brier": brier_score_loss(yte, p),
                         "PR-AUC на CV": cvs.mean(), "база PR": yte.mean()})
            if h == 1:
                store[name] = p
        print(f"горизонт {h} г. — готово")
    res = pd.DataFrame(rows)
    res.to_csv("outputs/metrics.csv", index=False)

    print("\n=== Горизонт 1 год (данные последнего года перед банкротством) ===")
    one = res[res["горизонт"] == 1].sort_values("PR-AUC", ascending=False)
    print(one[["модель","ROC-AUC","Gini","PR-AUC","KS","Brier","PR-AUC на CV"]].round(4).to_string(index=False))
    print(f"базовый уровень PR-AUC (доля банкротств) = {one['база PR'].iloc[0]:.3f}")

    print("\n=== Как качество падает с ростом горизонта (градиентный бустинг) ===")
    gb = res[res["модель"] == "Градиентный бустинг"].sort_values("горизонт")
    print(gb[["горизонт","ROC-AUC","PR-AUC","база PR"]].round(3).to_string(index=False))

    df = pd.read_csv("data/year5.csv")
    X = df.drop(columns=["bankrupt","horizon_years"]); y = df["bankrupt"].astype(int)
    _, Xte, _, yte = train_test_split(X, y, test_size=TEST, stratify=y, random_state=SEED)
    np.save("outputs/preds.npy", np.vstack([store[k] for k in store]))
    json.dump({"models": list(store), "y_test": yte.tolist()}, open("outputs/preds_meta.json","w"))

    miss = X.isna().mean().sort_values(ascending=False)
    miss[miss > 0].round(4).to_csv("outputs/missing.csv")
    print(f"\nпропуски: {(miss>0).sum()} признаков из {len(miss)}, худший — {miss.index[0]} ({miss.iloc[0]:.1%})")

if __name__ == "__main__":
    main()
