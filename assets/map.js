// Draws the pins from the JSON block that build.py writes into index.html,
// and wires the Players / Clubs / Shops checkboxes to both the map and the list.
(function () {
  "use strict";
  var dataEl = document.getElementById("map-data");
  var mapEl = document.getElementById("map");
  if (!dataEl || !mapEl || !window.L) return;

  var data = JSON.parse(dataEl.textContent);
  var s = data.settings;
  var map = L.map(mapEl, { scrollWheelZoom: false }).setView(s.center, s.zoom);
  L.tileLayer(s.tiles, { maxZoom: 18, attribution: s.attribution }).addTo(map);

  // Popups are built from DOM nodes, never HTML strings, so names can't inject markup.
  function popup(e) {
    var box = document.createElement("div");
    var title = document.createElement("strong");
    if (e.link) {
      var a = document.createElement("a");
      a.href = e.link;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = e.name;
      title.appendChild(a);
    } else {
      title.textContent = e.name;
    }
    box.appendChild(title);
    var lines = [s.types[e.type] + " · " + e.city];
    if (e.toys && e.toys.length) lines.push(e.toys.join(", "));
    if (e.note) lines.push(e.note);
    lines.forEach(function (text) {
      var p = document.createElement("div");
      p.textContent = text;
      box.appendChild(p);
    });
    return box;
  }

  var layers = {};
  Object.keys(s.types).forEach(function (t) { layers[t] = L.layerGroup().addTo(map); });
  data.entries.forEach(function (e) {
    var icon = L.divIcon({ className: "pin pin-" + e.type, iconSize: [14, 14] });
    L.marker([e.lat, e.lon], { icon: icon, title: e.name, alt: e.name })
      .bindPopup(popup(e))
      .addTo(layers[e.type]);
  });

  var rows = document.querySelectorAll("tr[data-type]");
  document.querySelectorAll(".filters input[type=checkbox]").forEach(function (box) {
    box.addEventListener("change", function () {
      var t = box.value;
      if (box.checked) map.addLayer(layers[t]); else map.removeLayer(layers[t]);
      rows.forEach(function (row) {
        if (row.getAttribute("data-type") === t) row.hidden = !box.checked;
      });
    });
  });

  // Let people scroll the page past the map; zoom with the wheel only after clicking in.
  map.on("click", function () { map.scrollWheelZoom.enable(); });
  mapEl.addEventListener("mouseleave", function () { map.scrollWheelZoom.disable(); });
})();
