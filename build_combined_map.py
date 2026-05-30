#!/usr/bin/env python3
"""Combined 2025+2026 Champaign crime map (City open data) with a year toggle."""
import csv, json, collections, datetime

FILES = [('champaign_crime_2025.csv', 2025), ('champaign_crime_2026.csv', 2026)]
OUT = 'champaign_crime_combined_map.html'
BASE = datetime.datetime(2025, 1, 1)

HARMONIZE = {
 'Assault/Battery/Intimidation':'Assault','Homicide':'Assault','Kidnapping/Abduction':'Assault','Unlawful Restraint':'Assault',
 'Robbery':'Robbery',
 'Theft':'Theft','Stolen Property':'Theft','Shoplifting':'Theft',
 'Burglary/Breaking & Entering':'Burglary',
 'Motor Vehicle Theft':'Vehicle Theft',
 'Destruction/Damage/Vandalism of Property':'Vandalism',
 'Fraud':'Fraud/Forgery','Counterfeiting/Forgery':'Fraud/Forgery','Embezzlement':'Fraud/Forgery',
 'Extortion/Blackmail':'Fraud/Forgery','Unlawful Use/Disclosure of Information/Data':'Fraud/Forgery',
 'Drugs/Narcotics':'Drugs/Alcohol','Driving under the Influence':'Drugs/Alcohol','Liquor Law Violations':'Drugs/Alcohol','Tobacco Offenses':'Drugs/Alcohol',
 'Weapon Law Violations':'Weapons',
 'Prostitution':'Sex/Vice','Pornography/Obscene Material':'Sex/Vice','Gambling':'Sex/Vice',
 'Accident':'Traffic/Accident','Traffic Offenses':'Traffic/Accident','Parking Offenses':'Traffic/Accident','Pedestrian Offenses':'Traffic/Accident','Vehicle Tow':'Traffic/Accident',
 'Arson':'Arson',
 'Investigation':'Other/Admin','Lost & Found':'Other/Admin','Warrants':'Other/Admin','Family Offenses, Nonviolent':'Other/Admin',
 'Disorderly Conduct':'Other/Admin','Trespassing':'Other/Admin','Missing Person':'Other/Admin','Interference w/Public Officers':'Other/Admin',
 'Violation of Criminal Registry Laws':'Other/Admin','Animal-Related':'Other/Admin','Probation/Parole/Bail/Pretrial violations':'Other/Admin',
 'Curfew/Loitering/Soliciting':'Other/Admin','Waste Management Offenses':'Other/Admin','Miscellaneous State Law Violations':'Other/Admin','Local Ordinance Violations':'Other/Admin',
}
COLORS = {'Assault':'#ef4444','Robbery':'#ec4899','Theft':'#3b82f6','Burglary':'#22c55e','Vehicle Theft':'#06b6d4','Vandalism':'#f59e0b',
 'Fraud/Forgery':'#a855f7','Drugs/Alcohol':'#84cc16','Weapons':'#b91c1c','Sex/Vice':'#db2777','Traffic/Accident':'#64748b','Arson':'#fb923c','Other/Admin':'#9ca3af'}

groups, cats = [], []
def gi(g):
    if g not in groups: groups.append(g)
    return groups.index(g)
def ci(c):
    if c not in cats: cats.append(c)
    return cats.index(c)

