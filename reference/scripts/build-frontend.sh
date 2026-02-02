#!/bin/bash
# Build Next.js frontend for production

set -e

echo "Building Next.js frontend for production..."

cd app/frontend

# Install dependencies
echo "Installing dependencies..."
npm ci

# Build for production
echo "Building..."
npm run build

echo "✓ Frontend build complete"
