# Обучение, честная валидация вперёд по времени и сравнение моделей.
panel <- readRDS("data/panel.rds")
H <- 5

# ---- модели: формулы в логарифмах волатильности ----
specs <- list(
  "HAR"                  = l_y ~ l_rv1 + l_rv5 + l_rv22,
  "HAR + квартал"        = l_y ~ l_rv1 + l_rv5 + l_rv22 + l_rv66,
  "HAR + VIX"            = l_y ~ l_rv1 + l_rv5 + l_rv22 + l_ivol,
  "HAR + VIX + рынок"    = l_y ~ l_rv1 + l_rv5 + l_rv22 + l_ivol + term + ret5
)

# ---- гребневая регрессия на тех же признаках ----
ridge_fit <- function(X, y, lambda) {
  Xs <- scale(X); mu <- attr(Xs,"scaled:center"); sg <- attr(Xs,"scaled:scale")
  p <- ncol(Xs)
  b <- solve(t(Xs) %*% Xs + lambda * diag(p), t(Xs) %*% (y - mean(y)))
  list(b = b, mu = mu, sg = sg, int = mean(y))
}
ridge_pred <- function(m, X) as.numeric(scale(X, center = m$mu, scale = m$sg) %*% m$b + m$int)
ridge_vars <- c("l_rv1","l_rv5","l_rv22","l_rv66","l_ivol","term","ret5")

# ---- валидация: расширяющееся окно, переобучение раз в 21 день ----
n <- nrow(panel)
start <- floor(n * 0.6)                 # первые 60% — только обучение
idx <- seq(start + 1, n)
refit_every <- 21

preds <- data.frame(date = panel$date[idx], actual = panel$y[idx])
for (nm in names(specs)) preds[[nm]] <- NA_real_
preds[["Гребневая"]] <- NA_real_
preds[["Наивный (RW)"]] <- panel$rv5[idx]        # «завтра как вчера»
preds[["VIX как прогноз"]] <- panel$ivol[idx]    # рынок уже всё сказал

fits_last <- list()
for (k in seq_along(idx)) {
  i <- idx[k]
  if ((k - 1) %% refit_every == 0) {
    tr <- panel[1:(i - H - 1), ]                 # отступ H дней: цель на i-H ещё не наблюдалась
    fits_last <- lapply(specs, function(f) lm(f, data = tr))
    Xtr <- as.matrix(tr[, ridge_vars]); ytr <- tr$l_y
    ridge_last <- ridge_fit(Xtr, ytr, lambda = 10)
  }
  newd <- panel[i, , drop = FALSE]
  for (nm in names(specs)) preds[k, nm] <- exp(predict(fits_last[[nm]], newd))
  preds[k, "Гребневая"] <- exp(ridge_pred(ridge_last, as.matrix(newd[, ridge_vars])))
}

# ---- метрики ----
qlike <- function(a, f) mean(a^2 / f^2 - log(a^2 / f^2) - 1)
metrics <- function(a, f) c(
  RMSE = sqrt(mean((a - f)^2)),
  MAE  = mean(abs(a - f)),
  R2   = 1 - sum((a - f)^2) / sum((a - mean(a))^2),
  QLIKE = qlike(a, f),
  Bias = mean(f - a)
)
model_names <- c("Наивный (RW)", "VIX как прогноз", names(specs), "Гребневая")
M <- t(sapply(model_names, function(nm) metrics(preds$actual, preds[[nm]])))
M <- as.data.frame(M); M$model <- rownames(M)
M <- M[order(M$RMSE), ]
cat("\n=== OUT-OF-SAMPLE (", nrow(preds), " дней, ", format(min(preds$date)), " — ", format(max(preds$date)), ") ===\n", sep="")
print(round(M[, c("RMSE","MAE","R2","QLIKE","Bias")], 4))

# ---- тест Диболда–Мариано против наивного прогноза (с поправкой Ньюи–Уэста) ----
dm_test <- function(a, f1, f2, h = H) {
  d <- (a - f1)^2 - (a - f2)^2
  T <- length(d); dbar <- mean(d); L <- h - 1
  g <- function(k) sum((d[(k+1):T] - dbar) * (d[1:(T-k)] - dbar)) / T
  v <- g(0); if (L > 0) for (k in 1:L) v <- v + 2 * (1 - k/(L+1)) * g(k)
  stat <- dbar / sqrt(v / T)
  c(stat = stat, p = 2 * (1 - pnorm(abs(stat))))
}
cat("\n=== Диболд–Мариано против наивного прогноза ===\n")
for (nm in c("VIX как прогноз", names(specs), "Гребневая")) {
  t <- dm_test(preds$actual, preds[["Наивный (RW)"]], preds[[nm]])
  cat(sprintf("%-20s стат %6.2f  p = %s\n", nm, t[1], format.pval(t[2], digits = 3)))
}

# ---- финальная модель на всей выборке: коэффициенты ----
best <- "HAR + VIX + рынок"
fit <- lm(specs[[best]], data = panel[1:(n - H), ])
cat("\n=== Коэффициенты финальной модели (", best, ") ===\n", sep="")
print(round(summary(fit)$coefficients, 4))
cat("R2 внутри выборки:", round(summary(fit)$r.squared, 4), "\n")

saveRDS(list(preds = preds, M = M, fit = fit, panel = panel, specs = specs), "outputs/results.rds")
write.csv(preds, "outputs/predictions.csv", row.names = FALSE)
write.csv(M, "outputs/metrics.csv", row.names = FALSE)
