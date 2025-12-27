// static/js/home.js
document.addEventListener("DOMContentLoaded", function () {
  // ==================== CAROUSEL ====================
  const slide = document.querySelector(".carousel-slide");
  const images = slide.querySelectorAll("img");
  const prev = document.querySelector(".carousel-prev");
  const next = document.querySelector(".carousel-next");
  const dotsContainer = document.querySelector(".carousel-dots");

  let index = 0;
  const total = images.length;

  // Tạo dots tự động
images.forEach((_, i) => {
  const dot = document.createElement("span");
  dot.className = "dot";
  dot.innerHTML = "․";
  dot.addEventListener("click", () => goTo(i));
  dotsContainer.appendChild(dot);
});
  const dots = dotsContainer.querySelectorAll("span");
  if (dots.length > 0) dots[0].classList.add("active");

  function update() {
    slide.style.transform = `translateX(${-index * 100}%)`;
    dots.forEach((d, i) => d.classList.toggle("active", i === index));
  }

  function goTo(n) {
    index = (n + total) % total;
    update();
    resetTimer();
  }

  prev.addEventListener("click", () => goTo(index - 1));
  next.addEventListener("click", () => goTo(index + 1));

  // Auto slide 5s
  let timer = setInterval(() => goTo( index + 1), 5000);
  function resetTimer() {
    clearInterval(timer);
    timer = setInterval(() => goTo(index + 1), 5000);
  }

  // Pause khi hover/touch
  const container = document.querySelector(".carousel-container");
  container.addEventListener("mouseenter", () => clearInterval(timer));
  container.addEventListener("mouseleave", resetTimer);
  container.addEventListener("touchstart", () => clearInterval(timer), {
    passive: true,
  });
  container.addEventListener("touchend", resetTimer);

  update();

  // ==================== AUTOCOMPLETE + FORM ====================
  let names = [];

  fetch("/api/names")
    .then((r) => r.json())
    .then((d) => {
      names = d.names;
    })
    .catch(console.error);

  const input = document.getElementById("name");
  const suggestionsDiv = document.getElementById("autocomplete-suggestions");
  const form = document.getElementById("name-form");

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
// Trong hàm updateSuggestionsPosition()
suggestionsDiv.style.display = "block";
suggestionsDiv.style.visibility = "hidden";
void suggestionsDiv.offsetHeight; // force reflow
// ... phần tính top/left còn lại ...

// Thêm dòng này ở cuối hàm
suggestionsDiv.classList.add('visible-scroll'); // chỉ để trigger
setTimeout(() => suggestionsDiv.classList.remove('visible-scroll'), 50);

