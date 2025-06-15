from urllib.parse import unquote
import requests
import os

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

DO_ARCHIVES = True
COOKIE_CACHE_FILE = "./cookie_jar.json"
# Headers might be needed - further testing needed.
request_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"}

# +---------------------------------------+
# |           Helper Functions            |
# +---------------------------------------+
def strip_schema(url: str) -> str:
    return url.split('http://', 1)[-1].split('https://', 1)[-1]


def make_file_safe_name(name):
    keepcharacters = (' ','.','_','(',')')  # Explicitly in windows *:\/<>| are not allowed
    safe_file_name = "".join(c for c in name if c.isalnum() or c in keepcharacters).rstrip()
    return safe_file_name


def get_auth_cookies(url) -> dict:
    # For cs just loading into the page will prompt for login
    cookie_cache = COOKIE_CACHE_FILE if os.path.isfile(COOKIE_CACHE_FILE) else None
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=cookie_cache)
        page = context.new_page()
        
        page.goto(url)
        page.wait_for_load_state("load")  # Waits for the page to load fully.
        page.wait_for_url(url, timeout=0)  # Waits for auth and redirection to original url
        cookies = context.cookies()
        context.storage_state(path=COOKIE_CACHE_FILE)
        
        browser.close()
    # adjust cookies to a format for requests
    cookies_dict = {c["name"]:c["value"] for c in cookies}
    return cookies_dict

# +---------------------------------------+
# |          Find Course Pages            |
# +---------------------------------------+
def scrape(root, tag=None, cookies=None):
    resp = requests.get(root, headers=request_headers, cookies=cookies)
    
    # check valid status
    if resp.status_code != 200:
        print(f"Invalid response code returned ({resp.status_code}), check the url.")
    
    # Find the 
    tree = find_links(resp.content)
    if tag is None:
        print(f"{len(tree):3d} Sub-Categories in: Root - {resp.url}")
        tag = ""
    else:
        print(f"{len(tree):3d} Sub-Categories in: {tag}")
    if len(tree) == 0:
        return {}
    tree = domain_expansion(tree, tag, cookies)
    return tree
    

def domain_expansion(tree: dict, tag: str, cookies: dict) -> dict:
    for name, href in tree.items():
        # Link examples
        #   Category: https://courses.maths.ox.ac.uk/course/index.php?categoryid=807
        #   Course: https://courses.maths.ox.ac.uk/course/view.php?id=5479
        
        # Checks for archived courses and skips if flag is set.
        if not DO_ARCHIVES and name == "Archive":
            print("Skipping Archives!")
            continue
        
        courses = ("course/view.php?id=", "course/view.php?name=")
        if any(sub in href for sub in courses):
            # course, do nothing
            continue
        # consistent between maths & cs
        elif "course/index.php?categoryid=" in href:
            # category
            tree[name] = scrape(href, tag+"/"+name, cookies)
        else:
            print(f"Unexpected link: {name}, {href}")
        
    if not DO_ARCHIVES and "Archive" in tree.keys():
        tree.pop("Archive")
        
    return tree
        

def find_links(content) -> dict:
    # given a connection response, find the links to courses / course categories
    soup = BeautifulSoup(content, 'html.parser')
    
    all_divs = soup.find_all("div")
    
    filtered_links = [div.a for div in all_divs if div.a is not None]
    valid_links = ("course/index.php?categoryid=", "course/view.php?name=", "course/view.php?id=")
    link_categories = {a.text: a["href"] for a in filtered_links if any(sub in a["href"] for sub in valid_links)}

    return link_categories


# +---------------------------------------+
# |        Download Course Pages          |
# +---------------------------------------+
def recursive_page_downloader(structure: dict | str, folder_root="."):
    # go through the tree to setup folders and call page downloader
    os.makedirs(folder_root, exist_ok=True)
    
    if isinstance(structure, dict):
        for name, sub_tree in structure.items():
            folder_name = make_file_safe_name(name)
            recursive_page_downloader(sub_tree, folder_root+"/"+folder_name)
    elif isinstance(structure, str):
        num_files = scrape_course_page(structure, folder_root)
        print(f"Found {num_files:3d} files: {folder_root}")
    else:
        raise TypeError(f"Unsupported type passed: {type(structure)}")


def scrape_course_page(href, folder_root):
    # Session required to get some assignment files e.g. https://courses.maths.ox.ac.uk/pluginfile.php/104615/mod_resource/content/38/Introduction%20to%20University%20Mathematics.pdf?forcedownload=0
    req_session = requests.Session() 
    
    # can assume the folder exists
    page = req_session.get(href, headers=request_headers)
    if page.status_code != 200:
        print("Unexpected status while loading course page")
        return False
    
    with open(folder_root+"/source.html", 'wb') as f:
        f.write(page.content)
    
    resources, assignments, folders, others = find_page_files(page.content)
    
    def deeper_request_check(href):
        assign_resp = req_session.get(href, headers=request_headers)
        if assign_resp.status_code != 200:
            print("Unexpected status while loading deeper page")
        a, b, c, files = find_page_files(assign_resp.content)  # Only expect direct links
        if len(a) + len(b) + len(c) > 0:
            print(f"Non direct file links found in: {assign}")
        return files
    
    found = 0
    # Download resource files - usually pdfs
    for resource in resources:
        download_file(resource, folder_root, req_session)
    found += len(resources)
    
    # Find assignment files & download:
    for assign in assignments:
        files = deeper_request_check(assign)
        for assign_file in files:
            download_file(assign_file, folder_root, req_session)
        found += len(files)
    
    # Folders
    for raw_folder_name, link in folders.items():
        files = deeper_request_check(link)
        new_folder = raw_folder_name.rsplit("Folder", 1)[0].strip()
        deeper_folder = folder_root + "/" + make_file_safe_name(new_folder)
        os.makedirs(deeper_folder, exist_ok=True)
        for folder_file in files:
            download_file(folder_file, deeper_folder, req_session)
        found += len(files)

    # Direct downloads
    for file in others:
        download_file(file, folder_root, req_session)
    found += len(others)
    
    return found
    
    
