# Quick Start Guide

Get the VitalMatch frontend running locally in 5 minutes.

## Prerequisites

- Node.js 16+ installed
- npm or yarn package manager
- Backend API running (or use mock data)

## Installation

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   ```

4. **Update API endpoint in `.env`:**
   ```
   VITE_API_ENDPOINT=https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod
   ```

   Or for local development with mock data:
   ```
   VITE_API_ENDPOINT=http://localhost:8000
   ```

5. **Start development server:**
   ```bash
   npm run dev
   ```

6. **Open browser:**
   Navigate to `http://localhost:3000`

## Testing the Application

### With Real Backend

If your backend API is deployed:

1. Fill out the patient profile form
2. Submit and watch the processing indicator
3. View match results
4. Click on a trial to see details

### With Mock Data (Development)

If you don't have the backend running, you can modify `src/api/client.js` to return mock data:

```javascript
export const matchTrials = async (patientProfile) => {
  // Mock response for development
  return {
    matches: [
      {
        trial_id: "NCT12345678",
        title: "Phase II Study of Drug X in NSCLC Patients",
        match_score: 0.92,
        explanation: "High match: Trial specifically seeks patients with smoking history. Age and location criteria met.",
        key_criteria: [
          "✅ History of smoking (required)",
          "✅ Age 18-70 (patient: 65)",
          "✅ Location: New York area",
          "⚠️ Hypertension noted - may require monitoring"
        ],
        location: "Memorial Sloan Kettering, NYC (12 miles)",
        description: "This is a Phase II clinical trial studying the effectiveness of Drug X...",
        inclusion_text: "Patients must have confirmed NSCLC diagnosis...",
        exclusion_text: "Patients with active infections are excluded..."
      }
    ],
    total_trials_considered: 1247,
    hard_filtered_count: 43,
    processing_time_ms: 8500
  }
}
```

## Project Structure Overview

```
frontend/
├── src/
│   ├── api/client.js              # API communication
│   ├── components/                # React components
│   ├── App.jsx                    # Main app
│   └── main.jsx                   # Entry point
├── index.html                     # HTML template
├── package.json                   # Dependencies
└── vite.config.js                 # Vite configuration
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

## Common Issues

### Port 3000 already in use

Change the port in `vite.config.js`:
```javascript
export default defineConfig({
  server: {
    port: 3001  // Use different port
  }
})
```

### API connection errors

Check:
1. API endpoint in `.env` is correct
2. Backend is running and accessible
3. CORS is configured on backend
4. Network/firewall settings

### Module not found errors

Reinstall dependencies:
```bash
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for AWS deployment
- Explore the component files in `src/components/`
- Customize styling in the `.css` files

## Need Help?

- Check browser console for errors
- Review the component code for examples
- Ensure backend API is returning expected format
- Verify environment variables are set correctly
