# Tor Proxy Pool - Admin UI

React-based admin interface for Tor Proxy Pool management.

## Features

- Real-time node status monitoring
- Circuit rotation controls
- Configuration management
- Export token management
- Authentication with 2FA
- Metrics dashboard
- Audit log viewer

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Production Deployment

The admin UI is served through the FastAPI backend. Build the frontend and copy to the backend's static directory:

```bash
npm run build
cp -r dist/* ../backend/app/static/
```

## Environment Variables

Create `.env.local`:

```
VITE_API_URL=http://localhost:8000
```

## Technology Stack

- React 18
- Vite
- React Router
- TanStack Query (React Query)
- Axios
- Recharts (for metrics visualization)

## Project Structure

```
src/
├── components/     # Reusable UI components
├── pages/         # Page components
├── api/           # API client functions
├── hooks/         # Custom React hooks
├── utils/         # Utility functions
└── App.jsx        # Main application component
```

## Key Components

### Dashboard
- Node status overview
- Health metrics
- Quick actions

### Nodes Management
- List all nodes
- Individual node details
- Circuit rotation controls

### Configuration
- Firewall settings
- Whitelist management
- General settings

### Export Tokens
- Create tokens
- View active tokens
- Revoke tokens

### Security
- 2FA setup
- Password change
- Audit logs

## API Integration

The UI communicates with the backend API at `/api/v1/`. All requests include JWT authentication token in the Authorization header.

## Building

```bash
# Production build
npm run build

# Output will be in dist/
```

## Notes

- This is a placeholder structure. Full React implementation would require additional development.
- For production use, consider adding:
  - WebSocket support for real-time updates
  - Advanced data visualization
  - Mobile-responsive design
  - Accessibility improvements
  - Internationalization (i18n)
