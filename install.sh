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
NC='\033[0m'

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
#   Install Python Packages
# ============================
install_dependencies() {
    log_message "info" "Installing required Python libraries..."
    pip3 install luma.core==2.4.2 luma.oled==3.13.0 python-socketio==4.6.1 RPi.GPIO==0.7.0
    yes | pip3 uninstall websocket websocket-client || true
    pip3 install websocket-client==1.6.1
}


# ============================
#   Detect MCP23017 I2C Address
# ============================
detect_i2c_address() {
    log_message "info" "Detecting MCP23017 I2C address..."
    address=$(i2cdetect -y 1 | grep -o '^[0-9a-f][0-9a-f]')
    if [[ -z "$address" ]]; then
        log_message "warning" "MCP23017 not found. Check wiring and ensure connections are correct."
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
        sed -i "s/MCP23017_ADDRESS = 0x[0-9a-f][0-9a-f]/MCP23017_ADDRESS = 0x$detected_address/" "$BUTTONSLEDS_FILE"
        log_message "success" "Updated MCP23017 address in buttonsleds.py to 0x$detected_address."
    else
        log_message "error" "buttonsleds.py not found. Ensure the path is correct."
    fi
}

# ============================
#   Configure Systemd Service
# ============================
setup_main_service() {
    log_message "info" "Setting up the Main Quadify Service..."
    tee /etc/systemd/system/quadify.service > /dev/null <<EOL
[Unit]
Description=Quadify Main Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/volumio/Quadify/main.py
Restart=always
User=volumio
WorkingDirectory=/home/volumio/Quadify
Environment=PATH=/usr/bin:/usr/local/bin
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOL
    systemctl daemon-reload
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
    install_dependencies
    detect_i2c_address
    setup_main_service
    log_message "success" "Installation complete. Please reboot to apply hardware settings if necessary."
}

# Execute the main function
main
