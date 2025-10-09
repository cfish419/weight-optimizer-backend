
// supervisor-sync.v2.js — drop-in replacement for /assets/js/supervisor-sync.js
// - Writes every 1s if window.state.bags exists
// - Adds `ts` timestamp and change-hash to avoid stale overwrites
// - Adds lightweight console logs you can toggle with DEBUG=true
(function(){
  const DEBUG = false; // set to true to see console logs

  function log(...args){ if (DEBUG) console.log('[supervisor-sync]', ...args); }
  function zIndex(c){
    if (!c) return null;
    c = String(c).toLowerCase();
    if (c === 'red') return 1;
    if (c === 'yellow') return 2;
    if (c === 'blue') return 3;
    return null;
  }
  function djb2(s){ let h=5381; for(let i=0;i<s.length;i++){ h=((h<<5)+h)+s.charCodeAt(i); } return h>>>0; }

  let lastHash = null;

  function build(){
    if (!window.state || !Array.isArray(window.state.bags)) {
      log('No state.bags found');
      return null;
    }
    const cells = {
      'FWD.LEFT.1':{count:0, weightLb:0}, 'FWD.RIGHT.1':{count:0, weightLb:0},
      'FWD.LEFT.2':{count:0, weightLb:0}, 'FWD.RIGHT.2':{count:0, weightLb:0},
      'FWD.LEFT.3':{count:0, weightLb:0}, 'FWD.RIGHT.3':{count:0, weightLb:0},
      'AFT.LEFT.1':{count:0, weightLb:0}, 'AFT.RIGHT.1':{count:0, weightLb:0},
      'AFT.LEFT.2':{count:0, weightLb:0}, 'AFT.RIGHT.2':{count:0, weightLb:0},
      'AFT.LEFT.3':{count:0, weightLb:0}, 'AFT.RIGHT.3':{count:0, weightLb:0},
    };
    const rr = {'FWD.1':'LEFT','FWD.2':'LEFT','FWD.3':'LEFT','AFT.1':'LEFT','AFT.2':'LEFT','AFT.3':'LEFT'};
    const toggle = s => s === 'LEFT' ? 'RIGHT' : 'LEFT';

    let midToFront = true;
    let totalLb = 0;

    for(const b of window.state.bags){
      if(!b) continue;
      const zoneNum = zIndex(b.color);
      const kg = Number(b.weightKg||0);
      const lb = kg * 2.20462;
      totalLb += lb;
      // If no color (no zone), still count into totals but skip mapping
      if(!zoneNum) continue;

      let area = (b.zone === 'FWD') ? 'FWD' : (b.zone === 'AFT' ? 'AFT' : null);
      if(!area){ area = midToFront ? 'FWD' : 'AFT'; midToFront = !midToFront; }

      const key = `${area}.${zoneNum}`;
      const side = rr[key]; rr[key] = toggle(side);
      const cellKey = `${area}.${side}.${zoneNum}`;
      cells[cellKey].count += 1;
      cells[cellKey].weightLb += lb;
    }

    const snap = {
      version: 2,
      perCellCap: 20,
      totals: { bags: window.state.bags.length, weightLb: totalLb },
      ts: Date.now(),
      cells
    };
    return snap;
  }

  function persist(force=false){
    const snap = build();
    if(!snap) return;
    const h = djb2(JSON.stringify(snap));
    if (!force && h === lastHash) { return; }
    lastHash = h;
    try {
      localStorage.setItem('balanceiq-supervisor', JSON.stringify(snap));
      log('wrote snapshot', snap.totals, new Date(snap.ts).toLocaleTimeString());
    } catch(e) {
      log('localStorage error', e);
    }
  }

  // public debug hook
  window.__balanceiqPersist = (force)=>persist(force!==false);

  // periodic writer
  persist(true);
  setInterval(persist, 1000);

  // attempt to hook common functions (safe if they don't exist)
  ['addBag','optimize','removeBag','resetBags'].forEach(fn=>{
    if (typeof window[fn] === 'function') {
      const orig = window[fn];
      window[fn] = function(){
        const r = orig.apply(this, arguments);
        try{ persist(true); }catch(e){}
        return r;
      };
      log('hooked', fn);
    }
  });

  window.addEventListener('beforeunload', ()=>{ try{ persist(true); }catch(e){} });
})();
