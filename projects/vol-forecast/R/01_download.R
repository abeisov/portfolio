# Загрузка исходных рядов с FRED. Ключи и регистрация не нужны.
# Запуск: Rscript R/01_download.R
dir.create("data", showWarnings = FALSE)

series <- c(
  SP500  = "SP500",    # индекс S&P 500, дневные значения
  VIXCLS = "VIXCLS",   # индекс подразумеваемой волатильности VIX
  DGS10  = "DGS10",    # доходность 10-летних казначейских облигаций
  DGS2   = "DGS2"      # доходность 2-летних казначейских облигаций
)

for (id in series) {
  url <- sprintf("https://fred.stlouisfed.org/graph/fredgraph.csv?id=%s&cosd=2016-09-01", id)
  dest <- file.path("data", paste0(id, ".csv"))
  download.file(url, dest, quiet = TRUE)
  cat(sprintf("%-14s %6d строк -> %s\n", id, nrow(read.csv(dest)), dest))
}
