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
var NW=160,NH=48,XG=80,YG=16,PX=20,PY=20;

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
  sa(m1,'refX','9');sa(m1,'refY','3.5');sa(m1,'orient','auto');
  var p1=svgEl('polygon');sa(p1,'points','0 0, 10 3.5, 0 7');sa(p1,'fill','#374151');
  m1.appendChild(p1);d.appendChild(m1);
  // Open arrowhead (unresolved)
  var m2=svgEl('marker');
  sa(m2,'id',pfx+'ao');sa(m2,'markerWidth','10');sa(m2,'markerHeight','7');
  sa(m2,'refX','9');sa(m2,'refY','3.5');sa(m2,'orient','auto');
  var p2=svgEl('polyline');sa(p2,'points','0 0, 10 3.5, 0 7');sa(p2,'fill','none');
  sa(p2,'stroke','#9ca3af');sa(p2,'stroke-width','1.5');m2.appendChild(p2);d.appendChild(m2);
  // Hollow arrowhead (asserted)
  var m3=svgEl('marker');
  sa(m3,'id',pfx+'ah');sa(m3,'markerWidth','10');sa(m3,'markerHeight','7');
  sa(m3,'refX','9');sa(m3,'refY','3.5');sa(m3,'orient','auto');
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

// ── Text label above a path midpoint
function edgeLabel(g,x1,y1,x2,y2,txt,fill){
  var t=svgEl('text');
  sa(t,'x',(x1+x2)/2);sa(t,'y',Math.min(y1,y2)-5);
  sa(t,'text-anchor','middle');sa(t,'font-size','10');sa(t,'fill',fill||'#4b5563');
  t.textContent=txt;g.appendChild(t);
}

// ── Node group (<g role="button">)
function drawNode(svg,nid,x,y,nw,nh,rec,isSel,isCyc,isOld,scale,navigate_fn){
  var lcv=(rec&&rec.lifecycle&&!rec.lifecycle.missing&&(rec.lifecycle.display_value||rec.lifecycle.raw_value))||'(missing)';
  var titleTxt=(rec&&(rec.display_title||rec.title))||'';
  var maxT=Math.max(Math.floor(nw/7)-2,8);
  var shortT=titleTxt.length>maxT?titleTxt.slice(0,maxT-1)+'…':titleTxt;
  var g=svgEl('g');
  sa(g,'role','button');sa(g,'tabindex',isSel?'0':'-1');
  sa(g,'aria-label',nid+': '+titleTxt+', '+lcv);
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
  var fs1=Math.round(10*scale),fs2=Math.round(9*scale);
  var idt=svgEl('text');
  sa(idt,'x',x+6);sa(idt,'y',y+nh*0.42);
  sa(idt,'font-family','ui-monospace,monospace');sa(idt,'font-size',fs1+'');
  sa(idt,'fill',isSel?'#fff':'#1d4ed8');
  if(isOld)sa(idt,'text-decoration','line-through');
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
  var fr=svgEl('rect');
  sa(fr,'x',x-3);sa(fr,'y',y-3);sa(fr,'width',nw+6);sa(fr,'height',nh+6);
  sa(fr,'rx','9');sa(fr,'fill','none');sa(fr,'stroke','#f59e0b');sa(fr,'stroke-width','3');
  fr.style.display='none';g.appendChild(fr);
  g.addEventListener('click',function(){navigate_fn('graph',nid);});
  g.addEventListener('keydown',function(e){
    if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();navigate_fn('graph',nid);}
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
   'Checked partial: same + scope chip label (e.g. D3, or "scope not stated")',
   'Cycle: dashed arc, "cycle" label on edge',
   'One-sided (unresolved): dashed line, open arrowhead, "one-sided" label',
   'Caller-asserted guidance: dash-dot line, hollow arrowhead, "asserted" label',
   'Contextual (related): thin dotted muted line (hidden by default)',
  ].forEach(function(txt){
    var li=document.createElement('li');li.textContent=txt;ul.appendChild(li);
  });
  d.appendChild(ul);container.appendChild(d);
}

