!function(){
'use strict';
var dataEl=document.getElementById('nav-data');
var D;
try{D=JSON.parse(dataEl?dataEl.textContent:'');}
catch(e){
var main=document.getElementById('app-main')||document.body;
main.textContent='';
var ep=document.createElement('div');ep.className='error-panel';ep.setAttribute('role','alert');
ep.textContent='This export is damaged: its embedded data could not be read ('+String(e)+
'). Run the export again to get a fresh copy.';
var qn=document.getElementById('questions-nav');if(qn)qn.hidden=true;
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
// picked: a record was chosen, so below 40rem the detail zone replaces the list zone.
var state={view:'recent',sel:null,picked:false,kind:'',status:'',q:''};
// A literal array checked by indexOf, so a key such as "constructor" is never a view.
// The first six are the rail's questions; context is reached from a record's detail.
var VALID_VIEWS=['recent','deciding','replaced','graph','areas','list','context'];
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
// Lifecycle mark: the first run of letters in the raw value picks one of four marks.
var MARK_OF={accepted:'approved',experimental:'active',proposed:'draft',draft:'draft',
open:'draft',final:'draft',superseded:'done',deprecated:'done',rejected:'done',withdrawn:'done'};
var MARK_GLYPH={active:'●',approved:'◆',draft:'◇',done:'✓'};
function markName(rec){
var l=rec.lifecycle;if(!l||l.missing)return'draft';
var w=/[A-Za-z]+/.exec(l.raw_value||'');
// Only the map's own names count; an inherited one such as "constructor" is a draft.
var k=w?w[0].toLowerCase():'';
return Object.prototype.hasOwnProperty.call(MARK_OF,k)?MARK_OF[k]:'draft';}
function markEl(rec){
var l=rec.lifecycle,m=markName(rec);
var e=el('span','mark');e.setAttribute('data-mark',m);
var g=el('span','mark-g',MARK_GLYPH[m]);g.setAttribute('aria-hidden','true');
e.appendChild(g);
e.appendChild(document.createTextNode(!l||l.missing?'No status':(l.display_value||l.raw_value||'No status')));
return e;}
// ── Questions ────────────────────────────────────────────────────────────────
// One table holds each question's words, so a label lives once. A lookup walks the array.
var QUESTIONS=[
{key:'recent',label:'Recently decided',name:'What was decided most recently?',
heading:'Decided records',sort:'Newest decision first (ADR Date, RFC Date closed)',
empty:'No record has a decided status: Accepted, Superseded, Deprecated, Rejected or Withdrawn.'},
{key:'deciding',label:'Still being decided',name:'What is still being decided?',
heading:'Records still open',sort:'Oldest first (ADR Date, RFC Date opened)',
empty:'Nothing is being decided: no record has a Draft, Proposed, Open, Final Comment Period or Experimental status.'},
{key:'replaced',label:'Replaced',name:'Which decisions were replaced?',
heading:'Replaced records',sort:'Replaced in full first, then in part; by id within each',
empty:'No record is replaced in full or in part.'},
{key:'graph',label:'Lineage',name:'How did decisions replace each other?',
heading:'Lifecycle graph',sort:'Largest chain first, then by lowest record number',empty:''},
{key:'areas',label:'By area',name:'What does each area hold?',
heading:'Records by area',sort:'Areas A to Z; newest decision first within each',
empty:'No record has an Areas field.'},
{key:'list',label:'Browse all',name:'Browse every record',
heading:'All records',sort:'By kind, then number',
empty:'No canonical ADR or RFC records were admitted. Check the corpus boundary.'}];
var RAIL_GROUPS=[
{key:'decisions',label:'Decisions',questions:['recent','deciding']},
{key:'changes',label:'Changes',questions:['replaced','graph']},
{key:'browse',label:'Browse',questions:['areas','list']}];
function question(key){
for(var i=0;i<QUESTIONS.length;i++){if(QUESTIONS[i].key===key)return QUESTIONS[i];}
return null;}
// Membership words: own keys only, so a lifecycle word such as "constructor" is plain data.
function wordSet(words){
var m=Object.create(null);words.forEach(function(w){m[w]=true;});return m;}
var DECIDED=wordSet(['accepted','superseded','deprecated','rejected','withdrawn']);
var DECIDING=wordSet(['draft','proposed','open','final','experimental']);
function hasOwn(m,k){return Object.prototype.hasOwnProperty.call(m,k);}
// A record's word: the first run of letters in its lifecycle value, lowercased.
function wordOf(rec){
var l=rec.lifecycle;if(!l||l.missing)return'';
var w=/[A-Za-z]+/.exec(l.raw_value||'');
return w?w[0].toLowerCase():'';}
function isDecided(rec){return hasOwn(DECIDED,wordOf(rec));}
function isDeciding(rec){return hasOwn(DECIDING,wordOf(rec));}
// A record's areas: the comma-separated parts of its first Areas field, trimmed, without
// empty parts or repeats. An own-key set keeps a huge hostile field linear in its length.
function areasOf(rec){
var hf=Array.isArray(rec.header_fields)?rec.header_fields:[],out=[],seen=Object.create(null);
for(var i=0;i<hf.length;i++){
if(hf[i]&&String(hf[i].label).toLowerCase()==='areas'){
String(hf[i].display_value!=null?hf[i].display_value:'').split(',').forEach(function(p){
p=p.trim();if(p&&!hasOwn(seen,p)){seen[p]=1;out.push(p);}});
break;}}
return out;}
// The count beside a question: unchanged by search and filters.
function questionCount(key){
if(key==='recent')return records.filter(isDecided).length;
if(key==='deciding')return records.filter(isDeciding).length;
if(key==='replaced')return records.filter(function(r){return(r.superseded_by||[]).length>0;}).length;
if(key==='graph')return Lineage.allChains(rels).length;
if(key==='areas'){
var seen=Object.create(null),n=0;
records.forEach(function(r){areasOf(r).forEach(function(a){if(!hasOwn(seen,a)){seen[a]=true;n++;}});});
return n;}
return null;}
// The links are built once; a render only moves aria-current, and activation moves focus to the list heading.
function buildRail(){
var rail=document.getElementById('question-list');if(!rail)return;
RAIL_GROUPS.forEach(function(g){
var head=el('h2','rail-group',g.label);head.id='rail-'+g.key;rail.appendChild(head);
var ul=el('ul','question-list');ul.setAttribute('aria-labelledby',head.id);
g.questions.forEach(function(key){
var q=question(key);
var li=el('li','question');
var a=el('a','question-link');a.id='q-'+q.key;a.setAttribute('href','#'+q.key);
a.appendChild(el('span','q-name',q.label));
var n=questionCount(q.key);
if(n!==null)a.appendChild(el('span','q-count',String(n)));
// The full question is the link's description, so the visible name can stay short.
var why=el('span','visually-hidden',q.name);why.id='q-desc-'+q.key;
a.setAttribute('aria-describedby',why.id);
// A modified or non-primary click keeps the browser's own link handling.
a.addEventListener('click',function(e){
if(e.button!==0||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;
e.preventDefault();switchView(q.key);});
li.appendChild(a);li.appendChild(why);ul.appendChild(li);});
rail.appendChild(ul);});}
// ── Kind pill helper ─────────────────────────────────────────────────────────
function setKindPill(kind){
if(!kindEl)return;
kindEl.querySelectorAll('button[data-kind]').forEach(function(b){
b.setAttribute('aria-pressed',(b.getAttribute('data-kind')||'')===kind?'true':'false');});}
// ── Routing ──────────────────────────────────────────────────────────────────
// A history entry is #<view>[/<id>[/unpicked]]: the id with no suffix is picked (the
// detail replaces the list below 40rem); the suffix marks a selection that is not picked.
function parseHash(){
state.sel=null;state.picked=false;
try{
var h=location.hash.slice(1);
if(!h){state.view='recent';return;}
var parts=h.split('/');
var v=parts[0];
// #detail/<id> opens Browse all with the record picked; an unknown first part opens it with nothing.
if(v==='detail')state.view='list';
else{
if(VALID_VIEWS.indexOf(v)<0){state.view='list';return;}
state.view=v;}
if(parts.length>1){try{state.sel=decodeURIComponent(parts[1]);}
catch(ue){state.sel=null;}}
state.picked=state.sel!==null&&parts[2]!=='unpicked';
// A #detail/<id> entry is rewritten to the view it opened in, so history restores that view.
if(v==='detail')history.replaceState(null,'',stateHash());
}catch(ex){state.view='list';state.sel=null;state.picked=false;}}
function stateHash(){
return '#'+state.view+(state.sel?'/'+encodeURIComponent(state.sel)+(state.picked?'':'/unpicked'):'');}
function pushState(){
var h=stateHash();
// The empty hash is the Recently decided route, so that route adds no entry.
if((location.hash||'#recent')!==h)history.pushState(null,'',h);}
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
function focusDetailHeading(){
var h=document.querySelector('#detail-body h2');
if(h){h.setAttribute('tabindex','-1');h.focus({preventScroll:false});}}
// Focus the first row of the selected record in the current list. A row in a closed area section
// cannot take focus: opening every section that holds the record (back to list) or, failing an
// open one, the first section lets focus land without disturbing the reader's other sections.
function focusRow(openAll){
var rows=document.querySelectorAll('#view-'+state.view+' button.row-link'),mine=[];
for(var i=0;i<rows.length;i++){
if(rows[i].getAttribute('data-id')===state.sel)mine.push(rows[i]);}
if(mine.length===0)return false;
var target=mine[0];
mine.forEach(function(r){var d=r.closest('details');if(openAll&&d)d.open=true;});
if(!openAll){
var ready=mine.filter(function(r){var d=r.closest('details');return !d||d.open;});
if(ready.length)target=ready[0];
else{var d0=target.closest('details');if(d0)d0.open=true;}}
target.focus();return true;}
// With the list zone hidden (one column) focus follows the pick into the detail.
// Every view but Lineage and the guidance context is a list of rows.
function isListView(v){return v!=='graph'&&v!=='context';}
function focusAfterPick(){
var wl=document.querySelector('.worklist');
if(state.picked&&wl&&wl.offsetParent===null)focusDetailHeading();
else if(state.picked&&isListView(state.view)&&focusRow())return;
else focusViewHeading();}
// Pick a record in a view; the view stays current. 'detail' means the current view.
function navigate(view,id){
state.view=view==='detail'?state.view:view;
if(id!==undefined){state.sel=id;state.picked=id!==null;}
pushState();render();focusAfterPick();}
function switchView(v){
state.view=v;state.picked=false;pushState();render();focusViewHeading();}
function render(onlyView){
VALID_VIEWS.forEach(function(v){
var b=document.getElementById('q-'+v);
if(b){if(state.view===v){b.setAttribute('aria-current','page');}
else{b.removeAttribute('aria-current');}}
var d=document.getElementById('view-'+v);
if(d)d.hidden=state.view!==v;});
var zones=document.getElementById('app-main');
if(zones){if(state.picked)zones.setAttribute('data-picked','');
else zones.removeAttribute('data-picked');}
var c=document.getElementById('view-'+state.view);
if(!c)return;parkTools();c.textContent='';
listInfo=null;
if(state.view==='graph')renderGraph(c);
else if(state.view==='context')renderContext(c);
else renderList(c,state.view);
placeTools(c);
// With nothing selected the detail summarises the list, so a search or filter refreshes it too.
if(!onlyView||!state.sel){
renderDetail(document.getElementById('detail-body'));
var pr=state.picked&&state.sel?records.find(function(r){return r.id===state.sel;}):null;
if(pr)updateLive(pr.id+': '+(pr.display_title||pr.title));}
syncExpandLabel();}
// Expand all acts on the sections of the current view and of the detail zone.
function openable(){
var out=[];
['view-'+state.view,'detail-body'].forEach(function(id){
var e=document.getElementById(id);
if(e)e.querySelectorAll('details').forEach(function(d){if(d!==keyEl)out.push(d);});});
return out;}
// Expand all and the Key follow the list head, as in the intents view: they move into the
// current region after its head, and back to their place before a region is cleared.
var toolsEl=document.querySelector('.worklist > .tools'),keyEl=document.getElementById('key');
var toolsHome=keyEl?keyEl.nextSibling:null;
function parkTools(){
if(!toolsEl||!keyEl||!toolsHome)return;
var wl=toolsHome.parentNode;wl.insertBefore(toolsEl,toolsHome);wl.insertBefore(keyEl,toolsHome);}
function placeTools(c){
// The guidance context has no list head: its heading and record line stand in for one.
var head=c.querySelector('.list-head')||c.querySelector('.ctx-record')||c.querySelector('h2');
if(!head||!toolsEl||!keyEl)return;
head.parentNode.insertBefore(keyEl,head.nextSibling);head.parentNode.insertBefore(toolsEl,keyEl);}
function syncExpandLabel(){
var b=document.getElementById('expand-all-btn');if(!b)return;
var d=openable(),all=d.length>0;
for(var i=0;i<d.length;i++){if(!d[i].open){all=false;break;}}
b.disabled=d.length===0;
b.textContent=all?'Collapse all':'Expand all';}
// ── Supersession banner ──────────────────────────────────────────────────────
function supBanner(entry,isDetail){
var div=document.createElement('div');
div.className='notice supersede-banner';div.setAttribute('role','note');
div.appendChild(document.createTextNode(entry.partial?'Superseded in part by ':'Superseded by '));
var a=document.createElement('a');
a.href='#detail/'+encodeURIComponent(entry.by);a.textContent=entry.by;
// Follow the link in the view that is current, with the target picked.
a.addEventListener('click',function(e){
// A modified or non-primary click keeps the browser's own link handling.
if(e.button!==0||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;
e.preventDefault();navigate('detail',entry.by);});
div.appendChild(a);
if(entry.partial){
var sc=entry.scope&&entry.scope.length?'('+entry.scope.join(', ')+')':'(scope not stated)';
div.appendChild(document.createTextNode(' '+sc));}
return div;}
// ── List view ────────────────────────────────────────────────────────────────
// A list's head: its full question, its heading, how it is sorted and, for a list of
// records, how many of them the search and filters leave.
function listHead(c,q,count,extra){
var d=el('div','list-head');
d.appendChild(el('p','list-question',q.name));
d.appendChild(el('h2','list-title',q.heading));
d.appendChild(el('p','meta list-sort',q.sort));
if(count!=null)d.appendChild(el('p','meta list-count',count));
if(extra)d.appendChild(el('p','meta list-noarea',extra));
c.appendChild(d);}
// A header date: the first ten characters of the first field with this label, when they read
// YYYY-MM-DD. The first field with the label decides, even when it holds no date.
function headerDate(rec,label){
var hf=Array.isArray(rec.header_fields)?rec.header_fields:[];
for(var i=0;i<hf.length;i++){
if(hf[i]&&String(hf[i].label).toLowerCase()===label){
var d=String(hf[i].raw_value!=null?hf[i].raw_value:'').slice(0,10);
return /^\d{4}-\d{2}-\d{2}$/.test(d)?d:null;}}
return null;}
function decisionDate(rec){return headerDate(rec,rec.kind==='RFC'?'date closed':'date');}
function openedDate(rec){return headerDate(rec,rec.kind==='RFC'?'date opened':'date');}
// Text order by code point: the lowercased names first, then the names themselves.
function cpCmp(a,b){
var x=Array.from(a),y=Array.from(b),n=Math.min(x.length,y.length);
for(var i=0;i<n;i++){var d=x[i].codePointAt(0)-y[i].codePointAt(0);if(d)return d;}
return x.length-y.length;}
function nameCmp(a,b){return cpCmp(a.toLowerCase(),b.toLowerCase())||cpCmp(a,b);}
// Records sorted by a date key and then by export position (ascending or descending); records
// with no date follow in export order. Returns the dated part and the undated part.
var POS=new Map();
records.forEach(function(r,i){POS.set(r,i);});
function byDate(recs,dateOf,newestFirst){
var dated=[],undated=[];
recs.forEach(function(r){
var d=dateOf(r),i=POS.get(r);
if(d===null)undated.push(r);else dated.push({r:r,d:d,i:i});});
dated.sort(function(a,b){
var c=a.d<b.d?-1:a.d>b.d?1:0;
if(c===0)c=a.i-b.i;
return newestFirst?-c:c;});
return{dated:dated.map(function(x){return x.r;}),undated:undated};}
// Each question's membership: sections of records, with no reference to search or filters.
// A section's head is the heading shown before its rows, or null when it has none.
function recentSections(){
var p=byDate(records.filter(isDecided),decisionDate,true);
return[{head:null,recs:p.dated,date:decisionDate},{head:'No decision date',recs:p.undated,date:decisionDate}];}
function decidingSections(){
var p=byDate(records.filter(isDeciding),openedDate,false);
return[{head:null,recs:p.dated,date:openedDate},{head:'No opened date',recs:p.undated,date:openedDate}];}
function replacedSections(){
var full=[],part=[];
records.forEach(function(r){
var s=r.superseded_by||[];
if(s.some(function(e){return !e.partial;}))full.push(r);
else if(s.length)part.push(r);});
return[{head:'Replaced in full',recs:full},{head:'Replaced in part',recs:part}];}
function areaSections(){
var groups=Object.create(null),names=[];
records.forEach(function(r){areasOf(r).forEach(function(a){
if(!hasOwn(groups,a)){groups[a]=[];names.push(a);}
groups[a].push(r);});});
names.sort(nameCmp);
return names.map(function(a){
var p=byDate(groups[a],decisionDate,true);
return{area:a,recs:p.dated.concat(p.undated),date:decisionDate};});}
function sectionsOf(key){
if(key==='recent')return recentSections();
if(key==='deciding')return decidingSections();
if(key==='replaced')return replacedSections();
if(key==='areas')return areaSections();
return[{head:null,recs:records}];}
// What the current list holds after narrowing, for the empty detail's summary:
// {recs: records shown, areas: sections shown (By area), chains/linked: Lineage}, or null.
var listInfo=null;
// Areas the reader has opened stay open when the list is built again.
var openAreas=Object.create(null);
function rowItem(r,key,dateText){
// Strike-through is reserved for full supersession; a record superseded only
// in part stays in force and gets the lighter "in part" treatment.
var supAll=r.superseded_by||[];
var supCls=supAll.some(function(s){return !s.partial;})?' is-superseded':
supAll.length?' is-superseded-part':'';
var li=el('li','row'+supCls);
// One button per row: title first, then the lifecycle mark, then the sorting date, kind and id.
var b=el('button','row-link');b.type='button';
b.setAttribute('data-id',r.id);
if(r.id===state.sel)b.setAttribute('aria-current','true');
b.appendChild(el('span','c-title c-name',r.display_title||r.title));
b.appendChild(markEl(r));
var ctx=el('span','c-context');
ctx.appendChild(document.createTextNode((dateText?dateText+' · ':'')+r.kind+' · '));
ctx.appendChild(el('span','value rid',r.id));
b.appendChild(ctx);
var supBy=r.superseded_by||[];
var unresClaims=r.unresolved_claims||[];
b.addEventListener('click',function(){navigate(key,r.id);});
li.appendChild(b);
// The marker follows the button inside the row, never inside the button.
if(supBy.length>0){
supBy.forEach(function(s){li.appendChild(supBanner(s,false));});}
else if(unresClaims.length>0){
var sb2=document.createElement('div');sb2.className='notice supersede-banner is-unresolved';sb2.setAttribute('role','note');
sb2.appendChild(document.createTextNode('Unresolved supersession claim: '+claimText(unresClaims[0])));
li.appendChild(sb2);}
return li;}
function rowList(recs,key,dateOf){
var ul=el('ul','rows record-list');
recs.forEach(function(r){ul.appendChild(rowItem(r,key,dateOf?dateOf(r):null));});
return ul;}
function emptyAfterNarrowing(c){
var activeFilters=[];
if(state.q)activeFilters.push('search: "'+state.q+'"');
if(state.kind)activeFilters.push('kind: '+state.kind);
if(state.status)activeFilters.push('status: '+V(state.status));
var msg=activeFilters.length>0?
'No records match '+activeFilters.join(', ')+'.':
'No records match the active filters.';
c.appendChild(el('p','empty-msg empty',msg));
if(activeFilters.length>0){
var rb=btn('reset-btn','Reset filters',function(){
state.q='';state.kind='';state.status='';
if(searchEl)searchEl.value='';
setKindPill('');
if(statusEl)statusEl.value='';
render(true);focusViewHeading();});
c.appendChild(rb);}
return msg;}
// Every list but Lineage and the guidance context: the question's rows, narrowed by search and filters.
function renderList(c,key){
var q=question(key),secs=sectionsOf(key);
var keep=new Set(filtered());
var all=new Set(),shown=new Set();
secs.forEach(function(s){s.recs.forEach(function(r){all.add(r);if(keep.has(r))shown.add(r);});});
var noArea='';
if(key==='areas'&&all.size>0&&all.size<records.length){
var n=records.length-all.size;
noArea=n+(n===1?' record has':' records have')+' no area; Browse all lists them.';}
listHead(c,q,shown.size+' of '+all.size+' records shown',noArea);
if(all.size===0){
c.appendChild(el('p','empty-msg empty',q.empty));
updateLive(q.empty);return;}
if(shown.size===0){updateLive(emptyAfterNarrowing(c));return;}
var sectionsShown=0;
secs.forEach(function(s){
var recs=s.recs.filter(function(r){return keep.has(r);});
if(recs.length===0)return;
sectionsShown++;
if(key==='areas'){
var d=el('details','key area-group');
var open=hasOwn(openAreas,s.area);
d.open=open;
d.appendChild(el('summary',null,s.area+' ('+recs.length+')'));
d.addEventListener('toggle',function(){
if(d.open)openAreas[s.area]=true;else delete openAreas[s.area];});
d.appendChild(rowList(recs,key,s.date));
c.appendChild(d);return;}
if(s.head)c.appendChild(el('h3','group-head',s.head));
c.appendChild(rowList(recs,key,s.date));});
listInfo={recs:Array.from(shown),areas:sectionsShown};
updateLive(shown.size+' of '+all.size+' records shown.');}
// ── Graph view ───────────────────────────────────────────────────────────────
function renderGraph(c){
listHead(c,question('graph'));
if(state.sel){
// Focused view: SVG lineage diagram for the selected record
var back=el('button','atlas-back','← All chains');back.type='button';
back.addEventListener('click',function(){navigate('graph',null);});
c.appendChild(back);
Lineage.renderFocused(c,state.sel,rels,records,navigate);
}else{
// Atlas: all checked-supersession chains
c.appendChild(el('p','graph-note',
'Every chain of records joined by checked supersession. Click a node to focus.'));
Lineage.renderAtlas(c,rels,records,navigate);
var chains=Lineage.allChains(rels);
if(chains.length)listInfo={chains:chains.length,linked:chains.reduce(function(n,ch){return n+ch.length;},0)};
}
updateLive('');}
// ── Context view ─────────────────────────────────────────────────────────────
function renderContext(c){
var rec=state.sel?records.find(function(r){return r.id===state.sel;}):null;
var h2=el('h2',null,rec?'Guidance context: '+rec.id:'Guidance context');
c.appendChild(h2);
if(!rec){
c.appendChild(el('p','empty-msg empty',state.sel?
shownId(state.sel)+' is not in this export.':
'Pick a record, then choose Guidance context in its detail.'));
updateLive('');return;}
var ctxHead=el('p','ctx-record',(rec.display_title||rec.title)+' · '+lc(rec));
c.appendChild(ctxHead);
(rec.superseded_by||[]).forEach(function(s){c.appendChild(supBanner(s,true));});
var ctx=rels.filter(function(r){
return r.trust_class==='contextual'&&(r.from===rec.id||r.to===rec.id);});
c.appendChild(el('h3',null,
'Contextual references — Related field (weaker than checked lineage)'));
if(ctx.length===0){
c.appendChild(el('p','empty-msg empty','No contextual references for this record.'));}
else{
var ul=el('ul','ctx-list');
ctx.forEach(function(r){
var peer=r.from===rec.id?r.to:r.from;
var dir=r.from===rec.id?'refers to':'referred to by';
var label=dir+' '+V(peer||'?')+' [contextual · '+r.resolution_state+']';
var li=el('li',null);
var admitted=records.find(function(x){return x.id===peer;});
if(admitted){
var b=btn('ctx-btn',label,function(){navigate('context',peer);});
li.appendChild(b);}
else{li.textContent=label+' — not admitted';}
ul.appendChild(li);});
c.appendChild(ul);}
var asserts=rels.filter(function(r){
return r.trust_class==='navigation_only'
&&(r.from===rec.id||r.to===rec.id);});
c.appendChild(el('h3',null,'Caller assertions (non-authoritative view input)'));
if(asserts.length===0){
c.appendChild(el('p','empty-msg empty','No caller assertions embedded for this record.'));}
else{
var ul2=el('ul','assert-list');
asserts.forEach(function(a){
var li=el('li',null);
var tlEl=el('span','trust-label chip','[navigation_only · caller_asserted]');
li.appendChild(tlEl);
li.appendChild(document.createTextNode(' '));
li.appendChild(document.createTextNode(a.display_raw_value||V(a.raw_value||'')));
if(a.from)li.appendChild(document.createTextNode(' from: '+V(a.from)));
if(a.to)li.appendChild(document.createTextNode(' → '+V(a.to)));
ul2.appendChild(li);});
c.appendChild(ul2);}
updateLive('');}
// ── Detail view ──────────────────────────────────────────────────────────────
// Each record the selected one supersedes through a checked relationship.
function replacesOf(rec){
return rels.filter(function(r){
return r.trust_class==='checked'&&r.from===rec.id&&r.to&&
(r.relation==='supersedes'||r.relation==='supersedes_in_part');
}).map(function(r){return{to:r.to,partial:r.relation==='supersedes_in_part',scope:r.scope};});}
// A click on a link that is not modified keeps the browser's handling off and acts in the page.
function plainClick(e){return e.button===0&&!e.ctrlKey&&!e.metaKey&&!e.shiftKey&&!e.altKey;}
function recordLink(id){
if(!records.some(function(r){return r.id===id;}))return document.createTextNode(V(id));
var a=el('a',null,id);a.setAttribute('href','#detail/'+encodeURIComponent(id));
a.addEventListener('click',function(e){
if(!plainClick(e))return;
e.preventDefault();navigate('detail',id);});
return a;}
// A link to another view of the selected record: the selection stays, so that view focuses it.
function viewLink(text,view,id){
var a=el('a',null,text);// The target is the entry a click pushes: the record selected, not picked.
a.setAttribute('href','#'+view+'/'+encodeURIComponent(id)+'/unpicked');
a.addEventListener('click',function(e){
if(!plainClick(e))return;
e.preventDefault();switchView(view);});
return a;}
function plural(n,noun){return n+' '+noun+(n===1?'':'s');}
// A plain count of what the current list holds, from fixed words, numbers and kind names only.
function listSummary(){
if(!listInfo)return'';
if(listInfo.chains)return'In this list: '+plural(listInfo.chains,'chain')+' joining '+plural(listInfo.linked,'record')+'.';
var recs=listInfo.recs;
if(!recs||recs.length===0)return'';
var kinds=Object.create(null),names=[];
recs.forEach(function(r){var k=String(r.kind);if(!hasOwn(kinds,k)){kinds[k]=0;names.push(k);}kinds[k]++;});
names.sort(nameCmp);
var out='In this list: '+names.map(function(k){return plural(kinds[k],k);}).join(', ');
if(state.view==='replaced'){
var full=0,part=0;
recs.forEach(function(r){
if((r.superseded_by||[]).some(function(e){return !e.partial;}))full++;else part++;});
out+='; '+full+' replaced in full and '+part+' in part';}
if(state.view==='areas')out+='; '+plural(listInfo.areas,'area section');
return out+'.';}
function renderDetail(c){
var rec=state.sel?records.find(function(r){return r.id===state.sel;}):null;
c.textContent='';
var h2=el('h2',null,rec?(rec.display_title||rec.title):'Record detail');
h2.className='detail-heading focus-target';c.appendChild(h2);
if(!rec){
if(state.sel){c.appendChild(el('p','empty',shownId(state.sel)+' is not in this export.'));return;}
c.appendChild(el('p','note','Pick a record to see its detail.'));
var sum=listSummary();
if(sum!=='')c.appendChild(el('p','list-summary',sum));
return;}
// The state line: the lifecycle mark, then the kind and the id.
var sl0=el('p','state-line');sl0.appendChild(markEl(rec));
var sctx=el('span','c-context');sctx.appendChild(document.createTextNode(rec.kind+' · '));
sctx.appendChild(el('span','value',rec.id));sl0.appendChild(sctx);c.appendChild(sl0);
// Supersession banners from checked relationships only — at top of detail
var supBy=rec.superseded_by||[];
var unresClaims=rec.unresolved_claims||[];
if(supBy.length>0){
supBy.forEach(function(s){c.appendChild(supBanner(s,true));});}
else if(unresClaims.length>0){
unresClaims.forEach(function(u){
var div=document.createElement('div');div.className='notice supersede-banner';div.setAttribute('role','note');
div.appendChild(document.createTextNode('Unresolved supersession claim: '+claimText(u)));
c.appendChild(div);});}
// The lead: what this record replaced, when it was decided and where it sits, then where to go next.
var replaces=replacesOf(rec);
if(replaces.length>0){
var rp=el('p','replaces-line');rp.appendChild(document.createTextNode('Replaces '));
replaces.forEach(function(r,k){
if(k>0)rp.appendChild(document.createTextNode(', '));
rp.appendChild(recordLink(r.to));
if(r.partial){rp.appendChild(document.createTextNode(' in part '+(r.scope&&r.scope.length?'('+r.scope.join(', ')+')':'(scope not stated)')));}});
c.appendChild(rp);}
var facts=[];
var when=isDeciding(rec)?openedDate(rec):decisionDate(rec);
if(when!==null)facts.push((isDeciding(rec)?'Opened ':'Decided ')+when);
var areas=areasOf(rec);
if(areas.length>0)facts.push('Areas: '+areas.join(', '));
if(facts.length>0)c.appendChild(el('p','facts-line',facts.join(' · ')));
var links=el('p','detail-links');
links.appendChild(viewLink('Lineage','graph',rec.id));
links.appendChild(viewLink('Guidance context','context',rec.id));
var srcA=makeLink(rec.source);
links.appendChild(srcA||el('span','source-path',V(rec.source)));
c.appendChild(links);
c.appendChild(el('h3',null,'Record body'+(mode==='bounded'?' (omitted in bounded mode)':'')));
var body=rec.body;
if(!body){c.appendChild(el('p','empty','Body not available.'));}
else if(!body.available){
var reason=body.omission_reason||'not_available';
var notice=el('p','bounded-notice notice');
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
sec.setAttribute('aria-label','Record content');sec.setAttribute('tabindex','0');
sec.className='record-content';
renderMarkdown(content,sec);
bd.appendChild(sec);bodyEl=bd;}
else{
var sec2=document.createElement('section');
sec2.setAttribute('aria-label','Record content');sec2.setAttribute('tabindex','0');
sec2.className='record-content';
renderMarkdown(content,sec2);
bodyEl=sec2;}
c.appendChild(bodyEl);}
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
var tlEl=el('span','trust-label chip','['+r.trust_class+' · '+r.resolution_state+']');
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

var tbl=el('table','meta-table');
var metaRows=[['Kind',rec.kind],['Status',lc(rec)],['Source',V(rec.source)]];
// Every header-region field, exactly as recorded (escaped for display).
(Array.isArray(rec.header_fields)?rec.header_fields:[]).forEach(function(hf){
if(hf&&hf.label&&!(hf.label.toLowerCase()==='status'&&statusShownAs(hf,rec)))metaRows.push([V(hf.label),hf.display_value!=null?hf.display_value:V(hf.raw_value||'')]);});
metaRows.forEach(function(row){
var tr=document.createElement('tr');
var th=el('th','field',row[0]);var td=el('td',null,row[1]);
tr.appendChild(th);tr.appendChild(td);tbl.appendChild(tr);});
var slTr=document.createElement('tr');
var slTh=el('th','field','Source link');var slTd=el('td',null);
var sl=makeLink(rec.source);
if(sl){slTd.appendChild(sl);}
else{slTd.textContent=V(rec.source)+' (remote not on allowlist — inert provenance)';}
slTr.appendChild(slTh);slTr.appendChild(slTd);tbl.appendChild(slTr);
var allDet=el('details','all-fields');
allDet.appendChild(el('summary',null,'All header fields'));
allDet.appendChild(tbl);c.appendChild(allDet);}
// ── Event bindings ───────────────────────────────────────────────────────────
if(searchEl)searchEl.addEventListener('input',function(){
state.q=this.value;render(true);});
// Kind filter: a segmented control of buttons
if(kindEl){
kindEl.querySelectorAll('button[data-kind]').forEach(function(b){
b.addEventListener('click',function(){
state.kind=b.getAttribute('data-kind')||'';
setKindPill(state.kind);
render(true);});});}
if(statusEl)statusEl.addEventListener('change',function(){
state.status=this.value;render(true);});
// Expand all: toggles every section in the current view and the detail zone
var expandAllBtn=document.getElementById('expand-all-btn');
if(expandAllBtn){
expandAllBtn.addEventListener('click',function(){
var dets=openable();
if(!dets.length)return; // nothing to expand on this view; keep the label
var allOpen=true;
for(var di=0;di<dets.length;di++){if(!dets[di].open){allOpen=false;break;}}
for(var dj=0;dj<dets.length;dj++){dets[dj].open=!allOpen;}
expandAllBtn.textContent=allOpen?'Expand all':'Collapse all';});}
var mainEl=document.getElementById('app-main');
if(mainEl)mainEl.addEventListener('toggle',syncExpandLabel,true);
// Back to list (one column): show the list zone again in the view that was current.
var backBtn=document.getElementById('back-btn');
if(backBtn)backBtn.addEventListener('click',function(){
state.picked=false;pushState();render(true);
if(!(isListView(state.view)&&focusRow(true)))focusViewHeading();});
window.addEventListener('popstate',function(){parseHash();render();focusAfterPick();});
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
buildRail();
parseHash();render();
}();
