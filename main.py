import requests
import os

from bs4 import BeautifulSoup

DO_ARCHIVES = True


def strip_schema(url: str) -> str:
    return url.split('http://', 1)[-1].split('https://', 1)[-1]


def scrape(root, tag=None):
    resp = requests.get(root)
    
    # check valid status
    if resp.status_code != 200:
        print(f"Invalid response code returned ({resp.status_code}), check the url.")
    
    # Find the 
    tree = find_links(resp.content)
    if tag is None:
        print(f"{len(tree)}: Root - {resp.url}")
        tag = ""
    else:
        print(f"{len(tree)}: {tag}")
    if len(tree) == 0:
        return {}
    tree = domain_expansion(tree, tag)
    return tree
    

def domain_expansion(tree: dict, tag) -> dict:
    for name, href in tree.items():
        # Link examples
        #   Category: https://courses.maths.ox.ac.uk/course/index.php?categoryid=807
        #   Course: https://courses.maths.ox.ac.uk/course/view.php?id=5479
        
        # Checks for archived courses and skips if flag is set.
        if not DO_ARCHIVES and name == "Archive":
            print("Skipping Archives!")
            continue
        
        if "view.php?id=" in href:
            # course, do nothing
            continue
        elif "index.php?categoryid=" in href:
            # category
            tree[name] = scrape(href, tag+"/"+name)
        else:
            print(f"Unexpected link: {name}, {href}")
        
    if not DO_ARCHIVES and "Archive" in tree.keys():
        tree.pop("Archive")
        
    return tree
        

def find_links(content) -> dict:
    # given a connection response, find the links to courses / course categories
    soup = BeautifulSoup(content, 'html.parser')
    
    all_divs = soup.find_all("div")
    filtered_divs = [div for div in all_divs if "class" in div.attrs.keys() and (div["class"] == "category notloaded with_children collapsed".split() or div["class"] == ["coursename"])]
    filtered_cats = {div.a.string: div.a['href'] for div in filtered_divs}
    
    #print(filtered_cats)
    return filtered_cats


def recursive_page_downloader(structure: dict | str, folder_root="."):
    # go through the tree to setup folders and call page downloader
    os.makedirs(folder_root, exist_ok=True)
    
    if isinstance(structure, dict):
        for name, sub_tree in structure.items():
            recursive_page_downloader(sub_tree, folder_root+"/"+name)
    elif isinstance(structure, str):
        scrape_course_page(structure, folder_root)
    else:
        raise TypeError(f"Unsupported type passed: {type(structure)}")


def scrape_course_page(href, folder_root):
    # can assume the folder exists
    page = requests.get(href)
    with open(folder_root+"/source.html", 'wb') as f:
        f.write(page.content)
    
    resources, assignments, folders, others = find_page_files(page.content)
    print("Test")
    
    
def find_page_files(content) -> (list, list, dict, list):
    # Finds the different resouces on a page and returns the found links
    soup = BeautifulSoup(content, "html.parser")
    
    # Find links in the divs
    all_divs = soup.find_all("div")
    filtered_divs = [div for div in all_divs if "class" in div.attrs.keys() and div["class"] == ["activityname"]]
    
    div_links = [div.a["href"] for div in filtered_divs]
    
    resource_links = [link for link in div_links if "resource/view.php?id=" in link]  # e.g. lecture notes
    assign_links = [link for link in div_links if "assign/view.php?id=" in link]  # e.g. problem sheets / submission page
    folder_name_link = {div.a.string: div.a["href"] for div in filtered_divs if "folder/view.php?id=" in div.a["href"]}  # e.g.
    
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
        if "." in end_url and not ".php" in end_url:
            # File extension in end section of url
            return True
        
        return False
    
    all_a = soup.find_all("a")
    other_direct_links = [a["href"] for a in all_a if valid_file_link(a["href"])]
    
    # "resource/view.php?id=..." <- pdf     always true??
    # "assign/view.php?id=..." <- link for sheet & upload     always true??
    # "folder/view.php?id=..." potential folder of pdfs... 
    return resource_links, assign_links, folder_name_link, other_direct_links


def download_files(href, folder_root, folder_name=None):
    pass        


def main():
    global DO_ARCHIVES
    output_path = "./output/"
    
    # Get root website
    root_url = input("Input the base website to scrape:").strip().lower() or "maths"
    
    # adds aliases for the maths course website
    if strip_schema(root_url) in ["maths", "math", "courses.maths.ox.ac.uk", "courses.maths.ox.ac.uk/course/index.php?categoryid=0"]:
        root_url = "https://courses.maths.ox.ac.uk/course/index.php?categoryid=0"
        DO_ARCHIVES = input("Download Arhcives? (y/n): ").lower().strip() == "y"
        
    # Ensures a schema is present
    if not root_url.startswith("http"):
        root_url = "http://" + root_url  # assume not secure
        
    # Gets a tree of all the course pages and the 'route' to get there
    course_structrue = scrape(root_url)
    structure = course_structrue if len(course_structrue) > 0 else root_url
    
    # Clean output_path
    if os.path.isdir(output_path):
        raise SystemError(f"Output directory already exists: {output_path}")
    if output_path.endswith("/"):
        output_path = output_path[:-1]
        
    # Download all the page contents
    recursive_page_downloader(structure, output_path)
    
    
    print(course_structrue)
    print("End")
    

if __name__ == "__main__":
    # course test: https://courses.maths.ox.ac.uk/course/view.php?id=5478
    # small scrape: https://courses.maths.ox.ac.uk/course/index.php?categoryid=817
    # general: maths
    main()