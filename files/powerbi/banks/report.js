(function(){
  "use strict";
  var records = (window.BANK_DATA && window.BANK_DATA.rows) || [];
  var months = Array.from(new Set(records.map(function(r){ return r.month; }))).sort();
  var banks = Array.from(new Set(records.map(function(r){ return r.bank; }))).sort(function(a,b){ return a.localeCompare(b,"ru"); });
  var monthSelect = document.getElementById("month");
  var bankSelect = document.getElementById("bank");
  var charts = {};
  var colors = ["#2e5266","#557d8f","#b68a4b","#89a7a0","#a1604d","#8e9b6f","#72849b"];
  var trn = 1000000000;
  var bn = 1000000;
  var number = new Intl.NumberFormat("ru-RU",{maximumFractionDigits:2,minimumFractionDigits:2});
  var percent = new Intl.NumberFormat("ru-RU",{maximumFractionDigits:1,minimumFractionDigits:1});
  var monthNames = ["янв","фев","мар","апр","май","июн","июл","авг","сен","окт","ноя","дек"];

  function monthLabel(m){ var p=m.split("-"); return monthNames[Number(p[1])-1]+" "+p[0]; }
  function esc(s){ return String(s).replace(/[&<>"']/g,function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]; }); }
  function sum(rows,key){ return rows.reduce(function(total,r){ return total+(typeof r[key]==="number" ? r[key] : 0); },0); }
  function fmtTrn(raw){ return number.format(raw/trn); }
  function fmtBn(raw){ return number.format(raw/bn); }
  function fmtPct(value){ return percent.format(value)+"%"; }
  function shortBank(name){
    return name.replace(/^(АО|ДО АО)\s*/,"").replace(/^ДБ\s*/,"").replace(/\"/g,"")
      .replace("Народный Банк Казахстана","Народный банк")
      .replace("First Heartland Jusan Bank","Jusan")
      .replace("Банк ЦентрКредит","ЦентрКредит")
      .replace("Банк Казахстана","банк")
      .replace("ДОЧЕРНИЙ БАНК ","");
  }
  function currentRows(){ return records.filter(function(r){ return r.month===monthSelect.value && (!bankSelect.value || r.bank===bankSelect.value); }); }
  function filteredRows(){ return records.filter(function(r){ return !bankSelect.value || r.bank===bankSelect.value; }); }
  function monthly(rows,key){ return months.map(function(m){ return sum(rows.filter(function(r){ return r.month===m; }),key); }); }
  function chart(id){ return charts[id]; }
  function updateChart(id,option){ if(chart(id)) chart(id).setOption(option,true); }
  function base(){
    return {
      color:colors,
      backgroundColor:"transparent",
      textStyle:{fontFamily:"Inter, Arial, sans-serif",color:"#4b4a45"},
      animationDuration:280,
      tooltip:{trigger:"item",backgroundColor:"#fbfaf7",borderColor:"#dedad1",textStyle:{color:"#191917",fontSize:12}},
      aria:{enabled:true}
    };
  }
  function cartesianOption(values,unit,format){
    var o=base();
    o.grid={left:54,right:18,top:16,bottom:52};
    o.tooltip={trigger:"axis",backgroundColor:"#fbfaf7",borderColor:"#dedad1",textStyle:{color:"#191917",fontSize:12},
      formatter:function(items){
        var p=items[0]; return esc(p.axisValue)+"<br>"+esc(p.seriesName)+": <b>"+format(p.value)+" "+unit+"</b>";
      }};
    o.xAxis={type:"category",data:months.map(monthLabel),axisTick:{show:false},axisLine:{lineStyle:{color:"#cbc6ba"}},axisLabel:{color:"#85837a",fontSize:11}};
    o.yAxis={type:"value",name:unit,nameTextStyle:{color:"#85837a"},splitLine:{lineStyle:{color:"#ece9e2"}},axisLabel:{color:"#85837a",formatter:function(v){return format(v);}}};
    o.series=[{type:"line",name:bankSelect.value ? shortBank(bankSelect.value) : "Все банки",data:values.map(function(v){return v/(unit==="млрд ₸"?bn:trn);}),smooth:false,symbolSize:7,lineStyle:{width:3},areaStyle:{opacity:.08}}];
    return o;
  }

  function fillFilters(){
    months.forEach(function(m){ var o=document.createElement("option"); o.value=m; o.textContent=monthLabel(m); monthSelect.appendChild(o); });
    monthSelect.value=months[months.length-1];
    var all=document.createElement("option"); all.value=""; all.textContent="Все банки"; bankSelect.appendChild(all);
    banks.forEach(function(b){ var o=document.createElement("option"); o.value=b; o.textContent=b; bankSelect.appendChild(o); });
    updateBankOptions();
  }
  function updateBankOptions(){
    var present=new Set(records.filter(function(r){return r.month===monthSelect.value;}).map(function(r){return r.bank;}));
    Array.from(bankSelect.options).forEach(function(option){if(option.value) option.disabled=!present.has(option.value);});
    if(bankSelect.value && !present.has(bankSelect.value)) bankSelect.value="";
  }
  function renderKpis(rows){
    var depositSum=sum(rows,"deposits_people")+sum(rows,"deposits_business");
    document.getElementById("kpi-assets").textContent=fmtTrn(sum(rows,"assets"));
    document.getElementById("kpi-loans").textContent=fmtTrn(sum(rows,"loans"));
    document.getElementById("kpi-liabilities").textContent=fmtTrn(sum(rows,"liabilities"));
    document.getElementById("kpi-people").textContent=depositSum ? fmtPct(sum(rows,"deposits_people")/depositSum*100) : "—";
  }
  function renderAssets(rows){
    var data=rows.slice().sort(function(a,b){return a.assets-b.assets;});
    var o=base();
    o.grid={left:165,right:38,top:10,bottom:38};
    o.tooltip={trigger:"item",backgroundColor:"#fbfaf7",borderColor:"#dedad1",textStyle:{color:"#191917"},
      formatter:function(p){return esc(p.data.full)+"<br><b>"+fmtTrn(p.value*trn)+" трлн ₸</b>";}};
    o.xAxis={type:"value",name:"трлн ₸",nameTextStyle:{color:"#85837a"},splitLine:{lineStyle:{color:"#ece9e2"}},axisLabel:{color:"#85837a",formatter:function(v){return number.format(v);}}};
    o.yAxis={type:"category",data:data.map(function(r){return shortBank(r.bank);}),axisLabel:{color:"#4b4a45",fontSize:11,width:150,overflow:"truncate"},axisTick:{show:false},axisLine:{show:false}};
    o.series=[{type:"bar",barMaxWidth:16,data:data.map(function(r){return {value:r.assets/trn,full:r.bank};}),itemStyle:{color:"#2e5266"}}];
    updateChart("chart-assets",o);
  }
  function renderTreemap(rows){
    var o=base();
    o.tooltip={formatter:function(p){return esc(p.data.full)+"<br><b>"+fmtTrn(p.value*trn)+" трлн ₸</b>";},backgroundColor:"#fbfaf7",borderColor:"#dedad1",textStyle:{color:"#191917"}};
    o.series=[{type:"treemap",roam:false,breadcrumb:{show:false},nodeClick:false,leafDepth:1,label:{show:true,formatter:function(p){return p.data.short;},fontSize:11},itemStyle:{borderColor:"#fbfaf7",borderWidth:2,gapWidth:2},
      data:rows.map(function(r){return {name:r.bank,short:shortBank(r.bank),full:r.bank,value:r.assets/trn};})}];
    updateChart("chart-treemap",o);
  }
  function renderDepositBanks(rows){
    var data=rows.slice().sort(function(a,b){return a.assets-b.assets;});
    var o=base();
    o.grid={left:165,right:26,top:26,bottom:60};
    o.legend={data:["Физлица","Юрлица"],top:0,textStyle:{color:"#4b4a45",fontSize:11}};
    o.tooltip={trigger:"axis",axisPointer:{type:"shadow"},formatter:function(items){var i=items[0].dataIndex,r=data[i],total=r.deposits_people+r.deposits_business;return esc(r.bank)+"<br>Физлица: <b>"+fmtPct(r.deposits_people/total*100)+"</b><br>Юрлица: <b>"+fmtPct(r.deposits_business/total*100)+"</b>";}};
    o.xAxis={type:"value",max:100,axisLabel:{formatter:"{value}%",color:"#85837a"},splitLine:{lineStyle:{color:"#ece9e2"}}};
    o.yAxis={type:"category",data:data.map(function(r){return shortBank(r.bank);}),axisLabel:{color:"#4b4a45",fontSize:11,width:150,overflow:"truncate"},axisTick:{show:false},axisLine:{show:false}};
    o.series=[
      {name:"Физлица",type:"bar",stack:"deposits",barMaxWidth:17,data:data.map(function(r){var t=r.deposits_people+r.deposits_business;return t?r.deposits_people/t*100:0;}),itemStyle:{color:"#2e5266"}},
      {name:"Юрлица",type:"bar",stack:"deposits",barMaxWidth:17,data:data.map(function(r){var t=r.deposits_people+r.deposits_business;return t?r.deposits_business/t*100:0;}),itemStyle:{color:"#b68a4b"}}
    ];
    updateChart("chart-deposit-banks",o);
  }
  function renderOverdue(rows){
    var values=monthly(rows,"overdue");
    var o=base();
    o.legend={bottom:0,type:"scroll",textStyle:{fontSize:11,color:"#4b4a45"}};
    o.tooltip={formatter:function(p){return esc(p.name)+"<br><b>"+fmtBn(p.value*bn)+" млрд ₸</b>";},backgroundColor:"#fbfaf7",borderColor:"#dedad1",textStyle:{color:"#191917"}};
    o.series=[{type:"pie",radius:["43%","70%"],center:["50%","44%"],label:{formatter:"{b}",fontSize:11},data:months.map(function(m,i){return {name:monthLabel(m),value:values[i]/bn};})}];
    updateChart("chart-overdue",o);
  }
  function renderDepositMix(rows){
    var people=sum(rows,"deposits_people"),business=sum(rows,"deposits_business");
    var o=base();
    o.legend={bottom:0,textStyle:{fontSize:11,color:"#4b4a45"}};
    o.tooltip={formatter:function(p){return esc(p.name)+"<br><b>"+fmtTrn(p.value*trn)+" трлн ₸</b> · "+fmtPct(p.percent);},backgroundColor:"#fbfaf7",borderColor:"#dedad1",textStyle:{color:"#191917"}};
    o.series=[{type:"pie",radius:"72%",center:["50%","43%"],label:{formatter:"{d}%",fontSize:12},data:[{name:"Физлица",value:people/trn,itemStyle:{color:"#2e5266"}},{name:"Юрлица",value:business/trn,itemStyle:{color:"#b68a4b"}}]}];
    updateChart("chart-deposit-mix",o);
  }
  function renderTable(rows){
    var body=document.getElementById("bank-table"); body.replaceChildren();
    rows.slice().sort(function(a,b){return b.assets-a.assets;}).forEach(function(r){
      var t=document.createElement("tr");
      var total=r.deposits_people+r.deposits_business;
      [r.bank,fmtTrn(r.assets),fmtTrn(r.loans),fmtTrn(r.liabilities),r.overdue===null?"—":fmtBn(r.overdue),total?fmtPct(r.deposits_people/total*100):"—"].forEach(function(value){
        var cell=document.createElement("td"); cell.textContent=value; t.appendChild(cell);
      });
      body.appendChild(t);
    });
  }
  function renderJusan(){
    var rows=records.filter(function(r){return r.bank.indexOf("First Heartland Jusan Bank")!==-1;});
    var o=base();
    o.grid={left:55,right:20,top:58,bottom:50};
    o.legend={top:10,textStyle:{color:"#4b4a45"}};
    o.tooltip={trigger:"axis",axisPointer:{type:"shadow"},formatter:function(items){return esc(items[0].axisValue)+"<br>"+items.map(function(p){return esc(p.seriesName)+": <b>"+number.format(p.value)+" трлн ₸</b>";}).join("<br>");}};
    o.xAxis={type:"category",data:months.map(monthLabel),axisTick:{show:false},axisLabel:{color:"#85837a"}};
    o.yAxis={type:"value",name:"трлн ₸",splitLine:{lineStyle:{color:"#ece9e2"}},axisLabel:{color:"#85837a",formatter:function(v){return number.format(v);}}};
    o.series=[
      {name:"Активы",type:"bar",barMaxWidth:18,data:monthly(rows,"assets").map(function(v){return v/trn;}),itemStyle:{color:"#2e5266"}},
      {name:"Депозиты",type:"bar",barMaxWidth:18,data:months.map(function(m){var one=rows.find(function(r){return r.month===m;});return one?(one.deposits_people+one.deposits_business)/trn:null;}),itemStyle:{color:"#b68a4b"}},
      {name:"Кредиты",type:"bar",barMaxWidth:18,data:monthly(rows,"loans").map(function(v){return v/trn;}),itemStyle:{color:"#89a7a0"}}
    ];
    updateChart("chart-jusan",o);
  }
  function render(){
    var current=currentRows(),all=filteredRows();
    renderKpis(current);
    renderTable(current);
    if(!window.echarts) return;
    renderAssets(current);
    renderTreemap(current);
    renderDepositBanks(current);
    updateChart("chart-loans",cartesianOption(monthly(all,"loans"),"трлн ₸",number.format));
    updateChart("chart-liabilities",cartesianOption(monthly(all,"liabilities"),"трлн ₸",number.format));
    renderOverdue(all);
    renderDepositMix(current);
  }
  function setupTabs(){
    document.querySelectorAll(".tab").forEach(function(btn){btn.addEventListener("click",function(){
      document.querySelectorAll(".tab").forEach(function(other){var active=other===btn;other.classList.toggle("active",active);other.setAttribute("aria-selected",String(active));});
      document.querySelectorAll(".tab-panel").forEach(function(panel){panel.hidden=panel.id!==btn.dataset.tab;});
      if(btn.dataset.tab==="jusan") renderJusan();
      requestAnimationFrame(function(){Object.keys(charts).forEach(function(id){charts[id].resize();});});
    });});
  }
  if(!records.length){document.querySelector(".wrap").innerHTML='<p class="loading-error">Данные отчёта недоступны.</p>';return;}
  fillFilters();
  setupTabs();
  monthSelect.addEventListener("change",function(){updateBankOptions();render();});
  bankSelect.addEventListener("change",render);
  document.getElementById("reset").addEventListener("click",function(){monthSelect.value=months[months.length-1];bankSelect.value="";updateBankOptions();render();});
  if(window.echarts){
    document.querySelectorAll(".chart").forEach(function(el){charts[el.id]=echarts.init(el);});
    window.addEventListener("resize",function(){Object.keys(charts).forEach(function(id){charts[id].resize();});});
  } else {
    document.querySelectorAll(".chart").forEach(function(el){el.innerHTML='<p class="loading-error">Графики недоступны. Числа можно посмотреть в таблице ниже.</p>';});
  }
  render();
})();
