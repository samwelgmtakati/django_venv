#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python version (if pyenv is available)
if command -v pyenv &> /dev/null; then
    pyenv install -s 3.12.3
    pyenv global 3.12.3
fi

# Update pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Create cache table if using database cache
python manage.py createcachetable

echo "Build completed successfully!"
