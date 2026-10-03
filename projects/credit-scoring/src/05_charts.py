"""Графики: качество, калибровка, бизнес-срез, вклад признаков."""
import json, pathlib
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, precision_recall_curve
from sklearn.calibration import calibration_curve

ACC, WARN, GREY, PANEL = "#2e5266", "#b4472e", "#85837a", "#fbfaf7"
plt.rcParams.update({"figure.facecolor": PANEL, "axes.facecolor": PANEL, "savefig.facecolor": PANEL,
                     "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 10, "axes.grid": True, "grid.color": "#e8e4db"})
OUT = pathlib.Path("outputs")
meta = json.load(open(OUT / "preds_meta.json"))
P = np.load(OUT / "preds.npy"); y = np.array(meta["y_test"]); names = meta["models"]
cols = [ACC, GREY, WARN]

# 1. ROC
fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
for p, n, c in zip(P, names, cols):
    fpr, tpr, _ = roc_curve(y, p)
    ax[0].plot(fpr, tpr, color=c, lw=1.6, label=f"{n} (AUC {np.trapezoid(tpr, fpr):.3f})")
ax[0].plot([0, 1], [0, 1], ls="--", color="#c9c4b8", lw=1)
ax[0].set(xlabel="доля ложных срабатываний", ylabel="доля пойманных дефолтов", title="ROC-кривая")
ax[0].legend(fontsize=7, frameon=False)
for p, n, c in zip(P, names, cols):
    pr, rc, _ = precision_recall_curve(y, p)
    ax[1].plot(rc, pr, color=c, lw=1.6, label=n)
ax[1].axhline(y.mean(), ls="--", color="#c9c4b8", lw=1)
ax[1].set(xlabel="полнота", ylabel="точность", title="Precision–Recall (базовый уровень 22,1 %)")
ax[1].legend(fontsize=7, frameon=False)
plt.tight_layout(); plt.savefig(OUT / "01-roc-pr.png", dpi=140); plt.close()

# 2. KS
fig, ax = plt.subplots(figsize=(6, 3.4))
p = P[0]
fpr, tpr, thr = roc_curve(y, p)
k = np.argmax(tpr - fpr)
ax.plot(thr[1:], tpr[1:], color=ACC, lw=1.6, label="пойманные дефолты")
ax.plot(thr[1:], fpr[1:], color=GREY, lw=1.6, label="ложные срабатывания")
ax.vlines(thr[k], fpr[k], tpr[k], color=WARN, lw=2)
ax.annotate(f"KS = {tpr[k]-fpr[k]:.3f}", (thr[k], (tpr[k]+fpr[k])/2), xytext=(8, 0),
            textcoords="offset points", color=WARN, fontsize=9)
ax.set(xlabel="порог вероятности дефолта", ylabel="доля", title="Статистика Колмогорова–Смирнова, скоркарта")
ax.invert_xaxis(); ax.legend(fontsize=8, frameon=False)
plt.tight_layout(); plt.savefig(OUT / "02-ks.png", dpi=140); plt.close()

# 3. калибровка
fig, ax = plt.subplots(figsize=(5.4, 3.8))
for p, n, c in zip(P, names, cols):
    x, yy = calibration_curve(y, p, n_bins=10, strategy="quantile")
    ax.plot(yy, x, "o-", color=c, lw=1.4, ms=4, label=n)
ax.plot([0, 1], [0, 1], ls="--", color="#c9c4b8", lw=1)
ax.set(xlabel="предсказанная вероятность", ylabel="фактическая доля дефолтов", title="Калибровка")
ax.legend(fontsize=7, frameon=False)
plt.tight_layout(); plt.savefig(OUT / "03-calibration.png", dpi=140); plt.close()

# 4. бизнес-срез
cuts = pd.read_csv(OUT / "cutoffs.csv"); dec = pd.read_csv(OUT / "deciles.csv")
fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
ax[0].plot(cuts["одобрение"] * 100, cuts["дефолт среди одобренных"] * 100, "o-", color=ACC, lw=1.8)
ax[0].axhline(22.1, ls="--", color=WARN, lw=1.2)
ax[0].annotate("без скоринга: 22,1 %", (52, 22.8), color=WARN, fontsize=8)
ax[0].set(xlabel="доля одобренных заявок, %", ylabel="дефолт среди одобренных, %",
          title="Чем строже отбор, тем чище портфель")
ax[1].bar(dec["дециль"], dec["лифт"], color=ACC, width=.75)
ax[1].axhline(1, color=WARN, lw=1.2, ls="--")
ax[1].set(xlabel="дециль по баллу (0 — худшие заёмщики)", ylabel="лифт", title="Концентрация риска по децилям")
plt.tight_layout(); plt.savefig(OUT / "04-business.png", dpi=140); plt.close()

# 5. Information Value
iv = pd.Series(json.load(open(OUT / "binning.json"))["iv"]).sort_values()
fig, ax = plt.subplots(figsize=(6.2, 4.4))
ax.barh(iv.index, iv.values, color=[ACC if v >= 0.02 else GREY for v in iv.values])
for t, lab in [(0.02, "порог отбора"), (0.3, "сильный")]:
    ax.axvline(t, ls="--", color=WARN, lw=1)
    ax.annotate(lab, (t, 0.2), rotation=90, fontsize=7, color=WARN, xytext=(3, 0), textcoords="offset points")
ax.set(xlabel="Information Value", title="Предсказательная сила признаков")
plt.tight_layout(); plt.savefig(OUT / "05-iv.png", dpi=140); plt.close()

# 6. пример строк скоркарты
card = pd.read_csv(OUT / "scorecard.csv")
card.columns = ["feature", "bin", "good", "bad", "n", "bad_rate", "woe", "iv", "points"]
show = card[card["feature"].isin(["delay_last", "pay_ratio_mean", "limit"])]
fig, axes = plt.subplots(1, 3, figsize=(9.5, 3.2))
for a, (f, g) in zip(axes, show.groupby("feature")):
    a.bar(g["bin"].astype(str), g["points"], color=ACC, width=.7)
    a2 = a.twinx(); a2.plot(g["bin"].astype(str), g["bad_rate"] * 100, "o-", color=WARN, lw=1.4, ms=4)
    a2.set_ylabel("дефолт, %", color=WARN, fontsize=8); a2.grid(False)
    a.set_title(f, fontsize=9); a.set_xlabel("бин"); a.set_ylabel("баллы")
plt.tight_layout(); plt.savefig(OUT / "06-scorecard.png", dpi=140); plt.close()
print("графики готовы:", len(list(OUT.glob('*.png'))))
