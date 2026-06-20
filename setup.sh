#!/bin/bash
# ============================================================================
# Timelyna - Complete Docker Setup & Deployment Script
# ============================================================================
# This script handles the complete setup and deployment of Timelyna
# Usage: bash setup.sh [options]
#
# Options:
#   setup        - Full setup (build + start + seed)
#   build        - Build Docker images
#   up           - Start all services
#   down         - Stop all services
#   reset        - Full reset (delete data)
#   seed         - Seed database with test data
#   logs         - View logs
#   status       - Show system status
#   test         - Run tests
#   help         - Show this help message
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="timelyna"
DOCKER_COMPOSE_FILE="docker-compose.yml"
BACKEND_PORT="8000"
FRONTEND_PORT="80"
DB_PORT="5432"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

print_header() {
  echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║${NC} $1"
  echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"
}

print_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
  echo -e "${RED}❌ $1${NC}"
}

print_warning() {
  echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
  echo -e "${BLUE}ℹ️  $1${NC}"
}

check_docker() {
  if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
  fi
  print_success "Docker installed"

  if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
  fi
  print_success "Docker Compose installed"
}

check_docker_running() {
  if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker."
    exit 1
  fi
  print_success "Docker daemon is running"
}

# ============================================================================
# MAIN FUNCTIONS
# ============================================================================

cmd_setup() {
  print_header "🚀 COMPLETE SETUP - Build + Start + Seed"

  cmd_build
  cmd_up
  sleep 5
  cmd_seed
  cmd_status

  print_header "✨ SETUP COMPLETE!"
  echo -e "${GREEN}Your application is ready!${NC}\n"
  echo "Access your application:"
  echo -e "  Frontend:  ${BLUE}http://localhost${NC}"
  echo -e "  Backend:   ${BLUE}http://localhost:${BACKEND_PORT}${NC}"
  echo -e "  PgAdmin:   ${BLUE}http://localhost:5050${NC}\n"
  echo "Test Credentials:"
  echo "  Email:    admin@timelyna.com"
  echo "  Password: Admin1234!\n"
}

cmd_build() {
  print_header "🔨 Building Docker Images"

  if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    print_error "docker-compose.yml not found. Make sure you're in the project root."
    exit 1
  fi

  print_info "Building backend..."
  docker-compose build backend
  print_success "Backend built"

  print_info "Building frontend..."
  docker-compose build frontend
  print_success "Frontend built"
}

cmd_up() {
  print_header "🚀 Starting Services"

  print_info "Starting PostgreSQL..."
  docker-compose up -d postgres
  sleep 3
  docker-compose logs postgres | grep "database system is ready" && print_success "PostgreSQL ready" || print_warning "PostgreSQL starting..."

  print_info "Starting Redis..."
  docker-compose up -d redis
  sleep 2
  print_success "Redis started"

  print_info "Starting Backend..."
  docker-compose up -d backend
  sleep 3
  print_success "Backend started"

  print_info "Starting Frontend..."
  docker-compose up -d frontend
  sleep 2
  print_success "Frontend started"

  print_info "Starting Celery Worker..."
  docker-compose up -d celery-worker
  print_success "Celery Worker started"

  print_info "Starting Celery Beat..."
  docker-compose up -d celery-beat
  print_success "Celery Beat started"

  print_info "Starting PgAdmin..."
  docker-compose up -d pgadmin
  print_success "PgAdmin started"
}

cmd_down() {
  print_header "🛑 Stopping Services"

  docker-compose down
  print_success "All services stopped"
}

cmd_reset() {
  print_header "⚠️  FULL RESET (This will delete all data!)"

  echo -e "${YELLOW}This will:${NC}"
  echo "  1. Stop all containers"
  echo "  2. Delete all volumes (DATA LOSS!)"
  echo "  3. Remove all containers"
  echo ""

  read -p "Are you sure? Type 'yes' to continue: " confirm
  if [ "$confirm" != "yes" ]; then
    print_info "Reset cancelled"
    return
  fi

  print_info "Stopping containers..."
  docker-compose down -v --remove-orphans || true

  print_info "Removing unused images..."
  docker system prune -f || true

  print_success "Full reset complete"
  print_info "Run 'bash setup.sh setup' to start fresh"
}

cmd_seed() {
  print_header "🌱 Seeding Database"

  print_info "Checking if database is ready..."
  sleep 3

  print_info "Running seed script..."
  docker-compose exec -T backend python seed_dev.py

  print_success "Database seeded with test data"
  print_info "Test users created:"
  echo "  • admin@timelyna.com / Admin1234!"
  echo "  • manager@timelyna.com / Manager1234!"
  echo "  • employee@timelyna.com / Employee1234!"
  echo "  • finance@timelyna.com / Finance1234!"
}

cmd_logs() {
  print_header "📋 Service Logs"

  service=$1

  if [ -z "$service" ]; then
    print_info "Showing all logs (Press Ctrl+C to exit)"
    docker-compose logs -f
  else
    print_info "Showing $service logs (Press Ctrl+C to exit)"
    docker-compose logs -f "$service"
  fi
}

