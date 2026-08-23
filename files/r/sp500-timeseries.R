# путь относительный: держите sp500.csv рядом со скриптом
SP <- read.csv("sp500.csv", header = TRUE)
class(SP)     
dim(SP)       
head(SP)      
tail(SP)      
summary(SP)   

SP$Date <- as.Date(SP$Date)
SP <- SP[order(SP$Date), ]


Close.ts <- ts(SP$Close,    start = c(2020, 1), frequency = 252)
Adj.ts   <- ts(SP$Adjusted, start = c(2020, 1), frequency = 252)
Vol.ts   <- ts(SP$Volume,   start = c(2020, 1), frequency = 252)
Ret.ts   <- ts(SP$Returns[-1], start = c(2020, 1), frequency = 252)
LR <- diff(log(SP$Close))
LogRet.ts <- ts(LR, start = c(2020, 1), frequency = 252)


# Графики — все ценовые ряды по отдельности
Open.ts <- ts(SP$Open, start = c(2020, 1), frequency = 252)
High.ts <- ts(SP$High, start = c(2020, 1), frequency = 252)
Low.ts  <- ts(SP$Low,  start = c(2020, 1), frequency = 252)

par(mfrow = c(2, 2))
plot(Open.ts,  ylab = "Open price",  main = "(a) S&P500 Open price")
plot(High.ts,  ylab = "High price",  main = "(b) S&P500 High price")
plot(Low.ts,   ylab = "Low price",   main = "(c) S&P500 Low price")
plot(Close.ts, ylab = "Close price", main = "(d) S&P500 Close price")
par(mfrow = c(1, 1))

par(mfrow = c(2, 2))
plot(Close.ts,       ylab = "Close price",   main = "(a) S&P500 Close price")
plot(LogRet.ts,      ylab = "Log-returns",   main = "(b) Daily log-returns")
plot(Vol.ts,         ylab = "Volume",        main = "(c) Trading volume")
plot(abs(LogRet.ts), ylab = "|Log-returns|", main = "(d) Absolute log-returns")
par(mfrow = c(1, 1))


#Статистика
mean(Close.ts); var(Close.ts); sd(Close.ts)
mean(LogRet.ts); var(LogRet.ts); sd(LogRet.ts)
sd(LogRet.ts) * sqrt(252)
summary(LogRet.ts)
library(moments)
skewness(LogRet.ts)
kurtosis(LogRet.ts)
hist(LogRet.ts, breaks = 50, freq = FALSE,
     main = "Distribution of log-returns",
     xlab = "Log-returns", col = "lightgray")
curve(dnorm(x, mean = mean(LogRet.ts), sd = sd(LogRet.ts)),
      add = TRUE, col = "red", lwd = 2)


#Декомпозиция
LogClose.ts <- ts(log(SP$Close), start = c(2020, 1), frequency = 252)
dec.mul <- decompose(Close.ts, type = "multiplicative")
plot(dec.mul)
dec.add <- decompose(LogClose.ts, type = "additive")
plot(dec.add)
stl.fit <- stl(LogClose.ts, s.window = "periodic")
plot(stl.fit, main = "STL decomposition of log(Close)")


#Коррелограммы и тесты стационарности
par(mfrow = c(2, 2))
acf(Close.ts,   main = "ACF of Close price")
pacf(Close.ts,  main = "PACF of Close price")
acf(LogRet.ts,  main = "ACF of log-returns")
pacf(LogRet.ts, main = "PACF of log-returns")
par(mfrow = c(1, 1))
acf((LogRet.ts - mean(LogRet.ts))^2, main = "ACF of squared log-returns")
library(tseries)
adf.test(Close.ts)
adf.test(LogRet.ts)
kpss.test(Close.ts)
kpss.test(LogRet.ts)


#AR/ARMA
fit.ar <- ar(LogRet.ts)
fit.ar$order
fit.ar$ar
fit.ar$aic
acf(na.omit(fit.ar$res), main = "ACF of AR(9) residuals")

# Пробуем 20 разных моделей
fit.arima1  <- arima(LogRet.ts, order = c(1,0,0))   # AR(1)
fit.arima2  <- arima(LogRet.ts, order = c(2,0,0))   # AR(2)
fit.arima3  <- arima(LogRet.ts, order = c(3,0,0))   # AR(3)
fit.arima4  <- arima(LogRet.ts, order = c(4,0,0))   # AR(4)
fit.arima5  <- arima(LogRet.ts, order = c(5,0,0))   # AR(5)
fit.arima6  <- arima(LogRet.ts, order = c(9,0,0))   # AR(9)
fit.arima7  <- arima(LogRet.ts, order = c(0,0,1))   # MA(1)
fit.arima8  <- arima(LogRet.ts, order = c(0,0,2))   # MA(2)
fit.arima9  <- arima(LogRet.ts, order = c(0,0,3))   # MA(3)
fit.arima10 <- arima(LogRet.ts, order = c(1,0,1))   # ARMA(1,1)
fit.arima11 <- arima(LogRet.ts, order = c(1,0,2))   # ARMA(1,2)
fit.arima12 <- arima(LogRet.ts, order = c(2,0,1))   # ARMA(2,1)
fit.arima13 <- arima(LogRet.ts, order = c(2,0,2))   # ARMA(2,2)
fit.arima14 <- arima(LogRet.ts, order = c(3,0,1))   # ARMA(3,1)
fit.arima15 <- arima(LogRet.ts, order = c(3,0,3))   # ARMA(3,3)
fit.arima16 <- arima(LogRet.ts, order = c(4,0,4))   # ARMA(4,4)
fit.arima17 <- arima(LogRet.ts, order = c(5,0,5))   # ARMA(5,5)
fit.arima18 <- arima(LogRet.ts, order = c(9,0,1))   # ARMA(9,1)
fit.arima19 <- arima(LogRet.ts, order = c(2,0,3))   # ARMA(2,3)
fit.arima20 <- arima(LogRet.ts, order = c(3,0,2))   # ARMA(3,2)

