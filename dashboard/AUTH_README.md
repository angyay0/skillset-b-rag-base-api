# Dashboard Authentication

The Blinky Metrics Dashboard is now protected with OAuth 2.0 authentication.

## Authentication Flow

1. **Login Page** (`login.html`)
   - Users must authenticate before accessing the dashboard
   - Credentials are validated against the OAuth 2.0 endpoint
   - Upon successful login, an access token is stored in localStorage

2. **Protected Dashboard** (`index.html`)
   - Automatically checks for valid authentication token on load
   - Redirects to login page if not authenticated or token expired
   - Includes logout button in the header

3. **Token Management**
   - Tokens are stored in localStorage with expiry timestamp
   - Default expiry: 24 hours (or as provided by API)
   - Automatic cleanup on expiry

## API Endpoint

**Login Endpoint:**
```
POST https://flow-company-auth-api-1060245240559.us-central1.run.app/auth/login
```

**Request Body:**
```json
{
  "email": "admin@company.com",
  "password": "password123"
}
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": 86400,
  "token_type": "Bearer"
}
```

## Files

- `login.html` - Login page with form
- `auth.js` - Authentication logic and token management
- `index.html` - Protected dashboard (modified)
- `dashboard.js` - Dashboard logic (modified with logout)

## Usage

### Access Dashboard
1. Navigate to `login.html`
2. Enter credentials:
   - Email: `admin@company.com`
   - Password: `password123`
3. Click "Sign In"
4. Redirected to dashboard on success

### Logout
1. Click the "🚪 Logout" button in the dashboard header
2. Confirm logout
3. Redirected to login page

## Security Features

✅ Token-based authentication (OAuth 2.0)  
✅ Automatic token expiry checking  
✅ Secure token storage in localStorage  
✅ Protected routes with redirect  
✅ Logout confirmation dialog  
✅ HTTPS endpoint for authentication  

## Development Notes

- Tokens are stored client-side in localStorage
- For production, consider implementing:
  - Token refresh mechanism
  - HTTP-only cookies for enhanced security
  - CSRF protection
  - Rate limiting on login attempts
