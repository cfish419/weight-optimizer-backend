
/** Simple demo optimizer (not for real-world aircraft ops) **/

const state = {
  bags: [],       // {id, weightKg, volumeL?, density?, zone, color}
  units: 'lb',    // 'lb' or 'kg' for input convenience
  cfg: {
    // Simplified arms (meters from datum) for demo
    zones: [
      {key:'FWD', arm: 3.0},
      {key:'MID', arm: 7.0},
      {key:'AFT', arm: 11.0},
    ],
    // Demo CG envelope (meters)
    targetCG: 7.0,
    minCG: 5.5,
    maxCG: 8.5
  },
  nextId: 1
};

// Helpers
const toKg = (w, units) => units === 'lb' ? (w * 0.45359237) : w;
const fmt = (n, d=1) => isFinite(n) ? n.toFixed(d) : '-';

// Add a bag to the list
function addBag(weightValue, units, volumeL) {
  const id = state.nextId++;
  const weightKg = toKg(Number(weightValue || 0), units);
  const vol = volumeL ? Number(volumeL) : null;
  const density = (vol && vol > 0) ? weightKg / vol : null;
  state.bags.push({ id, weightKg, volumeL: vol, density, zone:null, color:null });
  render();
}

// Remove bag
function removeBag(id){
  state.bags = state.bags.filter(b => b.id !== id);
  render();
}

// Core: greedy assignment to keep CG near target within envelope
function optimize() {
  // reset assignments
  state.bags.forEach(b => { b.zone = null; b.color = null; });

  // Sort heavy -> light
  const sorted = [...state.bags].sort((a,b)=> b.weightKg - a.weightKg);

  let totW = 0, totM = 0; // total weight and moment
  const placed = [];

  for(const bag of sorted){
    let best = null;
    for(const z of state.cfg.zones){
      const W = totW + bag.weightKg;
      const M = totM + bag.weightKg * z.arm;
      const cg = M / W;
      const within = (cg >= state.cfg.minCG && cg <= state.cfg.maxCG);
      const dist = Math.abs(cg - state.cfg.targetCG);
      const score = (within ? 0 : 100) + dist; // penalize leaving envelope
      if(!best || score < best.score){
        best = {zone:z.key, cg, W, M, score};
      }
    }
    // Place bag
    bag.zone = best.zone;
    totW = best.W; totM = best.M;
    placed.push(bag);
  }

  // Assign load order colors: red -> yellow -> blue (thirds)
  const n = placed.length || 1;
  placed.forEach((b, idx) => {
    const frac = (idx+1)/n;
    b.color = frac <= 1/3 ? 'red' : (frac <= 2/3 ? 'yellow' : 'blue');
  });

  renderCG(totW, totM);
  render();
}

// Render CG summary
function renderCG(W, M){
  const cg = M / (W || 1);
  const cgSpan = document.getElementById('cg-value');
  const status = document.getElementById('cg-status');
  const needle = document.getElementById('cg-needle');

  cgSpan.textContent = fmt(cg, 2) + ' m';

  const within = (cg >= state.cfg.minCG && cg <= state.cfg.maxCG);
  status.textContent = within ? 'Within envelope' : 'Outside envelope (demo numbers)';
  status.style.color = within ? 'var(--ok)' : 'var(--bad)';

  // Visualize: map 3..11 m to 0..100%
  const map = (x) => ((x-3)/(11-3))*100;
  needle.style.left = Math.max(0, Math.min(100, map(cg))) + '%';
}

