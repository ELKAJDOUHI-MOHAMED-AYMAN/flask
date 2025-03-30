(function() { 
let refreshInterval;
let retryCount = 0;
const MAX_RETRIES = 3;

function showFeaturedQuote(data) {
    const quoteHTML = `
        <div class="animate__animated animate__fadeIn">
            <p class="display-6 mb-4">"${data.content}"</p>
            <footer class="blockquote-footer mt-4">
                – ${data.author}
            </footer>
            <small class="text-muted d-block mt-2">
                Source: ${data.source || 'External API'}
                ${data.status === 'fallback' ? ' (Fallback)' : ''}
            </small>
            ${data.status === 'fallback' ? `
            <div class="alert alert-warning mt-3 animate__animated animate__fadeIn">
                <i class="fas fa-info-circle me-2"></i>
                Using fallback quotes as external services are unavailable
            </div>` : ''}
        </div>
    `;
    $('#featured-quote .quote-content').html(quoteHTML);
}

function showLoadingSpinner() {
    $('#featured-quote .quote-content').html(`
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div class="mt-2">Fetching fresh quote...</div>
        </div>
    `);
}

function handleQuoteError(message) {
    retryCount++;
    const errorHTML = `
        <div class="alert alert-danger animate__animated animate__headShake">
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}<br>
            <small>${retryCount <= MAX_RETRIES ? 
                `Retry ${retryCount}/${MAX_RETRIES}` : 
                'Maximum retries reached'}
            </small>
            <div class="mt-2">
                <button onclick="forceNewQuote()" class="btn btn-sm btn-warning">
                    <i class="fas fa-redo me-2"></i>Try Again
                </button>
            </div>
        </div>
    `;
    
    $('#featured-quote .quote-content').html(errorHTML);
    
    if(retryCount <= MAX_RETRIES) {
        startRefreshTimer(10);
    } else {
        $('#refresh-timer').parent().hide();
    }
}

function startRefreshTimer(seconds = 10) {
    clearInterval(refreshInterval);
    $('#refresh-timer').text(seconds).parent().show();
    
    refreshInterval = setInterval(() => {
        seconds--;
        $('#refresh-timer').text(seconds);
        
        if(seconds <= 0) {
            clearInterval(refreshInterval);
            if(retryCount <= MAX_RETRIES) {
                updateFeaturedQuote();
            }
        }
    }, 1000);
}

function updateFeaturedQuote() {
    showLoadingSpinner();
    $.ajax({
        url: '/api/external-random-quote',
        success: function(data) {
            retryCount = 0;
            if(data.content && data.author) {
                showFeaturedQuote(data);
                startRefreshTimer();
            } else {
                handleQuoteError(data.error || 'Invalid response format');
            }
        },
        error: function(xhr) {
            handleQuoteError(xhr.responseJSON?.error || 
                          `Connection error (${xhr.status})`);
        }
    });
}

// Change the function declaration
window.forceNewQuote = function() {  
    clearInterval(refreshInterval);
    showLoadingSpinner();
    
    const timestamp = new Date().getTime();
    $.ajax({
        url: `/api/external-random-quote?nocache=${timestamp}`,
        success: function(data) {
            retryCount = 0;
            if(data.content && data.author) {
                showFeaturedQuote(data);
                startRefreshTimer();
            } else {
                handleQuoteError(data.error || 'Invalid response format');
            }
        },
        error: function(xhr) {
            handleQuoteError(xhr.responseJSON?.error || 
                          `Connection error (${xhr.status})`);
        }
    });
}

// Quote Search and Browse functions
let currentPage = 1;

function searchQuotes() {
    const searchTerm = $('#search-input').val();
    if(searchTerm.length < 2) return;
    
    $('#quotes-grid').html(`
        <div class="col-12 text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `);
    
    $.ajax({
        url: `/api/quotes/search?q=${encodeURIComponent(searchTerm)}`,
        success: function(data) {
            renderQuotesGrid(data, `Search Results for "${searchTerm}"`);
        },
        error: function() {
            $('#quotes-grid').html(`
                <div class="col-12 text-center text-danger py-4">
                    Failed to load search results
                </div>
            `);
        }
    });
}

function loadRandomQuotes() {
    $('#quotes-grid').html(`
        <div class="col-12 text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `);
    
    $.ajax({
        url: '/api/random-quotes?count=6', 
        success: function(data) {
            renderQuotesGrid(data, 'Magical Random Picks ✨');
        },
        error: function() {
            $('#quotes-grid').html(`
                <div class="col-12 text-center text-danger py-4">
                    Failed to load random quotes
                </div>
            `);
        }
    });
}

function renderQuotesGrid(quotes, title) {
    $('#grid-title').text(title);
    const grid = $('#quotes-grid');
    grid.html('');
    
    if(!quotes || quotes.length === 0) {
        grid.html(`
            <div class="col-12 text-center text-muted py-4">
                No quotes found
            </div>
        `);
        return;
    }
    
    quotes.forEach(quote => {
        grid.append(`
            <div class="col-md-6 col-lg-4 mb-4 animate__animated animate__zoomIn">
                <div class="card h-100 quote-card">
                    <div class="card-body">
                        <div class="quote-card-content">  <!-- Added wrapper div -->
                            <p class="card-text">${quote.content}</p>
                            <footer class="blockquote-footer mt-3">
                                ${quote.author}
                            </footer>
                        </div>
                        <div class="card-button-container">
                            <a href="/quotes/${quote.id}" class="btn btn-sm btn-primary">
                                <i class="fas fa-info-circle me-2"></i>Learn More
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `);
    });
    
    $('#load-more').toggle(quotes.length >= 6);
}

// Initialize home page
$(document).ready(function(){
    if(window.location.pathname === '/') {
        // Add this event listener
        $('#refreshNowButton').on('click', function() {
            forceNewQuote();
        });
        updateFeaturedQuote();
        loadRandomQuotes();
        
        // Search as you type with debounce
        let searchTimeout;
        $('#search-input').on('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if(this.value.length > 2) {
                    searchQuotes();
                } else if(this.value.length === 0) {
                    loadRandomQuotes();
                }
            }, 500);
        });
    }
});

// Lottie Animation
document.addEventListener('DOMContentLoaded', function() {
    if(document.getElementById('lottie-animation')) {
        lottie.loadAnimation({
            container: document.getElementById('lottie-animation'),
            renderer: 'svg',
            loop: true,
            autoplay: true,
            path: 'https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json' // New animation
        });
    }
});

})();