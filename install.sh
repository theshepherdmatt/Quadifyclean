#!/bin/bash
set -e

# ============================
#   Color Code Definitions
# ============================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# ============================
#   ASCII Art Banner Function
# ============================
banner() {
    echo -e "${MAGENTA}"
    echo "  ___  _   _   _    ____ ___ _______   __"
    echo " / _ \| | | | / \  |  _ \_ _|  ___\ \ / /"
    echo "| | | | | | |/ _ \ | | | | || |_   \ V / "
    echo "| |_| | |_| / ___ \| |_| | ||  _|   | |  "
    echo " \__\_\\___/_/   \_\____/___|_|     |_|  "
    echo -e "${NC}"
}

# ============================
#   Log Message Function
# ============================
log_message() {
    local type="$1"
    local message="$2"
    case "$type" in
        "info") echo -e "${BLUE}[INFO]${NC} $message" ;;
        "success") echo -e "${GREEN}[SUCCESS]${NC} $message" ;;
        "warning") echo -e "${YELLOW}[WARNING]${NC} $message" ;;
        "error") echo -e "${RED}[ERROR]${NC} $message" >&2 ;;
    esac
}

# ============================
#   Check for Root Privileges
# ============================
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_message "error" "Please run as root or use sudo."
        exit 1
    fi
}

# ============================
#   Install System-Level Dependencies
# ============================
install_system_dependencies() {
    log_message "info" "Installing system-level dependencies..."

    # Update package lists
    apt-get update

    # Install essential packages
    apt-get install -y \
        python3.10 \
        python3.10-venv \
        python3.10-dev \
        python3-pip \
        libjpeg-dev \
        zlib1g-dev \
        libfreetype6-dev \
        i2c-tools \
        python3-smbus \
        libgirepository1.0-dev \
        pkg-config \
        libcairo2-dev \
        libffi-dev \
        build-essential \
        libxml2-dev \
        libxslt1-dev \
        libssl-dev

    log_message "success" "System-level dependencies installed successfully."
}

# ============================
#   Create and Activate Virtual Environment
# ============================
setup_virtualenv() {
    log_message "info" "Setting up Python virtual environment..."

    # Navigate to project directory
    cd ~/Quadifyclean/

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3.10 -m venv venv
        log_message "success" "Virtual environment created."
    else
        log_message "info" "Virtual environment already exists."
    fi

    # Activate virtual environment
    source venv/bin/activate
    log_message "success" "Virtual environment activated."
}

# ============================
#   Upgrade pip, setuptools, and wheel
# ============================
upgrade_pip() {
    log_message "info" "Upgrading pip, setuptools, and wheel..."
    pip install --upgrade pip setuptools wheel
    log_message "success" "pip, setuptools, and wheel upgraded."
}

# ============================
#   Install Python Dependencies
# ============================
install_python_dependencies() {
    log_message "info" "Installing Python dependencies..."

    # Install dependencies from requirements.txt
    pip install -r ~/Quadifyclean/requirements.txt

    log_message "success" "Python dependencies installed successfully."
}

# ============================
#   Enable I2C and SPI in config.txt
# ============================
enable_i2c_spi() {
    log_message "info" "Enabling I2C and SPI in config.txt..."

    CONFIG_FILE="/boot/config.txt"

    # Enable SPI
    if ! grep -q "^dtparam=spi=on" "$CONFIG_FILE"; then
        echo "dtparam=spi=on" >> "$CONFIG_FILE"
        log_message "success" "SPI enabled."
    else
        log_message "info" "SPI is already enabled."
    fi

    # Enable I2C
    if ! grep -q "^dtparam=i2c_arm=on" "$CONFIG_FILE"; then
        echo "dtparam=i2c_arm=on" >> "$CONFIG_FILE"
        log_message "success" "I2C enabled."
    else
        log_message "info" "I2C is already enabled."
    fi

    log_message "success" "I2C and SPI enabled in config.txt."
}

# ============================
#   Detect MCP23017 I2C Address
# ============================
detect_i2c_address() {
    log_message "info" "Detecting MCP23017 I2C address..."

    # Use i2cdetect to find MCP23017 (common addresses: 0x20 - 0x27)
    address=$(i2cdetect -y 1 | grep -E '20|21|22|23|24|25|26|27' | awk '{print $1}' | head -n 1)

    if [[ -z "$address" ]]; then
        log_message "warning" "MCP23017 not found. Check wiring and connections as per instructions on our website."
    else
        log_message "success" "Detected MCP23017 at I2C address: 0x$address."
        update_buttonsleds_address "$address"
    fi
}

# ============================
#   Update MCP23017 Address in buttonsleds.py
# ============================
update_buttonsleds_address() {
    local detected_address="$1"
    BUTTONSLEDS_FILE="/home/volumio/Quadify/buttonsleds.py"

    if [[ -f "$BUTTONSLEDS_FILE" ]]; then
        sed -i "s/MCP23017_ADDRESS = 0x[0-9a-fA-F][0-9a-fA-F]/MCP23017_ADDRESS = 0x$detected_address/" "$BUTTONSLEDS_FILE"
        log_message "success" "Updated MCP23017 address in buttonsleds.py to 0x$detected_address."
    else
        log_message "error" "buttonsleds.py not found at $BUTTONSLEDS_FILE. Ensure the path is correct."
        exit 1
    fi
}

# ============================
#   Configure Systemd Service
# ============================
setup_main_service() {
    log_message "info" "Setting up the Main Quadify Service..."

    SERVICE_FILE="/etc/systemd/system/quadify.service"

    tee "$SERVICE_FILE" > /dev/null <<EOL
[Unit]
Description=Quadify Main Service
After=network.target

[Service]
ExecStart=/home/volumio/Quadifyclean/venv/bin/python3 /home/volumio/Quadifyclean/src/main.py
Restart=always
User=volumio
WorkingDirectory=/home/volumio/Quadifyclean/
Environment=PATH=/home/volumio/Quadifyclean/venv/bin
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOL

    # Reload systemd daemon to recognize the new service
    systemctl daemon-reload

    # Enable and start the service
    systemctl enable quadify.service
    systemctl start quadify.service

    log_message "success" "Main Quadify Service has been created, enabled, and started."
}

# ============================
#   Main Installation Function
# ============================
main() {
    banner
    check_root
    install_system_dependencies
    enable_i2c_spi
    setup_virtualenv
    upgrade_pip
    install_python_dependencies
    detect_i2c_address
    setup_main_service
    log_message "success" "Installation complete. Please reboot to apply hardware settings if necessary."
}

# Execute the main function
main
