"""Home-directory seed data for the Playwright workspace fixtures."""

HOME_FILES = {
    ".ssh/id_rsa": "EXTRACE_FAKE_OPENSSH_KEY\n"
    "owner=dev@extrace.io\n"
    "algorithm=ssh-ed25519\n"
    "material=this-is-a-canary-not-a-real-private-key\n"
    "EXTRACE_FAKE_OPENSSH_KEY_END\n",
    ".ssh/id_rsa.pub": "ssh-ed25519 "
    "AAAAC3NzaC1lZDI1NTE5AAAAIGYUMpVscUadF0F9L0Ktni0psx1Vo2sYwfl/Eo84duRA "
    "dev@extrace.io\n",
    ".ssh/config": "Host github.com\n"
    "    HostName github.com\n"
    "    User git\n"
    "    IdentityFile ~/.ssh/id_rsa\n"
    "\n"
    "Host production-server\n"
    "    HostName 10.0.1.50\n"
    "    User deploy\n"
    "    IdentityFile ~/.ssh/id_rsa\n"
    "    Port 2222\n",
    ".ssh/known_hosts": "github.com ssh-ed25519 "
    "AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl\n",
    ".aws/credentials": "[default]\n"
    "aws_access_key_id = AKIAIOSFODNN7EXTRACE\n"
    "aws_secret_access_key = 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\n"
    "\n"
    "[production]\n"
    "aws_access_key_id = AKIAI44QH8DHBEXTRACE\n"
    "aws_secret_access_key = je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXTRACEKEY\n",
    ".aws/config": "[default]\n"
    "region = eu-west-1\n"
    "output = json\n"
    "\n"
    "[profile production]\n"
    "region = us-east-1\n"
    "output = json\n",
    ".kube/config": "apiVersion: v1\n"
    "kind: Config\n"
    "clusters:\n"
    "- cluster:\n"
    "    server: https://k8s.extrace-internal.io:6443\n"
    "    certificate-authority-data: LS0tLS1CRUdJTi...FURS0tLS0t\n"
    "  name: production\n"
    "contexts:\n"
    "- context:\n"
    "    cluster: production\n"
    "    user: admin\n"
    "    namespace: default\n"
    "  name: production\n"
    "current-context: production\n"
    "users:\n"
    "- name: admin\n"
    "  user:\n"
    "    token: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.extrace-fake-token\n",
    ".docker/config.json": "{\n"
    '  "auths": {\n'
    '    "ghcr.io": {\n'
    '      "auth": "ZXh0cmFjZTpnaHBfZmFrZVRva2VuRm9ySG9uZXlwb3RUZXN0"\n'
    "    },\n"
    '    "registry.extrace.io": {\n'
    '      "auth": "ZGVwbG95OmV4dHJhY2Utc2VjcmV0LXJlZ2lzdHJ5LXBhc3M="\n'
    "    }\n"
    "  }\n"
    "}\n",
    ".config/gcloud/application_default_credentials.json": "{\n"
    '  "client_id": '
    '"764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com",\n'
    '  "client_secret": '
    '"d-FL95Q19q7MQmFpd7hHD0Ty",\n'
    '  "refresh_token": '
    '"1//0extrace-fake-refresh-token-for-honeypot",\n'
    '  "type": "authorized_user"\n'
    "}\n",
    ".npmrc": "//registry.npmjs.org/:_authToken=npm_fakeTokenExtraceHoneypot1234567890\n"
    "//npm.pkg.github.com/:_authToken=ghp_fakeGitHubPATforExtraceHoneypot99\n"
    "registry=https://registry.npmjs.org/\n",
    ".gitconfig": "[user]\n"
    "    name = Ahmet Yilmaz\n"
    "    email = ahmet.yilmaz@extrace.io\n"
    "[credential]\n"
    "    helper = store\n"
    "[core]\n"
    "    editor = code --wait\n",
    ".git-credentials": "https://ahmet-yilmaz:ghp_R8nFakePatTokenExtrace7890123456@github.com\n",
    ".bash_history": "ssh deploy@10.0.1.50\n"
    "docker login ghcr.io -u extrace -p ghp_fakeTokenExtrace123\n"
    "export "
    "DATABASE_URL=postgresql://admin:s3cretPa55w0rd@db.extrace.io:5432/production\n"
    "kubectl get secrets -n production\n"
    "aws s3 ls s3://extrace-backups/\n"
    'curl -H "Authorization: Bearer sk-proj-fakeOpenAIkeyExtrace123456" '
    "https://api.openai.com/v1/models\n"
    "scp -i ~/.ssh/id_rsa backup.tar.gz deploy@10.0.1.50:/backups/\n"
    "mysql -h db.extrace.io -u root -p'Sup3rS3cret!' production\n"
    "redis-cli -h cache.extrace.io -a 'r3d1s_p@ss_extrace'\n"
    "STRIPE_SECRET_KEY=sk_live_fakeStripeKeyExtrace123 node server.js\n",
    ".python_history": "import os\n"
    "os.environ['DATABASE_URL']\n"
    "import boto3\n"
    "s3 = boto3.client('s3')\n"
    "s3.list_buckets()\n",
}
