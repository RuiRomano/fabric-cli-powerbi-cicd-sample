import os
import shutil
import subprocess
import re
import json

def fab_authenticate_spn(
    client_id: str = None, client_secret: str = None, tenant_id: str = None
):
    """
    Authenticates with a Service Principal Name (SPN) using environment variables.
    This function retrieves the client ID, client secret, and tenant ID from the environment
    variables `FABRIC_CLIENT_ID`, `FABRIC_CLIENT_SECRET`, and `FABRIC_TENANT_ID` respectively.
    It then uses these credentials to authenticate with the SPN.
    Raises:
        Exception: If any of the required environment variables (`FABRIC_CLIENT_ID`,
                   `FABRIC_CLIENT_SECRET`, `FABRIC_TENANT_ID`) are not set.
    Side Effects:
        Executes the `run_fab_command` function to set the encryption fallback and perform the authentication.
    """

    print("Authenticating with SPN")

    if client_id is None or client_secret is None or tenant_id is None:
        client_id = os.getenv("FABRIC_CLIENT_ID")
        client_secret = os.getenv("FABRIC_CLIENT_SECRET")
        tenant_id = os.getenv("FABRIC_TENANT_ID")

    if not tenant_id or not client_id or not client_secret:
        raise Exception(
            "Environment variables FABRIC_CLIENT_ID, FABRIC_CLIENT_SECRET and FABRIC_TENANT_ID must be set"
        )

    run_fab_command("config set fab_encryption_fallback_enabled true")

    run_fab_command(
        f"auth login -u {client_id} -p {client_secret} --tenant {tenant_id}",
        include_secrets=True,
    )


def run_fab_command(
    command,
    capture_output: bool = False,
    include_secrets: bool = False,
    silently_continue: bool = False,
):
    """
    Executes a Fabric command.
    Parameters:
    command (str): The Fabric command to execute.
    capture_output (bool): If True, captures the command's output. Defaults to False.
    include_secrets (bool): If True, includes secrets in the debug output. Defaults to False.
    Returns:
    str: The output of the command if capture_output is True.
    Raises:
    Exception: If there is an error running the Fabric command.
    """

    result = subprocess.run(
        ["fab", "-c", command], capture_output=capture_output, text=True
    )

    if not (silently_continue) and (result.returncode > 0 or result.stderr):
        raise Exception(
            f"Error running fab command. exit_code: '{result.returncode}'; stderr: '{result.stderr}'"
        )

    if capture_output:

        output = result.stdout.strip().split("\n")[-1]

        return output


def create_workspace(workspace_name, capacity_name: str = "none", upns: list = None):
    """
    Creates a new workspace with the specified name and optional capacity.
    Additionally, assigns admin roles to the provided user principal names (UPNs).
    Args:
        workspace_name (str): The name of the workspace to be created.
        capacity_name (str, optional): The name of the capacity to assign to the workspace. Defaults to None.
        upns (list, optional): A list of user principal names to be assigned as admins to the workspace. Defaults to None.
    Returns:
        None
    """

    print(f"::group::Creating workspace: {workspace_name}")

    command = f"create /{workspace_name}.Workspace"

    if capacity_name:
        command += f" -P capacityName={capacity_name}"

    run_fab_command(command, silently_continue=True)

    if upns is not None:

        upns = [x for x in upns if x.strip()]

        if len(upns) > 0:
            print(f"Adding UPNs")

            for upn in upns:
                run_fab_command(
                    f"acl set -f /{workspace_name}.Workspace -I {upn} -R admin"
                )

    workspace_id = run_fab_command(
        f"get /{workspace_name}.Workspace -q id", capture_output=True
    )

    print(f"::endgroup::")

    return workspace_id


def create_connection(
    connection_name: str = None, parameters: dict = None, upns: list = None
):
    """
    Creates a connection with the specified name, parameters, and UPNs.
    Args:
        connection_name (str, optional): The name of the connection to create. Defaults to None.
        parameters (dict, optional): A dictionary of parameters to include in the connection. Defaults to None.
        upns (list, optional): A list of UPNs to add to the connection with admin rights. Defaults to None.
    Returns:
        str: The ID of the created connection.
    """

    print(f"::group::Creating connection {connection_name}")

    if parameters:
        param_str = ",".join(f"{key}={value}" for key, value in parameters.items())
        param_str = f"-P {param_str}"
    else:
        param_str = ""

    run_fab_command(
        f"create .connections/{connection_name}.Connection {param_str}",
        silently_continue=True,
    )

    connection_id = run_fab_command(
        f"get .connections/{connection_name}.Connection -q id", capture_output=True
    )

    if upns is not None:

        upns = [x for x in upns if x.strip()]

        if len(upns) > 0:
            print(f"Adding UPNs to item {connection_name}")

            for upn in upns:
                run_fab_command(
                    f"acl set -f .connections/{connection_name}.Connection -I {upn} -R admin"
                )

    print(f"::endgroup::")

    return connection_id


