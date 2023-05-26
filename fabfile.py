from fabric import task
from os.path import basename
from glob import glob

IMAGE = "weathermonitor"


@task(help={"repo": "The domain-name of the docker registry to push to"})
def build(ctx, repo=""):
    repo = repo or ctx["docker"]["registry"]
    version = ctx.run("python3 setup.py --version").stdout.strip()
    ctx.run("rm -rf dist")
    ctx.run("python3 setup.py bdist_wheel", hide="stdout").stdout.strip()
    files = glob("dist/*.whl")
    distfile = basename(files[0])
    ctx.run(
        (
            "docker build "
            f"--build-arg DISTFILE={distfile} "
            f"-t {repo}/{IMAGE}:v{version} "
            f"-t {repo}/{IMAGE}:latest ."
        ),
        pty=True,
    )


@task(help={"repo": "The domain-name of the docker registry to push to"})
def publish(ctx, repo=""):
    repo = repo or ctx["docker"]["registry"]
    version = ctx.run("python3 setup.py --version").stdout.strip()
    ctx.run(f"docker login {repo}", pty=True)
    try:
        ctx.run(f"docker push {repo}/{IMAGE}:latest", pty=True)
        ctx.run(f"docker push {repo}/{IMAGE}:v{version}", pty=True)
    finally:
        ctx.run(f"docker logout {repo}", pty=True)
