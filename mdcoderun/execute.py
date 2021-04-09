
import docker
import re
import string
import random
import os

_client = None
_containers = {}

def get_client():
    global _client
    if _client is None:
        _client = docker.from_env()
    return _client

def get_container(image_name: str):
    global _containers
    if image_name not in _containers:
        client = get_client()
        _containers[image_name] = client.containers.run(image=image_name, detach=True, tty=True)
    return _containers[image_name]

def _merge_command_lines(command: str):
    "Merges command lines split by \\"
    return re.sub(r"\\\s*\n\s*", " ", command)

def _fix_initial_dollar(command: str):
    command = re.sub(r"^[$]\s+", "", command)
    return command

def _remove_no_prompt_lines(command_lines: str, prompt = "$ "):
    return "\n".join([l[len(prompt):] for l in command_lines.split("\n") if l.startswith(prompt)])
    

def _split_command_lines(command: str):
    "Splits commands written in a single code block"
    return command.split("\n")

def _prepare_command_script(commands: str, fix_initial_dollar=True, debug=False):
    commands = _merge_command_lines(commands)
    if fix_initial_dollar:
        if len(re.findall(r'^[$]\s+', commands, re.MULTILINE)) > 0:
            commands = _remove_no_prompt_lines(commands)

    if debug: 
        command_lines = commands.split("\n")
        new_commands = []
        for command in command_lines:
            cat_command = f"cat << MARKDOWNCOMMANDEOL\n### RUNNING ###\n{command}\nMARKDOWNCOMMANDEOL\n"
            new_commands.append(cat_command)
            new_commands.append(command)
        commands = "\n".join(new_commands)

    script_template = f"""/usr/bin/env bash 

{commands}
    """

    return script_template


def run_in_child_container(image_name: str, commands: str, fix_initial_dollar=True, debug=False):
    "Runs the commands in a new container derived from the given image"

    random_dirname = random.randint(10000, 99999)
    temp_dir = f"/tmp/markdown-runner-{random_dirname}"
    script_filename = "markdown-runner.sh"

    dockerfile_content = f"""FROM {image_name}

COPY {script_filename} /{script_filename}

CMD ["/{script_filename}"]
    """

    os.makedirs(temp_dir)

    script = _prepare_command_script(commands, fix_initial_dollar)
    if debug:
        print("#### SCRIPT TO RUN IN {image_name}")
        print(script)

    with open(f"{temp_dir}/{script_filename}", "w") as script_f:
        script_f.write(script)

    os.chmod(f"{temp_dir}/{script_filename}", 0o0755)

    with open(f"{temp_dir}/Dockerfile", "w") as docker_f:
        docker_f.write(dockerfile_content)

    if debug:
        print("### DOCKERFILE FOR CHILD CONTAINER")
        print(dockerfile_content)

    client = get_client()
    image, logs = client.images.build(path=temp_dir)
    if debug:
        print("### BUILD LOGS FOR THE CONTAINER")
        print("\n".join([str(l) for l in logs]))
    output = client.containers.run(image)
    return output.decode("utf-8")

def run_in_container(image_name: str, command: str, fix_initial_dollar=True, debug=False):
    container = get_container(image_name)
    command = _merge_command_lines(command)
    if fix_initial_dollar:
        command = _fix_initial_dollar(command)
    command_list = _split_command_lines(command)
    outputs = []
    exit_codes = []
    for cmd in command_list:
        if len(cmd.strip()) == 0:
            continue
        if debug:
            print(f"### Running ###\n{cmd}\n###############\n")
        (exit_code, output) = container.exec_run(cmd=cmd)
        if debug:
            print(f"### Exit Code: {exit_code}")
            print(f"### Output ###\n{output}\n############\n")
        exit_codes.append(exit_code)
        outputs.append(output.decode(encoding="utf-8"))

    return (exit_codes, "\n".join(outputs))

def stop_containers():
    for k, c in _containers.items():
        c.stop()

