"""Очистка данных и построение признаков под кредитный скоринг.

Логика признаков повторяет то, на что смотрит кредитный аналитик:
глубина просрочки, использование лимита, дисциплина погашения и их динамика.
"""
import pathlib
import numpy as np
import pandas as pd

RAW = pathlib.Path("data/credit.csv")
OUT = pathlib.Path("data/features.csv")
PAY = [f"PAY_{i}" for i in [0, 2, 3, 4, 5, 6]]      # статус платежа за 6 месяцев
BILL = [f"BILL_AMT{i}" for i in range(1, 7)]        # выставленный счёт
AMT = [f"PAY_AMT{i}" for i in range(1, 7)]          # фактический платёж

def build(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    # --- чистка справочников: в данных есть незадокументированные коды ---
    d["EDUCATION"] = d["EDUCATION"].replace({0: 4, 5: 4, 6: 4})   # 4 = прочее
    d["MARRIAGE"] = d["MARRIAGE"].replace({0: 3})                 # 3 = прочее
    # отрицательные значения PAY_* означают «оплачено вовремя или досрочно»
    delay = d[PAY].clip(lower=0)

    f = pd.DataFrame(index=d.index)
    f["limit"] = d["LIMIT_BAL"]
    f["age"] = d["AGE"]
    f["sex"] = d["SEX"]
    f["education"] = d["EDUCATION"]
    f["marriage"] = d["MARRIAGE"]

    # --- просрочки ---
    f["delay_max"] = delay.max(axis=1)                      # худшая просрочка за полгода
    f["delay_last"] = delay["PAY_0"]                        # просрочка в последнем месяце
    f["delay_months"] = (delay > 0).sum(axis=1)             # сколько месяцев с просрочкой
    f["delay_mean"] = delay.mean(axis=1)
    f["delay_trend"] = delay["PAY_0"] - delay["PAY_6"]      # ухудшается или выправляется

    # --- использование лимита ---
    bill = d[BILL].clip(lower=0)
    f["util_last"] = bill["BILL_AMT1"] / d["LIMIT_BAL"]
    f["util_mean"] = bill.mean(axis=1) / d["LIMIT_BAL"]
    f["util_max"] = bill.max(axis=1) / d["LIMIT_BAL"]
    f["util_trend"] = (bill["BILL_AMT1"] - bill["BILL_AMT6"]) / d["LIMIT_BAL"]

    # --- дисциплина погашения: какую долю счёта клиент реально гасит ---
    pay_ratio = []
    for i in range(1, 6):
        b = bill[f"BILL_AMT{i+1}"].replace(0, np.nan)
        pay_ratio.append((d[f"PAY_AMT{i}"] / b).clip(0, 2))
    pr = pd.concat(pay_ratio, axis=1)
    f["pay_ratio_mean"] = pr.mean(axis=1).fillna(0)
    f["pay_ratio_last"] = pr.iloc[:, 0].fillna(0)
    f["zero_pay_months"] = (d[AMT] == 0).sum(axis=1)        # месяцы без единого платежа
    f["pay_total"] = d[AMT].sum(axis=1) / d["LIMIT_BAL"]

    f["target"] = d["default"]
    return f.replace([np.inf, -np.inf], np.nan).fillna(0)

def main() -> None:
    df = pd.read_csv(RAW)
    f = build(df)
    f.to_csv(OUT, index=False)
    print(f"признаков: {f.shape[1]-1}, наблюдений: {len(f)}")
    print(f"доля дефолтов: {f['target'].mean():.1%}")
    print("\nсредние значения по группам (дефолт / без дефолта):")
    g = f.groupby("target").mean().T
    g.columns = ["без дефолта", "дефолт"]
    g["разница, %"] = (g["дефолт"] / g["без дефолта"].replace(0, np.nan) - 1) * 100
    print(g.round(2).to_string())

if __name__ == "__main__":
    main()
