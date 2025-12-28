# 🎯 UDO Dashboard v3.0 - Web Interface

Real-time monitoring and control interface for the Unified Development Orchestrator platform.

## 🚀 Features

### Real-Time Monitoring
- **System Status**: Live status of all UDO components (Orchestrator, Uncertainty Map, AI Connector, ML System, 3-AI Bridge)
- **Phase Progress**: Visual tracking of development phases (Ideation → Design → MVP → Implementation → Testing)
- **Uncertainty Analysis**: Quantum state visualization with predictive insights
- **Performance Metrics**: Confidence trends, phase performance radar, execution statistics

### AI Collaboration
- **3-AI Bridge Status**: Real-time status of Claude, Codex MCP, and Gemini
- **Active Patterns**: Visualization of current AI collaboration patterns
- **Service Health**: Individual AI service availability and processing status

### Control Panel
- **Task Execution**: Submit tasks for immediate execution
- **Quick Templates**: Pre-defined task templates for common operations
- **ML Training**: Trigger model training with one click
- **System Reset**: Reset system state when needed

### Execution History
- **Detailed Logs**: Complete history of all executed tasks
- **Decision Tracking**: GO/NO_GO/CHECKPOINTS decisions with confidence levels
- **Performance Stats**: Success rates and confidence metrics

## 📦 Tech Stack

### Frontend
- **Next.js 15**: Latest App Router with Turbopack
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Framer Motion**: Smooth animations
- **Recharts**: Data visualization
- **TanStack Query**: Server state management
- **Socket.io Client**: Real-time WebSocket connections

### Backend
- **FastAPI**: High-performance Python web framework
- **WebSockets**: Real-time bidirectional communication
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server for production

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn

### Quick Start

#### Windows
```bash
# Clone the repository
git clone https://github.com/yourusername/UDO-Development-Platform.git
cd UDO-Development-Platform

# Run the startup script
start_dashboard.bat
```

#### macOS/Linux
```bash
# Clone the repository
git clone https://github.com/yourusername/UDO-Development-Platform.git
cd UDO-Development-Platform

# Run the startup script
python start_dashboard.py
```

### Manual Setup

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python main.py
```
The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

#### Frontend Setup
```bash
cd web-dashboard
npm install
npm run dev
```
The dashboard will be available at `http://localhost:3000`

## 🎨 Dashboard Components

### 1. System Status Panel
Shows real-time health of all UDO components:
- ✅ Green: Component operational
- ❌ Red: Component offline
- Overall system health indicator

### 2. Phase Progress
Interactive phase selector with visual progress:
- Click to change active phase
- Progress bar shows completion percentage
- Color-coded phase states (completed/current/future)

### 3. Uncertainty Map
Advanced predictive analytics display:
- **Quantum States**: Deterministic, Probabilistic, Quantum, Chaotic, Void
- **Confidence Meter**: Real-time confidence level
- **Risk Assessment**: Dynamic risk calculation
- **24h Prediction**: Stability and action recommendations

### 4. Performance Metrics
Comprehensive performance visualization:
- **Confidence Trend**: 24-hour confidence history chart
- **Phase Radar**: Multi-dimensional phase performance
- **Key Metrics**: Average confidence and total executions

### 5. AI Collaboration
3-AI system status and patterns:
- Individual AI service status
- Active collaboration patterns
- Real-time processing indicators

### 6. Control Panel
Task execution interface:
- Text area for task description
- Quick template buttons
- Auto/Manual mode selection
- ML model training trigger

### 7. Execution History
Scrollable history with statistics:
- Task details with timestamps
- Decision outcomes (GO/NO_GO/CHECKPOINTS)
- Confidence and uncertainty levels
- Summary statistics

## 🔌 API Endpoints

### Core Endpoints
- `GET /api/health`: System health check
- `GET /api/status`: Complete system status
- `GET /api/metrics`: Dashboard metrics and statistics
- `POST /api/execute`: Execute development cycle
- `POST /api/train`: Train ML models
- `GET /api/phases/{phase}`: Get phase-specific data

### Control Endpoints
- `POST /api/control`: System control commands
  - `reset`: Reset system state
  - `save_state`: Save current state
  - `change_phase`: Change active phase

### Real-Time
- `WS /ws`: WebSocket connection for real-time updates

## 🎯 Usage Examples

### Execute a Task
1. Enter task description in the Control Panel
2. Select current phase (or use auto-detection)
3. Click "Execute" button
4. Monitor progress in Execution History

### Train ML Models
1. Click "Train ML Models" in Control Panel
2. Monitor training progress
3. View updated model metrics

### Monitor System Health
1. Check System Status panel for component health
2. Review Uncertainty Map for risk assessment
3. Analyze Performance Metrics for trends

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the web-dashboard directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend Configuration
Modify `backend/main.py` for:
- CORS origins
- WebSocket settings
- API port and host

## 📊 Real-Time Features

### WebSocket Events
- `connection_established`: Initial connection with system state
- `task_executed`: Task completion notifications
- `phase_changed`: Phase transition updates
- `error`: Error notifications

### Auto-Refresh
- Metrics refresh every 5 seconds
- WebSocket maintains persistent connection
- Automatic reconnection on disconnect

## 🐛 Troubleshooting

### Backend Issues
```bash
# Check if port 8000 is in use
netstat -an | findstr 8000

# Kill existing process
taskkill /F /PID <process_id>
```

### Frontend Issues
```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Connection Issues
- Ensure both backend and frontend are running
- Check firewall settings
- Verify CORS configuration

## 📈 Performance Optimization

### Production Build
```bash
# Frontend production build
cd web-dashboard
npm run build
npm start

# Backend production mode
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Caching
- TanStack Query caches API responses
- Stale time: 2 seconds
- Refetch interval: 5 seconds

## 🎨 Customization

### Themes
Modify `tailwind.config.js` for custom color schemes

### Components
All components in `components/dashboard/` are modular and customizable

### Charts
Recharts configuration in each metric component

## 📝 Development

### Adding New Components
1. Create component in `components/dashboard/`
2. Import in `dashboard.tsx`
3. Add corresponding API endpoint if needed

### Adding New Metrics
1. Update backend metrics endpoint
2. Modify MetricsChart component
3. Add visualization logic

## 🚀 Deployment

### Docker Deployment
```dockerfile
# Backend Dockerfile
FROM python:3.9
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Vercel Deployment (Frontend)
```bash
npm install -g vercel
vercel
```

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open pull request

## 📞 Support

For issues and questions:
- GitHub Issues: [Create Issue](https://github.com/yourusername/UDO-Development-Platform/issues)
- Documentation: [Full Docs](./README.md)

---

**Version**: 3.0.0
**Last Updated**: 2025-11-17
**Status**: Production Ready (Beta)
