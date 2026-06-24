# NTU STARS Automations

One interactive Selenium CLI uses the same STARS login from `.env` for two workflows:

- **STARS** retries an already-selected course-registration request until STARS accepts it.
- **Add/Drop** changes one or more registered indexes. Each `CURRENT_INDEX` value is paired with the `DESIRED_INDEX` value in the same position.

## Setup

1. Set up the virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
Ensure environment is activated, check for `(.venv)` in terminal.

2. Create a `.env` file:

   ```bash
   cp .env.example .env
   ```

   Set `NTU_USERNAME` and `NTU_PASSWORD`. Keep `.env` private; it is ignored by Git.

3. For index changes, set comma-separated, positional pairs:

   ```dotenv
   CURRENT_INDEX=12345,23456
   DESIRED_INDEX=67890,98765
   ```

   This changes `12345` to `67890`, then `23456` to `98765`. Both lists must contain the same number of values.

## Usage

```bash
python main.py
```

Choose one option when prompted:

- **1 — STARS:** First select the course(s) in STARS as usual. The CLI clicks `Add (Register) Selected Course(s)`, then `Confirm to add course(s)`. If STARS responds with `Not Added.`, it clicks `Back to Timetable` and tries again. When registration is not open, it closes the alert, returns to the logged-in timetable, and keeps waiting/retrying. If STARS reports that a page has expired, it signs in again and resumes the workflow.
- **2 — Add/Drop:** The CLI opens one browser per pair and retries every current→desired index change independently and simultaneously. Each browser signs in, selects its current registered index, selects STARS' Change Index action, chooses the paired desired index, and confirms the change.

### Optional controls

- Set `STARS_HEADLESS=true` to run Chrome without its visible window.
- Set `STARS_WAIT_SECONDS` to adjust the per-page wait (default: `3`).
- Set `STARS_ALERT_WAIT_SECONDS` to adjust how long STARS waits for a browser alert (default: `5`).
- Set `STARS_POLL_INTERVAL_SECONDS` to adjust how often STARS checks for page changes (default: `0.2`).
- Set `STARS_RETRY_DELAY_SECONDS` to pause between failed registration attempts.
- Set `ADD_DROP_RETRY_DELAY_SECONDS` and `ADD_DROP_MAX_ATTEMPTS` to control each concurrent Add/Drop browser; an attempt limit of `0` retries indefinitely.


Accepting alert:  You are not allowed to access more than 1 session of STARS/ !