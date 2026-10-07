!function(){
'use strict';
// Safe Markdown renderer for decision-navigation record bodies.
// Security: text only via createTextNode/textContent; no unsafe DOM-mutation APIs.
// All text inserted via createTextNode or textContent.
// Elements only from ETAG allowlist; class only from ECLS allowlist.
// Depth counter: block or inline nesting > MAX_DEPTH renders whole body as plain pre.

var MAX_DEPTH=32;
var _d=0;   // current nesting depth
var _err=false; // depth-exceeded flag

// Visible-escape bidi/zero-width/control chars (mirrors Python _escape_display).
var UNSAFE_RE=/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F\xAD\u061C\u180E\u200B-\u200F\u202A-\u202E\u2060-\u2064\u2066-\u206F\uFEFF\uFFF9-\uFFFB\u{E0000}-\u{E007F}]/gu;
function vis(s){
  return String(s).replace(UNSAFE_RE,function(c){
    var h=c.codePointAt(0).toString(16).toUpperCase();
    while(h.length<4)h='0'+h;
    return '[U+'+h+']';});}

function tn(s){return document.createTextNode(vis(s));}

// Fixed element tag allowlist
var ETAG={p:1,h3:1,h4:1,h5:1,h6:1,ul:1,ol:1,li:1,blockquote:1,pre:1,code:1,
  strong:1,em:1,table:1,thead:1,tbody:1,tr:1,th:1,td:1,hr:1,span:1};
// Fixed class allowlist for renderer-generated classes
var ECLS={'md-link':1,'md-link-target':1,'md-image-alt':1};

function mel(tag,cls){
  var e=document.createElement(ETAG[tag]?tag:'span');
  if(cls&&ECLS[cls])e.className=cls;
  return e;}

// Split a table row by |, strip leading/trailing empty cells from outer pipes.
function splitRow(line){
  var cells=line.split('|');
  if(cells[0].trim()==='')cells.shift();
  if(cells.length&&cells[cells.length-1].trim()==='')cells.pop();
  return cells;}

// Inline parser: append nodes to parent element.
// Every closer search goes through find(), which remembers the last answer per
// needle, so repeated unmatched openers cost linear time, not quadratic.
function inline(text,parent){
  _d++;
  if(_d>MAX_DEPTH){_err=true;_d--;return;}
  var i=0,n=text.length,seen={};
  function find(needle,from){
    var c=seen[needle];
    if(c&&from>=c.from&&(c.pos<0||from<=c.pos))return c.pos;
    var pos=text.indexOf(needle,from);
    seen[needle]={from:from,pos:pos};return pos;}
  while(i<n){
    var c=text[i];
    // Raw HTML — render the whole tag as literal text
    if(c==='<'){
      var j=find('>',i+1);if(j<0)j=n;
      parent.appendChild(tn(text.slice(i,j<n?j+1:n)));
      i=j<n?j+1:n;continue;}
    // Image: ![alt](url) — alt text only, no img element
    if(c==='!'&&i+1<n&&text[i+1]==='['){
      var cb=find('](',i+2);
      if(cb>=0){var ue=find(')',cb+2);
        if(ue>=0){var sp=mel('span','md-image-alt');sp.appendChild(tn(text.slice(i+2,cb)));parent.appendChild(sp);i=ue+1;continue;}}
      parent.appendChild(tn('!'));i++;continue;}
    // Link: [text](url) — inert span, no href
    if(c==='['){
      var cb2=find('](',i+1);
      if(cb2>=0){var ue2=find(')',cb2+2);
        if(ue2>=0){
          var os=mel('span','md-link');
          inline(text.slice(i+1,cb2),os);
          os.appendChild(tn(' '));
          var ts=mel('span','md-link-target');
          ts.appendChild(tn('('+text.slice(cb2+2,ue2)+')'));
          os.appendChild(ts);parent.appendChild(os);i=ue2+1;continue;}}
      parent.appendChild(tn('['));i++;continue;}
    // Code span: `code`
    if(c==='`'){
      var t0=i;while(i<n&&text[i]==='`')i++;
      var tks=text.slice(t0,i);
      var ce=find(tks,i);
      if(ce>=0){var cd=mel('code','');cd.textContent=vis(text.slice(i,ce));parent.appendChild(cd);i=ce+tks.length;continue;}
      parent.appendChild(tn(tks));continue;}
    // Strong **text**
    if(c==='*'&&i+1<n&&text[i+1]==='*'){
      var se=find('**',i+2);
      if(se>=0){var st=mel('strong','');inline(text.slice(i+2,se),st);parent.appendChild(st);i=se+2;continue;}}
    // Strong __text__
    if(c==='_'&&i+1<n&&text[i+1]==='_'){
      var se2=find('__',i+2);
      if(se2>=0){var st2=mel('strong','');inline(text.slice(i+2,se2),st2);parent.appendChild(st2);i=se2+2;continue;}}
    // Emphasis *text*
    if(c==='*'){
      var ee=find('*',i+1);
      if(ee>=0){var em=mel('em','');inline(text.slice(i+1,ee),em);parent.appendChild(em);i=ee+1;continue;}}
    // Emphasis _text_
    if(c==='_'){
      var ee2=find('_',i+1);
      if(ee2>=0){var em2=mel('em','');inline(text.slice(i+1,ee2),em2);parent.appendChild(em2);i=ee2+1;continue;}}
    // Regular characters — accumulate until a special char
    var s=i;
    while(i<n&&'<[!`*_'.indexOf(text[i])<0)i++;
    if(i>s){parent.appendChild(tn(text.slice(s,i)));}
    else{parent.appendChild(tn(text[i]));i++;}}
  _d--;}