# Сравниваем все 20 по AIC
AIC(fit.arima1,  fit.arima2,  fit.arima3,  fit.arima4,  fit.arima5,
    fit.arima6,  fit.arima7,  fit.arima8,  fit.arima9,  fit.arima10,
    fit.arima11, fit.arima12, fit.arima13, fit.arima14, fit.arima15,
    fit.arima16, fit.arima17, fit.arima18, fit.arima19, fit.arima20)

# Лучшая модель AR(9) = fit.arima6, смотрим её параметры с 95% ДИ
lower <- fit.arima6$coef - 2 * sqrt(diag(fit.arima6$var.coef))
upper <- fit.arima6$coef + 2 * sqrt(diag(fit.arima6$var.coef))
cbind(lower, fit.arima6$coef, upper)
acf(na.omit(fit.arima6$residuals), main = "ACF of AR(9) residuals")


#SARIMA (сезонная модель)
library(forecast)
LogRet.s <- ts(LR, frequency = 5)
fit.sarima <- arima(LogRet.s,
                    order = c(1,0,0),
                    seasonal = list(order = c(1,0,0), period = 5))
summary(fit.sarima)
AIC(fit.sarima)
acf(na.omit(fit.sarima$residuals), main = "ACF of SARIMA residuals")


#GARCH
library(tseries)
sp.garch <- garch(LogRet.ts, trace = FALSE)
summary(sp.garch)
sp.res <- sp.garch$res[-1]
acf(sp.res,   main = "ACF of GARCH residuals")
acf(sp.res^2, main = "ACF of squared GARCH residuals")


#Прогнозы (AR(9) = fit.arima6)
forecast10 <- predict(fit.arima6, n.ahead = 10)
forecast20 <- predict(fit.arima6, n.ahead = 20)
forecast30 <- predict(fit.arima6, n.ahead = 30)

# График 1: прогноз на 10 дней
plot(window(LogRet.ts, start = c(2025, 1)),
     main = "AR(9) forecast — 10 days",
     ylab = "Log-returns", xlab = "Time",
     xlim = c(2025, 2025.25), ylim = c(-0.03, 0.03))
lines(forecast10$pred, col = "red")
lines(forecast10$pred + 1.96*forecast10$se, col = "red", lty = 2)
lines(forecast10$pred - 1.96*forecast10$se, col = "red", lty = 2)
legend("topleft", legend = c("Observed", "Forecast", "95% CI"),
       col = c("black", "red", "red"), lty = c(1, 1, 2))

# График 2: прогноз на 20 дней
plot(window(LogRet.ts, start = c(2025, 1)),
     main = "AR(9) forecast — 20 days",
     ylab = "Log-returns", xlab = "Time",
     xlim = c(2025, 2025.3), ylim = c(-0.03, 0.03))
lines(forecast20$pred, col = "red")
lines(forecast20$pred + 1.96*forecast20$se, col = "red", lty = 2)
lines(forecast20$pred - 1.96*forecast20$se, col = "red", lty = 2)
legend("topleft", legend = c("Observed", "Forecast", "95% CI"),
       col = c("black", "red", "red"), lty = c(1, 1, 2))

# График 3: прогноз на 30 дней
plot(window(LogRet.ts, start = c(2025, 1)),
     main = "AR(9) forecast — 30 days",
     ylab = "Log-returns", xlab = "Time",
     xlim = c(2025, 2025.4), ylim = c(-0.03, 0.03))
lines(forecast30$pred, col = "red")
lines(forecast30$pred + 1.96*forecast30$se, col = "red", lty = 2)
lines(forecast30$pred - 1.96*forecast30$se, col = "red", lty = 2)
legend("topleft", legend = c("Observed", "Forecast", "95% CI"),
       col = c("black", "red", "red"), lty = c(1, 1, 2))

# Числовые значения прогноза на 30 дней
cbind(
  lower = round(forecast30$pred - 1.96*forecast30$se, 5),
  pred  = round(forecast30$pred, 5),
  upper = round(forecast30$pred + 1.96*forecast30$se, 5)
)
