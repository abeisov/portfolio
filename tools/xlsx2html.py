#!/usr/bin/env python3
"""
Делает из .xlsx простую HTML-страницу с таблицей, чтобы её можно было
посмотреть прямо на сайте (kind: "embed" / "report"), не скачивая файл.

    python3 tools/xlsx2html.py files/excel/model.xlsx "Название таблицы"

Рядом с исходником появится файл с тем же именем и расширением .html.
Формулы не считаются — берутся значения, сохранённые Excel при последнем
сохранении файла. Оформление (цвета, объединённые ячейки) не переносится.
"""
import sys, os, zipfile, html
import xml.etree.ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

def col_index(ref):
    letters = "".join(c for c in ref if c.isalpha())
    n = 0
    for c in letters:
        n = n * 26 + (ord(c) - 64)
    return n - 1

def read_sheet(path):
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall(NS + "si"):
                shared.append("".join(t.text or "" for t in si.iter(NS + "t")))
        names = [n for n in z.namelist() if n.startswith("xl/worksheets/sheet")]
        root = ET.fromstring(z.read(sorted(names)[0]))
        rows = []
        for row in root.iter(NS + "row"):
            cells = {}
            for c in row.findall(NS + "c"):
                t = c.get("t")
                if t == "inlineStr":
                    v = "".join(x.text or "" for x in c.iter(NS + "t"))
                else:
                    node = c.find(NS + "v")
                    v = node.text if node is not None else ""
                    if t == "s" and v not in (None, ""):
                        v = shared[int(v)]
                cells[col_index(c.get("r", "A1"))] = v or ""
            width = max(cells) + 1 if cells else 0
            rows.append([cells.get(i, "") for i in range(width)])
        return rows

def to_html(rows, title):
    width = max((len(r) for r in rows), default=0)
    body = []
    for i, r in enumerate(rows):
        r = r + [""] * (width - len(r))
        tag = "th" if i == 0 else "td"
        body.append("<tr>" + "".join(
            "<%s>%s</%s>" % (tag, html.escape(str(v)), tag) for v in r) + "</tr>")
    return """<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<style>
 body{font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
      margin:0;padding:24px;color:#191917;background:#fbfaf7}
 h1{font-size:18px;margin:0 0 16px;font-weight:600}
 .scroll{overflow-x:auto}
 table{border-collapse:collapse;min-width:100%%}
 th,td{border:1px solid #dedad1;padding:7px 12px;text-align:right;white-space:nowrap}
 th:first-child,td:first-child{text-align:left}
 th{background:#f0ede6;font-weight:600;font-size:13px;text-align:left}
 tr:nth-child(even) td{background:#f7f5f0}
</style></head><body>
<h1>%s</h1>
<div class="scroll"><table>%s</table></div>
</body></html>
""" % (html.escape(title), html.escape(title), "".join(body))

if __name__ == "__main__":
    src = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(src)
    out = os.path.splitext(src)[0] + ".html"
    open(out, "w", encoding="utf-8").write(to_html(read_sheet(src), title))
    print("готово:", out)
