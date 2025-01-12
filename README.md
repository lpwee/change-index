# NTU STARS Index Change Script

This script automates the index change process for NTU STARS using Selenium WebDriver.

## Setup

1. Set up the conda environment:
```bash
conda create
conda activate change-index
```
Ensure environment is activated, check for `(change-index)` in terminal.

2. Create a `.env` file:
   - Copy `.env.example` to `.env`
   - Fill in your :
      - NTU username
      - password
      - old index no.
      - desired index no.

## Usage

Run the script:
```bash
python change_index.py
```

The script will:
1. Launch a Chrome browser
2. Navigate to the NTU STARS Planner login page
3. Automatically fill in your credentials
4. Submit the login form
5. Upon successful login, request to swap to desired index
6. Continuously try until index has been swapped.

