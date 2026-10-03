"""Графики проекта."""
import sys, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, "src"); from ratios import RATIOS
from sklearn.metrics import precision_recall_curve, roc_curve
from sklearn.calibration import calibration_curve

ACC, WARN, GREY, PANEL = "#2e5266", "#b4472e", "#85837a", "#fbfaf7"
plt.rcParams.update({"figure.facecolor": PANEL, "axes.facecolor": PANEL, "savefig.facecolor": PANEL,
                     "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 10, "axes.grid": True, "grid.color": "#e8e4db"})
meta = json.load(open("outputs/preds_meta.json")); P = np.load("outputs/preds.npy")
y = np.array(meta["y_test"]); names = meta["models"]
cols = [GREY, "#9a8f7a", "#5d7f8c", ACC]

# 1. PR и ROC
fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
for p, n, c in zip(P, names, cols):
    pr, rc, _ = precision_recall_curve(y, p); ax[0].plot(rc, pr, color=c, lw=1.6, label=n)
ax[0].axhline(y.mean(), ls="--", color=WARN, lw=1.2)
ax[0].annotate(f"случайная модель: {y.mean():.1%}", (0.35, y.mean()+0.03), color=WARN, fontsize=7.5)
ax[0].set(xlabel="полнота: доля пойманных банкротств", ylabel="точность сигнала", title="Precision–Recall")
ax[0].legend(fontsize=7, frameon=False)
for p, n, c in zip(P, names, cols):
    fpr, tpr, _ = roc_curve(y, p); ax[1].plot(fpr, tpr, color=c, lw=1.6, label=n)
ax[1].plot([0,1],[0,1], ls="--", color="#c9c4b8", lw=1)
ax[1].set(xlabel="ложные тревоги", ylabel="пойманные банкротства", title="ROC-кривая")
ax[1].legend(fontsize=7, frameon=False)
plt.tight_layout(); plt.savefig("outputs/01-pr-roc.png", dpi=140); plt.close()

# 2. горизонты
m = pd.read_csv("outputs/metrics.csv")
fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
for mod, c in zip(["Градиентный бустинг","Случайный лес","Логистическая регрессия","Дерево решений (глубина 3)"],
                  [ACC, "#5d7f8c", GREY, "#c0a080"]):
    s = m[m["модель"] == mod].sort_values("горизонт")
    ax[0].plot(s["горизонт"], s["PR-AUC"], "o-", color=c, lw=1.6, ms=4, label=mod)
    ax[1].plot(s["горизонт"], s["ROC-AUC"], "o-", color=c, lw=1.6, ms=4)
base = m[m["модель"]=="Градиентный бустинг"].sort_values("горизонт")
ax[0].plot(base["горизонт"], base["база PR"], "--", color=WARN, lw=1.2, label="случайная модель")
ax[0].set(xlabel="горизонт прогноза, лет", ylabel="PR-AUC", title="Качество по горизонтам: монотонного спада нет")
ax[0].legend(fontsize=6.5, frameon=False); ax[0].set_xticks([1,2,3,4,5])
ax[1].set(xlabel="горизонт прогноза, лет", ylabel="ROC-AUC", title="ROC-AUC по горизонтам"); ax[1].set_xticks([1,2,3,4,5])
plt.tight_layout(); plt.savefig("outputs/02-horizons.png", dpi=140); plt.close()

# 3. важность
imp = pd.read_csv("outputs/importance.csv").head(12).iloc[::-1]
lbl = [f"{r['признак']}: {str(r['смысл'])[:46]}" for _, r in imp.iterrows()]
fig, ax = plt.subplots(figsize=(7.6, 4.4))
ax.barh(lbl, imp["важность"], xerr=imp["sd"], color=ACC, error_kw={"ecolor": "#b9b2a4", "lw": 1})
ax.set(xlabel="падение PR-AUC при перемешивании признака", title="Что держит прогноз")
plt.tight_layout(); plt.savefig("outputs/03-importance.png", dpi=140); plt.close()

# 4. бизнес-срез
cut = pd.read_csv("outputs/cutoffs.csv")
fig, ax = plt.subplots(figsize=(6.4, 3.6))
x = cut["доля компаний на проверке"]*100
ax.plot(x, cut["поймано банкротств"]*100, "o-", color=ACC, lw=1.8, label="поймано банкротств")
ax.plot(x, cut["точность сигнала"]*100, "o-", color=WARN, lw=1.8, label="точность сигнала")
ax.axhline(y.mean()*100, ls="--", color=GREY, lw=1.2)
ax.annotate("случайная проверка", (22, y.mean()*100+2), color=GREY, fontsize=7.5)
ax.set(xlabel="какую долю портфеля отправляем на проверку, %", ylabel="%",
       title="Сколько проверять и что получим")
ax.legend(fontsize=8, frameon=False)
plt.tight_layout(); plt.savefig("outputs/04-business.png", dpi=140); plt.close()

# 5. калибровка
fig, ax = plt.subplots(figsize=(5.2, 3.8))
for p, n, c in zip(P, names, cols):
    a, b = calibration_curve(y, p, n_bins=8, strategy="quantile")
    ax.plot(b, a, "o-", color=c, lw=1.4, ms=4, label=n)
ax.plot([0,1],[0,1], ls="--", color="#c9c4b8", lw=1)
ax.set(xlabel="предсказанная вероятность", ylabel="фактическая доля банкротств", title="Калибровка")
ax.legend(fontsize=6.5, frameon=False)
plt.tight_layout(); plt.savefig("outputs/05-calibration.png", dpi=140); plt.close()

# 6. пропуски
miss = pd.read_csv("outputs/missing.csv", index_col=0).head(14).iloc[::-1]
fig, ax = plt.subplots(figsize=(7.2, 3.8))
lbl = [f"{i}: {str(RATIOS.get(i,''))[:40]}" for i in miss.index]
ax.barh(lbl, miss.iloc[:,0]*100, color=[WARN if v > 0.2 else ACC for v in miss.iloc[:,0]])
ax.set(xlabel="доля пропусков, %", title="Пропуски в отчётности")
plt.tight_layout(); plt.savefig("outputs/06-missing.png", dpi=140); plt.close()
print("графиков:", len(list(__import__('pathlib').Path('outputs').glob('*.png'))))
