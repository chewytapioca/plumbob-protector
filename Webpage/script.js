(function () {
  var STORAGE_KEY = "pp-checklist-v1";

  var boxes = Array.prototype.slice.call(document.querySelectorAll("#checks input"));
  var face = document.getElementById("face");
  var meterText = document.getElementById("meterText");
  var meterSub = document.getElementById("meterSub");
  var bar = document.getElementById("bar");
  var barFill = document.getElementById("barFill");

  var faces = ["(・_・)", "(・ω・)", "(◕‿◕)", "(๑>◡<๑)", "(ﾉ◕ヮ◕)ﾉ✧"];
  var messages = [
    "Start with where the file comes from.",
    "Nice start. Keep going.",
    "You're checking like a pro.",
    "Almost there.",
    "All checked. Happy downloading!"
  ];

  function loadSaved() {
    try {
      var saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
      boxes.forEach(function (box, i) {
        box.checked = !!saved[i];
      });
    } catch (e) {}
  }

  function save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(boxes.map(function (box) {
        return box.checked;
      })));
    } catch (e) {}
  }

  function render() {
    var done = boxes.filter(function (box) { return box.checked; }).length;
    var total = boxes.length;
    var step;

    if (done === 0) {
      step = 0;
    } else if (done === total) {
      step = 4;
    } else {
      step = Math.min(3, Math.ceil((done / total) * 3));
    }

    face.textContent = faces[step];
    meterSub.textContent = messages[step];
    meterText.textContent = done + " of " + total + " checked";
    barFill.style.width = (done / total * 100) + "%";
    bar.setAttribute("aria-valuenow", done);
  }

  boxes.forEach(function (box) {
    box.addEventListener("change", function () {
      save();
      render();
    });
  });

  document.getElementById("reset").addEventListener("click", function () {
    boxes.forEach(function (box) { box.checked = false; });
    save();
    render();
  });

  loadSaved();
  render();
})();