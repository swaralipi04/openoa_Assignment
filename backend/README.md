# OpenOA Backend API

REST API wrapping the [OpenOA](https://github.com/NREL/OpenOA) wind plant operational analysis library.

## Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

## API Endpoints

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Service health check |

### Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/data/upload` | Upload CSV data files |
| POST | `/api/data/example` | Load La Haute Borne example dataset |
| GET | `/api/data/list` | List loaded datasets |
| GET | `/api/data/{id}/summary` | Get dataset summary |
| DELETE | `/api/data/{id}` | Delete dataset |

### Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analysis/aep` | Monte Carlo AEP estimation |
| POST | `/api/analysis/electrical-losses` | Electrical losses analysis |
| POST | `/api/analysis/turbine-energy` | Turbine long-term gross energy |
| POST | `/api/analysis/wake-losses` | Wake losses analysis |

## Docker

```bash
docker build -t openoa-api .
docker run -p 8000:8000 openoa-api
```
