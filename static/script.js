// wait untim DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {

  // event listeners to button
  function attachEventListeners() {
    // for index.html: buttons with fixed IDs
    const petCard = document.getElementById('pet-card');
    const skipBtn = document.getElementById('skip-btn');
    const heartBtn = document.getElementById('heart-btn');

    if (skipBtn && heartBtn && petCard) {
      skipBtn.addEventListener('click', (e) => {
        e.preventDefault();
        animate(null, 'skip', true); // true = index page
      });

      heartBtn.addEventListener('click', (e) => {
        e.preventDefault();
        animate(null, 'heart', true); // true = index page
      });
    }

    // for hearted.html / previous.html: buttons with class selectors and data attributes
    document.querySelectorAll('.skip-btn').forEach(button => {
      button.addEventListener('click', (e) => {
        e.preventDefault();
        const petId = button.getAttribute('data-pet-id');
        animate(petId, 'skip');
      });
    });

    document.querySelectorAll('.heart-btn').forEach(button => {
      button.addEventListener('click', (e) => {
        e.preventDefault();
        const petId = button.getAttribute('data-pet-id');
        animate(petId, 'heart');
      });
    });
  }
  
  // function to handle swipe animation and fetch action
  function animate(petId, type, isIndexPage = false) {
    const card = isIndexPage ? 
      document.getElementById('pet-card') : 
      document.getElementById(`pet-${petId}`);

    if (!card) return;

    if (type === 'skip') {
      card.classList.add('swipe-left');

      setTimeout(() => {
        const url = isIndexPage ? `/skip/${petId || getPetIdFromCard(card)}` : `/skip/${petId}`;
        fetch(url, { method: 'POST' })
          .then(res => {
            if (res.ok) {
              if (isIndexPage) {
                loadNextPet();
              } else {
                card.remove();
              }
            } else {
              alert("Error skipping pet.");
              card.classList.remove('swipe-left');
            }
          })
          .catch(() => {
            alert("Failed to skip pet.");
            card.classList.remove('swipe-left');
          });
      }, 500); // wait for animation to finish

    } else if (type === 'heart') {
      card.classList.add('swipe-right');

      setTimeout(() => {
        const url = isIndexPage ? `/adopt/${petId || getPetIdFromCard(card)}` : `/adopt/${petId}`;
        fetch(url, { method: 'POST' })
          .then(res => {
            if (res.ok) {
              if (isIndexPage) {
                loadNextPet();
              } else {
                card.remove();
              }
            } else {
              alert("Error hearting pet.");
              card.classList.remove('swipe-right');
            }
          })
          .catch(() => {
            alert("Failed to heart pet.");
            card.classList.remove('swipe-right');
          });
      }, 500);

    } else {
      console.warn('Unknown animation type:', type);
    }
  }

  // helper to get pet ID from the card element on index page
  function getPetIdFromCard(card) {
    return card.getAttribute('data-pet-id');
  }

  // fetch and display the next random pet on the index page
  function loadNextPet() {
    fetch('/next-pet')
      .then(res => res.json())
      .then(data => {
        const container = document.getElementById('pet-container');
        if (!container) return;

        //if no more pets available show this
        if (data.no_more) {
          container.innerHTML = '<p>No more pets available. Come back later!</p>';
          return;
        }

        //builds the new pet card HTML and insert it into the DOM
        const petCardHtml = `
          <div class="pet-card" id="pet-card" data-pet-id="${data.id}">
            <img src="${data.image_url}" alt="${data.name}">
            <h2>${data.name}</h2>       
            <p class = bubble>Gender: ${data.gender} </p>
            <p class = bubble> Age: ${data.age} </p> <p class = bubble>Size: ${data.size}</p>             
            <p>${data.description}</p>           
            <div class="btns">
              <a id="skip-btn" href="/skip/${data.id}" class="btn btn-danger">❌</a>
              <a id="heart-btn" href="/adopt/${data.id}" class="btn btn-success me-2">❤️</a>
            </div>
          </div>
        `;

        //updates DOM and re-attach listeners to the new button
        container.innerHTML = petCardHtml;
        attachEventListeners();
      })
      .catch(err => console.error('Error loading next pet:', err));
  }

  // initial call to bind all event listeners
  attachEventListeners(); 

});