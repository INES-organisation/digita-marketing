document.addEventListener('DOMContentLoaded', function() {
  // Crée l'overlay s'il n'existe pas
  let overlay = document.querySelector('.sidebar-onglet-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'sidebar-onglet-overlay';
    document.body.appendChild(overlay);
  }

  // Fonction pour fermer tous les popups
  function closeAllPopups() {
    // Ferme tous les popups en fullscreen (qui peuvent être dans le body)
    document.querySelectorAll('.sidebar-onglet-popup-content.popup-fullscreen').forEach(popup => {
      popup.classList.remove('popup-fullscreen');
      
      // Remet le popup dans son conteneur d'origine
      if (popup.dataset.originalParent) {
        const originalParent = document.querySelector(`[data-popup-id="${popup.dataset.originalParent}"]`);
        if (originalParent) {
          originalParent.appendChild(popup);
        }
      }
      
      popup.removeAttribute('style');
    });
    
    // Retire la classe active de tous les onglets
    document.querySelectorAll('.sidebar-onglet-with-popup').forEach(tab => {
      tab.classList.remove('active-popup');
    });
    
    // Cache l'overlay
    overlay.classList.remove('active');
  }

  // Initialisation des popups
  document.querySelectorAll('.sidebar-onglet-with-popup').forEach((tab, index) => {
    const btn = tab.querySelector('.sidebar-onglet-link');
    const popup = tab.querySelector('.sidebar-onglet-popup-content');
    
    if (!btn || !popup) return;

    // Nom du service pour les lecteurs d'écran (le bouton ne contient qu'une icône)
    const title = popup.querySelector('.popup-title');
    if (title) btn.setAttribute('aria-label', title.textContent.trim());

    // Marque le conteneur avec un ID unique
    tab.dataset.popupId = `popup-container-${index}`;
    popup.dataset.originalParent = `popup-container-${index}`;

    // Crée le bouton de fermeture s'il n'existe pas
    let closeBtn = popup.querySelector('.sidebar-onglet-close');
    if (!closeBtn) {
      closeBtn = document.createElement('span');
      closeBtn.className = 'sidebar-onglet-close';
      closeBtn.title = 'Fermer';
      closeBtn.innerHTML = '&times;';
      popup.appendChild(closeBtn);
    }

    // Gestion du clic sur l'onglet
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      // Si le popup est déjà actif, on le ferme
      if (tab.classList.contains('active-popup')) {
        closeAllPopups();
        return;
      }
      
      // Ferme les autres popups
      closeAllPopups();
      
      // Déplace le popup dans le body pour éviter les problèmes de CSS hérité
      document.body.appendChild(popup);
      
      // Active ce popup
      tab.classList.add('active-popup');
      popup.classList.add('popup-fullscreen');
      
      // Affiche l'overlay
      overlay.classList.add('active');
    });

    // Gestion de la flèche d'expansion
    const expandArrow = popup.querySelector('.sidebar-onglet-expand-arrow');
    if (expandArrow) {
      expandArrow.addEventListener('click', function(e) {
        e.stopPropagation();
        
        // Si on est déjà en mode plein écran, on ne fait rien
        if (popup.classList.contains('popup-fullscreen')) {
          return;
        }
        
        // Déplace le popup dans le body
        document.body.appendChild(popup);
        
        // Passe en mode plein écran
        tab.classList.add('active-popup');
        popup.classList.add('popup-fullscreen');
        
        // Affiche l'overlay
        overlay.classList.add('active');
      });
    }

    // Gestion du bouton de fermeture
    if (closeBtn) {
      closeBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        closeAllPopups();
      });
    }

    // Empêche la fermeture quand on clique dans le popup
    popup.addEventListener('click', function(e) {
      e.stopPropagation();
    });
  });

  // Ferme les popups quand on clique sur l'overlay
  overlay.addEventListener('click', function() {
    closeAllPopups();
  });

  // Ferme les popups quand on clique en dehors
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.sidebar-onglet-popup-content') && 
        !e.target.closest('.sidebar-onglet-link') &&
        !e.target.classList.contains('sidebar-onglet-overlay')) {
      closeAllPopups();
    }
  });

  // Ferme avec la touche Échap
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      closeAllPopups();
    }
  });
});
