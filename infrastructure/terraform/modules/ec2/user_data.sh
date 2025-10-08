#!/bin/bash
# User Data Script for Weight Optimizer EC2 Instance

set -e

# Update system
yum update -y

# Install required packages
yum install -y \
    docker \
    awscli \
    amazon-cloudwatch-agent \
    htop \
    git \
    curl \
    wget \
    unzip

# Start and enable Docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Create application directories
mkdir -p /opt/weight-optimizer/{data,logs,config}
chown -R ec2-user:ec2-user /opt/weight-optimizer

# Mount additional EBS volume for data
mkfs -t xfs /dev/nvme1n1
mkdir -p /opt/weight-optimizer/data
mount /dev/nvme1n1 /opt/weight-optimizer/data
echo '/dev/nvme1n1 /opt/weight-optimizer/data xfs defaults,nofail 0 2' >> /etc/fstab
chown -R ec2-user:ec2-user /opt/weight-optimizer/data

# Create environment file template
cat > /opt/weight-optimizer/.env << 'EOF'
# Weight Optimizer Environment Configuration
ENVIRONMENT=${environment}
PROJECT_NAME=${project_name}

# Database Configuration
DATABASE_URL=postgresql://weight_user:CHANGE_ME@localhost:5432/weight_optimizer

# Application Settings
SECRET_KEY=CHANGE_ME_IN_PRODUCTION
JWT_SECRET=CHANGE_ME_IN_PRODUCTION
LOG_LEVEL=INFO

# AWS Configuration
AWS_REGION=${ecr_region}
AWS_DEFAULT_REGION=${ecr_region}

# Docker Configuration
COMPOSE_PROJECT_NAME=${project_name}
EOF

chown ec2-user:ec2-user /opt/weight-optimizer/.env
chmod 600 /opt/weight-optimizer/.env

# Create deployment script
cat > /opt/weight-optimizer/deploy.sh << 'EOF'
#!/bin/bash
set -e

cd /opt/weight-optimizer

# Login to ECR
aws ecr get-login-password --region ${ecr_region} | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.${ecr_region}.amazonaws.com

# Pull latest image
ECR_REGISTRY=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.${ecr_region}.amazonaws.com
docker pull $ECR_REGISTRY/${project_name}:latest

# Stop existing containers
docker-compose down || true

# Start new containers
docker-compose up -d

# Wait for health check
sleep 30
curl -f http://localhost:8000/health || exit 1

echo "Deployment completed successfully at $(date)"
EOF

chmod +x /opt/weight-optimizer/deploy.sh
chown ec2-user:ec2-user /opt/weight-optimizer/deploy.sh

# Create docker-compose file for production
cat > /opt/weight-optimizer/docker-compose.yml << 'EOF'
version: '3.8'

services:
  app:
    image: $(aws sts get-caller-identity --query Account --output text).dkr.ecr.${ecr_region}.amazonaws.com/${project_name}:latest
    container_name: weight-optimizer-app
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  database:
    image: postgres:15-alpine
    container_name: weight-optimizer-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: weight_optimizer
      POSTGRES_USER: weight_user
      POSTGRES_PASSWORD: ${DB_PASSWORD:-secure_password_change_me}
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U weight_user -d weight_optimizer"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: weight-optimizer-redis
    restart: unless-stopped
    volumes:
      - ./data/redis:/data
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
EOF

chown ec2-user:ec2-user /opt/weight-optimizer/docker-compose.yml

# Configure CloudWatch Agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -s \
    -c ssm:/aws/ec2/${project_name}/cloudwatch-config

# Create systemd service for automatic startup
cat > /etc/systemd/system/weight-optimizer.service << 'EOF'
[Unit]
Description=Weight Optimizer Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/weight-optimizer
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=ec2-user
Group=ec2-user

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable weight-optimizer.service

# Create log rotation
cat > /etc/logrotate.d/weight-optimizer << 'EOF'
/opt/weight-optimizer/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 ec2-user ec2-user
}
EOF

# Set up automatic security updates
yum install -y yum-cron
systemctl enable yum-cron
systemctl start yum-cron

# Configure SSH hardening
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl restart sshd

# Install and configure fail2ban
yum install -y epel-release
yum install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# Signal completion
/opt/aws/bin/cfn-signal -e $? --stack ${AWS::StackName} --resource AutoScalingGroup --region ${AWS::Region} || true

echo "EC2 initialization completed at $(date)" >> /var/log/user-data.log