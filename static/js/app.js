const navToggle = document.querySelector("[data-nav-toggle]");
const siteNav = document.querySelector("[data-site-nav]");

if (navToggle && siteNav) {
  navToggle.addEventListener("click", () => {
    siteNav.classList.toggle("is-open");
  });
}

const revealItems = document.querySelectorAll(".reveal");
if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 },
  );
  revealItems.forEach((item) => observer.observe(item));
} else {
  revealItems.forEach((item) => item.classList.add("is-visible"));
}

const messageStack = document.querySelector("[data-messages]");
if (messageStack) {
  window.setTimeout(() => {
    messageStack.style.opacity = "0";
    messageStack.style.transform = "translateY(-8px)";
  }, 4200);
}

function drawGenreChart(canvas) {
  const raw = canvas.dataset.genres || "[]";
  let data = [];
  try {
    data = JSON.parse(raw);
  } catch (error) {
    data = [];
  }
  const ctx = canvas.getContext("2d");
  const ratio = window.devicePixelRatio || 1;
  const width = canvas.clientWidth || canvas.parentElement.clientWidth;
  const height = Number(canvas.getAttribute("height")) || 220;
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  ctx.scale(ratio, ratio);
  ctx.clearRect(0, 0, width, height);

  if (!data.length) {
    ctx.fillStyle = "#63706d";
    ctx.font = "14px Inter, sans-serif";
    ctx.fillText("No collection data yet.", 12, 26);
    return;
  }

  const palette = ["#1f6f5b", "#c47a28", "#285f8f", "#b64b57", "#6d6b3f", "#423b77"];
  const max = Math.max(...data.map((item) => item.total), 1);
  const barGap = 12;
  const barWidth = Math.max((width - barGap * (data.length + 1)) / data.length, 20);

  data.forEach((item, index) => {
    const barHeight = Math.max((item.total / max) * (height - 72), 8);
    const x = barGap + index * (barWidth + barGap);
    const y = height - barHeight - 36;
    ctx.fillStyle = palette[index % palette.length];
    ctx.fillRect(x, y, barWidth, barHeight);
    ctx.fillStyle = "#17211f";
    ctx.font = "700 12px Inter, sans-serif";
    ctx.fillText(String(item.total), x, y - 8);
    ctx.save();
    ctx.translate(x + 2, height - 16);
    ctx.rotate(-0.3);
    ctx.fillStyle = "#63706d";
    ctx.font = "12px Inter, sans-serif";
    ctx.fillText(item.genre, 0, 0);
    ctx.restore();
  });
}

const genreChart = document.getElementById("genreChart");
if (genreChart) {
  drawGenreChart(genreChart);
  window.addEventListener("resize", () => drawGenreChart(genreChart));
}
