// static/js/home.js
document.addEventListener("DOMContentLoaded", function () {
  // ==================== AUTOCOMPLETE + FORM ====================
  let names = [];
  let namesLoaded = false;

  const input = document.getElementById("name");
  const suggestionsDiv = document.getElementById("autocomplete-suggestions");
  const form = document.getElementById("name-form");

  // ---- Loading state cho input khi fetch /api/names ----
  input.setAttribute("placeholder", "Đang tải...");
  input.disabled = true;

  fetch("/api/names")
    .then((r) => r.json())
    .then((d) => {
      names = d.names;
      namesLoaded = true;
      input.disabled = false;
      input.setAttribute("placeholder", "Nhập tên của bạn vào");
    })
    .catch(() => {
      // Nếu lỗi vẫn cho nhập bình thường, không block người dùng
      namesLoaded = true;
      input.disabled = false;
      input.setAttribute("placeholder", "Nhập tên của bạn vào");
    });

  function updateSuggestionsPosition() {
    if (suggestionsDiv.children.length === 0) {
      suggestionsDiv.style.display = "none";
      return;
    }

    suggestionsDiv.style.display = "block";
    suggestionsDiv.style.visibility = "hidden";
    void suggestionsDiv.offsetHeight; // force reflow
    const boxWidth = suggestionsDiv.offsetWidth;

    const rect = input.getBoundingClientRect();
    const scrollLeft =
      window.pageXOffset || document.documentElement.scrollLeft;
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

    const top = rect.bottom + scrollTop + 8;
    let left = rect.left + scrollLeft + rect.width / 2 - boxWidth / 2;

    left = Math.max(16, Math.min(left, window.innerWidth - boxWidth - 16));

    suggestionsDiv.style.top = `${top}px`;
    suggestionsDiv.style.left = `${left}px`;
    suggestionsDiv.style.visibility = "visible";
  }

  function hideSuggestions() {
    suggestionsDiv.innerHTML = "";
    suggestionsDiv.style.display = "none";
  }

  input.addEventListener("input", function () {
    const query = this.value.toLowerCase().trim();
    suggestionsDiv.innerHTML = "";
    if (!query) {
      hideSuggestions();
      return;
    }
    const matches = names.filter((n) => n.toLowerCase().includes(query));
    if (matches.length === 0) {
      hideSuggestions();
      return;
    }
    matches.forEach((match) => {
      const div = document.createElement("div");
      div.className = "autocomplete-suggestion";
      div.textContent = match;
      div.addEventListener("click", () => {
        input.value = match;
        hideSuggestions();
      });
      suggestionsDiv.appendChild(div);
    });
    updateSuggestionsPosition();
    suggestionsDiv.style.display = "block";
  });

  suggestionsDiv.addEventListener("click", (e) => {
    if (e.target.classList.contains("autocomplete-suggestion")) {
      input.value = e.target.textContent;
      hideSuggestions();
    }
  });

  // Form submit + iOS audio unlock
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    const name = input.value.trim();
    if (!name) return;
    hideSuggestions();
    sessionStorage.setItem("audio_allowed", "true");

    const url = new URL(this.action, window.location.origin);
    url.searchParams.set("name", name);
    location.href = url.toString();
  });

  // Reposition khi scroll/resize
  ["scroll", "resize"].forEach((ev) => {
    window.addEventListener(ev, () => {
      if (suggestionsDiv.style.display === "block") {
        updateSuggestionsPosition();
      }
    });
  });

  // Touch feedback
  const btn = document.querySelector(".btn-primary");
  if (btn) {
    btn.addEventListener("touchstart", () => btn.classList.add("tapped"));
    btn.addEventListener("touchend", () =>
      setTimeout(() => btn.classList.remove("tapped"), 100)
    );
  }

  suggestionsDiv.addEventListener(
    "touchstart",
    (e) => {
      if (e.target.classList.contains("autocomplete-suggestion")) {
        e.target.classList.add("tapped");
      }
    },
    true
  );

  suggestionsDiv.addEventListener(
    "touchend",
    (e) => {
      if (e.target.classList.contains("autocomplete-suggestion")) {
        setTimeout(() => e.target.classList.remove("tapped"), 1000);
      }
    },
    true
  );
});