// ── Text equivalent (synchronized list of nodes and relationships)
function appendTextEquiv(container,chainNodes,chainCheckedRels,allRels,allRecords,selectedId,sccList,n2s){
  var det=document.createElement('details');det.className='lineage-text';
  var s=document.createElement('summary');s.textContent='Lineage as text';det.appendChild(s);
  var ul=document.createElement('ul');
  chainNodes.forEach(function(nid){
    var rec=allRecords.find(function(r){return r.id===nid;});
    var lcv=(rec&&rec.lifecycle&&!rec.lifecycle.missing&&(rec.lifecycle.display_value||rec.lifecycle.raw_value))||'(missing)';
    var isCyc=sccList&&n2s&&sccList[n2s[nid]]&&sccList[n2s[nid]].length>1;
    var li=document.createElement('li');li.className='lt-node';
    li.textContent=nid+': '+((rec&&(rec.display_title||rec.title))||'')+' ['+lcv+']'+(isCyc?' [cycle member]':'');
    ul.appendChild(li);
  });
  chainCheckedRels.forEach(function(r){
    if(chainNodes.indexOf(r.from)<0||chainNodes.indexOf(r.to)<0)return;
    var scope=r.scope&&r.scope.length?r.scope.join(', '):'scope not stated';
    var rel=r.relation==='supersedes_in_part'?'supersedes in part ('+scope+')':'supersedes';
    var isCyc=n2s&&n2s[r.from]===n2s[r.to];
    var li=document.createElement('li');li.className='lt-rel';
    li.textContent=r.from+' '+rel+' '+r.to+(isCyc?' [cycle]':'');
    ul.appendChild(li);
  });
  // Unchecked from selected
  allRels.forEach(function(r){
    if(r.from!==selectedId||r.trust_class!=='candidate'||r.resolution_state!=='unresolved')return;
    var li=document.createElement('li');
    li.textContent=r.from+' → '+(r.to||'?')+' [one-sided · unresolved]';ul.appendChild(li);
  });
  det.appendChild(ul);container.appendChild(det);
}

