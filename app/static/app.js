const PRESETS = {
  billing_true: {
    text: "tax invoice not received for water purifier, double payment deducted from credit card",
    product: "Water Purifier",
    warranty: "in_warranty",
    channel: "email"
  },
  billing_trap: {
    text: "water purifier leaking water from bottom, paid for repair in full yesterday pls send technician",
    product: "Water Purifier",
    warranty: "in_warranty",
    channel: "chat"
  },
  repair_breakdown: {
    text: "induction cooktop tripping the mcb immediately upon turning on, spark sound inside",
    product: "Induction Cooktop",
    warranty: "in_warranty",
    channel: "ivr"
  },
  consumable: {
    text: "need replacement ro membrane and sediment candle filter pack for purifier",
    product: "Water Purifier",
    warranty: "shield",
    channel: "whatsapp"
  },
  install: {
    text: "new air fryer delivered yesterday, need technician visit for wall mounting and demo",
    product: "Air Fryer",
    warranty: "in_warranty",
    channel: "chat"
  },
  return_replace: {
    text: "mixer grinder arrived with cracked jar and damaged packaging, please arrange return pickup",
    product: "Mixer Grinder",
    warranty: "in_warranty",
    channel: "chat"
  },
  warranty: {
    text: "how to register kestrel shield extended warranty plan for room heater bought last week",
    product: "Room Heater",
    warranty: "shield",
    channel: "whatsapp"
  },
  advice: {
    text: "what is the recommended temperature setting for baking cake in air fryer model AF300",
    product: "Air Fryer",
    warranty: "in_warranty",
    channel: "email"
  }
};

document.getElementById('examplePresets').addEventListener('change', (e) => {
  const key = e.target.value;
  if (key && PRESETS[key]) {
    const item = PRESETS[key];
    document.getElementById('requestText').value = item.text;
    document.getElementById('productFamily').value = item.product;
    document.getElementById('warrantyStatus').value = item.warranty;
    document.getElementById('channel').value = item.channel;
  }
});

document.getElementById('routingForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const payload = {
    request_text: document.getElementById('requestText').value.trim(),
    product_family: document.getElementById('productFamily').value,
    warranty_status: document.getElementById('warrantyStatus').value,
    channel: document.getElementById('channel').value
  };

  const btn = document.getElementById('routeBtn');
  const btnText = btn.querySelector('.btn-text');
  const btnSpinner = document.getElementById('btnSpinner');

  btnText.textContent = 'Routing...';
  btnSpinner.style.display = 'inline-block';
  btn.disabled = true;

  try {
    const res = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Prediction request failed');
    }

    const data = await res.json();
    renderResults(data);
  } catch (err) {
    alert(`Error: ${err.message}`);
  } finally {
    btnText.textContent = 'Route Request';
    btnSpinner.style.display = 'none';
    btn.disabled = false;
  }
});

function renderResults(data) {
  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('resultsContent').style.display = 'block';
  document.getElementById('inferenceBadge').textContent = 'Assigned: ' + data.predicted_team;

  document.getElementById('predictedTeam').textContent = data.predicted_team;
  const pct = (data.confidence * 100).toFixed(1) + '%';
  document.getElementById('confidenceVal').textContent = pct;
  document.getElementById('confidenceBar').style.width = pct;

  // Render reasons
  const reasonsList = document.getElementById('reasonsList');
  reasonsList.innerHTML = '';
  data.reasons.forEach(r => {
    const li = document.createElement('li');
    li.textContent = r;
    reasonsList.appendChild(li);
  });

  // Render probabilities
  const probTable = document.getElementById('probTable');
  probTable.innerHTML = '';
  const sorted = Object.entries(data.probabilities).sort((a, b) => b[1] - a[1]);
  
  sorted.forEach(([team, p]) => {
    const row = document.createElement('div');
    row.className = 'prob-row';
    row.innerHTML = `
      <div class="prob-name">${team}</div>
      <div class="prob-bar-wrap">
        <div class="prob-bar-inner" style="width: ${(p * 100).toFixed(1)}%;"></div>
      </div>
      <div class="prob-val">${(p * 100).toFixed(1)}%</div>
    `;
    probTable.appendChild(row);
  });

  document.getElementById('modelSignal').textContent = data.model_signal;
}
