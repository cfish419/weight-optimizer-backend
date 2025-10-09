// assets/js/app_center_first.js
(function(){
  // ------------ State ------------
  window.state = {
    bags: [],
    selectedFlight: null,
    data: null,
    _allFlights: [],
    flightInfo: null // {dep, arr, hours}
  };

  // ------------ Config ------------
  const OPT_WEIGHTS = {
    CG: 1.2,     // CG closeness
    W:  1.0,     // weight balance
    V:  0.7,     // volume balance
    D:  0.20     // density-at-ends penalty
  };
  const FUEL = {
    burnKgPerHr: 2400,   // demo for 737-class
    kgPerGal: 3.05,      // Jet-A ~ 6.7 lb/gal -> ~3.04 kg/gal
    pricePerGal: 2.75,   // $/gal
    kImbalance: 0.02,    // penalty weights
    kCg: 0.01,
    cap: 0.08            // cap at +8% extra burn
  };

  // ------------ Helpers ------------
  const $  = sel => document.querySelector(sel);
  const lbToKg = lb => lb * 0.45359237;
  const kgToLb = kg => kg * 2.20462;
  const fmtLb  = n  => `${Math.round(n)} lb`;
  const clamp  = (n, min, max) => Math.max(min, Math.min(max, n));
  const colorForZone = z => z==='FWD'?'red':(z==='MID'?'yellow':(z==='AFT'?'blue':null));
  const volumeFromDimsL = (dims) => {
    if(!dims) return null;
    const L = Number(dims.length), W = Number(dims.width), H = Number(dims.height);
    if([L,W,H].some(isNaN)) return null;
    return (L*W*H)/1000; // cm^3 -> L
  };
  const densityKgPerL = (wKg, volL) => (wKg && volL) ? (wKg / volL) : null;

  // Simple airport lat/lon set (extend as needed)
  const AIRPORTS = {
    'DAL': {lat:32.8471, lon:-96.8518}, 'HOU': {lat:29.6454, lon:-95.2789},
    'DEN': {lat:39.8561, lon:-104.6737}, 'PHX': {lat:33.4343, lon:-112.0116},
    'LAS': {lat:36.0840, lon:-115.1537}, 'LAX': {lat:33.9416, lon:-118.4085},
    'SFO': {lat:37.6213, lon:-122.3790}, 'SEA': {lat:47.4502, lon:-122.3088},
    'MDW': {lat:41.7868, lon:-87.7522}, 'BWI': {lat:39.1754, lon:-76.6684},
    'MCO': {lat:28.4312, lon:-81.3081}, 'ATL': {lat:33.6407, lon:-84.4277},
    'SLC': {lat:40.7899, lon:-111.9791}, 'AUS': {lat:30.1975, lon:-97.6664},
    'SAN': {lat:32.7338, lon:-117.1933}, 'OAK': {lat:37.7126, lon:-122.2197},
    'SMF': {lat:38.6954, lon:-121.5908}, 'STL': {lat:38.7500, lon:-90.3700},
    'MSY': {lat:29.9934, lon:-90.2580}, 'OAK': {lat:37.7126, lon:-122.2197},
    'OAK': {lat:37.7126, lon:-122.2197} // keep OAK once (harmless duplicates ignored)
  };
  function toRad(d){ return d*Math.PI/180; }
  function haversineKm(a, b){
    const R = 6371;
    const dLat = toRad(b.lat-a.lat), dLon = toRad(b.lon-a.lon);
    const s = Math.sin(dLat/2)**2 + Math.cos(toRad(a.lat))*Math.cos(toRad(b.lat))*(Math.sin(dLon/2)**2);
    return 2*R*Math.asin(Math.sqrt(s));
  }
  function estimateHoursFromAirports(dep, arr){
    const A = AIRPORTS[dep], B = AIRPORTS[arr];
    if(!A || !B) return 1.8; // fallback
    const distKm = haversineKm(A, B);
    const cruiseKmh = 780; // typical 737 TAS
    const taxiPadHr = 0.3; // taxi/ATC
    const hrs = clamp(distKm/cruiseKmh + taxiPadHr, 0.5, 6);
    return Math.round(hrs*100)/100;
  }
  function hoursFromManifest(man){
    if(!man?.flight) return 1.8;
    const f = man.flight;
    if(typeof f.duration_minutes === 'number') return Math.max(0.5, f.duration_minutes/60);
    if(f.departure && f.arrival) return estimateHoursFromAirports(f.departure, f.arrival);
    return 1.8;
  }

  // ------------ Data Loading ------------
  async function loadManifestJSON(){
    try{
      const res = await fetch('/assets/data/mock_flight_data.json', {cache:'no-cache'});
      const data = await res.json();
      state.data = data;
      state._allFlights = (data?.flights || []).slice().sort((a,b)=> a.flight_number.localeCompare(b.flight_number));
      buildFlightSelect(state._allFlights);
    }catch(err){
      console.error('Failed to load mock_flight_data.json', err);
    }
  }
  function buildFlightSelect(flights){
    const sel = $('#flight-select');
    if (!sel) return;
    sel.innerHTML = '<option value=\"\">Select flight…</option>';
    for(const f of flights){
      const opt = document.createElement('option');
      opt.value = f.flight_number;
      opt.textContent = `${f.flight_number} (${f.departure}→${f.arrival})`;
      sel.appendChild(opt);
    }
  }
  function manifestFor(flightNum){
    if(!state.data?.manifests) return null;
    return state.data.manifests.find(m => m.flight?.flight_number === flightNum) || null;
  }
  function buildPassengerSelect(flightNum){
    const man = manifestFor(flightNum);
    const sel = $('#passenger-select');
    if(!sel){ return; }
    sel.innerHTML = '<option value=\"\">Select passenger…</option>';
    if(!man){ sel.disabled = true; $('#prefill-passenger') && ($('#prefill-passenger').disabled = true); return; }
    const names = [...new Set(man.baggage.map(b => b.passenger_name))].sort((a,b)=> a.localeCompare(b));
    for(const n of names){
      const o = document.createElement('option');
      o.value = n;
      o.textContent = n;
      sel.appendChild(o);
    }
    sel.disabled = false;
    $('#prefill-passenger') && ($('#prefill-passenger').disabled = false);
  }

  // ------------ Auto-load on flight change ------------
  $('#flight-select')?.addEventListener('change', (e)=>{
    const fn = e.target.value || null;
    state.selectedFlight = fn;
    const kpi = $('#kpi-flight'); if (kpi) kpi.textContent = fn || '-';
    const meta = $('#flight-meta');

    if (!fn){
      if (meta){ meta.style.display='none'; meta.textContent=''; }
      $('#passenger-select') && ( $('#passenger-select').innerHTML = '<option value=\"\">Select passenger…</option>', $('#passenger-select').disabled = true );
      state.bags = []; state.flightInfo = null; render(); persistSupervisorSnapshot();
      return;
    }

    const man = manifestFor(fn);
    if(man){
      const f = man.flight;
      if (meta){ meta.style.display='inline-flex'; meta.textContent = `${f.flight_number} • ${f.departure}→${f.arrival} • ${f.aircraft_type}`; }
      buildPassengerSelect(fn);

      // Store flight info (hours)
      const hours = hoursFromManifest(man);
      state.flightInfo = {dep:f.departure, arr:f.arrival, hours};

      // Auto-fill plan using manifest (compute volume from dimensions)
      state.bags = man.baggage
        .filter(b => b.status === 'CHECKED_IN')
        .map(b => {
          const volL = volumeFromDimsL(b.dimensions_cm) ?? null;
          return {
            weightKg: Number(b.weight_kg || 0),
            volumeL: volL,
            zone: null,
            color: null,
            meta: {
              tag: b.tag_number,
              pax: b.passenger_name,
              priority: b.priority,
              category: b.category,
              dims: b.dimensions_cm || null
            }
          };
        });
      optimizeBalanced();               // balanced optimizer
      persistSupervisorSnapshot(true);
    } else {
      if (meta){ meta.style.display='none'; meta.textContent=''; }
      buildPassengerSelect(null);
      state.bags = []; state.flightInfo = null; render(); persistSupervisorSnapshot();
    }
  });

  // ------------ Flight filter input ------------
  $('#flight-filter')?.addEventListener('input', (e)=>{
    const q = (e.target.value || '').trim().toLowerCase();
    if (!Array.isArray(state._allFlights)) return;
    const filtered = q
      ? state._allFlights.filter(f => String(f.flight_number).toLowerCase().includes(q))
      : state._allFlights;
    buildFlightSelect(filtered);
  });

  // ------------ Passenger prefill ------------
  $('#prefill-passenger')?.addEventListener('click', ()=>{
    const paxSel = $('#passenger-select');
    const pax = paxSel ? paxSel.value : '';
    if(!pax || !state.selectedFlight) return;
    const man = manifestFor(state.selectedFlight);
    if(!man) return;
    const bags = man.baggage.filter(b => b.passenger_name === pax);
    if(!bags.length) return;
    const b = bags.slice().sort((a,b)=> (b.weight_kg||0)-(a.weight_kg||0))[0];
    const v = volumeFromDimsL(b.dimensions_cm);
    $('#units') && ($('#units').value = 'lb');
    $('#weight') && ($('#weight').value = Math.round(kgToLb(Number(b.weight_kg||0))));
    if($('#volume')) $('#volume').value = v ? v.toFixed(1) : '';
    const paxMeta = $('#pax-meta');
    if (paxMeta){ paxMeta.style.display='inline-flex'; paxMeta.textContent = `${pax} • ${b.tag_number} • ${Math.round(kgToLb(b.weight_kg))} lb${v? ' • '+v.toFixed(1)+' L':''}`; }
  });

  // ------------ Manual add / seed / reset / optimize / print ------------
  $('#add-btn')?.addEventListener('click', ()=>{
    const wEl = $('#weight'); const unitsEl = $('#units'); const volEl = $('#volume');
    const w = parseFloat(wEl?.value); if(!w || w<=0) return;
    const units = unitsEl?.value || 'lb';
    const vol = parseFloat(volEl?.value);
    const wKg = (units === 'lb') ? lbToKg(w) : w;
    state.bags.push({ weightKg: wKg, volumeL: isNaN(vol)?null:vol, zone: null, color: null, meta:{} });
    if (wEl) wEl.value = ''; if (volEl) volEl.value='';
    optimizeBalanced();
    persistSupervisorSnapshot(true);
  });
  $('#reset-btn')?.addEventListener('click', ()=>{ state.bags = []; render(); persistSupervisorSnapshot(); });
  $('#seed-btn')?.addEventListener('click', ()=>{
    const samples = [{lb:18,v:30},{lb:22,v:40},{lb:27,v:45},{lb:31,v:55},{lb:12,v:25},{lb:26,v:35},{lb:14,v:28},{lb:24,v:38}];
    for(const s of samples){ state.bags.push({ weightKg: lbToKg(s.lb), volumeL: s.v, zone: null, color:null, meta:{} }); }
    optimizeBalanced(); persistSupervisorSnapshot(true);
  });
  $('#optimize-btn')?.addEventListener('click', ()=>{ optimizeBalanced(); persistSupervisorSnapshot(true); });
  $('#labels-btn')?.addEventListener('click', ()=>{ printLabels(); });

  // ------------ Balanced Optimizer ------------
  function optimizeBalanced(){
    if(!Array.isArray(state.bags) || !state.bags.length){ render(); return; }

    // Per-zone arm (toy) for CG calc
    const ARM = {FWD:0, MID:1, AFT:2};
    const CG_TARGET = 1.0;
    const zones = ['FWD','MID','AFT'];

    // Desired counts (even split with remainder to MID, then AFT, then FWD)
    const N = state.bags.length;
    const base = Math.floor(N/3);
    const quotas = {FWD:base, MID:base, AFT:base};
    let rem = N - base*3;
    for(const z of ['MID','AFT','FWD']){ if(rem>0){ quotas[z]++; rem--; } }

    // Targets for weight/volume
    const totW = state.bags.reduce((a,b)=> a+(b.weightKg||0),0);
    const totV = state.bags.reduce((a,b)=> a+(b.volumeL||0),0);
    const targetW = totW/3, targetV = totV/3;

    // Accumulators
    const bins = {FWD:{w:0,v:0,c:0}, MID:{w:0,v:0,c:0}, AFT:{w:0,v:0,c:0}};
    let sumW=0, moment=0;

    // Order: heavy & bulky first
    const order = state.bags
      .map(b=>({b, key: (b.weightKg||0) + 0.2*(b.volumeL||0)}))
      .sort((a,b)=> b.key-a.key)
      .map(x=>x.b);

    // Greedy assignment with hard quota penalty
    for(const b of order){
      const w=b.weightKg||0, v=b.volumeL||0;
      const dens = densityKgPerL(w,v) || 0;
      const densNorm = Math.min(1, dens/0.6);

      let best=null, bestScore=Infinity;
      for(const z of zones){
        const quotaPenalty = (bins[z].c >= quotas[z]) ? 1e6 : 0;
        const wZ = bins[z].w + w;
        const vZ = bins[z].v + v;

        const sumW_c = sumW + w;
        const moment_c = moment + w*ARM[z];
        const cg_c = sumW_c>0 ? (moment_c/sumW_c) : CG_TARGET;
        const cgErr = Math.abs(cg_c - CG_TARGET);

        const wErr = Math.abs(wZ - targetW);
        const vErr = Math.abs(vZ - targetV);
        const densPenalty = (z==='MID'?0:densNorm);

        const score = quotaPenalty
                    + OPT_WEIGHTS.CG*cgErr
                    + OPT_WEIGHTS.W*wErr
                    + OPT_WEIGHTS.V*vErr
                    + OPT_WEIGHTS.D*densPenalty;
        if(score < bestScore){ bestScore=score; best=z; }
      }

      b.zone = best; b.color = colorForZone(best);
      bins[best].w += w; bins[best].v += v; bins[best].c += 1;
      sumW += w; moment += w*ARM[best];
    }

    render();
  }

  // ------------ Render + Fuel Savings (gallons) ------------
  function render(){
    const get = (id) => document.getElementById(id);
    const setText = (id, text) => { const el = get(id); if (el) el.textContent = text; };
    const setLeft = (id, pct) => { const el = get(id); if (el) el.style.left = pct; };

    // Totals by zone
    const totals = {FWD:0, MID:0, AFT:0, total:0};
    if (Array.isArray(state.bags)) {
      for(const b of state.bags){
        totals.total += b.weightKg||0;
        if(b.zone) totals[b.zone] += b.weightKg||0;
      }
    }
    setText('kpi-flight', state.selectedFlight || '-');
    setText('kpi-total', fmtLb(kgToLb(totals.total)));
    setText('kpi-fwd', fmtLb(kgToLb(totals.FWD)));
    setText('kpi-mid', fmtLb(kgToLb(totals.MID)));
    setText('kpi-aft', fmtLb(kgToLb(totals.AFT)));

    
  // CG

  // CG as %MAC (demo mapping). We map internal 0–2 metric → 20–32 %MAC.
  const ENVELOPE = { min: 20, max: 32, target: 26 };
  const total = totals.total || 1;
  const cgMetric = (2*totals.AFT + 1*totals.MID + 0*totals.FWD)/total; // 0(front)..2(tail)
  const cgPct = ENVELOPE.min + (cgMetric/2) * (ENVELOPE.max - ENVELOPE.min);

  setText('cg-value', cgPct.toFixed(1) + '% MAC');
  const posPct = clamp(((cgPct - ENVELOPE.min) / (ENVELOPE.max - ENVELOPE.min)) * 100, 0, 100);
  setLeft('cg-needle', `${posPct}%`);
  const statusEl = get('cg-status');
  if (statusEl) {
    const ok = (cgPct >= ENVELOPE.min && cgPct <= ENVELOPE.max);
    statusEl.textContent = ok ? 'IN RANGE' : 'OUT OF RANGE';
    statusEl.style.color = ok ? 'var(--green)' : 'var(--red)';
  }
  const cap = document.getElementById('cg-caption');
  if (cap) cap.textContent = `Target ${ENVELOPE.target}% MAC | Envelope ${ENVELOPE.min}–${ENVELOPE.max}% (demo)`;

// Fuel savings with flight hours -> convert KG to GALLONS
    const routeEl = get('fuel-route');
    const hours = state.flightInfo?.hours ?? 1.8;
    const routeTxt = (state.flightInfo?.dep && state.flightInfo?.arr) ? `${state.flightInfo.dep}→${state.flightInfo.arr}` : '-';
    if(routeEl) routeEl.textContent = `Route: ${routeTxt} • ~${hours.toFixed(1)} h`;

    const meanW = (totals.FWD + totals.MID + totals.AFT)/3;
    const sd = Math.sqrt(((Math.pow(totals.FWD-meanW,2)+Math.pow(totals.MID-meanW,2)+Math.pow(totals.AFT-meanW,2))/3)) || 0;
    const imbalanceNorm = clamp(sd/(meanW||1), 0, 1);
    const cgErrNorm = clamp(Math.abs(cgMetric-1.0)/2.0, 0, 1); // normalize to 2-arm span

    const extraBurnFrac = Math.min(FUEL.cap, FUEL.kImbalance*imbalanceNorm + FUEL.kCg*cgErrNorm);
    const fuelSavedKg = FUEL.burnKgPerHr * hours * extraBurnFrac;
    const fuelSavedGal = fuelSavedKg / FUEL.kgPerGal;
    const dollars = Math.round(fuelSavedGal * FUEL.pricePerGal);

    setText('fuel-savings-amt', `$${dollars.toLocaleString()}`);
    setText('fuel-savings-sub', dollars>0 ? 'Estimated savings from balanced load' : 'No savings (unbalanced)');
    setText('fuel-savings-details', `${fuelSavedGal.toFixed(0)} gal saved • balance ${(100*(1-imbalanceNorm)).toFixed(0)}% • CG err ${(cgErrNorm*100).toFixed(0)}%`);

    // Table
    const tbody = get('bag-rows');
    if (tbody) {
      tbody.innerHTML = '';
      if (Array.isArray(state.bags)) {
        state.bags.forEach((b, idx)=>{
          const wLb = kgToLb(b.weightKg||0);
          const volL = b.volumeL;
          const dens = densityKgPerL(b.weightKg, b.volumeL);
          const dims = b.meta?.dims;
          const dimsStr = dims ? `${dims.length}×${dims.width}×${dims.height}` : '-';
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td>${b.meta?.tag || ('Bag ' + (idx+1))}<div style="font-size:11px;color:#64748b">${b.meta?.pax||''}</div></td>
            <td>${fmtLb(wLb)}</td>
            <td>${dimsStr}</td>
            <td>${(volL? volL.toFixed(1) : '-')}</td>
            <td>${(dens? dens.toFixed(2) : '-')}</td>
            <td>${b.zone || '-'}</td>
            <td><span class="swatch" style="background:${b.color ? 'var(--'+b.color+')' : '#e5e7eb'}"></span> ${b.color ? b.color.toUpperCase() : '-'}</td>
            <td><button class="ghost" data-i="${idx}">remove</button></td>`;
          tbody.appendChild(tr);
        });
        Array.from(tbody.querySelectorAll('button.ghost[data-i]')).forEach(btn=>{
          btn.onclick=()=>{
            const i = parseInt(btn.getAttribute('data-i'));
            state.bags.splice(i,1);
            optimizeBalanced();
            persistSupervisorSnapshot(true);
          };
        });
      }
    }
  }

  // ------------ Print Labels ------------
  function printLabels(){
    try{
      const kgToLb = (kg)=> kg*2.20462;
      const win = window.open('', '_blank');
      const styles = `
        <style>
          body{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; margin:16px; }
          .grid{ display:grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap:12px; }
          .card{ border:1px solid #e5e7eb; border-radius:12px; padding:12px; }
          .hdr{ font-weight:700; margin-bottom:6px; }
          .meta{ font-size:12px; color:#475569; margin-bottom:6px; }
          .pill{ display:inline-block; padding:2px 8px; border-radius:999px; font-size:12px; border:1px solid #e5e7eb; }
          .red{ background:#fee2e2; }
          .yellow{ background:#fef3c7; }
          .blue{ background:#dbeafe; }
        </style>`;
      let html = `<h2>Bag Labels</h2><div class="grid">`;
      (state.bags||[]).forEach((b,i)=>{
        const wLb = Math.round(kgToLb(b.weightKg||0));
        const zone = b.zone || '-';
        const color = b.color || '';
        const tag = (b.meta && b.meta.tag) ? b.meta.tag : `Bag ${i+1}`;
        const pax = (b.meta && b.meta.pax) ? b.meta.pax : '';
        const dims = b.meta?.dims;
        const dimsStr = dims ? `${dims.length}×${dims.width}×${dims.height} cm` : '';
        const vol = b.volumeL ? `${b.volumeL.toFixed(1)} L` : '';
        html += `<div class="card ${color}">
          <div class="hdr">${tag}</div>
          <div class="meta">${pax}</div>
          <div class="meta">Flight: ${state.selectedFlight || '-'}</div>
          <div class="meta">Weight: ${wLb} lb</div>
          <div class="meta">${dimsStr} ${vol ? '• '+vol : ''}</div>
          <div class="pill">Zone: ${zone} ${color ? '('+color.toUpperCase()+')' : ''}</div>
        </div>`;
      });
      html += `</div>`;
      win.document.write(`<html><head><title>Labels</title>${styles}</head><body>${html}</body></html>`);
      win.document.close();
      win.focus();
      win.print();
    }catch(e){ console.error('printLabels error', e); }
  }

  // ------------ Snapshot for Supervisor (center-first proportional fill) ------------
  function persistSupervisorSnapshot(force){
    if (!Array.isArray(state.bags)) return;
    const kgToLb = (kg)=> kg*2.20462;

    const cells = {
      'FWD.LEFT.1':{count:0, weightLb:0}, 'FWD.RIGHT.1':{count:0, weightLb:0},
      'FWD.LEFT.2':{count:0, weightLb:0}, 'FWD.RIGHT.2':{count:0, weightLb:0},
      'FWD.LEFT.3':{count:0, weightLb:0}, 'FWD.RIGHT.3':{count:0, weightLb:0},
      'AFT.LEFT.1':{count:0, weightLb:0},  'AFT.RIGHT.1':{count:0, weightLb:0},
      'AFT.LEFT.2':{count:0, weightLb:0},  'AFT.RIGHT.2':{count:0, weightLb:0},
      'AFT.LEFT.3':{count:0, weightLb:0},  'AFT.RIGHT.3':{count:0, weightLb:0},
    };

    const areaW = {FWD:0, AFT:0};
    const zoneW = {FWD:{1:0,2:0,3:0}, AFT:{1:0,2:0,3:0}};
    const sideNext = {
      'FWD.1':'LEFT','FWD.2':'LEFT','FWD.3':'LEFT',
      'AFT.1':'LEFT','AFT.2':'LEFT','AFT.3':'LEFT'
    };
    const zoneOrder = { FWD:[3,2,1], AFT:[1,2,3] }; // center -> nose/tail

    let totalLb = 0;

    for(const b of state.bags){
      const wLb = kgToLb(Number(b.weightKg||0));
      totalLb += wLb;

      // area from b.zone; if MID/unknown => send to lighter area
      let area = (b.zone==='FWD') ? 'FWD' : (b.zone==='AFT') ? 'AFT' :
                 (areaW.FWD <= areaW.AFT ? 'FWD' : 'AFT');

      // choose zone with least weight in that area (center-first tiebreak)
      let chosenZone = zoneOrder[area][0];
      let best = Infinity;
      for(const z of zoneOrder[area]){
        const w = zoneW[area][z];
        if (w < best){ best = w; chosenZone = z; }
      }

      // alternate left/right within the zone
      const base = `${area}.${chosenZone}`;
      const side = sideNext[base];
      sideNext[base] = (side==='LEFT') ? 'RIGHT' : 'LEFT';

      const cellKey = `${area}.${side}.${chosenZone}`;
      cells[cellKey].count += 1;
      cells[cellKey].weightLb += wLb;

      areaW[area] += wLb;
      zoneW[area][chosenZone] += wLb;
    }

    const snapshot = {
      version: 4,
      perCellCap: 20,
      ts: Date.now(),
      flightNumber: state.selectedFlight || null,
      totals: { bags: state.bags.length, weightLb: totalLb },
      cells
    };

    try{ localStorage.setItem('balanceiq-supervisor', JSON.stringify(snapshot)); }catch(e){}
  }
  window.__balanceiqPersist = ()=>persistSupervisorSnapshot(true);

  // ------------ Boot ------------
  loadManifestJSON().then(()=>{ render(); });

})();