// ATX heading without a backtracking regex: 1-6 '#', whitespace, text, and an
// optional closing run of '#' preceded by whitespace.
function atxHeading(line){
  var k=0;while(k<line.length&&line[k]==='#')k++;
  if(k<1||k>6||k>=line.length||!/\s/.test(line[k]))return null;
  var t=line.slice(k).trim(),e=t.length;
  while(e>0&&t[e-1]==='#')e--;
  if(e===0)t='';
  else if(e<t.length&&/\s/.test(t[e-1]))t=t.slice(0,e).trim();
  return{level:k,text:t};}

// Build a list (ul or ol) from lines starting at i0.
// Returns {el, next} where next is the line index after the list.
function buildList(lines,i0,i1,ordered){
  _d++;
  if(_d>MAX_DEPTH){_err=true;_d--;return{el:mel(ordered?'ol':'ul',''),next:i0+1};}
  var listEl=mel(ordered?'ol':'ul','');
  var mi=lines[i0].match(/^(\s*)/);
  var baseInd=mi?mi[1].length:0;
  var i=i0;
  while(i<i1){
    var line=lines[i];
    var m=ordered?line.match(/^(\s*)\d+\.\s(.*)$/):line.match(/^(\s*)[-*+]\s(.*)$/);
    if(!m)break;
    var ind=m[1].length;
    if(ind<baseInd)break;
    if(ind>baseInd){
      // Nested list — attach to last li
      var last=listEl.lastChild;
      if(last){var nested=buildList(lines,i,i1,ordered);last.appendChild(nested.el);i=nested.next;}
      else i++;
      continue;}
    // A wrapped item continues on following lines indented past its marker.
    var itemText=m[2];i++;
    while(i<i1&&lines[i].trim()&&!/^\s*([-*+]|\d+\.)\s/.test(lines[i])){
      var ci=lines[i].match(/^(\s*)/)[1].length;
      if(ci<=baseInd)break;
      itemText+=' '+lines[i].trim();i++;}
    var li=mel('li','');inline(itemText,li);listEl.appendChild(li);}
  _d--;return{el:listEl,next:i};}

