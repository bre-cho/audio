import json, os

run_url = f"{os.getenv('GITHUB_SERVER_URL','https://github.com')}/{os.getenv('GITHUB_REPOSITORY','repo')}/actions/runs/{os.getenv('GITHUB_RUN_ID','') }"
workflow = os.getenv('GITHUB_WORKFLOW', 'audio-canary-deploy')
ref = os.getenv('GITHUB_REF_NAME', '')
target_env = os.getenv('TARGET_ENV', 'production')
canary = os.getenv('CANARY_BASE_URL', '')
text = (
    f":rotating_light: {workflow} that bai\n"
    f"moi truong: {target_env}\n"
    f"nhanh: {ref}\n"
    f"canary: {canary or 'khong co'}\n"
    f"lan chay: {run_url}"
)
print(json.dumps({"text": text}))
