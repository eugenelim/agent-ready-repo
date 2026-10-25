!function(){
'use strict';
// ── Colour theme: Auto follows the system; Light and Dark override it. ──────
var THEME_KEY='decision-nav-theme';
var darkMq=window.matchMedia?window.matchMedia('(prefers-color-scheme: dark)'):null;
function storedTheme(){
try{var v=localStorage.getItem(THEME_KEY);return v==='light'||v==='dark'?v:'auto';}
catch(se){return 'auto';}}
function applyTheme(choice){
var dark=choice==='dark'||(choice==='auto'&&!!(darkMq&&darkMq.matches));
document.documentElement.setAttribute('data-theme',dark?'dark':'light');
document.querySelectorAll('[data-theme-choice]').forEach(function(b){
b.setAttribute('aria-pressed',b.getAttribute('data-theme-choice')===choice?'true':'false');});}
var themeChoice=storedTheme();
applyTheme(themeChoice);
if(darkMq&&darkMq.addEventListener)darkMq.addEventListener('change',function(){
if(themeChoice==='auto')applyTheme('auto');});
document.querySelectorAll('[data-theme-choice]').forEach(function(b){
b.addEventListener('click',function(){
themeChoice=b.getAttribute('data-theme-choice');
try{if(themeChoice==='auto')localStorage.removeItem(THEME_KEY);
else localStorage.setItem(THEME_KEY,themeChoice);}catch(se){}
applyTheme(themeChoice);});});
var dataEl=document.getElementById('nav-data');
var D;
try{D=JSON.parse(dataEl?dataEl.textContent:'');}
catch(e){
var main=document.getElementById('app-main')||document.body;
main.textContent='';
var ep=document.createElement('div');ep.className='error-panel';ep.setAttribute('role','alert');
ep.textContent='This export is damaged: its embedded data could not be read ('+String(e)+
'). Run the export again to get a fresh copy.';
main.appendChild(ep);
return;}
var records=D.records||[],rels=D.relationships||[],mode=D.mode||'full';
var srcLinks=D.source_links||{};
// Visible escaping for paths and caller text shown beside trust labels.
var V=window.visEscape||function(x){return String(x);};
// The header Status row repeats the lifecycle row only when both show the same
// value; otherwise (another label form, a wrapped value) it stays visible.
// A one-line Status field whose value, one trailing comment removed, equals
// the lifecycle value adds nothing; a wrapped one always shows. String searches
// only, so a huge hostile value costs linear time.
function stripTrailingComment(v){
var s=v.trimEnd();
if(s.slice(-3)!=='-->')return s;
var end=s.length-3,k=s.lastIndexOf('-->',end-3),lo=k<0?0:Math.max(0,k-3);
for(;;){var st=s.indexOf('<!--',lo);
if(st<0||st+4>end)return s;
if(s.slice(st+4,end).indexOf('-->')<0)return s.slice(0,st).trimEnd();
lo=st+1;}}
function statusShownAs(hf,rec){
var lv=rec.lifecycle&&!rec.lifecycle.missing?rec.lifecycle.raw_value:null;
if(lv===null||hf.raw_value.indexOf('\n')>=0)return false;
return stripTrailingComment(hf.raw_value).trim()===lv;}
// A record ID from the URL is untrusted: escape it and cap its length.
function shownId(x){var t=V(String(x));return t.length>64?t.slice(0,63)+'…':t;}
function claimText(u){
if(typeof u==='string')return V(u);
return u?(u.display_value||V(u.raw_value||u.by||'')):'';}
var state={view:'list',sel:null,kind:'',status:'',q:''};
var VALID_VIEWS=['list','graph','context','detail'];
var statusMap={};
records.forEach(function(r){
var l=r.lifecycle;if(!l||l.missing)return;
var rv=l.raw_value;
if(rv!=null&&!(rv in statusMap))statusMap[rv]=l.display_value||rv;});
var searchEl=document.getElementById('search-input');
var kindEl=document.getElementById('kind-filter');
var statusEl=document.getElementById('status-filter');
var liveEl=document.getElementById('live-region');
Object.keys(statusMap).sort().forEach(function(rv){
var o=document.createElement('option');
o.value=rv;o.textContent=statusMap[rv]||rv;statusEl.appendChild(o);});
// ── Helpers ──────────────────────────────────────────────────────────────────
function lc(r){
var l=r.lifecycle;if(!l||l.missing)return'(missing)';
return l.display_value||l.raw_value||'(missing)';}
function el(tag,cls,txt){
var e=document.createElement(tag);
if(cls)e.className=cls;if(txt!=null)e.textContent=txt;return e;}
function attr(e,k,v){if(v!=null)e.setAttribute(k,v);return e;}
function btn(cls,txt,handler){
var b=el('button',cls,txt);b.addEventListener('click',handler);return b;}
function updateLive(msg){if(liveEl)liveEl.textContent=msg;}
// Map lifecycle raw_value to a status CSS class
function statusClass(rv){
if(!rv)return'status-default';
var v=rv.toLowerCase();
if(v.indexOf('accepted')>=0||v.indexOf('active')>=0)return'status-accepted';
if(v.indexOf('proposed')>=0||v.indexOf('draft')>=0||v.indexOf('open')>=0)return'status-proposed';
if(v.indexOf('superseded')>=0)return'status-superseded';
if(v.indexOf('deprecated')>=0||v.indexOf('rejected')>=0||v.indexOf('withdrawn')>=0)return'status-deprecated';
return'status-default';}
// ── Stat cards ───────────────────────────────────────────────────────────────
function renderStatCards(){
var sc=document.getElementById('stat-cards');if(!sc)return;
sc.textContent='';
var bk=(D.summary&&D.summary.by_kind)||{};
var unresCnt=(D.summary&&D.summary.unresolved_reference_count)||0;
var supCnt=records.filter(function(r){return r.superseded_by&&r.superseded_by.length>0;}).length;
var stats=[
  {n:records.length,l:'total'},
  {n:bk.ADR||0,l:'ADRs'},
  {n:bk.RFC||0,l:'RFCs'},
  {n:supCnt,l:'superseded'},
  {n:unresCnt,l:'unresolved'}];
stats.forEach(function(s){
var card=document.createElement('div');card.className='stat-card';
var num=document.createElement('div');num.className='stat-num';
num.textContent=String(s.n);
var lbl=document.createElement('div');lbl.className='stat-label';
lbl.textContent=s.l;
card.appendChild(num);card.appendChild(lbl);sc.appendChild(card);});}
// ── Kind pill helper ─────────────────────────────────────────────────────────
function setKindPill(kind){
if(!kindEl)return;
kindEl.querySelectorAll('button.kind-pill').forEach(function(b){
var bk=b.getAttribute('data-kind')||'';
if(bk===kind){b.classList.add('active');}
else{b.classList.remove('active');}
b.setAttribute('aria-pressed',bk===kind?'true':'false');});}
// ── Routing ──────────────────────────────────────────────────────────────────
function parseHash(){
try{
var h=location.hash.slice(1);
if(!h){state.view='list';state.sel=null;return;}
var i=h.indexOf('/');
var v=i<0?h:h.slice(0,i);
if(VALID_VIEWS.indexOf(v)<0){state.view='list';state.sel=null;return;}
state.view=v;state.sel=null;
if(i>=0){try{state.sel=decodeURIComponent(h.slice(i+1));}
catch(ue){state.sel=null;}}
}catch(ex){state.view='list';state.sel=null;}}
function pushState(){
var h='#'+state.view+(state.sel?'/'+encodeURIComponent(state.sel):'');
if(location.hash!==h)history.pushState(null,'',h);}
function filtered(){return records.filter(function(r){
if(state.kind&&r.kind!==state.kind)return false;
if(state.status&&(r.lifecycle.missing||
r.lifecycle.raw_value!==state.status))return false;
if(state.q){var q=state.q.toLowerCase();
var qm=/^(adr|rfc)?[-\s]*0*(\d{1,4})$/i.exec(state.q.trim());
var kp=qm&&qm[1]?qm[1].toUpperCase():null;
var ord=qm?parseInt(qm[2],10):NaN;
var rord=parseInt((r.id.split('-')[1])||'',10);
if(r.id.toLowerCase().indexOf(q)<0&&
r.title.toLowerCase().indexOf(q)<0&&
lc(r).toLowerCase().indexOf(q)<0&&
!(rord===ord&&(!kp||r.kind===kp)))return false;}
return true;});}
function srcLink(src){var sl=srcLinks[src];if(!sl||!sl.url)return null;return sl;}
function makeLink(src){
var sl=srcLink(src);if(!sl)return null;
var a=el('a',null,sl.label);
attr(a,'href',sl.url);attr(a,'rel','noopener noreferrer');return a;}
function focusViewHeading(){
var c=document.getElementById('view-'+state.view);if(!c)return;
var h=c.querySelector('h2,h1');
if(h){h.setAttribute('tabindex','-1');h.focus({preventScroll:false});}}
function navigate(view,id){
state.view=view;if(id!==undefined)state.sel=id;pushState();render();focusViewHeading();}
function render(){
VALID_VIEWS.forEach(function(v){
var b=document.getElementById('btn-'+v);
if(b){if(state.view===v){b.setAttribute('aria-current','page');}
else{b.removeAttribute('aria-current');}}});
VALID_VIEWS.forEach(function(v){
var d=document.getElementById('view-'+v);
if(d)d.hidden=state.view!==v;});
var c=document.getElementById('view-'+state.view);
if(!c)return;c.textContent='';

if(state.view==='list')renderList(c);
else if(state.view==='graph')renderGraph(c);
else if(state.view==='context')renderContext(c);
else if(state.view==='detail')renderDetail(c);
syncExpandLabel(c);}
// The Expand all button names the action it will take on this view.
function syncExpandLabel(c){
var b=document.getElementById('expand-all-btn');if(!b)return;
var d=c.querySelectorAll('details'),all=d.length>0;
for(var i=0;i<d.length;i++){if(!d[i].open){all=false;break;}}
b.textContent=all?'Collapse all':'Expand all';}
// ── Supersession banner ──────────────────────────────────────────────────────
function supBanner(entry,isDetail){
var div=document.createElement('div');
div.className='supersede-banner';div.setAttribute('role','note');
div.appendChild(document.createTextNode(entry.partial?'Superseded in part by ':'Superseded by '));
var a=document.createElement('a');
a.href='#detail/'+encodeURIComponent(entry.by);a.textContent=entry.by;
div.appendChild(a);
if(entry.partial){
var sc=entry.scope&&entry.scope.length?'('+entry.scope.join(', ')+')':'(scope not stated)';
div.appendChild(document.createTextNode(' '+sc));}
return div;}
// ── List view ────────────────────────────────────────────────────────────────
function renderList(c){
var fr=filtered();
var h2=el('h2',null,'Corpus list');c.appendChild(h2);
if(fr.length===0){
var activeFilters=[];
if(state.q)activeFilters.push('search: "'+state.q+'"');
if(state.kind)activeFilters.push('kind: '+state.kind);
if(state.status)activeFilters.push('status: '+V(state.status));
var msg=records.length===0?
'No canonical ADR or RFC records were admitted. Check the corpus boundary.':
activeFilters.length>0?
'No records match '+activeFilters.join(', ')+'.':
'No records match the active filters.';
c.appendChild(el('p','empty-msg',msg));
if(activeFilters.length>0){
var rb=btn('reset-btn','Reset filters',function(){
state.q='';state.kind='';state.status='';
if(searchEl)searchEl.value='';
setKindPill('');
if(statusEl)statusEl.value='';
render();focusViewHeading();});
c.appendChild(rb);}
updateLive(msg);return;}
var ul=el('ul','record-list');
fr.forEach(function(r){
// Strike-through is reserved for full supersession; a record superseded only
// in part stays in force and gets the lighter "in part" treatment.
var supAll=r.superseded_by||[];
var supCls=supAll.some(function(s){return !s.partial;})?' is-superseded':
supAll.length?' is-superseded-part':'';
var liCls='record-item'+(r.id===state.sel?' selected':'')+supCls;
var li=el('li',liCls);
var b=el('button','record-btn');
if(r.id===state.sel)b.setAttribute('aria-current','true');
var ridEl=el('span','rid',r.id);
var ttEl=el('span','rtitle',r.display_title||r.title);
var badge=el('span','badge badge-'+r.kind.toLowerCase(),r.kind);
var lcv=(r.lifecycle&&!r.lifecycle.missing&&r.lifecycle.raw_value)||null;
var stEl=el('span','rstatus '+statusClass(lcv),lc(r));
var chev=el('span','chevron','▼');
b.appendChild(ridEl);b.appendChild(ttEl);b.appendChild(badge);b.appendChild(stEl);b.appendChild(chev);
// Supersession banners from checked relationships only
var supBy=r.superseded_by||[];
var unresClaims=r.unresolved_claims||[];
b.addEventListener('click',function(){navigate('detail',r.id);});
li.appendChild(b);
if(supBy.length>0){
supBy.forEach(function(s){li.appendChild(supBanner(s,false));});}
else if(unresClaims.length>0){
var sb2=document.createElement('div');sb2.className='supersede-banner is-unresolved';sb2.setAttribute('role','note');
sb2.appendChild(document.createTextNode('Unresolved supersession claim: '+claimText(unresClaims[0])));
li.appendChild(sb2);}
ul.appendChild(li);});
c.appendChild(ul);
updateLive(fr.length+' of '+records.length+' records shown.');}
// ── Graph view ───────────────────────────────────────────────────────────────
function renderGraph(c){
var h2=el('h2',null,'Lifecycle graph');c.appendChild(h2);
if(state.sel){
// Focused view: SVG lineage diagram for the selected record
var back=el('button','atlas-back pill-btn','← All chains');back.type='button';
back.addEventListener('click',function(){navigate('graph',null);});
c.appendChild(back);
Lineage.renderFocused(c,state.sel,rels,records,navigate);
}else{
// Atlas: all checked-supersession chains
c.appendChild(el('p','graph-note',
'Every chain of records joined by checked supersession. Click a node to focus.'));
Lineage.renderAtlas(c,rels,records,navigate);
}
updateLive('');}
// ── Context view ─────────────────────────────────────────────────────────────
function renderContext(c){
var rec=state.sel?records.find(function(r){return r.id===state.sel;}):null;
var h2=el('h2',null,rec?'Guidance context: '+rec.id:'Guidance context');
c.appendChild(h2);
if(!rec){
c.appendChild(el('p','empty-msg',state.sel?
shownId(state.sel)+' is not in this export.':
'Select a record from the corpus list, then switch to this view.'));
updateLive('');return;}
var ctxHead=el('p','ctx-record',(rec.display_title||rec.title)+' · '+lc(rec));
c.appendChild(ctxHead);
(rec.superseded_by||[]).forEach(function(s){c.appendChild(supBanner(s,true));});
var ctx=rels.filter(function(r){
return r.trust_class==='contextual'&&(r.from===rec.id||r.to===rec.id);});
c.appendChild(el('h3',null,
'Contextual references — Related field (weaker than checked lineage)'));
if(ctx.length===0){
c.appendChild(el('p','empty-msg','No contextual references for this record.'));}
else{
var ul=el('ul','ctx-list');
ctx.forEach(function(r){
var peer=r.from===rec.id?r.to:r.from;
var dir=r.from===rec.id?'refers to':'referred to by';
var label=dir+' '+V(peer||'?')+' [contextual · '+r.resolution_state+']';
var li=el('li',null);
var admitted=records.find(function(x){return x.id===peer;});
if(admitted){
var b=btn('ctx-btn',label,function(){navigate('detail',peer);});
li.appendChild(b);}
else{li.textContent=label+' — not admitted';}
ul.appendChild(li);});
c.appendChild(ul);}
var asserts=rels.filter(function(r){
return r.trust_class==='navigation_only'
&&(r.from===rec.id||r.to===rec.id);});
c.appendChild(el('h3',null,'Caller assertions (non-authoritative view input)'));
if(asserts.length===0){
c.appendChild(el('p','empty-msg','No caller assertions embedded for this record.'));}
else{
var ul2=el('ul','assert-list');
asserts.forEach(function(a){
var li=el('li',null);
var tlEl=el('span','trust-label','[navigation_only · caller_asserted]');
li.appendChild(tlEl);
li.appendChild(document.createTextNode(' '));
li.appendChild(document.createTextNode(a.display_raw_value||V(a.raw_value||'')));
if(a.from)li.appendChild(document.createTextNode(' from: '+V(a.from)));
if(a.to)li.appendChild(document.createTextNode(' → '+V(a.to)));
ul2.appendChild(li);});
c.appendChild(ul2);}
updateLive('');}
// ── Detail view ──────────────────────────────────────────────────────────────
function renderDetail(c){
var rec=state.sel?records.find(function(r){return r.id===state.sel;}):null;
var h2=el('h2',null,rec?rec.id+': '+(rec.display_title||rec.title):'Record detail');
h2.className='detail-heading';c.appendChild(h2);
if(!rec){
var p=el('p','empty-msg');
if(state.sel){p.textContent=shownId(state.sel)+' is not in this export.';}
else{p.textContent='Select a record from the corpus list to see its detail.';}
c.appendChild(p);updateLive('');return;}
// Supersession banners from checked relationships only — at top of detail
var supBy=rec.superseded_by||[];
var unresClaims=rec.unresolved_claims||[];
if(supBy.length>0){
supBy.forEach(function(s){c.appendChild(supBanner(s,true));});}
else if(unresClaims.length>0){
unresClaims.forEach(function(u){
var div=document.createElement('div');div.className='supersede-banner';div.setAttribute('role','note');
div.appendChild(document.createTextNode('Unresolved supersession claim: '+claimText(u)));
c.appendChild(div);});}
var tbl=el('table','meta-table');
var metaRows=[['Kind',rec.kind],['Status',lc(rec)],['Source',V(rec.source)]];
// Every header-region field, exactly as recorded (escaped for display).
(Array.isArray(rec.header_fields)?rec.header_fields:[]).forEach(function(hf){
if(hf&&hf.label&&!(hf.label.toLowerCase()==='status'&&statusShownAs(hf,rec)))metaRows.push([V(hf.label),hf.display_value!=null?hf.display_value:V(hf.raw_value||'')]);});
metaRows.forEach(function(row){
var tr=document.createElement('tr');
var th=el('th',null,row[0]);var td=el('td',null,row[1]);
tr.appendChild(th);tr.appendChild(td);tbl.appendChild(tr);});
var slTr=document.createElement('tr');
var slTh=el('th',null,'Source link');var slTd=el('td',null);
var sl=makeLink(rec.source);
if(sl){slTd.appendChild(sl);}
else{slTd.textContent=V(rec.source)+' (remote not on allowlist — inert provenance)';}
slTr.appendChild(slTh);slTr.appendChild(slTd);tbl.appendChild(slTr);
c.appendChild(tbl);
var recRels=rels.filter(function(r){return r.from===rec.id||r.to===rec.id;});
if(recRels.length>0){
var rCnt={checked:0,candidate:0,contextual:0,navigation_only:0};
recRels.forEach(function(r){var tc=r.trust_class;if(tc in rCnt)rCnt[tc]++;});
var rSummary='Relationships — '+rCnt.checked+' checked · '
+rCnt.candidate+' candidate · '+rCnt.contextual+' contextual · '
+rCnt.navigation_only+' navigation-only';
var rDet=el('details','rel-details');
var rSum=el('summary',null,rSummary);rDet.appendChild(rSum);
var ul=el('ul','rel-list');
recRels.forEach(function(r){
var li=el('li','rel-item rel-'+r.trust_class.replace(/_/g,'-'));
var tlEl=el('span','trust-label','['+r.trust_class+' · '+r.resolution_state+']');
li.appendChild(tlEl);
var scope=r.scope&&r.scope.length?r.scope.join(', '):'';
if(r.relation==='supersedes_in_part'&&!(r.scope&&r.scope.length))
scope='scope not stated';
li.appendChild(document.createTextNode(' '+r.relation+': '+V(r.from||'?')+' → '
+(r.to?V(r.to):'(unparseable)')+(scope?' ('+scope+')':'')));
li.appendChild(el('span','trust-source',' · source: '+(r.source?V(r.source):'caller')));
li.appendChild(document.createTextNode(' · '));
li.appendChild(document.createTextNode(r.display_raw_value||''));
ul.appendChild(li);});
rDet.appendChild(ul);c.appendChild(rDet);}
var supRefs=rec.support_refs||[];
if(supRefs.length>0){
var srDet=el('details','sr-details');
var srSum=el('summary',null,'Support references ('+supRefs.length+')');
srDet.appendChild(srSum);
var srUl=el('ul',null);
supRefs.forEach(function(sr){
var li=el('li',null);
li.appendChild(document.createTextNode(V(sr.path)+' ['+sr.kind+']'));
srUl.appendChild(li);});
srDet.appendChild(srUl);c.appendChild(srDet);}
c.appendChild(el('h3',null,'Record body'+(mode==='bounded'?' (omitted in bounded mode)':'')));
var body=rec.body;
if(!body){c.appendChild(el('p','empty-msg','Body not available.'));}
else if(!body.available){
var reason=body.omission_reason||'not_available';
var notice=el('p','bounded-notice');
if(reason==='bounded_mode'||reason==='not_requested'){
notice.textContent='Body omitted in bounded mode. ';
if(body.source_action){
var lnk=makeLink(body.source_action.path);
if(lnk){notice.appendChild(lnk);}
else{notice.appendChild(document.createTextNode(V(body.source_action.path)));}}}
else if(reason==='body_too_large'){
notice.textContent='Body too large to embed. Source: '+V(rec.source);}
else{notice.textContent='Body not included. Reason: '+reason;}
c.appendChild(notice);}
else{
var FOLD_THRESHOLD=3000;
var content=body.content||'';
var bodyEl;
if(content.length>FOLD_THRESHOLD){
var bd=el('details','body-details');bd.open=true;
var bs=el('summary',null,'Record content ('+content.length+' chars)');
bd.appendChild(bs);
var sec=document.createElement('section');
sec.setAttribute('aria-label','Record content');
sec.className='record-content';
renderMarkdown(content,sec);
bd.appendChild(sec);bodyEl=bd;}
else{
var sec2=document.createElement('section');
sec2.setAttribute('aria-label','Record content');
sec2.className='record-content';
renderMarkdown(content,sec2);
bodyEl=sec2;}
c.appendChild(bodyEl);}
updateLive(rec.id+': '+(rec.display_title||rec.title));}
// ── Event bindings ───────────────────────────────────────────────────────────
VALID_VIEWS.forEach(function(v){
var b=document.getElementById('btn-'+v);
if(b)b.addEventListener('click',function(){navigate(v,state.sel);});});
if(searchEl)searchEl.addEventListener('input',function(){
state.q=this.value;render();});
// Kind filter: pill buttons (not a select)
if(kindEl){
kindEl.querySelectorAll('button.kind-pill').forEach(function(b){
b.addEventListener('click',function(){
state.kind=b.getAttribute('data-kind')||'';
setKindPill(state.kind);
render();});});}
if(statusEl)statusEl.addEventListener('change',function(){
state.status=this.value;render();});
// Expand-all pill: toggles all <details> in the current view
var expandAllBtn=document.getElementById('expand-all-btn');
if(expandAllBtn){
expandAllBtn.addEventListener('click',function(){
var viewEl=document.getElementById('view-'+state.view);if(!viewEl)return;
var dets=viewEl.querySelectorAll('details');
if(!dets.length)return; // nothing to expand on this view; keep the label
var allOpen=true;
for(var di=0;di<dets.length;di++){if(!dets[di].open){allOpen=false;break;}}
for(var dj=0;dj<dets.length;dj++){dets[dj].open=!allOpen;}
expandAllBtn.textContent=allOpen?'Expand all':'Collapse all';});}
var mainEl=document.getElementById('app-main');
if(mainEl)mainEl.addEventListener('toggle',function(){
var cv=document.getElementById('view-'+state.view);if(cv)syncExpandLabel(cv);},true);
window.addEventListener('popstate',function(){parseHash();render();focusViewHeading();});
var provPre=document.getElementById('prov-pre');
if(provPre)provPre.textContent=JSON.stringify(D.provenance||{},null,2);
var supInvEl=document.getElementById('sup-inv');
if(supInvEl&&D.corpus_support_refs){
var siUl=el('ul',null);
var csr=D.corpus_support_refs;
if(csr.length===0){siUl.appendChild(el('li',null,'None found.'));}
else{csr.forEach(function(sr){
var li=el('li',null);
li.appendChild(document.createTextNode(V(sr.path)+' ['+sr.kind+']'));
siUl.appendChild(li);});}
supInvEl.appendChild(siUl);}
// ── Boot ─────────────────────────────────────────────────────────────────────
renderStatCards();
parseHash();render();
}();
