// assets/js/supervisor_center_sync.js
(function(){
  const $ = (s)=>document.querySelector(s);
  const perCellCapDefault = 20;

  function loadLatest(){ try{ return JSON.parse(localStorage.getItem('balanceiq-supervisor')); }catch(e){ return null; } }
  function loadForFlight(fn){ if(!fn) return null; try{ return JSON.parse(localStorage.getItem(`balanceiq-supervisor:${fn}`)); }catch(e){ return null; } }

  function setCell(area, side, zone, bags, weight, cap){
    const id = `#${area}-${side[0]}-${zone}`;
    const root = $(id);
    if(!root) return;
    const b = root.querySelector('.bags'), w = root.querySelector('.lb'), bar = root.querySelector('.fill');
    if(b) b.textContent = String(bags||0);
    if(w) w.textContent = `${Math.round(weight||0)} lb`;
    const pct = Math.min(100, Math.round(((bags||0)/(cap||perCellCapDefault))*100));
    if(bar) bar.style.width = pct+'%';
  }

  function render(snapshot){
    const info = $('#snap-info');
    if(!snapshot){ info.textContent = 'No snapshot available'; return; }

    const cap = snapshot.perCellCap || perCellCapDefault;
    const dt = new Date(snapshot.ts);
    const ageMin = Math.floor((Date.now()-snapshot.ts)/60000);

    $('#snap-flight').textContent = snapshot.flightNumber || '-';
    $('#snap-bags').textContent   = snapshot.totals?.bags ?? 0;
    $('#snap-weight').textContent = Math.round(snapshot.totals?.weightLb ?? 0) + ' lb';
    info.textContent = `Synced ${ageMin===0?'just now':ageMin+' min ago'}`;

    const cells = snapshot.cells || {};
    const get = (k)=>cells[k] || {count:0, weightLb:0};

    // FWD
    setCell('FWD','LEFT',1, get('FWD.LEFT.1').count, get('FWD.LEFT.1').weightLb, cap);
    setCell('FWD','LEFT',2, get('FWD.LEFT.2').count, get('FWD.LEFT.2').weightLb, cap);
    setCell('FWD','LEFT',3, get('FWD.LEFT.3').count, get('FWD.LEFT.3').weightLb, cap);
    setCell('FWD','RIGHT',1, get('FWD.RIGHT.1').count, get('FWD.RIGHT.1').weightLb, cap);
    setCell('FWD','RIGHT',2, get('FWD.RIGHT.2').count, get('FWD.RIGHT.2').weightLb, cap);
    setCell('FWD','RIGHT',3, get('FWD.RIGHT.3').count, get('FWD.RIGHT.3').weightLb, cap);

    // AFT
    setCell('AFT','LEFT',1, get('AFT.LEFT.1').count, get('AFT.LEFT.1').weightLb, cap);
    setCell('AFT','LEFT',2, get('AFT.LEFT.2').count, get('AFT.LEFT.2').weightLb, cap);
    setCell('AFT','LEFT',3, get('AFT.LEFT.3').count, get('AFT.LEFT.3').weightLb, cap);
    setCell('AFT','RIGHT',1, get('AFT.RIGHT.1').count, get('AFT.RIGHT.1').weightLb, cap);
    setCell('AFT','RIGHT',2, get('AFT.RIGHT.2').count, get('AFT.RIGHT.2').weightLb, cap);
    setCell('AFT','RIGHT',3, get('AFT.RIGHT.3').count, get('AFT.RIGHT.3').weightLb, cap);
  }

  // Populate flights from manifest for convenience
  async function buildFlightSelect(){
    try{
      const res = await fetch('/assets/data/mock_flight_data.json', {cache:'no-cache'});
      const data = await res.json();
      const sel = $('#flight-select');
      for(const f of (data?.flights||[])){
        const o = document.createElement('option');
        o.value = f.flight_number;
        o.textContent = `${f.flight_number} (${f.departure}→${f.arrival})`;
        sel.appendChild(o);
      }
    }catch(e){ /* ignore */ }
  }

  $('#sync-btn')?.addEventListener('click', ()=>{
    const fn = $('#flight-select')?.value || '';
    if(fn){
      render(loadForFlight(fn) || loadLatest());
    }else{
      render(loadLatest());
    }
  });

  $('#flight-select')?.addEventListener('change', (e)=>{
    const fn = e.target.value || '';
    const snap = fn ? loadForFlight(fn) : loadLatest();
    render(snap);
  });

  // Listen to updates across tabs (when loader writes a new snapshot)
  window.addEventListener('storage', (ev)=>{
    if(!ev.key) return;
    const fn = $('#flight-select')?.value || '';
    if(fn && ev.key === `balanceiq-supervisor:${fn}`) render(loadForFlight(fn));
    if(!fn && ev.key === 'balanceiq-supervisor') render(loadLatest());
  });

  buildFlightSelect().then(()=>{
    render(loadLatest());
  });
})();