rows = []; maxmin = 0; per_year = collections.Counter()
for fn, yr in FILES:
    for r in csv.DictReader(open(fn, encoding='utf-8')):
        try:
            la = round(float(r['latitude']), 5); lo = round(float(r['longitude']), 5)
        except: continue
        if not la or not lo or not r.get('datetime'): continue
        dt = datetime.datetime.strptime(r['datetime'][:16], '%Y-%m-%dT%H:%M')
        mins = int((dt - BASE).total_seconds() // 60)
        cat = r['category'] or 'Unknown'
        rows.append([gi(HARMONIZE.get(cat, 'Other/Admin')), mins, la, lo, ci(cat)])
        maxmin = max(maxmin, mins); per_year[yr] += 1

# order groups by frequency
cnt = collections.Counter(r[0] for r in rows)
order = sorted(range(len(groups)), key=lambda i: -cnt[i])
remap = {old: new for new, old in enumerate(order)}
groups = [groups[i] for i in order]
for r in rows: r[0] = remap[r[0]]

gcat = collections.defaultdict(collections.Counter)
for r in rows: gcat[r[0]][cats[r[4]]] += 1
groupcats = [[c for c, _ in gcat[g].most_common()] for g in range(len(groups))]
payload = {'groups': groups, 'colors': [COLORS.get(g, '#9ca3af') for g in groups], 'cats': cats,
           'groupcats': groupcats, 'rows': rows, 'maxmin': maxmin,
           'meta': {'n': len(rows), 'y2025': per_year[2025], 'y2026': per_year[2026]}}
data_js = json.dumps(payload, separators=(',', ':'))
json.dump(payload, open('champaign_crime_combined.json', 'w'), separators=(',', ':'))

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Champaign County Crime Map 2025–2026</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
<style>
 :root{--bg:#0f172a;--panel:#1e293b;--ink:#e2e8f0;--muted:#94a3b8;--line:#334155;--accent:#2563eb;}
 *{box-sizing:border-box;} html,body{margin:0;height:100%;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;}
 #app{display:flex;height:100vh;overflow:hidden;} #map{flex:1;height:100%;background:#aadaff;}
 #side{width:344px;background:var(--bg);color:var(--ink);overflow-y:auto;padding:14px 14px 50px;}
 #side h1{font-size:16px;margin:0 0 2px;} .sub{color:var(--muted);font-size:11.5px;margin-bottom:12px;line-height:1.5;}
 .card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:11px;margin-bottom:11px;}
 .card h2{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:0 0 9px;}
 .kpi{display:flex;gap:8px;} .kpi .box{flex:1;text-align:center;background:#0b1220;border-radius:8px;padding:7px 2px;}
 .kpi .num{font-size:18px;font-weight:700;} .kpi .lab{font-size:9px;color:var(--muted);text-transform:uppercase;}
 input,select,button{font:inherit;}
 .srch{display:flex;gap:6px;} .srch input{flex:1;background:#0b1220;border:1px solid var(--line);color:var(--ink);border-radius:8px;padding:8px;font-size:13px;}
 .srch button{background:var(--accent);color:#fff;border:none;border-radius:8px;padding:0 12px;cursor:pointer;}
 .rowflex{display:flex;gap:8px;align-items:center;margin-top:8px;font-size:12px;color:var(--muted);}
 .rowflex select{background:#0b1220;border:1px solid var(--line);color:var(--ink);border-radius:6px;padding:5px;}
 #searchInfo{font-size:12px;margin-top:8px;line-height:1.5;} #searchInfo b{color:#fff;}
 .seg{display:flex;gap:6px;margin-bottom:9px;} .seg button{flex:1;background:#0b1220;color:var(--ink);border:1px solid var(--line);padding:8px;border-radius:8px;font-size:13px;cursor:pointer;font-weight:600;}
 .seg button.active{background:var(--accent);border-color:var(--accent);color:#fff;}
 .dates{display:flex;gap:8px;} .dates label{flex:1;font-size:10px;color:var(--muted);}
 .dates input{width:100%;background:#0b1220;border:1px solid var(--line);color:var(--ink);border-radius:7px;padding:6px;font-size:12px;margin-top:3px;}
 .chips{display:flex;flex-wrap:wrap;gap:5px;margin-top:9px;} .chips button{background:#0b1220;border:1px solid var(--line);color:var(--ink);border-radius:13px;padding:4px 9px;font-size:11px;cursor:pointer;}
 .chips button:hover{border-color:var(--accent);}
 .hourwrap{padding:2px 4px 0;} .hourlab{font-size:12px;color:var(--ink);margin-bottom:6px;text-align:center;}
 .dual{position:relative;height:30px;}
 .dual input[type=range]{position:absolute;width:100%;margin:0;background:none;pointer-events:none;-webkit-appearance:none;top:9px;height:0;}
 .dual input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;pointer-events:auto;height:16px;width:16px;border-radius:50%;background:var(--accent);border:2px solid #fff;cursor:pointer;}
 .dual .track{position:absolute;top:13px;left:0;right:0;height:4px;background:#0b1220;border-radius:3px;} .dual .fill{position:absolute;top:13px;height:4px;background:var(--accent);border-radius:3px;}
 .toggle{display:flex;gap:6px;} .toggle button{flex:1;background:var(--panel);color:var(--ink);border:1px solid var(--line);padding:7px;border-radius:8px;font-size:12px;cursor:pointer;}
 .toggle button.active{background:var(--accent);border-color:var(--accent);color:#fff;}
 .drawbtn{background:#0b1220;border:1px solid var(--line);color:var(--ink);border-radius:8px;padding:5px 9px;font-size:12px;cursor:pointer;}
 .drawbtn.on{background:var(--accent);border-color:var(--accent);color:#fff;}
 .sbadge{display:inline-block;font-weight:800;padding:2px 9px;border-radius:12px;font-size:12px;color:#06121f;}
 #safetyHelp{margin-left:auto;cursor:help;text-decoration:underline dotted;}
 .trow{display:flex;align-items:center;gap:8px;font-size:12.5px;padding:3px 2px;cursor:pointer;border-radius:6px;user-select:none;}
 .trow:hover{background:#0b1220;} .trow.off{opacity:.34;} .sw{width:12px;height:12px;border-radius:3px;flex:0 0 auto;} .trow .nm{flex:1;} .trow .ct{color:var(--muted);font-variant-numeric:tabular-nums;}
 .bar{height:6px;background:#0b1220;border-radius:4px;overflow:hidden;margin-top:2px;} .bar>i{display:block;height:100%;}
 #chart{width:100%;height:64px;display:block;} .small{font-size:10.5px;color:var(--muted);}
 .leaflet-popup-content{font-size:13px;line-height:1.45;} .pin{border-radius:50%;border:1.5px solid rgba(255,255,255,.85);box-shadow:0 0 2px rgba(0,0,0,.5);}
</style></head>
<body><div id="app">
 <div id="side">
  <h1>Champaign County Crime Map — 2025 &amp; 2026</h1>
  <div class="sub">Countywide (all agencies) &middot; <span id="hdrCount"></span><br>Jan 2025 – May 2026</div>

  <div class="card"><h2>Search a location</h2>
   <div class="srch"><input id="q" placeholder="address or place, e.g. Market Place Mall"><button id="go">Go</button></div>
   <div class="rowflex">Radius
     <select id="radius"><option value="250">250 m</option><option value="400" selected>400 m</option><option value="800">800 m</option><option value="1600">1 mi</option></select>
     <button id="clearSearch" style="margin-left:auto;background:none;border:1px solid var(--line);color:var(--muted);border-radius:6px;padding:4px 8px;cursor:pointer;">clear</button></div>
   <div id="searchInfo" class="small">Type an address to center the map and count nearby incidents (within the current filters).</div>
  </div>

  <div class="card"><h2>Plan a route &amp; safety score</h2>
   <div class="srch" style="margin-bottom:6px"><input id="rStart" placeholder="start, e.g. Market Place Mall"></div>
   <div class="srch" style="margin-bottom:6px"><input id="rEnd" placeholder="end, e.g. Main Quad"><button id="rGo">Route</button></div>
   <div class="rowflex"><button id="rDraw" class="drawbtn">✎ Draw on map</button><span class="small">click 2+ map points</span>
     <button id="rClear" style="margin-left:auto;background:none;border:1px solid var(--line);color:var(--muted);border-radius:6px;padding:4px 8px;cursor:pointer;">clear</button></div>
   <div class="rowflex">Corridor
     <select id="corridor"><option value="100">100 m</option><option value="150" selected>150 m</option><option value="250">250 m</option></select>
     <span class="small" id="safetyHelp" title="Safety score = 100·exp(-risk/30), where risk = (violent per km·yr) + 0.2·(property per km·yr) within the route corridor, under the current filters. Higher = safer. Levels: Low <10, Moderate <25, Elevated <45, High otherwise.">&#9432; how scored</span></div>
   <div id="routeInfo" class="small">Enter a start &amp; end, or click &#9998; Draw on map, to route and score its safety.</div>
  </div>

  <div class="card"><h2>Year</h2>
   <div class="seg"><button id="yBoth" class="active">Both</button><button id="y2025">2025</button><button id="y2026">2026</button></div>
   <h2 style="margin-top:4px">Time window</h2>
   <div class="dates"><label>From<input type="date" id="from"></label><label>To<input type="date" id="to"></label></div>
   <div class="chips" id="chips"></div>
  </div>

  <div class="card"><h2>Hour of day</h2>
   <div class="hourwrap"><div class="hourlab" id="hourLab">12 AM – 12 AM (all hours)</div>
     <div class="dual"><div class="track"></div><div class="fill" id="hourFill"></div>
       <input type="range" id="h0" min="0" max="24" value="0"><input type="range" id="h1" min="0" max="24" value="24"></div></div>
  </div>

  <div class="card"><h2>Display</h2><div class="toggle"><button id="btnPins">Clustered pins</button><button id="btnHeat" class="active">Heatmap</button></div></div>

  <div class="card"><h2>KPIs (current filter)</h2>
   <div class="kpi"><div class="box"><div class="num" id="kTotal">0</div><div class="lab">incidents</div></div>
     <div class="box"><div class="num" id="kDay">0</div><div class="lab">per day</div></div>
     <div class="box"><div class="num" id="kViol">0</div><div class="lab">violent</div></div></div>
  </div>

  <div class="card"><h2>Incidents by type <span class="small">(click to toggle · hover for details)</span></h2><div id="types"></div>
   <div class="small" style="margin-top:7px">⌀ <b>Other/Admin</b> is <b>off by default</b> — these are non-crime / administrative reports (investigations, lost &amp; found, warrants, trespassing, nonviolent family offenses, missing persons, disorderly conduct, etc.), not offenses against a person or property.</div></div>
  <div class="card"><h2>Daily timeline</h2><canvas id="chart"></canvas><div class="small" id="chartlab"></div></div>
  <div class="small">2025: <span id="n25"></span> · 2026 (through May 29): <span id="n26"></span>. Countywide (Champaign-Urbana ~85%, Rantoul ~7%, other towns/rural ~8%). 40 NIBRS categories → 13 groups; original in each popup. Geocoding & routing via OSM.</div>
 </div>
 <div id="map"></div>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
<script>
const DATA = /*__DATA__*/;
const G=DATA.groups, COL=DATA.colors, CATS=DATA.cats, ROWS=DATA.rows;
const BASE=Date.UTC(2025,0,1);
const VIOLENT=new Set(['Assault','Robbery','Arson','Weapons']);
function rowDate(min){return new Date(BASE+min*60000);}
function mins(y,m,d){return Math.round((Date.UTC(y,m,d)-BASE)/60000);}
function fmt(min){const d=rowDate(min);let h=d.getUTCHours();const ap=h<12?'AM':'PM';let hh=h%12;if(hh===0)hh=12;
 return (d.getUTCMonth()+1)+'/'+d.getUTCDate()+'/'+d.getUTCFullYear()+' '+hh+':'+String(d.getUTCMinutes()).padStart(2,'0')+' '+ap;}
function dstr(d){return d.getUTCFullYear()+'-'+String(d.getUTCMonth()+1).padStart(2,'0')+'-'+String(d.getUTCDate()).padStart(2,'0');}
const Y2026=mins(2026,0,1);

const map=L.map('map',{preferCanvas:true}).setView([40.12,-88.21],10);
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{attribution:'&copy; OpenStreetMap &copy; CARTO',subdomains:'abcd',maxZoom:19}).addTo(map);
window._map=map;

// shared per-group icons (performance for ~23k markers)
const ICONS=COL.map(c=>L.divIcon({className:'',html:'<div class="pin" style="width:9px;height:9px;background:'+c+'"></div>',iconSize:[9,9],iconAnchor:[4,4]}));
let minLat=90,maxLat=-90,minLon=180,maxLon=-180;
const HOUR=new Array(ROWS.length), MK=new Array(ROWS.length);
for(let i=0;i<ROWS.length;i++){const r=ROWS[i];
 HOUR[i]=rowDate(r[1]).getUTCHours();
 const m=L.marker([r[2],r[3]],{icon:ICONS[r[0]]});
 m.bindPopup('<b style="color:'+COL[r[0]]+'">'+G[r[0]]+'</b><br>'+CATS[r[4]]+'<br>'+fmt(r[1])+'<br><span style="color:#777">Champaign County</span>');
 MK[i]=m;
 if(r[2]<minLat)minLat=r[2];if(r[2]>maxLat)maxLat=r[2];if(r[3]<minLon)minLon=r[3];if(r[3]>maxLon)maxLon=r[3];}
const BOUNDS=[[minLat,minLon],[maxLat,maxLon]];

const cluster=L.markerClusterGroup({chunkedLoading:true,maxClusterRadius:50,
 iconCreateFunction:c=>{const n=c.getChildCount();const s=n<10?30:n<100?38:n<1000?46:54;
  return L.divIcon({html:'<div style="width:'+s+'px;height:'+s+'px;line-height:'+s+'px;border-radius:50%;background:rgba(37,99,235,.85);color:#fff;text-align:center;font-weight:700;font-size:12px;border:3px solid rgba(255,255,255,.7)">'+n+'</div>',className:'',iconSize:[s,s]});}});
let heat=null, mode='heat';

let active=new Array(G.length).fill(true);
let dMin=0, dMax=DATA.maxmin+1, hMin=0, hMax=24;
let searchPt=null, searchCircle=null, searchMarker=null;
let routeLine=null, routeLayers=[], corridorM=150;
let drawMode=false, clickPts=[], clickMk=[];

function passes(i){const r=ROWS[i];if(!active[r[0]])return false;if(r[1]<dMin||r[1]>=dMax)return false;const h=HOUR[i];if(h<hMin||h>=hMax)return false;return true;}
function currentIdx(){const o=[];for(let i=0;i<ROWS.length;i++)if(passes(i))o.push(i);return o;}
function render(idx){
 if(mode==='pins'){ if(heat){map.removeLayer(heat);heat=null;} cluster.clearLayers(); cluster.addLayers(idx.map(i=>MK[i])); if(!map.hasLayer(cluster))map.addLayer(cluster); }
 else { if(map.hasLayer(cluster))map.removeLayer(cluster); if(heat)map.removeLayer(heat);
  heat=L.heatLayer(idx.map(i=>[ROWS[i][2],ROWS[i][3],0.6]),{radius:18,blur:15,maxZoom:16,gradient:{0.2:'#1d4ed8',0.4:'#22c55e',0.6:'#eab308',0.8:'#f97316',1:'#dc2626'}}); map.addLayer(heat); }
}
function updateStats(idx){
 document.getElementById('kTotal').textContent=idx.length.toLocaleString();
 const days=Math.max(1,Math.round((dMax-dMin)/1440)); document.getElementById('kDay').textContent=(idx.length/days).toFixed(1);
 let viol=0; for(const i of idx){if(VIOLENT.has(G[ROWS[i][0]]))viol++;}
 document.getElementById('kViol').textContent=viol.toLocaleString();
 // type-bar counts: per group within the time window, ignoring the category toggle so off categories still show their count
 const gc=new Array(G.length).fill(0);
 for(let i=0;i<ROWS.length;i++){const r=ROWS[i];if(r[1]<dMin||r[1]>=dMax)continue;const h=HOUR[i];if(h<hMin||h>=hMax)continue;gc[r[0]]++;}
 const mx=Math.max(1,...gc);
 document.querySelectorAll('.trow').forEach(row=>{const g=+row.dataset.g;row.querySelector('.ct').textContent=gc[g].toLocaleString();row.querySelector('.bar>i').style.width=(100*gc[g]/mx)+'%';});
 drawChart(idx);
 if(searchPt)updateSearchInfo(idx);
 if(routeLine)routeStats(idx);
}
function drawChart(idx){
 const cv=document.getElementById('chart');const w=cv.width=cv.clientWidth*2,h=cv.height=128;const x=cv.getContext('2d');x.clearRect(0,0,w,h);
 const d0=Math.floor(dMin/1440),d1=Math.floor((dMax-1)/1440);const nd=Math.max(1,d1-d0+1);const bins=new Array(nd).fill(0);
 for(const i of idx){const d=Math.floor(ROWS[i][1]/1440)-d0;if(d>=0&&d<nd)bins[d]++;}
 const mx=Math.max(1,...bins);const bw=w/nd;
 for(let i=0;i<nd;i++){const bh=(bins[i]/mx)*(h-6);x.fillStyle='#3b82f6';x.fillRect(i*bw,h-bh,Math.max(1,bw-1),bh);}
 document.getElementById('chartlab').textContent=dstr(rowDate(dMin))+' → '+dstr(rowDate(Math.max(dMin,dMax-1)))+' · peak '+mx+'/day';
}
let tmr=null;
function apply(){ if(tmr)clearTimeout(tmr); tmr=setTimeout(()=>{const idx=currentIdx();render(idx);updateStats(idx);},30); }

// type legend/filter
const tEl=document.getElementById('types'); const gtot=new Array(G.length).fill(0); ROWS.forEach(r=>gtot[r[0]]++);
const GCATS=DATA.groupcats||[];
for(let g=0;g<G.length;g++){const row=document.createElement('div');row.className='trow';row.dataset.g=g;
 row.title=G[g]+': '+(GCATS[g]||[]).join(', ');
 row.innerHTML='<span class="sw" style="background:'+COL[g]+'"></span><span class="nm">'+G[g]+'<div class="bar"><i style="width:100%;background:'+COL[g]+'"></i></div></span><span class="ct">'+gtot[g]+'</span>';
 if(G[g]==='Other/Admin'){active[g]=false;row.classList.add('off');}
 row.onclick=()=>{active[g]=!active[g];row.classList.toggle('off',!active[g]);apply();};tEl.appendChild(row);}

// display toggle
document.getElementById('btnPins').onclick=function(){mode='pins';this.classList.add('active');document.getElementById('btnHeat').classList.remove('active');apply();};
document.getElementById('btnHeat').onclick=function(){mode='heat';this.classList.add('active');document.getElementById('btnPins').classList.remove('active');apply();};

// dates + year toggle + month chips
const fromI=document.getElementById('from'),toI=document.getElementById('to');
const MIN_D=rowDate(0),MAX_D=rowDate(DATA.maxmin);
fromI.min=toI.min=dstr(MIN_D);fromI.max=toI.max=dstr(MAX_D);
function setInputs(){fromI.value=dstr(rowDate(dMin));toI.value=dstr(rowDate(Math.min(DATA.maxmin,dMax-1)));}
const yB=document.getElementById('yBoth'),y25=document.getElementById('y2025'),y26=document.getElementById('y2026');
function hiY(b){[yB,y25,y26].forEach(x=>x.classList.remove('active'));if(b)b.classList.add('active');}
const MONTHS=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function renderChips(year){const c=document.getElementById('chips');c.innerHTML='';
 if(year==='both'){const b=document.createElement('button');b.textContent='Last 30 days';
   b.onclick=()=>{hiY(null);dMax=DATA.maxmin+1;dMin=Math.max(0,DATA.maxmin-30*1440);setInputs();apply();};c.appendChild(b);return;}
 const yr=+year; const lastM=(yr===2026)?4:11; // 2026 data ends in May
 for(let m=0;m<=lastM;m++){const b=document.createElement('button');b.textContent=MONTHS[m];
   b.onclick=()=>{dMin=mins(yr,m,1);dMax=Math.min(DATA.maxmin+1,mins(yr,m+1,1));setInputs();apply();};c.appendChild(b);}
}
function setYear(y,btn){hiY(btn);
 if(y==='both'){dMin=0;dMax=DATA.maxmin+1;}
 else if(y==='2025'){dMin=mins(2025,0,1);dMax=mins(2026,0,1);}
 else {dMin=mins(2026,0,1);dMax=DATA.maxmin+1;}
 setInputs();renderChips(y);apply();}
yB.onclick=()=>setYear('both',yB); y25.onclick=()=>setYear('2025',y25); y26.onclick=()=>setYear('2026',y26);
function syncDates(){const p=s=>{const a=s.split('-');return Math.round((Date.UTC(+a[0],+a[1]-1,+a[2])-BASE)/60000);};
 dMin=p(fromI.value);dMax=p(toI.value)+1440;hiY(null);apply();}
fromI.onchange=syncDates;toI.onchange=syncDates;

// hour dual slider
const h0=document.getElementById('h0'),h1=document.getElementById('h1'),fill=document.getElementById('hourFill'),hlab=document.getElementById('hourLab');
function htxt(h){const ap=h<12?'AM':'PM';let hh=h%12;if(hh===0)hh=12;return h===24?'12 AM':hh+' '+ap;}
function syncHour(){let a=+h0.value,b=+h1.value;if(a>b){const t=a;a=b;b=t;}hMin=a;hMax=(b===a)?a+1:b;
 fill.style.left=(a/24*100)+'%';fill.style.width=((b-a)/24*100)+'%';
 hlab.textContent=(a===0&&b===24)?'12 AM – 12 AM (all hours)':(htxt(a)+' – '+htxt(b));apply();}
h0.oninput=syncHour;h1.oninput=syncHour;

// location search
const qI=document.getElementById('q'),info=document.getElementById('searchInfo');
function haversine(la1,lo1,la2,lo2){const R=6371000,p=Math.PI/180;const dla=(la2-la1)*p,dlo=(lo2-lo1)*p;const x=Math.sin(dla/2)**2+Math.cos(la1*p)*Math.cos(la2*p)*Math.sin(dlo/2)**2;return 2*R*Math.asin(Math.sqrt(x));}
function updateSearchInfo(idx){if(!searchPt)return;const rad=+document.getElementById('radius').value;let near=0;const gc={};
 for(const i of idx){const r=ROWS[i];if(haversine(searchPt[0],searchPt[1],r[2],r[3])<=rad){near++;gc[G[r[0]]]=(gc[G[r[0]]]||0)+1;}}
 const top=Object.entries(gc).sort((a,b)=>b[1]-a[1]).slice(0,4).map(e=>e[0]+' '+e[1]).join(', ');
 info.innerHTML='<b>'+near.toLocaleString()+'</b> incidents within '+(rad>=1600?'1 mi':rad+' m')+' of <b>'+searchPt[2]+'</b> in the current filter.'+(top?'<br><span class="small">'+top+'</span>':'');}
async function doSearch(){const q=qI.value.trim();if(!q)return;info.textContent='Searching…';
 try{const vb='-88.50,40.50,-87.80,39.85';
  const url='https://nominatim.openstreetmap.org/search?format=json&limit=1&viewbox='+vb+'&bounded=1&q='+encodeURIComponent(q+', Champaign County, IL');
  const j=await (await fetch(url,{headers:{'Accept':'application/json'}})).json();
  if(!j.length){info.textContent='No match for "'+q+'". Add more detail.';return;}
  const la=+j[0].lat,lo=+j[0].lon,label=(j[0].display_name||q).split(',').slice(0,2).join(',');
  searchPt=[la,lo,label];
  if(searchMarker)map.removeLayer(searchMarker);if(searchCircle)map.removeLayer(searchCircle);
  const rad=+document.getElementById('radius').value;
  searchMarker=L.marker([la,lo],{icon:L.divIcon({className:'',html:'<div style="font-size:26px;line-height:26px;transform:translate(-50%,-100%)">📍</div>',iconSize:[0,0]})}).addTo(map);
  searchCircle=L.circle([la,lo],{radius:rad,color:'#2563eb',weight:2,fillColor:'#2563eb',fillOpacity:.08}).addTo(map);
  map.setView([la,lo],15,{animate:false});
  updateSearchInfo(currentIdx());
 }catch(e){info.textContent='Search failed (network/geocoder). '+e.message;}}
document.getElementById('go').onclick=doSearch;
qI.addEventListener('keydown',e=>{if(e.key==='Enter')doSearch();});
document.getElementById('radius').onchange=()=>{if(searchPt){if(searchCircle)searchCircle.setRadius(+document.getElementById('radius').value);updateSearchInfo(currentIdx());}};
document.getElementById('clearSearch').onclick=()=>{searchPt=null;if(searchMarker){map.removeLayer(searchMarker);searchMarker=null;}if(searchCircle){map.removeLayer(searchCircle);searchCircle=null;}
 info.innerHTML='Type an address to center the map and count nearby incidents (within the current filters).';};

// route planning (A -> B)
const MLAT=111320, MLON=111320*Math.cos(40.13*Math.PI/180);
function locxy(la,lo){return [(lo+88.23)*MLON,(la-40.11)*MLAT];}
function segDistM(px,py,a,b){const dx=b[0]-a[0],dy=b[1]-a[1],L2=dx*dx+dy*dy;const t=L2?Math.max(0,Math.min(1,((px-a[0])*dx+(py-a[1])*dy)/L2)):0;return Math.hypot(px-(a[0]+t*dx),py-(a[1]+t*dy));}
async function geocode2(q){const vb='-88.50,40.50,-87.80,39.85';
 const url='https://nominatim.openstreetmap.org/search?format=json&limit=1&viewbox='+vb+'&bounded=1&q='+encodeURIComponent(q+', Champaign County, IL');
 const j=await (await fetch(url,{headers:{'Accept':'application/json'}})).json();
 return j.length?{lat:+j[0].lat,lon:+j[0].lon,label:(j[0].display_name||q).split(',').slice(0,2).join(',')}:null;}
const rInfo=document.getElementById('routeInfo');
function clearRoute(){routeLayers.forEach(l=>map.removeLayer(l));routeLayers=[];routeLine=null;
 clickMk.forEach(m=>map.removeLayer(m));clickMk=[];clickPts=[];
 drawMode=false;const db=document.getElementById('rDraw');if(db)db.classList.remove('on');document.getElementById('map').style.cursor='';
 rInfo.innerHTML='Enter a start &amp; end, or click &#9998; Draw on map, to route and score its safety.';}
function safetyLevel(violent,property,lenKm,windowDays){
 const yf=365/Math.max(1,windowDays), L=Math.max(0.25,lenKm);
 const vKmYr=violent*yf/L, pKmYr=property*yf/L, risk=vKmYr+0.2*pKmYr;
 let level,color;
 if(risk<10){level='Low risk';color='#22c55e';}
 else if(risk<25){level='Moderate';color='#eab308';}
 else if(risk<45){level='Elevated';color='#f97316';}
 else{level='High risk';color='#dc2626';}
 return {level,color,score:Math.max(0,Math.min(100,Math.round(100*Math.exp(-risk/30)))),vKmYr,pKmYr};}
function routeStats(idx){if(!routeLine)return;
 let lenKm=0;for(let i=0;i<routeLine.length-1;i++)lenKm+=haversine(routeLine[i][0],routeLine[i][1],routeLine[i+1][0],routeLine[i+1][1]);lenKm/=1000;
 let mnLa=90,mxLa=-90,mnLo=180,mxLo=-180;for(const p of routeLine){if(p[0]<mnLa)mnLa=p[0];if(p[0]>mxLa)mxLa=p[0];if(p[1]<mnLo)mnLo=p[1];if(p[1]>mxLo)mxLo=p[1];}
 const padLa=corridorM/111320+0.001, padLo=corridorM/MLON+0.001;
 const RX=routeLine.map(p=>locxy(p[0],p[1]));
 const VIO=new Set(['Assault','Robbery','Weapons']), PRP=new Set(['Theft','Burglary','Vehicle Theft','Vandalism']);
 let near=0,viol=0,prop=0,vnight=0;const gc={};
 for(const i of idx){const r=ROWS[i],la=r[2],lo=r[3];
  if(la<mnLa-padLa||la>mxLa+padLa||lo<mnLo-padLo||lo>mxLo+padLo)continue;
  const xy=locxy(la,lo);let dm=1e9;for(let s=0;s<RX.length-1;s++){const dd=segDistM(xy[0],xy[1],RX[s],RX[s+1]);if(dd<dm){dm=dd;if(dm<=corridorM)break;}}
  if(dm<=corridorM){near++;const g=G[r[0]];gc[g]=(gc[g]||0)+1;if(VIO.has(g)){viol++;const h=(ROWS[i][1]%1440)/60|0;if(h>=22||h<6)vnight++;}else if(PRP.has(g))prop++;}}
 const wd=Math.max(1,Math.round((dMax-dMin)/1440)), yf=365/wd;
 const s=safetyLevel(viol,prop,lenKm,wd), nightPct=viol?Math.round(100*vnight/viol):0;
 const top=Object.entries(gc).sort((a,b)=>b[1]-a[1]).slice(0,5).map(e=>e[0]+' '+e[1]).join(', ');
 rInfo.innerHTML='<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px"><span class="sbadge" style="background:'+s.color+'">'+s.level+'</span><b style="font-size:13px">Safety '+s.score+'/100</b><span class="small">'+lenKm.toFixed(1)+' km</span></div>'
  +'<b>'+near.toLocaleString()+'</b> crimes within '+corridorM+' m &middot; <b>'+viol+'</b> violent &middot; ~'+Math.round(near*yf)+'/yr'
  +'<br><span class="small">'+s.vKmYr.toFixed(1)+' violent &amp; '+s.pKmYr.toFixed(0)+' property per km&middot;yr'+((nightPct>=40&&viol>=5)?' &middot; &#9888; '+nightPct+'% of violent after dark':'')+'</span>'
  +(top?'<br><span class="small">'+top+'</span>':'');}
async function planRoute(){const a=document.getElementById('rStart').value.trim(),b=document.getElementById('rEnd').value.trim();
 if(!a||!b){rInfo.textContent='Enter both a start and an end.';return;}
 rInfo.textContent='Geocoding start…';const ga=await geocode2(a);if(!ga){rInfo.textContent='No match for start: '+a;return;}
 rInfo.textContent='Geocoding end…';await new Promise(r=>setTimeout(r,1100));const gb=await geocode2(b);if(!gb){rInfo.textContent='No match for end: '+b;return;}
 rInfo.textContent='Routing…';let coords=null;
 try{const u='https://router.project-osrm.org/route/v1/driving/'+ga.lon+','+ga.lat+';'+gb.lon+','+gb.lat+'?overview=full&geometries=geojson';
  const jr=await (await fetch(u)).json();if(jr.routes&&jr.routes.length)coords=jr.routes[0].geometry.coordinates.map(c=>[c[1],c[0]]);}catch(e){}
 let approx=false;if(!coords||coords.length<2){coords=[[ga.lat,ga.lon],[gb.lat,gb.lon]];approx=true;}
 clearRoute();routeLine=coords;corridorM=+document.getElementById('corridor').value;
 routeLayers.push(L.polyline(coords,{color:'#0b1220',weight:8,opacity:.55}).addTo(map));
 routeLayers.push(L.polyline(coords,{color:'#22d3ee',weight:4,opacity:.95,dashArray:approx?'6,8':null}).addTo(map));
 const mk=(la,lo,t,c)=>L.marker([la,lo],{icon:L.divIcon({className:'',html:'<div style=\"background:'+c+';color:#fff;width:22px;height:22px;line-height:22px;border-radius:50%;text-align:center;font-weight:700;border:2px solid #fff;box-shadow:0 0 3px #000\">'+t+'</div>',iconSize:[22,22],iconAnchor:[11,11]})}).addTo(map);
 routeLayers.push(mk(ga.lat,ga.lon,'A','#16a34a'));routeLayers.push(mk(gb.lat,gb.lon,'B','#dc2626'));
 map.fitBounds(routeLayers[0].getBounds(),{padding:[45,45],animate:false});
 routeStats(currentIdx());}
document.getElementById('rGo').onclick=planRoute;
document.getElementById('rEnd').addEventListener('keydown',e=>{if(e.key==='Enter')planRoute();});
document.getElementById('corridor').onchange=()=>{corridorM=+document.getElementById('corridor').value;if(routeLine)routeStats(currentIdx());};
document.getElementById('rClear').onclick=clearRoute;
// point-to-point: click on map to connect a route
const drawBtn=document.getElementById('rDraw');
drawBtn.onclick=()=>{drawMode=!drawMode;drawBtn.classList.toggle('on',drawMode);
 document.getElementById('map').style.cursor=drawMode?'crosshair':'';
 if(drawMode){clickMk.forEach(m=>map.removeLayer(m));clickMk=[];clickPts=[];routeLayers.forEach(l=>map.removeLayer(l));routeLayers=[];routeLine=null;
  rInfo.innerHTML='&#9998; <b>Draw mode on</b> — click points on the map to connect a route. Click &#9998; again to stop.';}};
map.on('click',e=>{if(!drawMode)return;
 clickPts.push([e.latlng.lat,e.latlng.lng]);const n=clickPts.length;
 clickMk.push(L.marker([e.latlng.lat,e.latlng.lng],{icon:L.divIcon({className:'',html:'<div style=\"background:#2563eb;color:#fff;width:18px;height:18px;line-height:18px;border-radius:50%;text-align:center;font-weight:700;font-size:11px;border:2px solid #fff\">'+n+'</div>',iconSize:[18,18],iconAnchor:[9,9]})}).addTo(map));
 if(n>=2)buildClickRoute();else rInfo.innerHTML='Point 1 set — click another point to form a route.';});
async function buildClickRoute(){rInfo.textContent='Routing '+clickPts.length+' points…';let coords=null;
 try{const path=clickPts.map(p=>p[1]+','+p[0]).join(';');
  const u='https://router.project-osrm.org/route/v1/driving/'+path+'?overview=full&geometries=geojson';
  const jr=await (await fetch(u)).json();if(jr.routes&&jr.routes.length)coords=jr.routes[0].geometry.coordinates.map(c=>[c[1],c[0]]);}catch(e){}
 let approx=false;if(!coords||coords.length<2){coords=clickPts.slice();approx=true;}
 routeLayers.forEach(l=>map.removeLayer(l));routeLayers=[];
 routeLine=coords;corridorM=+document.getElementById('corridor').value;
 routeLayers.push(L.polyline(coords,{color:'#0b1220',weight:8,opacity:.55}).addTo(map));
 routeLayers.push(L.polyline(coords,{color:'#22d3ee',weight:4,opacity:.95,dashArray:approx?'6,8':null}).addTo(map));
 routeStats(currentIdx());}

// init
document.getElementById('hdrCount').textContent=DATA.meta.n.toLocaleString()+' incidents';
document.getElementById('n25').textContent=DATA.meta.y2025.toLocaleString();
document.getElementById('n26').textContent=DATA.meta.y2026.toLocaleString();
setInputs(); renderChips('both'); syncHour();
let userMoved=false;
function fitAll(){if(userMoved)return;map.invalidateSize();map.fitBounds(BOUNDS,{padding:[28,28],animate:false});}
[0,250,700,1300].forEach(t=>setTimeout(fitAll,t));
setTimeout(()=>{userMoved=true;},1400);
map.on('zoomstart dragstart',()=>{userMoved=true;});
window.addEventListener('resize',()=>{map.invalidateSize();});
</script></body></html>
"""
open(OUT,'w',encoding='utf-8').write(TEMPLATE.replace('/*__DATA__*/', data_js))
print('Wrote %s (%d KB)'%(OUT, len(TEMPLATE)//1024 + len(data_js)//1024))
print('Total incidents:', len(rows), '| 2025:', per_year[2025], '| 2026:', per_year[2026], '| groups:', len(groups))
