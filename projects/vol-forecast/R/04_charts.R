Sys.setlocale("LC_ALL", "ru_RU.UTF-8")
res <- readRDS("outputs/results.rds")
preds <- res$preds; M <- res$M; fit <- res$fit; panel <- res$panel
ink <- "#191917"; acc <- "#2e5266"; warn <- "#b4472e"; grey <- "#85837a"
png_ <- function(f, w = 1200, h = 560) png(file.path("outputs", f), width = w, height = h, res = 140)

# 1. контекст: реализованная и подразумеваемая волатильность
png_("01-context.png")
par(mar = c(3.5, 4, 2.5, 1))
plot(panel$date, panel$y * 100, type = "l", col = grey, lwd = 1,
     xlab = "", ylab = "волатильность, % годовых",
     main = "Реализованная волатильность S&P 500 и VIX")
lines(panel$date, panel$ivol * 100, col = acc, lwd = 1)
legend("topright", c("реализованная (5 дней вперёд)", "VIX"), col = c(grey, acc), lwd = 2, bty = "n", cex = .85)
dev.off()

# 2. факт против прогноза во времени
png_("02-oos.png")
par(mar = c(3.5, 4, 2.5, 1))
plot(preds$date, preds$actual * 100, type = "l", col = grey, lwd = 1,
     xlab = "", ylab = "волатильность, % годовых",
     main = "Вне обучающей выборки: факт и прогноз")
lines(preds$date, preds[["HAR + VIX + рынок"]] * 100, col = warn, lwd = 1.4)
legend("topright", c("факт", "прогноз HAR + VIX + рынок"), col = c(grey, warn), lwd = 2, bty = "n", cex = .85)
dev.off()

# 3. прогноз против факта
png_("03-scatter.png", 900, 620)
par(mar = c(4, 4, 2.5, 1))
plot(preds[["HAR + VIX + рынок"]] * 100, preds$actual * 100, pch = 16, col = adjustcolor(acc, .35),
     xlab = "прогноз, %", ylab = "факт, %", main = "Прогноз против факта (OOS)")
abline(0, 1, col = warn, lwd = 2, lty = 2)
legend("topleft", "идеальное совпадение", col = warn, lwd = 2, lty = 2, bty = "n", cex = .85)
dev.off()

# 4. сравнение моделей
png_("04-models.png", 1100, 520)
par(mfrow = c(1, 2), mar = c(8, 4, 2.5, 1))
b <- barplot(M$RMSE * 100, names.arg = M$model, las = 2, col = acc, border = NA,
             ylab = "RMSE, п.п.", main = "Ошибка прогноза", cex.names = .75)
b <- barplot(M$R2, names.arg = M$model, las = 2, col = ifelse(M$R2 > 0, acc, warn), border = NA,
             ylab = "R2 вне выборки", main = "Объяснённая дисперсия", cex.names = .75)
abline(h = 0, col = ink)
dev.off()

# 5. коэффициенты финальной модели
png_("05-coefs.png", 900, 520)
s <- summary(fit)$coefficients
s <- s[rownames(s) != "(Intercept)", ]
sdx <- sapply(rownames(s), function(v) sd(fit$model[[v]]))
std <- s[, 1] * sdx / sd(fit$model$l_y)      # стандартизованные коэффициенты
par(mar = c(4, 7, 2.5, 1))
barplot(rev(std), horiz = TRUE, las = 1, border = NA,
        col = ifelse(rev(std) > 0, acc, warn),
        xlab = "вклад в стандартных отклонениях", main = "Что реально двигает прогноз")
abline(v = 0, col = ink)
dev.off()

# 6. диагностика остатков
png_("06-residuals.png", 1100, 460)
par(mfrow = c(1, 2), mar = c(4, 4, 2.5, 1))
e <- residuals(fit)
hist(e, breaks = 50, col = "#dfe4e8", border = "#b9c3ca", freq = FALSE,
     main = "Остатки: распределение", xlab = "остаток, лог-волатильность")
curve(dnorm(x, mean(e), sd(e)), add = TRUE, col = warn, lwd = 2)
acf(e, main = "Остатки: автокорреляция", lag.max = 30)
dev.off()

cat("графики готовы\n")
writeLines(capture.output(print(round(M[, c("RMSE","MAE","R2","QLIKE","Bias")], 4))), "outputs/metrics.txt")
