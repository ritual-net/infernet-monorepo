import json
import os
import subprocess

import click


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Helper function to run shell commands."""
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,  # Suppress standard output
        stderr=subprocess.PIPE,  # Suppress standard error
        text=True,  # Get the output as text
    )


def docker_start(dir: str) -> None:
    """Start the containers."""
    try:
        # Run the docker compose command without showing the output
        result = run_command(
            ["docker", "compose", "-f", f"{dir}/docker-compose.yaml", "up", "-d"]
        )

        # Check if the command was successful
        if result.returncode == 0:
            click.echo("Containers started successfully.")
        else:
            click.echo(f"Failed to start containers. Error: {result.stderr}")

    except Exception as e:
        click.echo(f"An error occurred: {e}")


def docker_stop(dir: str) -> None:
    """Stop the containers."""
    try:
        # Run the docker compose command without showing the output
        result = run_command(
            ["docker", "compose", "-f", f"{dir}/docker-compose.yaml", "stop"],
        )

        # Check if the command was successful
        if result.returncode == 0:
            click.echo("Containers stopped successfully.")
        else:
            click.echo(f"Failed to stop containers. Error: {result.stderr}")

    except Exception as e:
        click.echo(f"An error occurred while stopping containers: {e}")


def docker_destroy(dir: str) -> None:
    """Destroy the containers."""
    try:
        # Run the docker compose command without showing the output
        result = run_command(
            ["docker", "compose", "-f", f"{dir}/docker-compose.yaml", "rm", "-f"],
        )

        # Check if the command was successful
        if result.returncode == 0:
            click.echo("Containers destroyed successfully.")
        else:
            click.echo(f"Failed to destroy containers. Error: {result.stderr}")

    except Exception as e:
        click.echo(f"An error occurred while destroying containers: {e}")


def health_check(dir: str) -> None:
    """Check if all containers are up and healthy."""
    try:
        # Run `docker compose ps` to get the status of the containers
        result = run_command(
            [
                "docker",
                "compose",
                "-f",
                f"{dir}/docker-compose.yaml",
                "ps",
                "-a",
                "--format",
                "json",
            ],
        )
        # Parse the result as JSON to inspect each container
        containers = ",".join(result.stdout.split("\n")[:-1])
        containers_obj = json.loads(f"[{containers}]")

        if len(containers_obj) == 0:
            click.echo("No containers found.")
            return

        # Check if the command was successful
        if result.returncode != 0:
            click.echo(f"Failed to get the container status. Error: {result.stderr}")
            return

        # Check if all containers are up and healthy
        all_healthy = True
        for container in containers_obj:
            name = container["Service"]
            status = container["State"]  # State includes "running", "exited", etc.

            # Simply check if the container is running
            if status != "running":
                click.echo(f"Container {name} is not running. Status: {status}.")
                all_healthy = False

        if all_healthy:
            click.echo("\033[92mAll containers are up and running.\033[0m")
        else:
            click.echo("\033[91mSome containers are not running.\033[0m")

    except Exception as e:
        click.echo(f"An error occurred while checking container health: {e}")


def destroy_services(dir: str) -> None:
    """Stop and remove all service containers found in the config file."""

    if not os.path.exists(f"{dir}/config.json"):
        raise click.ClickException(f"{dir}/config.json not found.")

    # Read container IDs from config.json
    config = json.load(open(f"{dir}/config.json"))
    container_ids = [container["id"] for container in config["containers"]]

    # Force stop and remove containers
    for container_id in container_ids:
        # Stop and remove the container
        run_command(["docker", "stop", container_id])
        run_command(["docker", "rm", container_id])
