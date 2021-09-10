from fabric import task

IMAGE = "exhuma/weathermonitor"


@task(help={"repo": "The domain-name of the docker registry to push to"})
def build(ctx, repo):
    version = ctx.run("python3 setup.py --version").stdout.strip()
    ctx.run(
        f"docker build -t {repo}/{IMAGE}:v{version} -t {repo}/{IMAGE}:latest .",
        pty=True,
    )


@task(help={"repo": "The domain-name of the docker registry to push to"})
def publish(ctx, repo):
    repo, _, _ = IMAGE.partition("/")
    version = ctx.run("python3 setup.py --version").stdout.strip()
    ctx.run(f"docker login {repo}", pty=True)
    ctx.run(f"docker push {repo}/{IMAGE}:latest", pty=True)
    ctx.run(f"docker push {repo}/{IMAGE}:v{version}", pty=True)
