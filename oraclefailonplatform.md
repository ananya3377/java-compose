Oracle Solution failed on platform but passes locally.

Solution :

This is simply due to differences between their local environment and our on platform sandbox.

Some ways to troubleshoot:

1. Identify the Platform CI Log Error
Check the platform build logs to see the exact error message or if it fails on reward.txt not found.

2. Verify Common Platform Root Causes
The most common reasons for platform-only failures are:

Blocking Entrypoint (Most Common):If yourentrypoint.shends with a blocking service command likeexec nginx -g 'daemon off;'or similar background daemons, it prevents the platform's test script from executing.
Fix:Ensure your entrypoint script finishes withexec "$@"to hand over control to the verifier.

set -e in test.sh exiting early:If any command intest.shfails before reaching the echo statement,set -eorset -euo pipefailwill terminate the script instantly, preventing it from writingreward.txt.
Fix:Useset -uo pipefailand capture exit statuses (e.g., runningpytest ... && rc=0 || rc=$?) sotest.shis guaranteed to write either1or0to/logs/verifier/reward.txt.

Missing Output Directory:The test runner needs to write to/logs/verifier/reward.txt.
Fix:Addmkdir -p /logs/verifiernear the top of yourtest.sh.

Network Requests at Runtime:The platform blocks all internet access during verification (allow_internet = false). If yourtest.shor tests try to pull packages viapip install,wget,curl, or clone from Git, they will fail on the platform.
Fix:Pre-install and pin all dependencies directly inside the Dockerfile.

Relative Paths / Environment Variables:Differences in working directories or shell environment variables can break relative paths.
Fix:Use absolute paths everywhere (e.g.,/app/config/settings.jsoninstead ofconfig/settings.json).



3. Debug Locally with Platform Conditions
To replicate the platform CI environment locally:

Rundocker network pruneto clear out stale networks.
Ensure you are running the exact CLI commands:
bash
# Test the oracle
harbor run -a oracle -p <task-folder>
# Run quality checks
harbor tasks check -m openai/@openai/gpt-5.2 harbor_tasks/<task_name>
Start the environment interactively (harbor tasks start-env -p <task-folder> -i) to inspect the path structures and test execution behavior in real-time.


4. Download Platform Feedback & Logs

Method 1: Using the stb CLI (Recommended)
1. Get the Submission ID: List your submissions for the project to find the target SUBMISSION_ID:
bash
stb submissions list -p PROJECT_ID
(Note: You can add --show-folder-names to map the IDs back to your local folder names).
2. Download Feedback & Logs: Run the following command to download the latest automated check results (including test outputs, error logs, and reviewer comments) directly to your machine:
bash
stb submissions feedback SUBMISSION_ID
3. Open the Platform View: Alternatively, you can open the specific submission page directly in your default browser to view the live checks/logs:
bash
stb submissions view SUBMISSION_ID


Suggestion for failing Oracle test.

The submission needs to avoid exec /solution/foo.sh, instead, use bash /solution/foo.sh . This is because the verifier-side /solution mount is nonexec . Use bash instead of exec when calling anything inside /solution.

We strongly recommend using the STB-CLI to download feedback for any failures, and using stb claude to analyze the logs and suggest fixes.
