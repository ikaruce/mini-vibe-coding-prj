# Build Docker image for test execution sandbox

# Navigate to docker directory and build
cd docker/test-runner
docker build -t ai-assistant-test-runner .
cd ../..

# Show image info
docker images ai-assistant-test-runner