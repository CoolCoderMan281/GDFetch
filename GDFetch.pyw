import os,toml,urllib.request,time,requests,zipfile,json,shutil
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from colorama import Fore,init

# Constants
version:str = "0.4.5"
workingDirectory:str = "./"

# Variables
data:dict = dict()
userInput:str
verbose:bool = False
downloading:bool = False
waiting:bool = False
ranProcess:str = None

# Logs
class Debug:
    def Log(msg:str):
        print(Fore.WHITE + msg)
    def Warn(msg:str):
        print(Fore.YELLOW + msg+Fore.WHITE)
    def Error(msg:str):
        print(Fore.RED + msg+Fore.WHITE)
    def DLog(msg:str):
        if verbose: print(Fore.CYAN+msg+Fore.WHITE)

# Create save data
def setup():
    def check_repository_existence(username, repository):
        url = f"https://api.github.com/repos/{username}/{repository}"
        headers = {"Accept": "application/vnd.github.v3+json"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return True
        else:
            return False
    def submit():
        username = username_entry.get()
        repository = repo_var.get()
        Debug.DLog(f"Username: {username}, Repository: {repository}")
        if (username == "" or repository == ""):
            return
        if (not check_repository_existence(username,repository)):
            messagebox.showerror("GDFetch",f"The repository {username}/{repository} does not exist!")
            return
        data['username']:str = username
        data['repository']:str = repository
        data['verbose']:bool = False
        Debug.Log("Setup complete!")
        data['setupComplete'] = True
        with open(workingDirectory+".data", "w") as f:
            toml.dump(data,f)
        setup_root.destroy()
        get_all_releases(data['username'],data['repository'],True)
        babyspace()

    def check_updates():
        global data
        url = f"https://api.github.com/repos/CoolCoderMan281/GDFetch/releases/latest"
        response = requests.get(url)
        if response.status_code == 200:
            response = response.json()
            if response:
                latest_version = response["tag_name"]
                current_version = version
                if latest_version > current_version:
                    versions = []
                    all_releases = get_all_releases("CoolCoderMan281", "GDFetch",True)
                    if all_releases:
                        Debug.DLog("List of Releases:")
                        for release in all_releases:
                            Debug.DLog(f"Tag Name: {release['tag_name']} - Name: {release['name']}")
                            versions.append(release['name'])
                    else:
                        Debug.Error("Update failed, not found")
                        return
                    dataBackup = data
                    data['username'] = "CoolCoderMan281"
                    data['repository'] = "GDFetch"
                    download_path = downloadVersion(versions[0])
                    extract_path = f"./self-updater/"
                    if download_path:
                        unzipVersion(download_path, extract_path)
                        Debug.Log("Unzipped..")
                    data = dataBackup
                    if not os.path.exists("./self-updater/"):
                        Debug.Error("Update failed, download")
                        return
                    subfolder = next((f for f in os.listdir(extract_path) if os.path.isdir(os.path.join(extract_path, f))), None)
                    if subfolder:
                        subfolder_path = os.path.join(extract_path, subfolder)
                        for item in os.listdir(subfolder_path):
                            item_path = os.path.join(subfolder_path, item)
                            destination_path = os.path.join(extract_path, item)
                            shutil.move(item_path, destination_path)
                        shutil.rmtree(subfolder_path)
                    Debug.Log("Downloaded new version")
                    os.system("start cmd /c update.bat")
                    os._exit(1)
                else:
                    messagebox.showinfo("GDFetch","You have the latest version.")
            else:
                messagebox.showerror("GDFetch","Failed to fetch release information.")
        else:
            messagebox.showerror("GDFetch","Couldn't find updates.")
            return

    def update_repos(event=None):
        Debug.DLog("Checking repos..")
        url = f"https://api.github.com/users/{username_entry.get()}/repos"
        response = requests.get(url)

        if response.status_code == 200:
            repos = [repo['name'] for repo in response.json()]
            repository_entry['values'] = ()
            repo_var.set("")
            if repos:
                repository_entry['values'] = repos
                repository_entry.set(repos[0])
            return repos
        else:
            repository_entry['values'] = ()
            repo_var.set("")
            Debug.Warn(f"Failed to fetch repositories: {response.status_code}")
            return []

    setup_root = tk.Tk()
    setup_root.iconbitmap("./Icon.ico")
    setup_root.title("GitHub Repository Information")

    # Username input
    username_label = tk.Label(setup_root, text="Username:")
    username_label.pack()
    username_entry = tk.Entry(setup_root)
    username_entry.pack()
    username_entry.insert(0, "CoolCoderMan281")
    username_entry.bind("<Return>",update_repos)

    # Repository input
    repository_label = tk.Label(setup_root, text="Repository:")
    repository_label.pack()
    repo_var = tk.StringVar()
    repository_entry = tk.ttk.Combobox(setup_root, textvariable=repo_var, width=200, state='readonly')
    repository_entry.pack()

    # Submit button
    submit_button = tk.Button(setup_root, text="Submit", command=submit)
    submit_button.pack()

    # Self update button
    update_button = tk.Button(setup_root, text="Update GDFetch", command=check_updates)
    update_button.pack()

    # Calculate center position
    window_width = 180
    window_height = 120
    screen_width = setup_root.winfo_screenwidth()
    screen_height = setup_root.winfo_screenheight()
    x_coordinate = (screen_width - window_width) // 2
    y_coordinate = (screen_height - window_height) // 2

    # Set window position
    setup_root.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")
    update_repos()
    setup_root.mainloop()

def userspace():
    check_updates()
    def get_releases(fetch:bool=False):
        versions = []
        all_releases = get_all_releases(data['username'], data['repository'],refresh=fetch)
        if all_releases:
            Debug.DLog("List of Releases:")
            for release in all_releases:
                Debug.DLog(f"Tag Name: {release['tag_name']} - Name: {release['name']}")
                versions.append(release['name'])
        else:
            Debug.Warn("No releases found.")
        version_dropdown['values'] = versions

    def get():
        selected_version = version_var.get()
        if selected_version == "":
            return
        Debug.Log(f"Pulling version: {selected_version}")
        releases = get_all_releases(data['username'],data['repository'])
        the_release = ""
        for release in releases:
            if release['name'] == selected_version:
                the_release = release['tag_name']
        pullVersion(the_release)

    def refresh_releases():
        get_releases(True)

    def back_setup():
        root.destroy()
        setup()

    root = tk.Tk()
    root.iconbitmap("./Icon.ico")
    root.title(f"GDFetch {version}")
    # Dropdown to select versions (empty initially)
    version_var = tk.StringVar()
    version_dropdown = tk.ttk.Combobox(root, textvariable=version_var, width=200, state='readonly')
    version_dropdown.pack()
    # Button to run the pullVersion() method
    pull_button = tk.Button(root, text="Pull Version", command=get)
    pull_button.pack()
    # Refresh button to update the release list in the dropdown
    refresh_button = tk.Button(root, text="Refresh Versions", command=refresh_releases)
    refresh_button.pack()
    # Version label
    version_label = tk.Label(root, text=f"GDFetch {version}", relief=tk.SUNKEN, anchor=tk.W)
    version_label.pack(side=tk.BOTTOM, fill=tk.X)
    # Button to go back to setup
    setup_button = tk.Button(root, text="Go Back to Setup", command=back_setup)
    setup_button.pack(side=tk.BOTTOM, pady=5)
    # Get all versions here and fill the dropdown
    get_releases()
    
    # Calculate center position
    window_width = 220
    window_height = 120
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_coordinate = (screen_width - window_width) // 2
    y_coordinate = (screen_height - window_height) // 2

    # Set window position
    root.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")
    root.mainloop()    

def babyspace():
    check_updates()
    def get_releases(fetch:bool=True):
        versions = []
        data['username'] = "CoolCoderMan281"
        data['repository'] = repo_var.get()
        all_releases = get_all_releases(data['username'], data['repository'],refresh=fetch)
        if all_releases:
            Debug.DLog("List of Releases:")
            for release in all_releases:
                Debug.DLog(f"Tag Name: {release['tag_name']} - Name: {release['name']}")
                versions.append(release['name'])
        else:
            Debug.Warn("No releases found.")
        version_dropdown['values'] = versions

    def get():
        data['username'] = "CoolCoderMan281"
        data['repository'] = repo_var.get()
        selected_version = version_var.get()
        if selected_version == "":
            return
        Debug.Log(f"Pulling version: {selected_version}")
        releases = get_all_releases(data['username'],data['repository'])
        the_release = ""
        for release in releases:
            if release['name'] == selected_version:
                the_release = release['tag_name']
        pullVersion(the_release)

    def advanced():
        root.destroy()
        userspace()

    def update_repos(event=None):
        Debug.DLog("Checking repos..")
        url = f"https://api.github.com/users/CoolCoderMan281/repos"
        response = requests.get(url)

        if response.status_code == 200:
            repos = [repo['name'] for repo in response.json()]
            repository_entry['values'] = ()
            repo_var.set("")
            if repos:
                repository_entry['values'] = repos
                repository_entry.set(repos[0])
            return repos
        else:
            repository_entry['values'] = ()
            repo_var.set("")
            Debug.Warn(f"Failed to fetch repositories: {response.status_code}")
            return []

    root = tk.Tk()
    root.iconbitmap("./Icon.ico")
    root.title(f"GDFetch {version}")
    # Repository input
    repository_label = tk.Label(root, text="Game:")
    repository_label.pack()
    repo_var = tk.StringVar()
    repository_entry = tk.ttk.Combobox(root, textvariable=repo_var, width=200, state='readonly')
    repository_entry.pack()
    repository_entry.bind("<<ComboboxSelected>>",get_releases)
    # Dropdown to select versions (empty initially)
    version_var = tk.StringVar()
    version_dropdown = tk.ttk.Combobox(root, textvariable=version_var, width=200, state='readonly')
    version_dropdown.pack()
    # Button to run the pullVersion() method
    pull_button = tk.Button(root, text="Go", command=get)
    pull_button.pack()
    # Button to go back to setup
    setup_button = tk.Button(root, text="Advanced", command=advanced)
    setup_button.pack()
    # Version label
    version_label = tk.Label(root, text=f"GDFetch {version}", relief=tk.SUNKEN, anchor=tk.W)
    version_label.pack(side=tk.BOTTOM, fill=tk.X)
    # Get all versions here and fill the dropdown
    update_repos()
    
    # Calculate center position
    window_width = 220
    window_height = 140
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_coordinate = (screen_width - window_width) // 2
    y_coordinate = (screen_height - window_height) // 2

    # Set window position
    root.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")
    root.mainloop()    

# Download selected version
def downloadVersion(target:str) -> str:
    try:
        release_api_url = f"https://api.github.com/repos/{data['username']}/{data['repository']}/releases/tags/{target}"
        response = requests.get(release_api_url)
        
        if response.status_code == 200:
            assets = response.json().get("assets", [])
            if assets:
                if len(assets) == 1:
                    download_url = assets[0]['browser_download_url']
                    file_name = assets[0]['name']
                    print(f"Downloading {file_name}")
                    download_path = f"./{file_name}"
                    urllib.request.urlretrieve(download_url, download_path)
                    print("Download complete!")
                    return os.path.splitext(download_path)[0]
                else:
                    print("Available assets for this release:")
                    for index, asset in enumerate(assets, start=1):
                        print(f"{index}. {asset['name']}")

                    asset_choice = input("Enter the number of the file to download: ")
                    try:
                        asset_index = int(asset_choice) - 1
                        if 0 <= asset_index < len(assets):
                            download_url = assets[asset_index]['browser_download_url']
                            file_name = assets[asset_index]['name']
                            print(f"Downloading {file_name}...")
                            download_path = f"./{file_name}"
                            urllib.request.urlretrieve(download_url, download_path)
                            print("Download complete!")
                            return os.path.splitext(download_path)[0]
                        else:
                            print("Invalid choice.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")
            else:
                print("No assets found for this release.")
        else:
            print(f"Failed to fetch release information: {response.status_code}")
    except requests.RequestException as e:
        print(f"Request failed: {e}")
    return ""


def unzipVersion(file_path: str, extract_path: str):
    if (not file_path.endswith(".zip")):
        file_path += ".zip"
    try:
        Debug.Log(f"Extracting {file_path} to {extract_path}")
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        Debug.Log(f"Extraction complete to {extract_path}")
    except zipfile.BadZipFile:
        Debug.Warn("Invalid ZIP file. Extraction failed.")
    except FileNotFoundError:
        Debug.Warn(f"File not found: {file_path}")
    except Exception as e:
        Debug.Warn(f"An error occurred while unzipping: {e}")
    
    try:
        Debug.Log("Removing old .zip")
        os.remove(file_path)
    except:
        Debug.Warn("Failed to remove ZIP.")

def find_executables(start_dir):
    executable_list = []
    for root, dirs, files in os.walk(start_dir):
        for file in files:
            if file.endswith(".exe"):
                executable_list.append(os.path.join(root, file))
    return executable_list

# Run the build
def executeVersion(extract_path: str):
    global ranProcess
    Debug.Log(f"Scanning {extract_path} for build .exe")

    executable_files = find_executables(extract_path)
    if executable_files:
        Debug.DLog("Executable files found:")
        for exe_file in executable_files:
            Debug.DLog(exe_file)
    else:
        Debug.DLog("No executable files found.")
    exe_files = [f for f in executable_files if f.endswith(".exe")]

    unity_exe = None
    for exe_file in exe_files:
        if "UnityCrashHandler" not in exe_file:
            unity_exe = exe_file
            break

    if unity_exe:
        Debug.Log(f"Opening {unity_exe}")
        ranProcess = unity_exe.removesuffix(".exe")
        os.system(f'start "" "{unity_exe}"')
    else:
        Debug.Warn("Unity executable not found.")

def get_all_releases(username, repository,refresh:bool=False):
    cache_file = "releases_cache.json"

    if refresh or not os.path.exists(cache_file):
        Debug.DLog("Fetching from GitHub...")
        url = f"https://api.github.com/repos/{username}/{repository}/releases"
        headers = {"Accept": "application/vnd.github.v3+json"}

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            with open(cache_file, "w") as f:
                json.dump(response.json(), f)
            return response.json()
        else:
            Debug.Warn(f"Failed to fetch releases: {response.status_code}")
            return None
    else:
        Debug.DLog("Using cache.")
        with open(cache_file, "r") as f:
            return json.load(f)

def pullVersion(target:str):
    extract_path = f"./{target}"
    if os.path.exists(extract_path) and os.path.isdir(extract_path):
        Debug.Warn("You already have that version!")
        executeVersion(f"./{target}")
    else:
        download_path = downloadVersion(target)
        if download_path:
            unzipVersion(download_path, extract_path)
            executeVersion(extract_path)
            Debug.Log("Done!")

def check_updates():
    url = f"https://api.github.com/repos/CoolCoderMan281/GDFetch/releases/latest"
    response = requests.get(url)
    if response.status_code == 200:
        response = response.json()
        if response:
            latest_version = response["tag_name"]
            current_version = version
            if latest_version > current_version:
                messagebox.showwarning("GDFetch","A new version is available. Update in setup.")

# Fix issues with coloring the console on older systems
init()
os.system("cls")

# Info
Debug.Log("GDFetch "+version)

# Practically the entrypoint, use this for startup execution
if(os.path.exists(workingDirectory+".data")):
    Debug.Log("Found configuration!")
    with open(workingDirectory+".data","r") as f:
        data = toml.load(f)
        verbose = data["verbose"]
        babyspace()
    if(data['setupComplete'] != True):
        Debug.Warn("Setup was not completed.")
        setup()
else:
    Debug.Log("No configuration found.")
    setup()