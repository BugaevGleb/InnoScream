# InnoScream

Anonymous Stress Relief Platform for Students

## Table of Contents

- [Negotiation on the Project](#negotiation-on-the-project)
- [Project Functionality and Usage](#project-functionality-and-usage)
- [Quality Metrics](#quality-metrics)
- [Tasks Distribution](#tasks-distribution)
- [Lessons Learned](#lessons-learned)

## Negotiation on the Project

During the first week of the work on this project we discussed all features and metrics and agreed on the following clarifications and changes to the initial task statement:

1. Memes generation will take at the end of day for the post with maximum number of reactions (among posts published during the current day).
2. Instead of using ImgFlip API for creating memes with top-voted post text we will use Unsplash API to find and download image related top-voted to post text. This decision was made since ImgFlip API can create memes with only predefined template (image).
3. Memes (once per day) along with statistics graph (once per week) will be published to the channel.
4. Admins can reply to particular post with text "/delete" to remove this post from the channel.
5. There is no 💀 emoji in usual (not premium) telegram channels, so we replaced it with 😭 emoji.
6. "No critical vulnerabilities (Bandit)" from the task statement means no HIGH severity-level vulnerabilities detected by Bandit.

## Getting Started

Aт overview of how to set up the project locally for development and testing.

1. **Clone the Repository:**  
   ```bash
   git clone https://github.com/BugaevGleb/InnoScream.git
   cd InnoScream
   ```

2. **Install Poetry:**  
   ```bash
   pip install poetry
   ```

3. **Install Dependencies:**  
   ```bash
   poetry install
   ```

4. **Create .env file:**  
   Create `.env` file at the root of the repository and fulfill all variables from `.env.example` with your values (token of your telegram bot, ID of your telegram channel, your Unsplash access key, and so on).

5. **Run Telegram Bot (first shell):**  
   ```bash
   poetry run python -m app.bot.main
   ```

6. **Run API (second shell):**  
   ```bash
   poetry run fastapi run app/api/main.py
   ```

## Project Functionality and Usage

A summary of the key features offered by the project and its usage.

- **Sending anonymous messages:**  
  Students can write their messages to the telegram bot and these messages will be anonymously posted in InnoScream channel. To post a message, student should send `/scream <message>` to the bot.

- **Reactions:**  
  Students can view all anonymous posts in InnoScream channel and put reactions (😭/🔥/🤡) to them.

- **Pinning most-voted (most-reacted) posts:**  
  At the end of the day a system automatically find a post with greatest number of reactions and pin it. Also, admins can send `/pin` command to the bot and this functionality will be triggered immediately.

- **Generating memes:**  
  At the end of the day a system automatically find a post with greatest number of reactions and create a meme with its text and auto-found background image (by free Unsplash service API). This meme posted to the channel along with all anonymous posts. Also, admins can send `/generate_meme` command to the bot and this functionality will be triggered immediately.

- **Individual statistics:**  
  Student can send `/stats` command to the bot and get a number of anonymous messages sent by him/her.

- **Weekly stress graphs:**  
  At the end of the week a system collects info about all posts sent during the past week and generates (by QuickChart.io API) a stress graph (how many anonymous posts were sent by the students in each day of the week).

- **Posts moderation:**  
  Admins can reply on a post with `/delete` command in a channel and this post (along with `/delete` message) will be deleted from the channel.

## Quality Metrics

This is a description of all required quality metrics (project treshold, our result, and how to measured/test it):

- **Code style:**  
  *Tool:* Flake8  
  *Treshold:* Zero warnings  
  *Our result:* Zero warnings  
  *How we measured it:* Using Flake8 in pre-commit hook and CI  

- **Documentation:**  
  *Tool:* Pydocstyle  
  *Treshold:* Docstrings for all functions  
  *Our result:* Docstrings for all functions  
  *How we measured it:* Using Pydocstyle in pre-commit hook and CI  

- **Code complexity:**  
  *Tool:* Radon cc  
  *Treshold:* Code complexity ≤ 10  
  *Our result:* Max code complexity is 9  
  *How we measured it:* Using Radon in pre-commit hook and CI  

- **Test coverage:**  
  *Tool:* Pytest  
  *Treshold:* Test coverage ≥ 60%  
  *Our result:* Line coverage is 61%, Branch coverage is 61%, Total coverage (from pytest) is 61.22%  
  *How we measured it:* Using `poetry run pytest --cov=app --cov-report=term-missing` and `poetry run pytest --cov=app --cov-report=term-missing --cov-branch` command and `poetry run pytest --cov=app --cov-fail-under=60` step in GitHub Actions.  

- **Mutation testing:**  
  *Tool:* Mutmut  
  *Treshold:* ≥ 80% mutants killed  
  *Our result:* 84% mutants killed  
  *How we measured it:* We created setup.cfg for mutmut and ran commands `poetry run mutmut run` and `poetry run mutmut browse`.  

- **Bot response time:**  
  *Tool:* Locust  
  *Treshold:* Bot response time ≤ 500 ms under 100 RPS
  *Our result:* ([See Locust Results](locust_result.html))

  *How we measured it:* We executed the Locust performance test defined in [`locustfile.py`](locustfile.py), simulating 100 concurrent users to achieve a load of approximately 100 requests per second (RPS) targeting the `POST /user_messages` API endpoint. **This simulates the API load generated when users execute the `/scream` command in the bot.**

- **SQL queries time:**  
  *Tool:* Python  
  *Treshold:* SQL queries ≤ 50 ms  
  *Our result:* 0.336 ms at most  
  *How we measured it:* We fulfilled a database with 300 messages and 300 reactions (approved size by our project master) using [this script](https://github.com/BugaevGleb/InnoScream/blob/main/scripts/dummy_db_data_generator.py). Then we measured all presented in the project SQL queries using [this script](https://github.com/BugaevGleb/InnoScream/blob/main/scripts/db_query_time_analysis.py). These are obtained results:  
    - get_user_message_by_message_id  
    Average time for 1000 queries: 0.195 milliseconds

    - get_best_message  
    Average time for 1000 queries: 0.333 milliseconds

    - get_reaction_by_message_id  
    Average time for 1000 queries: 0.219 milliseconds

    - get_count_of_messages_by_date  
    Average time for 1000 queries: 0.323 milliseconds

    - get_all_time_daily_stats  
    Average time for 1000 queries: 0.336 milliseconds

    - get_user_stats  
    Average time for 1000 queries: 0.256 milliseconds

  System configuration:  
    - CPU: Intel Core i7-13620H
    - RAM: 16 GB
    - SSD: NVMe SAMSUNG MZVMA1T0HCLD-00BTW

  *Note:* Initially by the project description EXPLAIN ANALYZE command was supposed to be used, but we found that SQLite has no such command. So, we decided (and got an approval from our project master) to measure it from Python module.

- **Vulnerabilities:**  
  *Tool:* Bandit  
  *Treshold:* No critical vulnerabilities  
  *Our result:* No critical vulnerabilities (with HIGH severity-level by Bandit)  
  *How we measured it:* Using Bandit in pre-commit hook and CI, configured on failing pipeline if HIGH severity-level vulnerabilities found  

- **Data anonymity:**  
  *Tool:* Bandit / Manual review  
  *Treshold:* user_id hashing  
  *Our result:* user_id hashing using sha256  
  *How we measured it:* Using Bandit in pre-commit hook and CI + Manual review (using hashlib.sha256)  

## Tasks Distribution

During the project we strived to divide tasks equally among all 5 team members, so each team member contributed at least one feature to the project and made at least one quality metric measurement (or wrote tests). This is a distribution of tasks among team members:

- **Dmitriy Okoneshnikov:**  
  Base bot and api functionality (messages sending, reactions, database connection), automated quality gates (GitHub Actions), pre-commit hook (to preserve code style using flake8+pydocstyle, security using bandit and complexity using radon cc).

- **Gleb Bugaev:**  
  Team lead, meme generation feature, unit tests (pytest), quality and functionalities report.

- **Milana Sirozhova:**  
  Pinning most-reacted message feature, sql queries time measuring, project presentation.

- **Nail Minnenullin:**  
  Posts deletion (by admins) feature, unit tests (mutmut).

- **Vladislav Bolshakov:**  
  Statistics and weekly stress graph features, performance measuring (locust).

## Lessons Learned

During the process of project work we learned several new insides:

- **Mutmut:**  
  While using mutmut testing with python async functions in bot main.py we faced up segfaults of many mutants. To fix it we wrote precise mutmut version in pyproject.toml file (3.2.3) and wrote "no mutate" comment to all lines which cause segfaults (for example: logger, calling C language functions, and so on).

- **Tasks Dependencies:**  
  We faced up with a problem of tasks dependencies (for example, meme generation feature can be done only after most-reacted message finding feature) and different team members work schedule. To neglect this problem we met online each week and defined deadlines for each feature/activity.

- **SQLite queries testing:**  
  Initially we were intended to measure SQL queries execution time with EXPLAIN ANALYZE. However, during the testing stage of the project work we found out that SQLite has no EXPLAIN ANALYZE at all (according to its documentation). Therefore, we agreed with our project master to measure queries time using Python `timeit` library.

- **Performance Testing Approach:**
  Directly simulating hundreds of real Telegram accounts interacting with the bot for performance testing is impractical due to limitations and complexity. Therefore, we opted to test the backend API endpoint (`POST /user_messages`) directly using Locust. This approach effectively simulates the *load* generated by the target number of users (100 RPS for the `/scream` command) on the critical API component, allowing us to measure its response time under stress and verify the performance requirement.
