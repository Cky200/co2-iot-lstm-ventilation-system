const maxPoints = 120;

const elements = {
  connection: document.getElementById("connectionStatus"),
  co2: document.getElementById("co2Value"),
  voltage: document.getElementById("voltageValue"),
  relay: document.getElementById("relayState"),
  fanSpeed: document.getElementById("fanSpeed"),
  device: document.getElementById("deviceId"),
  lastSeen: document.getElementById("lastSeen"),
  badge: document.getElementById("qualityBadge"),
  ventMode: document.getElementById("ventMode"),
  ventReason: document.getElementById("ventReason"),
  ventRelay: document.getElementById("ventRelay"),
  alertList: document.getElementById("alertList"),
  alertCount: document.getElementById("alertCount"),
};

const chart = new Chart(document.getElementById("co2Chart"), {
  type: "line",
  data: {
    labels: [],
    datasets: [
      {
        label: "CO2 ppm",
        data: [],
        borderColor: "#1f6fb2",
        backgroundColor: "rgba(31, 111, 178, 0.12)",
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.25,
        fill: true,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    scales: {
      y: {
        suggestedMin: 350,
        suggestedMax: 1600,
        ticks: { callback: (value) => `${value} ppm` },
      },
    },
    plugins: {
      legend: { display: false },
      tooltip: { mode: "index", intersect: false },
    },
  },
});

function formatTime(value) {
  return new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function qualityFor(ppm) {
  if (ppm >= 1800) return ["Critical", "critical"];
  if (ppm >= 1200) return ["High", "warning"];
  if (ppm >= 900) return ["Elevated", "info"];
  return ["Normal", "normal"];
}

function setConnection(online) {
  elements.connection.textContent = online ? "Online" : "Offline";
  elements.connection.className = `connection ${online ? "online" : "offline"}`;
}

function updateTelemetry(point) {
  elements.co2.textContent = Math.round(point.co2_ppm).toString();
  elements.voltage.textContent = point.voltage == null ? "--" : Number(point.voltage).toFixed(2);
  elements.device.textContent = point.device_id || "--";
  elements.lastSeen.textContent = formatTime(point.timestamp);

  if (point.relay_state !== null && point.relay_state !== undefined) {
    elements.relay.textContent = point.relay_state ? "On" : "Off";
  }
  if (point.fan_speed_percent !== null && point.fan_speed_percent !== undefined) {
    elements.fanSpeed.textContent = `${Math.round(point.fan_speed_percent)}%`;
  }

  const [label, level] = qualityFor(point.co2_ppm);
  elements.badge.textContent = label;
  elements.badge.className = `badge ${level}`;

  chart.data.labels.push(formatTime(point.timestamp));
  chart.data.datasets[0].data.push(point.co2_ppm);
  if (chart.data.labels.length > maxPoints) {
    chart.data.labels.shift();
    chart.data.datasets[0].data.shift();
  }
  chart.update();
}

function updateVentilation(status) {
  elements.ventMode.textContent = status.mode || "auto";
  elements.ventReason.textContent = status.reason || "telemetry_update";
  elements.ventRelay.textContent = status.relay_state ? "on" : "off";
  elements.relay.textContent = status.relay_state ? "On" : "Off";
  elements.fanSpeed.textContent = `${Math.round(status.fan_speed_percent || 0)}%`;
}

function renderAlerts(alerts) {
  elements.alertList.innerHTML = "";
  elements.alertCount.textContent = alerts.length.toString();
  alerts.slice(-8).reverse().forEach((alert) => {
    const item = document.createElement("li");
    item.className = alert.level;
    item.innerHTML = `
      <div class="alert-title">
        <span>${alert.message}</span>
        <span>${Math.round(alert.co2_ppm)} ppm</span>
      </div>
      <div class="alert-meta">${formatTime(alert.timestamp)}</div>
    `;
    elements.alertList.appendChild(item);
  });
}

function addAlert(alert) {
  fetch("/api/alerts")
    .then((response) => response.json())
    .then((payload) => renderAlerts(payload.data))
    .catch(() => renderAlerts([alert]));
}

function applySnapshot(snapshot) {
  chart.data.labels = [];
  chart.data.datasets[0].data = [];
  (snapshot.history || []).forEach(updateTelemetry);
  updateVentilation(snapshot.ventilation || {});
  renderAlerts(snapshot.alerts || []);
}

const socket = io();

socket.on("connect", () => setConnection(true));
socket.on("disconnect", () => setConnection(false));
socket.on("state_snapshot", applySnapshot);
socket.on("telemetry_update", updateTelemetry);
socket.on("ventilation_status", updateVentilation);
socket.on("alert", addAlert);
