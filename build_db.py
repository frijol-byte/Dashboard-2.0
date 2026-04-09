<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CFPS Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/react/18.2.0/umd/react.development.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.2.0/umd/react-dom.development.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/babel-standalone/7.23.9/babel.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'IBM Plex Mono','SF Mono',monospace;background:#fff;color:#1e293b}
.nav{display:flex;gap:0;border-bottom:1px solid #e2e8f0;margin-bottom:8px;padding:0 14px}
.nav a{padding:8px 16px;font-size:10.5px;font-weight:400;color:#94a3b8;text-decoration:none;border-bottom:2px solid transparent;font-family:inherit;margin-bottom:-1px}
.nav a.active{font-weight:600;color:#0f172a;border-bottom-color:#2563eb}
.nav a:hover{color:#475569}
.zoom-wrap{position:relative;overflow:hidden;border-radius:4px;cursor:grab}
.zoom-wrap:active{cursor:grabbing}
.zoom-hint{position:absolute;bottom:2px;right:6px;font-size:8px;color:#c1c9d4;pointer-events:none}
.home-btn{position:fixed;top:8px;right:160px;z-index:50;display:inline-flex;align-items:center;gap:5px;padding:5px 12px;border-radius:6px;background:#fff;border:1px solid #d1d5db;color:#64748b;font-size:10px;font-weight:600;text-decoration:none;font-family:inherit;transition:all .2s}
.home-btn:hover{border-color:#2563eb;color:#2563eb;background:#eff6ff}
</style>
</head>
<body>
<a class="home-btn" href="index.html"><svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M3 12l9-9 9 9"/><path d="M5 10v10a1 1 0 001 1h3v-6h6v6h3a1 1 0 001-1V10"/></svg>Toolkit</a>
<div id="app"></div>
<script>
function odb(){return new Promise(function(r,j){var q=indexedDB.open('cfps',1);q.onupgradeneeded=function(){q.result.createObjectStore('c')};q.onsuccess=function(){r(q.result)};q.onerror=function(){j(q.error)}})}
function getCSV(){return odb().then(function(db){var tx=db.transaction('c','readonly'),rq=tx.objectStore('c').get('k');return new Promise(function(r){rq.onsuccess=function(){r(rq.result||null)};rq.onerror=function(){r(null)}})}).catch(function(){return null})}
function parseCSV(text){
  var lines=text.trim().split('\n');var hdr=lines[0].split(',').map(function(h){return h.trim().replace(/"/g,'').toUpperCase()});var rows=[];
  for(var i=1;i<lines.length;i++){var vals=lines[i].split(',');var r={};for(var j=0;j<hdr.length;j++)r[hdr[j]]=(vals[j]||'').trim().replace(/"/g,'');rows.push(r)}
  var all=rows.map(function(r){return{well:r.WELL||'',meas:parseFloat(r.MEASUREMENT)||0,rn:parseInt(r.ROW_NUMBER)||0,rl:r.ROW_LETTER||'',cn:parseInt(r.COLUMN_NUMBER)||0,key:r.KEY||'',lys:r.LYSATE||'',mm:r.MASTER_MIX||'',prod:r.PRODUCT||'',tmpl:r.TEMPLATE||'',op:r.OPERATOR||'',rv:parseFloat(r.REACTION_VOLUME)||0,dil:parseFloat(r.DILUTION)||0,eid:r.EXP_ID||'',tc:r.TEST_CONDITION||'',conc:parseFloat(r.FINAL_CONCENTRATION_WITH_DILUTION)||null,label:r.LABEL||'',vessel:r.VESSEL||'',stdConc:parseFloat(r.CONCENTRATION)||null,calcConc:parseFloat(r.CALCULATED_CONCENTRATION)||null}});
  var samples=all.filter(function(r){return r.conc!==null&&r.key.indexOf('Standard')<0&&r.key.indexOf('spike-in')<0});
  var std={};all.forEach(function(r){var isS=r.key.indexOf('Standard')>=0||r.label.indexOf('Standard')>=0;if(isS&&r.stdConc!=null&&isFinite(r.stdConc)){if(!std[r.eid])std[r.eid]=[];std[r.eid].push([r.stdConc,Math.round(r.meas)])}});
  var spk={};all.forEach(function(r){if(r.key.indexOf('spike-in')>=0&&r.meas>0){if(!spk[r.eid])spk[r.eid]=[];spk[r.eid].push({meas:Math.round(r.meas),dil:r.dil,conc:r.conc,calcConc:r.calcConc})}});
  var samplePts={};samples.forEach(function(r){if(!samplePts[r.eid])samplePts[r.eid]=[];samplePts[r.eid].push(r.meas)});
  var plate={};var eids2={};all.forEach(function(r){eids2[r.eid]=1});
  Object.keys(eids2).sort().forEach(function(e){plate[e]=all.filter(function(r){return r.eid===e}).map(function(r){var iS=r.key.indexOf('Standard')>=0||r.label.indexOf('Standard')>=0;return r.rn+','+r.cn+','+Math.round(r.meas)+(iS?',1':'')}).join(';')});
  var meta={};var sE={};samples.forEach(function(r){sE[r.eid]=1});
  Object.keys(sE).sort().forEach(function(e){var sub=samples.filter(function(r){return r.eid===e});var ops={},lys={},tms={},vols={};sub.forEach(function(r){if(r.op)ops[r.op]=1;if(r.lys)lys[r.lys]=1;if(r.tmpl)tms[r.tmpl]=1;if(r.rv)vols[r.rv]=1});meta[e]={o:Object.keys(ops),l:Object.keys(lys),t:Object.keys(tms),v:Object.keys(vols).map(Number).sort(function(a,b){return a-b}),n:sub.length}});
  return{samples:samples,std:std,spk:spk,samplePts:samplePts,plate:plate,meta:meta}
}
getCSV().then(function(c){
  if(c){window.__CSV=c.csv;window.PARSED=parseCSV(window.__CSV);window.dispatchEvent(new CustomEvent('data-ready'))}
  else{window.location.href='load.html'}
});
</script>
<script type="text/babel">
const{useState,useMemo,useRef,useCallback,useEffect}=React;
function Q(a,q){if(!a||!a.length)return 0;const s=[...a].sort((x,y)=>x-y);const p=(s.length-1)*q;const lo=Math.floor(p),hi=Math.ceil(p);return lo===hi?s[lo]:s[lo]+(p-lo)*(s[hi]-s[lo]);}
function mn(a){return a&&a.length?a.reduce((s,v)=>s+v,0)/a.length:0;}
function stdev(a){if(!a||a.length<2)return 0;const m=mn(a);return Math.sqrt(a.reduce((s,v)=>s+(v-m)**2,0)/a.length);}
function iqrClean(v){if(!v||v.length<4)return v||[];const q1=Q(v,.25),q3=Q(v,.75),r=q3-q1;return v.filter(x=>x>=q1-1.5*r&&x<=q3+1.5*r);}
function fmtN(v){if(!isFinite(v))return"0";return v>=1e3?(v/1e3).toFixed(1)+"k":v.toFixed(0);}
const PAL=["#2563eb","#d97706","#059669","#dc2626","#7c3aed","#db2777","#0891b2","#65a30d","#ea580c","#4f46e5","#a855f7","#14b8a6"];
const CM={Premium:"#2563eb",Economy:"#d97706",Ready96:"#059669",control:"#64748b",neg:"#9ca3af","12-l neg ctrl":"#9ca3af",IB:"#db2777",JC:"#7c3aed",RK:"#0891b2","12-L":"#dc2626","15-L":"#ea580c","17-L":"#2563eb","20-L":"#059669","21-L":"#7c3aed","Arbor lysate":"#db2777",plasmid:"#2563eb",linear:"#d97706","5":"#db2777","10":"#2563eb","20":"#059669"};
const gc=k=>CM[k]||CM[String(k)]||CM[String(parseFloat(k))]||"#6b7280";
const gL=(r,b)=>{if(!r)return"";if(b==="lysate_mm")return(r.lys||"")+"/"+(r.mm||"");if(b==="product")return r.prod||"";if(b==="lysate")return r.lys||"";if(b==="rxn_vol")return(r.rv||0)+"µL";if(b==="template")return r.tmpl||"";if(b==="master_mix")return r.mm||"";if(b==="operator")return r.op||"";if(b==="test_cond")return r.tc||"";if(b==="experiment")return r.eid||"";return r.lys||"";};
const GO=[["product","Product"],["lysate","Lysate"],["operator","Operator"],["template","Template"],["rxn_vol","Rxn Vol"],["test_cond","Test Cond"],["master_mix","Master Mix"],["lysate_mm","Lys/MM"]];
const PO=[...GO,["experiment","Experiment"],["key","Key"],["vessel","Vessel"]];
const PR="ABCDEFGHIJKLMNOP".split("");const PC=Array.from({length:24},(_,i)=>i+1);
const sty={pn:{background:"#fff",borderRadius:5,border:"1px solid #e2e8f0",padding:"8px 10px",overflow:"hidden",boxShadow:"0 1px 3px rgba(0,0,0,.04)"},pt:{fontSize:10.5,fontWeight:600,color:"#0f172a",marginBottom:4,display:"flex",alignItems:"center",gap:5},dt:c=>({display:"inline-block",width:6,height:6,borderRadius:"50%",background:c,flexShrink:0}),sl:{background:"#f8fafc",border:"1px solid #d1d5db",color:"#1e293b",borderRadius:3,padding:"2px 5px",fontSize:10,fontFamily:"inherit",cursor:"pointer",outline:"none"},th:{padding:"4px 5px",borderBottom:"1px solid #e2e8f0",color:"#64748b",textAlign:"left",fontWeight:600,textTransform:"uppercase",letterSpacing:".04em",fontSize:8.5,background:"#fff"},td:{padding:"3px 5px",borderBottom:"1px solid #f1f5f9"},tn:{padding:"3px 5px",borderBottom:"1px solid #f1f5f9",textAlign:"right",fontVariantNumeric:"tabular-nums"},bt:{fontSize:9,color:"#64748b",background:"#f8fafc",border:"1px solid #d1d5db",borderRadius:3,padding:"2px 8px",cursor:"pointer",fontFamily:"inherit"},fb:{background:"#f8fafc",borderRadius:5,border:"1px solid #e2e8f0",padding:"6px 8px",marginBottom:6,display:"flex",flexDirection:"column",gap:3}};
function Tip({x,y,children}){if(!children)return null;return<div style={{position:"fixed",left:Math.min(x+14,window.innerWidth-300),top:y-8,background:"#1e293b",color:"#f1f5f9",padding:"5px 9px",borderRadius:5,fontSize:10.5,pointerEvents:"none",zIndex:999,maxWidth:300,lineHeight:1.4,boxShadow:"0 4px 14px rgba(0,0,0,.35)",border:"1px solid #334155",fontFamily:"inherit",whiteSpace:"pre-line"}}>{children}</div>;}
function Ch({label,options,selected,onChange,colorFn,formatFn}){const a=selected.length===options.length;return<div style={{display:"flex",alignItems:"center",gap:4,flexWrap:"wrap"}}><span style={{fontSize:8.5,color:"#64748b",textTransform:"uppercase",letterSpacing:".05em",width:56,flexShrink:0,textAlign:"right",fontWeight:600}}>{label}</span><button onClick={()=>onChange(a?[options[0]]:options)} style={{fontSize:8,padding:"1px 5px",borderRadius:3,border:"1px solid #d1d5db",cursor:"pointer",fontFamily:"inherit",background:a?"#e2e8f0":"transparent",color:a?"#1e293b":"#94a3b8"}}>ALL</button>{options.map(o=>{const on=selected.includes(o);const c=colorFn?colorFn(o):"#2563eb";return<button key={String(o)} onClick={()=>{const n=on?selected.filter(x=>x!==o):[...selected,o];onChange(n.length?n:[o]);}} style={{fontSize:8.5,padding:"1px 6px",borderRadius:3,cursor:"pointer",fontFamily:"inherit",border:"1px solid "+(on?c+"66":"#d1d5db"),background:on?c+"14":"transparent",color:on?"#1e293b":"#94a3b8"}}>{formatFn?formatFn(o):String(o)}</button>;})}</div>;}
function GS({g,sg,s,ss}){return<div style={{display:"flex",alignItems:"center",gap:5,flexWrap:"wrap"}}><div style={{display:"flex",alignItems:"center",gap:3}}><span style={{fontSize:8,color:"#64748b",fontWeight:600}}>Group:</span><select style={sty.sl} value={g} onChange={e=>sg(e.target.value)}>{GO.map(([k,l])=><option key={k} value={k}>{l}</option>)}</select></div><div style={{display:"flex",alignItems:"center",gap:3}}><span style={{fontSize:8,color:"#64748b",fontWeight:600}}>+Sub:</span><select style={sty.sl} value={s} onChange={e=>ss(e.target.value)}><option value="none">None</option>{GO.filter(([k])=>k!==g).map(([k,l])=><option key={k} value={k}>{l}</option>)}</select></div></div>;}
function Zoomable({children,width,height}){const[sc,setSc]=useState(1);const[tx,setTx]=useState(0);const[ty,setTy]=useState(0);const[drag,setDrag]=useState(false);const[ds,setDs]=useState(null);const ref=useRef(null);const onW=useCallback(e=>{e.preventDefault();setSc(s=>Math.min(8,Math.max(.5,s*(e.deltaY>0?.9:1.1))));},[]);useEffect(()=>{const el=ref.current;if(el)el.addEventListener('wheel',onW,{passive:false});return()=>{if(el)el.removeEventListener('wheel',onW)};},[onW]);return<div ref={ref} className="zoom-wrap" style={{width:width||"100%",height:height||"auto"}} onMouseDown={e=>{if(e.button===0){setDrag(true);setDs({x:e.clientX-tx,y:e.clientY-ty})}}} onMouseMove={e=>{if(drag&&ds){setTx(e.clientX-ds.x);setTy(e.clientY-ds.y)}}} onMouseUp={()=>{setDrag(false);setDs(null)}} onMouseLeave={()=>{setDrag(false);setDs(null)}} onDoubleClick={()=>{setSc(1);setTx(0);setTy(0)}}><div style={{transform:"translate("+tx+"px,"+ty+"px) scale("+sc+")",transformOrigin:"0 0",transition:drag?"none":"transform 0.1s"}}>{children}</div>{sc!==1&&<span className="zoom-hint">{Math.round(sc*100)+"% dblclick reset"}</span>}</div>;}
// Shared filter + header wrapper
function PageWrap({data,activePage,children}){
  const{samples}=data;
  const eids=useMemo(()=>{const s={};samples.forEach(r=>{s[r.eid]=1});return Object.keys(s).sort();},[samples]);
  const allLys=useMemo(()=>{const s={};samples.forEach(r=>{if(r.lys)s[r.lys]=1});return Object.keys(s).sort();},[samples]);
  const allMM=useMemo(()=>{const s={};samples.forEach(r=>{if(r.mm)s[r.mm]=1});return Object.keys(s).sort();},[samples]);
  const allProd=useMemo(()=>{const s={};samples.forEach(r=>{if(r.prod)s[r.prod]=1});return Object.keys(s).sort();},[samples]);
  const allTmpl=useMemo(()=>{const s={};samples.forEach(r=>{if(r.tmpl)s[r.tmpl]=1});return Object.keys(s).sort();},[samples]);
  const allOp=useMemo(()=>{const s={};samples.forEach(r=>{if(r.op)s[r.op]=1});return Object.keys(s).sort();},[samples]);
  const allRV=useMemo(()=>{const s={};samples.forEach(r=>{if(r.rv)s[r.rv]=1});return Object.keys(s).map(Number).sort((a,b)=>a-b);},[samples]);
  const allTC=useMemo(()=>{const s={};samples.forEach(r=>{if(r.tc)s[r.tc]=1});return Object.keys(s).sort();},[samples]);
  const[fE,sfE]=useState(eids);const[fL,sfL]=useState(allLys);const[fM,sfM]=useState(allMM);
  const[fP,sfP]=useState(()=>allProd.filter(p=>p!=="neg"&&p!=="12-l neg ctrl"));
  const[fT,sfT]=useState(allTmpl);const[fO,sfO]=useState(allOp);const[fR,sfR]=useState(allRV);const[fC,sfC]=useState(allTC);
  const[shF,sShF]=useState(true);
  const fd=useMemo(()=>samples.filter(r=>fE.indexOf(r.eid)>=0&&fL.indexOf(r.lys)>=0&&fM.indexOf(r.mm)>=0&&fP.indexOf(r.prod)>=0&&fT.indexOf(r.tmpl)>=0&&fO.indexOf(r.op)>=0&&fR.indexOf(r.rv)>=0&&(r.tc===""||fC.indexOf(r.tc)>=0)),[samples,fE,fL,fM,fP,fT,fO,fR,fC]);
  const cl=useMemo(()=>iqrClean(fd.map(r=>r.conc)),[fd]);
  const kp={n:fd.length,m:cl.length?mn(cl):0,md:cl.length?Q(cl,.5):0,cv:cl.length&&mn(cl)?stdev(cl)/mn(cl)*100:0,ex:(()=>{const s={};fd.forEach(r=>{s[r.eid]=1});return Object.keys(s).length;})(),o:fd.length-cl.length};
  const pages=[{k:"load",l:"📂 Load Data",href:"load.html"},{k:"index",l:"📊 Overview",href:"dashboard.html"},{k:"curves",l:"🔬 Curves & Lots",href:"curves.html"},{k:"experiment",l:"🧪 Experiment",href:"experiment.html"},{k:"raw",l:"📋 Raw Data",href:"raw.html"},{k:"repro",l:"🔄 Reproducibility",href:"repro.html"}];
  return<div style={{fontFamily:"'IBM Plex Mono','SF Mono',monospace",background:"#fff",color:"#1e293b",minHeight:"100vh",padding:"10px 14px",fontSize:11}}>
    <div style={{display:"flex",alignItems:"flex-end",justifyContent:"space-between",borderBottom:"1px solid #e2e8f0",paddingBottom:6}}><div><div style={{fontSize:15,fontWeight:700,color:"#0f172a"}}>CFPS Dashboard</div><div style={{fontSize:10,color:"#64748b"}}>Cell-Free Protein Synthesis · Multi-experiment</div></div><div style={{display:"flex",gap:6}}><span style={{fontSize:9,color:"#059669",background:"#f8fafc",padding:"2px 7px",borderRadius:8,border:"1px solid #05966933"}}>{fd.length+"/"+samples.length}</span><span style={{fontSize:9,color:"#d97706",background:"#f8fafc",padding:"2px 7px",borderRadius:8,border:"1px solid #d9770633"}}>{kp.ex+" exp"}</span></div></div>
    <div className="nav">{pages.map(p=><a key={p.k} href={p.href} className={activePage===p.k?"active":""}>{p.l}</a>)}</div>
    <div style={{marginBottom:6}}><button onClick={()=>sShF(!shF)} style={{...sty.bt,marginBottom:4}}>{(shF?"▾":"▸")+" Filters ("+fd.length+")"}</button>{shF&&<div style={sty.fb}><Ch label="Exp ID" options={eids} selected={fE} onChange={sfE}/><Ch label="Template" options={allTmpl} selected={fT} onChange={sfT} colorFn={gc}/><Ch label="Rxn Vol" options={allRV} selected={fR} onChange={sfR} colorFn={v=>gc(String(v))} formatFn={v=>v+"µL"}/><Ch label="Lysate" options={allLys} selected={fL} onChange={sfL} colorFn={gc}/><Ch label="Master Mix" options={allMM} selected={fM} onChange={sfM}/><Ch label="Product" options={allProd} selected={fP} onChange={sfP} colorFn={gc}/><Ch label="Operator" options={allOp} selected={fO} onChange={sfO} colorFn={gc}/><Ch label="Test Cond" options={allTC} selected={fC} onChange={sfC}/></div>}</div>
    <div style={{display:"grid",gridTemplateColumns:"repeat(6,1fr)",gap:5,marginBottom:6}}>{[["#2563eb",kp.n,"Filtered"],["#059669",isFinite(kp.m)?kp.m.toFixed(0):"0","Mean mg/L"],["#d97706",isFinite(kp.md)?kp.md.toFixed(0):"0","Median"],["#7c3aed",isFinite(kp.cv)?kp.cv.toFixed(1)+"%":"0%","CV%"],["#0891b2",kp.ex,"Experiments"],["#dc2626",kp.o,"Outliers"]].map((a,i)=><div key={i} style={{background:"#f8fafc",borderRadius:5,padding:"5px 8px",borderLeft:"3px solid "+a[0],border:"1px solid #e2e8f0",borderLeftColor:a[0]}}><div style={{fontSize:17,fontWeight:700,color:"#0f172a",lineHeight:1.2}}>{a[1]}</div><div style={{fontSize:8,color:"#64748b",textTransform:"uppercase",letterSpacing:".05em",marginTop:1}}>{a[2]}</div></div>)}</div>
    {children({fd,data})}
  </div>;
}
function AppWrap({activePage,renderContent}){
  const[data,setData]=useState(null);
  useEffect(()=>{function h(){if(window.PARSED)setData(window.PARSED);}window.addEventListener('data-ready',h);if(window.PARSED)setData(window.PARSED);return()=>window.removeEventListener('data-ready',h);},[]);
  if(!data)return<div style={{padding:40,textAlign:"center",color:"#94a3b8"}}>Waiting for data...</div>;
  return<PageWrap data={data} activePage={activePage}>{({fd,data:d})=>renderContent({fd,data:d})}</PageWrap>;
}

// ── Trend chart: tracks a component across experiments with group/subgroup ──
function TrendChart({data,defaultGroup,title,color,tipRef}){
  const[tip,setTip]=tipRef;
  const[gBy,setGBy]=useState(defaultGroup||"lysate");
  const[sgBy,setSgBy]=useState("none");

  const groups=useMemo(()=>{
    const g={};
    data.forEach(r=>{
      const p=gL(r,gBy),s2=sgBy&&sgBy!=="none"?gL(r,sgBy):null;
      const label=s2?p+" · "+s2:p;
      if(!label)return;
      if(!g[label])g[label]={};
      if(!g[label][r.eid])g[label][r.eid]=[];
      g[label][r.eid].push(r.conc);
    });
    return g;
  },[data,gBy,sgBy]);
  const keys=useMemo(()=>Object.keys(groups).sort(),[groups]);
  const exps=useMemo(()=>{const s={};data.forEach(r=>{s[r.eid]=1});return Object.keys(s).sort();},[data]);
  const colors=useMemo(()=>{const c={};keys.forEach((k,i)=>c[k]=PAL[i%PAL.length]);return c;},[keys]);

  const stats=useMemo(()=>{
    const s={};keys.forEach(k=>{s[k]={};exps.forEach(e=>{const v=groups[k]&&groups[k][e];if(v&&v.length){const c=iqrClean(v);s[k][e]={m:mn(c),s:c.length>1?stdev(c):0,n:v.length};}});});return s;
  },[groups,keys,exps]);

  const W=680,H=210,pad={t:14,r:14,b:36,l:54},iw=W-pad.l-pad.r,ih=H-pad.t-pad.b;
  const maxV=useMemo(()=>{let m=100;keys.forEach(k=>exps.forEach(e=>{const d=stats[k][e];if(d)m=Math.max(m,d.m+d.s);}));return m;},[stats,keys,exps]);
  const yS=useMemo(()=>d3.scaleLinear().domain([0,maxV*1.12]).range([ih,0]),[maxV,ih]);
  const xS=useMemo(()=>d3.scaleBand().domain(exps).range([0,iw]).padding(.15),[exps,iw]);

  // Summary table
  const summary=useMemo(()=>keys.map(k=>{
    const allVals=exps.flatMap(e=>(groups[k]&&groups[k][e])||[]);
    const c=iqrClean(allVals);const m=c.length?mn(c):0;const s=c.length>1?stdev(c):0;
    const expCount=exps.filter(e=>stats[k][e]).length;
    const expWithData=exps.filter(e=>stats[k][e]);
    let trend=0;
    if(expWithData.length>=2){const first=stats[k][expWithData[0]].m;const last=stats[k][expWithData[expWithData.length-1]].m;trend=first>0?(last-first)/first*100:0;}
    return{k,n:allVals.length,nc:c.length,m,s,cv:m>0?s/m*100:0,exps:expCount,trend};
  }).sort((a,b)=>b.m-a.m),[keys,exps,groups,stats]);

  return<div>
    <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:4,flexWrap:"wrap",gap:4}}>
      <div style={sty.pt}><span style={sty.dt(color||"#2563eb")}/> {title}</div>
      <GS g={gBy} sg={setGBy} s={sgBy} ss={setSgBy}/>
    </div>
    <div style={{display:"grid",gridTemplateColumns:"1.3fr 0.7fr",gap:8}}>
      <Zoomable width={W} height={H}><svg width={W} height={H} style={{display:"block"}}><g transform={"translate("+pad.l+","+pad.t+")"}>
        {yS.ticks(5).map(t=><g key={t}><line x1={0} x2={iw} y1={yS(t)} y2={yS(t)} stroke="#e2e8f0"/><text x={-6} y={yS(t)} dy={3} textAnchor="end" fill="#64748b" fontSize={8}>{fmtN(t)}</text></g>)}
        <text transform={"translate(-42,"+ih/2+") rotate(-90)"} textAnchor="middle" fill="#64748b" fontSize={8.5}>mg/L</text>
        {/* Connecting lines */}
        {keys.map(k=>{const pts=exps.filter(e=>stats[k][e]).map(e=>({x:xS(e)+xS.bandwidth()/2,y:yS(stats[k][e].m)}));
          if(pts.length<2)return null;
          return<polyline key={"l"+k} points={pts.map(p=>p.x+","+p.y).join(" ")} fill="none" stroke={colors[k]} strokeWidth={1.5} strokeDasharray="4,4" strokeOpacity={.4}/>;
        })}
        {/* Points + error bars */}
        {exps.map(e=>{const bw=xS.bandwidth();const items=keys.filter(k=>stats[k][e]);const sb=bw/Math.max(items.length,1);
          return<g key={e}>{items.map((k,ki)=>{const d=stats[k][e];const cx=xS(e)+sb*ki+sb/2;const c=colors[k];
            return<g key={k}>
              <line x1={cx} x2={cx} y1={yS(d.m+d.s)} y2={yS(Math.max(0,d.m-d.s))} stroke={c} strokeWidth={1.5} strokeOpacity={.4}/>
              <circle cx={cx} cy={yS(d.m)} r={5} fill={c} stroke="#fff" strokeWidth={1.5}
                onMouseMove={ev=>setTip({x:ev.clientX,y:ev.clientY,c:e+" — "+k+"\nMean: "+d.m.toFixed(0)+"±"+d.s.toFixed(0)+" mg/L\nn="+d.n})}
                onMouseLeave={()=>setTip(null)} style={{cursor:"pointer"}}/>
            </g>})}<text x={xS(e)+bw/2} y={ih+14} textAnchor="middle" fill="#475569" fontSize={8.5}>{e}</text></g>;
        })}
      </g></svg></Zoomable>
      <div style={{overflowY:"auto",maxHeight:H}}>
        <table style={{width:"100%",borderCollapse:"collapse",fontSize:9}}>
          <thead><tr><th style={sty.th}>Group</th><th style={{...sty.th,textAlign:"right"}}>Exps</th><th style={{...sty.th,textAlign:"right"}}>Mean</th><th style={{...sty.th,textAlign:"right"}}>CV%</th><th style={{...sty.th,textAlign:"right"}}>Trend</th></tr></thead>
          <tbody>{summary.map(r=><tr key={r.k}>
            <td style={{...sty.td,display:"flex",alignItems:"center",gap:3}}><span style={sty.dt(colors[r.k])}/><span style={{fontSize:8.5}}>{r.k}</span></td>
            <td style={sty.tn}>{r.exps}</td>
            <td style={sty.tn}>{r.m.toFixed(0)}</td>
            <td style={{...sty.tn,color:r.cv>30?"#dc2626":r.cv>15?"#d97706":"#059669",fontWeight:600}}>{r.cv.toFixed(1)+"%"}</td>
            <td style={{...sty.tn,color:r.trend>10?"#059669":r.trend<-10?"#dc2626":"#64748b",fontWeight:600}}>{r.trend>0?"+":""}{r.trend.toFixed(0)+"%"}</td>
          </tr>)}</tbody>
        </table>
      </div>
    </div>
    <div style={{display:"flex",flexWrap:"wrap",gap:"3px 10px",paddingLeft:54,marginTop:3}}>
      {keys.map(k=><span key={k} style={{display:"flex",alignItems:"center",gap:3,fontSize:8.5,color:"#475569"}}><span style={{width:8,height:8,borderRadius:"50%",background:colors[k],flexShrink:0}}/>{k}</span>)}
    </div>
  </div>;
}

// ── Operator comparison ──
function OperatorComp({data,tipRef}){
  const[tip,setTip]=tipRef;
  const ops=useMemo(()=>{const s={};data.forEach(r=>{if(r.op)s[r.op]=1});return Object.keys(s).sort();},[data]);
  const opComp=useMemo(()=>{
    const g={};data.forEach(r=>{if(!r.op)return;const c=r.lys+"/"+r.mm+"/"+r.rv+"µL/"+r.tmpl;if(!g[c])g[c]={};if(!g[c][r.op])g[c][r.op]=[];g[c][r.op].push(r.conc);});
    return Object.entries(g).filter(([,o])=>Object.keys(o).length>=2).map(([c,o])=>{
      const os={};Object.entries(o).forEach(([op,v])=>{const cl=iqrClean(v);os[op]={m:cl.length?mn(cl):0,s:cl.length>1?stdev(cl):0,n:v.length};});
      return{c,os};
    }).sort((a,b)=>a.c.localeCompare(b.c));
  },[data]);

  if(ops.length<2)return<div style={{...sty.pn,marginTop:8}}><div style={sty.pt}><span style={sty.dt("#db2777")}/>Operator Comparison</div><div style={{color:"#94a3b8",fontSize:10,padding:16,textAlign:"center"}}>Need data from 2+ operators to compare. Try broadening filters.</div></div>;

  return<div style={{...sty.pn,marginTop:8}}>
    <div style={sty.pt}><span style={sty.dt("#db2777")}/>Operator Comparison — Matched Conditions ({opComp.length} pairs)</div>
    {opComp.length===0?<div style={{color:"#94a3b8",fontSize:10,padding:16,textAlign:"center"}}>No matched conditions across operators with current filters.</div>:
    <div style={{overflowX:"auto",maxHeight:280,overflowY:"auto"}}>
      <table style={{width:"100%",borderCollapse:"collapse",fontSize:9.5}}>
        <thead><tr>
          <th style={sty.th}>Condition (Lys/MM/Vol/Tmpl)</th>
          {ops.map(op=><th key={op} style={{...sty.th,textAlign:"right"}}><span style={{display:"inline-flex",alignItems:"center",gap:3}}><span style={sty.dt(gc(op))}/>{op}</span></th>)}
          <th style={{...sty.th,textAlign:"right"}}>Spread</th>
        </tr></thead>
        <tbody>{opComp.map(row=>{
          const ms=[];ops.forEach(op=>{if(row.os[op]&&row.os[op].m>0)ms.push(row.os[op].m);});
          const avg=ms.length?mn(ms):1;const sp=ms.length>1&&avg>0?(Math.max(...ms)-Math.min(...ms))/avg*100:0;
          return<tr key={row.c} onMouseEnter={e=>e.currentTarget.style.background="#f8fafc"} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
            <td style={{...sty.td,fontSize:9,maxWidth:220,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}} title={row.c}>{row.c}</td>
            {ops.map(op=><td key={op} style={sty.tn}>{row.os[op]?row.os[op].m.toFixed(0)+"±"+row.os[op].s.toFixed(0)+" ("+row.os[op].n+")":"—"}</td>)}
            <td style={{...sty.tn,color:sp>30?"#dc2626":sp>15?"#d97706":"#059669",fontWeight:600}}>{sp.toFixed(1)+"%"}</td>
          </tr>;
        })}</tbody>
      </table>
    </div>}
  </div>;
}

// ── Experiment comparison ──
function ExpComparison({data,tipRef}){
  const[tip,setTip]=tipRef;
  const[cA,scA]=useState("");const[cB,scB]=useState("");
  const exps=useMemo(()=>{const s={};data.forEach(r=>{s[r.eid]=1});return Object.keys(s).sort();},[data]);
  const matched=useMemo(()=>{
    if(!cA||!cB)return[];
    const gA={},gB={};
    data.filter(r=>r.eid===cA).forEach(r=>{const k=r.lys+"/"+r.mm+"/"+r.prod+"/"+r.tmpl;if(!gA[k])gA[k]=[];gA[k].push(r.conc);});
    data.filter(r=>r.eid===cB).forEach(r=>{const k=r.lys+"/"+r.mm+"/"+r.prod+"/"+r.tmpl;if(!gB[k])gB[k]=[];gB[k].push(r.conc);});
    return Object.keys(gA).filter(k=>gB[k]).map(k=>{
      const ca=iqrClean(gA[k]),cb=iqrClean(gB[k]);
      const mA=ca.length?mn(ca):0,mB=cb.length?mn(cb):0;
      return{c:k,a:{m:mA,s:ca.length>1?stdev(ca):0,n:gA[k].length},b:{m:mB,s:cb.length>1?stdev(cb):0,n:gB[k].length},d:mA>0?(mB-mA)/mA*100:0};
    }).sort((a,b)=>Math.abs(b.d)-Math.abs(a.d));
  },[cA,cB,data]);

  return<div style={{...sty.pn,marginTop:8}}>
    <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:6,flexWrap:"wrap",gap:4}}>
      <div style={sty.pt}><span style={sty.dt("#0891b2")}/>Experiment-to-Experiment Comparison</div>
      <div style={{display:"flex",gap:8,alignItems:"center"}}>
        <span style={{fontSize:8,color:"#64748b",fontWeight:600}}>A:</span>
        <select style={sty.sl} value={cA} onChange={e=>scA(e.target.value)}><option value="">Select…</option>{exps.map(e=><option key={e} value={e}>{e}</option>)}</select>
        <span style={{color:"#94a3b8",margin:"0 2px"}}>vs</span>
        <span style={{fontSize:8,color:"#64748b",fontWeight:600}}>B:</span>
        <select style={sty.sl} value={cB} onChange={e=>scB(e.target.value)}><option value="">Select…</option>{exps.filter(e=>e!==cA).map(e=><option key={e} value={e}>{e}</option>)}</select>
      </div>
    </div>
    {!cA||!cB?<div style={{color:"#94a3b8",fontSize:10,padding:16,textAlign:"center"}}>Select two experiments above to compare matched conditions.</div>:
     matched.length===0?<div style={{color:"#d97706",fontSize:10,padding:16,textAlign:"center"}}>No overlapping conditions between {cA} and {cB}.</div>:
     <div style={{overflowX:"auto",maxHeight:260,overflowY:"auto"}}>
       <table style={{width:"100%",borderCollapse:"collapse",fontSize:9.5}}>
         <thead><tr><th style={sty.th}>Condition (Lys/MM/Prod/Tmpl)</th><th style={{...sty.th,textAlign:"right"}}>{cA}</th><th style={{...sty.th,textAlign:"right"}}>{cB}</th><th style={{...sty.th,textAlign:"right"}}>Δ%</th></tr></thead>
         <tbody>{matched.map(m=><tr key={m.c} onMouseEnter={e=>e.currentTarget.style.background="#f8fafc"} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
           <td style={{...sty.td,fontSize:9}}>{m.c}</td>
           <td style={sty.tn}>{m.a.m.toFixed(0)+"±"+m.a.s.toFixed(0)+" ("+m.a.n+")"}</td>
           <td style={sty.tn}>{m.b.m.toFixed(0)+"±"+m.b.s.toFixed(0)+" ("+m.b.n+")"}</td>
           <td style={{...sty.tn,color:m.d>10?"#059669":m.d<-10?"#dc2626":"#64748b",fontWeight:600}}>{(m.d>0?"+":"")+m.d.toFixed(1)+"%"}</td>
         </tr>)}</tbody>
       </table>
       <div style={{fontSize:9,color:"#64748b",marginTop:4}}>Δ = (B−A)/A × 100%. Sorted by largest absolute change.</div>
     </div>}
  </div>;
}

// ── Main page content (receives filtered data from AppWrap/PageWrap) ──
function ReproContent({fd, data}){
  const tipState=useState(null);
  const[tip]=tipState;

  return<div>
    {tip&&<Tip x={tip.x} y={tip.y}>{tip.c}</Tip>}

    {/* Lysate tracking */}
    <div style={sty.pn}>
      <TrendChart data={fd} defaultGroup="lysate" title="Lysate Performance Across Experiments" color="#dc2626" tipRef={tipState}/>
    </div>

    {/* Master Mix tracking */}
    <div style={{...sty.pn,marginTop:8}}>
      <TrendChart data={fd} defaultGroup="master_mix" title="Master Mix Performance Across Experiments" color="#d97706" tipRef={tipState}/>
    </div>

    {/* Product tracking */}
    <div style={{...sty.pn,marginTop:8}}>
      <TrendChart data={fd} defaultGroup="product" title="Product Type Consistency Across Experiments" color="#059669" tipRef={tipState}/>
    </div>

    {/* Operator comparison */}
    <OperatorComp data={fd} tipRef={tipState}/>

    {/* Experiment comparison */}
    <ExpComparison data={fd} tipRef={tipState}/>
  </div>;
}

ReactDOM.render(<AppWrap activePage="repro" renderContent={({fd,data})=><ReproContent fd={fd} data={data}/>}/>,document.getElementById("app"));
</script></body></html>