// Block parser: processes lines[i0..i1) and appends elements to parent.
function blocks(lines,i0,i1,parent){
  _d++;
  if(_d>MAX_DEPTH){_err=true;_d--;return;}
  var i=i0;
  while(i<i1){
    if(_err)break;
    var line=lines[i];
    // Blank line
    if(!line.trim()){i++;continue;}
    // Fenced code block
    var fc=line.match(/^(`{3,}|~{3,})/);
    if(fc){
      var fence=fc[1];var fi=i+1;
      while(fi<i1&&lines[fi].indexOf(fence)<0)fi++;
      var pre2=mel('pre','');var code2=mel('code','');
      // info string ignored; content is lines between fences
      code2.textContent=vis(lines.slice(i+1,fi).join('\n'));
      pre2.appendChild(code2);parent.appendChild(pre2);
      i=fi<i1?fi+1:i1;continue;}
    // Indented code (4 spaces or tab)
    if(line.match(/^( {4}|\t)/)){
      var clines=[];
      while(i<i1&&(lines[i].match(/^( {4}|\t)/)||!lines[i].trim())){
        clines.push(lines[i].replace(/^( {4}|\t)/,''));i++;}
      while(clines.length&&!clines[clines.length-1].trim())clines.pop();
      var pre3=mel('pre','');var code3=mel('code','');
      code3.textContent=vis(clines.join('\n'));pre3.appendChild(code3);parent.appendChild(pre3);continue;}
    // ATX heading: # to ######
    var hm=atxHeading(line);
    if(hm){
      // #→h3, ##→h4, …, ####-######→h6
      var lvl=Math.min(hm.level+2,6);
      var h=mel('h'+lvl,'');inline(hm.text,h);parent.appendChild(h);i++;continue;}
    // Thematic break
    if(line.match(/^(\*{3,}|-{3,}|_{3,})\s*$/)){
      parent.appendChild(mel('hr',''));i++;continue;}
    // Block quote
    if(line.startsWith('>')){
      var qlines=[];
      while(i<i1&&lines[i].startsWith('>')){
        qlines.push(lines[i].slice(1).replace(/^ /,''));i++;}
      var bq=mel('blockquote','');blocks(qlines,0,qlines.length,bq);parent.appendChild(bq);continue;}
    // GFM table: current line has | and next is a separator line
    if(line.includes('|')&&i+1<i1&&/^\|?[\s:|-]+\|?$/.test(lines[i+1])&&lines[i+1].includes('-')){
      var tbl=mel('table','');
      var thead=mel('thead','');var hr2=mel('tr','');
      splitRow(line).forEach(function(cell){
        var th=mel('th','');inline(cell.trim(),th);hr2.appendChild(th);});
      thead.appendChild(hr2);tbl.appendChild(thead);
      var tbody=mel('tbody','');tbl.appendChild(tbody);
      i+=2;// skip header and separator rows
      while(i<i1&&lines[i].includes('|')){
        var tr=mel('tr','');
        splitRow(lines[i]).forEach(function(cell){
          var td=mel('td','');inline(cell.trim(),td);tr.appendChild(td);});
        tbody.appendChild(tr);i++;}
      parent.appendChild(tbl);continue;}
    // Unordered list
    if(line.match(/^(\s*)[-*+]\s/)){
      var ul=buildList(lines,i,i1,false);parent.appendChild(ul.el);i=ul.next;continue;}
    // Ordered list
    if(line.match(/^(\s*)\d+\.\s/)){
      var ol=buildList(lines,i,i1,true);parent.appendChild(ol.el);i=ol.next;continue;}
    // Paragraph: accumulate until blank line or block-start
    var plines=[line];i++;
    while(i<i1&&lines[i].trim()&&
      !lines[i].match(/^(#{1,6}\s|`{3,}|~{3,}|>\s*|(\s*)([-*+]|\d+\.)\s|(\*{3,}|-{3,}|_{3,})\s*$|( {4}|\t))/)){
      plines.push(lines[i]);i++;}
    var p=mel('p','');inline(plines.join(' '),p);parent.appendChild(p);}
  _d--;}

// Public: render Markdown text into container element.
// On depth error, clears container and shows plain-text fallback with a note.
function renderMarkdown(text,container){
  _d=0;_err=false;
  var frag=document.createDocumentFragment();
  blocks(text.split('\n'),0,text.split('\n').length,frag);
  if(_err){
    var note=mel('p','');note.textContent='Shown as plain text: nesting deeper than 32 levels';
    container.appendChild(note);
    var pre=mel('pre','');pre.textContent=vis(text);container.appendChild(pre);
    return;}
  container.appendChild(frag);}

window.renderMarkdown=renderMarkdown;
// Shared with the explorer runtime so every human-facing string escapes the same way.
window.visEscape=vis;
}();
