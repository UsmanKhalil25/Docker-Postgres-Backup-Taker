import sys
import subprocess
from enum import Enum, auto

class DockerState(Enum):
    RUNNING = auto()
    NOT_RUNNING = auto()
    NOT_INSTALLED = auto()

def display_error(message):
    # ANSI escape code for red foreground
    print(f"\033[31mError:\033[0m", end=" ")
    print(message)

def display_success(message):
    # ANSI escape code for green foreground
    print(f"\033[32mSuccess:\033[0m", end=" ")
    print(message)

def get_docker_status():
    try:
        result = subprocess.run(["docker", "info"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            return DockerState.RUNNING
        else:
            return DockerState.NOT_RUNNING
    except FileNotFoundError:
        return DockerState.NOT_INSTALLED

def handle_docker_status(docker_state):
    if docker_state == DockerState.NOT_INSTALLED:
        display_error("Docker is not installed")
        sys.exit(1)
    elif docker_state == DockerState.NOT_RUNNING:
        display_error("Docker is not running")
        sys.exit(1)
    else:
        display_success("Docker is running")

        
def main():
    docker_state = get_docker_status()
    handle_docker_status(docker_state)

if __name__ == "__main__":
    main()
