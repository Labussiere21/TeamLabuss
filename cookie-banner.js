(function () {
  if (localStorage.getItem('cookie_consent')) return;

  const style = document.createElement('style');
  style.textContent = `
    #cookie-banner {
      position: fixed;
      bottom: 0; left: 0; right: 0;
      background: #1a1a1a;
      color: rgba(255,255,255,0.88);
      padding: 1.1rem 2rem;
      z-index: 9999;
      display: flex;
      align-items: center;
      gap: 1.2rem;
      flex-wrap: wrap;
      box-shadow: 0 -4px 24px rgba(0,0,0,0.35);
      font-family: system-ui, sans-serif;
      font-size: 0.84rem;
      line-height: 1.5;
      transform: translateY(100%);
      transition: transform 0.35s cubic-bezier(.4,0,.2,1);
    }
    #cookie-banner.visible { transform: translateY(0); }
    #cookie-banner p { flex: 1; min-width: 240px; margin: 0; }
    #cookie-banner a { color: #7fff00; text-underline-offset: 2px; }
    .cb-btn {
      border: none; border-radius: 5px;
      padding: 0.48rem 1.1rem;
      font-size: 0.82rem; font-weight: 700;
      cursor: pointer; white-space: nowrap;
      transition: background 0.15s;
    }
    .cb-accept { background: #e0007a; color: #fff; }
    .cb-accept:hover { background: #ff3fa0; }
    .cb-refuse { background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.72); }
    .cb-refuse:hover { background: rgba(255,255,255,0.18); }
  `;
  document.head.appendChild(style);

  const banner = document.createElement('div');
  banner.id = 'cookie-banner';
  banner.innerHTML = `
    <p>
      🍪 Ce site utilise des cookies techniques nécessaires à son fonctionnement (sécurité Cloudflare) et charge des polices via Google Fonts. Aucun cookie publicitaire ou de traçage n'est utilisé.
      <a href="mentions-legales.html#cookies">En savoir plus</a>
    </p>
    <button class="cb-btn cb-refuse" id="cb-refuse">Continuer sans accepter</button>
    <button class="cb-btn cb-accept" id="cb-accept">J'ai compris</button>
  `;
  document.body.appendChild(banner);

  requestAnimationFrame(() => banner.classList.add('visible'));

  function close(choice) {
    localStorage.setItem('cookie_consent', choice);
    banner.style.transform = 'translateY(100%)';
    setTimeout(() => banner.remove(), 350);
  }

  document.getElementById('cb-accept').addEventListener('click', () => close('accepted'));
  document.getElementById('cb-refuse').addEventListener('click', () => close('refused'));
})();
