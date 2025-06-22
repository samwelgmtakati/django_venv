#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install system dependencies for MySQL client
if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu
    apt-get update && apt-get install -y \
        default-libmysqlclient-dev \
        python3-dev \
        python3-pip
elif [ -f /etc/redhat-release ]; then
    # RHEL/CentOS
    yum install -y \
        mysql-devel \
        python3-devel \
        python3-pip
fi

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