cmd_status() {
  print_header "📊 System Status"

  echo -e "${BLUE}Docker Compose Status:${NC}"
  docker-compose ps

  echo ""
  echo -e "${BLUE}Service Health Checks:${NC}"

  # Check Backend
  if curl -s http://localhost:${BACKEND_PORT}/api/v1/auth/login \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"email":"test","password":"test"}' | grep -q "detail"; then
    print_success "Backend responding on port ${BACKEND_PORT}"
  else
    print_warning "Backend may not be ready yet"
  fi

  # Check Frontend
  if curl -s -o /dev/null -w "%{http_code}" http://localhost:${FRONTEND_PORT}/ | grep -q "200"; then
    print_success "Frontend responding on port ${FRONTEND_PORT}"
  else
    print_warning "Frontend may not be ready yet"
  fi

  echo ""
  echo -e "${BLUE}Access Points:${NC}"
  echo "  • Frontend:  http://localhost:${FRONTEND_PORT}"
  echo "  • Backend:   http://localhost:${BACKEND_PORT}"
  echo "  • Database:  localhost:${DB_PORT}"
  echo "  • PgAdmin:   http://localhost:5050"
}

cmd_test() {
  print_header "🧪 Running Tests"

  print_info "Testing login endpoint..."
  LOGIN=$(curl -s -X POST http://localhost:${BACKEND_PORT}/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@timelyna.com","password":"Admin1234!"}')

  if echo "$LOGIN" | grep -q "access_token"; then
    print_success "✓ Login successful"
    TOKEN=$(echo "$LOGIN" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
  else
    print_error "✗ Login failed"
    return
  fi

  print_info "Testing /admin/users endpoint..."
  USERS=$(curl -s -X GET "http://localhost:${BACKEND_PORT}/api/v1/admin/users?page_size=5" \
    -H "Authorization: Bearer $TOKEN")

  if echo "$USERS" | grep -q "employee_id"; then
    print_success "✓ /admin/users endpoint working"
  else
    print_error "✗ /admin/users endpoint failed"
  fi

  print_info "Testing /finance/invoices endpoint..."
  INVOICES=$(curl -s -X GET "http://localhost:${BACKEND_PORT}/api/v1/finance/invoices" \
    -H "Authorization: Bearer $TOKEN")

  if echo "$INVOICES" | grep -q "invoice_id"; then
    print_success "✓ /finance/invoices endpoint working"
  else
    print_error "✗ /finance/invoices endpoint failed"
  fi

  print_info "Testing frontend..."
  if curl -s -o /dev/null -w "%{http_code}" http://localhost:${FRONTEND_PORT}/ | grep -q "200"; then
    print_success "✓ Frontend is responding"
  else
    print_error "✗ Frontend is not responding"
  fi

  print_header "✅ Test Summary"
  echo "All critical systems are operational!"
}

cmd_restart() {
  print_header "🔄 Restarting Services"

  docker-compose restart
  print_success "All services restarted"

  sleep 3
  cmd_status
}

cmd_clean() {
  print_header "🧹 Cleaning Up"

  print_info "Removing stopped containers..."
  docker container prune -f || true

  print_info "Removing unused images..."
  docker image prune -f || true

  print_info "Removing unused volumes..."
  docker volume prune -f || true

  print_success "Cleanup complete"
}

cmd_help() {
  cat << 'EOF'
╔═══════════════════════════════════════════════════════════════════════════╗
║                    Timelyna Setup Script                              ║
║                                                                           ║
║  Complete Docker deployment automation                                    ║
╚═══════════════════════════════════════════════════════════════════════════╝

USAGE:
  bash setup.sh [COMMAND] [OPTIONS]

COMMANDS:
  setup       Full setup (build + start + seed database)
  build       Build Docker images only
  up          Start all services
  down        Stop all services
  restart     Restart all services
  reset       Full reset (DELETE ALL DATA!)
  seed        Seed database with test data
  status      Show system status
  logs        View service logs (add service name for specific log)
  test        Run endpoint tests
  clean       Clean up stopped containers and unused images
  help        Show this help message

EXAMPLES:
  # Complete setup from scratch
  bash setup.sh setup

  # Just build the images
  bash setup.sh build

  # Start services
  bash setup.sh up

  # View backend logs
  bash setup.sh logs backend

  # Check system status
  bash setup.sh status

  # Run tests
  bash setup.sh test

  # Stop everything
  bash setup.sh down

  # Full reset (be careful!)
  bash setup.sh reset

TEST CREDENTIALS:
  Admin:    admin@timelyna.com / Admin1234!
  Manager:  manager@timelyna.com / Manager1234!
  Employee: employee@timelyna.com / Employee1234!
  Finance:  finance@timelyna.com / Finance1234!

ACCESS POINTS:
  Frontend:  http://localhost
  Backend:   http://localhost:8000
  API Docs:  http://localhost:8000/docs
  PgAdmin:   http://localhost:5050

DOCUMENTATION:
  README_TESTING.md  - Quick start guide
  FINAL_SUMMARY.md   - Complete overview
  DEBUGGING_GUIDE.md - Troubleshooting
  USEFUL_COMMANDS.sh - More commands

For help with specific issues, see the documentation files in the project root.
EOF
}

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

main() {
  local command="${1:-help}"

  # Check prerequisites
  check_docker
  check_docker_running

  case "$command" in
    setup)
      cmd_setup
      ;;
    build)
      cmd_build
      ;;
    up)
      cmd_up
      cmd_status
      ;;
    down)
      cmd_down
      ;;
    restart)
      cmd_restart
      ;;
    reset)
      cmd_reset
      ;;
    seed)
      cmd_seed
      ;;
    status)
      cmd_status
      ;;
    logs)
      cmd_logs "$2"
      ;;
    test)
      cmd_test
      ;;
    clean)
      cmd_clean
      ;;
    help|--help|-h)
      cmd_help
      ;;
    *)
      print_error "Unknown command: $command"
      echo ""
      cmd_help
      exit 1
      ;;
  esac
}

# Run main function with all arguments
main "$@"
