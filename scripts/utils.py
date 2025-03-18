import os
import shutil
import subprocess
import re
import json

current_folder = os.path.dirname(__file__)
debug = False


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

    if debug and not include_secrets:
        print(f"Running fab command: {command}")

    result = subprocess.run(
        ["fab", "-c", command], capture_output=capture_output, text=True
    )

    if not (silently_continue) and (result.returncode > 0 or result.stderr):
        raise Exception(
            f"Error running fab command. exit_code: '{result.returncode}'; stderr: '{result.stderr}'"
        )

    if capture_output:

        output = result.stdout.strip()

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

    print(f"::endgroup::")


def deploy_semanticmodel(
    path,
    workspace_name,
    semanticmodel_name: str = None,
    semanticmodel_parameters: dict = None,
):
    """
    Deploys a semantic model to a specified workspace.
    Args:
        path (str): The file path to the semantic model.
        workspace_name (str): The name of the workspace where the semantic model will be deployed.
        semanticmodel_name (str, optional): The name of the semantic model. If not provided, it will be read from the platform properties.
        semanticmodel_parameters (dict, optional): A dictionary of parameters to update the semantic model definition.
    Returns:
        str: The ID of the deployed semantic model.
    """

    print(f"::group::Deploying semantic model: {path}")

    # Create a staging copy of the semantic model for manipulation before publish

    staging_path = copy_to_staging(path)

    if semanticmodel_parameters is not None:
        # Update semantic model definition with new parameters
        update_semanticmodel_definition(staging_path, semanticmodel_parameters)

    if semanticmodel_name is None:

        # Read platform properties if name is not supplied

        platform_data = read_pbip_jsonfile(os.path.join(staging_path, ".platform"))

        semanticmodel_name = platform_data["metadata"]["displayName"]

    # Deploy semantic model

    run_fab_command(
        f"import -f /{workspace_name}.workspace/{semanticmodel_name}.semanticmodel -i {staging_path}"
    )

    # Get semantic model id

    semanticmodel_id = run_fab_command(
        f"get /{workspace_name}.workspace/{semanticmodel_name}.semanticmodel -q id",
        capture_output=True,
    )

    print(f"::endgroup::")

    return semanticmodel_id


