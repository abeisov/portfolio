"""Обучение и сравнение моделей скоринга.

Три подхода к одной задаче:
  1. скоркарта  — логистическая регрессия на WoE, отобранные признаки, баллы;
  2. логит сырой — та же регрессия, но на исходных стандартизованных признаках;
  3. градиентный бустинг — верхняя граница качества без требований к интерпретируемости.
"""
import json, pathlib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, roc_curve

SEED = 42
PDO, BASE_SCORE, BASE_ODDS = 20, 600, 20      # параметры перевода вероятности в баллы
IV_MIN, CORR_MAX = 0.02, 0.80

def ks_stat(y, p):
    fpr, tpr, _ = roc_curve(y, p)
    return float(np.max(tpr - fpr))

def evaluate(y, p) -> dict:
    auc = roc_auc_score(y, p)
    return {"AUC": auc, "Gini": 2 * auc - 1, "KS": ks_stat(y, p),
            "PR-AUC": average_precision_score(y, p), "Brier": brier_score_loss(y, p)}

def select_features(W: pd.DataFrame, iv: dict) -> list[str]:
    """Отбор: IV выше порога, затем снятие мультиколлинеарности в пользу большего IV."""
    cand = sorted([c for c in W.columns if iv.get(c, 0) >= IV_MIN], key=lambda c: -iv[c])
    chosen: list[str] = []
    for c in cand:
        if all(abs(W[c].corr(W[k])) < CORR_MAX for k in chosen):
            chosen.append(c)
    return chosen

def main() -> None:
    Wtr = pd.read_csv("data/woe_train.csv"); Wte = pd.read_csv("data/woe_test.csv")
    Rtr = pd.read_csv("data/raw_train.csv"); Rte = pd.read_csv("data/raw_test.csv")
    ytr, yte = Wtr.pop("target"), Wte.pop("target")
    Rtr.pop("target"); Rte.pop("target")
    iv = json.load(open("outputs/binning.json"))["iv"]

    feats = select_features(Wtr, iv)
    print("отобрано признаков:", len(feats))
    print("  ", ", ".join(feats))
    dropped = [c for c in Wtr.columns if c not in feats]
    print("  отсеяно:", ", ".join(dropped))

    models = {
        "Скоркарта (логит на WoE)": (LogisticRegression(max_iter=1000, C=1.0), Wtr[feats], Wte[feats]),
        "Логит на сырых признаках": (make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)), Rtr, Rte),
        "Градиентный бустинг": (HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06,
                                                               max_leaf_nodes=15, random_state=SEED), Rtr, Rte),
    }
    cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
    rows, preds = [], {}
    for name, (model, Xtr, Xte) in models.items():
        cvs = cross_val_score(model, Xtr, ytr, cv=cv, scoring="roc_auc")
        model.fit(Xtr, ytr)
        p = model.predict_proba(Xte)[:, 1]
        preds[name] = p
        m = evaluate(yte, p)
        m["AUC на кросс-валидации"] = f"{cvs.mean():.4f} ± {cvs.std():.4f}"
        m["модель"] = name
        rows.append(m)
        models[name] = (model, Xtr, Xte)

    res = pd.DataFrame(rows).set_index("модель")
    print("\n=== Качество на отложенной выборке (9000 заёмщиков) ===")
    print(res[["AUC", "Gini", "KS", "PR-AUC", "Brier", "AUC на кросс-валидации"]].round(4).to_string())

    # ---- скоркарта в баллах ----
    sc_model = models["Скоркарта (логит на WoE)"][0]
    factor = PDO / np.log(2)
    offset = BASE_SCORE - factor * np.log(BASE_ODDS)
    coefs = pd.Series(sc_model.coef_[0], index=feats)
    card = pd.read_csv("outputs/woe_tables.csv", index_col=[0, 1])
    card = card[card.index.get_level_values(0).isin(feats)].copy()
    card["points"] = [
        -factor * coefs[f] * w - (factor * sc_model.intercept_[0] - offset) / len(feats)
        for f, w in zip(card.index.get_level_values(0), card["woe"])
    ]
    card["points"] = card["points"].round(0)
    card.to_csv("outputs/scorecard.csv")
    print(f"\nскоркарта: {len(card)} строк баллов, разброс {card['points'].min():.0f}—{card['points'].max():.0f}")

    # ---- бизнес-срез: сколько одобряем и какой дефолт получаем ----
    p_sc = preds["Скоркарта (логит на WoE)"]
    score = offset - factor * np.log(p_sc / (1 - p_sc))
    df = pd.DataFrame({"score": score, "y": yte.values}).sort_values("score", ascending=False)
    cuts = []
    for rate in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        k = int(len(df) * rate)
        sub = df.head(k)
        cuts.append({"одобрение": rate, "порог балла": round(sub["score"].iloc[-1]),
                     "дефолт среди одобренных": sub["y"].mean(),
                     "поймано дефолтов, %": 1 - sub["y"].sum() / df["y"].sum()})
    cuts = pd.DataFrame(cuts)
    print("\n=== Что это даёт бизнесу ===")
    print(cuts.assign(**{"дефолт среди одобренных": lambda d: (d["дефолт среди одобренных"] * 100).round(1),
                         "поймано дефолтов, %": lambda d: (d["поймано дефолтов, %"] * 100).round(1)}).to_string(index=False))

    # ---- децили по баллу ----
    df["дециль"] = pd.qcut(df["score"], 10, labels=False, duplicates="drop")
    dec = df.groupby("дециль").agg(заёмщиков=("y", "size"), дефолтов=("y", "sum"),
                                   доля_дефолтов=("y", "mean"), мин_балл=("score", "min")).reset_index()
    dec["лифт"] = dec["доля_дефолтов"] / yte.mean()
    print("\n=== Децили по скоринговому баллу (0 — худшие) ===")
    print(dec.round(3).to_string(index=False))

    np.save("outputs/preds.npy", np.vstack([preds[k] for k in preds]))
    json.dump({"models": list(preds), "y_test": yte.tolist(), "feats": feats,
               "factor": factor, "offset": offset}, open("outputs/preds_meta.json", "w"))
    res.to_csv("outputs/metrics.csv"); cuts.to_csv("outputs/cutoffs.csv", index=False)
    dec.to_csv("outputs/deciles.csv", index=False)

if __name__ == "__main__":
    main()
