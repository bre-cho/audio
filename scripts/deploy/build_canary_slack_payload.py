import json, os

run_url = f"{os.getenv('GITHUB_SERVER_URL','https://github.com')}/{os.getenv('GITHUB_REPOSITORY','repo')}/actions/runs/{os.getenv('GITHUB_RUN_ID','') }"
workflow = os.getenv('GITHUB_WORKFLOW', 'audio-canary-deploy')
ref = os.getenv('GITHUB_REF_NAME', '')
target_env = os.getenv('TARGET_ENV', 'production')
canary = os.getenv('CANARY_BASE_URL', '')
text = (
    f":rotating_light: {workflow} failed\n"
    f"env: {target_env}\n"
    f"ref: {ref}\n"
    f"canary: {canary or 'n/a'}\n"
    f"run: {run_url}"
)
print(json.dumps({"text": text}))
