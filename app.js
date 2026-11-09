// Filtros, búsqueda y "hace X min". Sin cookies ni almacenamiento: nada se guarda en el navegador.
(function () {
  var hilo = document.getElementById("hilo");
  if (!hilo) return;
  var items = Array.prototype.slice.call(hilo.querySelectorAll(".item"));
  var dias = Array.prototype.slice.call(hilo.querySelectorAll("[data-dia]"));
  var chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
  var q = document.getElementById("q");
  var sinres = document.getElementById("sinres");
  var seccion = "todas";

  function norm(t) {
    return (t || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  function aplicar() {
    var texto = norm(q ? q.value.trim() : "");
    var visibles = 0;
    items.forEach(function (li) {
      var ok = (seccion === "todas" || li.dataset.s === seccion) &&
               (!texto || norm(li.textContent).indexOf(texto) !== -1);
      li.hidden = !ok;
      if (ok) visibles++;
    });
    // oculta las cabeceras de día que se quedan sin noticias
    dias.forEach(function (d) {
      var sig = d.nextElementSibling, alguno = false;
      while (sig && !sig.hasAttribute("data-dia")) { if (!sig.hidden) alguno = true; sig = sig.nextElementSibling; }
      d.hidden = !alguno;
    });
    if (sinres) sinres.hidden = visibles > 0 || items.length === 0;
  }

  chips.forEach(function (b) {
    b.addEventListener("click", function () {
      seccion = b.dataset.s;
      chips.forEach(function (c) { c.setAttribute("aria-pressed", String(c === b)); });
      aplicar();
    });
  });
  if (q) q.addEventListener("input", aplicar);

  function hace(iso) {
    var m = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
    if (isNaN(m) || m < 0) return "";
    if (m < 1) return "ahora mismo";
    if (m < 60) return "hace " + m + " min";
    var h = Math.floor(m / 60);
    return h < 24 ? "hace " + h + " h" : "";
  }
  function relojes() {
    document.querySelectorAll(".hace[data-t]").forEach(function (s) { s.textContent = hace(s.dataset.t); });
  }
  relojes();
  setInterval(relojes, 60000);

  // Si la página lleva más de 70 minutos abierta, recarga para traer la nueva edición.
  var gen = document.getElementById("generado");
  if (gen) {
    setInterval(function () {
      if (Date.now() - new Date(gen.getAttribute("datetime")).getTime() > 70 * 60000 && !document.hidden) location.reload();
    }, 5 * 60000);
  }
})();
