#!/bin/bash

# Prompt Ops Hub Release Tagging Script
# Tags the current commit with a version number

set -e

# Default version
VERSION=${1:-"v0.3.0-clean"}

echo "🏷️  Tagging Prompt Ops Hub release: $VERSION"

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Warning: Not on main branch (currently on $CURRENT_BRANCH)"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Tagging cancelled"
        exit 1
    fi
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Working directory is not clean. Please commit or stash changes first."
    git status --short
    exit 1
fi

# Check if tag already exists
if git tag -l | grep -q "^$VERSION$"; then
    echo "❌ Tag $VERSION already exists"
    exit 1
fi

# Create and push tag
echo "📝 Creating tag: $VERSION"
git tag -a "$VERSION" -m "Release $VERSION - Cleanup and CI pipeline"

echo "✅ Tag $VERSION created successfully!"
echo ""
echo "To push the tag to remote:"
echo "  git push origin $VERSION"
echo ""
echo "To delete the tag (if needed):"
echo "  git tag -d $VERSION"
echo "  git push origin :refs/tags/$VERSION" 