// ── Render focused lineage for one selected record
function renderFocused(container,selectedId,allRels,allRecords,navigate){
  var checkedRels=allRels.filter(function(r){return r.trust_class==='checked';});
  var cn=chainOf(selectedId,allRels);

  if(cn.length<2){
    var note=document.createElement('p');note.className='graph-note';
    note.textContent=selectedId+' has no checked supersession lineage.';
    container.appendChild(note);
    var unres=allRels.filter(function(r){
      return r.from===selectedId&&r.trust_class==='candidate';
    });
    if(unres.length){
      var ul0=document.createElement('ul');
      unres.forEach(function(r){
        var li=document.createElement('li');
        li.textContent=r.from+' → '+(r.to||'?')+' [one-sided · unresolved]';
        ul0.appendChild(li);
      });
      container.appendChild(ul0);
    }
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
  var unresRels=allRels.filter(function(r){
    return r.from===selectedId&&r.trust_class==='candidate'&&r.resolution_state==='unresolved'
      &&(r.relation==='supersedes'||r.relation==='supersedes_in_part')
      &&(!r.to||cn.indexOf(r.to)<0);
  });
  var assertedRels=allRels.filter(function(r){
    return r.trust_class==='navigation_only'&&(r.from===selectedId||r.to===selectedId)
      &&cn.indexOf(r.from===selectedId?r.to:r.from)<0;
  });
  var ctxRels=allRels.filter(function(r){
    return r.trust_class==='contextual'&&(r.from===selectedId||r.to===selectedId);
  });
  var satCount=unresRels.length+assertedRels.length;
  var ctxCount=Object.keys(ctxRels.reduce(function(acc,r){
    var pid=r.from===selectedId?r.to:r.from;acc[pid]=1;return acc;},{})  ).length;
  var hasSat=satCount>0||ctxCount>0;
  var svgW=PX*2+maxL*(NW+XG)+NW+(hasSat?XG+Math.round(NW*0.8):0);
  var svgH=PY*2+Math.max((maxRow+1)*(NH+YG),Math.max(satCount,ctxCount)*(NH+YG))-YG+PY;
  svgW=Math.max(svgW,300);svgH=Math.max(svgH,100);

  var pfx='lg'+selectedId.replace(/\W/g,'').slice(0,10)+'-';
  var capId=pfx+'cap';

  // Caption (visible, referenced by aria-labelledby)
  var cap=document.createElement('div');cap.className='lineage-caption';
  cap.id=capId;
  cap.textContent='Lineage: '+selectedId+' · '+cn.length+' records in chain';
  container.appendChild(cap);

  var svg=svgEl('svg');
  sa(svg,'role','group');sa(svg,'aria-labelledby',capId);
  sa(svg,'width',svgW);sa(svg,'height',svgH);
  addDefs(svg,pfx);

  // Edge group (behind nodes)
  var eg=svgEl('g');sa(eg,'aria-hidden','true');

  // Draw checked edges within the chain
  chainCheckedRels.forEach(function(r){
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
      var arcX=xn+50,arcY=(y1c+y2c)/2;
      var arc=svgEl('path');
      sa(arc,'d','M '+xn+','+y1c+' Q '+arcX+','+arcY+' '+xn+','+y2c);
      sa(arc,'fill','none');sa(arc,'stroke','#374151');sa(arc,'stroke-width','1.5');
      sa(arc,'stroke-dasharray','8 4');sa(arc,'marker-end','url(#'+pfx+'af)');
      eg.appendChild(arc);
      var lt=svgEl('text');sa(lt,'x',arcX+4);sa(lt,'y',arcY);
      sa(lt,'font-size','10');sa(lt,'fill','#b45309');lt.textContent='cycle';eg.appendChild(lt);
    }else{
      // FROM is newer (right), TO is older (left)
      var x1=PX+fp.col*(NW+XG)+NW,y1=PY+fp.row*(NH+YG)+NH/2;
      var x2=PX+tp.col*(NW+XG),y2=PY+tp.row*(NH+YG)+NH/2;
      drawEdge(eg,x1,y1,x2,y2,stroke,'2',null,'url(#'+pfx+'af)');
      if(isPartial){
        var sc2=r.scope&&r.scope.length?r.scope.join(', '):'scope not stated';
        edgeLabel(eg,x1,y1,x2,y2,sc2,'#1d4ed8');
      }
    }
  });

  // Satellite column x
  var satX=PX+(maxL+1)*(NW+XG);
  var satY=PY;

  // Unresolved (one-sided) edges from selected node
  unresRels.forEach(function(r){
    var sx=satX,sy=satY;satY+=NH+YG;
    var sg=svgEl('rect');sa(sg,'x',sx);sa(sg,'y',sy);sa(sg,'width',Math.round(NW*0.78));sa(sg,'height',NH);
    sa(sg,'rx','4');sa(sg,'fill','none');sa(sg,'stroke','#d1d5db');sa(sg,'stroke-dasharray','5 3');
    eg.appendChild(sg);
    var st=svgEl('text');sa(st,'x',sx+5);sa(st,'y',sy+NH/2);
    sa(st,'dominant-baseline','middle');sa(st,'font-size','10');sa(st,'fill','#9ca3af');
    st.textContent=r.to||'?';eg.appendChild(st);
    var sp=np[selectedId];if(!sp)return;
    var ex1=PX+sp.col*(NW+XG)+NW,ey1=PY+sp.row*(NH+YG)+NH/2;
    drawEdge(eg,ex1,ey1,sx,sy+NH/2,'#9ca3af','1.5','6 4','url(#'+pfx+'ao)');
    edgeLabel(eg,ex1,ey1,sx,sy+NH/2,'one-sided','#9ca3af');
  });

  // Caller-asserted edges for selected node
  assertedRels.forEach(function(r){
    var peerId=r.from===selectedId?r.to:r.from;
    var sx=satX,sy=satY;satY+=NH+YG;
    var sg=svgEl('rect');sa(sg,'x',sx);sa(sg,'y',sy);sa(sg,'width',Math.round(NW*0.78));sa(sg,'height',NH);
    sa(sg,'rx','4');sa(sg,'fill','none');sa(sg,'stroke','#a78bfa');sa(sg,'stroke-dasharray','8 3 2 3');
    eg.appendChild(sg);
    var st=svgEl('text');sa(st,'x',sx+5);sa(st,'y',sy+NH/2);
    sa(st,'dominant-baseline','middle');sa(st,'font-size','10');sa(st,'fill','#7c3aed');
    st.textContent=peerId||'?';eg.appendChild(st);
    var sp=np[selectedId];if(!sp)return;
    var ex1=PX+sp.col*(NW+XG)+NW,ey1=PY+sp.row*(NH+YG)+NH/2;
    drawEdge(eg,ex1,ey1,sx,sy+NH/2,'#a78bfa','1.5','8 3 2 3','url(#'+pfx+'ah)');
    edgeLabel(eg,ex1,ey1,sx,sy+NH/2,'asserted','#7c3aed');
  });

  svg.appendChild(eg);

  // Contextual edges (hidden by default, separate group)
  var ctxG=svgEl('g');sa(ctxG,'aria-hidden','true');ctxG.style.display='none';
  var ctxX=satX,ctxY=satY,seenCtx={},ctxNP={};
  ctxRels.forEach(function(r){
    var pid=r.from===selectedId?r.to:r.from;
    if(!seenCtx[pid]){
      seenCtx[pid]=1;ctxNP[pid]={x:ctxX,y:ctxY};ctxY+=Math.round(NH*0.75)+YG;
      var sr=svgEl('rect');sa(sr,'x',ctxX);sa(sr,'y',ctxNP[pid].y);
      sa(sr,'width',Math.round(NW*0.82));sa(sr,'height',Math.round(NH*0.75));
      sa(sr,'rx','4');sa(sr,'fill','#f9fafb');sa(sr,'stroke','#d1d5db');sa(sr,'stroke-dasharray','2 3');
      ctxG.appendChild(sr);
      var st=svgEl('text');sa(st,'x',ctxX+5);sa(st,'y',ctxNP[pid].y+Math.round(NH*0.4));
      sa(st,'dominant-baseline','middle');sa(st,'font-size','10');sa(st,'fill','#9ca3af');
      st.textContent=pid;ctxG.appendChild(st);
    }
    var sp=np[selectedId];if(!sp)return;
    var cp=ctxNP[pid];if(!cp)return;
    var ex1=PX+sp.col*(NW+XG)+NW,ey1=PY+sp.row*(NH+YG)+NH/2;
    var ep=svgEl('path');
    sa(ep,'d','M '+ex1+','+ey1+' L '+cp.x+','+(cp.y+Math.round(NH*0.4)));
    sa(ep,'fill','none');sa(ep,'stroke','#d1d5db');sa(ep,'stroke-width','1');
    sa(ep,'stroke-dasharray','2 3');ctxG.appendChild(ep);
  });
  svg.appendChild(ctxG);

  // Node groups
  var nodeGs=[],nodeMap={};
  cn.forEach(function(nid){
    var p=np[nid];if(!p)return;
    var rec=allRecords.find(function(r){return r.id===nid;});
    var x=PX+p.col*(NW+XG),y=PY+p.row*(NH+YG);
    var isSel=nid===selectedId;
    var isOld=rec&&rec.superseded_by&&rec.superseded_by.length>0;
    var isCyc=sccList&&sccList[p.scc]&&sccList[p.scc].length>1;
    var g=drawNode(svg,nid,x,y,NW,NH,rec,isSel,isCyc,isOld,1,navigate);
    nodeGs.push(g);nodeMap[nid]=g;
  });
  rovingTab(nodeGs,np,chainCheckedRels);

  // Scrollable wrapper
  var wrap=document.createElement('div');
  wrap.className='lineage-wrap';wrap.style.overflowX='auto';wrap.style.maxWidth='100%';
  wrap.appendChild(svg);container.appendChild(wrap);

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
      ctxBtn.setAttribute('aria-expanded',shown?'true':'false');
      ctxBtn.textContent=(shown?'Hide':'Show')+' '+ctxRels.length
        +' contextual link'+(ctxRels.length!==1?'s':'');
    });
    container.appendChild(ctxBtn);
  }

  appendLegend(container);
  appendTextEquiv(container,cn,chainCheckedRels,allRels,allRecords,selectedId,sccList,n2s);
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
  var scale=0.62;
  var nw=Math.round(NW*scale),nh=Math.round(NH*scale);
  var xg=Math.round(XG*scale),yg=Math.round(YG*scale);
  chains.forEach(function(cn){
    var card=document.createElement('div');card.className='chain-card';
    var lbl=document.createElement('div');lbl.className='chain-card-label';
    lbl.textContent=cn.length+' records';card.appendChild(lbl);
    var cRels=allRels.filter(function(r){
      return r.trust_class==='checked'&&cn.indexOf(r.from)>=0&&cn.indexOf(r.to)>=0;
    });
    var pr2=positions(cn,cRels);
    var np2=pr2.nodePos,sl2=pr2.sccList,maxL2=pr2.maxL;
    var maxR=0;
    cn.forEach(function(n){if(np2[n]&&np2[n].row>maxR)maxR=np2[n].row;});
    var sw=PX*2+maxL2*(nw+xg)+nw,sh=PY*2+(maxR+1)*(nh+yg)-yg;
    sw=Math.max(sw,120);sh=Math.max(sh,60);
    var pfx='at'+cn[0].replace(/\W/g,'').slice(0,8)+'-';
    var svg=svgEl('svg');
    sa(svg,'width',sw);sa(svg,'height',sh);
    sa(svg,'role','group');sa(svg,'aria-label','Chain: '+cn.join(', '));
    addDefs(svg,pfx);
    var eg2=svgEl('g');sa(eg2,'aria-hidden','true');
    cRels.forEach(function(r){
      var fp=np2[r.from],tp=np2[r.to];if(!fp||!tp)return;
      if(fp.scc===tp.scc)return; // cycle arcs omitted in atlas compact view
      var x1=PX+fp.col*(nw+xg)+nw,y1=PY+fp.row*(nh+yg)+nh/2;
      var x2=PX+tp.col*(nw+xg),y2=PY+tp.row*(nh+yg)+nh/2;
      drawEdge(eg2,x1,y1,x2,y2,'#374151','1.5',null,'url(#'+pfx+'af)');
    });
    svg.appendChild(eg2);
    cn.forEach(function(nid){
      var p2=np2[nid];if(!p2)return;
      var rec2=allRecords.find(function(r){return r.id===nid;});
      var x=PX+p2.col*(nw+xg),y=PY+p2.row*(nh+yg);
      var isCyc=sl2&&sl2[p2.scc]&&sl2[p2.scc].length>1;
      var g=drawNode(svg,nid,x,y,nw,nh,rec2,false,isCyc,false,scale,navigate);
      sa(g,'tabindex','0');
    });
    var wrap2=document.createElement('div');
    wrap2.className='chain-svg-wrap';wrap2.style.overflowX='auto';
    wrap2.appendChild(svg);card.appendChild(wrap2);
    container.appendChild(card);
  });
}

return{renderFocused:renderFocused,renderAtlas:renderAtlas};
})();
