# Credit Approval System Backend

This is the backend of the credit approval system. It is a RESTful API that is used to manage the credit approval system. It is built using the Django REST framework.

## Prerequisites

- Docker
- Docker Compose
- Git

## Installation

1. Clone the repository

```bash
git clone https://github.com/henishpatel9045/CreditApprovalBackend
```

2. Change the directory to the cloned repository

```bash
cd CreditApprovalBackend
```

3. Create a `.env` file in the root directory of the project from the `.env.example` file and fill in the required environment variables.

4. Run the docker-compose file

```bash
docker-compose up --build -d
```

5. The backend will be running on `http://localhost:8000`

## API Documentation

The API documentation can be found at `http://localhost:8000/swagger/`
