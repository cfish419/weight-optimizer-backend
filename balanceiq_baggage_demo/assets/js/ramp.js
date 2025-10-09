// assets/js/ramp.js
(function(){
  const $ = (s)=>document.querySelector(s);
  const flightSel = $('#ramp-flight');
  const paxSel = $('#ramp-passenger');
  const labels = $('#labels');

  async function loadData(){
    const res = await fetch('/assets/data/mock_flight_data.json', {cache:'no-cache'});
    return await res.json();
  }

  // center-first placement that returns a per-bag placement map
  function assignBags(manifest){
    const kg2lb = (kg)=>kg*2.20462;
    const checked = (manifest.baggage||[]).filter(b=>b.status==='CHECKED_IN');
    // heavy first
    const sorted = checked.slice().sort((a,b)=> (b.weight_kg||0)-(a.weight_kg||0));

    const order = {FWD:[3,2,1], AFT:[1,2,3]};
    const areaW = {FWD:0, AFT:0};
    const zoneW = {FWD:{1:0,2:0,3:0}, AFT:{1:0,2:0,3:0}};
    const rr = {'FWD.1':'LEFT','FWD.2':'LEFT','FWD.3':'LEFT','AFT.1':'LEFT','AFT.2':'LEFT','AFT.3':'LEFT'};
    const flip = s => s === 'LEFT' ? 'RIGHT' : 'LEFT';

    const place = {}; // tag_number -> {area, side, zone, color, zoneText}
    for(const b of sorted){
      const lb = kg2lb(Number(b.weight_kg||0));
      const area = areaW.FWD <= areaW.AFT ? 'FWD' : 'AFT';

      let chosen = order[area][0], best = Infinity;
      for(const z of order[area]){
        const w = zoneW[area][z];
        if(w < best){ best = w; chosen = z; }
      }
      const side = rr[`${area}.${chosen}`]; rr[`${area}.${chosen}`] = flip(side);

      const zoneText = chosen===1 ? 'RED' : (chosen===2 ? 'YELLOW' : 'BLUE');
      const color = zoneText.toLowerCase();

      place[b.tag_number] = { area, side, zone: chosen, color, zoneText, weightLb: lb };

      areaW[area] += lb;
      zoneW[area][chosen] += lb;
    }
    return place;
  }

  function litersFromDimensions(cm){
    if(!cm || cm.length==null || cm.width==null || cm.height==null) return null;
    return Math.round((cm.length*cm.width*cm.height)/1000);
  }

  function renderLabels(flight, manifest, paxName){
    labels.innerHTML = '';
    if(!flight || !manifest) return;

    const map = assignBags(manifest);
    const paxBags = (manifest.baggage||[]).filter(b=> b.passenger_name === paxName);
    if(paxBags.length===0){
      labels.innerHTML = '<div class="mini">No bags for this passenger.</div>';
      return;
    }
    for(const b of paxBags){
      const pl = map[b.tag_number] || {color:'blue', zoneText:'BLUE', area:'AFT'};
      const volL = litersFromDimensions(b.dimensions_cm);
      const dims = b.dimensions_cm ? `${b.dimensions_cm.length}x${b.dimensions_cm.width}x${b.dimensions_cm.height} cm` : '-';
      const html = `
        <div class="lbl ${pl.color}">
          <div class="hdr ${pl.color}"></div>
          <div class="body">
            <div class="line"><strong>${b.tag_number}</strong></div>
            <div class="line">${b.passenger_name}</div>
            <div class="line">Flight: ${flight.flight_number}</div>
            <div class="line">Weight: ${Math.round((b.weight_kg||0)*2.20462)} lb</div>
            <div class="line">${dims}${volL? ' • '+volL+' L':''}</div>
            <div class="zone">Zone: ${pl.area} (${pl.zoneText})</div>
          </div>
        </div>`;
      labels.insertAdjacentHTML('beforeend', html);
    }
  }

  function populatePassengers(manifest){
    paxSel.innerHTML = '<option value="">Select passenger…</option>';
    const names = Array.from(new Set((manifest.baggage||[]).map(b=>b.passenger_name).filter(Boolean))).sort();
    for(const n of names){
      const o = document.createElement('option');
      o.value = n; o.textContent = n;
      paxSel.appendChild(o);
    }
    paxSel.disabled = false;
  }

  loadData().then(data=>{
    // Build flights dropdown
    const flights = data?.flights || [];
    const manifests = data?.manifests || [];
    for(const f of flights){
      const o = document.createElement('option');
      o.value = f.flight_number;
      o.textContent = `${f.flight_number} (${f.departure}→${f.arrival})`;
      flightSel.appendChild(o);
    }
    // initial select first
    if(flights.length>0){
      flightSel.value = flights[0].flight_number;
      const man = manifests.find(m=> m.flight?.flight_number === flights[0].flight_number);
      if(man){ populatePassengers(man); }
    }

    flightSel.addEventListener('change', ()=>{
      const fn = flightSel.value;
      const man = manifests.find(m=> m.flight?.flight_number === fn);
      if(man){ populatePassengers(man); labels.innerHTML=''; }
    });

    paxSel.addEventListener('change', ()=>{
      const fn = flightSel.value;
      const man = manifests.find(m=> m.flight?.flight_number === fn);
      const pax = paxSel.value || '';
      if(pax && man){
        const f = flights.find(x=> x.flight_number===fn);
        renderLabels(f, man, pax);
      }else{
        labels.innerHTML='';
      }
    });
  });
})();