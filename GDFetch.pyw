import os,toml,urllib.request,time,requests,zipfile,json
import tkinter as tk
import customtkinter as ctk
from colorama import Fore,init

# Constants
version:str = "0.4"
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
    def submit():
        username = username_entry.get()
        repository = repository_entry.get()
        Debug.DLog(f"Username: {username}, Repository: {repository}")  # Just an example, replace this with your logic
        if (username == "" or repository == ""):
            return
        data['username']:str = username
        data['repository']:str = repository
        data['verbose']:bool = False
        Debug.Log("Setup complete!")
        data['setupComplete'] = True
        with open(workingDirectory+".data", "w") as f:
            toml.dump(data,f)
        Debug.DLog("Setup was succesful!")
        setup_root.destroy()
        get_all_releases(data['username'],data['repository'],True)
        userspace()
        

    setup_root = tk.Tk()
    setup_root.title("GitHub Repository Information")

    # Username input
    username_label = tk.Label(setup_root, text="Username:")
    username_label.pack()
    username_entry = tk.Entry(setup_root)
    username_entry.pack()
    # Set default value
    username_entry.insert(0, "CoolCoderMan281")

    # Repository input
    repository_label = tk.Label(setup_root, text="Repository:")
    repository_label.pack()
    repository_entry = tk.Entry(setup_root)
    repository_entry.pack()

    # Submit button
    submit_button = tk.Button(setup_root, text="Submit", command=submit)
    submit_button.pack()

    # Calculate center position
    window_width = 180  # Adjust this according to your frame width
    window_height = 120  # Adjust this according to your frame height
    screen_width = setup_root.winfo_screenwidth()
    screen_height = setup_root.winfo_screenheight()
    x_coordinate = (screen_width - window_width) // 2
    y_coordinate = (screen_height - window_height) // 2

    # Set window position
    setup_root.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")
    setup_root.mainloop()

def userspace():
    def get_releases(fetch:bool=False):
        # Code to fetch and populate the versions in the dropdown
        # Replace this with your logic to fetch versions and populate the dropdown
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
        # Code to handle the pullVersion() method
        # Replace this with your logic to handle the pullVersion() method
        selected_version = version_var.get()
        if selected_version == "":
            return
        Debug.Log(f"Pulling version: {selected_version}")  # Example: print the selected version
        releases = get_all_releases(data['username'],data['repository'])
        the_release = ""
        for release in releases:
            if release['name'] == selected_version:
                the_release = release['tag_name']
        pullVersion(the_release)

    def refresh_releases():
            # Code to refresh the release list in the dropdown
            get_releases(True)

    def back_setup():
        root.destroy()
        setup()

    root = tk.Tk()
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
    #
    version_label = tk.Label(root, text=f"GDFetch {version}", relief=tk.SUNKEN, anchor=tk.W)
    version_label.pack(side=tk.BOTTOM, fill=tk.X)
    # Button to go back to setup
    setup_button = tk.Button(root, text="Go Back to Setup", command=back_setup)
    setup_button.pack(side=tk.BOTTOM, pady=5)
    # Get all versions here and fill the dropdown
    get_releases()
    
    # Calculate center position
    window_width = 220  # Adjust this according to your frame width
    window_height = 120  # Adjust this according to your frame height
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_coordinate = (screen_width - window_width) // 2
    y_coordinate = (screen_height - window_height) // 2

    # Set window position
    root.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")
    root.mainloop()

# Fetch latest version
def getLatestVersion(refresh:bool=False) -> str:
    global waiting
    waiting = True
    Debug.DLog("Pulling from github..")
    os.system(f"curl -i https://github.com/{data['username']}/{data['repository']}/releases/latest > latest.txt")
    while True:
        if (os.path.exists("./latest.txt")):
            break
        pass
    tmp:str = ""
    with(open(workingDirectory+"latest.txt")) as f: 
        tmp = f.readlines(); tmp = tmp[5].removeprefix(f"Location: https://github.com/{data['username']}/{data['repository']}/releases/tag/")
    os.system("del latest.txt")
    waiting = False
    Debug.Log(f"Found version: {tmp.strip()}")
    return tmp.strip()
    

# Download latest version
def downloadVersion(target:str) -> str:
    try:
        release_api_url = f"https://api.github.com/repos/{data['username']}/{data['repository']}/releases/tags/{target}"
        response = requests.get(release_api_url)
        
        if response.status_code == 200:
            assets = response.json().get("assets", [])
            if assets:
                if len(assets) == 1:  # Automatically select if only one asset is available
                    download_url = assets[0]['browser_download_url']
                    file_name = assets[0]['name']
                    print(f"Downloading {file_name}")
                    download_path = f"./{file_name}"
                    urllib.request.urlretrieve(download_url, download_path)
                    print("Download complete!")
                    return os.path.splitext(download_path)[0]  # Return the path without extension
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
                            return os.path.splitext(download_path)[0]  # Return the path without extension
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
            # Extract all contents directly into the specified folder
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
    # List all files in the specified directory to identify available files
    Debug.Log(f"Scanning {extract_path} for build .exe")

    executable_files = find_executables(extract_path)
    if executable_files:
        Debug.DLog("Executable files found:")
        for exe_file in executable_files:
            Debug.DLog(exe_file)
    else:
        Debug.DLog("No executable files found.")
    # Locate and run the Unity executable within the extracted folder
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
    cache_file = "releases_cache.json"  # Path to the cache file

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

def pullVersion(target: str = None):
    if target is None:
        target = getLatestVersion()

    extract_path = f"./{target}"  # Set the extract_path to the target folder
    if os.path.exists(extract_path) and os.path.isdir(extract_path):
        Debug.Warn("You already have that version!")
        executeVersion(f"./{target}")
    else:
        download_path = downloadVersion(target)
        if download_path:
            unzipVersion(download_path, extract_path)  # Unzip to the specified folder
            executeVersion(extract_path)  # Run Unity exe from the extracted folder
            Debug.Log("Done!")

# Pre-user experience
init()
os.system("cls")

# Info
Debug.Log("GDFetch "+version)

# Check for saves
if(os.path.exists(workingDirectory+".data")):
    Debug.Log("Found configuration!")
    with open(workingDirectory+".data","r") as f:
        data = toml.load(f)
        verbose = data["verbose"]
        userspace()
    if(data['setupComplete'] != True):
        Debug.Warn("Setup was not completed.")
        setup()
else:
    Debug.Log("No configuration found.")
    setup()

# Main program - finally...
Debug.Log("Ready!")
# userspace is now called when setup completes