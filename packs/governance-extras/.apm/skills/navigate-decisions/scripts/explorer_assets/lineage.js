/* lineage.js — SVG lineage diagram for the navigate-decisions explorer.
 * Security: DOM mutations use createElementNS and textContent only.
 * No direct HTML string injection, no dynamic script execution,
 * no SVG xlink attributes, no embedded-document or reuse elements.
 * Event handlers registered via addEventListener.
 */
var Lineage=(function(){'use strict';
var NS='http://www.w3.org/2000/svg';
function svgEl(t){return document.createElementNS(NS,t);}
function sa(e,k,v){e.setAttribute(k,String(v));return e;}
var NW=160,NH=48,XG=112,YG=16,PX=20,PY=20;
// Satellites sit SAT_GAP further out, so each branch into one is long enough
// for its label.
var SAT_GAP=40,SAT_BRANCH=96;

// ── Connected component over checked edges (undirected)
function chainOf(startId,rels){
  var adj={};
  rels.forEach(function(r){
    if(r.trust_class!=='checked')return;
    (adj[r.from]=adj[r.from]||[]).push(r.to);
    (adj[r.to]=adj[r.to]||[]).push(r.from);
  });
  var vis={};vis[startId]=1;var q=[startId];
  while(q.length){
    var c=q.shift();
    (adj[c]||[]).forEach(function(n){if(!vis[n]){vis[n]=1;q.push(n);}});
  }
  return Object.keys(vis);
}

// ── All connected components with ≥2 nodes
function allChains(rels){
  var adj={},nodes={};
  rels.forEach(function(r){
    if(r.trust_class!=='checked')return;
    nodes[r.from]=nodes[r.to]=1;
    (adj[r.from]=adj[r.from]||[]).push(r.to);
    (adj[r.to]=adj[r.to]||[]).push(r.from);
  });
  var vis={},chains=[];
  Object.keys(nodes).forEach(function(n){
    if(vis[n])return;
    var q=[n],comp=[];vis[n]=1;
    while(q.length){
      var c=q.shift();comp.push(c);
      (adj[c]||[]).forEach(function(nb){if(!vis[nb]){vis[nb]=1;q.push(nb);}});
    }
    if(comp.length>=2)chains.push(comp);
  });
  return chains;
}

// ── Tarjan SCC on directed checked edges (from=newer → to=older)
function findSCCs(nodes,rels){
  var adj={};
  nodes.forEach(function(n){adj[n]=[];});
  rels.forEach(function(r){if(adj[r.from])adj[r.from].push(r.to);});
  var idx=0,stack=[],onStack={},indices={},low={},result=[];
  function sc(v){
    indices[v]=low[v]=idx++;stack.push(v);onStack[v]=1;
    (adj[v]||[]).forEach(function(w){
      if(indices[w]==null){sc(w);if(low[w]<low[v])low[v]=low[w];}
      else if(onStack[w]&&indices[w]<low[v])low[v]=indices[w];
    });
    if(low[v]===indices[v]){
      var scc=[],w;
      do{w=stack.pop();onStack[w]=0;scc.push(w);}while(w!==v);
      result.push(scc);
    }
  }
  nodes.forEach(function(n){if(indices[n]==null)sc(n);});
  return result;
}

// ── Longest-path layering: older → layer 0 (left), newer → max layer (right)
// Checked edge: from=superseding(newer), to=superseded(older)
// Condensed DAG: edge si→sj when a member of si supersedes a member of sj (si is newer)
// Longest path from each condensed node to a sink = its layer; sinks (oldest) = layer 0
function layerDAG(chainNodes,checkedRels){
  var sccList=findSCCs(chainNodes,checkedRels);
  var n2s={};
  sccList.forEach(function(s,i){s.forEach(function(n){n2s[n]=i;});});
  var cadj={};
  sccList.forEach(function(_,i){cadj[i]=[];});
  checkedRels.forEach(function(r){
    var si=n2s[r.from],sj=n2s[r.to];
    if(si!=null&&sj!=null&&si!==sj)cadj[si].push(sj);
  });
  // Kahn topological sort of condensed DAG
  var ind=sccList.map(function(){return 0;});
  Object.keys(cadj).forEach(function(i){
    cadj[i].forEach(function(j){ind[j]++;});
  });
  var q=[],topo=[];
  ind.forEach(function(d,i){if(d===0)q.push(i);});
  while(q.length){
    var c=q.shift();topo.push(c);
    cadj[c].forEach(function(j){if(--ind[j]===0)q.push(j);});
  }
  // Any remaining nodes (due to residual cycles — shouldn't happen after Tarjan)
  sccList.forEach(function(_,i){if(topo.indexOf(i)<0)topo.push(i);});
  // Process in reverse topo (sinks first): layer[v] = max(layer[child]+1) or 0
  var sLay=sccList.map(function(){return 0;});
  topo.slice().reverse().forEach(function(i){
    cadj[i].forEach(function(j){if(sLay[j]+1>sLay[i])sLay[i]=sLay[j]+1;});
  });
  return{sccList:sccList,n2s:n2s,sLay:sLay};
}

// ── Sort SCC members by kind (ADR/RFC) then ordinal
function sortMembers(members){
  return members.slice().sort(function(a,b){
    var ka=a.replace(/-\d+$/,''),kb=b.replace(/-\d+$/,'');
    if(ka!==kb)return ka<kb?-1:1;
    return(parseInt(a.replace(/\D/g,''),10)||0)-(parseInt(b.replace(/\D/g,''),10)||0);
  });
}

// ── Barycenter of SCC si relative to positions of adjacent layer's SCCs
function bary(si,sccList,checkedRels,n2s,adjOrd){
  var sum=0,cnt=0;
  sccList[si].forEach(function(n){
    checkedRels.forEach(function(r){
      var nb=(r.from===n)?n2s[r.to]:(r.to===n)?n2s[r.from]:null;
      if(nb!=null&&nb!==si&&adjOrd[nb]!=null){sum+=adjOrd[nb];cnt++;}
    });
  });
  return cnt?sum/cnt:si;
}

// ── Compute (col, row) positions for each node in the chain
function positions(chainNodes,checkedRels){
  var lr=layerDAG(chainNodes,checkedRels);
  var sccList=lr.sccList,n2s=lr.n2s,sLay=lr.sLay;
  var maxL=0;
  sLay.forEach(function(l){if(l>maxL)maxL=l;});
  // Group SCCs by layer
  var layerSCCs=[];
  for(var i=0;i<=maxL;i++)layerSCCs.push([]);
  sLay.forEach(function(l,i){layerSCCs[l].push(i);});
  // 3 sweeps of barycenter sort
  for(var sw=0;sw<3;sw++){
    for(var l=1;l<layerSCCs.length;l++){
      var prevOrd={};
      layerSCCs[l-1].forEach(function(si,idx){prevOrd[si]=idx;});
      layerSCCs[l].sort(function(a,b){
        return bary(a,sccList,checkedRels,n2s,prevOrd)-bary(b,sccList,checkedRels,n2s,prevOrd);
      });
    }
    for(var l2=layerSCCs.length-2;l2>=0;l2--){
      var nextOrd={};
      layerSCCs[l2+1].forEach(function(si,idx){nextOrd[si]=idx;});
      layerSCCs[l2].sort(function(a,b){
        return bary(a,sccList,checkedRels,n2s,nextOrd)-bary(b,sccList,checkedRels,n2s,nextOrd);
      });
    }
  }
  // Assign (col, row) to each node
  var nodePos={};
  layerSCCs.forEach(function(sccIdxList,colIdx){
    var row=0;
    sccIdxList.forEach(function(si){
      sortMembers(sccList[si]).forEach(function(n,mi){
        nodePos[n]={col:colIdx,row:row+mi,scc:si};
      });
      row+=sccList[si].length;
    });
  });
  return{nodePos:nodePos,sccList:sccList,n2s:n2s,maxL:maxL};
}

// ── Arrow markers in <defs>
function addDefs(svg,pfx){
  var d=svgEl('defs');
  // Filled arrowhead (checked)
  var m1=svgEl('marker');
  sa(m1,'id',pfx+'af');sa(m1,'markerWidth','10');sa(m1,'markerHeight','7');
  sa(m1,'refX','9');sa(m1,'refY','3.5');sa(m1,'orient','auto');sa(m1,'markerUnits','userSpaceOnUse');
  var p1=svgEl('polygon');sa(p1,'points','0 0, 10 3.5, 0 7');sa(p1,'fill','#374151');
  m1.appendChild(p1);d.appendChild(m1);
  // Open arrowhead (unresolved)
  var m2=svgEl('marker');
  sa(m2,'id',pfx+'ao');sa(m2,'markerWidth','10');sa(m2,'markerHeight','7');
  sa(m2,'refX','9');sa(m2,'refY','3.5');sa(m2,'orient','auto');sa(m2,'markerUnits','userSpaceOnUse');
  var p2=svgEl('polyline');sa(p2,'points','0 0, 10 3.5, 0 7');sa(p2,'fill','none');
  sa(p2,'stroke','#9ca3af');sa(p2,'stroke-width','1.5');m2.appendChild(p2);d.appendChild(m2);
  // Hollow arrowhead (asserted)
  var m3=svgEl('marker');
  sa(m3,'id',pfx+'ah');sa(m3,'markerWidth','10');sa(m3,'markerHeight','7');
  sa(m3,'refX','9');sa(m3,'refY','3.5');sa(m3,'orient','auto');sa(m3,'markerUnits','userSpaceOnUse');
  var p3=svgEl('polygon');sa(p3,'points','0 0, 10 3.5, 0 7');sa(p3,'fill','white');
  sa(p3,'stroke','#a78bfa');sa(p3,'stroke-width','1.2');m3.appendChild(p3);d.appendChild(m3);
  svg.appendChild(d);
}

// ── Bezier edge between two points
function drawEdge(g,x1,y1,x2,y2,stroke,sw,dash,markerEnd){
  var path=svgEl('path');
  var cx=(x1+x2)/2;
  sa(path,'d','M '+x1+','+y1+' C '+cx+','+y1+' '+cx+','+y2+' '+x2+','+y2);
  sa(path,'fill','none');sa(path,'stroke',stroke||'#374151');
  sa(path,'stroke-width',sw||'2');
  if(dash)sa(path,'stroke-dasharray',dash);
  if(markerEnd)sa(path,'marker-end',markerEnd);
  g.appendChild(path);return path;
}

// ── Spread edge ends along each node's side so fanned edges stay apart.
// Returns, per relationship index, the y offsets of its start and end within
// a node of height nh; ends are ordered by the other node's row.
function edgePorts(rels,np,nh){
  var outs={},ins={},res=[];
  rels.forEach(function(r,i){
    var fp=np[r.from],tp=np[r.to];
    if(!fp||!tp||fp.scc===tp.scc)return;
    (outs[r.from]=outs[r.from]||[]).push(i);(ins[r.to]=ins[r.to]||[]).push(i);
    res[i]={};
  });
  function spread(map,key,other){
    Object.keys(map).forEach(function(n){
      var list=map[n];
      list.sort(function(a,b){return np[rels[a][other]].row-np[rels[b][other]].row;});
      list.forEach(function(ri,k){res[ri][key]=nh*(k+1)/(list.length+1);});
    });
  }
  spread(outs,'y1','to');spread(ins,'y2','from');
  return res;
}

// ── Edge labels
// A label sits on or right beside its own edge and never touches a node, a
// supersession ring, an arrowhead, another label or the drawing's border.
// Another edge's line may pass under it only where it is centred on its own
// line. Where no such spot exists it becomes a numbered marker on its edge,
// keyed in a list under the drawing, so nothing is ever covered.
var MAX_LABEL=16,LABEL_H=12;
// Labels are placed after every edge is drawn and the diagram is in the page.
function edgeLabel(g,x1,y1,x2,y2,txt,fill,path){
  (g._defer||(g._defer=[])).push([txt,fill,path]);
}
// A uniform grid over the drawing, so each collision test reads only the
// boxes near the candidate and placement stays near-linear in edge count.
function BoxGrid(){this.cells={};}
BoxGrid.prototype.CELL=32;
BoxGrid.prototype.each=function(b,fn){
  var c=this.CELL,x0=Math.floor(b.x/c),x1=Math.floor((b.x+b.w)/c),y0=Math.floor(b.y/c),y1=Math.floor((b.y+b.h)/c);
  for(var i=x0;i<=x1;i++)for(var j=y0;j<=y1;j++)if(fn(i+','+j))return true;
  return false;
};
BoxGrid.prototype.add=function(b,owner,hard){
  var cells=this.cells,e={b:b,owner:owner||null,hard:!!hard};
  this.each(b,function(k){(cells[k]||(cells[k]=[])).push(e);return false;});
};
// True when b meets a stored box. Line samples owned by `own` are skipped;
// `linesOnly` counts only line samples, and `boxesOnly` counts boxes and the
// lines marked hard (bus, satellite and contextual lines).
BoxGrid.prototype.hits=function(b,own,linesOnly,boxesOnly){
  var cells=this.cells;
  return this.each(b,function(k){
    var list=cells[k];if(!list)return false;
    for(var n=0;n<list.length;n++){
      var e=list[n],o=e.b;
      if(e.owner&&(e.owner===own||(boxesOnly&&!e.hard)))continue;
      if(linesOnly&&!e.owner)continue;
      if(b.x<o.x+o.w&&o.x<b.x+b.w&&b.y<o.y+o.h&&o.y<b.y+b.h)return true;
    }
    return false;
  });
};
function relDesc(path){
  var k=((path&&path.dataset&&path.dataset.rel)||'').split('|');
  var esc=window.visEscape||String;
  return k.length<3?'':esc(k[0])+' '+k[1].replace(/_/g,' ')+' '+esc(k[2]);
}
// Placement runs in three passes — read all geometry, choose every spot,
// then draw — because reading geometry after any drawing forces a fresh
// layout of the whole diagram, which made placement quadratic.
function placeLabels(g,edges,keyHost){
  var svg=g.ownerSVGElement,vb=svg&&svg.viewBox&&svg.viewBox.baseVal;
  var grid=new BoxGrid();
  (g._blockBoxes||[]).forEach(function(b){grid.add(b);});
  var paths=[];
  [].concat(edges||[]).forEach(function(e){paths=paths.concat([].slice.call(e.querySelectorAll('path')));});
  paths.forEach(function(p){
    // A hollow edge's inner line belongs to the edge it is drawn inside.
    var owner=p.hasAttribute('data-inner')?p.previousElementSibling:p;
    // Bus, satellite and contextual lines may never pass under a plate.
    var hard=!!(p.dataset&&(p.dataset.trunk||p.dataset.sat));
    try{
      var n=p.getTotalLength();
      for(var s=0;s<=n;s+=3){var q=p.getPointAtLength(s);grid.add({x:q.x-0.5,y:q.y-0.5,w:1,h:1},owner,hard);}
      if(p.getAttribute('marker-end')){
        var a=p.getPointAtLength(n),b=p.getPointAtLength(Math.max(0,n-10));
        grid.add({x:Math.min(a.x,b.x)-1,y:Math.min(a.y,b.y)-5,w:Math.abs(a.x-b.x)+2,h:Math.abs(a.y-b.y)+10});
      }
    }catch(e){}
  });
  // Where each chain edge's arrowhead lands, and the record it points at.
  var ends=[];
  paths.forEach(function(p){
    if(!p.getAttribute('marker-end')||!p.dataset.rel||p.dataset.sat)return;
    try{var e=p.getPointAtLength(p.getTotalLength());
      ends.push({x:e.x,y:e.y,to:p.dataset.rel.split('|')[2]});}catch(x){}
  });
  var jobs=(g._defer||[]).map(function(args){
    var rel=args[2]&&args[2].dataset&&args[2].dataset.rel;
    return{txt:args[0],fill:args[1],path:args[2],pts:edgePoints(args[2]),
      to:rel&&!args[2].dataset.sat?rel.split('|')[2]:null,ends:ends};
  });
  g._defer=[];
  // Measure each distinct label text once, in one batch.
  var widths={},probes=[];
  var measure=function(s){
    if(s in widths)return;widths[s]=0;
    var m=svgEl('text');sa(m,'font-size','10');sa(m,'font-weight','600');
    m.textContent=s;g.appendChild(m);probes.push([s,m]);
  };
  jobs.forEach(function(j){if(j.txt.length<=MAX_LABEL)measure(j.txt);});
  jobs.forEach(function(j,n){measure(String(n+1));});
  probes.forEach(function(e){try{widths[e[0]]=e[1].getComputedTextLength();}catch(x){}});
  probes.forEach(function(e){g.removeChild(e[1]);});
  // Choose spots: the label itself, else a numbered marker.
  var key=[],draws=[];
  // A label is drawn whole or not at all: one that is too long, or has no
  // clear spot, becomes a numbered marker with its full text in the key.
  jobs.forEach(function(j){
    var whole=j.txt.length<=MAX_LABEL;
    var box=whole&&chooseSpot(grid,vb,j,labelWidth(j.txt,widths));
    if(box){draws.push({j:j,shown:j.txt,box:box});return;}
    var num=String(key.length+1),mbox=chooseSpot(grid,vb,j,labelWidth(num,widths));
    if(mbox)draws.push({j:j,shown:num,box:mbox});
    key.push({num:num,txt:j.txt,desc:relDesc(j.path),marked:!!mbox});
  });
  draws.forEach(function(d){drawLabel(g,d.j,d.shown,d.box);});
  if(key.length&&keyHost){
    var ol=document.createElement('ol');ol.className='lineage-key';
    ol.setAttribute('aria-label','Edge labels shown as numbers');
    key.forEach(function(k){
      var li=document.createElement('li');li.value=+k.num;
      li.textContent=k.txt+(k.desc?' — '+k.desc:'')+(k.marked?'':' (no room to mark it on the diagram)');
      ol.appendChild(li);
    });
    keyHost.appendChild(ol);
  }
}
function labelWidth(s,widths){return Math.ceil((widths[s]||s.length*6)+8);}
// Points every 4 px along the half of an edge nearest its arrowhead, with
// their unit normals, nearest the three-quarter point first: a label then
// sits by the record its edge points at, not by a neighbour's.
function edgePoints(path){
  var len=0;try{len=path&&path.getTotalLength?path.getTotalLength():0;}catch(e){}
  if(!len)return[];
  var pts=[];
  for(var s=0;s<=len;s+=4){var q=path.getPointAtLength(s);pts.push({s:s,x:q.x,y:q.y});}
  pts.forEach(function(e,n){
    var a=pts[Math.max(0,n-1)],c=pts[Math.min(pts.length-1,n+1)];
    var dx=c.x-a.x,dy=c.y-a.y,dl=Math.sqrt(dx*dx+dy*dy)||1;e.nx=-dy/dl;e.ny=dx/dl;
  });
  return pts.filter(function(e){return e.s>=len/2;})
    .sort(function(a,b){return Math.abs(a.s-len*0.75)-Math.abs(b.s-len*0.75);});
}
// The first pass wants a spot no other line touches: the plate centred on its
// line, then just above or below it, within one plate height. Where crossing
// lines leave no such spot (a fan-in), the second pass centres the plate on
// its own line and lets other lines pass under it, but none within 7 px of
// its centre, so the line through its middle is always the one it names.
function chooseSpot(grid,vb,j,w){
  var h=LABEL_H,path=j.path,pts=j.pts;
  var outside=function(b){return vb&&vb.width>0&&(b.x<vb.x||b.y<vb.y||
    b.x+b.w>vb.x+vb.width||b.y+b.h>vb.y+vb.height);};
  var clearNear=function(cx,cy,r){return!grid.hits({x:cx-r,y:cy-r,w:2*r,h:2*r},path,true);};
  // A chain-edge label must sit nearest an arrowhead at its own record, so it
  // is never read as another record's scope.
  var byOwnRecord=function(cx,cy){
    if(!j.to||!j.ends.length)return true;
    var best=null,bd=Infinity;
    for(var e=0;e<j.ends.length;e++){
      var d=Math.hypot(j.ends[e].x-cx,j.ends[e].y-cy);if(d<bd){bd=d;best=j.ends[e];}
    }
    return best.to===j.to;
  };
  var search=function(offs,strict){
    // On the line anywhere in the half first, then beside it.
    for(var k=0;k<offs.length;k++){
      for(var i=0;i<pts.length;i++){
        var cx=pts[i].x+pts[i].nx*offs[k],cy=pts[i].y+pts[i].ny*offs[k];
        var b={x:cx-w/2,y:cy-h/2,w:w,h:h};
        if(outside(b)||grid.hits(b,path,false,!strict))continue;
        if(strict?offs[k]&&!clearNear(cx,cy,Math.abs(offs[k])+1):!clearNear(cx,cy,7))continue;
        if(!byOwnRecord(cx,cy))continue;
        return b;
      }
    }
    return null;
  };
  var box=search([0,h/2+2,-(h/2+2),h,-h],true)||search([0],false);
  if(box)grid.add(box);
  return box;
}
function drawLabel(g,j,shown,box){
  var fill=j.fill||'#4b5563';
  var plate=svgEl('rect');
  sa(plate,'x',box.x);sa(plate,'y',box.y);sa(plate,'width',box.w);sa(plate,'height',box.h);
  sa(plate,'rx','3');sa(plate,'fill','#ffffff');sa(plate,'stroke',fill);sa(plate,'stroke-width','0.75');
  g.appendChild(plate);
  var t=svgEl('text');
  if(j.path.dataset&&j.path.dataset.rel)t.dataset.for=j.path.dataset.rel;
  sa(t,'x',box.x+box.w/2);sa(t,'y',box.y+box.h/2);
  sa(t,'dominant-baseline','middle');sa(t,'text-anchor','middle');sa(t,'font-size','10');
  sa(t,'font-weight','600');sa(t,'fill',fill);sa(t,'class','edge-label');
  t.appendChild(document.createTextNode(shown));
  g.appendChild(t);
}

// '' (in force), 'part' (superseded in part) or 'full' (fully superseded).
function supState(rec){
  var supB=(rec&&rec.superseded_by)||[];
  return supB.some(function(s){return !s.partial;})?'full':supB.length?'part':'';
}
var SUP_TEXT={'':'',part:', superseded in part',full:', superseded'};

// ── Node group (<g role="button">)
function drawNode(svg,nid,x,y,nw,nh,rec,isSel,isCyc,isOld,scale,navigate_fn){
  var lcv=(rec&&rec.lifecycle&&!rec.lifecycle.missing&&(rec.lifecycle.display_value||rec.lifecycle.raw_value))||'(missing)';
  var titleTxt=(rec&&(rec.display_title||rec.title))||'';
  var maxT=Math.max(Math.floor(nw/7)-2,8);
  var shortT=titleTxt.length>maxT?titleTxt.slice(0,maxT-1)+'…':titleTxt;
  var g=svgEl('g');
  sa(g,'role','button');sa(g,'tabindex',isSel?'0':'-1');
  sa(g,'aria-label',nid+': '+titleTxt+', '+lcv+(SUP_TEXT[isOld||'']||''));
  g.dataset.nodeId=nid;
  var rect=svgEl('rect');
  sa(rect,'x',x);sa(rect,'y',y);sa(rect,'width',nw);sa(rect,'height',nh);sa(rect,'rx','6');
  if(isSel){
    sa(rect,'fill','#1d4ed8');sa(rect,'stroke','#1e40af');sa(rect,'stroke-width','2');
  }else if(isOld){
    sa(rect,'fill','none');sa(rect,'stroke','#9ca3af');
    sa(rect,'stroke-width','1.5');sa(rect,'stroke-dasharray','4 3');
  }else{
    sa(rect,'fill','#f8faff');sa(rect,'stroke','#c7d2fe');sa(rect,'stroke-width','1.5');
  }
  g.appendChild(rect);
  if(isSel&&isOld){
    // The selected record keeps its supersession cue as a dashed outer ring.
    var ring=svgEl('rect');sa(ring,'class','sup-ring');
    sa(ring,'x',x-4);sa(ring,'y',y-4);sa(ring,'width',nw+8);sa(ring,'height',nh+8);sa(ring,'rx','8');
    sa(ring,'fill','none');sa(ring,'stroke','#6b7280');sa(ring,'stroke-width','1.5');sa(ring,'stroke-dasharray','4 3');
    g.appendChild(ring);
  }
  var fs1=Math.max(9,Math.round(10*scale)),fs2=Math.max(8,Math.round(9*scale));
  var idt=svgEl('text');
  sa(idt,'x',x+6);sa(idt,'y',y+nh*0.42);
  sa(idt,'font-family','ui-monospace,monospace');sa(idt,'font-size',fs1+'');
  sa(idt,'fill',isSel?'#fff':'#1d4ed8');
  if(isOld==='full')sa(idt,'text-decoration','line-through');
  else if(isOld==='part')sa(idt,'text-decoration','underline');
  idt.textContent=nid;g.appendChild(idt);
  if(nh>28){
    var ttt=svgEl('text');
    sa(ttt,'x',x+6);sa(ttt,'y',y+nh*0.75);
    sa(ttt,'font-size',fs2+'');
    sa(ttt,'fill',isSel?'rgba(255,255,255,.75)':'#4b5563');
    ttt.textContent=shortT;g.appendChild(ttt);
  }
  if(isCyc){
    var cb=svgEl('text');
    sa(cb,'x',x+nw-4);sa(cb,'y',y+fs1+2);
    sa(cb,'text-anchor','end');sa(cb,'font-size',fs2+'');sa(cb,'fill','#b45309');
    cb.textContent='cycle';g.appendChild(cb);
  }
  var titleEl=svgEl('title');titleEl.textContent=nid+': '+titleTxt+' ('+lcv+')';
  g.appendChild(titleEl);
  // Visible focus ring
  // A dark outer ring guarantees 3:1 on the light canvas; the amber inner ring
  // keeps the familiar focus colour. Both sit outside the supersession ring.
  var fr=svgEl('g');fr.setAttribute('class','focus-ring');
  var fo=svgEl('rect');
  sa(fo,'x',x-9);sa(fo,'y',y-9);sa(fo,'width',nw+18);sa(fo,'height',nh+18);
  sa(fo,'rx','12');sa(fo,'fill','none');sa(fo,'stroke','#111827');sa(fo,'stroke-width','2');
  var fi=svgEl('rect');
  sa(fi,'x',x-7);sa(fi,'y',y-7);sa(fi,'width',nw+14);sa(fi,'height',nh+14);
  sa(fi,'rx','10');sa(fi,'fill','none');sa(fi,'stroke','#f59e0b');sa(fi,'stroke-width','2');
  fr.appendChild(fo);fr.appendChild(fi);
  fr.style.display='none';g.appendChild(fr);
  g.addEventListener('click',function(){navigate_fn('graph',nid);});
  g.addEventListener('keydown',function(e){
    if((e.key==='Enter'||e.key===' ')&&!e.shiftKey){e.preventDefault();navigate_fn('graph',nid);}
    else if(e.key==='Enter'&&e.shiftKey){e.preventDefault();navigate_fn('detail',nid);}
  });
  g.addEventListener('focus',function(){fr.style.display='';});
  g.addEventListener('blur',function(){fr.style.display='none';});
  svg.appendChild(g);
  return g;
}

// ── Roving tabindex: arrow keys navigate between connected nodes
function rovingTab(nodeGs,np,chainCheckedRels){
  var nodeMap={};
  nodeGs.forEach(function(g){nodeMap[g.dataset.nodeId]=g;});
  nodeGs.forEach(function(g){
    g.addEventListener('keydown',function(e){
      var curId=g.dataset.nodeId,curPos=np[curId];
      if(!curPos)return;
      var target=null,bestDist=Infinity;
      // ArrowRight/Down → newer nodes (higher col, or same col lower row in cycle)
      // ArrowLeft/Up → older nodes (lower col)
      var goRight=(e.key==='ArrowRight'||e.key==='ArrowDown');
      var goLeft=(e.key==='ArrowLeft'||e.key==='ArrowUp');
      if(!goRight&&!goLeft)return;
      chainCheckedRels.forEach(function(r){
        var tId=null;
        if(goRight&&r.to===curId&&nodeMap[r.from])tId=r.from;   // r.from is newer
        else if(goLeft&&r.from===curId&&nodeMap[r.to])tId=r.to; // r.to is older
        if(!tId)return;
        var tp=np[tId];if(!tp)return;
        var dist=Math.abs(tp.col-curPos.col)*100+Math.abs(tp.row-curPos.row);
        if(dist<bestDist){bestDist=dist;target=nodeMap[tId];}
      });
      // Also allow ArrowDown within same-col cycle members
      if(!target&&(e.key==='ArrowDown'||e.key==='ArrowRight')){
        nodeGs.forEach(function(ng){
          var tp=np[ng.dataset.nodeId];
          if(!tp)return;
          if(tp.col===curPos.col&&tp.row===curPos.row+1){
            var dist=1;
            if(dist<bestDist){bestDist=dist;target=ng;}
          }
        });
      }
      if(!target&&(e.key==='ArrowUp'||e.key==='ArrowLeft')){
        nodeGs.forEach(function(ng){
          var tp=np[ng.dataset.nodeId];
          if(!tp)return;
          if(tp.col===curPos.col&&tp.row===curPos.row-1){
            var dist=1;
            if(dist<bestDist){bestDist=dist;target=ng;}
          }
        });
      }
      if(target){
        e.preventDefault();
        nodeGs.forEach(function(ng){ng.setAttribute('tabindex','-1');});
        target.setAttribute('tabindex','0');target.focus();
      }
    });
  });
}

// ── Legend
function appendLegend(container){
  var d=document.createElement('details');d.className='lineage-legend';
  var s=document.createElement('summary');s.textContent='Diagram legend';d.appendChild(s);
  var ul=document.createElement('ul');
  ['Checked full: solid line, filled arrowhead',
   'Checked partial: hollow double line + "in part" label with its scope (e.g. D3)',
   'Cycle: dashed arc, "cycle" label on edge',
   'One-sided (unresolved): dashed line, open arrowhead, "one-sided" label',
   'Caller-asserted guidance: dash-dot line, hollow arrowhead, "asserted" label',
   'Contextual (related): thin dotted muted line (hidden by default)',
   'Dashed node border: the record is superseded (fully or in part)',
   'Struck-through ID: fully superseded; underlined ID: superseded in part',
  ].forEach(function(txt){
    var li=document.createElement('li');li.textContent=txt;ul.appendChild(li);
  });
  d.appendChild(ul);container.appendChild(d);
}

// ── Relationships drawn around the chain for the selected record. The diagram
// and its text equivalent both read this one definition, so they cannot drift.
function extrasFor(selectedId,cn,allRels){
  var touches=function(r){return r.from===selectedId||r.to===selectedId;};
  var peer=function(r){return r.from===selectedId?r.to:r.from;};
  return{
    oneSided:allRels.filter(function(r){
      return r.from===selectedId&&r.trust_class==='candidate'&&r.resolution_state==='unresolved'
        &&(r.relation==='supersedes'||r.relation==='supersedes_in_part')
        &&(!r.to||cn.indexOf(r.to)<0);}),
    asserted:allRels.filter(function(r){
      return r.trust_class==='navigation_only'&&touches(r);}),
    contextual:allRels.filter(function(r){
      return r.trust_class==='contextual'&&touches(r);})
  };
}

// Identity of a relationship, stamped on its diagram element and its text line.
function relKey(r){return (r.from||'?')+'|'+r.relation+'|'+(r.to||'?')+'|'+r.trust_class;}

// One line of text for a relationship, using escaped display copies.
function relText(r){
  var f=r.display_from||r.from,t=r.display_to||r.to||'?';
  if(r.trust_class==='candidate')return f+' '+r.relation.replace(/_/g,' ')+' '+t+' [one-sided · unresolved]';
  if(r.trust_class==='navigation_only')return f+' → '+t+' [navigation_only · caller_asserted]'+
    (r.display_raw_value?': '+r.display_raw_value:'');
  return f+' related to '+t+' [contextual · '+r.resolution_state+']';
}

function appendExtrasText(ul,extras){
  ['oneSided','asserted','contextual'].forEach(function(k){
    extras[k].forEach(function(r){
      var li=document.createElement('li');li.className='lt-rel lt-'+k;li.dataset.rel=relKey(r);
      li.textContent=relText(r);ul.appendChild(li);});});
}

// ── Text equivalent (synchronized list of nodes and relationships)
function appendTextEquiv(container,chainNodes,chainCheckedRels,extras,allRecords,sccList,n2s,navigate){
  var det=document.createElement('details');det.className='lineage-text';
  var s=document.createElement('summary');s.textContent='Lineage as text';det.appendChild(s);
  // On narrow screens the scaled-down diagram is hard to read, so lead with the text.
  if(window.matchMedia&&window.matchMedia('(max-width:40rem)').matches)det.open=true;
  var ul=document.createElement('ul');
  chainNodes.forEach(function(nid){
    var rec=allRecords.find(function(r){return r.id===nid;});
    var lcv=(rec&&rec.lifecycle&&!rec.lifecycle.missing&&(rec.lifecycle.display_value||rec.lifecycle.raw_value))||'(missing)';
    var isCyc=sccList&&n2s&&sccList[n2s[nid]]&&sccList[n2s[nid]].length>1;
    var li=document.createElement('li');li.className='lt-node';
    // Each node is a button, so the text list is a full alternative to the diagram.
    var b=document.createElement('button');b.type='button';b.className='lt-node-btn';
    b.textContent=nid+': '+((rec&&(rec.display_title||rec.title))||'')+' ['+lcv+']'+(isCyc?' [cycle member]':'');
    b.addEventListener('click',function(){navigate('graph',nid);});
    li.appendChild(b);ul.appendChild(li);
  });
  chainCheckedRels.forEach(function(r){
    if(chainNodes.indexOf(r.from)<0||chainNodes.indexOf(r.to)<0)return;
    var scope=r.scope&&r.scope.length?r.scope.join(', '):'scope not stated';
    var rel=r.relation==='supersedes_in_part'?'supersedes in part ('+scope+')':'supersedes';
    var isCyc=n2s&&n2s[r.from]===n2s[r.to];
    var li=document.createElement('li');li.className='lt-rel';li.dataset.rel=relKey(r);
    li.textContent=r.from+' '+rel+' '+r.to+(isCyc?' [cycle]':'');
    ul.appendChild(li);
  });
  appendExtrasText(ul,extras);
  det.appendChild(ul);container.appendChild(det);
}

// ── Render focused lineage for one selected record
function renderFocused(container,selectedId,allRels,allRecords,navigate){
  var checkedRels=allRels.filter(function(r){return r.trust_class==='checked';});
  var cn=chainOf(selectedId,allRels);

  if(!allRecords.some(function(r){return r.id===selectedId;})){
    var miss=document.createElement('p');miss.className='empty-msg';
    var shown=(window.visEscape||String)(String(selectedId));
    if(shown.length>64)shown=shown.slice(0,63)+'…';
    miss.textContent=shown+' is not in this export.';
    container.appendChild(miss);return;
  }
  if(cn.length<2){
    var note=document.createElement('p');note.className='graph-note';
    note.textContent=selectedId+' has no checked supersession lineage.';
    container.appendChild(note);
    var ex0=extrasFor(selectedId,[selectedId],allRels);
    var ul0=document.createElement('ul');ul0.className='lineage-text-list';
    appendExtrasText(ul0,ex0);
    if(ul0.childNodes.length)container.appendChild(ul0);
    return;
  }

  var chainCheckedRels=checkedRels.filter(function(r){
    return cn.indexOf(r.from)>=0&&cn.indexOf(r.to)>=0;
  });
  var pr=positions(cn,chainCheckedRels);
  var np=pr.nodePos,sccList=pr.sccList,n2s=pr.n2s,maxL=pr.maxL;

  var maxRow=0;
  cn.forEach(function(n){if(np[n]&&np[n].row>maxRow)maxRow=np[n].row;});

  // Pre-count satellite nodes to size the SVG
  var extras=extrasFor(selectedId,cn,allRels);
  var unresRels=extras.oneSided,assertedRels=extras.asserted,ctxRels=extras.contextual;
  var satAsserted=assertedRels.filter(function(r){
    return cn.indexOf(r.from===selectedId?r.to:r.from)<0;});
  var satCount=unresRels.length+satAsserted.length;
  var ctxCount=Object.keys(ctxRels.reduce(function(acc,r){
    var pid=r.from===selectedId?r.to:r.from;acc[pid]=1;return acc;},{})  ).length;
  var hasSat=satCount>0||ctxCount>0;
  var svgW=PX*2+maxL*(NW+XG)+NW+(hasSat?XG+SAT_GAP+Math.round(NW*0.8):0);
  var chainH=PY*2+(maxRow+1)*(NH+YG)-YG+PY;
  var svgH=Math.max(chainH,PY+satCount*(NH+YG)+PY);
  // Hidden contextual peers add height only while they are shown.
  var svgHctx=Math.max(svgH,PY+(satCount*(NH+YG))+ctxCount*(Math.round(NH*0.75)+YG)+PY);
  svgW=Math.max(svgW,300);svgH=Math.max(svgH,100);svgHctx=Math.max(svgHctx,svgH);

  var pfx='lg'+selectedId.replace(/\W/g,'').slice(0,10)+'-';
  var capId=pfx+'cap';

  // Caption (visible, referenced by aria-labelledby)
  var cap=document.createElement('div');cap.className='lineage-caption';
  cap.id=capId;
  cap.textContent='Lineage: '+selectedId+' · '+cn.length+' records in chain';
  container.appendChild(cap);

  var svg=svgEl('svg');
  sa(svg,'role','group');sa(svg,'aria-labelledby',capId);
  sa(svg,'width',svgW);sa(svg,'height',svgH);sa(svg,'viewBox','0 0 '+svgW+' '+svgH);
  addDefs(svg,pfx);

  // Edge group (behind nodes)
  var lg=svgEl('g');sa(lg,'aria-hidden','true');
  // Labels never cover a node box or its supersession ring (4 px out).
  lg._blockBoxes=cn.filter(function(n){return np[n];}).map(function(n){
    return{x:PX+np[n].col*(NW+XG)-5,y:PY+np[n].row*(NH+YG)-5,w:NW+10,h:NH+10};});
  var eg=svgEl('g');sa(eg,'aria-hidden','true');

  // Draw checked edges within the chain
  var ports=edgePorts(chainCheckedRels,np,NH);
  chainCheckedRels.forEach(function(r,ri){
    var fp=np[r.from],tp=np[r.to];
    if(!fp||!tp)return;
    var isCyc=fp.scc===tp.scc;
    var isPartial=r.relation==='supersedes_in_part';
    var stroke=isPartial?'#1d4ed8':'#374151';
    if(isCyc){
      // Arc to the right of the nodes
      var xn=PX+fp.col*(NW+XG)+NW+3;
      var y1c=PY+fp.row*(NH+YG)+NH/2;
      var y2c=PY+tp.row*(NH+YG)+NH/2;
      // The two arcs of a two-record cycle bulge by different amounts, so
      // each keeps its own line and label.
      var twin=chainCheckedRels.some(function(o){return o.from===r.to&&o.to===r.from;});
      var arcX=xn+(twin&&r.from>r.to?80:50),arcY=(y1c+y2c)/2;
      var arc=svgEl('path');
      sa(arc,'d','M '+xn+','+y1c+' Q '+arcX+','+arcY+' '+xn+','+y2c);
      sa(arc,'fill','none');sa(arc,'stroke','#374151');sa(arc,'stroke-width','1.5');
      sa(arc,'stroke-dasharray','8 4');sa(arc,'marker-end','url(#'+pfx+'af)');
      arc.dataset.rel=relKey(r);eg.appendChild(arc);
      edgeLabel(lg,xn,y1c,xn,y2c,'cycle','#b45309',arc);
    }else{
      // FROM is newer (right), TO is older (left)
      var x1=PX+fp.col*(NW+XG),y1=PY+fp.row*(NH+YG)+ports[ri].y1;
      var x2=PX+tp.col*(NW+XG)+NW,y2=PY+tp.row*(NH+YG)+ports[ri].y2;
      var edgePath=drawEdge(eg,x1,y1,x2,y2,stroke,isPartial?'4':'2',null,'url(#'+pfx+'af)');
      edgePath.dataset.rel=relKey(r);
      // Partial supersession reads as a hollow double line, not colour alone.
      if(isPartial)drawEdge(eg,x1,y1,x2,y2,'#ffffff','1.5',null,null).setAttribute('data-inner','part');
      if(isPartial){
        var sc2='in part · '+(r.scope&&r.scope.length?r.scope.join(', '):'scope not stated');
        edgeLabel(lg,x1,y1,x2,y2,sc2,'#1d4ed8',edgePath);
      }
    }
  });

  // Satellite column x
  var satX=PX+(maxL+1)*(NW+XG)+SAT_GAP;
  var satY=PY;
  var sp=np[selectedId];
  // Satellites (one-sided targets, asserted peers outside the chain and,
  // when shown, contextual peers) hang off one thin neutral bus. It drops
  // from the selected node's bottom edge into the row gap below it, runs
  // along that gap and then down the gutter beyond the last column, where no
  // chain edge runs, so it crosses chain edges but never lies along one. Each
  // satellite gets a short branch in its relationship's style, carrying its
  // label; an assertion into the selected record points back along the bus.
  var sats=[];
  unresRels.forEach(function(r){sats.push({r:r,kind:'one'});});
  assertedRels.forEach(function(r){
    var peerId=r.from===selectedId?r.to:r.from;
    if(!np[peerId])sats.push({r:r,kind:r.from===selectedId?'as':'asIn'});
  });
  var SAT_STYLE={
    one:{box:'#9ca3af',line:'#9ca3af',dash:'6 4',mark:'ao',label:'one-sided',fill:'#4b5563',text:'#4b5563'},
    as:{box:'#a78bfa',line:'#a78bfa',dash:'8 3 2 3',mark:'ah',label:'asserted',fill:'#6d28d9',text:'#6d28d9'},
    asIn:{box:'#a78bfa',line:'#a78bfa',dash:'8 3 2 3',mark:'ah',label:'asserted',fill:'#6d28d9',text:'#6d28d9'}
  };
  sats.forEach(function(s){
    var st0=SAT_STYLE[s.kind],sx=satX,sy=satY;satY+=NH+YG;s.mid=sy+NH/2;
    var sg=svgEl('rect');sa(sg,'x',sx);sa(sg,'y',sy);sa(sg,'width',Math.round(NW*0.78));sa(sg,'height',NH);
    sa(sg,'rx','4');sa(sg,'fill','none');sa(sg,'stroke',st0.box);sa(sg,'stroke-dasharray',s.kind==='one'?'5 3':st0.dash);
    eg.appendChild(sg);
    lg._blockBoxes.push({x:sx-2,y:sy-2,w:Math.round(NW*0.78)+4,h:NH+4});
    var st=svgEl('text');sa(st,'x',sx+5);sa(st,'y',sy+NH/2);
    sa(st,'dominant-baseline','middle');sa(st,'font-size','10');sa(st,'fill',st0.text);
    var r=s.r;
    st.textContent=(s.kind==='one'?(r.display_to||r.to):
      (r.from===selectedId?(r.display_to||r.to):(r.display_from||r.from)))||'?';
    eg.appendChild(st);
  });
  var busX=satX-SAT_BRANCH,busY=sp?PY+(sp.row+1)*(NH+YG)-YG/2:0;
  // The bus as a path in group g, spanning the satellite midpoints ys.
  var bus=function(ys,g){
    var sx=PX+sp.col*(NW+XG)+NW-12,sy=PY+sp.row*(NH+YG)+NH;
    var lo=busY,hi=busY;
    for(var k=0;k<ys.length;k++){if(ys[k]<lo)lo=ys[k];if(ys[k]>hi)hi=ys[k];}
    var bp=svgEl('path');
    sa(bp,'d','M '+sx+','+sy+' L '+sx+','+busY+' L '+busX+','+busY+
      ' M '+busX+','+lo+' L '+busX+','+hi);
    sa(bp,'fill','none');sa(bp,'stroke','#9ca3af');sa(bp,'stroke-width','1');
    bp.dataset.trunk='bus';g.appendChild(bp);
  };
  if(sp&&sats.length)bus(sats.map(function(s){return s.mid;}),eg);
  if(sp)['one','as','asIn'].forEach(function(kind){
    var mine=sats.filter(function(s){return s.kind===kind;});
    if(!mine.length)return;
    var st0=SAT_STYLE[kind];
    mine.forEach(function(s){
      var br=svgEl('path');
      sa(br,'d',kind==='asIn'?'M '+satX+','+s.mid+' L '+busX+','+s.mid:'M '+busX+','+s.mid+' L '+satX+','+s.mid);
      sa(br,'fill','none');sa(br,'stroke',st0.line);sa(br,'stroke-width','1.5');
      sa(br,'stroke-dasharray',st0.dash);sa(br,'marker-end','url(#'+pfx+st0.mark+')');
      br.dataset.rel=relKey(s.r);br.dataset.sat=kind;eg.appendChild(br);
      edgeLabel(lg,busX,s.mid,satX,s.mid,st0.label,st0.fill,br);
    });
  });

  // Caller-asserted edges between two chain members route through the free
  // gutter right of each column and the free gap above the target row, so the
  // edge never passes beneath another node.
  assertedRels.forEach(function(r){
    var peerId=r.from===selectedId?r.to:r.from;
    if(!np[peerId]||!sp)return;
    var fpA=np[r.from],tpA=np[r.to];
    var fx=PX+fpA.col*(NW+XG)+NW,fy=PY+fpA.row*(NH+YG)+NH*0.7;
    var tx=PX+tpA.col*(NW+XG)+NW,ty=PY+tpA.row*(NH+YG)+NH*0.3;
    var gf=fx+XG*0.3,gt=tx+XG*0.3,gapY=PY+tpA.row*(NH+YG)-YG/2;
    if(tpA.row===0)gapY=PY/2;
    // The row gap below the selected record carries the satellite bus; use
    // the gap below the target instead, so the two never run side by side.
    if((sats.length||ctxCount)&&Math.abs(gapY-busY)<1)gapY=PY+(tpA.row+1)*(NH+YG)-YG/2;
    var ap=svgEl('path');
    // Two records in one column share a gutter: run straight down it.
    sa(ap,'d',fpA.col===tpA.col?'M '+fx+','+fy+' L '+gf+','+fy+' L '+gf+','+ty+' L '+tx+','+ty:
      'M '+fx+','+fy+' L '+gf+','+fy+' L '+gf+','+gapY+' L '+gt+','+gapY+
      ' L '+gt+','+ty+' L '+tx+','+ty);
    sa(ap,'fill','none');sa(ap,'stroke','#7c3aed');sa(ap,'stroke-width','1.5');
    sa(ap,'stroke-dasharray','8 3 2 3');sa(ap,'marker-end','url(#'+pfx+'ah)');
    ap.dataset.rel=relKey(r);eg.appendChild(ap);
    edgeLabel(lg,fx,fy,gt,ty,'asserted','#7c3aed',ap);
  });

  svg.appendChild(eg);svg.appendChild(lg);

  // Contextual edges (hidden by default, separate group) hang off the same
  // bus. Label placement counts their lines even while hidden, so showing
  // them never puts a line across a label.
  var ctxG=svgEl('g');sa(ctxG,'aria-hidden','true');ctxG.style.display='none';
  var ctxX=satX,ctxY=satY,seenCtx={},ctxNP={},ctxYs=[];
  ctxRels.forEach(function(r){
    var pid=r.from===selectedId?r.to:r.from;
    if(seenCtx[pid])return;
    seenCtx[pid]=1;ctxNP[pid]={x:ctxX,y:ctxY};ctxY+=Math.round(NH*0.75)+YG;
    var sr=svgEl('rect');sa(sr,'x',ctxX);sa(sr,'y',ctxNP[pid].y);
    sa(sr,'width',Math.round(NW*0.82));sa(sr,'height',Math.round(NH*0.75));
    sa(sr,'rx','4');sa(sr,'fill','#f9fafb');sa(sr,'stroke','#9ca3af');sa(sr,'stroke-dasharray','2 3');
    ctxG.appendChild(sr);
    var st=svgEl('text');sa(st,'x',ctxX+5);sa(st,'y',ctxNP[pid].y+Math.round(NH*0.4));
    sa(st,'dominant-baseline','middle');sa(st,'font-size','10');sa(st,'fill','#4b5563');
    st.textContent=pid;ctxG.appendChild(st);
    ctxYs.push(ctxNP[pid].y+Math.round(NH*0.4));
  });
  if(sp&&ctxYs.length){
    // A hidden copy of the bus, so contextual peers have one when shown alone.
    bus(ctxYs,ctxG);
    var clx=busX;
    ctxRels.forEach(function(r){
      var cp=ctxNP[r.from===selectedId?r.to:r.from];if(!cp)return;
      var cy=cp.y+Math.round(NH*0.4);
      var ep=svgEl('path');
      sa(ep,'d','M '+clx+','+cy+' L '+cp.x+','+cy);
      sa(ep,'fill','none');sa(ep,'stroke','#9ca3af');sa(ep,'stroke-width','1');
      sa(ep,'stroke-dasharray','2 3');ep.dataset.rel=relKey(r);ep.dataset.sat='ctx';ctxG.appendChild(ep);
    });
  }
  svg.appendChild(ctxG);

  // Node groups
  var nodeGs=[],nodeMap={};
  cn.forEach(function(nid){
    var p=np[nid];if(!p)return;
    var rec=allRecords.find(function(r){return r.id===nid;});
    var x=PX+p.col*(NW+XG),y=PY+p.row*(NH+YG);
    var isSel=nid===selectedId;
    var isOld=supState(rec);
    var isCyc=sccList&&sccList[p.scc]&&sccList[p.scc].length>1;
    var g=drawNode(svg,nid,x,y,NW,NH,rec,isSel,isCyc,isOld,1,navigate);
    nodeGs.push(g);nodeMap[nid]=g;
  });
  rovingTab(nodeGs,np,chainCheckedRels);

  // Scrollable wrapper
  var wrap=document.createElement('div');
  var axis=document.createElement('p');axis.className='lineage-axis';
  axis.textContent='← Older (superseded)  ·  arrows read “supersedes”  ·  Newer (superseding) →';
  container.appendChild(axis);
  wrap.className='lineage-wrap';wrap.style.overflowX='auto';wrap.style.maxWidth='100%';
  wrap.appendChild(svg);container.appendChild(wrap);
  placeLabels(lg,[eg,ctxG],container);

  // Contextual toggle
  if(ctxRels.length>0){
    var ctxBtn=document.createElement('button');
    ctxBtn.className='ctx-toggle pill-btn';
    ctxBtn.setAttribute('aria-expanded','false');
    ctxBtn.textContent='Show '+ctxRels.length+' contextual link'+(ctxRels.length!==1?'s':'');
    var shown=false;
    ctxBtn.addEventListener('click',function(){
      shown=!shown;
      ctxG.style.display=shown?'':'none';
      var h=shown?svgHctx:svgH;sa(svg,'height',h);sa(svg,'viewBox','0 0 '+svgW+' '+h);
      ctxBtn.setAttribute('aria-expanded',shown?'true':'false');
      ctxBtn.textContent=(shown?'Hide':'Show')+' '+ctxRels.length
        +' contextual link'+(ctxRels.length!==1?'s':'');
    });
    // Above the diagram, so showing the links never moves the focused button.
    container.insertBefore(ctxBtn,wrap);
  }

  appendLegend(container);
  appendTextEquiv(container,cn,chainCheckedRels,extras,allRecords,sccList,n2s,navigate);
}

// ── Atlas: render all chains as small cards
function renderAtlas(container,allRels,allRecords,navigate){
  var chains=allChains(allRels);
  // Sort by size desc, then lowest ordinal in chain
  chains.sort(function(a,b){
    if(b.length!==a.length)return b.length-a.length;
    var minA=a.reduce(function(m,id){return Math.min(m,parseInt(id.replace(/\D/g,''),10)||0);},Infinity);
    var minB=b.reduce(function(m,id){return Math.min(m,parseInt(id.replace(/\D/g,''),10)||0);},Infinity);
    return minA-minB;
  });
  var noChain=allRecords.filter(function(r){
    return!chains.some(function(c){return c.indexOf(r.id)>=0;});
  }).length;
  if(noChain>0){
    var note=document.createElement('p');note.className='graph-note';
    note.textContent=noChain+' record'+(noChain!==1?'s':'')+' with no checked supersession.';
    container.appendChild(note);
  }
  if(!chains.length){
    var empty=document.createElement('p');empty.className='empty-msg';
    empty.textContent='No checked supersession chains in this corpus.';
    container.appendChild(empty);return;
  }
  var scale=0.8;
  var nw=Math.round(NW*scale),nh=Math.round(NH*scale);
  var xg=Math.round(XG*scale),yg=Math.round(YG*scale);
  var grid=document.createElement('div');grid.className='chain-atlas';
  container.appendChild(grid);
  chains.forEach(function(cn){
    var card=document.createElement('div');card.className='chain-card';
    var lbl=document.createElement('div');lbl.className='chain-card-label';
    var cRels=allRels.filter(function(r){
      return r.trust_class==='checked'&&cn.indexOf(r.from)>=0&&cn.indexOf(r.to)>=0;
    });
    var pr2=positions(cn,cRels);
    var np2=pr2.nodePos,sl2=pr2.sccList,maxL2=pr2.maxL;
    var newest=cn.filter(function(n){return np2[n]&&np2[n].col===maxL2;});
    lbl.textContent=cn.length+' records · newest: '+newest.join(', ');card.appendChild(lbl);
    var maxR=0;
    cn.forEach(function(n){if(np2[n]&&np2[n].row>maxR)maxR=np2[n].row;});
    var hasCyc2=cn.some(function(n){return sl2&&np2[n]&&sl2[np2[n].scc]&&sl2[np2[n].scc].length>1;});
    var sw=PX*2+maxL2*(nw+xg)+nw+(hasCyc2?xg:0),sh=PY*2+(maxR+1)*(nh+yg)-yg;
    sw=Math.max(sw,120);sh=Math.max(sh,60);
    var pfx='at'+cn[0].replace(/\W/g,'').slice(0,8)+'-';
    var svg=svgEl('svg');
    sa(svg,'width',sw);sa(svg,'height',sh);sa(svg,'viewBox','0 0 '+sw+' '+sh);
    sa(svg,'role','group');sa(svg,'aria-label','Chain: '+cn.join(', '));
    addDefs(svg,pfx);
    var eg2=svgEl('g');sa(eg2,'aria-hidden','true');
    var lg2=svgEl('g');sa(lg2,'aria-hidden','true');
    lg2._blockBoxes=cn.filter(function(n){return np2[n];}).map(function(n){
      return{x:PX+np2[n].col*(nw+xg)-5,y:PY+np2[n].row*(nh+yg)-5,w:nw+10,h:nh+10};});
    var ports2=edgePorts(cRels,np2,nh);
    cRels.forEach(function(r,ri){
      var fp=np2[r.from],tp=np2[r.to];if(!fp||!tp)return;
      if(fp.scc===tp.scc){
        // Cycle members share a layer: arc to the right and label it.
        var cx=PX+fp.col*(nw+xg)+nw+3;
        var cy1=PY+fp.row*(nh+yg)+nh/2,cy2=PY+tp.row*(nh+yg)+nh/2;
        var ax=cx+Math.round(xg*0.6),ay=(cy1+cy2)/2;
        var arc=svgEl('path');
        sa(arc,'d','M '+cx+','+cy1+' Q '+ax+','+ay+' '+cx+','+cy2);
        sa(arc,'fill','none');sa(arc,'stroke','#374151');sa(arc,'stroke-width','1.5');
        sa(arc,'stroke-dasharray','6 3');sa(arc,'marker-end','url(#'+pfx+'af)');
        arc.dataset.rel=relKey(r);eg2.appendChild(arc);
        var cl=svgEl('text');sa(cl,'x',ax+3);sa(cl,'y',ay);sa(cl,'font-size','9');
        sa(cl,'fill','#b45309');cl.textContent='cycle';eg2.appendChild(cl);
        return;
      }
      var x1=PX+fp.col*(nw+xg),y1=PY+fp.row*(nh+yg)+ports2[ri].y1;
      var x2=PX+tp.col*(nw+xg)+nw,y2=PY+tp.row*(nh+yg)+ports2[ri].y2;
      var partA=r.relation==='supersedes_in_part';
      var aP=drawEdge(eg2,x1,y1,x2,y2,partA?'#1d4ed8':'#374151',partA?'3.5':'1.5',null,'url(#'+pfx+'af)');
      aP.dataset.rel=relKey(r);
      if(partA){
        drawEdge(eg2,x1,y1,x2,y2,'#ffffff','1.2',null,null).setAttribute('data-inner','part');
        edgeLabel(lg2,x1,y1,x2,y2,'in part','#1d4ed8',aP);
      }
    });
    svg.appendChild(eg2);svg.appendChild(lg2);
    cn.forEach(function(nid){
      var p2=np2[nid];if(!p2)return;
      var rec2=allRecords.find(function(r){return r.id===nid;});
      var x=PX+p2.col*(nw+xg),y=PY+p2.row*(nh+yg);
      var isCyc=sl2&&sl2[p2.scc]&&sl2[p2.scc].length>1;
      var g=drawNode(svg,nid,x,y,nw,nh,rec2,false,isCyc,supState(rec2),scale,navigate);
      sa(g,'tabindex','0');
    });
    var wrap2=document.createElement('div');
    wrap2.className='chain-svg-wrap';wrap2.style.overflowX='auto';
    wrap2.appendChild(svg);card.appendChild(wrap2);
    grid.appendChild(card);
    placeLabels(lg2,eg2,card);
  });
}

return{renderFocused:renderFocused,renderAtlas:renderAtlas};
})();
