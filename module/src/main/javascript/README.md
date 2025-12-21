# Zerobus Connector React Frontend

React-based configuration UI for the Ignition Zerobus Connector Gateway module.

## Development

### Prerequisites

- Node.js 18.x or higher
- npm 9.x or higher

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm start
```

The development server will run at `http://localhost:3000` and proxy API requests to `http://localhost:8088` (your Ignition Gateway).

### Building

```bash
# Build for production
npm run build
```

This creates optimized static files in the `build/` directory.

### Integration with Ignition Module

The Gradle build automatically:
1. Installs Node.js and npm
2. Runs `npm install`
3. Runs `npm run build`
4. Copies `build/` contents to `src/main/resources/web/`

These files are then packaged into the `.modl` file and served by the Ignition Gateway at `/system/zerobus/` (or configured mount point).

## Component Structure

```
src/
├── App.js          - Main configuration UI component
├── App.css         - Styling
├── index.js        - React entry point
└── index.css       - Global styles
```

## REST API Integration

The UI expects the following Gateway REST endpoints (to be implemented in Java):

- `GET /system/zerobus/config` - Load current configuration
- `POST /system/zerobus/config` - Save configuration
- `POST /system/zerobus/test-connection` - Test Databricks connection
- `GET /system/zerobus/diagnostics` - Get diagnostics info

See `ZerobusRestResource.java` (to be created) for implementation.

## Configuration Fields

The UI manages all ConfigModel fields:
- **Databricks Connection**: Workspace URL, OAuth credentials, target table
- **Tag Selection**: Mode (folder/pattern/explicit) and paths
- **Performance**: Batch size, flush interval, queue size, rate limit
- **Control**: Enable/disable, debug logging

## Proxy Configuration

During development, API requests are proxied to `http://localhost:8088` as configured in `package.json`:

```json
"proxy": "http://localhost:8088"
```

This avoids CORS issues when testing against a local Ignition Gateway.

## Production Build

The production build is optimized and minified. Static assets (JS, CSS, images) have content hashes for cache busting.

## Browser Support

Supports modern browsers:
- Chrome (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)
- Edge (last 2 versions)

