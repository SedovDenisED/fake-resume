/**
 * Скрытый вход в панель: 5 быстрых кликов по логотипу.
 * URL задаётся в data-panel-url у #logo-gate (доступен только из туннеля).
 */
document.addEventListener('DOMContentLoaded', function () {
  const gate = document.getElementById('logo-gate');
  if (!gate) {
    return;
  }

  const panelUrl = gate.dataset.panelUrl || '';
  const needed = 5;
  const windowMs = 2000;
  let clicks = 0;
  let timer = null;

  gate.addEventListener('click', function (event) {
    if (!panelUrl) {
      return;
    }
    event.preventDefault();
    clicks += 1;
    clearTimeout(timer);
    timer = setTimeout(function () {
      clicks = 0;
    }, windowMs);
    if (clicks >= needed) {
      clicks = 0;
      window.location.href = panelUrl;
    }
  });
});
