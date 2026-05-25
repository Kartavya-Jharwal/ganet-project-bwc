document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements - Define these first so they're available throughout the code
  const splashScreen = document.querySelector('.splash-screen');
  const startBtn = document.querySelector('.start-btn');
  const readMoreBtn = document.querySelector('.read-more-btn');
  const galleryContainer = document.querySelector('.gallery-container');
  const galleryTrack = document.querySelector('.gallery-track');
  const prevBtn = document.querySelector('.prev');
  const nextBtn = document.querySelector('.next');
  const modal = document.querySelector('.modal');
  const closeModal = document.querySelector('.close-modal');
  const keyboardLegend = document.querySelector('.keyboard-legend');
  const keyboardIcon = document.querySelector('.keyboard-icon');
  const feedbackForm = document.querySelector('.feedback-form');
  const ctaPortfolio = document.querySelector('.cta-portfolio');
  
  // Global variables
  let images = ['images/Template.png', 'images/Log_1.png', 'images/Log_2.png'];
  let currentIndex = 0;
  let touchStartY = 0;
  let touchEndY = 0;
  let galleryInitialized = false; // Track if gallery was initialized
  // lazyObserver will be created later via ensureLazyObserver()
  
  // Add background offset
  const backgroundOffset = document.createElement('div');
  backgroundOffset.className = 'background-offset';
  document.body.insertBefore(backgroundOffset, document.body.firstChild);
  
  // Add keyboard icon SVG to the existing element in HTML
  if (keyboardIcon) {
    keyboardIcon.innerHTML = `
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 5H4C2.9 5 2 5.9 2 7V17C2 18.1 2.9 19 4 19H20C21.1 19 22 18.1 22 17V7C22 5.9 21.1 5 20 5ZM20 17H4V7H20V17ZM11 8H13V10H11V8ZM11 11H13V13H11V11ZM8 8H10V10H8V8ZM8 11H10V13H8V11ZM5 11H7V13H5V11ZM5 8H7V10H5V8ZM8 14H16V16H8V14ZM14 11H16V13H14V11ZM14 8H16V10H14V8ZM17 11H19V13H17V11ZM17 8H19V10H17V8Z" fill="white"/>
      </svg>
    `;
    
    // Make keyboard icon accessible with keyboard navigation
    keyboardIcon.addEventListener('click', toggleKeyboardLegend);
    keyboardIcon.addEventListener('keydown', (e) => {
      if (['Enter', ' '].includes(e.key)) {
        e.preventDefault();
        toggleKeyboardLegend();
      }
    });
  }
  
  // Add ARIA roles and labels for accessibility
  document.querySelectorAll('button').forEach((button) => {
    if (!button.hasAttribute('aria-label')) {
      button.setAttribute('aria-label', button.textContent.trim() || 'Button');
    }
  });

  // Improved keyboard legend toggle with better visibility handling
  function toggleKeyboardLegend() {
    if (!keyboardLegend) return;
    
    const isVisible = keyboardLegend.classList.contains('visible');
    
    if (isVisible) {
      // Hide keyboard legend with animation
      keyboardLegend.classList.remove('visible');
      keyboardLegend.setAttribute('aria-hidden', 'true');
      
      setTimeout(() => {
        keyboardLegend.style.display = 'none';
      }, 300);
    } else {
      // Show keyboard legend with animation
      keyboardLegend.style.display = 'block';
      keyboardLegend.setAttribute('aria-hidden', 'false');
      
      // Small delay to ensure display:block is applied first
      setTimeout(() => {
        keyboardLegend.classList.add('visible');
      }, 10);
    }
  }
  
  // Function to handle orientation changes
  function handleOrientationChange() {
    const orientationMessage = document.querySelector('.orientation-message');
    if (window.matchMedia("(orientation: portrait) and (max-width: 768px)").matches) {
      orientationMessage.style.display = 'flex';
    } else {
      orientationMessage.style.display = 'none';
    }
  }
  
  // Initial check for orientation
  handleOrientationChange();
  
  // Listen for orientation changes with debounce for better performance
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(handleOrientationChange, 100);
  });
  
  // Fetch images from folder with enhanced probing for TEMPLATE + Log_N files
  async function fetchImages() {
    function createLoadingIndicator() {
      const loadingIndicator = document.createElement('div');
      loadingIndicator.className = 'loading-indicator';
      loadingIndicator.setAttribute('role', 'status');
      loadingIndicator.setAttribute('aria-live', 'polite');
      loadingIndicator.innerHTML = `
        <div class="loading-spinner" aria-hidden="true"></div>
        <div class="loading-text">Searching for images...</div>
      `;
      document.body.appendChild(loadingIndicator);
      return loadingIndicator;
    }

    function probeImage(src, timeout = 5000) {
      return new Promise((resolve) => {
        const img = new Image();
        let finished = false;
        const timer = setTimeout(() => {
          if (!finished) {
            finished = true;
            img.src = ''; // cancel
            resolve({ success: false, src, timeout: true });
          }
        }, timeout);

        img.onload = () => {
          if (finished) return;
          finished = true;
          clearTimeout(timer);
          resolve({ success: true, src });
        };
        img.onerror = () => {
          if (finished) return;
          finished = true;
          clearTimeout(timer);
          resolve({ success: false, src });
        };

        // Start loading
        img.src = src;
      });
    }

    const loadingIndicator = createLoadingIndicator();

    try {
      const found = [];

      // Probe for 1.png, 2.png, ... 8.png (simple numeric naming)
      const maxImages = 20; // safety cap
      let consecutiveMisses = 0;
      const maxConsecutiveMisses = 3;

      for (let i = 1; i <= maxImages; i++) {
        const src = `images/${i}.png`;
        loadingIndicator.querySelector('.loading-text').textContent = `Loading image ${i}...`;
        const res = await probeImage(src, 5000);
        if (res.success) {
          found.push(src);
          consecutiveMisses = 0;
          loadingIndicator.querySelector('.loading-text').textContent = `Found ${found.length} image(s)`;
        } else {
          consecutiveMisses += 1;
          // If we have several consecutive misses, assume there are no more sequential images
          if (consecutiveMisses >= maxConsecutiveMisses) {
            break;
          }
        }
      }

      // Fallback: if nothing found, try numbered images as last resort
      if (found.length === 0) {
        const fallbackNames = ['images/1.png', 'images/2.png', 'images/3.png'];
        for (const f of fallbackNames) {
          // probe quickly but don't block too long
          // eslint-disable-next-line no-await-in-loop
          const r = await probeImage(f, 3000);
          if (r.success) found.push(f);
        }
      }

      // Apply discovered images to the gallery order: template first (if present) then logs
      images = found.slice();

      // Remove loading indicator with fade out
      loadingIndicator.classList.add('fade-out');
      setTimeout(() => loadingIndicator.remove(), 400);

      // Announce completion for screen readers
      const loadingComplete = document.createElement('div');
      loadingComplete.setAttribute('role', 'status');
      loadingComplete.setAttribute('aria-live', 'assertive');
      loadingComplete.className = 'visually-hidden';
      loadingComplete.textContent = `Gallery found ${images.length} image(s)`;
      document.body.appendChild(loadingComplete);
      setTimeout(() => loadingComplete.remove(), 2500);

      return images.length > 0;
    } catch (err) {
      console.error('Error probing images:', err);
      loadingIndicator.remove();
      return false;
    }
  }
  
  // Initialize gallery
  async function initGallery() {
    if (galleryInitialized) {
      // If already initialized, just update the gallery
      updateGallery();
      return true;
    }
    
    // Show loading overlay
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'loading-overlay';
    loadingOverlay.innerHTML = `
      <div class="loading-spinner"></div>
      <div class="loading-text">Preparing your visual journey...</div>
    `;
    document.body.appendChild(loadingOverlay);
    
    // Fetch and preload images
    const imagesLoaded = await fetchImages();
    
  if (!imagesLoaded) {
      // Handle case where no images loaded
      loadingOverlay.innerHTML = `
        <div class="loading-error">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" fill="#ff6b6b"/>
          </svg>
          <h3>Unable to load gallery images</h3>
          <p>Please check your connection and try again.</p>
          <button class="retry-btn">Retry</button>
          <button class="fallback-btn">Visit Business Card</button>
        </div>
      `;
      
      // Add retry button functionality
      loadingOverlay.querySelector('.retry-btn').addEventListener('click', () => {
        loadingOverlay.remove();
        initGallery();
      });
      
      // Add fallback button functionality to e-business card
      loadingOverlay.querySelector('.fallback-btn').addEventListener('click', () => {
        window.location.href = 'https://kartavya-jharwal.github.io/';
      });
      
      return false;
    }
    
    // Set proper height for vertical scrolling
    galleryTrack.style.height = `${images.length * 100}vh`;
    // Use vertical layout for top to bottom carousel
    galleryTrack.style.flexDirection = 'column';
    galleryTrack.style.overflowY = 'hidden';
    galleryTrack.style.width = '100%';
  
    // Clear existing gallery items
    galleryTrack.innerHTML = '';
    
    // Remove loading overlay with fade out animation
    loadingOverlay.classList.add('fade-out');
    setTimeout(() => {
      loadingOverlay.remove();
    }, 600);
    
    // Add images to gallery with proper positioning for builder functionality
    images.forEach((img, index) => {
      const galleryItem = document.createElement('div');
      galleryItem.className = 'gallery-item';
      galleryItem.style.position = 'relative'; // Important for absolute positioning of buttons
      
      // Create week number and caption
      const weekNumber = index + 1;
      const captions = [
        'Initial concept exploration and wireframing',
        'Visual design language development',
        'Interactive prototype implementation',
        'User testing and feedback integration',
        'Final refinement and presentation'
      ];
      
      // Enhanced gallery item with metadata
      // Use a low-res placeholder and lazy-load the real image via data-src
      // Use a transparent 1x1 PNG data URI as the placeholder `src` to avoid flashing the TEMPLATE image
      // while preserving lazy-loading via `data-src`.
      const transparentPlaceholder = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AAn8B9o4J3QAAAABJRU5ErkJggg==';
      const errorPlaceholder = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjRjNGNEY2Ii8+Cjx0ZXh0IHg9IjEwMCIgeT0iMTAwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTIiIGZpbGw9IiM5OTk5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5JbWFnZSBuZXZlciBsb2FkZWQ8L3RleHQ+Cjwvc3ZnPg==';

      galleryItem.innerHTML = `
        <div class="image-container">
          <img data-src="${img}" src="${transparentPlaceholder}" alt="${captions[index] || 'Design development phase'} for week ${weekNumber}" class="zoomable-image blur-up" loading="lazy" onerror="this.src='${errorPlaceholder}'" role="img" aria-describedby="caption-${index}">
          <div class="image-overlay" aria-hidden="true"></div>
        </div>
        <div class="image-metadata">
          <div class="week-indicator">Week ${weekNumber}</div>
          <div class="image-caption" id="caption-${index}">${captions[index] || 'Design development phase'}</div>
        </div>
      `;
      
      // Add with animation delay based on index
      galleryItem.style.opacity = '0';
      galleryItem.style.transform = 'translateY(20px)';
      galleryTrack.appendChild(galleryItem);
      
      setTimeout(() => {
        galleryItem.style.opacity = '1';
        galleryItem.style.transform = 'translateY(0)';
      }, 100 + (index * 50));
    });
  
    // Add pinch-to-zoom functionality
    const zoomableImages = document.querySelectorAll('.zoomable-image');
    zoomableImages.forEach(img => {
      let scale = 1;
      let transformOrigin = 'center center';
      
      const resetScale = () => {
        scale = 1;
        img.style.transform = `scale(${scale})`;
        img.style.transformOrigin = transformOrigin;
      };
  
      img.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY * -0.01;
        scale = Math.min(Math.max(1.0, scale + delta), 4);
        transformOrigin = `${e.offsetX}px ${e.offsetY}px`;
        img.style.transform = `scale(${scale})`;
        img.style.transformOrigin = transformOrigin;
      });
  
      img.addEventListener('dblclick', resetScale);
      galleryTrack.addEventListener('scroll', resetScale);
    });

    // After images have been added to DOM, ensure lazy loader observes the new images
    observePendingLazyImages();

    // Lightbox: create once
    if (!document.querySelector('.image-lightbox')) {
      createImageLightbox();
    }
  
    // Add overlay button to return to splash screen
    if (!document.querySelector('.overlay-btn')) {
      const overlayBtn = document.createElement('button');
      overlayBtn.className = 'overlay-btn';
      overlayBtn.textContent = 'Home';
      overlayBtn.addEventListener('click', returnToSplash);
      document.body.appendChild(overlayBtn);
    }
  
    // Implement inactivity timer
    let timeout;
    const resetTimer = () => {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        returnToSplash();
      }, 300000); // 5 minutes
    };
  
    ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
      document.addEventListener(event, resetTimer, false);
    });
    resetTimer();
    
    // Mark gallery as initialized
    galleryInitialized = true;
    
    // Update gallery position initially
    updateGallery();
    return true;
  }
  
  // Function to handle returning to splash screen
  function returnToSplash() {
    // Reset to first slide for next time
    currentIndex = 0;
    updateGallery();
    
    // Hide gallery, show splash screen
    galleryContainer.classList.add('hidden');
    splashScreen.classList.remove('hidden');
  }
  
  // Show feedback form and CTA portfolio after the last image
  function showFeedbackAndCTA() {
    feedbackForm.classList.remove('hidden');
    ctaPortfolio.classList.remove('hidden');
  }

  // Update gallery position
  function updateGallery() {
    // Ensure currentIndex is within bounds
    currentIndex = Math.max(0, Math.min(currentIndex, images.length - 1));
    
    // Apply transform to move gallery vertically
    galleryTrack.style.transform = `translateY(-${currentIndex * 100}vh)`;
    
    // Add parallax effect to image metadata
    document.querySelectorAll('.image-metadata').forEach((meta, i) => {
      const offset = (i - currentIndex) * 20; // 20px parallax offset
      meta.style.transform = `translateY(${offset}px)`;
    });
    
    // Update navigation buttons visibility
    if (prevBtn && nextBtn) {
      prevBtn.style.opacity = currentIndex > 0 ? '1' : '0.3';
      nextBtn.style.opacity = currentIndex < images.length - 1 ? '1' : '0.3';
    }
    


    if (currentIndex === images.length - 1) {
      showFeedbackAndCTA();
    } else {
      feedbackForm.classList.add('hidden');
      ctaPortfolio.classList.add('hidden');
    }
  }
  
  // Event Listeners for navigation
  function handleSwipe() {
    const swipeThreshold = 50;
    const swipeDistance = touchStartY - touchEndY;
    
    if (Math.abs(swipeDistance) > swipeThreshold) {
      if (swipeDistance > 0 && currentIndex < images.length - 1) {
        currentIndex++;
      } else if (swipeDistance < 0 && currentIndex > 0) {
        currentIndex--;
      }
      updateGallery();
    }
  }
  
  // Main button event listeners
  startBtn.addEventListener('click', async () => {
    // Hide the start button and show a small loader while images are prepared
    if (startBtn) {
      startBtn.style.visibility = 'hidden';
      startBtn.setAttribute('aria-busy', 'true');
    }

    // Add inline loader to splash (so user sees progress on the same screen)
    let splashLoader = splashScreen.querySelector('.splash-loader');
    if (!splashLoader) {
      splashLoader = document.createElement('div');
      splashLoader.className = 'splash-loader';
      splashLoader.innerHTML = '<div class="splash-loader-content"><div class="loader-spinner"></div><div class="loading-text">Opening sketchbook...</div></div>';
      splashScreen.appendChild(splashLoader);
    }

    // Attempt to initialize gallery. Only switch to gallery view when initialization succeeds.
    const ok = await initGallery();

    if (ok) {
      splashScreen.classList.add('hidden');
      galleryContainer.classList.remove('hidden');
    } else {
      // If init failed, restore start button so user can retry
      if (startBtn) {
        startBtn.style.visibility = '';
        startBtn.removeAttribute('aria-busy');
      }
      // Optionally show a transient error message (initGallery already shows overlays)
    }

    // Clean up splash loader
    if (splashLoader) {
      splashLoader.remove();
    }
  });

  readMoreBtn.addEventListener('click', () => {
    modal.classList.remove('hidden');
  });

  closeModal.addEventListener('click', () => {
    modal.classList.add('hidden');
  });

  // Update the modal content to include e-business card link
  if (modal && modal.querySelector('.modal-content')) {
    // Don't overwrite the rich modal content that's already in the HTML
    // Just ensure the close button has the right event listener
    const closeModalBtn = modal.querySelector('.close-modal');
    if (closeModalBtn) {
      closeModalBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
      });
    }
  }

  prevBtn.addEventListener('click', () => {
    if (currentIndex > 0) {
      currentIndex--;
      updateGallery();
    }
  });

  nextBtn.addEventListener('click', () => {
    if (currentIndex < images.length - 1) {
      currentIndex++;
      updateGallery();
    }
  });
  
  // Touch events for mobile swipe
  galleryTrack.addEventListener('touchstart', (e) => {
    touchStartY = e.changedTouches[0].screenY;
  });
  
  galleryTrack.addEventListener('touchend', (e) => {
    touchEndY = e.changedTouches[0].screenY;
    handleSwipe();
  });
  
  // Show/hide navigation buttons on cursor movement
  let navTimeout;
  galleryContainer.addEventListener('mousemove', () => {
    // Show buttons
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(btn => {
      btn.classList.remove('fade-out');
      btn.style.opacity = '0.8';
    });
    
    // Clear any existing timeout
    clearTimeout(navTimeout);
    
    // Set new timeout to hide buttons after 2 seconds of inactivity
    navTimeout = setTimeout(() => {
      navButtons.forEach(btn => {
        btn.classList.add('fade-out');
      });
    }, 2000);
  });
  
  // Hide buttons when mouse leaves the container
  galleryContainer.addEventListener('mouseleave', () => {
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(btn => {
      btn.classList.add('fade-out');
    });
  });
  
  // Close modal when clicking outside
  window.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.classList.add('hidden');
    }
  });
  
  // Complete reimplementation of keyboard navigation
  document.addEventListener('keydown', (e) => {
    // R key to open Read More from anywhere
    if (e.key.toLowerCase() === 'r') {
      modal.classList.remove('hidden');
      return;
    }

    // S key to start gallery from splash screen
    if (e.key.toLowerCase() === 's' && !splashScreen.classList.contains('hidden')) {
      splashScreen.classList.add('hidden');
      galleryContainer.classList.remove('hidden');
      initGallery();
      return;
    }

    // Common shortcuts available everywhere
    if (e.shiftKey && e.key === '?') {
      e.preventDefault();
      toggleKeyboardLegend();
      return;
    }

    // Handle Escape key
    if (e.key === 'Escape') {
      // First check if keyboard legend is open
      if (keyboardLegend && keyboardLegend.classList.contains('visible')) {
        toggleKeyboardLegend();
        return;
      }
      
      // Then check if modal is open
      if (!modal.classList.contains('hidden')) {
        modal.classList.add('hidden');
        return;
      }
      
      // If in gallery and not on splash screen, return to splash
      if (!galleryContainer.classList.contains('hidden') && splashScreen.classList.contains('hidden')) {
        returnToSplash();
        return;
      }
    }
    
    // F1 key for keyboard shortcuts help
    if (e.key === 'F1') {
      e.preventDefault(); // Prevent browser's F1 help
      toggleKeyboardLegend();
      return;
    }
    
    // Gallery navigation shortcuts - only when gallery is visible
    if (!galleryContainer.classList.contains('hidden')) {
      switch (e.key) {
        case 'ArrowUp':
          if (currentIndex > 0) {
            currentIndex--;
            updateGallery();
          }
          break;
          
        case 'ArrowDown':
          if (currentIndex < images.length - 1) {
            currentIndex++;
            updateGallery();
          }
          break;
          
        case 'h':
        case 'H':
          returnToSplash();
          break;
          
        case 'Home':
          currentIndex = 0;
          updateGallery();
          break;
          
        case 'End':
          currentIndex = images.length - 1;
          updateGallery();
          break;
      }
    }
  });
  
  // Initialize lazy loading
  const lazyLoadImages = () => {
    const images = document.querySelectorAll('.zoomable-image[data-src]');
    const observer = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.removeAttribute('data-src');
          // Once image loads, remove blur-up class for a smooth transition
          img.addEventListener('load', () => {
            img.classList.remove('blur-up');
            img.classList.add('loaded');
          }, { once: true });
          observer.unobserve(img);

          // Prefetch neighbor images (previous and next)
          prefetchNeighborImages(img);
        }
      });
    }, { 
      rootMargin: '200px 0px 200px 0px',
      threshold: 0.01
    });

    images.forEach(img => {
      if (img.dataset.src) {
        observer.observe(img);
      }
    });

    return observer;
  };

  // Helper to ensure a singleton observer and observe pending images
  let _lazyObserverInstance = null;
  function ensureLazyObserver() {
    if (!_lazyObserverInstance) {
      _lazyObserverInstance = lazyLoadImages();
    }
    return _lazyObserverInstance;
  }

  function observePendingLazyImages() {
    const observer = ensureLazyObserver();
    document.querySelectorAll('.zoomable-image[data-src]').forEach(img => {
      if (observer && typeof observer.observe === 'function') {
        observer.observe(img);
      }
    });
  }

  // Prefetch neighbor images (used after an image is loaded)
  function prefetchNeighborImages(imgEl) {
    // Try to find neighbors by locating the parent gallery-item
    const item = imgEl.closest('.gallery-item');
    if (!item) return;
    const items = Array.from(document.querySelectorAll('.gallery-item'));
    const idx = items.indexOf(item);
    [idx - 1, idx + 1].forEach(i => {
      if (i >= 0 && i < items.length) {
        const neighborImg = items[i].querySelector('.zoomable-image');
        if (neighborImg && neighborImg.dataset && neighborImg.dataset.src) {
          // Create a temporary Image to trigger browser caching
          const pre = new Image();
          pre.src = neighborImg.dataset.src;
        }
      }
    });
  }

  // Create a simple lightbox for viewing images full-screen
  function createImageLightbox() {
    const lightbox = document.createElement('div');
    lightbox.className = 'image-lightbox hidden';
    lightbox.innerHTML = `
      <div class="lightbox-inner" role="dialog" aria-modal="true">
        <button class="lightbox-close" aria-label="Close">×</button>
        <button class="lightbox-prev" aria-label="Previous image">‹</button>
        <div class="lightbox-content">
          <img src="" alt="" class="lightbox-img">
          <div class="lightbox-caption" aria-live="polite"></div>
        </div>
        <button class="lightbox-next" aria-label="Next image">›</button>
      </div>
    `;
    document.body.appendChild(lightbox);

    const imgEl = lightbox.querySelector('.lightbox-img');
    const captionEl = lightbox.querySelector('.lightbox-caption');
    const closeBtn = lightbox.querySelector('.lightbox-close');
    const prevBtn = lightbox.querySelector('.lightbox-prev');
    const nextBtn = lightbox.querySelector('.lightbox-next');

    function openLightbox(index) {
      const items = Array.from(document.querySelectorAll('.gallery-item'));
      const target = items[index];
      if (!target) return;
      const src = target.querySelector('.zoomable-image').src || target.querySelector('.zoomable-image').dataset.src;
      imgEl.src = src;
      captionEl.textContent = target.querySelector('.image-caption') ? target.querySelector('.image-caption').textContent : '';
      lightbox.classList.remove('hidden');
      setTimeout(() => lightbox.classList.add('visible'), 10);
      currentIndex = index;
    }

    function closeLightbox() {
      lightbox.classList.remove('visible');
      setTimeout(() => lightbox.classList.add('hidden'), 300);
    }

    function showPrev() { if (currentIndex > 0) { currentIndex--; openLightbox(currentIndex); } }
    function showNext() { if (currentIndex < images.length - 1) { currentIndex++; openLightbox(currentIndex); } }

    // Delegated click to open lightbox
    document.addEventListener('click', (e) => {
      const galleryItem = e.target.closest('.gallery-item');
      if (galleryItem && e.target.classList.contains('zoomable-image')) {
        const items = Array.from(document.querySelectorAll('.gallery-item'));
        openLightbox(items.indexOf(galleryItem));
      }
    });

    closeBtn.addEventListener('click', closeLightbox);
    prevBtn.addEventListener('click', showPrev);
    nextBtn.addEventListener('click', showNext);

    // Keyboard controls for lightbox
    document.addEventListener('keydown', (e) => {
      const isOpen = !lightbox.classList.contains('hidden');
      if (!isOpen) return;
      if (e.key === 'Escape') closeLightbox();
      if (e.key === 'ArrowLeft') showPrev();
      if (e.key === 'ArrowRight') showNext();
    });
  }

  // Cleanup observer when leaving page
  window.addEventListener('beforeunload', () => {
    if (_lazyObserverInstance) {
      _lazyObserverInstance.disconnect();
    }
  });
  


  // Fallback handling - redirect if errors occur or provide manual link
  window.addEventListener('error', function(e) {
    console.error('Gallery error:', e.error || e.message);
    
    // Only redirect for critical errors, show fallback link for minor ones
    if (e.error && (e.error.message.includes('critical') || 
        e.error.message.includes('Cannot read property') || 
        e.error.message.includes('undefined is not'))) {
      
      const fallbackUrl = 'https://kartavya-jharwal.github.io/';
      console.log(`Redirecting to fallback: ${fallbackUrl}`);
      window.location.href = fallbackUrl;
    }
    
    // Show fallback link more prominently for non-critical errors
    const fallbackLink = document.querySelector('.fallback-link');
    if (fallbackLink) {
      fallbackLink.style.opacity = '1';
      fallbackLink.style.bottom = '4rem';
    }
  });
});