def create_item(
    workspace_name: str = None,
    item_type: str = None,
    item_name: str = None,
    parameters: dict = None,
    upns: list = None,
):
    """
    Creates an item in the specified workspace.
    Args:
        workspace_name (str, optional): The name of the workspace where the item will be created.
        item_type (str, optional): The type of the item to be created.
        item_name (str, optional): The name of the item to be created.
        parameters (dict, optional): A dictionary of parameters to be passed during item creation.
        upns (list, optional): A list of UPNs (User Principal Names) associated with the item.
    Returns:
        str: The ID of the created item.
    """

    print(f"::group::Creating item {workspace_name}/{item_name}.{item_type}")

    if parameters:
        param_str = ",".join(f"{key}={value}" for key, value in parameters.items())
        param_str = f"-P {param_str}"
    else:
        param_str = ""

    run_fab_command(
        f"create /{workspace_name}.workspace/{item_name}.{item_type} {param_str}",
        silently_continue=True,
    )

    item_id = run_fab_command(
        f"get /{workspace_name}.workspace/{item_name}.{item_type} -q id",
        capture_output=True,
    )

    print(f"::endgroup::")

    return item_id


def deploy_item(
    src_path,
    workspace_name,
    item_type: str = None,
    item_name: str = None,
    find_and_replace: dict = None,
    what_if: bool = False,
    func_after_staging=None,
):
    """
    Deploys an item to a specified workspace.
    Args:
        src_path (str): The source path of the item to be deployed.
        workspace_name (str): The name of the workspace where the item will be deployed.
        item_type (str, optional): The type of the item. If not provided, it will be inferred from the platform data.
        item_name (str, optional): The name of the item. If not provided, it will be inferred from the platform data.
        find_and_replace (dict, optional): A dictionary where keys are tuples containing a file filter regex and a find regex,
                                           and values are the replacement strings. This will be used to perform find and replace
                                           operations on the files in the staging path.
        what_if (bool, optional): If True, the deployment will be simulated but not actually performed. Defaults to False.
        func_after_staging (callable, optional): A function to be called after the item is copied to the staging path. It should
                                                 accept the staging path as its only argument.
    Returns:
        str: The ID of the deployed item if `what_if` is False. Otherwise, returns None.
    """

    print(f"::group::Deploying {src_path}")

    staging_path = copy_to_staging(src_path)

    # Call function that provides flexibility to change something in the staging files

    if func_after_staging:
        func_after_staging(staging_path)

    if os.path.exists(os.path.join(staging_path, ".platform")):

        with open(os.path.join(staging_path, ".platform"), "r") as file:
            platform_data = json.load(file)

        if item_name is None:
            item_name = platform_data["metadata"]["displayName"]

        if item_type is None:
            item_type = platform_data["metadata"]["type"]

        # Loop through all files and apply the find & replace with regular expressions

        if find_and_replace:

            for root, _, files in os.walk(staging_path):
                for file in files:

                    file_path = os.path.join(root, file)

                    with open(file_path, "r") as file:
                        text = file.read()

                    # Loop parameters and execute the find & replace in the ones that match the file path

                    for key, replace_value in find_and_replace.items():

                        find_and_replace_file_filter = key[0]

                        find_and_replace_file_find = key[1]

                        if re.search(find_and_replace_file_filter, file_path):
                            text, count_subs = re.subn(
                                find_and_replace_file_find, replace_value, text
                            )

                            if count_subs > 0:

                                print(
                                    f"Find & replace in file '{file_path}' with regex '{find_and_replace_file_find}'"
                                )

                                with open(file_path, "w") as file:
                                    file.write(text)

    if not what_if:
        run_fab_command(
            f"import -f /{workspace_name}.workspace/{item_name}.{item_type} -i {staging_path}"
        )

        # Return id after deployment

        item_id = run_fab_command(
            f"get /{workspace_name}.workspace/{item_name}.{item_type} -q id",
            capture_output=True,
        )

        return item_id

    print(f"::endgroup::")


def copy_to_staging(path):
    """
    Copies the contents of the specified directory to a staging folder.
    This function ensures that a staging folder exists, and if it already exists,
    it removes the existing staging folder and creates a new one. It then copies
    all files and directories from the specified path to the staging folder.
    Args:
        path (str): The path of the directory to be copied to the staging folder.
    Returns:
        str: The path to the staging folder where the contents have been copied.
    """

    # ensure staging folder exists

    current_folder = os.path.dirname(__file__)
    
    path_staging = os.path.join(current_folder, "_stg", os.path.basename(path))

    if os.path.exists(path_staging):
        shutil.rmtree(path_staging)

    os.makedirs(path_staging)

    # copy files to staging folder

    shutil.copytree(
        path, path_staging, dirs_exist_ok=True, ignore=shutil.ignore_patterns("*.abf")
    )

    return path_staging
