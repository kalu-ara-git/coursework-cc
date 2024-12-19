healthsync/
├── kubernetes/               # Kubernetes manifests and configs
│   ├── patient-service/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   ├── appointment-service/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   ├── notification-service/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   └── aggregator-job.yaml    # CronJob for aggregation service
├── microservices/            # Source code for all microservices
│   ├── patient-service/
│   │   ├── app/
│   │   │   ├── app.py         # Main application logic
│   │   │   ├── database.py    # Database connection logic
│   │   │   ├── models.py      # Database models
│   │   └── Dockerfile
│   │   └── requirements.txt
│   ├── appointment-service/
│   │   ├── app/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── notification-service/
│   │   ├── app/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── aggregator-service/
│       ├── app/
│       ├── Dockerfile
│       └── requirements.txt
├── database/                 # SQL scripts for database setup
│   ├── init.sql               # Schema setup for Patient, Appointments, etc.
│   ├── seed.sql               # Seed data for testing
├── scripts/                  # Automation scripts
│   ├── start_minikube.sh      # Script to start Minikube and apply configs
│   ├── build_docker.sh        # Build Docker images for microservices
│   ├── deploy_services.sh     # Deploy all Kubernetes services
│   └── test_apis.sh           # Postman collection runner or API tests
├── ci-cd/                    # CI/CD pipeline configurations
│   ├── github-actions/        # GitHub Actions YAML files
│   ├── jenkins-pipeline/      # Jenkins pipeline scripts
├── postman/                  # Postman collections and environment
│   ├── healthsync.postman_collection.json
│   ├── healthsync.postman_environment.json
└── docs/                     # Documentation
    ├── architecture_diagram.png
    ├── README.md              # Instructions for setting up and running the project
