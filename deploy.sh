#!/usr/bin/env bash
#
# deploy.sh — Build and deploy the Lambda function
#
# Usage:
#   ./deploy.sh                  # deploy to default function
#   ./deploy.sh my-function      # deploy to a specific function name
#
set -euo pipefail

FUNCTION_NAME="${1:-cPaas-sNow-summarisation-agent}"
BUILD_DIR="/tmp/lambda_linux_build"
ZIP_FILE="/tmp/lambda_deploy.zip"
SOURCE_FILES=(
    lambda_handler.py
    app.py
    config.py
    servicenow_client.py
    summarizer.py
    formatter.py
)

echo "━━━ Step 1: Install dependencies (Linux x86_64) ━━━"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/vendor"
pip install \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.13 \
    --only-binary=:all: \
    --target "$BUILD_DIR/vendor" \
    -r requirements.txt \
    --quiet

echo "━━━ Step 2: Copy source files ━━━"
for f in "${SOURCE_FILES[@]}"; do
    cp "$f" "$BUILD_DIR/"
    echo "  ✓ $f"
done

echo "━━━ Step 3: Create zip package ━━━"
rm -f "$ZIP_FILE"
cd "$BUILD_DIR"
zip -r "$ZIP_FILE" . -x '__pycache__/*' '*.pyc' '*.dist-info/*' --quiet
SIZE=$(du -h "$ZIP_FILE" | cut -f1)
echo "  ✓ $ZIP_FILE ($SIZE)"

echo "━━━ Step 4: Deploy to Lambda ━━━"
LAST_MODIFIED=$(aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --zip-file "fileb://$ZIP_FILE" \
    --query 'LastModified' \
    --output text)
echo "  ✓ Deployed $FUNCTION_NAME — $LAST_MODIFIED"

echo ""
echo "✅ Done!"
