(() => {
  const BOOK_PAGES = [
    "./portfolio/book/book-page-01.jpg",
    "./portfolio/book/book-page-02.jpg",
    "./portfolio/book/book-page-03.jpg",
    "./portfolio/book/book-page-04.jpg",
    "./portfolio/book/book-page-05.jpg",
    "./portfolio/book/book-page-06.jpg",
    "./portfolio/book/book-page-07.jpg",
    "./portfolio/book/book-page-08.jpg",
    "./portfolio/book/book-page-09.jpg",
    "./portfolio/book/book-page-10.jpg",
  ];

  let currentPage = 0;
  let turning = false;

  function closeBook() {
    document.querySelector(".flipbook-backdrop")?.remove();
    document.body.classList.remove("flipbook-open");
  }

  function renderPage(dialog) {
    const image = dialog.querySelector(".flipbook-sheet img");
    const counter = dialog.querySelector(".flipbook-counter");
    const previous = dialog.querySelector(".flipbook-prev");
    const next = dialog.querySelector(".flipbook-next");
    image.src = BOOK_PAGES[currentPage];
    image.alt = `Страница ${currentPage + 1} из ${BOOK_PAGES.length}`;
    counter.textContent = `${currentPage + 1} / ${BOOK_PAGES.length}`;
    previous.disabled = currentPage === 0;
    next.disabled = currentPage === BOOK_PAGES.length - 1;
    dialog.querySelectorAll(".flipbook-dot").forEach((dot, index) => {
      dot.classList.toggle("active", index === currentPage);
      dot.setAttribute("aria-current", index === currentPage ? "page" : "false");
    });
  }

  function turnToPage(dialog, target) {
    if (turning) return;
    if (target < 0 || target >= BOOK_PAGES.length) return;
    if (target === currentPage) return;

    turning = true;
    const direction = target > currentPage ? 1 : -1;
    const sheet = dialog.querySelector(".flipbook-sheet");
    sheet.classList.add(direction > 0 ? "turn-next" : "turn-prev");

    window.setTimeout(() => {
      currentPage = target;
      renderPage(dialog);
      sheet.classList.remove("turn-next", "turn-prev");
      sheet.classList.add(direction > 0 ? "enter-next" : "enter-prev");
      requestAnimationFrame(() => {
        requestAnimationFrame(() => sheet.classList.remove("enter-next", "enter-prev"));
      });
      window.setTimeout(() => {
        turning = false;
      }, 330);
    }, 230);
  }

  function openBook(startPage = 0) {
    closeBook();
    currentPage = Math.max(0, Math.min(startPage, BOOK_PAGES.length - 1));

    const backdrop = document.createElement("div");
    backdrop.className = "flipbook-backdrop";
    backdrop.setAttribute("role", "dialog");
    backdrop.setAttribute("aria-modal", "true");
    backdrop.setAttribute("aria-label", "Фрагмент книги «Эпоксидная смола», 10 страниц");
    backdrop.innerHTML = `
      <div class="flipbook-dialog">
        <div class="flipbook-head">
          <div>
            <strong>Книга «Эпоксидная смола»</strong>
            <span>Фрагмент · 10 страниц</span>
          </div>
          <button class="flipbook-close" type="button" aria-label="Закрыть">×</button>
        </div>
        <div class="flipbook-stage">
          <button class="flipbook-arrow flipbook-prev" type="button" aria-label="Предыдущая страница">‹</button>
          <div class="flipbook-book">
            <div class="flipbook-sheet"><img alt="" /></div>
          </div>
          <button class="flipbook-arrow flipbook-next" type="button" aria-label="Следующая страница">›</button>
        </div>
        <div class="flipbook-foot">
          <div class="flipbook-dots" aria-label="Страницы">
            ${BOOK_PAGES.map((_, index) => `<button class="flipbook-dot" type="button" data-page="${index}" aria-label="Страница ${index + 1}"></button>`).join("")}
          </div>
          <span class="flipbook-counter"></span>
        </div>
      </div>`;

    const dialog = backdrop.querySelector(".flipbook-dialog");
    backdrop.addEventListener("click", (event) => {
      if (event.target === backdrop) closeBook();
    });
    dialog.querySelector(".flipbook-close").addEventListener("click", closeBook);
    dialog.querySelector(".flipbook-prev").addEventListener("click", () => turnToPage(dialog, currentPage - 1));
    dialog.querySelector(".flipbook-next").addEventListener("click", () => turnToPage(dialog, currentPage + 1));
    dialog.querySelector(".flipbook-book").addEventListener("click", (event) => {
      const rect = event.currentTarget.getBoundingClientRect();
      turnToPage(dialog, currentPage + (event.clientX < rect.left + rect.width / 2 ? -1 : 1));
    });
    dialog.querySelectorAll(".flipbook-dot").forEach((dot) => {
      dot.addEventListener("click", () => {
        const target = Number(dot.dataset.page);
        turnToPage(dialog, target);
      });
    });

    document.body.append(backdrop);
    document.body.classList.add("flipbook-open");
    renderPage(dialog);
  }

  function enhanceBook() {
    const cover = document.querySelector(".book-cover");
    const pages = document.querySelector(".book-pages");
    const link = document.querySelector(".book-link");
    if (!cover || !pages || !link) return false;

    const replaceClick = (element, startPage) => {
      const clone = element.cloneNode(true);
      element.replaceWith(clone);
      clone.addEventListener("click", (event) => {
        event.preventDefault();
        openBook(startPage);
      });
      return clone;
    };

    replaceClick(cover, 0);
    pages.querySelectorAll("button").forEach((button, index) => replaceClick(button, index + 1));
    const newLink = replaceClick(link, 0);
    newLink.removeAttribute("href");
    newLink.removeAttribute("target");
    newLink.textContent = "Перелистать 10 страниц";
    return true;
  }

  function start() {
    if (enhanceBook()) return;
    const observer = new MutationObserver(() => {
      if (enhanceBook()) observer.disconnect();
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });
  }

  document.addEventListener("keydown", (event) => {
    const dialog = document.querySelector(".flipbook-dialog");
    if (event.key === "Escape") closeBook();
    if (dialog && event.key === "ArrowLeft") turnToPage(dialog, currentPage - 1);
    if (dialog && event.key === "ArrowRight") turnToPage(dialog, currentPage + 1);
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start, { once: true });
  } else {
    start();
  }
})();
