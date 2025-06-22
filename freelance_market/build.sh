#!/usr/bin/env bash
# Exit on any error
set -e

# Install system dependencies for MySQL client and Python
echo "Installing system dependencies..."
if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu
    apt-get update && apt-get install -y \
        default-libmysqlclient-dev \
        python3-dev \
        python3-pip \
        python3-venv \
        gcc
elif [ -f /etc/redhat-release ]; then
    # RHEL/CentOS
    yum install -y \
        mysql-devel \
        python3-devel \
        python3-pip \
        gcc
fi

# Ensure pip is up to date and install required packages
echo "Upgrading pip and installing Python packages..."
python3 -m pip install --upgrade pip
pip install --no-cache-dir gunicorn

# Install Python version (if pyenv is available)
if command -v pyenv &> /dev/null; then
    pyenv install -s 3.12.3
    pyenv global 3.12.3
fi

# Install project dependencies
echo "Installing project dependencies..."
pip install --no-cache-dir -r requirements.txt

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Build completed successfully!"

python manage.py migrate

# Create cache table if using database cache
python manage.py createcachetable

echo "Build completed successfully!"
