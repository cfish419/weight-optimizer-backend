# Aircraft Weight Optimizer Backend

A FastAPI-based backend service for optimizing aircraft baggage loading positions. This service helps optimize fuel efficiency and aircraft stability through intelligent baggage placement and automated measurements.

## Features

- 🛫 **Aircraft Loading Optimization**
  - Calculates optimal baggage positions for fuel efficiency
  - Ensures aircraft stability through center of gravity calculations
  - Generates sequential loading plans with color coding

- 📸 **Automated Baggage Measurement**
  - Computer vision-based dimension measurement
  - Automated weight and density calculations
  - Image processing for baggage analysis

- 🔧 **Smart Planning**
  - Real-time loading plan generation
  - Stability score calculations
  - Fuel efficiency optimization

## Quick Start

1. **Setup Python Environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**

   ```bash
   cp .env.example .env
   # Edit .env with your database and AWS credentials
   ```

3. **Run Development Server**

   ```bash
   uvicorn src.main:app --reload
   ```

4. **Run Tests**

   ```bash
   PYTHONPATH=. pytest
   ```

## API Documentation

Once running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```plaintext
weight-optimizer-backend/
├── src/
│   ├── api/              # API endpoints
│   ├── services/         # Business logic
│   │   ├── computer_vision/  # Image processing
│   │   └── optimization/     # Loading optimization
│   └── db/               # Database models and config
├── tests/               # Test suites
└── requirements.txt     # Dependencies
```

## Technology Stack

- **FastAPI**: Web framework
- **SQLAlchemy**: Database ORM
- **OpenCV/NumPy**: Computer vision and calculations
- **pytest**: Testing framework
- **PostgreSQL**: Primary database
- **AWS S3**: Image storage

## Development Requirements

- Python 3.11+
- PostgreSQL
- AWS Account (for S3 image storage)

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request
