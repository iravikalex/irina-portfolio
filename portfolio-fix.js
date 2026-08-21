(() => {
  const PDF_URL = "./portfolio/book/epoxy-resin-guide.pdf#page=1&view=FitH";

  function closeBook() {
    document.querySelector(".book-reader-backdrop")?.remove();
    document.body.classList.remove("book-reader-open");
  }

  function openBook() {
    closeBook();

    const backdrop = document.createElement("div");
    backdrop.className = "book-reader-backdrop";
    backdrop.setAttribute("role", "dialog");
    backdrop.setAttribute("aria-modal", "true");
    backdrop.setAttribute("aria-label", "Книга «Эпоксидная смола», 65 страниц");
    backdrop.innerHTML = `
      <div class="book-reader">
        <div class="book-reader-bar">
          <div>
            <strong>Книга «Эпоксидная смола»</strong>
            <span>65 страниц</span>
          </div>
          <a href="./portfolio/book/epoxy-resin-guide.pdf" target="_blank" rel="noreferrer">Открыть отдельно</a>
          <button type="button" aria-label="Закрыть книгу">×</button>
        </div>
        <object data="${PDF_URL}" type="application/pdf" class="book-reader-frame">
          <div class="book-reader-fallback">
            <p>Откройте книгу в отдельной вкладке, чтобы прочитать все 65 страниц.</p>
            <a href="./portfolio/book/epoxy-resin-guide.pdf" target="_blank" rel="noreferrer">Открыть книгу</a>
          </div>
        </object>
      </div>`;

    backdrop.addEventListener("click", (event) => {
      if (event.target === backdrop) closeBook();
    });
    backdrop.querySelector("button").addEventListener("click", closeBook);
    document.body.append(backdrop);
    document.body.classList.add("book-reader-open");
  }

  function enhanceBook() {
    const cover = document.querySelector(".book-cover");
    const pages = document.querySelector(".book-pages");
    const bookSection = document.querySelector(".book-section");
    if (!cover || !pages || !bookSection) return false;

    const replaceClick = (element) => {
      const clone = element.cloneNode(true);
      element.replaceWith(clone);
      clone.addEventListener("click", openBook);
      return clone;
    };

    const newCover = replaceClick(cover);
    const coverLabel = newCover.querySelector("span");
    if (coverLabel) coverLabel.textContent = "Листать все 65 страниц";

    pages.querySelectorAll("button").forEach(replaceClick);

    const callout = document.createElement("div");
    callout.className = "full-book-callout section-shell";
    callout.innerHTML = `
      <div>
        <strong>Полная книга — 65 страниц</strong>
        <span>Открывается целиком, страницы можно листать и увеличивать.</span>
      </div>
      <button type="button">Листать книгу</button>`;
    callout.querySelector("button").addEventListener("click", openBook);
    pages.insertAdjacentElement("afterend", callout);

    bookSection.querySelectorAll(".book-link").forEach((link) => {
      link.textContent = "Открыть все 65 страниц";
    });
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
    if (event.key === "Escape") closeBook();
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start, { once: true });
  } else {
    start();
  }
})();
