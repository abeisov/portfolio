# Сборка панели признаков и целевой переменной.
# Цель: реализованная волатильность S&P 500 на горизонте 5 торговых дней ВПЕРЁД.
# Все признаки известны на момент t — заглядывания в будущее нет.

H <- 5          # горизонт прогноза, торговых дней
ANN <- 252      # дней в году для годового масштаба

read_fred <- function(id) {
  d <- read.csv(file.path("data", paste0(id, ".csv")), stringsAsFactors = FALSE)
  names(d) <- c("date", "value")
  d$date <- as.Date(d$date)
  d$value <- suppressWarnings(as.numeric(d$value))   # в FRED пропуски помечены точкой
  d[!is.na(d$value), ]
}

sp  <- read_fred("SP500");  names(sp)[2]  <- "px"
vix <- read_fred("VIXCLS"); names(vix)[2] <- "vix"
y10 <- read_fred("DGS10");  names(y10)[2] <- "y10"
y2  <- read_fred("DGS2");   names(y2)[2]  <- "y2"

d <- merge(sp, vix, by = "date", all.x = TRUE)
d <- merge(d, y10, by = "date", all.x = TRUE)
d <- merge(d, y2,  by = "date", all.x = TRUE)
d <- d[order(d$date), ]

# заполняем редкие пропуски ставок последним известным значением
carry <- function(x) { for (i in seq_along(x)) if (is.na(x[i]) && i > 1) x[i] <- x[i-1]; x }
d$vix <- carry(d$vix); d$y10 <- carry(d$y10); d$y2 <- carry(d$y2)

# дневные логарифмические доходности
d$r <- c(NA, diff(log(d$px)))

# реализованная волатильность за последние k дней, в годовом выражении
rv_back <- function(r, k) {
  n <- length(r); out <- rep(NA_real_, n)
  for (i in k:n) out[i] <- sqrt(ANN / k * sum(r[(i-k+1):i]^2))
  out
}
# реализованная волатильность за следующие H дней — это и есть цель
rv_fwd <- function(r, h) {
  n <- length(r); out <- rep(NA_real_, n)
  for (i in 1:(n-h)) out[i] <- sqrt(ANN / h * sum(r[(i+1):(i+h)]^2))
  out
}

d$rv1  <- sqrt(ANN) * abs(d$r)      # вчерашний модуль доходности
d$rv5  <- rv_back(d$r, 5)           # недельная
d$rv22 <- rv_back(d$r, 22)          # месячная
d$rv66 <- rv_back(d$r, 66)          # квартальная
d$y    <- rv_fwd(d$r, H)            # цель

d$term <- d$y10 - d$y2               # наклон кривой доходности
d$ret5 <- c(rep(NA, 5), sapply(6:nrow(d), function(i) sum(d$r[(i-4):i])))  # эффект рычага
d$ivol <- d$vix / 100                # VIX как готовый прогноз волатильности

keep <- c("date","y","rv1","rv5","rv22","rv66","ivol","term","ret5")
panel <- d[complete.cases(d[, keep]), keep]

# логарифмы: волатильность распределена логнормально, в логах регрессия ведёт себя лучше
for (v in c("y","rv1","rv5","rv22","rv66","ivol")) panel[[paste0("l_", v)]] <- log(pmax(panel[[v]], 1e-6))

saveRDS(panel, "data/panel.rds")
cat(sprintf("панель: %d наблюдений, %s — %s\n", nrow(panel), min(panel$date), max(panel$date)))
