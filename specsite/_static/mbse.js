// Click a diagram to open it in an overlay fitted to the screen.
// Wheel zooms around the cursor, drag pans, double-click refits,
// Esc or the button closes. Boxes stay clickable at any zoom.
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("svg.mbse-diagram").forEach(function (src) {
    src.addEventListener("click", function (e) {
      if (e.target.closest("a")) return;          // a box link: let it navigate
      openViewer(src);
    });
  });

  function openViewer(src) {
    var overlay = document.createElement("div");
    overlay.className = "mbse-overlay";
    overlay.innerHTML =
      '<button class="mbse-close">Close (Esc)</button>' +
      '<div class="mbse-hint">wheel: zoom · drag: pan · double-click: fit · click a box: open it</div>' +
      '<div class="mbse-stage"></div>';
    var stage = overlay.querySelector(".mbse-stage");
    var svg = src.cloneNode(true);
    svg.classList.remove("mbse-diagram"); svg.classList.add("mbse-view");
    svg.style.width = "100%"; svg.style.height = "100%";
    stage.appendChild(svg);
    document.body.appendChild(overlay);

    var nat = (svg.getAttribute("viewBox") || "").split(/[\s,]+/).map(Number); // natural box
    var vb, home;
    function apply() { svg.setAttribute("viewBox", vb.join(" ")); }
    // Initial scale: fit the screen if that is still readable (>= 60 % of
    // natural size); otherwise open at 1:1 anchored at the start. Never upscale.
    function fitInitial() {
      var r = stage.getBoundingClientRect();
      var fit = Math.min(r.width / nat[2], r.height / nat[3]);
      var s = fit >= 0.8 ? Math.min(fit, 1) : 1;
      var w = r.width / s, h = r.height / s;
      var x = s === fit ? nat[0] - (w - nat[2]) / 2 : nat[0] - 24;
      var y = s === fit ? nat[1] - (h - nat[3]) / 2 : nat[1] - 24;
      vb = [x, y, w, h]; home = vb.slice(); apply();
    }
    fitInitial();

    svg.addEventListener("wheel", function (e) {
      e.preventDefault();
      var r = svg.getBoundingClientRect();
      var mx = vb[0] + (e.clientX - r.left) / r.width * vb[2];
      var my = vb[1] + (e.clientY - r.top) / r.height * vb[3];
      var k = e.deltaY < 0 ? 0.85 : 1.18;
      vb = [mx - (mx - vb[0]) * k, my - (my - vb[1]) * k, vb[2] * k, vb[3] * k];
      apply();
    }, { passive: false });

    var drag = null, moved = false;
    svg.addEventListener("mousedown", function (e) {
      if (e.button !== 0) return;
      drag = { x: e.clientX, y: e.clientY, vb: vb.slice() }; moved = false; e.preventDefault();
    });
    window.addEventListener("mousemove", function (e) {
      if (!drag) return;
      var r = svg.getBoundingClientRect();
      vb[0] = drag.vb[0] - (e.clientX - drag.x) / r.width * vb[2];
      vb[1] = drag.vb[1] - (e.clientY - drag.y) / r.height * vb[3];
      moved = true; apply();
    });
    window.addEventListener("mouseup", function () { drag = null; });
    svg.addEventListener("click", function (e) { if (moved) e.preventDefault(); }, true);
    svg.addEventListener("dblclick", function () { fitInitial(); });

    function remove() { overlay.remove(); document.removeEventListener("keydown", onKey); }
    function onKey(e) { if (e.key === "Escape") remove(); }
    overlay.querySelector(".mbse-close").addEventListener("click", remove);
    document.addEventListener("keydown", onKey);
  }
});
