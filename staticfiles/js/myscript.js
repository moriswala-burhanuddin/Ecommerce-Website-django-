$('#slider1, #slider2, #slider3').owlCarousel({
    loop: true,
    margin: 20,
    responsiveClass: true,
    responsive: {
        0: {
            items: 1,
            nav: false,
            autoplay: true,
        },
        600: {
            items: 3,
            nav: true,
            autoplay: true,
        },
        1000: {
            items: 5,
            nav: true,
            loop: true,
            autoplay: true,
        }
    }
})

document.querySelectorAll('.plus-cart').forEach(item => {
    item.addEventListener('click', function() {
        const productId = this.getAttribute('pid');
        updateQuantity(productId, 'increase');
    });
});

document.querySelectorAll('.minus-cart').forEach(item => {
    item.addEventListener('click', function() {
        const productId = this.getAttribute('pid');
        updateQuantity(productId, 'decrease');
    });
});

function updateQuantity(productId, action) {
    fetch("{% url 'update-cart' %}", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: JSON.stringify({
            'prod_id': productId,
            'action': action
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error(data.error);
        } else {
            const quantityElement = document.querySelector(`.quantity[data-id="${productId}"]`);
            quantityElement.innerText = data.quantity;

            // Update the amount displayed for the specific product
            const amountElement = document.querySelector(`.total-amount[data-id="${productId}"]`);
            amountElement.innerText = `Rs. ${data.amount}`;

            // Optionally update total cart amount here if needed
            updateTotalAmount();
        }
    })
    .catch(error => console.error('Error:', error));
}

// Function to update total amount displayed
function updateTotalAmount() {
    let totalAmount = 0;
    document.querySelectorAll('.quantity').forEach(quantityElement => {
        const productId = quantityElement.getAttribute('data-id');
        const quantity = parseInt(quantityElement.innerText, 10);
        const priceElement = document.querySelector(`.total-amount[data-id="${productId}"]`);
        const price = parseFloat(priceElement.innerText.replace('Rs. ', ''));
        totalAmount += price;
    });

    const shippingCost = 70.00;
    const finalTotal = totalAmount + shippingCost;
    document.querySelector('.total-amount').innerText = `Rs. ${finalTotal.toFixed(2)}`; // Update total amount displayed
}


// const sr = ScrollReveal ({
//     distance:'60px',
//     duration:2500,
//     delay:400,
//     reset:true
     


// })

// sr.reveal('.banner-slider',{delay:200, origin:'top'})
// sr.reveal('.ourstory',{delay:800, origin:'top'})
// sr.reveal('.ptitles',{delay:300, origin:'top'})
// sr.reveal('.product',{delay:300, origin:'top'})
// sr.reveal('.hoodieimg',{delay:200, origin:'bottom'})
// sr.reveal('.address ',{delay:300, origin:'top'})
// sr.reveal('.text-center',{delay:300, origin:'top'})
// sr.reveal('.cart-pd',{delay:300, origin:'bottom'})
// sr.reveal('.payments',{delay:300, origin:'bottom'})
// // sr.reveal('.footer',{delay:300, origin:'bottom'})

// sr.reveal('.buynowscroll',{delay:200, origin:'top'})
// sr.reveal('.form-group',{delay:800, origin:'top'})
// sr.reveal('.custom-form-group',{delay:300, origin:'top'})
// sr.reveal('.order-card',{delay:300, origin:'top'})
// sr.reveal('.pos',{delay:200, origin:'top'})
// sr.reveal('.fillscr',{delay:300, origin:'left'})
// sr.reveal('.product-detail',{delay:300, origin:'top'})
// sr.reveal('.reviews-section',{delay:300, origin:'bottom'})
// sr.reveal('.suggested-products  ',{delay:300, origin:'bottom'})
// sr.reveal('.',{delay:300, origin:'top'})
// sr.reveal('.',{delay:300, origin:'bottom'})




// Function to toggle mute/unmute state of the background video
function toggleMute() {
    var video = document.getElementById('background-video');
    var muteButton = document.getElementById('mute-btn');
  
    if (video.muted) {
      video.muted = false;
      muteButton.innerText = 'Mute';
    } else {
      video.muted = true;
      muteButton.innerText = 'Unmute';
    }
  }
  
  // Function to toggle mute/unmute state of the advertisement video
  function toggleAdMute() {
    var adVideo = document.getElementById('advertisement-video');
    var adMuteButton = document.getElementById('advertisement-mute-btn');
  
    if (adVideo.muted) {
      adVideo.muted = false;
      adMuteButton.innerText = 'Mute';
    } else {
      adVideo.muted = true;
      adMuteButton.innerText = 'Unmute';
    }
  }
  
  // Function to toggle play/pause state of the advertisement video
  function togglePlayPause() {
    var adVideo = document.getElementById('advertisement-video');
    var playPauseButton = document.getElementById('play-pause-btn');
  
    if (adVideo.paused) {
      adVideo.play();
      playPauseButton.innerText = 'Pause';
    } else {
      adVideo.pause();
      playPauseButton.innerText = 'Play';
    }
  }


    // Prevent right-click context menu
document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
    alert('Right-click is disabled for security reasons!');
});

// Disable F12 key (Developer Tools)
document.addEventListener('keydown', function(e) {
    if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && e.key === 'I')) {
        e.preventDefault();
        alert('Developer Tools are disabled!');
    }
});

// Disable opening the developer tools with "Ctrl+Shift+I"
document.onkeydown = function(e) {
    if (e.ctrlKey && e.shiftKey && e.keyCode == 73) {  // Ctrl + Shift + I
        e.preventDefault();
        alert("Access to Developer Tools is disabled.");
    }
};

// Disable right-clicking and copy-paste
document.addEventListener("copy", function(e) {
    e.preventDefault();
    alert("Copying is disabled on this page.");
});