#!/bin/bash
# Release script for Ignition Zerobus Connector
# Usage: ./release.sh <version>
# Example: ./release.sh 1.0.0

set -e

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Error: Version number required"
    echo "Usage: ./release.sh <version>"
    echo "Example: ./release.sh 1.0.0"
    exit 1
fi

echo "================================================"
echo "Creating release v${VERSION}"
echo "================================================"
echo ""

# Check if working directory is clean
if [[ -n $(git status -s) ]]; then
    echo "Error: Working directory is not clean"
    echo "Please commit or stash changes first"
    git status -s
    exit 1
fi

# Update version in build.gradle if needed
echo "Step 1: Checking version in build.gradle..."
cd module
GRADLE_VERSION=$(grep "version = " build.gradle | cut -d'"' -f2)
echo "Current version in build.gradle: $GRADLE_VERSION"

if [ "$GRADLE_VERSION" != "$VERSION" ]; then
    echo "Updating version in build.gradle to $VERSION..."
    sed -i.bak "s/version = \".*\"/version = \"$VERSION\"/" build.gradle
    rm build.gradle.bak
    git add build.gradle
    git commit -m "Bump version to $VERSION"
fi

# Clean and build
echo ""
echo "Step 2: Building module..."
./gradlew clean buildModule

# Check if .modl file was created
MODL_FILE="build/modules/zerobus-connector-${VERSION}.modl"
if [ ! -f "$MODL_FILE" ]; then
    echo "Error: Module file not found: $MODL_FILE"
    exit 1
fi

# Get file size
FILE_SIZE=$(ls -lh "$MODL_FILE" | awk '{print $5}')
echo "Module built successfully: $FILE_SIZE"

cd ..

# Create git tag
echo ""
echo "Step 3: Creating git tag..."
git tag -a "v${VERSION}" -m "Release version ${VERSION}"

echo ""
echo "================================================"
echo "Release preparation complete!"
echo "================================================"
echo ""
echo "Module file: module/$MODL_FILE"
echo "Git tag created: v${VERSION}"
echo ""
echo "Next steps:"
echo "1. Push the tag:"
echo "   git push origin v${VERSION}"
echo ""
echo "2. Go to GitHub:"
echo "   https://github.com/pravinva/lakeflow-ignition-zerobus-connector/releases/new"
echo ""
echo "3. Select tag: v${VERSION}"
echo ""
echo "4. Upload the module file:"
echo "   module/$MODL_FILE"
echo ""
echo "5. Copy release notes from RELEASE_NOTES_v${VERSION}.md"
echo ""

