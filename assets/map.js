// Draws the pins from the JSON block that build.py writes into index.html,
// and wires the search box and category checkboxes to both the map and the list.
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
    var lines = [s.labels[e.type] + " · " + e.city];
    if (e.tags && e.tags.length) lines.push(e.tags.join(", "));
    if (e.note) lines.push(e.note);
    lines.forEach(function (text) {
      var p = document.createElement("div");
      p.textContent = text;
      box.appendChild(p);
    });
    return box;
  }

  // Lower-case and drop accents, so "montreal" finds "Montréal".
  function fold(text) {
    return String(text).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }

  // Entries and table rows are written in the same order, so index i is the same entry in both.
  var rows = document.querySelectorAll("tr[data-type]");
  var pins = L.layerGroup().addTo(map);
  var items = data.entries.map(function (e, i) {
    var icon = L.divIcon({ className: "pin pin-" + e.type, iconSize: [14, 14] });
    var marker = L.marker([e.lat, e.lon], { icon: icon, title: e.name, alt: e.name }).bindPopup(popup(e));
    marker.addTo(pins);
    var text = [e.name, e.city, s.labels[e.type], (e.tags || []).join(" "), e.note || ""].join(" ");
    return { entry: e, marker: marker, row: rows[i], text: fold(text), shown: true };
  });

  var shownTypes = {};
  Object.keys(s.labels).forEach(function (t) { shownTypes[t] = true; });
  var search = document.getElementById("map-search");
  var count = document.getElementById("map-count");

  function update(fit) {
    var words = search ? fold(search.value).split(/\s+/).filter(Boolean) : [];
    var visible = [];
    items.forEach(function (it) {
      var show = shownTypes[it.entry.type] && words.every(function (w) { return it.text.indexOf(w) !== -1; });
      if (show !== it.shown) {
        if (show) pins.addLayer(it.marker); else pins.removeLayer(it.marker);
        it.shown = show;
      }
      if (it.row) it.row.hidden = !show;
      if (show) visible.push(it.marker.getLatLng());
    });
    if (count) {
      count.textContent = words.length || visible.length !== items.length
        ? "Showing " + visible.length + " of " + items.length + "." : "";
    }
    // Zoom to the matches, but never closer than city level.
    if (fit && words.length && visible.length) {
      map.fitBounds(L.latLngBounds(visible), { maxZoom: Math.max(s.zoom, 9), padding: [30, 30] });
    }
  }

  document.querySelectorAll(".filters input[type=checkbox]").forEach(function (box) {
    box.addEventListener("change", function () {
      shownTypes[box.value] = box.checked;
      update(false);
    });
  });

  if (search) {
    search.closest(".search").hidden = false;
    var timer;
    search.addEventListener("input", function () {
      clearTimeout(timer);
      timer = setTimeout(function () { update(true); }, 200);
    });
  }

  // Let people scroll the page past the map; zoom with the wheel only after clicking in.
  map.on("click", function () { map.scrollWheelZoom.enable(); });
  mapEl.addEventListener("mouseleave", function () { map.scrollWheelZoom.disable(); });
})();
