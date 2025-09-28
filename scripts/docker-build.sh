#!/bin/bash

# Docker Build Script for Databricks Delta Lake Project
# This script demonstrates how to use the parameterized Dockerfile

set -e

# Default values
TARGET="api"
ENV_FILE="example.env"
ENVIRONMENT="dev"
TAG_SUFFIX=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            TARGET="$2"
            shift 2
            ;;
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --tag-suffix)
            TAG_SUFFIX="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --target TARGET        Docker build target (api, data-processing, production, development)"
            echo "  --env-file FILE        Environment file to use (default: example.env)"
            echo "  --environment ENV      Environment name (default: dev)"
            echo "  --tag-suffix SUFFIX    Additional tag suffix"
            echo "  -h, --help            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --target api --env-file dev.env --environment dev"
            echo "  $0 --target data-processing --env-file test.env --environment test"
            echo "  $0 --target api --env-file prod.env --environment prod --tag-suffix latest"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate target
case $TARGET in
    api|data-processing|production|development)
        ;;
    *)
        echo "Error: Invalid target '$TARGET'. Valid targets are: api, data-processing, production, development"
        exit 1
        ;;
esac

# Check if environment file exists
if [[ ! -f "config/environments/$ENV_FILE" ]]; then
    echo "Error: Environment file 'config/environments/$ENV_FILE' not found"
    echo "Available environment files:"
    ls -1 config/environments/ 2>/dev/null || echo "  No environment files found"
    exit 1
fi

# Build image tag
IMAGE_NAME="delta-lake-$TARGET"
if [[ -n "$TAG_SUFFIX" ]]; then
    TAG="$ENVIRONMENT-$TAG_SUFFIX"
else
    TAG="$ENVIRONMENT"
fi

echo "Building Docker image..."
echo "  Target: $TARGET"
echo "  Environment file: $ENV_FILE"
echo "  Environment: $ENVIRONMENT"
echo "  Image: $IMAGE_NAME:$TAG"
echo ""

# Build the Docker image
docker build \
    --target "$TARGET" \
    --build-arg ENV_FILE="$ENV_FILE" \
    --build-arg ENVIRONMENT="$ENVIRONMENT" \
    -t "$IMAGE_NAME:$TAG" \
    .

echo ""
echo "✅ Successfully built $IMAGE_NAME:$TAG"
echo ""
echo "To run the container:"
echo "  docker run -p 8000:8000 $IMAGE_NAME:$TAG"
echo ""
echo "To run with environment file mounted:"
echo "  docker run -p 8000:8000 -v \$(pwd)/config/environments/$ENV_FILE:/app/config/environments/$ENV_FILE $IMAGE_NAME:$TAG"