def deploy_report(
    path, workspace_name, report_name: str = None, semanticmodel_id: str = None
):
    """
    Deploys a Power BI report to a specified workspace.
    Args:
        path (str): The file path to the report to be deployed.
        workspace_name (str): The name of the workspace where the report will be deployed.
        report_name (str, optional): The name of the report. If not provided, the name will be read from the platform properties.
        semanticmodel_id (str, optional): The ID of the semantic model to connect the report to. If provided, the report will be connected to this semantic model.
    Returns:
        str: The ID of the deployed report.
    Raises:
        Exception: If the report definition does not have a 'byConnection' configuration and 'semanticmodel_id' is not provided.
    """

    print(f"::group::Deploying report: {path}")

    # Create a staging copy of the semantic model for manipulation before publish

    staging_path = copy_to_staging(path)

    if not report_name:

        # Read platform properties if name is not supplied

        platform_data = read_pbip_jsonfile(os.path.join(staging_path, ".platform"))

        report_name = platform_data["metadata"]["displayName"]

    definition_path = os.path.join(staging_path, "definition.pbir")

    report_definition = read_pbip_jsonfile(definition_path)

    # If semantic model id is provided, overwrite the definition.pbir to ensure its connected to the provided semantic model

    if semanticmodel_id:

        report_definition["datasetReference"]["byPath"] = None

        by_connection_obj = {
            "connectionString": None,
            "pbiServiceModelId": None,
            "pbiModelVirtualServerName": "sobe_wowvirtualserver",
            "pbiModelDatabaseName": semanticmodel_id,
            "name": "EntityDataSource",
            "connectionType": "pbiServiceXmlaStyleLive",
        }

        report_definition["datasetReference"]["byConnection"] = by_connection_obj

        with open(definition_path, "w") as file:
            json.dump(report_definition, file, indent=4)
    else:
        if not (
            "datasetReference" in report_definition
            and "byConnection" in report_definition["datasetReference"]
        ):
            raise Exception(
                "Report 'definition.pbir' must have a 'byConnection' configuration. Use of 'bypath' is not supported when importing report with API."
            )

    # Only for PBIR

    if os.path.exists(os.path.join(staging_path, "definition")):

        # Ensure default page

        report_json = read_pbip_jsonfile(
            os.path.join(staging_path, "definition", "report.json")
        )

        if "annotations" in report_json:

            defaultPageAnnotation = [
                x for x in report_json["annotations"] if x["name"] == "defaultPage"
            ]

            if defaultPageAnnotation:

                defaultPage = defaultPageAnnotation[0]["value"]

                print(f"Setting default page to '{defaultPage}'")

                pages_json = read_pbip_jsonfile(
                    os.path.join(staging_path, "definition", "pages", "pages.json")
                )

                pages_json["activePageName"] = defaultPage

                with open(
                    os.path.join(staging_path, "definition", "pages", "pages.json"), "w"
                ) as file:
                    json.dump(pages_json, file, indent=4)

    # Deploy report

    run_fab_command(
        f"import -f /{workspace_name}.workspace/{report_name}.report -i {staging_path}"
    )

    # Get report id

    report_id = run_fab_command(
        f"get /{workspace_name}.workspace/{report_name}.report -q id",
        capture_output=True,
    )

    print(f"::endgroup::")

    return report_id


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

    path_staging = os.path.join(current_folder, "_stg", os.path.basename(path))

    if os.path.exists(path_staging):
        shutil.rmtree(path_staging)

    os.makedirs(path_staging)

    # copy files to staging folder

    shutil.copytree(path, path_staging, dirs_exist_ok=True)

    return path_staging


def update_semanticmodel_definition(path, parameters: dict):
    """
    Updates the semantic model definition file with the provided parameters.
    This function reads the 'expressions.tmdl' file located in the given path,
    updates the expressions with the provided parameters, and writes the updated
    content back to the file.
    Args:
        path (str): The directory path where the 'definition' folder containing 'expressions.tmdl' is located.
        parameters (dict): A dictionary of parameters to update in the format {parameter_name: new_value}.
    Raises:
        Exception: If the 'expressions.tmdl' file does not exist or cannot be found.
    """

    print(f"Updating semantic model definition: {path}")

    file_path = os.path.join(path, "definition", "expressions.tmdl")

    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            text = file.read()

    if text:

        for key, value in parameters.items():

            print(f"Updating parameter '{key}'")

            text = re.sub(rf'(expression\s+{key}\s*=\s*)(".*?")', rf'\1"{value}"', text)

        with open(file_path, "w") as file:
            file.write(text)
    else:
        raise Exception("Cannot find expressions.tmdl")


def read_platform_file(path):
    """
    Reads the .platform file from the specified directory and returns its contents as a dictionary.
    Args:
        path (str): The directory path where the .platform file is located.
    Returns:
        dict: The contents of the .platform file.
    Raises:
        Exception: If the .platform file does not exist in the specified directory.
    """

    platform_file_path = os.path.join(path, ".platform")

    if not os.path.exists(platform_file_path):
        raise Exception(f"Cannot find .platform file: '{platform_file_path}'")

    with open(platform_file_path, "r") as platform_file:
        platform_data = json.load(platform_file)

        return platform_data


def read_pbip_jsonfile(path):
    """
    Reads a JSON file from the specified path and returns its contents as a dictionary.
    Args:
        path (str): The file path to the JSON file.
    Returns:
        dict: The contents of the JSON file.
    Raises:
        Exception: If the file does not exist at the specified path.
    """

    if not os.path.exists(path):
        raise Exception(f"Cannot find file: '{path}'")

    with open(path, "r") as file:
        data = json.load(file)

    return data