// Render table and KPIs
function render(){
  const tbody = document.getElementById('bag-rows');
  tbody.innerHTML = '';
  let total = 0;
  const perZone = {FWD:0, MID:0, AFT:0};

  for(const bag of state.bags){
    total += bag.weightKg;
    if(bag.zone) perZone[bag.zone] += bag.weightKg;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>#${bag.id}</td>
      <td>${fmt(bag.weightKg*2.20462,1)} lb</td>
      <td>${bag.volumeL ? fmt(bag.volumeL,1)+' L' : '-'}</td>
      <td>${bag.density ? fmt(bag.density,2)+' kg/L' : '-'}</td>
      <td>${bag.zone ? `<span class="badge zone">${bag.zone}</span>` : '-'}</td>
      <td>${bag.color ? `<span class="badge ${bag.color}">${bag.color.toUpperCase()}</span>` : '-'}</td>
      <td><button class="secondary" data-remove="${bag.id}">Remove</button></td>
    `;
    tbody.appendChild(tr);
  }

  document.getElementById('kpi-total').textContent = fmt(total*2.20462,1) + ' lb';
  document.getElementById('kpi-fwd').textContent = fmt(perZone.FWD*2.20462,1) + ' lb';
  document.getElementById('kpi-mid').textContent = fmt(perZone.MID*2.20462,1) + ' lb';
  document.getElementById('kpi-aft').textContent = fmt(perZone.AFT*2.20462,1) + ' lb';

  // wire removes
  document.querySelectorAll('[data-remove]').forEach(btn=>{
    btn.onclick = () => removeBag(Number(btn.getAttribute('data-remove')));
  });
}

// Demo data
function seedDemo(){
  state.bags = [];
  state.nextId = 1;
  const demoWeightsLb = [52, 41, 63, 28, 35, 57, 48, 29, 44, 31, 26, 60, 53, 22, 38];
  demoWeightsLb.forEach(w => addBag(w, 'lb', null));
}

// Print labels view
function printLabels(){
  const win = window.open('', '_blank');
  const rows = state.bags.map(b => `
    <div class="lbl">
      <div class="top ${b.color||'blue'}"></div>
      <div class="body">
        <div><strong>Bag #${b.id}</strong></div>
        <div>${(b.weightKg*2.20462).toFixed(1)} lb</div>
        <div>Zone: ${b.zone||'-'}</div>
        <div>Load: ${(b.color||'-').toUpperCase()}</div>
      </div>
    </div>
  `).join('');
  win.document.write(`
    <style>
      body{font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; margin:20px}
      .grid{display:grid; grid-template-columns:repeat(3, 1fr); gap:12px}
      .lbl{border:1px solid #e5e7eb; border-radius:10px; overflow:hidden}
      .top{height:20px}
      .top.red{background:#ef4444}
      .top.yellow{background:#f59e0b}
      .top.blue{background:#3b82f6}
      .body{padding:10px 12px; font-size:14px}
    </style>
    <h3>BalanceIQ – Load Labels (Demo)</h3>
    <div class="grid">${rows}</div>
  `);
  win.document.close();
  win.focus();
}

window.addEventListener('DOMContentLoaded', () => {
  // Form interactions
  document.getElementById('add-btn').onclick = () => {
    const w = Number(document.getElementById('weight').value);
    const units = document.getElementById('units').value;
    const vol = document.getElementById('volume').value;
    if(!w || w <= 0){ alert('Enter a valid weight'); return; }
    addBag(w, units, vol ? Number(vol) : null);
    document.getElementById('weight').value = '';
    document.getElementById('volume').value = '';
  };

  document.getElementById('optimize-btn').onclick = optimize;
  document.getElementById('seed-btn').onclick = seedDemo;
  document.getElementById('reset-btn').onclick = () => { state.bags = []; render(); };
  document.getElementById('labels-btn').onclick = printLabels;

  // Initial render + demo seed
  render();
});


/** ---------------- Supervisor Sync (Front/Aft x Left/Right x 3 zones) ----------------
 Color→Zone mapping: red→1, yellow→2, blue→3
 FWD/AFT mapping: bag.zone === 'FWD' -> Front; 'AFT' -> Aft; 'MID' split evenly.
 Left/Right distribution: round-robin for each area+zone.
-------------------------------------------------------------------------------------**/

function persistSupervisorSnapshot(){
  const cells = {
    // FRONT
    'FWD.LEFT.1':{count:0, weightLb:0}, 'FWD.RIGHT.1':{count:0, weightLb:0},
    'FWD.LEFT.2':{count:0, weightLb:0}, 'FWD.RIGHT.2':{count:0, weightLb:0},
    'FWD.LEFT.3':{count:0, weightLb:0}, 'FWD.RIGHT.3':{count:0, weightLb:0},
    // AFT
    'AFT.LEFT.1':{count:0, weightLb:0}, 'AFT.RIGHT.1':{count:0, weightLb:0},
    'AFT.LEFT.2':{count:0, weightLb:0}, 'AFT.RIGHT.2':{count:0, weightLb:0},
    'AFT.LEFT.3':{count:0, weightLb:0}, 'AFT.RIGHT.3':{count:0, weightLb:0},
  };

  // Round-robin pointers per area+zone
  const rr = {
    'FWD.1':'LEFT', 'FWD.2':'LEFT', 'FWD.3':'LEFT',
    'AFT.1':'LEFT', 'AFT.2':'LEFT', 'AFT.3':'LEFT',
  };
  const toggle = side => side === 'LEFT' ? 'RIGHT' : 'LEFT';
  const zIndex = c => c === 'red' ? 1 : (c === 'yellow' ? 2 : (c === 'blue' ? 3 : null));

  // Balance MID between FWD and AFT
  let midToFront = true;

  if (!window.state || !Array.isArray(state.bags)) return;

  for(const b of state.bags){
    if(!b || !b.color) continue;
    const zoneNum = zIndex(b.color);
    if(!zoneNum) continue;

    let area = b.zone === 'AFT' ? 'AFT' : (b.zone === 'FWD' ? 'FWD' : null);

    if(!area){ area = midToFront ? 'FWD' : 'AFT'; midToFront = !midToFront; }

    const keyForRR = `${area}.${zoneNum}`;
    const side = rr[keyForRR];
    rr[keyForRR] = toggle(side);

    const cellKey = `${area}.${side}.${zoneNum}`;
    const cell = cells[cellKey];
    cell.count += 1;
    cell.weightLb += ((b.weightKg||0) * 2.20462);
  }

  const totals = {
    bags: state.bags.length,
    weightLb: state.bags.reduce((s,b)=> s + ((b.weightKg||0)*2.20462), 0)
  };

  const snapshot = {
    version: 1,
    perCellCap: 20,
    totals,
    cells
  };

  try{
    localStorage.setItem('balanceiq-supervisor', JSON.stringify(snapshot));
  }catch(e){ /* ignore storage issues */ }
}

// Hook snapshotting into existing renders if present
if (typeof render === 'function') {
  const _renderOrig = render;
  render = function(){
    _renderOrig();
    try{ persistSupervisorSnapshot(); }catch(e){}
  };
}