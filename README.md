# NTU STARS Planner Login Script

This script automates the login process for NTU STARS Planner using Selenium WebDriver.

## Setup

1. Set up the conda environment:
```bash
conda create -n change-index python=3.10 selenium python-dotenv
conda activate change-index
```

2. Install Chrome WebDriver:
   - Download ChromeDriver from https://sites.google.com/chromium.org/driver/
   - Make sure the ChromeDriver version matches your Chrome browser version
   - Add ChromeDriver to your system PATH

3. Create a `.env` file:
   - Copy `.env.example` to `.env`
   - Fill in your NTU username and password

## Usage

Run the script:
```bash
python ntu_login.py
```

The script will:
1. Launch a Chrome browser
2. Navigate to the NTU STARS Planner login page
3. Automatically fill in your credentials
4. Submit the login form
5. Close the browser after a successful login

## Security Note

- Never commit your `.env` file containing your credentials
- Keep your credentials secure and don't share them
- The script uses environment variables to keep credentials out of the code
