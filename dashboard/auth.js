// Authentication configuration
const AUTH_API_URL = 'https://flow-company-auth-api-1060245240559.us-central1.run.app/auth/login';
const TOKEN_KEY = 'blinky_auth_token';
const TOKEN_EXPIRY_KEY = 'blinky_token_expiry';

// Check if user is authenticated
function isAuthenticated() {
    const token = localStorage.getItem(TOKEN_KEY);
    const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
    
    if (!token || !expiry) {
        return false;
    }
    
    // Check if token is expired
    const expiryDate = new Date(expiry);
    if (expiryDate <= new Date()) {
        // Token expired, clear storage
        clearAuth();
        return false;
    }
    
    return true;
}

// Get authentication token
function getAuthToken() {
    return localStorage.getItem(TOKEN_KEY);
}

// Clear authentication data
function clearAuth() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
}

// Redirect to login if not authenticated
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// Redirect to dashboard if already authenticated
function redirectIfAuthenticated() {
    if (isAuthenticated()) {
        window.location.href = 'index.html';
    }
}

// Handle login form submission
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    
    if (loginForm) {
        // Redirect if already logged in
        redirectIfAuthenticated();
        
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const loginBtn = document.getElementById('login-btn');
            const errorMessage = document.getElementById('error-message');
            
            // Clear previous errors
            errorMessage.classList.remove('show');
            errorMessage.textContent = '';
            
            // Disable button and show loading
            loginBtn.disabled = true;
            loginBtn.innerHTML = '<span class="loading-spinner"></span> Signing in...';
            
            try {
                const response = await fetch(AUTH_API_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email, password })
                });
                
                const data = await response.json();
                
                if (!response.ok || data.status != 'success') {
                    throw new Error(data.message || 'Invalid credentials');
                }
                
                // Store token and expiry (default 24 hours if not provided)
                const rData = data.data;
                const expiryDate = new Date();
                if (rData.expiresIn) {
                    // If API provides expiry in seconds
                    expiryDate.setSeconds(expiryDate.getSeconds() + rData.expiresIn);
                } else if (rData.expires_in) {
                    // Alternative format
                    expiryDate.setSeconds(expiryDate.getSeconds() + rData.expires_in);
                } else {
                    // Default to 24 hours
                    expiryDate.setHours(expiryDate.getHours() + 24);
                }
                
                // Store token (check different possible response formats)
                const token = rData.access_token || rData.accessToken || rData.token;
                if (!token) {
                    throw new Error('No token received from server');
                }
                
                localStorage.setItem(TOKEN_KEY, token);
                localStorage.setItem(TOKEN_EXPIRY_KEY, expiryDate.toISOString());
                
                // Redirect to dashboard
                window.location.href = 'index.html';
                
            } catch (error) {
                console.error('Login error:', error);
                errorMessage.textContent = error.message || 'Login failed. Please try again.';
                errorMessage.classList.add('show');
                
                // Re-enable button
                loginBtn.disabled = false;
                loginBtn.textContent = 'Sign In';
            }
        });
    }
});

// Logout function
function logout() {
    clearAuth();
    window.location.href = 'login.html';
}