def find_page_files(content) -> tuple[list, list, dict, list]:
    # Finds the different resouces on a page and returns the found links
    soup = BeautifulSoup(content, "html.parser")
    
    # Find links in the divs
    all_divs = soup.find_all("div")
    filtered_divs = [div for div in all_divs if "class" in div.attrs.keys() and div["class"] == ["activityname"]]
    
    div_links = [div.a["href"] for div in filtered_divs if div.a is not None]
    
    resource_links = [link for link in div_links if "resource/view.php?id=" in link]  # e.g. lecture notes
    assign_links = [link for link in div_links if "assign/view.php?id=" in link]  # e.g. problem sheets / submission page
    folder_name_link = {div.a.text.strip(): div.a["href"] for div in filtered_divs if (div.a is not None) and ("folder/view.php?id=" in div.a["href"])}  # e.g.
    
    # Find other file links
    def valid_file_link(link: str) -> bool:
        """
        if link.endswith(".pdf"):
            return True
        if link.endswith("?forcedownload=1"):
            return True
        """
        if link in div_links:
            return False
        
        end_url = link.rsplit("/", 1)[-1]
        
        # Files to ignore, e.g. other website links
        ignore_types = ['.php', '.com', '.uk', '.org']
        for type in ignore_types:
            if type in end_url:
                return False
        
        if "." in end_url:
            # File extension in end section of url
            return True
        
        return False
    
    all_a = soup.find_all("a")
    other_direct_links = [a["href"] for a in all_a if ("href" in a.attrs.keys()) and valid_file_link(a["href"])]
    
    # "resource/view.php?id=..." <- pdf     always true??
    # "assign/view.php?id=..." <- link for sheet & upload     always true??
    # "folder/view.php?id=..." potential folder of pdfs... 
    return resource_links, assign_links, folder_name_link, other_direct_links


def download_file(href: str, folder_root, req_session=None):
    if req_session is None:
        req_session = requests.Session()
    
    if href.startswith("mailto:"):
        # email link, no useful data.
        return False
    
    if href.endswith("?forcedownload=1"):
        href = href[:-16]
    
    try:
        resp = req_session.get(href, headers=request_headers)
    except Exception as e:
        print(f"Error occured downloading a file, skipping. {href}")
        print(e.with_traceback)
        return False
    
    if resp.status_code != 200:
        print(f"Unexpected status while downloading file: {href}")
        return False
    
    if resp.url.endswith("/"):
        file_name = strip_schema(resp.url)[:-1]+".html"
    else:
        file_name = unquote(resp.url.rsplit("/", 1)[-1])
        
    if file_name.endswith("?forcedownload=1"):
        file_name = file_name[:-16]
    
    safe_file_name = make_file_safe_name(file_name)
    with open(folder_root+"/"+safe_file_name, "wb") as f:
        f.write(resp.content)
    
    return True


def main():
    global DO_ARCHIVES
    output_path = "./output/"
    
    # Clean output_path
    if os.path.isdir(output_path):
        
        raise SystemError(f"Output directory already exists: {output_path}")
    
    # Get root website
    root_url = input("Input the base website to scrape: ").strip().lower() or "maths"
    
    # Adds aliases for the maths and cs course websites
    strip_url = strip_schema(root_url)
    if strip_url in ["maths", "math", "courses.maths.ox.ac.uk", "courses.maths.ox.ac.uk/course/index.php?categoryid=0"]:
        root_url = "https://courses.maths.ox.ac.uk/course/index.php?categoryid=0"
        DO_ARCHIVES = input("Download Arhcives? (y/n): ").lower().strip() == "y"
        
    if strip_url in ["cs", "compsci", "cources.cs.ox.ac.uk"]:
        root_url = "https://courses.cs.ox.ac.uk/course/index.php?categoryid=0"
        
    # Checks if SSO Auth is needed
    base_url = strip_schema(root_url).split("/",1)[0]
    sso_auth = base_url in ["courses.cs.ox.ac.uk"]
        
    # Ensures a schema is present
    if not root_url.startswith("http"):
        root_url = "http://" + root_url  # assume not secure
        
    # Does authentication if required
    if sso_auth:
        cookies = get_auth_cookies(root_url)
    else:
        cookies = {}
        
    # Gets a tree of all the course pages and the 'route' to get there
    course_structrue = scrape(root_url, cookies=cookies)
    alt_structure = domain_expansion({"tmp": root_url}, tag="", cookies=cookies)["tmp"]
    
    structure = course_structrue if len(course_structrue) > 0 else root_url
    print("\nDownload Starting:")
    
    if output_path.endswith("/"):
        output_path = output_path[:-1]
        
    # Download all the page contents
    recursive_page_downloader(structure, output_path)
    

if __name__ == "__main__":
    # course test: https://courses.maths.ox.ac.uk/course/view.php?id=5478
    # other course test: https://courses.maths.ox.ac.uk/course/view.php?id=5546
    # small scrape: https://courses.maths.ox.ac.uk/course/index.php?categoryid=817
    # general: maths
    
    # cs course test: https://courses.cs.ox.ac.uk/course/view.php?name=ai_2024_2025
    # cs small: https://courses.cs.ox.ac.uk/course/index.php?categoryid=59
    # full cs: cs
    
    # TODO: Look into - Unexpected status while downloading file: https://royalsocietypublishing.org/doi/10.1098/rsos.150526
    main()