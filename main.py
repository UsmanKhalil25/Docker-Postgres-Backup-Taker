import re
import sys
import subprocess
from enum import Enum, auto
import datetime

# Regex pattern to match Docker container listing headers
DOCKER_CONTAINER_PATTERN = r"CONTAINER ID|IMAGE|COMMAND|CREATED|STATUS|PORTS|NAMES"

class DockerState(Enum):
    RUNNING = auto()
    NOT_RUNNING = auto()
    NOT_INSTALLED = auto()

def display_error(message: str):
    """Display an error message in red."""
    print(f"\033[31mError:\033[0m {message}")

def display_success(message: str):
    """Display a success message in green."""
    print(f"\033[32mSuccess:\033[0m {message}")

def get_docker_status() -> DockerState:
    """Check the status of the Docker daemon.

    Returns:
        DockerState: The current state of Docker (running, not running, or not installed).
    """
    print("Checking Docker status...")
    try:
        result = subprocess.run(["docker", "info"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            return DockerState.RUNNING
        else:
            return DockerState.NOT_RUNNING
    except FileNotFoundError:
        return DockerState.NOT_INSTALLED

def handle_docker_status(docker_state: DockerState) -> None:
    """Handle the Docker status and display appropriate messages.

    Args:
        docker_state (DockerState): The state of Docker to handle.
    """
    if docker_state == DockerState.NOT_INSTALLED:
        display_error("Docker is not installed or not found in PATH.")
        sys.exit(1)
    elif docker_state == DockerState.NOT_RUNNING:
        display_error("Docker is not running")
        sys.exit(1)
    else:
        display_success("Docker is running")

def remove_docker_listing_headers(output: str) -> str:
    """Remove header from the Docker ps output.

    Args:
        output (str): The raw output from the Docker ps command.

    Returns:
        str: The cleaned output without headers.
    """
    return re.sub(DOCKER_CONTAINER_PATTERN, "", output, flags=re.MULTILINE).strip()

def get_container_names(docker_ps_output: str) -> list[str]:
    """Extract container names from the Docker ps output.

    Args:
        docker_ps_output (str): The output from the Docker ps command.

    Returns:
        list[str]: A list of valid container names.
    """
    container_names = re.findall(r'[^ ]*$', docker_ps_output, re.MULTILINE)
    valid_container_names = [name for name in container_names if name]
    return valid_container_names

def get_docker_containers() -> list[str]:
    """Get a list of running Docker container names.

    Returns:
        list[str]: A list of names of running Docker containers.
    """
    try:
        result = subprocess.run(
            ["docker", "ps"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        
        output = result.stdout.decode()
        clean_output = remove_docker_listing_headers(output)
        container_names = get_container_names(clean_output)
        
        return container_names  

    except subprocess.CalledProcessError:
        display_error("Unable to list running containers.")
        sys.exit(1)
    except FileNotFoundError:
        display_error("Docker is not installed or not found in PATH.")
        sys.exit(1)

def display_containers(containers: list[str]):
    """Display a list of Docker containers for selection.

    Args:
        containers (list[str]): A list of Docker container names.
    """
    print("Select a Docker container:")
    print("\n")
    for index, container in enumerate(containers):
        print(f"{index + 1}: {container}")
    print("\n")

def select_container(containers: list[str]) -> str:
    """Prompt the user to select a Docker container from the list.

    Args:
        containers (list[str]): A list of Docker container names.

    Returns:
        str: The name of the selected container.
    """
    while True:
        display_containers(containers)
        try:
            selection = int(input("Enter the number of the container you want to select (0 to cancel): ")) - 1
            if selection == -1:
                print("Selection cancelled.")
                sys.exit(0)
            if 0 <= selection < len(containers):
                return containers[selection]
            else:
                display_error("Invalid selection. Please try again.")
        except ValueError:
            display_error("Please enter a valid number.")

def take_backup(container_name: str):
    """Take a backup of the specified Docker container's database.

    Args:
        container_name (str): The name of the Docker container to back up.

    Raises:
        SystemExit: Exits if there is an error during the backup process.
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
        dump_file_name = f"dump_{timestamp}.sql"

        result = subprocess.run(
            ["docker", "exec", "-t", container_name, "pg_dumpall", "-c", "-U", "postgres"],
            stdout=open(dump_file_name, 'w'),
            stderr=subprocess.PIPE,
            check=True
        )

        display_success(f"Backup taken successfully: {dump_file_name}")

    except subprocess.CalledProcessError as e:
        display_error("Unable to take backup: " + e.stderr.decode())
        sys.exit(1)
    except FileNotFoundError:
        display_error("Docker is not installed or not found in PATH.")
        sys.exit(1)

def main():
    docker_state = get_docker_status()
    handle_docker_status(docker_state)

    containers = get_docker_containers()
    if len(containers) == 0:
        display_error("No Docker container is running")
        sys.exit(1)

    selected_container = select_container(containers)
    display_success(f"You selected: {selected_container}")

    take_backup(selected_container) 

if __name__ == "__main__":
    main()
